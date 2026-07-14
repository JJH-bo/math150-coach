const MATERIAL_PILOT_NODE_ID = "ode_separable.concept";

export function isStellarMaterialPilotNode(definition = {}) {
  return definition.id === MATERIAL_PILOT_NODE_ID && definition.role === "training";
}

export function stellarProfileFor(definition = {}, qualityLevel = "high") {
  const seed = hashUnit(definition.id || MATERIAL_PILOT_NODE_ID);
  const difficulty = clamp(Number(definition.difficulty ?? 0.24), 0, 1);
  const highQuality = qualityLevel === "high";
  return {
    seed,
    radius: Number((Number(definition.radius || 14) * 1.7).toFixed(3)),
    activity: Number((0.55 + difficulty * 0.22 + seed * 0.08).toFixed(4)),
    noiseOctaves: highQuality ? 5 : 3,
    surfaceDetail: highQuality ? 5 : 4,
    granulationScale: Number((7.4 + seed * 2.1).toFixed(4)),
    flowSpeed: Number((0.035 + difficulty * 0.025).toFixed(4)),
    coronaLayers: highQuality ? 3 : 2,
    prominenceCount: highQuality ? 4 : 2,
    lightIntensity: highQuality ? 13 : 8,
    coreColor: 0xfff2cf,
    midColor: 0xffa24a,
    edgeColor: 0xd94820,
  };
}

function hashUnit(value) {
  let hash = 2166136261;
  for (const character of String(value)) {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) / 4294967295;
}

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}
