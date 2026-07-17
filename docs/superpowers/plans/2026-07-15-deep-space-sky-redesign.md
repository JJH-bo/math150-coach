# Cold Deep-Space Sky Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the failed bright-galaxy panorama with a cold, restrained, physically grounded deep-space sky that matches the approved learning stars and relativistic Boss.

**Architecture:** Use an official NASA randomized 8K stellar catalog map as the stable spherical far field, then render only a few bounded three-dimensional molecular-cloud volumes in a full-resolution HDR shader. Remove the global thin-disc extinction pass entirely; the final pipeline becomes one sky pass, selective bloom, and ACES-style tone mapping.

**Tech Stack:** WebGL2, GLSL ES 3.00, `RGBA16F` render targets, deterministic 3D value noise, analytic stellar PSF, ACES-style tone mapping, NASA SVS randomized Tycho/Gaia star-map data.

## Global Constraints

- Modify only the isolated cosmic-sky proof and its dedicated sky asset.
- Do not modify the approved stars, links, Boss black hole, single-system composition, course data, or navigation.
- The default frame must remain 65%–75% near-black without becoming a flat black field.
- No bright Milky Way stripe, saturated nebula smoke, global extinction plane, decorative star carpet, or large black mask.
- All reachable camera directions must remain valid; no preset-only concealment.
- Do not run the project test suite or unrelated diagnostics. Verification is limited to shader compilation and direct visual inspection of the sky proof.

---

### Task 1: Replace the photographic Milky Way with a restrained catalog far field

**Files:**
- Create: `frontend/space/assets/nasa-randomized-skymap-t3-8k.jpg`
- Create: `frontend/space/assets/nasa-randomized-skymap-source.txt`

**Interfaces:**
- Consumes: NASA SVS source `https://svs.gsfc.nasa.gov/vis/a000000/a004400/a004451/RandomizedSkymap.t3_08192x04096.tif`.
- Produces: an 8192×4096 browser-decodable equirectangular JPEG and a local attribution record.

- [ ] **Step 1: Download the official 8K randomized star map**

Run from the worktree:

```powershell
Invoke-WebRequest `
  -Uri 'https://svs.gsfc.nasa.gov/vis/a000000/a004400/a004451/RandomizedSkymap.t3_08192x04096.tif' `
  -OutFile "$env:TEMP\nasa-randomized-skymap-t3-8k.tif"
```

Expected: a 8192×4096 TIFF created from the Tycho catalog with a faint galactic disc and randomized bright-star positions.

- [ ] **Step 2: Convert the TIFF to a high-quality browser asset**

Use Windows `System.Drawing` to preserve full resolution and save JPEG quality 95:

```powershell
Add-Type -AssemblyName System.Drawing
$source = [System.Drawing.Image]::FromFile("$env:TEMP\nasa-randomized-skymap-t3-8k.tif")
$codec = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() |
  Where-Object MimeType -eq 'image/jpeg'
$parameters = [System.Drawing.Imaging.EncoderParameters]::new(1)
$parameters.Param[0] = [System.Drawing.Imaging.EncoderParameter]::new(
  [System.Drawing.Imaging.Encoder]::Quality,
  [long]95
)
$source.Save(
  'frontend/space/assets/nasa-randomized-skymap-t3-8k.jpg',
  $codec,
  $parameters
)
$source.Dispose()
```

Expected: `frontend/space/assets/nasa-randomized-skymap-t3-8k.jpg` retains the catalog star color and brightness hierarchy without requiring EXR decoding in the browser.

- [ ] **Step 3: Record the source and remove the temporary TIFF**

Create the attribution file with exactly:

```text
NASA Scientific Visualization Studio
The Alternative Night Sky - Another Time - Another Place, ID 4451
https://svs.gsfc.nasa.gov/4451/
Source asset: RandomizedSkymap.t3_08192x04096.tif
Visualizers: Tom Bridgman and Ernie Wright
Catalog sources: Hipparcos and Tycho-2
```

Then remove only `$env:TEMP\nasa-randomized-skymap-t3-8k.tif`.

- [ ] **Step 4: Commit the far-field asset**

```powershell
git add frontend/space/assets/nasa-randomized-skymap-t3-8k.jpg frontend/space/assets/nasa-randomized-skymap-source.txt
git commit -m "Add the deep-space catalog far field"
```

Expected: the asset commit contains no application or renderer changes.

---

### Task 2: Rebuild the sky renderer around bounded HDR volumes

**Files:**
- Modify: `frontend/space/cosmos-lab/index.html`

**Interfaces:**
- Consumes: `../assets/nasa-randomized-skymap-t3-8k.jpg` as a stable plate-carrée far field.
- Produces: `/space/cosmos-lab/?view=abyss`, `?view=cloud`, and `?view=remote`, plus `window.renderCosmos(milliseconds: number): void`.

- [ ] **Step 1: Replace the old shader graph**

Delete `far-fragment`, `volume-fragment`, and `combine-fragment`. Add one full-resolution `sky-fragment` with this interface:

```glsl
uniform sampler2D starMap;
uniform vec2 resolution;
uniform vec3 orientation;
uniform vec3 cameraOffset;
uniform float fov;
uniform float time;
uniform float cloudVisibility;
out vec4 fragColor;
```

The shader must use the existing spherical `cameraRay` and `skyUv` mapping, decode the JPEG sample from sRGB to linear, and grade it below the approved subject luminance:

```glsl
vec3 catalog = pow(texture(starMap, skyUv(direction)).rgb, vec3(2.2));
float catalogLuma = dot(catalog, vec3(0.2126, 0.7152, 0.0722));
vec3 farField = catalog * mix(0.15, 0.42, smoothstep(0.02, 0.55, catalogLuma));
```

Do not derive or apply a global galactic-plane mask.

- [ ] **Step 2: Add finite ellipsoid intersections**

Define a bounded ray interval for each cloud:

```glsl
vec2 intersectEllipsoid(vec3 origin, vec3 direction, vec3 center, vec3 radii) {
  vec3 ro = (origin - center) / radii;
  vec3 rd = direction / radii;
  float b = dot(ro, rd);
  float c = dot(ro, ro) - 1.0;
  float h = b * b - dot(rd, rd) * c;
  if (h <= 0.0) return vec2(1.0, -1.0);
  h = sqrt(h);
  return vec2((-b - h) / dot(rd, rd), (-b + h) / dot(rd, rd));
}
```

Place exactly three non-overlapping large volumes at different distances. March only inside valid intervals with 28 blue-noise-jittered steps. Build density from a smooth ellipsoid envelope, four-octave low-frequency noise, and one higher-frequency filament term. Accumulate extremely low cold-blue/brown scattering and optical depth.

- [ ] **Step 3: Make extinction bounded by construction**

The cloud integration must end with:

```glsl
float transmittance = max(exp(-opticalDepth * 0.82), 0.24);
vec3 sky = farField * transmittance + inScatter;
```

The minimum transmittance is local to rays that actually intersect a cloud. Rays outside all ellipsoids retain `transmittance == 1.0`. No shader path may multiply the entire background by a screen-space or plane-space mask.

- [ ] **Step 4: Add restrained analytic foreground stars**

Add only two sparse spherical hash layers above the NASA catalog. The dense layer must remain subpixel and the rare bright layer may use a compact PSF with short diffraction rays. Use spectral colors, no time-varying brightness, and no uniform halo:

```glsl
foreground += starLayer(uv, vec2(640.0, 320.0), 11.0, 0.006, 0.018, 84.0, 0.0);
foreground += starLayer(uv, vec2(110.0, 55.0), 29.0, 0.008, 0.22, 128.0, 0.18);
```

- [ ] **Step 5: Rebuild the HDR pass chain**

Render `sky-fragment` directly into a full-resolution `RGBA16F` target. Keep two quarter-resolution bloom targets and the existing final ACES-style pass, but raise the bloom threshold above the dark-cloud range and reduce bloom contribution:

```glsl
vec3 color = aces((scene + bloom * 0.075) * exposure);
```

Remove the half-resolution volume target and the combine target entirely. This removes the architecture that created the diagonal black band and its stair-stepped edge.

- [ ] **Step 6: Replace views and interaction**

Use three restrained camera presets:

```js
const presets = {
  abyss:  { yaw: -0.58, pitch: 0.12, roll: -0.08, fov: 67, cloud: 0.78, exposure: 0.82 },
  cloud:  { yaw:  0.34, pitch: -0.08, roll: 0.05, fov: 61, cloud: 1.00, exposure: 0.78 },
  remote: { yaw:  1.82, pitch: 0.22, roll: -0.03, fov: 73, cloud: 0.48, exposure: 0.88 },
};
```

Keep drag-to-look and wheel FOV. Use pointer position only for a camera-origin offset no greater than `0.025` world units so the nearest bounded cloud has slow parallax. Remove the old “银河核心/暗尘裂谷/深空边缘” language and replace it with “深渊/暗云/远场”.

- [ ] **Step 7: Simplify the review surface**

Keep the canvas full-screen. Reduce the HUD to one quiet title, three compact view buttons, one low-opacity interaction hint, and the NASA SVS credit. The interface must not add decorative gradients, frames, star icons, or course content.

- [ ] **Step 8: Commit the renderer reconstruction**

```powershell
git add frontend/space/cosmos-lab/index.html
git commit -m "Rebuild the sky as a cold deep-space field"
```

Expected: the commit modifies only the isolated sky proof.

---

### Task 3: Visually calibrate the isolated sky

**Files:**
- Modify only if visual review requires it: `frontend/space/cosmos-lab/index.html`

**Interfaces:**
- Consumes: the three rebuilt sky views and free camera drag.
- Produces: the final review entry `http://127.0.0.1:4173/space/cosmos-lab/?view=abyss`.

- [ ] **Step 1: Start only the static visual server**

```powershell
python -m http.server 4173 -d frontend
```

Expected: the isolated proof is available without starting the course backend or running tests.

- [ ] **Step 2: Inspect the three presets at 1800×1100**

Open and capture:

```text
http://127.0.0.1:4173/space/cosmos-lab/?view=abyss
http://127.0.0.1:4173/space/cosmos-lab/?view=cloud
http://127.0.0.1:4173/space/cosmos-lab/?view=remote
```

Reject any frame with a bright galactic stripe, colorful smoke, wallpaper-flat depth, uniform star density, a hard cloud silhouette, a second focal object, or lifted gray blacks.

- [ ] **Step 3: Drag through the full allowed pitch and one complete yaw turn**

Visually reject any seam, polar stretch, black band, staircase, volume box edge, repeated noise tile, or direction where the frame becomes uniformly bright or uniformly empty.

- [ ] **Step 4: Tune only visual constants**

If a rejection occurs, adjust only cloud centers/radii, density thresholds, star gains, exposure, and bloom constants in `frontend/space/cosmos-lab/index.html`. Do not add another rendering subsystem or reintroduce an infinite plane.

- [ ] **Step 5: Commit final visual calibration**

```powershell
git add frontend/space/cosmos-lab/index.html
git commit -m "Calibrate the cold deep-space sky"
```

Expected: no commit is created if no calibration was needed.
