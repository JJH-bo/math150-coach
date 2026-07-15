# Unified World Camera Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make drag and wheel move one bounded orbital camera through a fixed world while preserving the accepted planet and Boss materials at every allowed viewpoint.

**Architecture:** `observatory-camera.mjs` owns the single camera pose, world projection, and Boss observer mapping. The galaxy compositor consumes that one frame for planets, routes, gravity lensing, cosmos orientation, and Boss placement; `boss-lab` receives only the ray-traced observer pose and renders the accepted material at sufficient resolution.

**Tech Stack:** JavaScript ES modules, Node.js built-in test runner, WebGL2/GLSL, embedded iframe canvas composition.

## Global Constraints

- Keep accepted planet, route, Boss, and cosmos shaders unchanged unless an expanded Boss boundary angle exposes a concrete defect.
- World objects never move because of input; only the camera state changes.
- Use yaw `-32deg..+32deg`, pitch `-16deg..+18deg`, distance `8.6..11.8`, and fixed `42deg` vertical FOV.
- Remove Boss screen pinning, screen clamps, focus state, and Boss-only scaling.
- Run only focused camera tests, script parsing, HTTP checks, and visual boundary inspection.

---

### Task 1: Replace mixed camera math with one world camera

**Files:**
- Modify: `frontend/space/galaxy-lab/observatory-camera.mjs`
- Test: `frontend/space/galaxy-lab/observatory-camera.test.mjs`

**Interfaces:**
- Produces: `createObservatoryCamera()` with `{yaw, pitch, distance}` current and target state.
- Produces: `createSceneFrame(camera, aspect)` with `camera.position`, projected world objects, and geometry-derived Boss observer data.

- [ ] **Step 1: Write failing tests for the expanded orbit and true dolly**

```js
test('camera uses expanded limits and a real dolly', () => {
  assert.equal(Math.round(OBSERVATORY_LIMITS.yaw[0] / DEG), -32);
  assert.equal(Math.round(OBSERVATORY_LIMITS.yaw[1] / DEG), 32);
  assert.equal(Math.round(OBSERVATORY_LIMITS.pitch[0] / DEG), -16);
  assert.equal(Math.round(OBSERVATORY_LIMITS.pitch[1] / DEG), 18);
  const camera = createObservatoryCamera();
  camera.dolly(-900);
  assert.equal(camera.target.distance, OBSERVATORY_LIMITS.distance[0]);
  assert.equal('focus' in camera.target, false);
});

test('Boss and planets share one projection', () => {
  const camera = createObservatoryCamera();
  Object.assign(camera.current, { yaw: 18 * DEG, pitch: 8 * DEG, distance: 9.2 });
  const frame = createSceneFrame(camera, 16 / 9);
  assert.deepEqual(frame.boss.center, frame.boss.projectedCenter);
  assert.equal(frame.planets.length, 12);
});

test('dolly changes the whole fixed scene', () => {
  const camera = createObservatoryCamera();
  const far = createSceneFrame(camera, 16 / 9);
  camera.current.distance = OBSERVATORY_LIMITS.distance[0];
  const near = createSceneFrame(camera, 16 / 9);
  assert.notDeepEqual(near.planets.map((p) => p.radius), far.planets.map((p) => p.radius));
  assert.ok(near.boss.distance < far.boss.distance);
  assert.ok(near.boss.lensRadius > far.boss.lensRadius);
});

test('Boss observer comes from shared camera position', () => {
  const camera = createObservatoryCamera();
  const base = createSceneFrame(camera, 16 / 9);
  Object.assign(camera.current, { yaw: 32 * DEG, pitch: 18 * DEG });
  const edge = createSceneFrame(camera, 16 / 9);
  assert.ok(Math.abs(edge.boss.viewAzimuth - base.boss.viewAzimuth) > 20 * DEG);
  assert.ok(edge.boss.viewInclination > base.boss.viewInclination + 10 * DEG);
});
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run: `node --test frontend/space/galaxy-lab/observatory-camera.test.mjs`

Expected: failures for old limits, unchanged distance, focus state, and pinned Boss center.

- [ ] **Step 3: Implement the shared camera**

Use these rules:

```js
export const OBSERVATORY_LIMITS = Object.freeze({
  yaw: Object.freeze([-32 * DEG, 32 * DEG]),
  pitch: Object.freeze([-16 * DEG, 18 * DEG]),
  distance: Object.freeze([8.6, 11.8]),
});
const DEFAULT_STATE = Object.freeze({ yaw: 0, pitch: 0.5 * DEG, distance: 10 });
const CAMERA_TARGET = Object.freeze([0, 0, -0.2]);

// True wheel dolly.
target.distance = clamp(target.distance + deltaY * 0.0024,
  ...OBSERVATORY_LIMITS.distance);

// Natural projection.
const bossCenter = bossProjection.point;
```

Build the camera position as a spherical offset around `CAMERA_TARGET`, then look back at that target. Remove `focus`, `baseBossX`, `bossOffset`, terminal-route screen offsets, and the yaw-to-inclination art formula.

Derive Boss azimuth and elevation from the normalized vector from `BOSS_WORLD` to the camera. Express them as deltas from the default vector, add them to the accepted default Boss pose (`0deg`, `20.2deg`), and map camera-to-Boss distance through the existing start-radius curve to `observerRadiusIndex`.

- [ ] **Step 4: Run tests and confirm GREEN**

Run: `node --test frontend/space/galaxy-lab/observatory-camera.test.mjs`

Expected: all camera tests pass.

- [ ] **Step 5: Commit**

```powershell
git add -- frontend/space/galaxy-lab/observatory-camera.mjs frontend/space/galaxy-lab/observatory-camera.test.mjs
git commit -m "Unify observatory world camera"
```

---

### Task 2: Synchronize every visual layer

**Files:**
- Modify: `frontend/space/galaxy-lab/index.html`
- Modify only if needed: `frontend/space/cosmos-lab/index.html`
- Test: `frontend/space/galaxy-lab/observatory-camera.test.mjs`

**Interfaces:**
- Consumes: shared camera snapshot and Boss frame from Task 1.
- Produces: one animation-frame update path for cosmos, Boss, routes, lensing, and planets.

- [ ] **Step 1: Add a failing source-contract test**

```js
const galaxySource = readFileSync(new URL('./index.html', import.meta.url), 'utf8');
assert.equal(galaxySource.includes('snapshot.focus'), false);
assert.equal(galaxySource.includes('Boss焦点'), false);
assert.equal(galaxySource.includes('sceneFrame.boss.observerRadiusIndex'), true);
```

- [ ] **Step 2: Run the test and confirm RED**

Run: `node --test frontend/space/galaxy-lab/observatory-camera.test.mjs`

Expected: FAIL because the page still consumes and displays `focus`.

- [ ] **Step 3: Replace focus composition with shared-frame composition**

Show `distance` in the HUD. Send `viewAzimuth`, `viewInclination`, and `observerRadiusIndex` to `bossObservatory.setState()` in the same animation callback used to update cosmos and the galaxy frame.

Draw the Boss source around `sceneFrame.boss.center` without clamping it to a screen region. Use a calibrated constant overscan composite scale while distance-dependent angular size comes from the ray-traced observer radius. Drive gravity-lens size and route influence from `sceneFrame.boss.lensRadius`. Replace the legend with `拖动有限轨道观察 · 滚轮移动观察距离 · 双击复位`.

- [ ] **Step 4: Run focused tests**

Run: `node --test frontend/space/galaxy-lab/observatory-camera.test.mjs`

Expected: all tests pass.

- [ ] **Step 5: Parse executable scripts**

Run the local Node `vm.Script` extraction check for `galaxy-lab/index.html`, `boss-lab/index.html`, and `cosmos-lab/index.html`.

Expected: every executable script parses; the galaxy module parses after removing its import declaration.

- [ ] **Step 6: Commit**

```powershell
git add -- frontend/space/galaxy-lab/index.html frontend/space/cosmos-lab/index.html
git commit -m "Synchronize observatory visual layers"
```

---

### Task 3: Expand and harden the Boss observer envelope

**Files:**
- Modify: `frontend/space/boss-lab/index.html`
- Modify only if a boundary defect is observed: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Consumes: `{azimuth, inclination, radiusIndex}` from the shared frame.
- Produces: stable ray-traced Boss output across expanded camera limits.

- [ ] **Step 1: Expand the Boss bridge without changing materials**

Accept geometry-derived azimuth bounded to `-34deg..+34deg` and inclination `3deg..38deg`. Retain `0.02deg` azimuth quantization, existing model-value conversion, and one `model.updateDerivedValues()` per changed state.

- [ ] **Step 2: Add embedded render-resolution scaling**

Add `CameraView.setEmbeddedRenderScale(value)`, clamped to `1..1.5`. Multiply backing canvas width and height by the scale while keeping CSS dimensions unchanged. Expose `bossObservatory.setRenderScale(value)` and call it once from the galaxy compositor. This changes sampling resolution only, not material or camera geometry.

- [ ] **Step 3: Inspect default and boundary poses**

Open `http://127.0.0.1:4173/space/galaxy-lab/`. Inspect default, yaw `-32/+32`, pitch `-16/+18`, the four yaw/pitch corners, and distance `8.6/11.8`.

Expected: no white blocks, missing disc surfaces, crop seams, iframe edges, low-resolution enlargement, screen-frozen layer, or disagreement between Boss and lensing.

- [ ] **Step 4: Correct only defects exposed by expanded angles**

First enlarge Boss source overscan or backing resolution. Only if the ray-traced model itself clips, adjust embedded framing or radius mapping. Do not change disc density, opacity, temperature, exposure, bloom, planet shaders, or layout.

- [ ] **Step 5: Run focused completion checks**

```powershell
node --test frontend/space/galaxy-lab/observatory-camera.test.mjs
git diff --check
Invoke-WebRequest http://127.0.0.1:4173/space/galaxy-lab/ -UseBasicParsing
Invoke-WebRequest 'http://127.0.0.1:4173/space/boss-lab/?view=far&embed=1' -UseBasicParsing
```

Expected: tests pass, no whitespace errors, and both entries return HTTP 200.

- [ ] **Step 6: Commit and push**

```powershell
git add -- frontend/space/boss-lab/index.html frontend/space/galaxy-lab/index.html frontend/space/galaxy-lab/observatory-camera.mjs frontend/space/galaxy-lab/observatory-camera.test.mjs
git commit -m "Harden expanded Boss observation"
git push
```

