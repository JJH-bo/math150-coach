import test from 'node:test';
import assert from 'node:assert/strict';

import {
  createObservatoryCamera,
  createSceneFrame,
  OBSERVATORY_LIMITS,
} from './observatory-camera.mjs';

const DEG = Math.PI / 180;

test('boundary Boss remains dominant and synchronized across the camera envelope', () => {
  assert.equal(Math.round(OBSERVATORY_LIMITS.yaw[1] / DEG), 24);
  assert.equal(Math.round(OBSERVATORY_LIMITS.pitch[0] / DEG), -12);
  assert.equal(Math.round(OBSERVATORY_LIMITS.pitch[1] / DEG), 14);

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

    const terminalRoutes = frame.routes.filter((route) => route.terminal === 1);
    assert.equal(terminalRoutes.length, 3);
    for (const route of terminalRoutes) {
      const terminalDistance = Math.hypot(
        route.d[0] - frame.boss.center[0],
        route.d[1] - frame.boss.center[1],
      );
      assert.ok(terminalDistance < 0.55);
    }
  }
});

