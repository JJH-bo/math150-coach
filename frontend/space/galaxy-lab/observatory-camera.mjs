const DEG = Math.PI / 180;

export const OBSERVATORY_LIMITS = Object.freeze({
  panX: Object.freeze([-0.58, 0.58]),
  panY: Object.freeze([-0.42, 0.42]),
  zoom: Object.freeze([0.68, 1.55]),
});

const DEFAULT_STATE = Object.freeze({ panX: 0, panY: 0, zoom: 1 });
const CAMERA_TARGET = Object.freeze([-0.20, 0, -0.25]);
const CAMERA_POSITION = Object.freeze([-0.20, 0.10, 11.55]);
const BOSS_WORLD = Object.freeze([3.92, 0.02, -0.10]);
const BOSS_WORLD_RADIUS = 1.44;
const FOV = 42 * DEG;
const DEFAULT_DISTANCE = 11.8;
const BOSS_VIEW_AZIMUTH = 0;
const BOSS_VIEW_INCLINATION = 20.2 * DEG;
const BOSS_OBSERVER_RADIUS_INDEX = 620;
const BOSS_COMPOSITE_SCALE = 1.58;
const ORTHOGRAPHIC_SCALE = 1 / (DEFAULT_DISTANCE * Math.tan(FOV * 0.5));
const FIXED_FORWARD = Object.freeze([0, -Math.sin(0.5 * DEG), -Math.cos(0.5 * DEG)]);
const FIXED_RIGHT = Object.freeze([1, 0, 0]);
const FIXED_UP = Object.freeze([0, Math.cos(0.5 * DEG), -Math.sin(0.5 * DEG)]);

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

function projectPoint(point, state) {
  const relative = subtract(point, CAMERA_TARGET);
  const scale = ORTHOGRAPHIC_SCALE * state.zoom;
  return {
    point: [
      dot(relative, FIXED_RIGHT) * scale + state.panX,
      dot(relative, FIXED_UP) * scale + state.panY,
    ],
    depth: DEFAULT_DISTANCE + dot(relative, FIXED_FORWARD),
    scale,
  };
}

function projectRoute(points, state, seed, terminal, energy) {
  const projected = points.map((point) => projectPoint(point, state).point);
  return { a: projected[0], b: projected[1], c: projected[2], d: projected[3], seed, terminal, energy };
}

export function createObservatoryCamera() {
  const current = { ...DEFAULT_STATE };
  const target = { ...DEFAULT_STATE };
  let lastTime = 0;

  return {
    current,
    target,
    pan(deltaX, deltaY, viewportHeight = 1) {
      const unitsPerPixel = 2 / Math.max(viewportHeight, 1);
      target.panX = clamp(target.panX + deltaX * unitsPerPixel, ...OBSERVATORY_LIMITS.panX);
      target.panY = clamp(target.panY - deltaY * unitsPerPixel, ...OBSERVATORY_LIMITS.panY);
    },
    zoom(deltaY) {
      target.zoom = clamp(
        target.zoom * Math.exp(-deltaY * 0.00115),
        ...OBSERVATORY_LIMITS.zoom,
      );
    },
    setState(next = {}, immediate = false) {
      if (Number.isFinite(next.panX)) target.panX = clamp(next.panX, ...OBSERVATORY_LIMITS.panX);
      if (Number.isFinite(next.panY)) target.panY = clamp(next.panY, ...OBSERVATORY_LIMITS.panY);
      if (Number.isFinite(next.zoom)) target.zoom = clamp(next.zoom, ...OBSERVATORY_LIMITS.zoom);
      if (immediate) Object.assign(current, target);
    },
    reset(immediate = false) {
      Object.assign(target, DEFAULT_STATE);
      if (immediate) Object.assign(current, target);
    },
    update(milliseconds) {
      const deltaSeconds = lastTime ? Math.min(0.05, (milliseconds - lastTime) * 0.001) : 0;
      lastTime = milliseconds;
      const smoothing = 1 - Math.exp(-deltaSeconds * 11.5);
      current.panX += (target.panX - current.panX) * smoothing;
      current.panY += (target.panY - current.panY) * smoothing;
      current.zoom += (target.zoom - current.zoom) * smoothing;
      return current;
    },
    snapshot() {
      return {
        panX: Number(current.panX.toFixed(3)),
        panY: Number(current.panY.toFixed(3)),
        zoom: Number(current.zoom.toFixed(3)),
      };
    },
  };
}

export function createSceneFrame(camera, aspect = 16 / 9) {
  void aspect;
  const state = camera.current;
  const planets = [];
  const routes = [];
  const systems = [];
  const bossProjection = projectPoint(BOSS_WORLD, state);

  SYSTEMS.forEach((system, systemIndex) => {
    const worldPlanets = LOCAL_PLANETS.map((planet) => {
      const volumetricPoint = [planet.point[0], planet.point[1], planet.point[2] * system.depthScale];
      return add(system.center, rotatePoint(volumetricPoint, system.rotation));
    });
    const projectedCenter = projectPoint(system.center, state);
    systems.push({
      center: projectedCenter.point,
      radius: 1.18 * projectedCenter.scale,
      energy: system.energy,
      depth: projectedCenter.depth,
    });

    LOCAL_PLANETS.forEach((planet, planetIndex) => {
      const projected = projectPoint(worldPlanets[planetIndex], state);
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
        [start, controlA, controlB, end], state,
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
      [merge, controlA, controlB, endpoint], state,
      system.seed + 6.7, 1, system.energy,
    ));
  });

  const bossDistance = length(subtract(CAMERA_POSITION, BOSS_WORLD));
  const bossScale = BOSS_COMPOSITE_SCALE * state.zoom;

  return {
    camera: {
      position: [...CAMERA_POSITION],
      target: add(CAMERA_POSITION, FIXED_FORWARD),
      forward: [...FIXED_FORWARD],
      pan: [state.panX, state.panY],
      zoom: state.zoom,
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
      viewAzimuth: BOSS_VIEW_AZIMUTH,
      viewInclination: BOSS_VIEW_INCLINATION,
      observerRadiusIndex: BOSS_OBSERVER_RADIUS_INDEX,
      lensRadius: 0.31 * bossScale,
      lensStrength: 0.0105 * bossScale,
    },
  };
}
