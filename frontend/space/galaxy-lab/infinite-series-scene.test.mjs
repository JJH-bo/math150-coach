import assert from 'node:assert/strict';
import test from 'node:test';

import chapter from './infinite-series-data.mjs';
import {
  buildChapterSectors,
  buildInfiniteSeriesSectors,
  createSectorSceneConfig,
  pickSceneTarget,
} from './infinite-series-scene.mjs';
import { createObservatoryCamera, createSceneFrame } from './observatory-camera.mjs';


test('ten systems are partitioned once across four uncrowded sectors', () => {
  const sectors = buildInfiniteSeriesSectors(chapter);

  assert.deepEqual(sectors.map((sector) => sector.id), [
    'convergence-i',
    'convergence-ii',
    'power-series',
    'fourier',
  ]);
  assert.deepEqual(sectors.map((sector) => sector.systems.length), [3, 2, 3, 2]);
  assert.deepEqual(sectors.map((sector) => sector.planetCount), [12, 9, 14, 8]);
  assert.ok(sectors.every((sector) => sector.systems.length <= 3));
  assert.ok(sectors.every((sector) => sector.planetCount <= 15));

  const systemIds = sectors.flatMap((sector) => sector.systems.map((system) => system.id));
  const planetIds = sectors.flatMap((sector) =>
    sector.systems.flatMap((system) => system.planets.map((planet) => planet.id)));
  assert.equal(new Set(systemIds).size, 10);
  assert.equal(new Set(planetIds).size, 43);
  assert.deepEqual(systemIds, chapter.systems.map((system) => system.id));
});


test('sector scene config preserves chapter metadata and one shared Boss', () => {
  const config = createSectorSceneConfig(chapter, 'power-series');

  assert.equal(config.systems.length, 3);
  assert.equal(config.systems.flatMap((system) => system.planets).length, 14);
  assert.equal(config.boss.id, 'infinite_series.boss');
  assert.equal(config.boss, chapter.boss);
  assert.ok(config.systems.every((system) => system.planets.every((planet) => planet.point.length === 3)));
  assert.ok(config.systems.flatMap((system) => system.planets).every((planet) => planet.radius >= 0.42));
  assert.ok(config.systems.every((system) => system.internalLinks.length >= system.planets.length - 1));
  assert.deepEqual(config.systems.map((system) => system.slot), [0, 1, 2]);

  const firstSector = createSectorSceneConfig(chapter, 'convergence-i');
  assert.deepEqual(firstSector.systems[0].internalLinks.map((link) => link.slice(0, 2)), [
    [0, 1],
    [1, 2],
    [2, 3],
  ]);
});


test('training planets remain individually readable in every default sector composition', () => {
  const camera = createObservatoryCamera();

  for (const sector of buildInfiniteSeriesSectors(chapter)) {
    const frame = createSceneFrame(camera, 16 / 9, createSectorSceneConfig(chapter, sector.id));
    for (const system of frame.systems) {
      const planets = frame.planets.filter((planet) => planet.macroId === system.id);
      for (let left = 0; left < planets.length; left += 1) {
        for (let right = left + 1; right < planets.length; right += 1) {
          const distance = Math.hypot(
            planets[left].center[0] - planets[right].center[0],
            planets[left].center[1] - planets[right].center[1],
          );
          const separation = distance / (planets[left].radius + planets[right].radius);
          assert.ok(
            separation >= 0.86,
            `${sector.id}/${system.id}: planets ${left} and ${right} overlap at ${separation.toFixed(3)}`,
          );
        }
      }
    }
  }
});


test('scene picking returns planets and Boss in the renderer coordinate system', () => {
  const frame = {
    planets: [
      { id: 'planet-a', title: 'Planet A', center: [0, 0], radius: 0.12, training: {} },
      { id: 'planet-b', title: 'Planet B', center: [-0.6, 0.4], radius: 0.08, training: {} },
    ],
    boss: {
      id: 'chapter-boss',
      title: 'Boss',
      center: [0.8, 0],
      lensRadius: 0.25,
      training: {},
    },
  };
  const viewport = { width: 1000, height: 500 };

  assert.equal(pickSceneTarget(frame, { x: 500, y: 250 }, viewport)?.id, 'planet-a');
  assert.equal(pickSceneTarget(frame, { x: 700, y: 250 }, viewport)?.id, 'chapter-boss');
  assert.equal(pickSceneTarget(frame, { x: 50, y: 450 }, viewport), null);

  const overlap = {
    planets: [
      { id: 'planet-far', center: [0, 0], radius: 0.12, depth: 10 },
      { id: 'planet-near', center: [0, 0], radius: 0.12, depth: 5 },
    ],
    boss: null,
  };
  assert.equal(pickSceneTarget(overlap, { x: 500, y: 250 }, viewport)?.id, 'planet-near');
});


test('generic chapters are partitioned into uncrowded two-or-three-system sectors', () => {
  const synthetic = {
    ...chapter,
    chapterId: 'synthetic',
    systems: Array.from({ length: 7 }, (_, index) => ({
      ...chapter.systems[index],
      id: `system-${index + 1}`,
      learningOrder: index + 1,
    })),
  };

  const sectors = buildChapterSectors(synthetic);

  assert.deepEqual(
    sectors.map((sector) => sector.systems.length),
    [2, 3, 2],
  );
  assert.deepEqual(
    sectors.flatMap((sector) => sector.systems.map((system) => system.id)),
    synthetic.systems.map((system) => system.id),
  );
  assert.ok(sectors.every((sector) => sector.systems.length <= 3));
});


test('three-planet systems receive a complete safe scene layout', () => {
  const synthetic = {
    chapterId: 'three-planets',
    title: 'Three Planets',
    systems: [{
      ...chapter.systems[0],
      id: 'three-planets.system',
      learningOrder: 1,
      planets: chapter.systems[0].planets.slice(0, 3),
      links: chapter.systems[0].links.slice(0, 2),
    }],
    boss: chapter.boss,
    metrics: { systemCount: 1, planetCount: 3, bossCount: 1 },
  };

  const sector = buildChapterSectors(synthetic)[0];
  const config = createSectorSceneConfig(synthetic, sector.id);

  assert.equal(config.systems[0].planets.length, 3);
  assert.equal(config.systems[0].internalLinks.length, 2);
  assert.ok(config.systems[0].planets.every((planet) => planet.point.length === 3));
});
