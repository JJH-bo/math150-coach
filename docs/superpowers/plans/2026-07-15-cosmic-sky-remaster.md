# Cosmic Sky Remaster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an isolated high-end universe background that combines a real astronomical far field with volumetric galactic dust, analytic stars, parallax, and HDR finishing.

**Architecture:** A standalone WebGL2 page samples the existing ESO equirectangular panorama as a directional far field, then reconstructs galactic emission and dust transmission in a full-screen fragment pass. Stable spherical star layers and sparse near-field clouds are accumulated into an `RGBA16F` target and finished through thresholded multi-scale bloom and ACES-style tone mapping.

**Tech Stack:** HTML, CSS, JavaScript, WebGL2, GLSL ES 3.00, `RGBA16F`, equirectangular direction mapping, procedural 3D noise, analytic PSF stars, HDR bloom.

## Global Constraints

- Display only the universe background; no nodes, Boss, connections, course UI, spacecraft, planets, or decorative objects.
- Reuse `frontend/space/assets/milky-way-eso-6000.jpg` only as the far-field boundary condition, not as a CSS background.
- Do not modify the approved Boss, learning stars, links, single-system lab, formal scene, or course data.
- Stars remain stable and do not twinkle; only nearby dust receives subtle parallax.
- Do not run the project test suite; verification consists only of rendered visual frames.

---

### Task 1: Build the directional HDR sky laboratory

**Files:**
- Create: `frontend/space/cosmos-lab/index.html`

**Interfaces:**
- Consumes: `../assets/milky-way-eso-6000.jpg` as an equirectangular texture.
- Produces: `/trainer/space/cosmos-lab/?view=core` and `renderCosmos(milliseconds: number): void`.

- [ ] **Step 1: Create the standalone page and view controls**

Create a full-viewport WebGL2 canvas with minimal `core`, `rift`, and `deep` buttons. Load the ESO image into an anisotropically filtered sRGB texture and expose fixed yaw, pitch, roll, field-of-view, exposure, and volume parameters for each preset.

- [ ] **Step 2: Implement directional equirectangular sampling**

Build the camera ray from pixel coordinates and rotate it with the preset orientation. Convert the normalized direction to longitude and latitude, sample the panorama in linear color, and preserve horizontal wrapping without an equirectangular seam.

- [ ] **Step 3: Commit the directional far-field boundary**

```powershell
git add frontend/space/cosmos-lab/index.html
git commit -m "Build the directional cosmic sky laboratory"
```

### Task 2: Reconstruct galactic depth, dust, and stellar scale

**Files:**
- Modify: `frontend/space/cosmos-lab/index.html`

**Interfaces:**
- Consumes: camera direction, panorama luminance, preset density controls, and elapsed time.
- Produces: one HDR sky color containing far field, galactic volume, dust transmission, resolved stars, and near-field clouds.

- [ ] **Step 1: Add the galactic volume integral**

March twenty-four stratified samples through an inclined thin-disk density field. Use low-frequency 3D noise for large molecular structures, domain-warped high-frequency noise for torn filaments, and panorama luminance as a structural prior. Accumulate warm central emission and cool outer emission front-to-back.

- [ ] **Step 2: Add independent dark-dust transmission**

Integrate a second clumped density that reduces transmittance before adding deeper emission. Keep the extinction brown-black and spectrally restrained so it forms real obscuring rifts rather than gray painted stripes.

- [ ] **Step 3: Add stable analytic star layers**

Generate faint, medium, and rare bright stars from spherical direction hashes. Use a long-tail magnitude distribution, blackbody-like spectral colors, compact Gaussian point-spread functions, and restrained diffraction spikes only for the brightest tier.

- [ ] **Step 4: Add sparse local clouds and parallax**

Render only two low-density near fields with red H-alpha bias and faint blue reflection components. Offset those fields by a small pointer-driven parallax while keeping the far field and star sphere fixed.

- [ ] **Step 5: Add HDR post-processing**

Render to `RGBA16F`, extract high luminance at quarter and sixteenth resolution, blur each scale separately, and recombine before ACES-style mapping. Keep black space below the bloom threshold and add only sub-perceptual dithering.

- [ ] **Step 6: Commit the complete sky renderer**

```powershell
git add frontend/space/cosmos-lab/index.html
git commit -m "Render the volumetric cosmic sky remaster"
```

### Task 3: Produce the visual-only review frames

**Files:**
- Create outside the repository: `cosmic-sky-core.png`
- Create outside the repository: `cosmic-sky-rift.png`
- Create outside the repository: `cosmic-sky-deep.png`

**Interfaces:**
- Consumes: the three `cosmos-lab` presets.
- Produces: three actual browser-rendered images for direct visual acceptance.

- [ ] **Step 1: Capture all three presets**

Capture the page at `1600x1000` after the sky image and shaders are ready. Do not run tests, linters, builds, or unrelated diagnostics.

- [ ] **Step 2: Apply the visual rejection checklist**

Reject any frame that looks like a flat panorama, uniformly distributed particle field, saturated purple smoke, white Milky Way stripe, repeated noise, visible seam, stretched pole, twinkling stars, lifted gray blacks, or bloom-covered fine detail. Adjust only `cosmos-lab/index.html` parameters.

- [ ] **Step 3: Push the visual-proof branch**

```powershell
git push origin stellar-material-proof
```
