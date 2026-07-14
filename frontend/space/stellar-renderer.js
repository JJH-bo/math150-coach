const MATERIAL_PILOT_NODE_ID = "ode_separable.concept";
const STELLAR_PILOT_NODE_IDS = new Set([
  MATERIAL_PILOT_NODE_ID,
  "ode_separable.trigger",
  "ode_separable.method",
  "ode_separable.transformation",
  "ode_separable.calculation",
  "ode_separable.expression",
]);
const STELLAR_PALETTES = Object.freeze({
  concept: [0xffe6ac, 0xff862e, 0x9a2218],
  trigger: [0xffdfa0, 0xff6b22, 0xa31c16],
  method: [0xffedbf, 0xff9a38, 0x8c2418],
  transformation: [0xffd9a3, 0xff7730, 0x852024],
  calculation: [0xffc98c, 0xff5d22, 0x77131c],
  expression: [0xffe8c4, 0xffa451, 0x91301d],
});

export function isStellarMaterialPilotNode(definition = {}) {
  return STELLAR_PILOT_NODE_IDS.has(definition.id) && definition.role === "training";
}

export function stellarProfileFor(definition = {}, qualityLevel = "high") {
  const seed = hashUnit(definition.id || MATERIAL_PILOT_NODE_ID);
  const difficulty = clamp(Number(definition.difficulty ?? 0.24), 0, 1);
  const highQuality = qualityLevel === "high";
  const palette = STELLAR_PALETTES[definition.type] || STELLAR_PALETTES.concept;
  const baseRadius = Number(definition.radius || 14);
  return {
    seed,
    radius: Number((baseRadius * (1.84 + difficulty * 0.38 + seed * 0.12)).toFixed(3)),
    activity: Number((0.55 + difficulty * 0.22 + seed * 0.08).toFixed(4)),
    noiseOctaves: highQuality ? 5 : 3,
    surfaceDetail: highQuality ? 5 : 4,
    granulationScale: Number((10.8 + seed * 2.4).toFixed(4)),
    flowSpeed: Number((0.035 + difficulty * 0.025).toFixed(4)),
    coronaLayers: highQuality ? 3 : 2,
    prominenceCount: highQuality ? 4 : 2,
    lightIntensity: highQuality ? 13 : 8,
    surfaceExposure: 0.86,
    limbDarkening: 0.58,
    coronaAsymmetry: 0.78,
    coreColor: palette[0],
    midColor: palette[1],
    edgeColor: palette[2],
  };
}

const PHOTOSPHERE_VERTEX_SHADER = `
  varying vec3 vObjectNormal;
  varying vec3 vViewNormal;
  varying vec3 vViewDirection;

  void main() {
    vObjectNormal = normalize(normal);
    vec4 viewPosition = modelViewMatrix * vec4(position, 1.0);
    vViewNormal = normalize(normalMatrix * normal);
    vViewDirection = normalize(-viewPosition.xyz);
    gl_Position = projectionMatrix * viewPosition;
  }
`;

const PHOTOSPHERE_FRAGMENT_SHADER = `
  uniform float time;
  uniform float seed;
  uniform float activity;
  uniform float noiseOctaves;
  uniform float granulationScale;
  uniform float flowSpeed;
  uniform float surfaceExposure;
  uniform float limbDarkening;
  uniform vec3 coreColor;
  uniform vec3 midColor;
  uniform vec3 edgeColor;
  varying vec3 vObjectNormal;
  varying vec3 vViewNormal;
  varying vec3 vViewDirection;

  float hash31(vec3 p) {
    p = fract(p * 0.1031);
    p += dot(p, p.yzx + 33.33 + seed * 7.0);
    return fract((p.x + p.y) * p.z);
  }

  float valueNoise(vec3 p) {
    vec3 cell = floor(p);
    vec3 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float n000 = hash31(cell + vec3(0.0, 0.0, 0.0));
    float n100 = hash31(cell + vec3(1.0, 0.0, 0.0));
    float n010 = hash31(cell + vec3(0.0, 1.0, 0.0));
    float n110 = hash31(cell + vec3(1.0, 1.0, 0.0));
    float n001 = hash31(cell + vec3(0.0, 0.0, 1.0));
    float n101 = hash31(cell + vec3(1.0, 0.0, 1.0));
    float n011 = hash31(cell + vec3(0.0, 1.0, 1.0));
    float n111 = hash31(cell + vec3(1.0, 1.0, 1.0));
    float nx00 = mix(n000, n100, f.x);
    float nx10 = mix(n010, n110, f.x);
    float nx01 = mix(n001, n101, f.x);
    float nx11 = mix(n011, n111, f.x);
    return mix(mix(nx00, nx10, f.y), mix(nx01, nx11, f.y), f.z);
  }

  float convection(vec3 p) {
    vec3 flow = vec3(
      sin(p.y * 2.7 + time * flowSpeed * 13.0),
      cos(p.z * 2.3 - time * flowSpeed * 9.0),
      sin(p.x * 2.1 + time * flowSpeed * 7.0)
    ) * (0.23 + activity * 0.08);
    float sum = 0.0;
    float amplitude = 0.58;
    float frequency = 1.0;
    for (int octave = 0; octave < 5; octave++) {
      float enabled = step(float(octave) + 0.5, noiseOctaves);
      sum += valueNoise((p + flow) * frequency) * amplitude * enabled;
      frequency *= 2.07;
      amplitude *= 0.48;
    }
    return sum;
  }

  void main() {
    vec3 p = normalize(vObjectNormal) * granulationScale;
    float field = convection(p);
    float cells = valueNoise(p * 2.9 + field * 1.7);
    float fineCells = valueNoise(p * 6.3 - field * 0.8 + time * flowSpeed * 0.7);
    float granulation = smoothstep(0.22, 0.82, cells + field * 0.31);
    float darkLane = 1.0 - smoothstep(0.025, 0.11, abs(cells - 0.47));
    float filament = pow(abs(sin((cells + fineCells * 0.34) * 18.0)), 8.0);
    float activeRegion = smoothstep(0.71, 0.88, valueNoise(p * 0.38 + seed * 13.0));
    float limb = clamp(dot(normalize(vViewNormal), normalize(vViewDirection)), 0.0, 1.0);
    float limbContour = mix(1.0 - limbDarkening, 1.0, pow(limb, 0.42));
    float heat = clamp(0.34 + granulation * 0.46 + fineCells * 0.16, 0.0, 1.0);
    vec3 hotCell = mix(midColor, coreColor, heat);
    vec3 color = mix(edgeColor * 0.48, hotCell, 0.38 + pow(limb, 0.46) * 0.62);
    color *= 0.78 + field * 0.2 - darkLane * 0.14;
    color *= 1.0 - activeRegion * (0.17 + darkLane * 0.14);
    color += coreColor * pow(fineCells, 6.0) * activity * 0.12;
    color += midColor * filament * activity * 0.06;
    color += edgeColor * pow(1.0 - limb, 3.4) * activity * 0.16;
    float slowPulse = 0.98 + sin(time * 0.43 + seed * 21.0) * 0.02;
    gl_FragColor = vec4(color * limbContour * surfaceExposure * slowPulse, 1.0);
  }
`;

const ATMOSPHERE_VERTEX_SHADER = `
  uniform float time;
  uniform float seed;
  uniform float layer;
  uniform float coronaAsymmetry;
  varying vec3 vObjectNormal;
  varying vec3 vViewNormal;
  varying vec3 vViewDirection;
  varying float vAsymmetry;

  void main() {
    vec3 direction = normalize(position);
    float angle = atan(direction.y, direction.x);
    float broadLobe = pow(0.5 + 0.5 * sin(angle * 3.0 + direction.z * 4.7 + seed * 17.0), 3.0);
    float brokenEdge = sin(angle * 11.0 - direction.z * 13.0 + time * 0.09 + seed * 29.0);
    float displacement = layer * coronaAsymmetry * (0.045 + broadLobe * 0.12 + brokenEdge * 0.018);
    vec3 displaced = position * (1.0 + displacement);
    vObjectNormal = direction;
    vec4 viewPosition = modelViewMatrix * vec4(displaced, 1.0);
    vViewNormal = normalize(normalMatrix * normal);
    vViewDirection = normalize(-viewPosition.xyz);
    vAsymmetry = broadLobe;
    gl_Position = projectionMatrix * viewPosition;
  }
`;

const ATMOSPHERE_FRAGMENT_SHADER = `
  uniform float time;
  uniform float seed;
  uniform float activity;
  uniform float layer;
  uniform float coronaAsymmetry;
  uniform vec3 edgeColor;
  varying vec3 vObjectNormal;
  varying vec3 vViewNormal;
  varying vec3 vViewDirection;
  varying float vAsymmetry;

  void main() {
    vec3 direction = normalize(vObjectNormal);
    float limb = 1.0 - clamp(dot(normalize(vViewNormal), normalize(vViewDirection)), 0.0, 1.0);
    float angle = atan(direction.y, direction.x);
    float broadFlow = sin(angle * (7.0 + layer * 3.0) + direction.z * 9.0 - time * (0.13 + activity * 0.04) + seed * 19.0);
    float fineFlow = sin(angle * (17.0 - layer * 2.0) - direction.z * 21.0 + time * 0.07 - seed * 11.0);
    float turbulence = 0.52 + broadFlow * 0.28 + fineFlow * 0.2;
    float plume = pow(max(0.0, broadFlow * 0.72 + vAsymmetry * coronaAsymmetry), 6.0) * (0.3 + activity * 0.18);
    float sectorMask = mix(0.08, 1.0, smoothstep(-0.08, 0.58, broadFlow * 0.58 + fineFlow * 0.22 + vAsymmetry * 0.52));
    float alpha = pow(limb, 2.35 + layer * 0.55) * max(0.0, turbulence + plume) * sectorMask;
    alpha *= (0.12 + activity * 0.13) * (1.0 - layer * 0.28);
    vec3 glow = mix(edgeColor, vec3(1.0, 0.74, 0.38), plume * 0.55 + limb * 0.16);
    gl_FragColor = vec4(glow * (1.0 + activity * 0.38), alpha);
  }
`;

const PROMINENCE_VERTEX_SHADER = `
  varying float vAlong;
  void main() {
    vAlong = uv.x;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const PROMINENCE_FRAGMENT_SHADER = `
  uniform float time;
  uniform float seed;
  uniform float activity;
  uniform vec3 edgeColor;
  varying float vAlong;
  void main() {
    float taper = sin(clamp(vAlong, 0.0, 1.0) * 3.14159265);
    float knots = 0.7 + 0.3 * sin(vAlong * 31.0 - time * (0.5 + activity * 0.2) + seed * 17.0);
    float alpha = taper * knots * (0.36 + activity * 0.22);
    vec3 color = mix(edgeColor, vec3(1.0, 0.78, 0.46), taper * 0.58);
    gl_FragColor = vec4(color * 1.4, alpha);
  }
`;

const DUST_VERTEX_SHADER = `
  uniform float time;
  attribute float particleSize;
  attribute float phase;
  varying float vEnergy;
  void main() {
    vec3 animated = position;
    float drift = time * (0.018 + phase * 0.014);
    float angle = drift + phase * 6.2831853;
    animated.x += cos(angle) * particleSize * 0.3;
    animated.y += sin(angle * 1.37) * particleSize * 0.22;
    vec4 viewPosition = modelViewMatrix * vec4(animated, 1.0);
    gl_Position = projectionMatrix * viewPosition;
    gl_PointSize = particleSize * (240.0 / max(8.0, -viewPosition.z));
    vEnergy = 0.55 + phase * 0.45;
  }
`;

const DUST_FRAGMENT_SHADER = `
  uniform vec3 midColor;
  varying float vEnergy;
  void main() {
    vec2 point = gl_PointCoord - vec2(0.5);
    float glow = 1.0 - smoothstep(0.03, 0.5, length(point));
    gl_FragColor = vec4(midColor * (0.72 + vEnergy * 0.48), glow * vEnergy * 0.42);
  }
`;

const HALO_VERTEX_SHADER = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const HALO_FRAGMENT_SHADER = `
  uniform float time;
  uniform float seed;
  uniform float activity;
  uniform vec3 coreColor;
  uniform vec3 midColor;
  varying vec2 vUv;

  void main() {
    vec2 point = vUv - vec2(0.5);
    float radius = length(point) * 2.0;
    float angle = atan(point.y, point.x);
    float edgeWarp = 0.78
      + sin(angle * 5.0 + seed * 21.0 + time * 0.035) * 0.11
      + sin(angle * 13.0 - seed * 37.0 - time * 0.021) * 0.07;
    float radialGlow = pow(max(0.0, 1.0 - radius / edgeWarp), 1.55);
    float rayField = pow(max(0.0, sin(angle * 9.0 + seed * 31.0 + time * 0.028)), 14.0);
    float rays = rayField * pow(max(0.0, 1.0 - radius), 0.7) * smoothstep(0.22, 0.64, radius);
    float cutoff = 1.0 - smoothstep(0.82, 1.0, radius);
    float alpha = (radialGlow * 0.2 + rays * 0.085) * cutoff * (0.82 + activity * 0.2);
    vec3 color = mix(midColor, coreColor, radialGlow * 0.72 + rays * 0.24);
    gl_FragColor = vec4(color * 1.08, alpha);
  }
`;

const SYSTEM_HAZE_VERTEX_SHADER = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const SYSTEM_HAZE_FRAGMENT_SHADER = `
  uniform vec3 warmColor;
  uniform vec3 coolColor;
  varying vec2 vUv;

  void main() {
    vec2 point = (vUv - vec2(0.5)) * vec2(2.0, 2.0);
    float bentBand = point.y + sin(point.x * 4.2) * 0.075 + sin(point.x * 9.0) * 0.025;
    float band = exp(-pow(bentBand * 4.4, 2.0));
    float radial = 1.0 - smoothstep(0.18, 1.0, length(point * vec2(0.82, 1.35)));
    float mottling = 0.68 + sin(point.x * 13.0 + point.y * 7.0) * 0.16
      + sin(point.x * 29.0 - point.y * 11.0) * 0.08;
    float alpha = max(0.0, band * radial * mottling) * 0.052;
    vec3 color = mix(coolColor, warmColor, smoothstep(-0.7, 0.65, point.x));
    gl_FragColor = vec4(color, alpha);
  }
`;

export function createStellarSystemEnvironment(THREE, definitions = [], qualityLevel = "high") {
  const learningNodes = definitions.filter((definition) => definition.kind === "micro");
  const group = new THREE.Group();
  group.userData.systemEnvironment = true;
  if (!learningNodes.length) return group;

  const center = learningNodes.reduce((total, definition) => [
    total[0] + definition.position[0],
    total[1] + definition.position[1],
    total[2] + definition.position[2],
  ], [0, 0, 0]).map((value) => value / learningNodes.length);
  group.position.set(...center);
  const seed = hashUnit(learningNodes.map((definition) => definition.id).join("|"));
  const dust = createSystemDustBelt(THREE, seed, qualityLevel);
  const haze = createSystemHaze(THREE);
  group.add(haze.mesh, dust.points);
  group.userData.materials = [haze.material, dust.material];
  return group;
}

function createSystemDustBelt(THREE, seed, qualityLevel) {
  const count = qualityLevel === "high" ? 760 : 420;
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  const random = mulberry32(Math.floor(seed * 0xffffffff));
  const warm = new THREE.Color(0xc88445);
  const cool = new THREE.Color(0x6e8fa4);
  const color = new THREE.Color();
  for (let index = 0; index < count; index += 1) {
    const angle = random() * Math.PI * 2;
    const radialNoise = (random() - 0.5) * 92;
    const verticalNoise = (random() - 0.5) * 48;
    positions[index * 3] = Math.cos(angle) * (355 + radialNoise);
    positions[index * 3 + 1] = Math.sin(angle) * (155 + radialNoise * 0.28) + verticalNoise;
    positions[index * 3 + 2] = Math.sin(angle * 2.0 + seed * 6.0) * 78 + (random() - 0.5) * 92;
    color.copy(cool).lerp(warm, 0.28 + random() * 0.5);
    colors[index * 3] = color.r;
    colors[index * 3 + 1] = color.g;
    colors[index * 3 + 2] = color.b;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const material = new THREE.PointsMaterial({
    size: qualityLevel === "high" ? 1.15 : 0.9,
    vertexColors: true,
    transparent: true,
    opacity: 0.22,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const points = new THREE.Points(geometry, material);
  points.renderOrder = 1;
  points.frustumCulled = false;
  return { points, material };
}

function createSystemHaze(THREE) {
  const material = new THREE.ShaderMaterial({
    uniforms: {
      warmColor: { value: new THREE.Color(0x8c3f26) },
      coolColor: { value: new THREE.Color(0x31566a) },
    },
    vertexShader: SYSTEM_HAZE_VERTEX_SHADER,
    fragmentShader: SYSTEM_HAZE_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(900, 520), material);
  const cameraWorldQuaternion = new THREE.Quaternion();
  const parentWorldQuaternion = new THREE.Quaternion();
  mesh.position.z = -110;
  mesh.onBeforeRender = (_renderer, _scene, camera) => {
    camera.getWorldQuaternion(cameraWorldQuaternion);
    mesh.parent?.getWorldQuaternion(parentWorldQuaternion);
    mesh.quaternion.copy(parentWorldQuaternion).invert().multiply(cameraWorldQuaternion);
  };
  mesh.renderOrder = 0;
  mesh.frustumCulled = false;
  return { mesh, material };
}

export function createKnowledgeStar(THREE, definition, qualityLevel = "high") {
  const profile = stellarProfileFor(definition, qualityLevel);
  const group = new THREE.Group();
  group.position.set(...(definition.position || [0, 0, 0]));
  group.userData.id = definition.id;
  group.rotateZ((profile.seed - 0.5) * 0.24);

  const photosphere = createPhotosphere(THREE, profile);
  const chromosphere = createChromosphere(THREE, profile);
  const corona = createCoronaLayers(THREE, profile);
  const prominences = createProminences(THREE, profile);
  const halo = createRadiativeHalo(THREE, profile);
  const dust = createLocalDustField(THREE, profile, qualityLevel);
  const beacon = createStellarBeacon(THREE, profile.radius, new THREE.Color(profile.midColor));
  const light = new THREE.PointLight(profile.midColor, profile.lightIntensity, profile.radius * 18, 1.65);
  light.position.z = profile.radius * 0.35;

  group.add(
    halo.mesh,
    photosphere.mesh,
    chromosphere.mesh,
    ...corona.meshes,
    ...prominences.meshes,
    dust.points,
    beacon,
    light,
  );

  const node = {
    id: definition.id,
    title: definition.title,
    description: definition.description,
    role: definition.role,
    kind: definition.kind,
    status: definition.status,
    radius: profile.radius,
    interactionRadius: Math.max(definition.interactionRadius || 0, profile.radius * 4.4),
    difficulty: definition.difficulty,
    trainable: definition.trainable,
    color: definition.color,
    group,
    userData: {
      beacon,
      shaderMaterials: [
        photosphere.material,
        chromosphere.material,
        ...corona.materials,
        ...prominences.materials,
        halo.material,
        dust.material,
      ],
      rotors: [],
      coronas: [],
      stellarProfile: profile,
      stellarLight: light,
    },
  };
  node.userData.stellar = true;
  return node;
}

function sharedUniforms(THREE, profile) {
  return {
    time: { value: 0 },
    seed: { value: profile.seed },
    activity: { value: profile.activity },
    noiseOctaves: { value: profile.noiseOctaves },
    layer: { value: 0 },
    granulationScale: { value: profile.granulationScale },
    flowSpeed: { value: profile.flowSpeed },
    coreColor: { value: new THREE.Color(profile.coreColor) },
    midColor: { value: new THREE.Color(profile.midColor) },
    edgeColor: { value: new THREE.Color(profile.edgeColor) },
    surfaceExposure: { value: profile.surfaceExposure },
    limbDarkening: { value: profile.limbDarkening },
    coronaAsymmetry: { value: profile.coronaAsymmetry },
  };
}

function createRadiativeHalo(THREE, profile) {
  const uniforms = sharedUniforms(THREE, profile);
  const material = new THREE.ShaderMaterial({
    uniforms,
    vertexShader: HALO_VERTEX_SHADER,
    fragmentShader: HALO_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const geometry = new THREE.PlaneGeometry(profile.radius * 5.4, profile.radius * 5.4);
  const mesh = new THREE.Mesh(geometry, material);
  const cameraWorldQuaternion = new THREE.Quaternion();
  const parentWorldQuaternion = new THREE.Quaternion();
  mesh.onBeforeRender = (_renderer, _scene, camera) => {
    camera.getWorldQuaternion(cameraWorldQuaternion);
    mesh.parent?.getWorldQuaternion(parentWorldQuaternion);
    mesh.quaternion
      .copy(parentWorldQuaternion)
      .invert()
      .multiply(cameraWorldQuaternion);
  };
  mesh.renderOrder = 2;
  mesh.frustumCulled = false;
  return { mesh, material };
}

function createPhotosphere(THREE, profile) {
  const material = new THREE.ShaderMaterial({
    uniforms: sharedUniforms(THREE, profile),
    vertexShader: PHOTOSPHERE_VERTEX_SHADER,
    fragmentShader: PHOTOSPHERE_FRAGMENT_SHADER,
    depthWrite: true,
    transparent: false,
    toneMapped: false,
  });
  const geometry = new THREE.IcosahedronGeometry(profile.radius, profile.surfaceDetail);
  const mesh = new THREE.Mesh(geometry, material);
  mesh.renderOrder = 4;
  return { mesh, material };
}

function createChromosphere(THREE, profile) {
  const material = new THREE.ShaderMaterial({
    uniforms: sharedUniforms(THREE, profile),
    vertexShader: ATMOSPHERE_VERTEX_SHADER,
    fragmentShader: ATMOSPHERE_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const geometry = new THREE.IcosahedronGeometry(
    profile.radius * 1.08,
    Math.max(3, profile.surfaceDetail - 1),
  );
  const mesh = new THREE.Mesh(geometry, material);
  mesh.renderOrder = 5;
  return { mesh, material };
}

function createCoronaLayers(THREE, profile) {
  const meshes = [];
  const materials = [];
  for (let index = 0; index < profile.coronaLayers; index += 1) {
    const uniforms = sharedUniforms(THREE, profile);
    uniforms.layer.value = index / Math.max(1, profile.coronaLayers - 1);
    const material = new THREE.ShaderMaterial({
      uniforms,
      vertexShader: ATMOSPHERE_VERTEX_SHADER,
      fragmentShader: ATMOSPHERE_FRAGMENT_SHADER,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      toneMapped: false,
    });
    const scale = 1.14 + index * 0.19 + index * index * 0.045;
    const geometry = new THREE.IcosahedronGeometry(
      profile.radius * scale,
      Math.max(3, profile.surfaceDetail - 2),
    );
    const mesh = new THREE.Mesh(geometry, material);
    mesh.rotation.set(index * 0.37, index * -0.29, index * 0.21);
    mesh.renderOrder = 5 + index;
    meshes.push(mesh);
    materials.push(material);
  }
  return { meshes, materials };
}

function createProminences(THREE, profile) {
  const meshes = [];
  const materials = [];
  for (let index = 0; index < profile.prominenceCount; index += 1) {
    const angle = profile.seed * Math.PI * 2 + index * 2.399963;
    const radial = new THREE.Vector3(
      Math.cos(angle),
      Math.sin(angle),
      (index % 2 - 0.5) * 0.34,
    ).normalize();
    const tangent = new THREE.Vector3(-radial.y, radial.x, 0).normalize();
    const base = radial.clone().multiplyScalar(profile.radius * 0.98);
    const points = [
      base.clone(),
      base.clone().addScaledVector(radial, profile.radius * 0.42).addScaledVector(tangent, profile.radius * 0.18),
      base.clone().addScaledVector(radial, profile.radius * 0.62).addScaledVector(tangent, profile.radius * 0.38),
      base.clone().addScaledVector(radial, profile.radius * 0.08).addScaledVector(tangent, profile.radius * 0.52),
    ];
    const curve = new THREE.CatmullRomCurve3(points, false, "centripetal", 0.42);
    const material = new THREE.ShaderMaterial({
      uniforms: sharedUniforms(THREE, profile),
      vertexShader: PROMINENCE_VERTEX_SHADER,
      fragmentShader: PROMINENCE_FRAGMENT_SHADER,
      transparent: true,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      toneMapped: false,
    });
    const geometry = new THREE.TubeGeometry(
      curve,
      qualitySegments(profile),
      profile.radius * 0.018,
      5,
      false,
    );
    const mesh = new THREE.Mesh(geometry, material);
    mesh.renderOrder = 8;
    meshes.push(mesh);
    materials.push(material);
  }
  return { meshes, materials };
}

function createLocalDustField(THREE, profile, qualityLevel) {
  const count = qualityLevel === "high" ? 180 : 96;
  const positions = new Float32Array(count * 3);
  const particleSizes = new Float32Array(count);
  const phases = new Float32Array(count);
  const random = mulberry32(Math.floor(profile.seed * 0xffffffff));
  for (let index = 0; index < count; index += 1) {
    const angle = random() * Math.PI * 2;
    const orbit = profile.radius * (1.65 + random() * 3.1);
    positions[index * 3] = Math.cos(angle) * orbit;
    positions[index * 3 + 1] = (random() - 0.5) * profile.radius * 2.1;
    positions[index * 3 + 2] = Math.sin(angle) * orbit * (0.62 + random() * 0.38);
    particleSizes[index] = profile.radius * (0.1 + random() * 0.16);
    phases[index] = random();
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("particleSize", new THREE.BufferAttribute(particleSizes, 1));
  geometry.setAttribute("phase", new THREE.BufferAttribute(phases, 1));
  const material = new THREE.ShaderMaterial({
    uniforms: {
      time: { value: 0 },
      midColor: { value: new THREE.Color(profile.midColor) },
    },
    vertexShader: DUST_VERTEX_SHADER,
    fragmentShader: DUST_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const points = new THREE.Points(geometry, material);
  points.renderOrder = 3;
  return { points, material };
}

function createStellarBeacon(THREE, radius, color) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute([
    radius * 1.18, radius * 0.84, radius * 0.08,
    radius * 1.3, radius * 0.66, radius * 0.06,
    radius * 1.39, radius * 0.46, radius * 0.04,
  ], 3));
  const material = new THREE.PointsMaterial({
    color,
    size: Math.max(0.55, radius * 0.07),
    transparent: true,
    opacity: 0.22,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  return new THREE.Points(geometry, material);
}

function qualitySegments(profile) {
  return profile.noiseOctaves >= 5 ? 34 : 22;
}

function mulberry32(seed) {
  let value = seed >>> 0;
  return function random() {
    value += 0x6d2b79f5;
    let result = value;
    result = Math.imul(result ^ (result >>> 15), result | 1);
    result ^= result + Math.imul(result ^ (result >>> 7), result | 61);
    return ((result ^ (result >>> 14)) >>> 0) / 4294967296;
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
