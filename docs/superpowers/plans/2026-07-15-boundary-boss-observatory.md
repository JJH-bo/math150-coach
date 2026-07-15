# Boundary Boss Observatory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the approved Boss dominate the right screen boundary while expanding the bounded observatory to a safe 48-degree horizontal viewing range.

**Architecture:** `observatory-camera.mjs` remains the only owner of camera limits, Boss projection, and terminal-route projection. It converts the physically projected Boss into a restrained screen anchor, applies the same anchor offset progressively to terminal Bézier controls, and returns one shared frame consumed by the Boss compositor, lensing shader, infall field, and route shader.

**Tech Stack:** Native JavaScript ES modules, WebGL2, GLSL ES 3.00, Canvas 2D Boss compositor, Node built-in test runner

## Global Constraints

- Preserve all planet sizes and surface materials.
- Default Boss optical scale is approximately `1.60`; safe dynamic range is `1.42–1.72`.
- Boss event horizon stays near the right `88%–94%` screen region while the outer accretion structure may be cropped.
- Camera limits are yaw `±24°`, pitch `-12°–14°`, and the existing bounded distance range.
- Lens, infall field, Boss composite, and terminal paths consume the same Boss anchor.
- No node interaction, free flight, new WebGL context, or full project test suite.

---

### Task 1: Boss Anchor and Expanded Observatory Envelope

**Files:**
- Modify: `frontend/space/galaxy-lab/observatory-camera.mjs`
- Create: `frontend/space/galaxy-lab/observatory-camera.test.mjs`

**Interfaces:**
- Consumes: `createObservatoryCamera()` and `createSceneFrame(camera, aspect)`.
- Produces: a frame whose `boss.center`, `boss.scale`, lens values, and three terminal route endpoints are synchronized at default and extreme camera states.

- [ ] **Step 1: Write the focused failing test**

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { createObservatoryCamera, createSceneFrame, OBSERVATORY_LIMITS } from './observatory-camera.mjs';

test('boundary Boss remains dominant and synchronized across the camera envelope', () => {
  assert.equal(Math.round(OBSERVATORY_LIMITS.yaw[1] * 180 / Math.PI), 24);
  assert.equal(Math.round(OBSERVATORY_LIMITS.pitch[0] * 180 / Math.PI), -12);
  assert.equal(Math.round(OBSERVATORY_LIMITS.pitch[1] * 180 / Math.PI), 14);

  const camera = createObservatoryCamera();
  const states = [
    [0, 0, 10],
    [OBSERVATORY_LIMITS.yaw[0], OBSERVATORY_LIMITS.pitch[0], 10],
    [OBSERVATORY_LIMITS.yaw[1], OBSERVATORY_LIMITS.pitch[1], 10],
  ];

  for (const [yaw, pitch, distance] of states) {
    Object.assign(camera.current, { yaw, pitch, distance });
    const frame = createSceneFrame(camera, 16 / 9);
    const screenRatio = 0.5 + frame.boss.center[0] / (2 * 16 / 9);
    assert.ok(screenRatio >= 0.86 && screenRatio <= 0.95);
    assert.ok(frame.boss.scale >= 1.42 && frame.boss.scale <= 1.72);
    assert.equal(frame.routes.filter((route) => route.terminal === 1).length, 3);
    for (const route of frame.routes.filter((item) => item.terminal === 1)) {
      assert.ok(Math.hypot(route.d[0] - frame.boss.center[0], route.d[1] - frame.boss.center[1]) < 0.55);
    }
  }
});
```

- [ ] **Step 2: Run the focused test and confirm it fails on the old limits and scale**

Run:

```powershell
& $node --test frontend/space/galaxy-lab/observatory-camera.test.mjs
```

Expected: FAIL because yaw is `12°`, pitch is `-7°–9°`, and Boss scale is below `1.42`.

- [ ] **Step 3: Implement the expanded bounds and one shared Boss anchor offset**

```js
export const OBSERVATORY_LIMITS = Object.freeze({
  yaw: Object.freeze([-24 * DEG, 24 * DEG]),
  pitch: Object.freeze([-12 * DEG, 14 * DEG]),
  distance: Object.freeze([8.6, 11.8]),
});

const rawBoss = projectPoint(BOSS_WORLD, basis);
const bossCenter = [
  clamp(1.34 + (rawBoss.point[0] - 1.01) * 0.22, 1.22, 1.48),
  clamp(rawBoss.point[1] * 0.44, -0.18, 0.22),
];
const bossOffset = [bossCenter[0] - rawBoss.point[0], bossCenter[1] - rawBoss.point[1]];
const bossScale = clamp(1.60 * 10 / rawBoss.depth, 1.42, 1.72);
```

Apply `bossOffset` to terminal route control points with weights `0.0`, `0.18`, `0.68`, and `1.0`, leaving internal routes untouched.

- [ ] **Step 4: Run the focused test and confirm it passes**

Run:

```powershell
& $node --test frontend/space/galaxy-lab/observatory-camera.test.mjs
```

Expected: `1` test passed, `0` failed.

### Task 2: Optical Hierarchy and Composition Synchronization

**Files:**
- Modify: `frontend/space/galaxy-lab/index.html`

**Interfaces:**
- Consumes: `sceneFrame.boss.center`, `sceneFrame.boss.scale`, and depth energy from the shared frame.
- Produces: the larger cropped Boss composite with unchanged event-horizon material and reduced middle/far star exposure competition.

- [ ] **Step 1: Preserve the shared Boss composite anchor**

Keep `destinationX = targetX - destinationWidth * 0.611` and `destinationY = targetY - destinationHeight * 0.545`; the larger `sceneFrame.boss.scale` deliberately makes the outer accretion structure exceed the canvas while the event horizon remains anchored.

- [ ] **Step 2: Strengthen depth exposure without changing planet size or texture detail**

Replace the surface multiplier with direct depth energy:

```glsl
surfaceColor *= mix(0.62, 1.0, energyScale);
```

Keep `planetData[i].z` unchanged so only visual hierarchy changes.

- [ ] **Step 3: Run targeted checks only**

Run:

```powershell
& $node --test frontend/space/galaxy-lab/observatory-camera.test.mjs
git diff --check
```

Expected: `1` test passed, no whitespace errors. Do not run the full project suite.

- [ ] **Step 4: Commit and push**

```powershell
git add frontend/space/galaxy-lab/observatory-camera.mjs frontend/space/galaxy-lab/observatory-camera.test.mjs frontend/space/galaxy-lab/index.html docs/superpowers/plans/2026-07-15-boundary-boss-observatory.md
git commit -m "Enlarge the boundary Boss observatory"
git push origin stellar-material-proof
```

## Self-Review

- Spec coverage: Boss size, boundary crop, expanded yaw/pitch, synchronized terminal paths/lens/infall/compositor, unchanged planet size, and no new interaction are all assigned.
- Placeholder scan: no deferred markers or unspecified code steps remain.
- Interface consistency: all downstream consumers continue reading the same `sceneFrame.boss` object; no new rendering context or duplicate camera state is introduced.

