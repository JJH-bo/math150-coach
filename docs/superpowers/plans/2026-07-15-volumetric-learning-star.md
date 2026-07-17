# Volumetric Learning Star Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build one isolated, shader-generated ordinary learning star whose material quality can be judged without the knowledge scene.

**Architecture:** Add a self-contained WebGL2 laboratory under `frontend/space/stellar-lab/`. A full-screen implicit-star shader produces the photosphere and atmospheric light field in HDR; two reduced-resolution passes provide selective bloom before final ACES-style tone mapping.

**Tech Stack:** HTML, CSS, JavaScript, WebGL2, GLSL ES 3.00, floating-point framebuffers.

## Global Constraints

- Render exactly one ordinary learning star.
- Do not modify `stellar-renderer.js`, the Boss, routes, knowledge data, or gameplay.
- Do not use conventional PBR sphere materials, bitmap surface textures, transparent sphere stacks, or tube prominences.
- Do not run project tests during this visual approval pass.
- Stop at the independent visual proof and request direct visual approval.

---

### Task 1: Build The Isolated Volumetric Star Laboratory

**Files:**
- Create: `frontend/space/stellar-lab/index.html`

**Interfaces:**
- Consumes: the backend's existing static `/trainer/space/` file serving.
- Produces: `/trainer/space/stellar-lab/?view=standard|close|limb`.

- [ ] **Step 1: Create the full-screen laboratory shell**

Add a full-viewport canvas, minimal view controls, WebGL2 capability message, drag rotation, and wheel scale. Keep all UI outside the rendered image and do not add knowledge-scene controls.

- [ ] **Step 2: Implement the implicit photosphere shader**

Use analytic ray/sphere intersection. Evaluate animated 3D cellular granulation, intergranular lanes, large convection, differential flow, two irregular active regions, faculae, and center-to-limb darkening from the intersection normal. Generate HDR emission directly; do not use a mesh surface or texture lookup.

- [ ] **Step 3: Implement the continuous atmosphere**

Evaluate chromosphere density from closest ray approach and procedural turbulence. Add anisotropic corona streamers and radial fibers with large dark gaps. Add multiple signed-distance prominence arcs with tapered filamentary interiors rooted at the limb.

- [ ] **Step 4: Implement HDR bloom and tone mapping**

Render the scene into `RGBA16F`, extract only luminance above the hot-emission threshold, apply horizontal and vertical half-resolution Gaussian blur, then combine with the source through ACES-style tone mapping and gamma correction.

- [ ] **Step 5: Add three visual presets**

`standard` shows the full corona, `close` fills most of the frame with the photosphere, and `limb` shifts the star so chromosphere and prominence attachment are easy to inspect. Query parameters and buttons select the same preset values.

- [ ] **Step 6: Produce visual-review captures**

Capture the three preset views after the procedural field has stabilized. This is product output for human visual review, not an automated test run.

- [ ] **Step 7: Commit the isolated proof**

```powershell
$git = 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe'
& $git add -- docs/superpowers/specs/2026-07-15-volumetric-learning-star-design.md docs/superpowers/plans/2026-07-15-volumetric-learning-star.md frontend/space/stellar-lab/index.html
& $git commit -m 'Render the volumetric learning star proof'
& $git push origin stellar-material-proof
```
