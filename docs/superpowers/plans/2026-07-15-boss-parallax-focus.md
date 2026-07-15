# Boss Parallax and Focus Dolly Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the Boss a safe real ray-traced viewpoint response while replacing global camera dolly with a Boss-only focus advance that leaves planet scale stable.

**Architecture:** `observatory-camera.mjs` owns a damped `focus` state and maps the full fan camera angle into a compressed Boss observer state. `boss-lab` exposes one embedded observer API that updates the ray-traced observer coordinates without recompiling shaders. `galaxy-lab` passes the shared frame to the Boss, sky lens, route field, and infall field.

**Tech Stack:** Native JavaScript ES modules, Node built-in test runner, WebGL2, GLSL ES 3.00, Canvas 2D composition

## Global Constraints

- Preserve planet world positions, projected radii, and material functions.
- Outer camera remains yaw `±24°` and pitch `-12°–14°`.
- Boss observer azimuth is limited to `±9°`; inclination is limited to approximately `14°–27°`.
- Wheel controls `focus` in `0–1`, default `0.28`; it does not change camera distance.
- Boss optical scale is `1.42–2.00`; default remains approximately `1.58`.
- No full project test suite, new WebGL context, free flight, or node interaction.

---

### Task 1: Damped Focus and Safe Boss View Mapping

**Files:**
- Modify: `frontend/space/galaxy-lab/observatory-camera.mjs`
- Modify: `frontend/space/galaxy-lab/observatory-camera.test.mjs`

**Interfaces:**
- Produces: `camera.current.focus`, `camera.target.focus`, and `sceneFrame.boss.viewAzimuth`, `viewInclination`, `focus`, `observerRadiusIndex`.

- [ ] **Step 1: Add failing focus and scale-isolation tests**

```js
test('wheel advances Boss focus without changing planet projection scale', () => {
  const camera = createObservatoryCamera();
  const initialDistance = camera.target.distance;
  const farFrame = createSceneFrame(camera, 16 / 9);
  camera.dolly(-900);
  assert.equal(camera.target.distance, initialDistance);
  assert.ok(camera.target.focus > camera.current.focus);
  camera.current.focus = 1;
  const closeFrame = createSceneFrame(camera, 16 / 9);
  assert.equal(closeFrame.boss.scale, 2);
  assert.deepEqual(
    closeFrame.planets.map((planet) => planet.radius),
    farFrame.planets.map((planet) => planet.radius),
  );
});

test('fan angles map into the safe real Boss observer envelope', () => {
  const camera = createObservatoryCamera();
  Object.assign(camera.current, {
    yaw: OBSERVATORY_LIMITS.yaw[1],
    pitch: OBSERVATORY_LIMITS.pitch[1],
  });
  const frame = createSceneFrame(camera, 16 / 9);
  assert.equal(Math.round(frame.boss.viewAzimuth / DEG), 9);
  assert.ok(frame.boss.viewInclination / DEG <= 27.3);
  assert.ok(frame.boss.viewInclination / DEG >= 27.0);
});
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run `node --test frontend/space/galaxy-lab/observatory-camera.test.mjs`.

Expected: FAIL because `focus`, `viewAzimuth`, and `viewInclination` do not exist and dolly changes distance.

- [ ] **Step 3: Implement focus and observer mapping**

```js
const DEFAULT_STATE = Object.freeze({ yaw: 0, pitch: 0.5 * DEG, distance: 10, focus: 0.28 });

dolly(deltaY) {
  target.focus = clamp(target.focus - deltaY * 0.00072, 0, 1);
},

const focus = clamp(camera.current.focus ?? 0.28, 0, 1);
const bossScale = 1.42 + focus * 0.58;
const viewAzimuth = clamp(camera.current.yaw * 0.375, -9 * DEG, 9 * DEG);
const viewInclination = clamp(20.2 * DEG + camera.current.pitch * 0.5, 14 * DEG, 27.3 * DEG);
const observerRadiusIndex = Math.round(620 - (focus - 0.28) * 42);
```

Interpolate `current.focus` in `update()` and expose it from `snapshot()`.

- [ ] **Step 4: Run the focused tests and verify GREEN**

Expected: all focused tests pass with no failures.

### Task 2: Embedded Ray-Traced Boss Observer API

**Files:**
- Modify: `frontend/space/boss-lab/index.html`
- Modify: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Produces: `window.bossObservatory.setState({ azimuth, inclination, radiusIndex })`.
- Consumes: `sceneFrame.boss.viewAzimuth`, `viewInclination`, and `observerRadiusIndex`.

- [ ] **Step 1: Add a real observer azimuth to the Boss model**

Initialize `this.observatoryAzimuth = 0` in `Model`. In `updateCameraCoordinates()`, use:

```js
const observerPhi = this.phi + this.observatoryAzimuth;
const cphi = Math.cos(observerPhi);
const sphi = Math.sin(observerPhi);
```

This changes the ray-traced observer coordinates instead of rotating the composed canvas.

- [ ] **Step 2: Expose one batched embedded API**

After applying the default preset, expose:

```js
const BOSS_DEG = Math.PI / 180;
window.bossObservatory = {
  setState({ azimuth = 0, inclination = 20.2 * Math.PI / 180, radiusIndex = 620 } = {}) {
    model.observatoryAzimuth = Math.max(-9 * BOSS_DEG, Math.min(9 * BOSS_DEG, azimuth));
    model.orbitInclination.index = Math.max(0, Math.min(1799,
      Math.round((inclination / Math.PI + 0.5) * 1799)));
    model.startRadius.index = Math.max(0, Math.min(1000, Math.round(radiusIndex)));
    model.updateDerivedValues();
  },
};
```

Update only when the quantized state changes so idle frames do no extra derived-value work.

- [ ] **Step 3: Pass the shared frame before each Boss render**

```js
bossFrame.contentWindow?.bossObservatory?.setState?.({
  azimuth: sceneFrame.boss.viewAzimuth,
  inclination: sceneFrame.boss.viewInclination,
  radiusIndex: sceneFrame.boss.observerRadiusIndex,
});
```

Call this immediately before `bossView.onRender()`.

### Task 3: Focus-Synchronized Environment Envelope

**Files:**
- Modify: `frontend/space/galaxy-lab/observatory-camera.mjs`
- Modify: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Consumes: `bossData.z` optical scale already uploaded to the system shader.
- Produces: focus-scaled lens, infall envelope, route gravity envelope, and Boss boundary drift.

- [ ] **Step 1: Shift the Boss anchor slightly with focus**

Use `baseBossX = aspect * (0.76 + focus * 0.04)`, which moves the center from roughly `88%` to `90%` screen width while leaving system projection unchanged.

- [ ] **Step 2: Scale the system-shader gravity envelope**

```glsl
float opticalFocus = clamp(bossData.z / 1.58, 0.86, 1.28);
float bossDistance = length((p - boss) * vec2(1.0, 0.82)) / opticalFocus;
```

Apply the same `opticalFocus` divisor to `bossRadius` in the spiral infall calculation. Lens radius and strength already derive from `bossScale` in the shared frame.

- [ ] **Step 3: Run targeted verification**

Run:

```powershell
& $node --test frontend/space/galaxy-lab/observatory-camera.test.mjs
git diff --check
```

Expected: all focused tests pass; no whitespace errors. Do not run the full project suite.

- [ ] **Step 4: Commit and push**

```powershell
git add frontend/space/galaxy-lab/observatory-camera.mjs frontend/space/galaxy-lab/observatory-camera.test.mjs frontend/space/galaxy-lab/index.html frontend/space/boss-lab/index.html docs/superpowers/plans/2026-07-15-boss-parallax-focus.md
git commit -m "Synchronize Boss parallax and focus"
git push origin stellar-material-proof
```

## Self-Review

- Spec coverage: real compressed Boss view, static planet scale during wheel focus, Boss-only scale, internal observer radius, shared lens/infall/routes, and unchanged interaction scope are assigned.
- Placeholder scan: no deferred markers or undefined implementation steps remain.
- Interface consistency: `createSceneFrame()` remains the only shared state producer, and every consumer reads the same `sceneFrame.boss` fields.
