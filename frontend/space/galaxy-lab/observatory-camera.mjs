const DEG = Math.PI / 180;

export const OBSERVATORY_LIMITS = Object.freeze({
  yaw: Object.freeze([-32 * DEG, 32 * DEG]),
  pitch: Object.freeze([-16 * DEG, 18 * DEG]),
  distance: Object.freeze([8.6, 15.6]),
});

const DEFAULT_STATE = Object.freeze({ yaw: 0, pitch: 0.5 * DEG, distance: 10.0 });
const CAMERA_TARGET = Object.freeze([-0.20, 0, -0.25]);
const BOSS_WORLD = Object.freeze([3.92, 0.02, -0.10]);
const BOSS_WORLD_RADIUS = 1.44;
const FOV = 42 * DEG;
const BOSS_DEFAULT_INCLINATION = 20.2 * DEG;
const BOSS_DEFAULT_RADIUS_INDEX = 620;
const BOSS_COMPOSITE_SCALE = 1.58;

const SYSTEMS = Object.freeze([
  Object.freeze({ center: [-3.30, -0.78, 1.22], rotation: [-10, -7, 8], depthScale: 1.0, energy: 1.00, seed: 1.3 }),
  Object.freeze({ center: [-2.15, 1.75, -0.15], rotation: [18, 28, -8], depthScale: 3.2, energy: 0.82, seed: 5.2 }),
  Object.freeze({ center: [-2.70, -1.60, 0.40], rotation: [-22, -31, 12], depthScale: 3.4, energy: 0.66, seed: 9.4 }),
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
const mix = (a, b, amount) => add(multiply(a, 1 - amount), multiply(b, amount));

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
  const cosPitch = Math.cos(state.pitch);
  const position = add(CAMERA_TARGET, [
    Math.sin(state.yaw) * cosPitch * state.distance,
    Math.sin(state.pitch) * state.distance,
    Math.cos(state.yaw) * cosPitch * state.distance,
  ]);
  const forward = normalize(subtract(CAMERA_TARGET, position));
  const right = normalize(cross(forward, [0, 1, 0]));
  const up = normalize(cross(right, forward));
  return { position, forward, right, up };
}

const DEFAULT_BASIS = cameraBasis(DEFAULT_STATE);
const DEFAULT_BOSS_OFFSET = subtract(DEFAULT_BASIS.position, BOSS_WORLD);
const DEFAULT_BOSS_DISTANCE = length(DEFAULT_BOSS_OFFSET);
const DEFAULT_BOSS_AZIMUTH = Math.atan2(DEFAULT_BOSS_OFFSET[0], DEFAULT_BOSS_OFFSET[2]);
const DEFAULT_BOSS_ELEVATION = Math.asin(DEFAULT_BOSS_OFFSET[1] / DEFAULT_BOSS_DISTANCE);

function projectPoint(point, basis) {
  const relative = subtract(point, basis.position);
  const depth = Math.max(dot(relative, basis.forward), 0.25);
  const tangent = Math.tan(FOV * 0.5);
  return {
    point: [dot(relative, basis.right) / (depth * tangent), dot(relative, basis.up) / (depth * tangent)],
    depth,
    scale: 1 / (depth * tangent),
  };
}

function projectRoute(points, basis, seed, terminal, energy) {
  const projected = points.map((point) => projectPoint(point, basis).point);
  return { a: projected[0], b: projected[1], c: projected[2], d: projected[3], seed, terminal, energy };
}

export function createObservatoryCamera() {
  const current = { ...DEFAULT_STATE };
  const target = { ...DEFAULT_STATE };
  let lastTime = 0;

  return {
    current,
    target,
    rotate(deltaX, deltaY, viewportHeight = 1) {
      const scale = 0.72 / Math.max(viewportHeight, 1);
      target.yaw = clamp(target.yaw - deltaX * scale, ...OBSERVATORY_LIMITS.yaw);
      target.pitch = clamp(target.pitch + deltaY * scale, ...OBSERVATORY_LIMITS.pitch);
    },
    dolly(deltaY) {
      target.distance = clamp(
        target.distance + deltaY * 0.0024,
        ...OBSERVATORY_LIMITS.distance,
      );
    },
    setState(next = {}, immediate = false) {
      if (Number.isFinite(next.yaw)) {
        target.yaw = clamp(next.yaw, ...OBSERVATORY_LIMITS.yaw);
      }
      if (Number.isFinite(next.pitch)) {
        target.pitch = clamp(next.pitch, ...OBSERVATORY_LIMITS.pitch);
      }
      if (Number.isFinite(next.distance)) {
        target.distance = clamp(next.distance, ...OBSERVATORY_LIMITS.distance);
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
      const smoothing = 1 - Math.exp(-deltaSeconds * 9.5);
      current.yaw += (target.yaw - current.yaw) * smoothing;
      current.pitch += (target.pitch - current.pitch) * smoothing;
      current.distance += (target.distance - current.distance) * smoothing;
      return current;
    },
    snapshot() {
      return {
        yaw: Number((current.yaw / DEG).toFixed(2)),
        pitch: Number((current.pitch / DEG).toFixed(2)),
        distance: Number(current.distance.toFixed(2)),
      };
    },
  };
}

export function createSceneFrame(camera, aspect = 16 / 9) {
  const basis = cameraBasis(camera.current);
  const planets = [];
  const routes = [];
  const systems = [];
  const bossProjection = projectPoint(BOSS_WORLD, basis);
  const bossCenter = bossProjection.point;

  SYSTEMS.forEach((system, systemIndex) => {
    const worldPlanets = LOCAL_PLANETS.map((planet) => {
      const volumetricPoint = [
        planet.point[0],
        planet.point[1],
        planet.point[2] * system.depthScale,
      ];
      return add(system.center, rotatePoint(volumetricPoint, system.rotation));
    });
    const projectedCenter = projectPoint(system.center, basis);
    systems.push({
      center: projectedCenter.point,
      radius: 1.18 * projectedCenter.scale,
      energy: system.energy,
      depth: projectedCenter.depth,
    });

    LOCAL_PLANETS.forEach((planet, planetIndex) => {
      const projected = projectPoint(worldPlanets[planetIndex], basis);
      planets.push({
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
        [start, controlA, controlB, end],
        basis,
        system.seed + linkIndex * 1.17,
        0,
        system.energy,
      ));
    });

    const merge = worldPlanets[3];
    const towardBoss = normalize(subtract(BOSS_WORLD, merge));
    const endpoint = add(BOSS_WORLD, multiply(towardBoss, -BOSS_WORLD_RADIUS));
    const terminalLift = multiply(localUp, 0.34 - systemIndex * 0.11);
    const controlA = add(add(merge, multiply(towardBoss, 1.05)), terminalLift);
    const controlB = add(add(endpoint, multiply(towardBoss, -1.20)), multiply(terminalLift, -0.55));
    const terminalRoute = projectRoute(
      [merge, controlA, controlB, endpoint],
      basis,
      system.seed + 6.7,
      1,
      system.energy,
    );
    routes.push(terminalRoute);
  });

  const bossOffset = subtract(basis.position, BOSS_WORLD);
  const bossDistance = length(bossOffset);
  const bossAzimuth = Math.atan2(bossOffset[0], bossOffset[2]);
  const bossElevation = Math.asin(bossOffset[1] / Math.max(bossDistance, 1e-6));
  const viewAzimuth = clamp(bossAzimuth - DEFAULT_BOSS_AZIMUTH, -34 * DEG, 34 * DEG);
  const viewInclination = clamp(
    BOSS_DEFAULT_INCLINATION + bossElevation - DEFAULT_BOSS_ELEVATION,
    3 * DEG,
    38 * DEG,
  );
  const observerRadiusIndex = Math.round(clamp(
    BOSS_DEFAULT_RADIUS_INDEX * Math.sqrt(bossDistance / DEFAULT_BOSS_DISTANCE),
    0,
    1000,
  ));
  const bossAngularScale = DEFAULT_BOSS_DISTANCE / bossDistance;
  const bossScale = BOSS_COMPOSITE_SCALE * bossAngularScale;

  return {
    camera: {
      position: [...basis.position],
      target: [...CAMERA_TARGET],
      forward: [...basis.forward],
      fov: FOV,
    },
    planets,
    routes,
    systems,
    boss: {
      center: bossCenter,
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
