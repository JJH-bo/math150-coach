const VERTEX_SHADER = `
  varying vec3 vNormal;
  varying vec3 vView;
  varying vec2 vUv;
  void main() {
    vUv = uv;
    vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
    vNormal = normalize(normalMatrix * normal);
    vView = normalize(-viewPosition.xyz);
    gl_Position = projectionMatrix * viewPosition;
  }
`;

const HORIZON_FRAGMENT_SHADER = `
  uniform vec3 accent;
  uniform float time;
  uniform float intensity;
  uniform float instability;
  varying vec3 vNormal;
  varying vec3 vView;
  varying vec2 vUv;
  void main() {
    float facing = max(dot(normalize(vNormal), normalize(vView)), 0.0);
    float fresnel = pow(1.0 - facing, 8.8);
    float band = 0.5 + 0.5 * sin((vUv.y * 18.0 + vUv.x * 7.0) + time * (0.7 + instability));
    float turbulence = mix(0.72, 1.12, band * instability);
    vec3 core = vec3(0.0015, 0.0025, 0.0045);
    vec3 color = core + accent * fresnel * intensity * turbulence * 0.58;
    gl_FragColor = vec4(color, 1.0);
  }
`;

const DISK_VERTEX_SHADER = `
  varying vec2 vUv;
  varying vec3 vPosition;
  void main() {
    vUv = uv;
    vPosition = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const DISK_FRAGMENT_SHADER = `
  uniform vec3 innerColor;
  uniform vec3 outerColor;
  uniform float time;
  uniform float opacity;
  uniform float turbulence;
  varying vec2 vUv;
  varying vec3 vPosition;
  void main() {
    float radius = length(vUv - vec2(0.5)) * 2.0;
    float angle = atan(vPosition.y, vPosition.x);
    float stream = 0.5 + 0.5 * sin(angle * 8.0 - time * 1.8 + radius * 30.0);
    float filament = smoothstep(0.25, 0.92, stream) * turbulence;
    float edge = smoothstep(0.0, 0.2, radius) * (1.0 - smoothstep(0.76, 1.0, radius));
    vec3 color = mix(innerColor, outerColor, clamp(radius, 0.0, 1.0));
    color *= 0.68 + filament * 0.72;
    gl_FragColor = vec4(color, edge * opacity * (0.62 + filament));
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
  const horizon = createHorizon(THREE, definition.radius, accent, 1.25, 0.12, qualityLevel);
  group.add(horizon.mesh);

  const accretion = createAccretionDisk(THREE, definition.radius, accent, {
    opacity: 0.46,
    turbulence: 0.72,
    qualityLevel,
  });
  accretion.rotation.x = Math.PI * 0.48;
  accretion.rotation.z = hashAngle(definition.id) * 0.42 - 0.21;
  group.add(accretion);

  const outerDisk = createAccretionDisk(THREE, definition.radius * 1.18, accent.clone().offsetHSL(0.04, -0.18, -0.12), {
    opacity: 0.11,
    turbulence: 0.42,
    qualityLevel,
  });
  outerDisk.rotation.x = Math.PI * 0.52;
  outerDisk.rotation.z = accretion.rotation.z + 0.32;
  group.add(outerDisk);

  const corona = createCoronaSprite(THREE, definition.radius * 6.2, accent, 0.34);
  group.add(corona);
  const beacon = createStatusBeacon(THREE, definition.radius, accent);
  group.add(beacon);

  return finalizeNode(definition, group, [horizon.material], [accretion, outerDisk], [corona], beacon);
}

export function createAuxiliaryStar(THREE, definition, qualityLevel = "high") {
  const group = baseGroup(THREE, definition);
  const accent = new THREE.Color(definition.color || 0xd9f1f4);
  const segments = qualityLevel === "high" ? 48 : 32;
  const material = new THREE.MeshPhysicalMaterial({
    color: accent.clone().multiplyScalar(0.3),
    emissive: accent,
    emissiveIntensity: 0.34,
    roughness: 0.62,
    metalness: 0.02,
    clearcoat: 0.5,
    toneMapped: true,
  });
  const core = new THREE.Mesh(new THREE.IcosahedronGeometry(definition.radius, qualityLevel === "high" ? 5 : 3), material);
  group.add(core);

  const shellMaterial = new THREE.MeshBasicMaterial({
    color: accent,
    transparent: true,
    opacity: 0.07,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    wireframe: false,
    toneMapped: false,
  });
  const shell = new THREE.Mesh(new THREE.SphereGeometry(definition.radius * 1.34, segments, segments / 2), shellMaterial);
  group.add(shell);
  const corona = createCoronaSprite(THREE, definition.radius * 7.4, accent, 0.22);
  group.add(corona);
  const beacon = createStatusBeacon(THREE, definition.radius, accent);
  group.add(beacon);

  const node = finalizeNode(definition, group, [material, shellMaterial], [shell], [corona], beacon);
  node.userData.auxiliary = true;
  return node;
}

export function createRepairSingularity(THREE, definition, qualityLevel = "high") {
  const group = baseGroup(THREE, definition);
  const accent = new THREE.Color(definition.color || 0x9e6bab);
  const horizon = createHorizon(THREE, definition.radius, accent, 1.05, 0.82, qualityLevel);
  horizon.mesh.scale.set(1, 0.94, 1.06);
  group.add(horizon.mesh);

  const accretion = createAccretionDisk(THREE, definition.radius, accent, {
    opacity: 0.48,
    turbulence: 1,
    qualityLevel,
  });
  accretion.rotation.x = Math.PI * 0.5;
  accretion.rotation.z = 0.44;
  group.add(accretion);

  const fractureMaterial = new THREE.MeshBasicMaterial({
    color: 0xe1a3cb,
    transparent: true,
    opacity: 0.62,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    toneMapped: false,
  });
  const fractureSegments = [];
  [0.08, 0.36, 0.67].forEach((start, index) => {
    const arc = new THREE.Mesh(
      new THREE.TorusGeometry(definition.radius * (1.52 + index * 0.12), definition.radius * 0.035, 8, 56, Math.PI * (0.64 + index * 0.08)),
      fractureMaterial,
    );
    arc.rotation.set(Math.PI * 0.48, start * Math.PI, index * 0.7);
    group.add(arc);
    fractureSegments.push(arc);
  });
  const corona = createCoronaSprite(THREE, definition.radius * 6.8, accent, 0.28);
  group.add(corona);
  const beacon = createStatusBeacon(THREE, definition.radius, accent);
  group.add(beacon);

  return finalizeNode(definition, group, [horizon.material, fractureMaterial], [accretion, ...fractureSegments], [corona], beacon);
}

export function createBossCataclysm(THREE, definition, qualityLevel = "high") {
  const group = baseGroup(THREE, definition);
  const ember = new THREE.Color(0xb44922);
  const whiteHeat = new THREE.Color(0xd97836);
  const horizon = createHorizon(THREE, definition.radius, ember, 1.65, 0.52, qualityLevel);
  group.add(horizon.mesh);

  const accretion = createAccretionDisk(THREE, definition.radius * 1.08, whiteHeat, {
    opacity: 0.64,
    turbulence: 1,
    qualityLevel,
  });
  accretion.rotation.x = Math.PI * 0.49;
  accretion.rotation.z = -0.2;
  group.add(accretion);
  const catastropheDisk = createAccretionDisk(THREE, definition.radius * 1.55, ember, {
    opacity: 0.24,
    turbulence: 0.9,
    qualityLevel,
  });
  catastropheDisk.rotation.x = Math.PI * 0.56;
  catastropheDisk.rotation.z = 0.38;
  group.add(catastropheDisk);

  const prominences = [];
  const prominenceMaterial = new THREE.MeshBasicMaterial({
    color: 0x9f321c,
    transparent: true,
    opacity: 0.36,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
    toneMapped: false,
  });
  const count = qualityLevel === "high" ? 5 : 3;
  for (let index = 0; index < count; index += 1) {
    const arc = new THREE.Mesh(
      new THREE.TorusGeometry(definition.radius * (1.18 + index * 0.12), definition.radius * 0.022, 10, 72, Math.PI * (0.65 + index * 0.08)),
      prominenceMaterial,
    );
    arc.rotation.set(index * 0.63, index * 0.9, index * 0.47);
    group.add(arc);
    prominences.push(arc);
  }

  const corona = createCoronaSprite(THREE, definition.radius * 7.8, ember, 0.52);
  const outerCorona = createCoronaSprite(THREE, definition.radius * 11.5, new THREE.Color(0x5f140f), 0.2);
  group.add(corona, outerCorona);
  const beacon = createStatusBeacon(THREE, definition.radius, whiteHeat);
  group.add(beacon);

  const light = new THREE.PointLight(0xcf4b22, qualityLevel === "high" ? 38 : 22, definition.radius * 18, 1.8);
  group.add(light);
  const node = finalizeNode(
    definition,
    group,
    [horizon.material, prominenceMaterial],
    [accretion, catastropheDisk, ...prominences],
    [corona, outerCorona],
    beacon,
  );
  node.userData.boss = true;
  return node;
}

export function createKnowledgeDomain(THREE, definition, qualityLevel = "high") {
  const group = baseGroup(THREE, definition);
  const accent = new THREE.Color(definition.color || 0x6fbfd6);
  const ringMaterial = new THREE.MeshBasicMaterial({
    color: accent,
    transparent: true,
    opacity: 0.08,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const rings = [];
  [0.9, 1.25, 1.65].forEach((scale, index) => {
    const ring = new THREE.Mesh(
      new THREE.TorusGeometry(definition.radius * scale, definition.radius * 0.018, 6, qualityLevel === "high" ? 120 : 72),
      ringMaterial,
    );
    ring.rotation.set(index * 0.74, index * 0.46, index * 0.91);
    group.add(ring);
    rings.push(ring);
  });
  const corona = createCoronaSprite(THREE, definition.radius * 5, accent, 0.08);
  group.add(corona);
  const beacon = createStatusBeacon(THREE, definition.radius, accent);
  group.add(beacon);
  const node = finalizeNode(definition, group, [ringMaterial], rings, [corona], beacon);
  node.userData.domain = true;
  return node;
}

export function createAccretionDisk(THREE, radius, color, options = {}) {
  const qualityLevel = options.qualityLevel || "high";
  const segments = qualityLevel === "high" ? 192 : 96;
  const material = new THREE.ShaderMaterial({
    uniforms: {
      innerColor: { value: color.clone().multiplyScalar(1.25) },
      outerColor: { value: color.clone().multiplyScalar(0.42) },
      time: { value: 0 },
      opacity: { value: options.opacity ?? 0.6 },
      turbulence: { value: options.turbulence ?? 0.7 },
    },
    vertexShader: DISK_VERTEX_SHADER,
    fragmentShader: DISK_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const disk = new THREE.Mesh(new THREE.RingGeometry(radius * 1.12, radius * 2.38, segments, 3), material);
  disk.renderOrder = 3;
  disk.userData.accretion = true;
  return disk;
}

export function createCoronaSprite(THREE, scale, color, opacity) {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  const gradient = ctx.createRadialGradient(128, 128, 8, 128, 128, 128);
  const css = `rgb(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)})`;
  gradient.addColorStop(0, "rgba(255,255,255,0.38)");
  gradient.addColorStop(0.18, css.replace("rgb", "rgba").replace(")", ",0.22)"));
  gradient.addColorStop(0.52, css.replace("rgb", "rgba").replace(")", ",0.07)"));
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
    locked: 0x5d6870,
    available: 0xc9edf4,
    active: 0x78e7ff,
    mastered: 0x78d9ad,
    failed: 0xb77588,
  };
  beacon.material.color.setHex(statusColors[status] || statusColors.available);
  beacon.material.opacity = isCurrent ? 0.86 : status === "locked" ? 0.08 : status === "mastered" ? 0.32 : 0.2;
  beacon.scale.setScalar(isCurrent ? 1.18 : 1);
}

export function updateCelestialObject(node, elapsed, delta, isFocused = false) {
  const speed = node.userData.boss ? 0.045 : node.userData.auxiliary ? 0.14 : 0.075;
  node.userData.rotors.forEach((rotor, index) => {
    rotor.rotation.z += delta * speed * (index % 2 ? -1 : 1) * (1 + index * 0.16);
    if (rotor.material?.uniforms?.time) rotor.material.uniforms.time.value = elapsed;
  });
  node.userData.shaderMaterials.forEach((material) => {
    if (material.uniforms?.time) material.uniforms.time.value = elapsed;
  });
  const pulse = isFocused ? 1 + Math.sin(elapsed * 2.1) * 0.035 : 1;
  node.group.scale.setScalar(pulse);
  node.userData.coronas.forEach((corona, index) => {
    corona.material.opacity = corona.userData.baseOpacity * (0.88 + Math.sin(elapsed * (0.5 + index * 0.16)) * 0.12);
  });
}

function createHorizon(THREE, radius, accent, intensity, instability, qualityLevel) {
  const material = new THREE.ShaderMaterial({
    uniforms: {
      accent: { value: accent },
      time: { value: 0 },
      intensity: { value: intensity },
      instability: { value: instability },
    },
    vertexShader: VERTEX_SHADER,
    fragmentShader: HORIZON_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: true,
    toneMapped: false,
  });
  const segments = qualityLevel === "high" ? 72 : 48;
  return {
    mesh: new THREE.Mesh(new THREE.SphereGeometry(radius, segments, segments / 2), material),
    material,
  };
}

function createStatusBeacon(THREE, radius, color) {
  const material = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.18,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const beacon = new THREE.Mesh(new THREE.TorusGeometry(radius * 1.48, Math.max(0.12, radius * 0.018), 8, 96), material);
  beacon.rotation.x = Math.PI * 0.5;
  return beacon;
}

function baseGroup(THREE, definition) {
  const group = new THREE.Group();
  group.position.set(...definition.position);
  group.userData.id = definition.id;
  return group;
}

function finalizeNode(definition, group, shaderMaterials, rotors, coronas, beacon) {
  const node = {
    ...definition,
    group,
    materials: shaderMaterials,
    baseScale: 1,
    userData: {
      shaderMaterials,
      rotors,
      coronas,
      beacon,
    },
  };
  return node;
}

function hashAngle(value) {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) hash = (hash * 31 + value.charCodeAt(index)) | 0;
  return ((hash >>> 0) % 1000) / 1000;
}
