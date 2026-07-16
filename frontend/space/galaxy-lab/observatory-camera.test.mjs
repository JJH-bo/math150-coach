import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import {
  createObservatoryCamera,
  createSceneFrame,
  OBSERVATORY_LIMITS,
} from './observatory-camera.mjs';

const DEG = Math.PI / 180;
const EPSILON = 1e-9;
const distance3 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
const distance2 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const normalize = (value) => {
  const magnitude = Math.hypot(...value);
  return value.map((component) => component / magnitude);
};

function frameAt({ azimuth = 0, elevation = 0, radius } = {}) {
  const camera = createObservatoryCamera();
  camera.setState({
    azimuth: azimuth * DEG,
    elevation: elevation * DEG,
    ...(Number.isFinite(radius) ? { radius } : {}),
  }, true);
  return { camera, frame: createSceneFrame(camera, 16 / 9) };
}

test('camera state is a bounded fan shell around the Boss', () => {
  assert.deepEqual(Object.keys(OBSERVATORY_LIMITS), ['azimuth', 'elevation', 'radius']);
  assert.equal(Math.round(OBSERVATORY_LIMITS.azimuth[0] / DEG), -30);
  assert.equal(Math.round(OBSERVATORY_LIMITS.azimuth[1] / DEG), 30);
  assert.equal(Math.round(OBSERVATORY_LIMITS.elevation[0] / DEG), -15);
  assert.equal(Math.round(OBSERVATORY_LIMITS.elevation[1] / DEG), 17);
  assert.deepEqual(OBSERVATORY_LIMITS.radius, [9.4, 18]);

  const camera = createObservatoryCamera();
  camera.setState({ azimuth: 99, elevation: -99, radius: 2 }, true);
  assert.equal(camera.current.azimuth, OBSERVATORY_LIMITS.azimuth[1]);
  assert.equal(camera.current.elevation, OBSERVATORY_LIMITS.elevation[0]);
  assert.equal(camera.current.radius, OBSERVATORY_LIMITS.radius[0]);
  assert.equal('panX' in camera.current, false);
  assert.equal('zoom' in camera.current, false);
});

test('camera physically orbits the Boss and always looks back at it', () => {
  const base = frameAt().frame;
  const edge = frameAt({ azimuth: 24, elevation: 12 }).frame;

  assert.ok(distance3(base.camera.position, edge.camera.position) > 4);
  assert.ok(Math.abs(distance3(edge.camera.position, edge.camera.pivot) - edge.camera.radius) < EPSILON);
  const toBoss = normalize(edge.camera.pivot.map((value, index) => value - edge.camera.position[index]));
  assert.ok(dot(toBoss, edge.camera.forward) > 1 - EPSILON);
  assert.ok(distance2(edge.boss.center, base.boss.center) < EPSILON);
});

test('all learning objects stay fixed in world space while projections change', () => {
  const left = frameAt({ azimuth: -26, elevation: -8 }).frame;
  const right = frameAt({ azimuth: 26, elevation: 10 }).frame;

  assert.deepEqual(right.planets.map((planet) => planet.world), left.planets.map((planet) => planet.world));
  assert.deepEqual(right.systems.map((system) => system.world), left.systems.map((system) => system.world));
  assert.notDeepEqual(right.planets.map((planet) => planet.center), left.planets.map((planet) => planet.center));

  const leftRatio = distance2(left.planets[0].center, left.planets[3].center) /
    distance2(left.planets[1].center, left.planets[2].center);
  const rightRatio = distance2(right.planets[0].center, right.planets[3].center) /
    distance2(right.planets[1].center, right.planets[2].center);
  assert.ok(Math.abs(leftRatio - rightRatio) > 0.2, 'orbit must create real perspective, not rigid translation');
});

test('wheel dolly changes only orbit radius and creates depth-dependent scale', () => {
  const near = frameAt({ radius: OBSERVATORY_LIMITS.radius[0] }).frame;
  const far = frameAt({ radius: OBSERVATORY_LIMITS.radius[1] }).frame;

  assert.deepEqual(near.planets.map((planet) => planet.world), far.planets.map((planet) => planet.world));
  assert.ok(near.boss.scale > far.boss.scale * 1.7);
  assert.ok(near.planets[0].radius > far.planets[0].radius);
  assert.ok(near.planets[0].radius / far.planets[0].radius !==
    near.planets[7].radius / far.planets[7].radius);
});

test('Boss ray-traced observer follows the shared orbit pose', () => {
  const base = frameAt().frame;
  const edge = frameAt({ azimuth: 24, elevation: 12, radius: 16 }).frame;

  assert.ok(edge.boss.viewAzimuth > base.boss.viewAzimuth + 20 * DEG);
  assert.ok(edge.boss.viewInclination > base.boss.viewInclination + 10 * DEG);
  assert.ok(edge.boss.observerRadiusIndex > base.boss.observerRadiusIndex);
  assert.deepEqual(edge.boss.center, edge.boss.projectedCenter);
});

test('default fan composition keeps Boss dominant and all planets visible', () => {
  const aspect = 900 / 817;
  const camera = createObservatoryCamera();
  const frame = createSceneFrame(camera, aspect);
  const horizontalLimit = aspect * 0.99;

  assert.ok(frame.boss.center[0] >= 0.85 && frame.boss.center[0] <= 1.05);
  assert.ok(Math.abs(frame.boss.center[1]) < 0.02);
  frame.planets.forEach((planet, index) => {
    assert.ok(planet.center[0] - planet.radius >= -horizontalLimit, `planet ${index} left`);
    assert.ok(planet.center[0] + planet.radius <= horizontalLimit, `planet ${index} right`);
    assert.ok(planet.center[1] - planet.radius >= -0.99, `planet ${index} bottom`);
    assert.ok(planet.center[1] + planet.radius <= 0.99, `planet ${index} top`);
  });
});

test('compositor uses orbit and dolly and sends the same orientation to the sky', () => {
  const galaxySource = readFileSync(new URL('./index.html', import.meta.url), 'utf8');
  const cosmosSource = readFileSync(new URL('../cosmos-lab/index.html', import.meta.url), 'utf8');

  assert.equal(galaxySource.includes('observatory.orbit(deltaX, deltaY, innerHeight)'), true);
  assert.equal(galaxySource.includes('observatory.dolly(event.deltaY)'), true);
  assert.equal(galaxySource.includes('observatory.pan('), false);
  assert.equal(galaxySource.includes('observatory.zoom('), false);
  assert.equal(galaxySource.includes('cosmosCamera?.setObservatory?.({'), true);
  assert.equal(galaxySource.includes('setViewportTransform?.({'), false);
  assert.equal(cosmosSource.includes('setObservatory(next = {})'), true);
});

test('approved high-resolution Boss material pipeline remains intact', () => {
  const galaxySource = readFileSync(new URL('./index.html', import.meta.url), 'utf8');
  const bossSource = readFileSync(new URL('../boss-lab/index.html', import.meta.url), 'utf8');

  assert.equal(bossSource.includes('setEmbeddedRenderScale(value)'), true);
  assert.equal(bossSource.includes('setRenderScale(value)'), true);
  assert.equal(galaxySource.includes('setRenderScale?.(1.35)'), true);
  assert.equal(galaxySource.includes('sceneFrame.boss.scale'), true);
});
