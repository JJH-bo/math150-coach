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

const FOUR_PLANET_LAYOUT = Object.freeze([
  Object.freeze({ point: [-0.88, 0.00, 0.00], radius: 0.46, heat: 0.58 }),
  Object.freeze({ point: [0.00, 0.72, -0.10], radius: 0.42, heat: 0.82 }),
  Object.freeze({ point: [0.00, -0.72, 0.12], radius: 0.44, heat: 0.42 }),
  Object.freeze({ point: [0.88, 0.00, 0.18], radius: 0.50, heat: 0.92 }),
]);

const FIVE_PLANET_LAYOUT = Object.freeze([
  Object.freeze({ point: [-1.10, 0.00, 0.02], radius: 0.40, heat: 0.56 }),
  Object.freeze({ point: [-0.25, 0.92, -0.10], radius: 0.36, heat: 0.76 }),
  Object.freeze({ point: [-0.25, -0.92, 0.10], radius: 0.38, heat: 0.44 }),
  Object.freeze({ point: [0.88, 0.66, 0.12], radius: 0.41, heat: 0.88 }),
  Object.freeze({ point: [0.98, -0.60, -0.12], radius: 0.43, heat: 0.96 }),
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


export function buildInfiniteSeriesSectors(chapter) {
  const systems = Array.isArray(chapter?.systems) ? chapter.systems : [];
  return SECTOR_DEFINITIONS.map((definition) => {
    const sectorSystems = systems.slice(definition.range[0], definition.range[1]);
    return {
      id: definition.id,
      title: definition.title,
      systems: sectorSystems,
      planetCount: sectorSystems.reduce((total, system) => total + system.planets.length, 0),
    };
  });
}


export function createSectorSceneConfig(chapter, sectorId) {
  const sectors = buildInfiniteSeriesSectors(chapter);
  const sector = sectors.find((candidate) => candidate.id === sectorId) || sectors[0];
  if (!sector) return { id: sectorId, title: '', systems: [], boss: chapter?.boss || null };
  const slots = sector.systems.length === 2 ? TWO_SYSTEM_SLOTS : THREE_SYSTEM_SLOTS;
  const systems = sector.systems.map((system, slot) => {
    const frame = slots[slot];
    const layout = system.planets.length === 5 ? FIVE_PLANET_LAYOUT : FOUR_PLANET_LAYOUT;
    const internalLinks = system.planets.length === 5 ? FIVE_PLANET_LINKS : FOUR_PLANET_LINKS;
    const energy = Math.max(0.64, 1 - slot * 0.17);
    return {
      ...system,
      slot,
      center: [...frame.center],
      rotation: [...frame.rotation],
      depthScale: frame.depthScale,
      energy,
      seed: 1.3 + (system.learningOrder - 1) * 1.91,
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
  const planets = [...(frame.planets || [])].sort((left, right) => right.depth - left.depth);
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
