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
    float granulation = smoothstep(0.28, 0.78, cells + field * 0.34);
    float darkLane = 1.0 - smoothstep(0.045, 0.18, abs(cells - 0.47));
    float filament = pow(abs(sin((cells + fineCells * 0.34) * 18.0)), 8.0);
    float limb = clamp(dot(normalize(vViewNormal), normalize(vViewDirection)), 0.0, 1.0);
    vec3 color = mix(edgeColor, midColor, pow(limb, 0.55));
    color = mix(color, coreColor, granulation * 0.72 + fineCells * 0.12);
    color *= 0.72 + field * 0.42 - darkLane * 0.16;
    color += coreColor * filament * activity * 0.12;
    color += edgeColor * pow(1.0 - limb, 3.4) * activity * 0.26;
    float slowPulse = 0.98 + sin(time * 0.43 + seed * 21.0) * 0.02;
    gl_FragColor = vec4(color * slowPulse * 1.18, 1.0);
  }
`;

const ATMOSPHERE_VERTEX_SHADER = PHOTOSPHERE_VERTEX_SHADER;

const ATMOSPHERE_FRAGMENT_SHADER = `
  uniform float time;
  uniform float seed;
  uniform float activity;
  uniform float layer;
  uniform vec3 edgeColor;
  varying vec3 vObjectNormal;
  varying vec3 vViewNormal;
  varying vec3 vViewDirection;

  void main() {
    vec3 direction = normalize(vObjectNormal);
    float limb = 1.0 - clamp(dot(normalize(vViewNormal), normalize(vViewDirection)), 0.0, 1.0);
    float angle = atan(direction.y, direction.x);
    float broadFlow = sin(angle * (7.0 + layer * 3.0) + direction.z * 9.0 - time * (0.13 + activity * 0.04) + seed * 19.0);
    float fineFlow = sin(angle * (17.0 - layer * 2.0) - direction.z * 21.0 + time * 0.07 - seed * 11.0);
    float turbulence = 0.6 + broadFlow * 0.24 + fineFlow * 0.16;
    float plume = pow(max(0.0, broadFlow), 7.0) * (0.28 + activity * 0.16);
    float alpha = pow(limb, 2.15 + layer * 0.48) * max(0.0, turbulence + plume);
    alpha *= (0.2 + activity * 0.16) * (1.0 - layer * 0.23);
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
  const dust = createLocalDustField(THREE, profile, qualityLevel);
  const beacon = createStellarBeacon(THREE, profile.radius, new THREE.Color(profile.midColor));
  const light = new THREE.PointLight(profile.midColor, profile.lightIntensity, profile.radius * 18, 1.65);
  light.position.z = profile.radius * 0.35;

  group.add(
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
  };
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
    const scale = 1.18 + index * 0.17;
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
