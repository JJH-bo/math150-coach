const PORTAL_VERTEX_SHADER = `
  precision highp float;
  varying vec2 vUv;
  varying vec3 vPosition;
  void main() {
    vUv = uv;
    vPosition = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const DOMAIN_WARP_GLSL = `
  float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
  }

  float valueNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash21(i);
    float b = hash21(i + vec2(1.0, 0.0));
    float c = hash21(i + vec2(0.0, 1.0));
    float d = hash21(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
  }

  float fbm(vec2 p) {
    float value = 0.0;
    float amplitude = 0.5;
    mat2 rotation = mat2(0.8, -0.6, 0.6, 0.8);
    for (int octave = 0; octave < 5; octave += 1) {
      value += valueNoise(p) * amplitude;
      p = rotation * p * 2.03 + vec2(7.13, 3.71);
      amplitude *= 0.5;
    }
    return value;
  }

  vec2 domainWarp(vec2 p, float seed, float motion) {
    vec2 q = vec2(
      fbm(p + vec2(seed * 9.7, motion * 0.13)),
      fbm(p + vec2(5.2 - motion * 0.11, seed * 7.3))
    );
    vec2 r = vec2(
      fbm(p + q * 3.1 + vec2(1.7, 9.2)),
      fbm(p + q * 2.7 + vec2(8.3, 2.8))
    );
    return p + (q - 0.5) * 0.72 + (r - 0.5) * 0.46;
  }
`;

const BALANCED_DOMAIN_WARP_GLSL = DOMAIN_WARP_GLSL.replace("octave < 5", "octave < 3");

const APERTURE_FRAGMENT_SHADER = `
  precision highp float;
  uniform vec3 accent;
  uniform vec3 coreColor;
  uniform float time;
  uniform float activity;
  uniform float seed;
  uniform float coreRadius;
  uniform float bossMode;
  varying vec2 vUv;
  ${DOMAIN_WARP_GLSL}

  void main() {
    vec2 p = vUv * 2.0 - 1.0;
    float radius = length(p);
    float angle = atan(p.y, p.x);
    vec2 warped = domainWarp(p * 3.15, seed, time * 0.2);
    float warpedRadius = length(warped);
    float vortexAngle = atan(warped.y, warped.x);
    float spiral = pow(0.5 + 0.5 * sin(vortexAngle * (9.0 + bossMode * 3.0) - log(radius + 0.06) * 31.0 + time * 0.3), 6.0);
    float counterSpiral = pow(0.5 + 0.5 * sin(angle * 17.0 + log(radius + 0.12) * 19.0 - time * 0.12), 10.0);
    float depthBands = pow(0.5 + 0.5 * sin(log(radius + 0.055) * 42.0 - angle * 2.0), 12.0);
    float tunnel = smoothstep(coreRadius * 0.72, 0.82, radius) * (1.0 - smoothstep(0.82, 1.0, radius));
    float rim = smoothstep(0.5, 0.92, warpedRadius) * (1.0 - smoothstep(0.83, 1.02, radius));
    float turbulence = fbm(warped * 3.4 - vec2(time * 0.025, seed * 5.0));
    vec2 cells = floor((warped + vec2(seed * 2.0)) * 92.0);
    float stars = step(0.9935, hash21(cells)) * smoothstep(coreRadius * 0.8, 0.94, radius);
    float centralVoid = 1.0 - smoothstep(coreRadius * 0.72, coreRadius * 1.28, radius);
    vec3 heatColor = mix(accent, vec3(1.0, 0.48, 0.2), bossMode * 0.42);
    vec3 color = coreColor * (0.58 + radius * 0.34);
    color += accent * turbulence * tunnel * (0.018 + activity * 0.025);
    color += heatColor * spiral * tunnel * (0.04 + activity * 0.052);
    color += accent * counterSpiral * tunnel * 0.026;
    color += heatColor * depthBands * tunnel * (0.014 + bossMode * 0.018);
    color += heatColor * rim * (0.035 + spiral * 0.072) * activity;
    color += mix(accent, vec3(1.0), 0.82) * stars * (0.48 + activity * 0.26);
    color *= 1.0 - centralVoid * (0.78 + bossMode * 0.08);
    float alpha = (1.0 - smoothstep(0.95, 1.0, radius)) * 0.98;
    gl_FragColor = vec4(color, alpha);
  }
`;

const DEPTH_CHAMBER_FRAGMENT_SHADER = `
  precision highp float;
  uniform vec3 accent;
  uniform vec3 hotColor;
  uniform float time;
  uniform float activity;
  uniform float seed;
  uniform float layer;
  uniform float bossMode;
  varying vec2 vUv;
  ${DOMAIN_WARP_GLSL}

  void main() {
    vec2 p = vUv * 2.0 - 1.0;
    float radius = length(p);
    float angle = atan(p.y, p.x);
    vec2 warped = domainWarp(p * (3.5 + layer * 1.4), seed + layer * 0.31, time * (0.16 + layer * 0.04));
    float turbulence = fbm(warped * 3.2 + vec2(layer * 6.0));
    float spiral = pow(0.5 + 0.5 * sin(angle * (8.0 + bossMode * 3.0) - radius * 24.0 + warped.x * 8.0 - time * 0.22), 8.0);
    float fracture = pow(0.5 + 0.5 * sin(angle * 19.0 + warped.y * 13.0 + time * 0.11), 18.0);
    float edge = 1.0 - smoothstep(0.57, 0.98, radius);
    float innerFade = smoothstep(0.08, 0.4, radius);
    float hotArc = pow(max(0.0, cos(angle - 0.72 - layer * 1.7)), 13.0);
    hotArc += 0.58 * pow(max(0.0, cos(angle + 2.3 + layer * 0.8)), 17.0);
    vec3 color = mix(accent * (0.28 + turbulence * 0.55), hotColor, clamp(hotArc + spiral * 0.26, 0.0, 1.0));
    float energy = edge * innerFade * (spiral * 0.42 + fracture * 0.22 + turbulence * 0.18 + hotArc * 0.52);
    float alpha = energy * (0.1 + activity * 0.13) * mix(1.0, 0.62, layer);
    if (alpha < 0.004) discard;
    gl_FragColor = vec4(color, alpha);
  }
`;

const FUNNEL_VERTEX_SHADER = `
  precision highp float;
  uniform float time;
  uniform float distortion;
  uniform float seed;
  varying vec2 vUv;
  varying float vDepth;

  void main() {
    vUv = uv;
    vDepth = uv.y;
    vec3 transformed = position;
    float wave = sin(uv.x * 31.4159 + seed * 9.0 + uv.y * 8.0 - time * 0.16);
    wave += sin(uv.x * 69.115 + seed * 17.0 - uv.y * 15.0 + time * 0.11) * 0.36;
    float depthProfile = sin(uv.y * 3.14159265);
    transformed.xz *= 1.0 + wave * distortion * depthProfile;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(transformed, 1.0);
  }
`;

const THROAT_FRAGMENT_SHADER = `
  precision highp float;
  uniform vec3 accent;
  uniform vec3 coreColor;
  uniform float time;
  uniform float activity;
  uniform float seed;
  varying vec2 vUv;
  varying float vDepth;
  ${DOMAIN_WARP_GLSL}

  void main() {
    vec2 p = vec2(vUv.x * 7.0, vUv.y * 3.4);
    vec2 warped = domainWarp(p, seed, time * 0.22);
    float laneA = pow(0.5 + 0.5 * sin(warped.x * 18.0 - warped.y * 12.0 + time * 0.22), 14.0);
    float laneB = pow(0.5 + 0.5 * sin(warped.x * 31.0 + warped.y * 17.0 - time * 0.15), 22.0);
    float depthFade = smoothstep(0.0, 0.92, vDepth);
    float edgeEnergy = smoothstep(0.0, 0.18, vDepth) * (1.0 - smoothstep(0.72, 1.0, vDepth));
    float filaments = laneA * 0.72 + laneB * 0.36;
    vec3 color = coreColor * (0.82 - depthFade * 0.28);
    color += accent * filaments * edgeEnergy * (0.025 + activity * 0.055);
    color += accent * fbm(warped * 1.7) * edgeEnergy * 0.012;
    float alpha = 0.18 + edgeEnergy * 0.1 + filaments * activity * 0.055;
    gl_FragColor = vec4(color, alpha);
  }
`;

const VOLUMETRIC_MANTLE_FRAGMENT_SHADER = `
  precision highp float;
  uniform vec3 accent;
  uniform vec3 hotColor;
  uniform float time;
  uniform float activity;
  uniform float seed;
  uniform float layer;
  uniform float bossMode;
  varying vec2 vUv;
  ${DOMAIN_WARP_GLSL}

  void main() {
    vec2 p = vUv * 2.0 - 1.0;
    float radius = length(p);
    float angle = atan(p.y, p.x);
    vec2 warped = domainWarp(p * (2.25 + layer * 0.31), seed + layer * 0.17, time * (0.13 + layer * 0.025));
    float turbulence = fbm(warped * 2.35 + vec2(layer * 3.4));
    float detail = fbm(warped * 5.7 - vec2(time * 0.025, seed * 4.0));
    vec2 polarNoise = vec2(cos(angle), sin(angle)) * 3.1;
    polarNoise += vec2(seed * 4.0 + layer * 1.7, layer * 2.7 + time * 0.035);
    float boundaryNoise = fbm(polarNoise);
    float innerRadius = mix(0.5, 0.58, layer) + (boundaryNoise - 0.5) * (0.13 + bossMode * 0.08);
    float outerRadius = mix(0.76, 0.89, layer) + (turbulence - 0.5) * (0.17 + bossMode * 0.09);
    float aperture = smoothstep(innerRadius - 0.075, innerRadius + 0.08, radius);
    float outer = 1.0 - smoothstep(outerRadius - 0.13, outerRadius + 0.12, radius);
    float mantle = aperture * outer;
    float braidFrequency = 7.0 + floor(layer * 3.0 + 0.5) * 2.0;
    float braided = pow(0.5 + 0.5 * sin(angle * braidFrequency - radius * 21.0 + warped.x * 9.0 - time * 0.13), 9.0);
    float braidBreak = smoothstep(0.45, 0.77, fbm(warped * 3.8 + vec2(layer * 5.0, seed * 3.0)));
    braided *= 0.12 + braidBreak * 0.88;
    float hair = pow(0.5 + 0.5 * sin(angle * 17.0 + warped.y * 16.0 - radius * 39.0), 21.0);
    hair *= smoothstep(0.38, 0.72, detail);
    float cloud = smoothstep(0.48, 0.82, turbulence * 0.72 + detail * 0.46);
    float innerEdge = 1.0 - smoothstep(0.018, 0.095, abs(radius - innerRadius));
    innerEdge *= 0.25 + smoothstep(0.38, 0.74, detail) * 0.75;
    float wisps = mantle * (cloud * 0.34 + braided * 0.34 + hair * 0.27 + innerEdge * 0.42);
    float outsideWisp = (1.0 - smoothstep(0.66, 1.13, radius)) * smoothstep(0.31, 0.57, radius);
    outsideWisp *= pow(max(0.0, turbulence - 0.43), 1.4) * (0.3 + braided * 0.7);
    float hotspot = pow(max(0.0, cos(angle - 0.68 + seed * 2.4)), 13.0);
    hotspot += 0.72 * pow(max(0.0, cos(angle + 2.2 + layer)), 18.0);
    vec3 cold = accent * (0.2 + turbulence * 0.7);
    vec3 color = mix(cold, hotColor, clamp(braided * 0.28 + hotspot * 0.7 + hair * 0.24 + innerEdge * 0.2, 0.0, 1.0));
    color += hotColor * hotspot * (0.3 + bossMode * 0.16);
    float alpha = (wisps * (0.09 + activity * 0.11) + outsideWisp * (0.04 + activity * 0.065));
    alpha += hotspot * mantle * (0.055 + activity * 0.095);
    alpha *= 1.0 - smoothstep(1.02, 1.2, radius);
    if (alpha < 0.004) discard;
    gl_FragColor = vec4(color, alpha);
  }
`;

const FILAMENT_VEIL_FRAGMENT_SHADER = `
  precision highp float;
  uniform sampler2D veilMap;
  uniform vec3 accent;
  uniform vec3 hotColor;
  uniform float opacity;
  uniform float time;
  uniform float seed;
  varying vec2 vUv;

  void main() {
    vec4 sampleColor = texture2D(veilMap, vUv);
    float luminance = dot(sampleColor.rgb, vec3(0.2126, 0.7152, 0.0722));
    vec2 p = vUv * 2.0 - 1.0;
    float radius = length(vec2(p.x * 1.5, p.y));
    float edgeFade = 1.0 - smoothstep(0.72, 1.03, radius);
    float energy = smoothstep(0.018, 0.72, luminance);
    float strands = pow(energy, 1.05);
    float shimmer = 0.94 + sin(time * 0.17 + seed * 9.0 + luminance * 8.0) * 0.06;
    vec3 color = mix(accent, hotColor, smoothstep(0.28, 0.92, luminance));
    float alpha = strands * edgeFade * opacity * shimmer;
    if (alpha < 0.006) discard;
    gl_FragColor = vec4(color, alpha);
  }
`;

const RIM_FRAGMENT_SHADER = `
  precision highp float;
  uniform vec3 accent;
  uniform float time;
  uniform float intensity;
  uniform float irregularity;
  uniform float seed;
  varying vec2 vUv;
  ${DOMAIN_WARP_GLSL}

  void main() {
    vec2 p = vUv * 2.0 - 1.0;
    float radius = length(p);
    float angle = atan(p.y, p.x);
    vec2 polarNoise = vec2(cos(angle), sin(angle)) * 3.4;
    polarNoise += vec2(seed * 8.0, time * 0.055);
    float noise = fbm(polarNoise);
    float target = 0.89 + (noise - 0.5) * irregularity * 0.13;
    float rimWidth = mix(0.022, 0.012, irregularity);
    float radial = 1.0 - smoothstep(rimWidth, rimWidth * 4.8, abs(radius - target));
    float breakup = sin(angle * 7.0 + noise * 8.0 + time * 0.18) + 0.54 * sin(angle * 17.0 - time * 0.12);
    float gaps = mix(0.72, smoothstep(-0.12, 0.62, breakup), irregularity);
    float hot = pow(max(0.0, cos(angle - 0.72 - sin(time * 0.1) * 0.08)), 10.0);
    hot += 0.46 * pow(max(0.0, cos(angle + 2.15)), 15.0);
    vec3 color = mix(accent, vec3(1.0), hot * 0.72) * (0.5 + hot * intensity * 1.7);
    float alpha = radial * gaps * (0.07 + intensity * (0.11 + hot * 0.3));
    gl_FragColor = vec4(color, alpha);
  }
`;

const BALANCED_APERTURE_FRAGMENT_SHADER = APERTURE_FRAGMENT_SHADER.replace(DOMAIN_WARP_GLSL, BALANCED_DOMAIN_WARP_GLSL);
const BALANCED_THROAT_FRAGMENT_SHADER = THROAT_FRAGMENT_SHADER.replace(DOMAIN_WARP_GLSL, BALANCED_DOMAIN_WARP_GLSL);
const BALANCED_DEPTH_CHAMBER_FRAGMENT_SHADER = DEPTH_CHAMBER_FRAGMENT_SHADER.replace(DOMAIN_WARP_GLSL, BALANCED_DOMAIN_WARP_GLSL);
const BALANCED_VOLUMETRIC_MANTLE_FRAGMENT_SHADER = VOLUMETRIC_MANTLE_FRAGMENT_SHADER.replace(DOMAIN_WARP_GLSL, BALANCED_DOMAIN_WARP_GLSL);
const BALANCED_RIM_FRAGMENT_SHADER = RIM_FRAGMENT_SHADER.replace(DOMAIN_WARP_GLSL, BALANCED_DOMAIN_WARP_GLSL);

const GLINT_VERTEX_SHADER = `
  precision highp float;
  attribute float size;
  attribute float energy;
  varying float vEnergy;
  void main() {
    vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
    gl_Position = projectionMatrix * viewPosition;
    gl_PointSize = min(size * (360.0 / max(2.0, -viewPosition.z)), 24.0);
    vEnergy = energy;
  }
`;

const GLINT_FRAGMENT_SHADER = `
  precision highp float;
  uniform vec3 accent;
  varying float vEnergy;
  void main() {
    vec2 p = abs(gl_PointCoord - vec2(0.5));
    float core = 1.0 - smoothstep(0.0, 0.12, length(p));
    float horizontal = exp(-p.y * 72.0) * (1.0 - smoothstep(0.04, 0.5, p.x));
    float vertical = exp(-p.x * 72.0) * (1.0 - smoothstep(0.04, 0.5, p.y));
    float diagonal = exp(-abs(p.x - p.y) * 54.0) * (1.0 - smoothstep(0.0, 0.32, length(p))) * 0.34;
    float glow = clamp(core + horizontal * 0.82 + vertical * 0.82 + diagonal, 0.0, 1.0) * vEnergy;
    if (glow < 0.01) discard;
    gl_FragColor = vec4(mix(accent, vec3(1.0), 0.78), glow);
  }
`;

let portalEnergyVeilTexture = null;

const INFALL_VERTEX_SHADER = `
  attribute vec4 seed;
  uniform float time;
  uniform float radius;
  uniform float depth;
  uniform float speed;
  varying float vLife;
  void main() {
    float progress = fract(seed.z + time * speed);
    float radial = mix(seed.y, radius * 0.12, pow(progress, 0.82));
    float angle = seed.x + progress * (4.2 + seed.z * 2.4);
    vec3 transformed = vec3(
      cos(angle) * radial,
      sin(angle) * radial,
      mix(seed.w, -depth * 0.82, progress)
    );
    vec4 viewPosition = modelViewMatrix * vec4(transformed, 1.0);
    gl_Position = projectionMatrix * viewPosition;
    gl_PointSize = (0.8 + seed.z * 1.55) * (260.0 / max(2.0, -viewPosition.z));
    vLife = sin(progress * 3.14159265);
  }
`;

const INFALL_FRAGMENT_SHADER = `
  uniform vec3 accent;
  varying float vLife;
  void main() {
    vec2 p = gl_PointCoord - vec2(0.5);
    float glow = 1.0 - smoothstep(0.04, 0.5, length(p));
    gl_FragColor = vec4(accent, glow * vLife * 0.72);
  }
`;

export function detectQualityLevel() {
  const memory = Number(navigator.deviceMemory || 4);
  const mobile = matchMedia("(pointer: coarse)").matches;
  if (mobile || memory <= 3) return "balanced";
  return "high";
}

export function createCelestialNode(THREE, definition, qualityLevel = detectQualityLevel()) {
  if (definition.role === "boss") return createBossCataclysm(THREE, definition, qualityLevel);
  if (definition.role === "auxiliary") return createAuxiliaryStar(THREE, definition, qualityLevel);
  if (definition.role === "repair") return createRepairSingularity(THREE, definition, qualityLevel);
  if (definition.role === "domain") return createKnowledgeDomain(THREE, definition, qualityLevel);
  return createKnowledgeSingularity(THREE, definition, qualityLevel);
}

export function createKnowledgeSingularity(THREE, definition, qualityLevel = "high") {
  const group = baseGroup(THREE, definition);
  const accent = new THREE.Color(definition.color || 0x7ddff7);
  const difficulty = clamp(definition.difficulty ?? 0.5, 0, 1);
  const depth = definition.radius * (1.08 + difficulty * 0.88);
  const throat = createPortalThroat(THREE, definition.radius, depth, accent, {
    activity: 0.62 + difficulty * 0.58,
    coreColor: 0x000207,
    qualityLevel,
    mouthScale: 1.34 + difficulty * 0.08,
    seed: hashAngle(definition.id),
    distortion: 0.035 + difficulty * 0.035,
  });
  group.add(throat.group);

  const mantle = createVolumetricMantle(THREE, definition.radius, accent, {
    activity: 0.7 + difficulty * 0.5,
    seed: hashAngle(definition.id),
    qualityLevel,
    scale: 2.12 + difficulty * 0.22,
  });
  group.add(mantle.group);
  const veil = createFilamentVeil(THREE, definition.radius, accent, {
    opacity: 0.72 + difficulty * 0.12,
    seed: hashAngle(definition.id),
    scale: 6.5 + difficulty * 0.45,
    hotColor: accent.clone().lerp(new THREE.Color(0xffffff), 0.86),
  });
  group.add(veil.mesh);

  const rim = createDistortedRim(THREE, definition.radius, accent, {
    intensity: 0.46 + difficulty * 0.46,
    irregularity: 0.18 + difficulty * 0.46,
    qualityLevel,
    seed: hashAngle(definition.id),
  });
  group.add(rim.mesh);
  const arcs = createEnergyFilaments(THREE, definition.radius, accent, {
    count: 0,
    thickness: 0.0048 + difficulty * 0.002,
    intensity: 0.4 + difficulty * 0.28,
    seed: hashAngle(definition.id),
    qualityLevel,
  });
  addMeshes(group, arcs.meshes);
  const glints = createEnergyGlints(THREE, definition.radius, accent, {
    count: qualityLevel === "high" ? 5 + Math.round(difficulty * 3) : 4,
    seed: hashAngle(definition.id),
  });
  group.add(glints.points);

  const infall = createInfallField(THREE, definition.radius, depth, accent, {
    count: qualityLevel === "high" ? 82 + Math.round(difficulty * 76) : 58,
    speed: 0.07 + difficulty * 0.035,
    seed: hashAngle(definition.id),
  });
  group.add(infall.points);
  const mist = createGasCloudHalo(THREE, definition.radius * (3.75 + difficulty * 0.62), accent, 0.15 + difficulty * 0.09, {
    seed: hashAngle(definition.id),
    qualityLevel,
  });
  mist.position.z = -depth * 0.28;
  group.add(mist);
  const halo = createCoronaSprite(THREE, definition.radius * (4.2 + difficulty), accent, 0.08 + difficulty * 0.07);
  halo.position.z = -depth * 0.72;
  group.add(halo);
  const beacon = createStatusBeacon(THREE, definition.radius, accent);
  group.add(beacon);

  const node = finalizeNode(
    definition,
    group,
    [...throat.materials, ...mantle.materials, veil.material, rim.material, ...arcs.materials, glints.material, infall.material],
    [...mantle.meshes, veil.mesh, ...arcs.meshes, infall.points],
    [mist, halo],
    beacon,
  );
  node.userData.portal = true;
  return node;
}

export function createAuxiliaryStar(THREE, definition, qualityLevel = "high") {
  const group = baseGroup(THREE, definition);
  const accent = new THREE.Color(definition.color || 0xd9f1f4);
  const depth = definition.radius * 0.58;
  const throat = createPortalThroat(THREE, definition.radius, depth, accent, {
    activity: 0.28,
    coreColor: 0x101a20,
    qualityLevel,
    auxiliary: true,
    mouthScale: 1.2,
    openness: 0.86,
    seed: hashAngle(definition.id),
    distortion: 0.018,
  });
  group.add(throat.group);
  const mantle = createVolumetricMantle(THREE, definition.radius, accent, {
    activity: 0.34,
    seed: hashAngle(definition.id),
    qualityLevel,
    scale: 1.78,
    hotColor: accent.clone().lerp(new THREE.Color(0xffffff), 0.82),
  });
  group.add(mantle.group);
  const veil = createFilamentVeil(THREE, definition.radius, accent, {
    opacity: 0.34,
    seed: hashAngle(definition.id),
    scale: 5.25,
    hotColor: accent.clone().lerp(new THREE.Color(0xffffff), 0.92),
  });
  group.add(veil.mesh);
  const rim = createDistortedRim(THREE, definition.radius, accent, {
    intensity: 0.35,
    irregularity: 0.08,
    qualityLevel,
    seed: hashAngle(definition.id),
  });
  group.add(rim.mesh);
  const arcs = createEnergyFilaments(THREE, definition.radius, accent, {
    count: 0,
    thickness: 0.004,
    intensity: 0.26,
    seed: hashAngle(definition.id),
    qualityLevel,
  });
  addMeshes(group, arcs.meshes);
  const glints = createEnergyGlints(THREE, definition.radius, accent, {
    count: qualityLevel === "high" ? 3 : 2,
    seed: hashAngle(definition.id),
  });
  group.add(glints.points);
  const infall = createInfallField(THREE, definition.radius, depth, accent, {
    count: qualityLevel === "high" ? 34 : 22,
    speed: 0.045,
    seed: hashAngle(definition.id),
  });
  group.add(infall.points);
  const mist = createGasCloudHalo(THREE, definition.radius * 3.8, accent, 0.09, {
    seed: hashAngle(definition.id),
    softness: 1.2,
    qualityLevel,
  });
  mist.position.z = -depth * 0.28;
  group.add(mist);
  const halo = createCoronaSprite(THREE, definition.radius * 4.4, accent, 0.1);
  halo.position.z = -depth * 0.6;
  group.add(halo);
  const beacon = createStatusBeacon(THREE, definition.radius, accent);
  group.add(beacon);

  const node = finalizeNode(
    definition,
    group,
    [...throat.materials, ...mantle.materials, veil.material, rim.material, ...arcs.materials, glints.material, infall.material],
    [...mantle.meshes, veil.mesh, ...arcs.meshes, infall.points],
    [mist, halo],
    beacon,
  );
  node.userData.auxiliary = true;
  node.userData.portal = true;
  return node;
}

export function createRepairSingularity(THREE, definition, qualityLevel = "high") {
  const group = baseGroup(THREE, definition);
  const accent = new THREE.Color(definition.color || 0xa66f9e);
  const depth = definition.radius * 1.28;
  const throat = createPortalThroat(THREE, definition.radius, depth, accent, {
    activity: 0.92,
    coreColor: 0x050107,
    qualityLevel,
    mouthScale: 1.46,
    seed: hashAngle(definition.id),
    distortion: 0.085,
  });
  group.add(throat.group);
  const mantle = createVolumetricMantle(THREE, definition.radius, accent, {
    activity: 1.02,
    seed: hashAngle(definition.id),
    qualityLevel,
    scale: 2.42,
    hotColor: accent.clone().offsetHSL(-0.02, 0.04, 0.26),
  });
  group.add(mantle.group);
  const veil = createFilamentVeil(THREE, definition.radius, accent, {
    opacity: 0.72,
    seed: hashAngle(definition.id),
    scale: 7.15,
    hotColor: accent.clone().lerp(new THREE.Color(0xffffff), 0.78),
  });
  group.add(veil.mesh);
  const rim = createDistortedRim(THREE, definition.radius, accent, {
    intensity: 0.94,
    irregularity: 0.92,
    qualityLevel,
    seed: hashAngle(definition.id),
  });
  group.add(rim.mesh);
  const arcs = createEnergyFilaments(THREE, definition.radius, accent.clone().offsetHSL(-0.02, 0.06, 0.14), {
    count: qualityLevel === "high" ? 2 : 1,
    thickness: 0.006,
    intensity: 0.56,
    seed: hashAngle(definition.id),
    qualityLevel,
    fracture: true,
  });
  addMeshes(group, arcs.meshes);
  const glints = createEnergyGlints(THREE, definition.radius, accent, {
    count: qualityLevel === "high" ? 8 : 5,
    seed: hashAngle(definition.id),
  });
  group.add(glints.points);
  const infall = createInfallField(THREE, definition.radius, depth, accent, {
    count: qualityLevel === "high" ? 128 : 76,
    speed: 0.105,
    seed: hashAngle(definition.id),
  });
  group.add(infall.points);
  const halo = createCoronaSprite(THREE, definition.radius * 5.4, accent, 0.16);
  halo.position.z = -depth * 0.65;
  group.add(halo);
  const beacon = createStatusBeacon(THREE, definition.radius, accent);
  group.add(beacon);

  const node = finalizeNode(
    definition,
    group,
    [...throat.materials, ...mantle.materials, veil.material, rim.material, infall.material, ...arcs.materials, glints.material],
    [...mantle.meshes, veil.mesh, ...arcs.meshes, infall.points],
    [halo],
    beacon,
  );
  node.userData.repair = true;
  node.userData.portal = true;
  return node;
}

export function createBossCataclysm(THREE, definition, qualityLevel = "high") {
  const group = baseGroup(THREE, definition);
  const ember = new THREE.Color(0xa72718);
  const whiteHeat = new THREE.Color(0xe36a2e);
  const bloodCloud = new THREE.Color(0x651014);
  const depth = definition.radius * 1.82;
  const throat = createPortalThroat(THREE, definition.radius, depth, ember, {
    activity: 1.45,
    coreColor: 0x030001,
    qualityLevel,
    openness: 0.68,
    mouthScale: 1.62,
    coreRadius: 0.29,
    hotColor: whiteHeat,
    boss: true,
    seed: hashAngle(definition.id),
    distortion: 0.12,
  });
  group.add(throat.group);
  const mantle = createVolumetricMantle(THREE, definition.radius, ember, {
    activity: 1.48,
    seed: hashAngle(definition.id),
    qualityLevel,
    scale: 2.76,
    hotColor: whiteHeat,
    boss: true,
  });
  group.add(mantle.group);
  const veil = createFilamentVeil(THREE, definition.radius, ember, {
    opacity: 0.78,
    seed: hashAngle(definition.id),
    scale: 8.45,
    hotColor: whiteHeat,
    boss: true,
  });
  group.add(veil.mesh);
  const rim = createDistortedRim(THREE, definition.radius, whiteHeat, {
    intensity: 1.08,
    irregularity: 0.98,
    qualityLevel,
    seed: hashAngle(definition.id),
  });
  group.add(rim.mesh);
  const innerArcs = createEnergyFilaments(THREE, definition.radius, whiteHeat, {
    count: 0,
    thickness: 0.0035,
    intensity: 0.24,
    seed: hashAngle(definition.id),
    qualityLevel,
    fracture: true,
    boss: true,
  });
  addMeshes(group, innerArcs.meshes);
  const outerArcs = createEnergyFilaments(THREE, definition.radius * 1.36, ember, {
    count: 0,
    thickness: 0.003,
    intensity: 0.18,
    seed: hashAngle(definition.id) + 0.37,
    qualityLevel,
    wide: true,
    boss: true,
  });
  addMeshes(group, outerArcs.meshes);
  const glints = createEnergyGlints(THREE, definition.radius * 1.2, whiteHeat, {
    count: qualityLevel === "high" ? 7 : 5,
    seed: hashAngle(definition.id),
    boss: true,
  });
  group.add(glints.points);
  const infall = createInfallField(THREE, definition.radius * 1.42, depth, whiteHeat, {
    count: qualityLevel === "high" ? 340 : 190,
    speed: 0.13,
    seed: hashAngle(definition.id),
  });
  group.add(infall.points);

  const gasEnvelope = createBossGasEnvelope(THREE, definition.radius, [bloodCloud, ember, whiteHeat], qualityLevel);
  group.add(...gasEnvelope.clouds);
  const outerGasHalo = createGasCloudHalo(THREE, definition.radius * 6.7, bloodCloud, 0.22, {
    seed: hashAngle(definition.id),
    turbulence: 1.35,
    qualityLevel,
    boss: true,
  });
  outerGasHalo.position.z = -depth * 0.52;
  outerGasHalo.rotation.z = 0.46;
  const hotGasHalo = createGasCloudHalo(THREE, definition.radius * 4.8, whiteHeat, 0.15, {
    seed: hashAngle(definition.id) + 0.41,
    turbulence: 0.92,
    qualityLevel,
    boss: true,
  });
  hotGasHalo.position.z = -depth * 0.34;
  hotGasHalo.rotation.z = -0.28;
  group.add(outerGasHalo, hotGasHalo);
  const halo = createCoronaSprite(THREE, definition.radius * 9.2, bloodCloud, 0.16);
  halo.position.z = -depth * 0.82;
  group.add(halo);
  const beacon = createStatusBeacon(THREE, definition.radius, whiteHeat);
  group.add(beacon);
  const light = new THREE.PointLight(0xb9361e, qualityLevel === "high" ? 46 : 28, definition.radius * 19, 1.75);
  light.position.z = definition.radius * 0.4;
  group.add(light);

  const node = finalizeNode(
    definition,
    group,
    [...throat.materials, ...mantle.materials, veil.material, rim.material, glints.material, infall.material, ...innerArcs.materials, ...outerArcs.materials, ...gasEnvelope.materials],
    [...mantle.meshes, veil.mesh, ...innerArcs.meshes, ...outerArcs.meshes, infall.points, ...gasEnvelope.clouds],
    [outerGasHalo, hotGasHalo, halo, ...gasEnvelope.clouds],
    beacon,
  );
  node.userData.boss = true;
  node.userData.portal = true;
  return node;
}

export function createKnowledgeDomain(THREE, definition, qualityLevel = "high") {
  const group = baseGroup(THREE, definition);
  const accent = new THREE.Color(definition.color || 0x6fbfd6);
  const depth = definition.radius * 0.72;
  const throat = createPortalThroat(THREE, definition.radius, depth, accent, {
    activity: 0.22,
    coreColor: 0x03080c,
    qualityLevel,
    mouthScale: 1.28,
    openness: 0.88,
    seed: hashAngle(definition.id),
    distortion: 0.028,
  });
  group.add(throat.group);
  const mantle = createVolumetricMantle(THREE, definition.radius, accent, {
    activity: 0.28,
    seed: hashAngle(definition.id),
    qualityLevel,
    scale: 1.92,
    hotColor: accent.clone().lerp(new THREE.Color(0xffffff), 0.72),
  });
  group.add(mantle.group);
  const veil = createFilamentVeil(THREE, definition.radius, accent, {
    opacity: 0.42,
    seed: hashAngle(definition.id),
    scale: 5.85,
    hotColor: accent.clone().lerp(new THREE.Color(0xffffff), 0.82),
  });
  group.add(veil.mesh);
  const rim = createDistortedRim(THREE, definition.radius, accent, {
    intensity: 0.34,
    irregularity: 0.14,
    qualityLevel,
    seed: hashAngle(definition.id),
  });
  group.add(rim.mesh);
  const arcs = createEnergyFilaments(THREE, definition.radius * 1.12, accent, {
    count: 0,
    thickness: 0.0045,
    intensity: 0.26,
    seed: hashAngle(definition.id),
    qualityLevel,
    wide: true,
  });
  addMeshes(group, arcs.meshes);
  const glints = createEnergyGlints(THREE, definition.radius, accent, {
    count: qualityLevel === "high" ? 4 : 2,
    seed: hashAngle(definition.id),
  });
  group.add(glints.points);
  const halo = createCoronaSprite(THREE, definition.radius * 4.8, accent, 0.055);
  halo.position.z = -depth * 0.8;
  group.add(halo);
  const beacon = createStatusBeacon(THREE, definition.radius, accent);
  group.add(beacon);
  const node = finalizeNode(
    definition,
    group,
    [...throat.materials, ...mantle.materials, veil.material, rim.material, ...arcs.materials, glints.material],
    [...mantle.meshes, veil.mesh, ...arcs.meshes],
    [halo],
    beacon,
  );
  node.userData.domain = true;
  node.userData.portal = true;
  return node;
}

export function createPortalThroat(THREE, radius, depth, accent, options = {}) {
  const group = new THREE.Group();
  const qualityLevel = options.qualityLevel || "high";
  const segments = qualityLevel === "high" ? 128 : 72;
  const depthSegments = qualityLevel === "high" ? 34 : 18;
  const boss = options.boss === true;
  const mouthScale = options.mouthScale ?? (boss ? 1.58 : options.auxiliary ? 1.2 : 1.34);
  const openness = options.openness ?? (boss ? 0.66 : 0.76);
  const coreColor = new THREE.Color(options.coreColor ?? 0x000205);
  const material = new THREE.ShaderMaterial({
    uniforms: {
      accent: { value: accent },
      coreColor: { value: coreColor },
      time: { value: 0 },
      activity: { value: options.activity ?? 0.7 },
      distortion: { value: options.distortion ?? 0.04 },
      seed: { value: options.seed ?? 0 },
    },
    vertexShader: FUNNEL_VERTEX_SHADER,
    fragmentShader: qualityLevel === "high" ? THROAT_FRAGMENT_SHADER : BALANCED_THROAT_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    side: THREE.BackSide,
    toneMapped: false,
  });
  const wallGeometry = new THREE.CylinderGeometry(radius * mouthScale, radius * openness, depth, segments, depthSegments, true);
  distortRadialGeometry(wallGeometry, "x", "z", options.distortion || 0, options.seed || 0);
  const wall = new THREE.Mesh(wallGeometry, material);
  wall.rotation.x = Math.PI * 0.5;
  wall.position.z = -depth * 0.5;
  wall.renderOrder = 1;
  group.add(wall);

  const chamber = createPortalDepthChamber(THREE, radius, depth, accent, {
    ...options,
    mouthScale,
    openness,
    activity: options.activity,
    coreColor,
    qualityLevel,
    seed: options.seed,
  });
  group.add(chamber.group);
  return {
    group,
    materials: [material, ...chamber.materials],
    meshes: [wall, ...chamber.meshes],
    wall,
    aperture: chamber.aperture,
  };
}

export function createPortalAperture(THREE, radius, accent, options = {}) {
  const qualityLevel = options.qualityLevel || "high";
  const material = new THREE.ShaderMaterial({
    uniforms: {
      accent: { value: accent },
      coreColor: { value: options.coreColor instanceof THREE.Color ? options.coreColor : new THREE.Color(options.coreColor ?? 0x000205) },
      time: { value: 0 },
      activity: { value: options.activity ?? 0.7 },
      seed: { value: options.seed ?? 0 },
      coreRadius: { value: options.coreRadius ?? 0.23 },
      bossMode: { value: options.boss ? 1 : 0 },
    },
    vertexShader: PORTAL_VERTEX_SHADER,
    fragmentShader: qualityLevel === "high" ? APERTURE_FRAGMENT_SHADER : BALANCED_APERTURE_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: true,
    side: THREE.DoubleSide,
    toneMapped: false,
  });
  const mesh = new THREE.Mesh(new THREE.CircleGeometry(radius, qualityLevel === "high" ? 128 : 72), material);
  mesh.renderOrder = 0;
  return { mesh, material };
}

export function createPortalDepthChamber(THREE, radius, depth, accent, options = {}) {
  const group = new THREE.Group();
  const qualityLevel = options.qualityLevel || "high";
  const boss = options.boss === true;
  const mouthScale = options.mouthScale ?? (boss ? 1.58 : 1.34);
  const openness = options.openness ?? (boss ? 0.66 : 0.76);
  const layerCount = options.layerCount ?? (boss
    ? (qualityLevel === "high" ? 7 : 4)
    : (qualityLevel === "high" ? 5 : 3));
  const coreRadius = options.coreRadius ?? (boss ? 0.27 : options.auxiliary ? 0.18 : 0.22);
  const materials = [];
  const meshes = [];
  const hotColor = options.hotColor instanceof THREE.Color
    ? options.hotColor
    : accent.clone().lerp(new THREE.Color(0xffffff), boss ? 0.32 : 0.68);

  const aperture = createPortalAperture(THREE, radius * mouthScale * 0.99, accent, {
    ...options,
    coreRadius,
    boss,
  });
  aperture.mesh.position.z = -depth * 0.78;
  aperture.mesh.renderOrder = 0.5;
  group.add(aperture.mesh);
  materials.push(aperture.material);
  meshes.push(aperture.mesh);

  for (let layerIndex = 0; layerIndex < layerCount; layerIndex += 1) {
    const layer = layerCount <= 1 ? 0 : layerIndex / (layerCount - 1);
    const outerScale = mouthScale * (1 - layer) + openness * 1.08 * layer;
    const outerRadius = radius * outerScale;
    const innerRadius = outerRadius * (0.56 + layer * 0.14);
    const rib = createTunnelRib(THREE, innerRadius, outerRadius, accent, {
      activity: options.activity,
      boss,
      hotColor,
      layer,
      qualityLevel,
      seed: (options.seed ?? 0) + layerIndex * 0.137,
      distortion: (options.distortion ?? 0.04) * (0.62 + layer * 0.72),
    });
    rib.mesh.position.z = -depth * (0.06 + layer * 0.64);
    rib.mesh.rotation.z = (options.seed ?? 0) * Math.PI * 2 + layerIndex * 0.83;
    rib.mesh.renderOrder = 1.25 + layerIndex * 0.015;
    group.add(rib.mesh);
    materials.push(rib.material);
    meshes.push(rib.mesh);
  }

  return { group, materials, meshes, aperture: aperture.mesh };
}

export function createTunnelRib(THREE, innerRadius, outerRadius, accent, options = {}) {
  const qualityLevel = options.qualityLevel || "high";
  const material = new THREE.ShaderMaterial({
    uniforms: {
      accent: { value: accent },
      hotColor: { value: options.hotColor instanceof THREE.Color ? options.hotColor : accent },
      time: { value: 0 },
      activity: { value: options.activity ?? 0.7 },
      seed: { value: options.seed ?? 0 },
      layer: { value: options.layer ?? 0 },
      bossMode: { value: options.boss ? 1 : 0 },
    },
    vertexShader: PORTAL_VERTEX_SHADER,
    fragmentShader: qualityLevel === "high"
      ? DEPTH_CHAMBER_FRAGMENT_SHADER
      : BALANCED_DEPTH_CHAMBER_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const geometry = new THREE.RingGeometry(
    innerRadius,
    outerRadius,
    qualityLevel === "high" ? 144 : 84,
    2,
  );
  distortRadialGeometry(geometry, "x", "y", options.distortion ?? 0.03, options.seed ?? 0);
  const mesh = new THREE.Mesh(geometry, material);
  return { mesh, material };
}

export function createDistortedRim(THREE, radius, accent, options = {}) {
  const qualityLevel = options.qualityLevel || "high";
  const material = new THREE.ShaderMaterial({
    uniforms: {
      accent: { value: accent },
      time: { value: 0 },
      intensity: { value: options.intensity ?? 0.8 },
      irregularity: { value: options.irregularity ?? 0.4 },
      seed: { value: options.seed ?? 0 },
    },
    vertexShader: PORTAL_VERTEX_SHADER,
    fragmentShader: qualityLevel === "high" ? RIM_FRAGMENT_SHADER : BALANCED_RIM_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const geometry = new THREE.RingGeometry(radius * 0.86, radius * 1.18, qualityLevel === "high" ? 192 : 112, 3);
  distortRadialGeometry(geometry, "x", "y", (options.irregularity ?? 0.4) * 0.08, options.seed || 0);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.z = radius * 0.035;
  mesh.renderOrder = 4;
  return { mesh, material };
}

export function createVolumetricMantle(THREE, radius, accent, options = {}) {
  const group = new THREE.Group();
  const qualityLevel = options.qualityLevel || "high";
  const boss = options.boss === true;
  const layerCount = boss
    ? (qualityLevel === "high" ? 4 : 2)
    : (qualityLevel === "high" ? 3 : 1);
  const materials = [];
  const meshes = [];
  const hotColor = options.hotColor instanceof THREE.Color
    ? options.hotColor
    : accent.clone().lerp(new THREE.Color(0xffffff), boss ? 0.34 : 0.5);
  const geometry = new THREE.CircleGeometry(
    radius * (options.scale ?? (boss ? 2.46 : 2.08)),
    qualityLevel === "high" ? 160 : 96,
  );
  for (let layerIndex = 0; layerIndex < layerCount; layerIndex += 1) {
    const layer = layerCount <= 1 ? 0 : layerIndex / (layerCount - 1);
    const material = new THREE.ShaderMaterial({
      uniforms: {
        accent: { value: accent },
        hotColor: { value: hotColor },
        time: { value: 0 },
        activity: { value: options.activity ?? 0.8 },
        seed: { value: (options.seed ?? 0) + layerIndex * 0.173 },
        layer: { value: layer },
        bossMode: { value: boss ? 1 : 0 },
      },
      vertexShader: PORTAL_VERTEX_SHADER,
      fragmentShader: qualityLevel === "high"
        ? VOLUMETRIC_MANTLE_FRAGMENT_SHADER
        : BALANCED_VOLUMETRIC_MANTLE_FRAGMENT_SHADER,
      transparent: true,
      depthWrite: false,
      depthTest: true,
      side: THREE.DoubleSide,
      blending: THREE.AdditiveBlending,
      toneMapped: false,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.rotation.z = (options.seed ?? 0) * Math.PI * 2 + layerIndex * 1.147;
    mesh.scale.setScalar(0.93 + layer * 0.19);
    mesh.position.z = radius * (-0.08 + layerIndex * 0.045);
    mesh.renderOrder = 2 + layerIndex * 0.01;
    group.add(mesh);
    meshes.push(mesh);
    materials.push(material);
  }
  return { group, meshes, materials };
}

export function createFilamentVeil(THREE, radius, accent, options = {}) {
  if (!portalEnergyVeilTexture) {
    portalEnergyVeilTexture = new THREE.TextureLoader().load("/trainer/space/assets/portal-energy-veil.png");
    portalEnergyVeilTexture.colorSpace = THREE.SRGBColorSpace;
    portalEnergyVeilTexture.minFilter = THREE.LinearMipmapLinearFilter;
    portalEnergyVeilTexture.magFilter = THREE.LinearFilter;
    portalEnergyVeilTexture.userData.sharedPortalTexture = true;
  }
  const hotColor = options.hotColor instanceof THREE.Color
    ? options.hotColor
    : accent.clone().lerp(new THREE.Color(0xffffff), 0.72);
  const material = new THREE.ShaderMaterial({
    uniforms: {
      veilMap: { value: portalEnergyVeilTexture },
      accent: { value: accent },
      hotColor: { value: hotColor },
      opacity: { value: options.opacity ?? 0.58 },
      time: { value: 0 },
      seed: { value: options.seed ?? 0 },
    },
    vertexShader: PORTAL_VERTEX_SHADER,
    fragmentShader: FILAMENT_VEIL_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    depthTest: true,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const width = radius * (options.scale ?? (options.boss ? 8.2 : 6.6));
  const geometry = new THREE.PlaneGeometry(width, width / 1.5, 1, 1);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.z = radius * 0.06;
  mesh.rotation.z = (options.seed ?? 0) * Math.PI * 0.7;
  mesh.renderOrder = 3.6;
  return { mesh, material };
}

export function createEnergyFilaments(THREE, radius, accent, options = {}) {
  const meshes = [];
  const materials = [];
  const count = options.count ?? 4;
  const seed = options.seed || 0;
  const qualityLevel = options.qualityLevel || "high";
  for (let index = 0; index < count; index += 1) {
    const randomA = pseudoRandom(seed * 1000 + index * 17 + 3);
    const randomB = pseudoRandom(seed * 1000 + index * 29 + 11);
    const randomC = pseudoRandom(seed * 1000 + index * 43 + 23);
    const phase = seed * Math.PI * 2 + index * 1.79 + randomA * 0.72;
    const span = options.boss
      ? 0.34 + randomB * 0.88
      : options.wide
        ? 1.18 + randomB * 1.36
        : 0.58 + randomB * 1.18;
    const arcRadius = radius * (0.88 + randomA * (options.boss ? 0.82 : 0.54));
    const points = [];
    const pointCount = qualityLevel === "high" ? 44 : 26;
    for (let pointIndex = 0; pointIndex <= pointCount; pointIndex += 1) {
      const t = pointIndex / pointCount;
      const angle = phase + t * span;
      const taper = Math.sin(t * Math.PI);
      const distortion = 1
        + Math.sin(angle * (2.2 + randomB) + index) * (options.fracture ? 0.16 : 0.075)
        + Math.sin(t * Math.PI * (4.0 + randomC * 4.0) + phase) * (0.025 + taper * 0.045);
      points.push(new THREE.Vector3(
        Math.cos(angle) * arcRadius * distortion,
        Math.sin(angle) * arcRadius * (0.84 + randomC * 0.24) * distortion,
        Math.sin(angle * (1.3 + randomA) + index) * radius * (0.055 + randomC * 0.095) + radius * (0.04 + taper * 0.1),
      ));
    }
    const curve = new THREE.CatmullRomCurve3(points);
    const haloMaterial = new THREE.MeshBasicMaterial({
      color: accent,
      transparent: true,
      opacity: (options.intensity ?? 0.48) * (0.1 + randomB * 0.09),
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      toneMapped: false,
    });
    const coreMaterial = new THREE.MeshBasicMaterial({
      color: index % 3 === 0 ? accent.clone().lerp(new THREE.Color(0xffffff), 0.82) : accent,
      transparent: true,
      opacity: (options.intensity ?? 0.48) * (0.28 + randomC * 0.24),
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      toneMapped: false,
    });
    const tubularSegments = qualityLevel === "high" ? 88 : 48;
    const radialSegments = qualityLevel === "high" ? 6 : 4;
    const thickness = radius * (options.thickness || 0.0065) * (0.7 + randomA * 0.65);
    const haloGeometry = new THREE.TubeGeometry(
      curve,
      tubularSegments,
      Math.max(thickness * 3.2, 0.018),
      radialSegments,
      false,
    );
    const coreGeometry = new THREE.TubeGeometry(
      curve,
      tubularSegments,
      Math.max(thickness, 0.006),
      radialSegments,
      false,
    );
    const haloMesh = new THREE.Mesh(haloGeometry, haloMaterial);
    const coreMesh = new THREE.Mesh(coreGeometry, coreMaterial);
    haloMesh.renderOrder = 5;
    coreMesh.renderOrder = 5.1;
    meshes.push(haloMesh, coreMesh);
    materials.push(haloMaterial, coreMaterial);
  }
  return { meshes, materials };
}

export function createLensingArcs(THREE, radius, accent, options = {}) {
  return createEnergyFilaments(THREE, radius, accent, options);
}

export function createEnergyGlints(THREE, radius, accent, options = {}) {
  const count = options.count || 5;
  const seed = options.seed || 0;
  const positions = new Float32Array(count * 3);
  const sizes = new Float32Array(count);
  const energies = new Float32Array(count);
  for (let index = 0; index < count; index += 1) {
    const randomA = pseudoRandom(seed * 1000 + index * 37 + 7);
    const randomB = pseudoRandom(seed * 1000 + index * 53 + 19);
    const angle = randomA * Math.PI * 2 + index * 1.41;
    const orbit = radius * (0.82 + randomB * (options.boss ? 0.92 : 0.56));
    positions[index * 3] = Math.cos(angle) * orbit;
    positions[index * 3 + 1] = Math.sin(angle) * orbit * (0.86 + randomA * 0.2);
    positions[index * 3 + 2] = radius * (0.1 + randomB * 0.16);
    sizes[index] = radius * (options.boss ? 0.25 + randomA * 0.22 : 0.38 + randomA * 0.28);
    energies[index] = options.boss ? 0.34 + randomB * 0.42 : 0.48 + randomB * 0.52;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("size", new THREE.BufferAttribute(sizes, 1));
  geometry.setAttribute("energy", new THREE.BufferAttribute(energies, 1));
  const material = new THREE.ShaderMaterial({
    uniforms: { accent: { value: accent } },
    vertexShader: GLINT_VERTEX_SHADER,
    fragmentShader: GLINT_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const points = new THREE.Points(geometry, material);
  points.renderOrder = 7;
  return { points, material };
}

export function createInfallField(THREE, radius, depth, accent, options = {}) {
  const count = options.count || 80;
  const positions = new Float32Array(count * 3);
  const seeds = new Float32Array(count * 4);
  const offset = options.seed || 0;
  for (let index = 0; index < count; index += 1) {
    const randomA = pseudoRandom(index + offset * 1000 + 11);
    const randomB = pseudoRandom(index + offset * 1000 + 43);
    const randomC = pseudoRandom(index + offset * 1000 + 97);
    seeds[index * 4] = randomA * Math.PI * 2;
    seeds[index * 4 + 1] = radius * (1.15 + randomB * 1.9);
    seeds[index * 4 + 2] = randomC;
    seeds[index * 4 + 3] = radius * (0.28 + randomA * 1.1);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("seed", new THREE.BufferAttribute(seeds, 4));
  const material = new THREE.ShaderMaterial({
    uniforms: {
      accent: { value: accent },
      time: { value: 0 },
      radius: { value: radius },
      depth: { value: depth },
      speed: { value: options.speed ?? 0.08 },
    },
    vertexShader: INFALL_VERTEX_SHADER,
    fragmentShader: INFALL_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const points = new THREE.Points(geometry, material);
  points.frustumCulled = false;
  points.renderOrder = 6;
  return { points, material };
}

export function createBossGasEnvelope(THREE, radius, colors, qualityLevel = "high") {
  const texture = createPlasmaCloudTexture(THREE);
  const clouds = [];
  const materials = [];
  const count = qualityLevel === "high" ? 12 : 7;
  for (let index = 0; index < count; index += 1) {
    const angle = (index / count) * Math.PI * 2 + pseudoRandom(index + 3) * 0.45;
    const color = colors[index % colors.length];
    const material = new THREE.SpriteMaterial({
      map: texture,
      color,
      transparent: true,
      opacity: 0.075 + (index % 3) * 0.025,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      toneMapped: false,
      rotation: angle * 0.37,
    });
    const cloud = new THREE.Sprite(material);
    const orbit = radius * (0.96 + pseudoRandom(index + 29) * 0.48);
    cloud.position.set(
      Math.cos(angle) * orbit,
      Math.sin(angle) * orbit * 0.82,
      radius * (-0.28 + pseudoRandom(index + 71) * 0.6),
    );
    const scale = radius * (1.48 + pseudoRandom(index + 101) * 0.92);
    cloud.scale.set(scale, scale * (0.62 + pseudoRandom(index + 47) * 0.46), 1);
    cloud.userData.baseOpacity = material.opacity;
    cloud.renderOrder = 2;
    clouds.push(cloud);
    materials.push(material);
  }
  return { clouds, materials };
}

export function createGasCloudHalo(THREE, scale, color, opacity, options = {}) {
  const highQuality = options.qualityLevel === "high";
  const textureSize = options.boss ? (highQuality ? 512 : 320) : (highQuality ? 320 : 224);
  const texture = createGasCloudHaloTexture(THREE, options.seed || 0, options.turbulence || 1, textureSize);
  const material = new THREE.SpriteMaterial({
    map: texture,
    color,
    transparent: true,
    opacity,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(scale, scale * (options.softness || 0.92), 1);
  sprite.userData.baseOpacity = opacity;
  sprite.renderOrder = 2;
  return sprite;
}

export function createCoronaSprite(THREE, scale, color, opacity) {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  const gradient = ctx.createRadialGradient(128, 128, 10, 128, 128, 128);
  const css = `rgb(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)})`;
  gradient.addColorStop(0, "rgba(0,0,0,0)");
  gradient.addColorStop(0.24, "rgba(0,0,0,0)");
  gradient.addColorStop(0.46, css.replace("rgb", "rgba").replace(")", ",0.08)"));
  gradient.addColorStop(0.72, css.replace("rgb", "rgba").replace(")", ",0.035)"));
  gradient.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 256, 256);
  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.SpriteMaterial({
    map: texture,
    color: 0xffffff,
    transparent: true,
    opacity,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(scale, scale, 1);
  sprite.userData.baseOpacity = opacity;
  return sprite;
}

export function applyCelestialStatus(THREE, node, status, isCurrent = false) {
  node.status = status;
  const beacon = node.userData.beacon;
  if (!beacon) return;
  const statusColors = {
    locked: 0x536068,
    available: 0xc9edf4,
    active: 0x78e7ff,
    mastered: 0x78d9ad,
    failed: 0xb77588,
  };
  beacon.material.color.setHex(statusColors[status] || statusColors.available);
  beacon.material.opacity = isCurrent ? 0.92 : status === "locked" ? 0.07 : status === "mastered" ? 0.4 : 0.24;
  beacon.scale.setScalar(isCurrent ? 1.22 : 1);
}

export function updateCelestialObject(node, elapsed, delta, isFocused = false) {
  const speed = node.userData.boss ? 0.026 : node.userData.auxiliary ? 0.055 : 0.042;
  node.userData.rotors.forEach((rotor, index) => {
    rotor.rotation.z += delta * speed * (index % 2 ? -1 : 1) * (1 + index * 0.035);
    if (rotor.material?.uniforms?.time) rotor.material.uniforms.time.value = elapsed;
  });
  node.userData.shaderMaterials.forEach((material) => {
    if (material.uniforms?.time) material.uniforms.time.value = elapsed;
  });
  const pulseStrength = node.userData.boss ? 0.018 : 0.028;
  const pulse = isFocused ? 1 + Math.sin(elapsed * 1.6) * pulseStrength : 1;
  node.group.scale.setScalar(pulse);
  node.userData.coronas.forEach((corona, index) => {
    if (!corona.material || corona.userData.baseOpacity == null) return;
    corona.material.opacity = corona.userData.baseOpacity * (0.9 + Math.sin(elapsed * (0.32 + index * 0.045)) * 0.1);
  });
}

function createStatusBeacon(THREE, radius, color) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute([
    radius * 1.14, radius * 0.72, radius * 0.12,
    radius * 1.28, radius * 0.54, radius * 0.08,
    radius * 1.37, radius * 0.34, radius * 0.04,
  ], 3));
  const material = new THREE.PointsMaterial({
    color,
    size: Math.max(0.45, radius * 0.075),
    transparent: true,
    opacity: 0.2,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  return new THREE.Points(geometry, material);
}

function createPlasmaCloudTexture(THREE) {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, 256, 256);
  ctx.globalCompositeOperation = "lighter";
  for (let index = 0; index < 36; index += 1) {
    const angle = pseudoRandom(index + 2) * Math.PI * 2;
    const distance = pseudoRandom(index + 19) * 62;
    const x = 128 + Math.cos(angle) * distance;
    const y = 128 + Math.sin(angle) * distance * 0.72;
    const size = 18 + pseudoRandom(index + 41) * 48;
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, size);
    gradient.addColorStop(0, `rgba(255,255,255,${0.035 + pseudoRandom(index + 67) * 0.055})`);
    gradient.addColorStop(0.42, "rgba(255,255,255,0.022)");
    gradient.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(x - size, y - size, size * 2, size * 2);
  }
  return new THREE.CanvasTexture(canvas);
}

function createGasCloudHaloTexture(THREE, seed, turbulence, textureSize) {
  const canvas = document.createElement("canvas");
  canvas.width = textureSize;
  canvas.height = textureSize;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, textureSize, textureSize);
  ctx.globalCompositeOperation = "lighter";
  const center = textureSize * 0.5;
  const cloudCount = 150;
  for (let index = 0; index < cloudCount; index += 1) {
    const angle = (index / cloudCount) * Math.PI * 2 + pseudoRandom(index + seed * 1000 + 5) * 0.42 * turbulence;
    const orbit = textureSize * 0.277 + (pseudoRandom(index + seed * 1000 + 37) - 0.5) * textureSize * 0.148 * turbulence;
    const x = center + Math.cos(angle) * orbit;
    const y = center + Math.sin(angle) * orbit * (0.84 + pseudoRandom(index + 71) * 0.14);
    const size = textureSize * (0.035 + pseudoRandom(index + seed * 1000 + 83) * 0.109 * turbulence);
    const strength = 0.028 + pseudoRandom(index + 113) * 0.065;
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, size);
    gradient.addColorStop(0, `rgba(255,255,255,${strength})`);
    gradient.addColorStop(0.38, `rgba(255,255,255,${strength * 0.48})`);
    gradient.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(x - size, y - size, size * 2, size * 2);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function baseGroup(THREE, definition) {
  const group = new THREE.Group();
  group.position.set(...definition.position);
  group.userData.id = definition.id;
  group.rotateZ((hashAngle(definition.id) - 0.5) * 0.36);
  return group;
}

function addMeshes(group, meshes) {
  if (meshes.length > 0) group.add(...meshes);
}

function distortRadialGeometry(geometry, axisA, axisB, amount, seed) {
  if (!amount) return;
  const positions = geometry.getAttribute("position");
  const getter = { x: "getX", y: "getY", z: "getZ" };
  const setter = { x: "setX", y: "setY", z: "setZ" };
  for (let index = 0; index < positions.count; index += 1) {
    const a = positions[getter[axisA]](index);
    const b = positions[getter[axisB]](index);
    const angle = Math.atan2(b, a);
    const distortion = 1
      + Math.sin(angle * 3 + seed * Math.PI * 2) * amount
      + Math.sin(angle * 7 - seed * Math.PI * 3) * amount * 0.38;
    positions[setter[axisA]](index, a * distortion);
    positions[setter[axisB]](index, b * distortion);
  }
  positions.needsUpdate = true;
  geometry.computeVertexNormals();
}

function finalizeNode(definition, group, shaderMaterials, rotors, coronas, beacon) {
  return {
    ...definition,
    group,
    materials: shaderMaterials,
    baseScale: 1,
    userData: {
      shaderMaterials: [...new Set(shaderMaterials.filter(Boolean))],
      rotors: [...new Set(rotors.filter(Boolean))],
      coronas: [...new Set(coronas.filter(Boolean))],
      beacon,
    },
  };
}

function hashAngle(value) {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) hash = (hash * 31 + value.charCodeAt(index)) | 0;
  return ((hash >>> 0) % 1000) / 1000;
}

function pseudoRandom(value) {
  const sine = Math.sin(value * 12.9898 + 78.233) * 43758.5453;
  return sine - Math.floor(sine);
}

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}
