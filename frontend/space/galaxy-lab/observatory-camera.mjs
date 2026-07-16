const DEG = Math.PI / 180;

export const OBSERVATORY_LIMITS = Object.freeze({
  azimuth: Object.freeze([-30 * DEG, 30 * DEG]),
  elevation: Object.freeze([-15 * DEG, 17 * DEG]),
  radius: Object.freeze([9.4, 18]),
});

const BASE_AZIMUTH = -19.47 * DEG;
const BASE_ELEVATION = 0.37 * DEG;
const DEFAULT_RADIUS = 12.36;
const DEFAULT_STATE = Object.freeze({ azimuth: 0, elevation: 0, radius: DEFAULT_RADIUS });
const BOSS_WORLD = Object.freeze([3.92, 0.02, -0.10]);
const BOSS_WORLD_RADIUS = 1.44;
const FOV = 52 * DEG;
const COMPOSITION_OFFSET = Object.freeze([0.91, 0]);
const BOSS_DEFAULT_INCLINATION = 20.2 * DEG;
const BOSS_DEFAULT_RADIUS_INDEX = 620;
const BOSS_COMPOSITE_SCALE = 1.58;

const SYSTEMS = Object.freeze([
  Object.freeze({ center: [-3.00, 0.00, 1.25], rotation: [-10, -7, 8], depthScale: 1.0, energy: 1.00, seed: 1.3 }),
  Object.freeze({ center: [-2.00, 2.90, -0.10], rotation: [18, 40, -8], depthScale: 3.2, energy: 0.82, seed: 5.2 }),
  Object.freeze({ center: [-2.40, -2.80, 0.25], rotation: [-22, -31, 12], depthScale: 3.4, energy: 0.66, seed: 9.4 }),
]);

const LOCAL_PLANETS = Object.freeze([
  Object.freeze({ point: [-0.88, 0.00, 0.00], radius: 0.46, heat: 0.58 }),
  Object.freeze({ point: [0.00, 0.72, -0.10], radius: 0.42, heat: 0.82 }),
  Object.freeze({ point: [0.00, -0.72, 0.12], radius: 0.44, heat: 0.42 }),
  Object.freeze({ point: [0.88, 0.00, 0.18], radius: 0.50, heat: 0.92 }),
]);

const INTERNAL_LINKS = Object.freeze([
  Object.freeze([0, 1, 0.18]),
  Object.freeze([0, 2, -0.18]),
  Object.freeze([1, 3, -0.14]),
  Object.freeze([2, 3, 0.14]),
]);

const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, value));
const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const subtract = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const multiply = (value, scalar) => [value[0] * scalar, value[1] * scalar, value[2] * scalar];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [
  a[1] * b[2] - a[2] * b[1],
  a[2] * b[0] - a[0] * b[2],
  a[0] * b[1] - a[1] * b[0],
];
const length = (value) => Math.hypot(value[0], value[1], value[2]);
const normalize = (value) => {
  const magnitude = Math.max(length(value), 1e-6);
  return multiply(value, 1 / magnitude);
};

function rotatePoint(point, degrees) {
  const [rx, ry, rz] = degrees.map((value) => value * DEG);
  let [x, y, z] = point;
  let c = Math.cos(rx), s = Math.sin(rx);
  [y, z] = [y * c - z * s, y * s + z * c];
  c = Math.cos(ry); s = Math.sin(ry);
  [x, z] = [x * c + z * s, -x * s + z * c];
  c = Math.cos(rz); s = Math.sin(rz);
  [x, y] = [x * c - y * s, x * s + y * c];
  return [x, y, z];
}

function cameraBasis(state) {
  const azimuth = BASE_AZIMUTH + state.azimuth;
  const elevation = BASE_ELEVATION + state.elevation;
  const cosElevation = Math.cos(elevation);
  const position = add(BOSS_WORLD, [
    Math.sin(azimuth) * cosElevation * state.radius,
    Math.sin(elevation) * state.radius,
    Math.cos(azimuth) * cosElevation * state.radius,
  ]);
  const forward = normalize(subtract(BOSS_WORLD, position));
  const right = normalize(cross(forward, [0, 1, 0]));
  const up = normalize(cross(right, forward));
  return { position, forward, right, up };
}

function projectPoint(point, basis) {
  const relative = subtract(point, basis.position);
  const depth = Math.max(dot(relative, basis.forward), 0.25);
  const tangent = Math.tan(FOV * 0.5);
  return {
    point: [
      dot(relative, basis.right) / (depth * tangent) + COMPOSITION_OFFSET[0],
      dot(relative, basis.up) / (depth * tangent) + COMPOSITION_OFFSET[1],
    ],
    depth,
    scale: 1 / (depth * tangent),
  };
}

function projectRoute(points, basis, seed, terminal, energy) {
  const projected = points.map((point) => projectPoint(point, basis).point);
  return {
    a: projected[0], b: projected[1], c: projected[2], d: projected[3],
    world: points.map((point) => [...point]),
    seed, terminal, energy,
  };
}

export function createObservatoryCamera() {
  const current = { ...DEFAULT_STATE };
  const target = { ...DEFAULT_STATE };
  let lastTime = 0;

  return {
    current,
    target,
    orbit(deltaX, deltaY, viewportHeight = 1) {
      const unitsPerPixel = 0.82 / Math.max(viewportHeight, 1);
      target.azimuth = clamp(
        target.azimuth - deltaX * unitsPerPixel,
        ...OBSERVATORY_LIMITS.azimuth,
      );
      target.elevation = clamp(
        target.elevation + deltaY * unitsPerPixel,
        ...OBSERVATORY_LIMITS.elevation,
      );
    },
    dolly(deltaY) {
      target.radius = clamp(
        target.radius * Math.exp(deltaY * 0.00115),
        ...OBSERVATORY_LIMITS.radius,
      );
    },
    setState(next = {}, immediate = false) {
      if (Number.isFinite(next.azimuth)) {
        target.azimuth = clamp(next.azimuth, ...OBSERVATORY_LIMITS.azimuth);
      }
      if (Number.isFinite(next.elevation)) {
        target.elevation = clamp(next.elevation, ...OBSERVATORY_LIMITS.elevation);
      }
      if (Number.isFinite(next.radius)) {
        target.radius = clamp(next.radius, ...OBSERVATORY_LIMITS.radius);
      }
      if (immediate) Object.assign(current, target);
    },
    reset(immediate = false) {
      Object.assign(target, DEFAULT_STATE);
      if (immediate) Object.assign(current, target);
    },
    update(milliseconds) {
      const deltaSeconds = lastTime ? Math.min(0.05, (milliseconds - lastTime) * 0.001) : 0;
      lastTime = milliseconds;
      const smoothing = 1 - Math.exp(-deltaSeconds * 10.5);
      current.azimuth += (target.azimuth - current.azimuth) * smoothing;
      current.elevation += (target.elevation - current.elevation) * smoothing;
      current.radius += (target.radius - current.radius) * smoothing;
      return current;
    },
    snapshot() {
      return {
        azimuth: Number((current.azimuth / DEG).toFixed(2)),
        elevation: Number((current.elevation / DEG).toFixed(2)),
        radius: Number(current.radius.toFixed(2)),
      };
    },
  };
}

export function createSceneFrame(camera, aspect = 16 / 9) {
  void aspect;
  const basis = cameraBasis(camera.current);
  const planets = [];
  const routes = [];
  const systems = [];
  const bossProjection = projectPoint(BOSS_WORLD, basis);

  SYSTEMS.forEach((system, systemIndex) => {
    const worldPlanets = LOCAL_PLANETS.map((planet) => {
      const volumetricPoint = [planet.point[0], planet.point[1], planet.point[2] * system.depthScale];
      return add(system.center, rotatePoint(volumetricPoint, system.rotation));
    });
    const projectedCenter = projectPoint(system.center, basis);
    systems.push({
      world: [...system.center],
      center: projectedCenter.point,
      radius: 1.18 * projectedCenter.scale,
      energy: system.energy,
      depth: projectedCenter.depth,
    });

    LOCAL_PLANETS.forEach((planet, planetIndex) => {
      const world = worldPlanets[planetIndex];
      const projected = projectPoint(world, basis);
      planets.push({
        world: [...world],
        center: projected.point,
        radius: planet.radius * projected.scale,
        seed: system.seed + planetIndex * 2.31,
        heat: planet.heat,
        energy: system.energy,
        depth: projected.depth,
      });
    });

    const localUp = normalize(rotatePoint([0, 1, 0], system.rotation));
    INTERNAL_LINKS.forEach(([fromIndex, toIndex, bend], linkIndex) => {
      const start = worldPlanets[fromIndex];
      const end = worldPlanets[toIndex];
      const chord = subtract(end, start);
      const controlA = add(add(start, multiply(chord, 0.31)), multiply(localUp, bend));
      const controlB = add(add(start, multiply(chord, 0.69)), multiply(localUp, bend));
      routes.push(projectRoute(
        [start, controlA, controlB, end], basis,
        system.seed + linkIndex * 1.17, 0, system.energy,
      ));
    });

    const merge = worldPlanets[3];
    const towardBoss = normalize(subtract(BOSS_WORLD, merge));
    const endpoint = add(BOSS_WORLD, multiply(towardBoss, -BOSS_WORLD_RADIUS));
    const terminalLift = multiply(localUp, 0.34 - systemIndex * 0.11);
    const controlA = add(add(merge, multiply(towardBoss, 1.05)), terminalLift);
    const controlB = add(add(endpoint, multiply(towardBoss, -1.20)), multiply(terminalLift, -0.55));
    routes.push(projectRoute(
      [merge, controlA, controlB, endpoint], basis,
      system.seed + 6.7, 1, system.energy,
    ));
  });

  const bossDistance = camera.current.radius;
  const bossScale = BOSS_COMPOSITE_SCALE * DEFAULT_RADIUS / bossDistance;
  const viewAzimuth = clamp(camera.current.azimuth, -34 * DEG, 34 * DEG);
  const viewInclination = clamp(
    BOSS_DEFAULT_INCLINATION + camera.current.elevation,
    3 * DEG,
    38 * DEG,
  );
  const observerRadiusIndex = Math.round(clamp(
    BOSS_DEFAULT_RADIUS_INDEX * Math.sqrt(bossDistance / DEFAULT_RADIUS),
    0,
    1000,
  ));

  return {
    camera: {
      position: [...basis.position],
      pivot: [...BOSS_WORLD],
      target: [...BOSS_WORLD],
      forward: [...basis.forward],
      radius: camera.current.radius,
      azimuth: camera.current.azimuth,
      elevation: camera.current.elevation,
      fov: FOV,
    },
    planets,
    routes,
    systems,
    boss: {
      center: bossProjection.point,
      projectedCenter: bossProjection.point,
      scale: bossScale,
      depth: bossProjection.depth,
      distance: bossDistance,
      viewAzimuth,
      viewInclination,
      observerRadiusIndex,
      lensRadius: 0.31 * bossScale,
      lensStrength: 0.0105 * bossScale,
    },
  };
}
