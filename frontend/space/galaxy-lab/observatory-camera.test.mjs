import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import {
  createObservatoryCamera,
  createSceneFrame,
  OBSERVATORY_LIMITS,
} from './observatory-camera.mjs';

const DEG = Math.PI / 180;

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
  assert.equal(Math.round(OBSERVATORY_LIMITS.yaw[0] / DEG), -32);
  assert.equal(Math.round(OBSERVATORY_LIMITS.yaw[1] / DEG), 32);
  assert.equal(Math.round(OBSERVATORY_LIMITS.pitch[0] / DEG), -16);
  assert.equal(Math.round(OBSERVATORY_LIMITS.pitch[1] / DEG), 18);
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

test('Boss observer comes from the shared camera position', () => {
  const camera = createObservatoryCamera();
  const base = createSceneFrame(camera, 16 / 9);

  Object.assign(camera.current, { yaw: 32 * DEG, pitch: 18 * DEG });
  const edge = createSceneFrame(camera, 16 / 9);

  assert.ok(Math.abs(edge.boss.viewAzimuth - base.boss.viewAzimuth) > 20 * DEG);
  assert.ok(edge.boss.viewInclination > base.boss.viewInclination + 10 * DEG);
  assert.ok(edge.boss.observerRadiusIndex >= 0 && edge.boss.observerRadiusIndex <= 1000);
});

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

test('lower-right system reverses horizontal travel around the default view', () => {
  const left = frameAt({ yaw: -16 });
  const center = frameAt();
  const right = frameAt({ yaw: 16 });
  const systemIndex = 2;
  const centerX = center.systems[systemIndex].center[0];

  assert.ok(centerX < left.systems[systemIndex].center[0] - 0.02);
  assert.ok(centerX < right.systems[systemIndex].center[0] - 0.02);
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
