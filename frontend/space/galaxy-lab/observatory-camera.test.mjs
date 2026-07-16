import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import {
  createObservatoryCamera,
  createSceneFrame,
  OBSERVATORY_LIMITS,
} from './observatory-camera.mjs';

const DEG = Math.PI / 180;

function frameAt({ yaw = 0, pitch = 0.5, distance = 11.8 } = {}) {
  const camera = createObservatoryCamera();
  camera.setState({ yaw: yaw * DEG, pitch: pitch * DEG, distance }, true);
  return createSceneFrame(camera, 16 / 9);
}

const systemPlanets = (frame, systemIndex) =>
  frame.planets.slice(systemIndex * 4, systemIndex * 4 + 4);

const systemBounds = (frame, systemIndex) => {
  const planets = systemPlanets(frame, systemIndex);
  return {
    left: Math.min(...planets.map((planet) => planet.center[0] - planet.radius)),
    right: Math.max(...planets.map((planet) => planet.center[0] + planet.radius)),
    bottom: Math.min(...planets.map((planet) => planet.center[1] - planet.radius)),
    top: Math.max(...planets.map((planet) => planet.center[1] + planet.radius)),
  };
};

test('camera uses expanded limits and a real dolly', () => {
  assert.equal(Math.round(OBSERVATORY_LIMITS.yaw[0] / DEG), -42);
  assert.equal(Math.round(OBSERVATORY_LIMITS.yaw[1] / DEG), 42);
  assert.equal(Math.round(OBSERVATORY_LIMITS.pitch[0] / DEG), -24);
  assert.equal(Math.round(OBSERVATORY_LIMITS.pitch[1] / DEG), 26);
  assert.equal(OBSERVATORY_LIMITS.distance[0], 8.6);
  assert.equal(OBSERVATORY_LIMITS.distance[1], 15.6);

  const camera = createObservatoryCamera();
  camera.dolly(-2000);

  assert.equal(camera.target.distance, OBSERVATORY_LIMITS.distance[0]);
  assert.equal('focus' in camera.target, false);
});

test('camera can apply an exact clamped pose for boundary inspection and reset', () => {
  const camera = createObservatoryCamera();

  camera.setState({ yaw: 80 * DEG, pitch: -50 * DEG, distance: 3 }, true);

  assert.equal(camera.current.yaw, OBSERVATORY_LIMITS.yaw[1]);
  assert.equal(camera.current.pitch, OBSERVATORY_LIMITS.pitch[0]);
  assert.equal(camera.current.distance, OBSERVATORY_LIMITS.distance[0]);
  assert.deepEqual(camera.current, camera.target);
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

test('look rotation changes direction without moving the ship', () => {
  const base = frameAt();
  const edge = frameAt({ yaw: 42, pitch: 26 });

  assert.deepEqual(edge.camera.position, base.camera.position);
  assert.notDeepEqual(edge.camera.forward, base.camera.forward);
  assert.notDeepEqual(edge.boss.center, base.boss.center);
});

test('dolly moves the ship only along the fixed observation corridor', () => {
  const near = frameAt({ yaw: 18, pitch: 8, distance: OBSERVATORY_LIMITS.distance[0] });
  const far = frameAt({ yaw: 18, pitch: 8, distance: OBSERVATORY_LIMITS.distance[1] });

  assert.equal(near.camera.position[0], far.camera.position[0]);
  assert.equal(near.camera.position[1], far.camera.position[1]);
  assert.notEqual(near.camera.position[2], far.camera.position[2]);
  assert.deepEqual(near.camera.forward, far.camera.forward);
});

test('Boss observer follows ship position rather than look direction', () => {
  const base = frameAt();
  const looked = frameAt({ yaw: 42, pitch: 26 });
  const far = frameAt({ distance: OBSERVATORY_LIMITS.distance[1] });

  assert.equal(looked.boss.viewAzimuth, base.boss.viewAzimuth);
  assert.equal(looked.boss.viewInclination, base.boss.viewInclination);
  assert.equal(looked.boss.distance, base.boss.distance);
  assert.notEqual(far.boss.observerRadiusIndex, base.boss.observerRadiusIndex);
});

test('default narrow view keeps all three system envelopes visibly separate', () => {
  const aspect = 900 / 817;
  const camera = createObservatoryCamera();
  const frame = createSceneFrame(camera, aspect);
  const bounds = [0, 1, 2].map((systemIndex) => systemBounds(frame, systemIndex));

  for (let first = 0; first < bounds.length; first += 1) {
    for (let second = first + 1; second < bounds.length; second += 1) {
      const a = bounds[first];
      const b = bounds[second];
      const horizontalGap = Math.max(b.left - a.right, a.left - b.right);
      const verticalGap = Math.max(b.bottom - a.top, a.bottom - b.top);
      assert.ok(
        Math.max(horizontalGap, verticalGap) >= 0.09,
        `systems ${first}/${second} gap ${Math.max(horizontalGap, verticalGap)}`,
      );
    }
  }

  const horizontalLimit = aspect * 0.94;
  bounds.forEach((value, systemIndex) => {
    assert.ok(value.left >= -horizontalLimit, `system ${systemIndex} left edge`);
    assert.ok(value.right <= horizontalLimit, `system ${systemIndex} right edge`);
    assert.ok(value.bottom >= -0.94, `system ${systemIndex} bottom edge`);
    assert.ok(value.top <= 0.94, `system ${systemIndex} top edge`);
  });
  assert.equal(camera.current.distance, 11.8);
});

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

test('galaxy compositor has no Boss-only focus camera path', () => {
  const galaxySource = readFileSync(new URL('./index.html', import.meta.url), 'utf8');

  assert.equal(galaxySource.includes('snapshot.focus'), false);
  assert.equal(galaxySource.includes('Boss焦点'), false);
  assert.equal(galaxySource.includes('sceneFrame.boss.observerRadiusIndex'), true);
  assert.equal(galaxySource.includes('sceneFrame.boss.compositeScale'), false);
  assert.equal(galaxySource.includes('sceneFrame.boss.scale'), true);
  assert.equal(galaxySource.includes('setImmediate:'), true);
  assert.equal(galaxySource.includes('snapshot.distance - 11.8'), true);
  assert.equal(galaxySource.includes('distance = 11.8'), true);
});

test('embedded Boss supports the expanded observer and high-resolution composite', () => {
  const galaxySource = readFileSync(new URL('./index.html', import.meta.url), 'utf8');
  const bossSource = readFileSync(new URL('../boss-lab/index.html', import.meta.url), 'utf8');

  assert.equal(bossSource.includes('setEmbeddedRenderScale(value)'), true);
  assert.equal(bossSource.includes('setRenderScale(value)'), true);
  assert.equal(bossSource.includes('Math.max(-450'), false);
  assert.equal(galaxySource.includes('setRenderScale?.(1.35)'), true);
});
