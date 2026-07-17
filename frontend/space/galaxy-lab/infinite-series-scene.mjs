const SECTOR_DEFINITIONS = Object.freeze([
  Object.freeze({ id: 'convergence-i', title: '数项判敛 I', range: [0, 3] }),
  Object.freeze({ id: 'convergence-ii', title: '数项判敛 II', range: [3, 5] }),
  Object.freeze({ id: 'power-series', title: '幂级数', range: [5, 8] }),
  Object.freeze({ id: 'fourier', title: '傅里叶', range: [8, 10] }),
]);

const THREE_SYSTEM_SLOTS = Object.freeze([
  Object.freeze({ center: [-3.00, 0.00, 1.25], rotation: [-10, -7, 8], depthScale: 1.0 }),
  Object.freeze({ center: [-2.00, 2.90, -0.10], rotation: [10, 14, -8], depthScale: 2.4 }),
  Object.freeze({ center: [-2.40, -2.80, 0.25], rotation: [-10, -12, 12], depthScale: 2.5 }),
]);

const TWO_SYSTEM_SLOTS = Object.freeze([
  Object.freeze({ center: [-2.35, 1.85, 0.72], rotation: [8, 12, -7], depthScale: 1.8 }),
  Object.freeze({ center: [-2.55, -1.90, 0.42], rotation: [-9, -12, 10], depthScale: 2.0 }),
]);

const THREE_PLANET_LAYOUT = Object.freeze([
  Object.freeze({ point: [-0.92, -0.48, 0.06], radius: 0.46, heat: 0.58 }),
  Object.freeze({ point: [0.00, 0.78, -0.10], radius: 0.43, heat: 0.82 }),
  Object.freeze({ point: [0.92, -0.48, 0.14], radius: 0.49, heat: 0.94 }),
]);

const FOUR_PLANET_LAYOUT = Object.freeze([
  Object.freeze({ point: [-0.88, 0.00, 0.00], radius: 0.46, heat: 0.58 }),
  Object.freeze({ point: [0.00, 0.72, -0.10], radius: 0.42, heat: 0.82 }),
  Object.freeze({ point: [0.00, -0.72, 0.12], radius: 0.44, heat: 0.42 }),
  Object.freeze({ point: [0.88, 0.00, 0.18], radius: 0.50, heat: 0.92 }),
]);

const FIVE_PLANET_LAYOUT = Object.freeze([
  Object.freeze({ point: [-1.28, 0.00, 0.02], radius: 0.45, heat: 0.56 }),
  Object.freeze({ point: [-0.28, 1.10, -0.10], radius: 0.42, heat: 0.76 }),
  Object.freeze({ point: [-0.28, -1.10, 0.10], radius: 0.44, heat: 0.44 }),
  Object.freeze({ point: [1.02, 0.80, 0.12], radius: 0.46, heat: 0.88 }),
  Object.freeze({ point: [1.14, -0.70, -0.12], radius: 0.49, heat: 0.96 }),
]);

const THREE_PLANET_LINKS = Object.freeze([
  Object.freeze([0, 1, 0.17]),
  Object.freeze([1, 2, -0.16]),
]);

const FOUR_PLANET_LINKS = Object.freeze([
  Object.freeze([0, 1, 0.18]),
  Object.freeze([0, 2, -0.18]),
  Object.freeze([1, 3, -0.14]),
  Object.freeze([2, 3, 0.14]),
]);

const FIVE_PLANET_LINKS = Object.freeze([
  Object.freeze([0, 1, 0.18]),
  Object.freeze([0, 2, -0.18]),
  Object.freeze([1, 3, -0.13]),
  Object.freeze([2, 4, 0.15]),
]);


export function buildChapterSectors(chapter) {
  const systems = Array.isArray(chapter?.systems) ? chapter.systems : [];
  if (chapter?.chapterId === 'infinite_series' && systems.length === 10) {
    return _sectorsFromDefinitions(systems, SECTOR_DEFINITIONS);
  }
  const ordered = [...systems].sort(
    (left, right) => (left.learningOrder || 0) - (right.learningOrder || 0),
  );
  const sectors = [];
  let cursor = 0;
  while (cursor < ordered.length) {
    const remaining = ordered.length - cursor;
    const count = remaining === 1
      ? 1
      : remaining === 4 || remaining === 7
        ? 2
        : Math.min(3, remaining);
    const sectorSystems = ordered.slice(cursor, cursor + count);
    const start = cursor + 1;
    const end = cursor + sectorSystems.length;
    sectors.push({
      id: `sector-${String(sectors.length + 1).padStart(2, '0')}`,
      title: start === end ? `第 ${start} 模块` : `第 ${start}–${end} 模块`,
      systems: sectorSystems,
      planetCount: sectorSystems.reduce(
        (total, system) => total + system.planets.length,
        0,
      ),
    });
    cursor += count;
  }
  return sectors;
}


export function buildInfiniteSeriesSectors(chapter) {
  return buildChapterSectors(chapter);
}


function _sectorsFromDefinitions(systems, definitions) {
  return definitions.map((definition) => {
    const sectorSystems = systems.slice(
      definition.range[0],
      definition.range[1],
    );
    return {
      id: definition.id,
      title: definition.title,
      systems: sectorSystems,
      planetCount: sectorSystems.reduce(
        (total, system) => total + system.planets.length,
        0,
      ),
    };
  });
}


export function createSectorSceneConfig(chapter, sectorId) {
  const sectors = buildChapterSectors(chapter);
  const sector = sectors.find((candidate) => candidate.id === sectorId) || sectors[0];
  if (!sector) return { id: sectorId, title: '', systems: [], boss: chapter?.boss || null };
  const slots = sector.systems.length === 2 ? TWO_SYSTEM_SLOTS : THREE_SYSTEM_SLOTS;
  const systems = sector.systems.map((system, slot) => {
    const frame = slots[slot];
    const layout = system.planets.length === 3
      ? THREE_PLANET_LAYOUT
      : system.planets.length === 5
        ? FIVE_PLANET_LAYOUT
        : FOUR_PLANET_LAYOUT;
    const fallbackLinks = system.planets.length === 3
      ? THREE_PLANET_LINKS
      : system.planets.length === 5
        ? FIVE_PLANET_LINKS
        : FOUR_PLANET_LINKS;
    const planetIndex = new Map(system.planets.map((planet, index) => [planet.id, index]));
    const semanticLinks = (system.links || []).map((link, index) => [
      planetIndex.get(link.sourceId),
      planetIndex.get(link.targetId),
      index % 2 === 0 ? 0.14 : -0.14,
    ]).filter((link) => Number.isInteger(link[0]) && Number.isInteger(link[1]));
    const internalLinks = semanticLinks.length ? semanticLinks : fallbackLinks;
    const energy = Math.max(0.64, 1 - slot * 0.17);
    return {
      ...system,
      slot,
      center: [...frame.center],
      rotation: [...frame.rotation],
      depthScale: frame.depthScale,
      energy,
      seed: 1.3 + ((system.learningOrder || slot + 1) - 1) * 1.91,
      planets: system.planets.map((planet, index) => ({
        ...planet,
        point: [...layout[index].point],
        radius: layout[index].radius,
        heat: layout[index].heat,
      })),
      internalLinks: internalLinks.map((link) => [...link]),
    };
  });
  return {
    id: sector.id,
    title: sector.title,
    planetCount: sector.planetCount,
    systems,
    boss: chapter.boss,
  };
}


export function pickSceneTarget(frame, point, viewport) {
  if (!frame || !point || !viewport?.width || !viewport?.height) return null;
  const scenePoint = [
    (point.x * 2 - viewport.width) / viewport.height,
    (viewport.height - point.y * 2) / viewport.height,
  ];
  const planets = [...(frame.planets || [])].sort((left, right) => left.depth - right.depth);
  for (const planet of planets) {
    const radius = Math.max(planet.radius * 1.24, 0.055);
    if (distance(scenePoint, planet.center) <= radius) return planet;
  }
  const boss = frame.boss;
  if (boss?.center) {
    const radius = Math.max((boss.lensRadius || 0.22) * 1.08, 0.23);
    if (distance(scenePoint, boss.center) <= radius) return boss;
  }
  return null;
}


function distance(left, right) {
  return Math.hypot(left[0] - right[0], left[1] - right[1]);
}
