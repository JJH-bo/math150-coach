export function isRapidTransitEdge(edge = {}, sourcePosition = null, targetPosition = null) {
  if (edge.decisionRole !== "progression") return false;
  if (!sourcePosition || !targetPosition) return true;
  return Number(targetPosition[2]) < Number(sourcePosition[2]) - 0.001;
}

export function buildRapidTransitControlPoints(sourcePosition, targetPosition, options = {}) {
  const source = copyPoint(sourcePosition);
  const target = copyPoint(targetPosition);
  const delta = subtract(target, source);
  const distance = Math.max(length(delta), 0.001);
  const direction = scale(delta, 1 / distance);
  const sourceInset = Math.min(distance * 0.16, Math.max(0, Number(options.sourceRadius || 0)) * 1.35);
  const targetInset = Math.min(distance * 0.2, Math.max(0, Number(options.targetRadius || 0)) * 1.35);
  const start = add(source, scale(direction, sourceInset));
  const end = add(target, scale(direction, -targetInset));
  const bend = Math.min(82, Math.max(18, distance * 0.085));
  const phase = Number(options.seed ?? 0.5) * Math.PI * 2;
  const fractions = [0, 0.24, 0.5, 0.76, 1];

  return fractions.map((fraction, index) => {
    const point = lerp(start, end, fraction);
    if (index === 0 || index === fractions.length - 1) return point;
    const envelope = Math.sin(fraction * Math.PI);
    point[0] += Math.cos(phase + fraction * Math.PI * 1.4) * bend * envelope;
    point[1] += Math.sin(phase * 0.7 + fraction * Math.PI * 1.7) * bend * 0.56 * envelope;
    return point;
  });
}

export function buildGuidedTransitWaypoints(cameraPosition, corridorPoints, destination) {
  const destinationPoint = copyPoint(destination);
  const usableCorridor = trimCorridorAtDestination(corridorPoints, destinationPoint);
  return [
    copyPoint(cameraPosition),
    ...usableCorridor,
    destinationPoint,
  ];
}

export function buildCombinedTransitControlPoints(routePointSets) {
  const combined = [];
  routePointSets.forEach((routePoints) => {
    routePoints.forEach((point) => {
      const next = copyPoint(point);
      const previous = combined.at(-1);
      if (previous && previous.every((value, index) => Math.abs(value - next[index]) < 0.0001)) return;
      combined.push(next);
    });
  });
  return combined;
}

function trimCorridorAtDestination(corridorPoints, destination) {
  const points = corridorPoints.map(copyPoint);
  if (points.length < 2) return points;
  const travelsDeeper = points.at(-1)[2] < points[0][2];
  return points.filter((point) => (
    travelsDeeper
      ? point[2] > destination[2] + 0.0001
      : point[2] < destination[2] - 0.0001
  ));
}

function copyPoint(point = [0, 0, 0]) {
  return [Number(point[0] || 0), Number(point[1] || 0), Number(point[2] || 0)];
}

function add(left, right) {
  return [left[0] + right[0], left[1] + right[1], left[2] + right[2]];
}

function subtract(left, right) {
  return [left[0] - right[0], left[1] - right[1], left[2] - right[2]];
}

function scale(point, amount) {
  return [point[0] * amount, point[1] * amount, point[2] * amount];
}

function length(point) {
  return Math.hypot(point[0], point[1], point[2]);
}

function lerp(start, end, amount) {
  return [
    start[0] + (end[0] - start[0]) * amount,
    start[1] + (end[1] - start[1]) * amount,
    start[2] + (end[2] - start[2]) * amount,
  ];
}
