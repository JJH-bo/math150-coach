# Black-Hole-Centered Fan Camera Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the affine screen viewer with a bounded perspective camera orbiting the Boss black hole.

**Architecture:** `observatory-camera.mjs` owns one spherical orbit pose and projects immutable world anchors. `galaxy-lab/index.html` forwards the same pose to the cosmos and Boss renderers while keeping approved material code untouched.

**Tech Stack:** JavaScript ES modules, Node.js test runner, WebGL2/GLSL, iframe canvas composition.

## Global Constraints

- Do not change accepted planet, route, Boss, or cosmos material shaders.
- `BOSS_WORLD` is the only orbit pivot.
- Object world coordinates never depend on input.
- Use azimuth `-30deg..+30deg`, elevation `-15deg..+17deg`, and radius `9.4..18.0`.

---

### Task 1: Replace affine camera with Boss-centered orbit

**Files:**
- Modify: `frontend/space/galaxy-lab/observatory-camera.mjs`
- Test: `frontend/space/galaxy-lab/observatory-camera.test.mjs`

**Interfaces:**
- Produces: `createObservatoryCamera()` state `{azimuth, elevation, radius}` and methods `orbit()`, `dolly()`, `setState()`, `reset()`.
- Produces: `createSceneFrame()` with immutable world points and shared perspective projections.

- [ ] **Step 1: Write failing orbit tests**

Assert that camera-to-Boss distance equals `radius`, the camera forward vector points at the Boss, Boss projection remains stable, world anchors remain unchanged, and changing azimuth produces non-rigid perspective motion.

- [ ] **Step 2: Run focused tests and confirm RED**

Run the bundled Node executable with `--test frontend/space/galaxy-lab/observatory-camera.test.mjs`.

- [ ] **Step 3: Implement the spherical camera**

```js
const position = add(BOSS_WORLD, [
  Math.sin(azimuth) * Math.cos(elevation) * radius,
  Math.sin(elevation) * radius,
  Math.cos(azimuth) * Math.cos(elevation) * radius,
]);
const forward = normalize(subtract(BOSS_WORLD, position));
```

Project every immutable world point with this basis and one fixed composition offset.

- [ ] **Step 4: Run focused tests and confirm GREEN**

Expected: orbit, dolly, world immutability, Boss observer, and default composition assertions pass.

### Task 2: Synchronize interaction and cosmos orientation

**Files:**
- Modify: `frontend/space/galaxy-lab/index.html`
- Modify: `frontend/space/cosmos-lab/index.html`
- Test: `frontend/space/galaxy-lab/observatory-camera.test.mjs`

**Interfaces:**
- Consumes: `{azimuth, elevation, radius}`.
- Produces: drag-to-orbit, wheel-to-dolly, shared sky orientation, neutral affine sky transform.

- [ ] **Step 1: Add failing source-contract assertions**

Require `observatory.orbit`, `observatory.dolly`, and `cosmosCamera.setObservatory`; forbid `observatory.pan`, `observatory.zoom`, and `setViewportTransform` in the galaxy compositor.

- [ ] **Step 2: Run focused tests and confirm RED**

Expected: current affine controls violate the contract.

- [ ] **Step 3: Rewire input and embedded layers**

Forward orbit orientation to the cosmos, keep the viewport transform at identity, and continue sending the shared Boss projection and lens data in the same animation frame.

- [ ] **Step 4: Run focused tests and commit**

Run the camera test file, check the diff for whitespace errors, and commit only the spec, plan, camera, compositor, cosmos, and focused test files.

