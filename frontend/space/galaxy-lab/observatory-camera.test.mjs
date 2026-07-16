import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import {
  createObservatoryCamera,
  createSceneFrame,
  OBSERVATORY_LIMITS,
} from './observatory-camera.mjs';

const EPSILON = 1e-10;
const close = (actual, expected, message = '') =>
  assert.ok(Math.abs(actual - expected) <= EPSILON, `${message}: ${actual} != ${expected}`);

function frameAt({ panX = 0, panY = 0, zoom = 1 } = {}) {
  const camera = createObservatoryCamera();
  camera.setState({ panX, panY, zoom }, true);
  return createSceneFrame(camera, 16 / 9);
}

const pointList = (frame) => [
  ...frame.planets.map((planet) => planet.center),
  ...frame.systems.map((system) => system.center),
  frame.boss.center,
  ...frame.routes.flatMap((route) => [route.a, route.b, route.c, route.d]),
];

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

test('camera exposes only bounded pan and uniform zoom', () => {
  assert.deepEqual(Object.keys(OBSERVATORY_LIMITS), ['panX', 'panY', 'zoom']);
  const camera = createObservatoryCamera();
  camera.setState({ panX: 99, panY: -99, zoom: 99 }, true);
  assert.equal(camera.current.panX, OBSERVATORY_LIMITS.panX[1]);
  assert.equal(camera.current.panY, OBSERVATORY_LIMITS.panY[0]);
  assert.equal(camera.current.zoom, OBSERVATORY_LIMITS.zoom[1]);
  assert.equal('yaw' in camera.current, false);
  assert.equal('distance' in camera.current, false);
});

test('drag applies one exact translation to every scene point', () => {
  const base = frameAt();
  const moved = frameAt({ panX: 0.31, panY: -0.19 });
  const before = pointList(base);
  const after = pointList(moved);

  before.forEach((point, index) => {
    close(after[index][0] - point[0], 0.31, `point ${index} x`);
    close(after[index][1] - point[1], -0.19, `point ${index} y`);
  });
  base.planets.forEach((planet, index) => close(moved.planets[index].radius, planet.radius));
  close(moved.boss.scale, base.boss.scale);
});

test('wheel applies one exact scale to positions, planets, routes and Boss', () => {
  const base = frameAt();
  const zoomed = frameAt({ zoom: 1.37 });
  const before = pointList(base);
  const after = pointList(zoomed);

  before.forEach((point, index) => {
    close(after[index][0], point[0] * 1.37, `point ${index} x`);
    close(after[index][1], point[1] * 1.37, `point ${index} y`);
  });
  base.planets.forEach((planet, index) =>
    close(zoomed.planets[index].radius, planet.radius * 1.37, `planet ${index} radius`));
  close(zoomed.boss.scale, base.boss.scale * 1.37, 'Boss scale');
  close(zoomed.boss.lensRadius, base.boss.lensRadius * 1.37, 'lens radius');
});

test('pan and zoom never alter approved Boss viewing angle or material observer', () => {
  const base = frameAt();
  const moved = frameAt({ panX: -0.42, panY: 0.28, zoom: 1.48 });
  assert.equal(moved.boss.viewAzimuth, base.boss.viewAzimuth);
  assert.equal(moved.boss.viewInclination, base.boss.viewInclination);
  assert.equal(moved.boss.observerRadiusIndex, base.boss.observerRadiusIndex);
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
      assert.ok(Math.max(horizontalGap, verticalGap) >= 0.09,
        `systems ${first}/${second} gap ${Math.max(horizontalGap, verticalGap)}`);
    }
  }

  const horizontalLimit = aspect * 0.94;
  bounds.forEach((value, systemIndex) => {
    assert.ok(value.left >= -horizontalLimit, `system ${systemIndex} left edge`);
    assert.ok(value.right <= horizontalLimit, `system ${systemIndex} right edge`);
    assert.ok(value.bottom >= -0.94, `system ${systemIndex} bottom edge`);
    assert.ok(value.top <= 0.94, `system ${systemIndex} top edge`);
  });
});

test('compositor controls the affine camera and sends the same transform to the sky', () => {
  const galaxySource = readFileSync(new URL('./index.html', import.meta.url), 'utf8');
  const cosmosSource = readFileSync(new URL('../cosmos-lab/index.html', import.meta.url), 'utf8');

  assert.equal(galaxySource.includes('observatory.pan(deltaX, deltaY, innerHeight)'), true);
  assert.equal(galaxySource.includes('observatory.zoom(event.deltaY)'), true);
  assert.equal(galaxySource.includes('observatory.rotate('), false);
  assert.equal(galaxySource.includes('observatory.dolly('), false);
  assert.equal(galaxySource.includes('panX: observatory.current.panX'), true);
  assert.equal(galaxySource.includes('zoom: observatory.current.zoom'), true);
  assert.equal(cosmosSource.includes('uniform vec3 viewportTransform;'), true);
  assert.equal(cosmosSource.includes('setViewportTransform(next = {})'), true);
});

test('embedded Boss keeps the approved high-resolution composite', () => {
  const galaxySource = readFileSync(new URL('./index.html', import.meta.url), 'utf8');
  const bossSource = readFileSync(new URL('../boss-lab/index.html', import.meta.url), 'utf8');

  assert.equal(bossSource.includes('setEmbeddedRenderScale(value)'), true);
  assert.equal(bossSource.includes('setRenderScale(value)'), true);
  assert.equal(galaxySource.includes('setRenderScale?.(1.35)'), true);
  assert.equal(galaxySource.includes('sceneFrame.boss.scale'), true);
});
