# Observatory World Scale and Trajectory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all three learning systems behave as fixed three-dimensional world objects and expand true dolly travel from the accepted Boss-pressure view to a complete chapter overview.

**Architecture:** Keep the existing single orbital camera and perspective projection. Rebuild only the fixed system center/depth data, then make the Boss compositor consume the same depth-derived scale already calculated by `createSceneFrame`; no camera-state-dependent object compensation or FOV change is allowed.

**Tech Stack:** Browser ES modules, JavaScript, WebGL2 compositor, Canvas 2D Boss composite, Node.js built-in test runner.

## Global Constraints

- Keep the accepted Boss model, ray-traced appearance, accretion-disc treatment, planet material, routes, and cosmos appearance unchanged.
- Keep yaw at `-32deg..+32deg`, pitch at `-16deg..+18deg`, minimum distance at `8.6`, default distance at `10.0`, and field of view at `42deg`.
- At the farthest default-angle view, all three complete systems and the complete Boss must fit with at least a 3% viewport margin; the Boss must occupy 35% to 45% of viewport height.
- Every system must remain fixed in world space. Drag and dolly may change only camera state.
- Every system must achieve at least `0.06` normalized-screen midpoint curvature, `12%` projected-width change, and `8%` camera-depth radius difference across the accepted yaw envelope.
- Do not add interactions, systems, materials, FOV compensation, object-scale compensation, or screen-space anchoring.
- Run only the focused camera test and boundary visual checks described below; do not run unrelated full-project validation.

---

### Task 1: Give every system a measurable fixed-world trajectory

**Files:**
- Modify: `frontend/space/galaxy-lab/observatory-camera.test.mjs`
- Modify: `frontend/space/galaxy-lab/observatory-camera.mjs`

**Interfaces:**
- Consumes: `createObservatoryCamera()` and `createSceneFrame(camera, aspect)`.
- Produces: fixed system projection data; the private `depthScale: number` is used only during world-point construction and is not added to the returned frame.

- [ ] **Step 1: Add reusable projection measurements to the focused test file**

Add these helpers after `const DEG = Math.PI / 180;`:

```js
function frameAt({ yaw = 0, pitch = 0.5, distance = 10 } = {}) {
  const camera = createObservatoryCamera();
  camera.setState({ yaw: yaw * DEG, pitch: pitch * DEG, distance }, true);
  return createSceneFrame(camera, 16 / 9);
}

const systemPlanets = (frame, systemIndex) =>
  frame.planets.slice(systemIndex * 4, systemIndex * 4 + 4);

const projectedWidth = (frame, systemIndex) => {
  const xs = systemPlanets(frame, systemIndex).map((planet) => planet.center[0]);
  return Math.max(...xs) - Math.min(...xs);
};

const midpointCurvature = (left, center, right, systemIndex) => {
  const a = left.systems[systemIndex].center;
  const m = center.systems[systemIndex].center;
  const b = right.systems[systemIndex].center;
  return Math.hypot(m[0] - (a[0] + b[0]) * 0.5, m[1] - (a[1] + b[1]) * 0.5);
};

const depthRadiusSpread = (frame, systemIndex) => {
  const radii = systemPlanets(frame, systemIndex).map((planet) => planet.radius);
  return Math.max(...radii) / Math.min(...radii) - 1;
};
```

- [ ] **Step 2: Write the failing trajectory test**

Append this test before the compositor source tests:

```js
test('all systems reveal curved fixed-world motion and internal depth', () => {
  const left = frameAt({ yaw: -32 });
  const center = frameAt();
  const right = frameAt({ yaw: 32 });

  for (let systemIndex = 0; systemIndex < 3; systemIndex += 1) {
    const curvature = midpointCurvature(left, center, right, systemIndex);
    const leftWidth = projectedWidth(left, systemIndex);
    const rightWidth = projectedWidth(right, systemIndex);
    const widthChange = Math.abs(rightWidth - leftWidth) / Math.max(leftWidth, rightWidth);
    const radiusSpread = Math.max(
      depthRadiusSpread(left, systemIndex),
      depthRadiusSpread(right, systemIndex),
    );

    assert.ok(curvature >= 0.06, `system ${systemIndex} curvature ${curvature}`);
    assert.ok(widthChange >= 0.12, `system ${systemIndex} width change ${widthChange}`);
    assert.ok(radiusSpread >= 0.08, `system ${systemIndex} radius spread ${radiusSpread}`);
  }
});
```

- [ ] **Step 3: Run the focused test and verify the current false-motion layout fails**

Run:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test frontend/space/galaxy-lab/observatory-camera.test.mjs
```

Expected: FAIL in `all systems reveal curved fixed-world motion and internal depth`; system 1 reports curvature below `0.06` and width change below `0.12`, and system 2 reports curvature below `0.06`.

- [ ] **Step 4: Replace the thin-card system layout with fixed three-dimensional data**

In `observatory-camera.mjs`, keep the lower-left system's existing center and rotation, move only the two rejected systems, and add fixed depth multipliers:

```js
const CAMERA_TARGET = Object.freeze([-0.20, 0, -0.25]);

const SYSTEMS = Object.freeze([
  Object.freeze({ center: [-3.30, -0.78, 1.22], rotation: [-10, -7, 8], depthScale: 1.0, energy: 1.00, seed: 1.3 }),
  Object.freeze({ center: [-2.15, 1.75, -0.15], rotation: [18, 28, -8], depthScale: 3.2, energy: 0.82, seed: 5.2 }),
  Object.freeze({ center: [-2.60, -1.75, -0.90], rotation: [-22, -31, 12], depthScale: 3.4, energy: 0.66, seed: 9.4 }),
]);
```

Replace the `worldPlanets` construction inside `createSceneFrame` with:

```js
const worldPlanets = LOCAL_PLANETS.map((planet) => {
  const volumetricPoint = [
    planet.point[0],
    planet.point[1],
    planet.point[2] * system.depthScale,
  ];
  return add(system.center, rotatePoint(volumetricPoint, system.rotation));
});
```

Do not change `LOCAL_PLANETS`, planet radii, route topology, material uniforms, or any camera-input handler.

- [ ] **Step 5: Run the focused test and verify the trajectory contract passes**

Run:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test frontend/space/galaxy-lab/observatory-camera.test.mjs
```

Expected: PASS for every test, including all three curvature/width/radius thresholds.

- [ ] **Step 6: Commit the fixed-world trajectory change**

```powershell
git add frontend/space/galaxy-lab/observatory-camera.mjs frontend/space/galaxy-lab/observatory-camera.test.mjs
git commit -m "Fix learning system world trajectories"
```

### Task 2: Expand true dolly and synchronize Boss projected scale

**Files:**
- Modify: `frontend/space/galaxy-lab/observatory-camera.test.mjs`
- Modify: `frontend/space/galaxy-lab/observatory-camera.mjs`
- Modify: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Consumes: `sceneFrame.boss.scale`, already calculated from the shared camera-to-Boss distance.
- Produces: `OBSERVATORY_LIMITS.distance === [8.6, 15.6]`; the Canvas 2D compositor uses `sceneFrame.boss.scale` for both destination dimensions.

- [ ] **Step 1: Write failing tests for the expanded overview and physical Boss scaling**

Extend the first camera-limit test with:

```js
assert.equal(OBSERVATORY_LIMITS.distance[0], 8.6);
assert.equal(OBSERVATORY_LIMITS.distance[1], 15.6);
```

Add these tests before the source-inspection tests:

```js
test('far dolly fits every complete learning planet inside a three percent margin', () => {
  const aspect = 16 / 9;
  const far = frameAt({ distance: OBSERVATORY_LIMITS.distance[1] });
  const horizontalLimit = aspect * 0.94;
  const verticalLimit = 0.94;

  far.planets.forEach((planet, planetIndex) => {
    assert.ok(planet.center[0] - planet.radius >= -horizontalLimit, `planet ${planetIndex} left`);
    assert.ok(planet.center[0] + planet.radius <= horizontalLimit, `planet ${planetIndex} right`);
    assert.ok(planet.center[1] - planet.radius >= -verticalLimit, `planet ${planetIndex} bottom`);
    assert.ok(planet.center[1] + planet.radius <= verticalLimit, `planet ${planetIndex} top`);
  });
});

test('dolly changes the Boss projected composite scale', () => {
  const near = frameAt({ distance: OBSERVATORY_LIMITS.distance[0] });
  const far = frameAt({ distance: OBSERVATORY_LIMITS.distance[1] });

  assert.ok(near.boss.scale > far.boss.scale * 1.35);
});
```

Replace the fixed-composite assertions in `galaxy compositor has no Boss-only focus camera path` with:

```js
assert.equal(galaxySource.includes('sceneFrame.boss.compositeScale'), false);
assert.equal(galaxySource.includes('sceneFrame.boss.scale'), true);
```

- [ ] **Step 2: Run the focused test and verify the old maximum distance and fixed compositor fail**

Run:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test frontend/space/galaxy-lab/observatory-camera.test.mjs
```

Expected: FAIL because the maximum distance is still `11.8` and `index.html` still sizes the Boss with `sceneFrame.boss.compositeScale`.

- [ ] **Step 3: Expand only the real camera distance**

Change the distance limit in `observatory-camera.mjs`:

```js
export const OBSERVATORY_LIMITS = Object.freeze({
  yaw: Object.freeze([-32 * DEG, 32 * DEG]),
  pitch: Object.freeze([-16 * DEG, 18 * DEG]),
  distance: Object.freeze([8.6, 15.6]),
});
```

Keep `DEFAULT_STATE.distance` at `10.0` and keep `FOV` at `42 * DEG`.

- [ ] **Step 4: Make the Boss canvas use its shared-camera projected scale**

In `index.html`, replace both fixed destination scale expressions:

```js
const destinationWidth = Math.round(
  bossFrame.clientWidth * dpr * sceneFrame.boss.scale
);
const destinationHeight = Math.round(
  bossFrame.clientHeight * dpr * sceneFrame.boss.scale
);
```

In the returned `boss` object in `createSceneFrame`, remove the obsolete `compositeScale: BOSS_COMPOSITE_SCALE` field. Keep `scale: bossScale`; `BOSS_COMPOSITE_SCALE` remains the accepted default-scale calibration used by the depth formula.

- [ ] **Step 5: Run the focused test and verify physical dolly passes**

Run:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test frontend/space/galaxy-lab/observatory-camera.test.mjs
```

Expected: PASS. The near view retains the default calibration, the far view fits every planet with margin, and the Boss compositor source uses only `sceneFrame.boss.scale`.

- [ ] **Step 6: Commit the true-dolly overview change**

```powershell
git add frontend/space/galaxy-lab/observatory-camera.mjs frontend/space/galaxy-lab/observatory-camera.test.mjs frontend/space/galaxy-lab/index.html
git commit -m "Expand observatory chapter overview"
```

### Task 3: Perform the focused visual acceptance pass

**Files:**
- Modify only if boundary inspection requires numeric tuning: `frontend/space/galaxy-lab/observatory-camera.mjs`

**Interfaces:**
- Consumes: `window.observatoryCamera.setImmediate({ yaw, pitch, distance })` from `index.html`.
- Produces: an accepted bounded camera envelope with no screen-following systems, Boss crop defects, detached routes, or material regressions.

- [ ] **Step 1: Start or reuse the local static server**

First check the existing endpoint:

```powershell
Invoke-WebRequest 'http://127.0.0.1:4173/space/galaxy-lab/' -UseBasicParsing
```

If it is unavailable, start the workspace server without opening a visible terminal window:

```powershell
Start-Process -FilePath 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -ArgumentList '-m','http.server','4173','--directory','frontend' -WorkingDirectory 'C:\Users\jjh\OneDrive\文档\数学闯关\math150-coach\.worktrees\stellar-material-proof' -WindowStyle Hidden
```

- [ ] **Step 2: Inspect the six approved boundary poses in the browser**

Open `http://127.0.0.1:4173/space/galaxy-lab/` and apply these exact states through `window.observatoryCamera.setImmediate(...)`:

```js
{ yaw: 0, pitch: 0.5, distance: 10.0 }
{ yaw: -32, pitch: 0.5, distance: 10.0 }
{ yaw: 32, pitch: 0.5, distance: 10.0 }
{ yaw: 0, pitch: 0.5, distance: 15.6 }
{ yaw: 0, pitch: 18, distance: 8.6 }
{ yaw: 0, pitch: -16, distance: 8.6 }
```

At the three yaw poses, confirm each system changes internal perspective and follows a curved world trajectory rather than rigid screen translation. At the far pose, confirm all systems and the complete Boss fit, the Boss remains 35% to 45% of viewport height, and at least one large-planet diameter separates each system envelope from the Boss footprint. At the two near pitch boundaries, confirm no route detachment, white patch, Boss crop seam, missing surface, or planet material degradation.

- [ ] **Step 3: Apply only bounded numeric tuning if a visual criterion misses**

Permitted tuning is limited to `CAMERA_TARGET`, the two rejected systems' `center`, `rotation`, and `depthScale`, and the maximum distance. Do not modify the lower-left system, Boss shader/source, planet material, route material, FOV, yaw/pitch limits, or compositor algorithm. After any tuning, rerun the focused Node test and repeat only the failed browser pose.

- [ ] **Step 4: Commit any visual-only numeric tuning**

If Step 3 changed values:

```powershell
git add frontend/space/galaxy-lab/observatory-camera.mjs
git commit -m "Tune observatory world composition"
```

If Step 3 required no changes, do not create an empty commit.

- [ ] **Step 5: Verify repository scope and publish the completed branch**

```powershell
git status --short
git log -4 --oneline
git push origin stellar-material-proof
```

Expected: the worktree is clean, recent commits contain only the design/plan and focused observatory changes, and the push updates `origin/stellar-material-proof`.
