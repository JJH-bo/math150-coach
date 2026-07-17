# Single-System Visual Remaster Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one isolated visual proof containing four living learning stars, five field-rendered connections, and the approved relativistic Boss black hole.

**Architecture:** Keep `boss-lab` as the unchanged physical black-hole renderer in a full-viewport base iframe. Add one transparent WebGL2 HDR canvas above it that renders the four implicit stars, connection density fields, lensing-adjacent terminal route, local dust, bloom, and tone mapping in a single visual layer.

**Tech Stack:** HTML, CSS, JavaScript, WebGL2, GLSL ES 3.00, RGBA16F render targets, procedural 3D noise, signed-distance Bézier fields, premultiplied-alpha compositing.

## Global Constraints

- Render exactly four ordinary learning stars and exactly one approved Boss.
- Use the fixed split-and-merge topology with five routes.
- Do not modify the Boss shader, course data, main knowledge scene, navigation, or business behavior.
- Do not use `TubeGeometry`, PBR spheres, bitmap star surfaces, or evenly spaced particle chains.
- Do not run project tests; review only the produced visual frames.

---

### Task 1: Compose the approved Boss and the new system layer

**Files:**
- Create: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Consumes: `../boss-lab/?view=far` as the already approved physical renderer.
- Produces: `/trainer/space/galaxy-lab/?view=overview` as the visual-review entry point.

- [ ] **Step 1: Build the isolated page shell**

Create a full-viewport page with `#boss-layer` as the bottom iframe, `#system-layer` as a transparent WebGL2 canvas, and a minimal HUD containing `overview`, `links`, and `ingress` view buttons. Give the iframe a wider viewport so its physical black hole sits in the right sector without re-rendering or approximating it.

- [ ] **Step 2: Preserve Boss ownership of the right half**

On the iframe `load` event, hide only its laboratory HUD and settings controls through same-origin DOM access. Do not alter `BlackHoleShaderDemoApp`, its shaders, lookup textures, camera model, or bloom implementation.

- [ ] **Step 3: Commit the composition boundary**

```powershell
git add frontend/space/galaxy-lab/index.html
git commit -m "Compose the single-system visual laboratory"
```

### Task 2: Render four living stars and five field connections

**Files:**
- Modify: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Consumes: normalized scene coordinates and the selected view preset.
- Produces: `renderSystem(seconds: number): void`, a transparent HDR frame over the Boss.

- [ ] **Step 1: Add the implicit-star GLSL field**

Implement analytic ray-sphere intersection for four stars. Reuse the accepted material language: domain-warped multi-octave 3D noise, evolving convection, dark magnetic regions, center-to-limb darkening, a thin chromosphere, asymmetric corona, and per-star seed/temperature variation.

- [ ] **Step 2: Add the Bézier distance-field network**

Implement a fixed eight-sample closest-distance estimate for cubic Bézier curves. Define the five routes `entry-upper`, `entry-lower`, `upper-merge`, `lower-merge`, and `merge-boss`, using one wide disrupted density field plus multiple phase-shifted fine fields per route.

- [ ] **Step 3: Add directional pulses and Boss ingress**

Drive sparse pulse groups with the curve parameter. Split pulse phase at the entry node, merge it at the terminal node, and apply inverse-distance angular deflection to the terminal route near the Boss. Add a faint secondary arc and mask all connection emission inside the event-horizon region.

- [ ] **Step 4: Add HDR compositing**

Render the system layer into `RGBA16F`, extract only high emission into quarter-resolution targets, apply separable blur, combine with ACES-style tone mapping, and output premultiplied alpha so the original Boss remains visible and sharp.

- [ ] **Step 5: Commit the completed field renderer**

```powershell
git add frontend/space/galaxy-lab/index.html
git commit -m "Render the remastered stellar system links"
```

### Task 3: Produce the visual review result

**Files:**
- Create outside the repository: `single-system-overview.png`
- Create outside the repository: `single-system-links.png`
- Create outside the repository: `single-system-ingress.png`

**Interfaces:**
- Consumes: `/trainer/space/galaxy-lab/` view presets.
- Produces: three actual rendered frames for direct visual judgment.

- [ ] **Step 1: Capture the three views**

Open the lab at a `1600x1000` viewport and capture `?view=overview`, `?view=links`, and `?view=ingress`. Wait only for the Boss loading panel to clear and for the shader animation to settle; do not run the project test suite.

- [ ] **Step 2: Visually reject regressions**

Reject the frame if the four stars form a line, any connection has a uniform tube edge, any route crosses the event horizon, the stars regain plastic highlights, or the Boss ceases to be the first focal point. Adjust only visual parameters in `galaxy-lab/index.html`.

- [ ] **Step 3: Push the review branch**

```powershell
git push origin stellar-material-proof
```
