import test from 'node:test';
import assert from 'node:assert/strict';

import {
  createObservatoryCamera,
  createSceneFrame,
  OBSERVATORY_LIMITS,
} from './observatory-camera.mjs';

const DEG = Math.PI / 180;

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
  assert.equal(frame.routes.filter((route) => route.terminal === 1).length, 3);
});

test('dolly changes the whole fixed scene', () => {
  const camera = createObservatoryCamera();
  const far = createSceneFrame(camera, 16 / 9);

  camera.current.distance = OBSERVATORY_LIMITS.distance[0];
  const near = createSceneFrame(camera, 16 / 9);

  assert.notDeepEqual(
    near.planets.map((planet) => planet.radius),
    far.planets.map((planet) => planet.radius),
  );
  assert.ok(near.boss.distance < far.boss.distance);
  assert.ok(near.boss.lensRadius > far.boss.lensRadius);
});

test('Boss observer comes from the shared camera position', () => {
  const camera = createObservatoryCamera();
  const base = createSceneFrame(camera, 16 / 9);

  Object.assign(camera.current, { yaw: 32 * DEG, pitch: 18 * DEG });
  const edge = createSceneFrame(camera, 16 / 9);

  assert.ok(Math.abs(edge.boss.viewAzimuth - base.boss.viewAzimuth) > 20 * DEG);
  assert.ok(edge.boss.viewInclination > base.boss.viewInclination + 10 * DEG);
  assert.ok(edge.boss.observerRadiusIndex >= 0 && edge.boss.observerRadiusIndex <= 1000);
});
