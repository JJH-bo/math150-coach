const PHOTON_RING_VERTEX_SHADER = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const PHOTON_RING_FRAGMENT_SHADER = `
  uniform float time;
  uniform vec3 ember;
  uniform vec3 whiteHeat;
  varying vec2 vUv;

  void main() {
    vec2 p = (vUv - vec2(0.5)) * 2.0;
    float radius = length(p);
    float angle = atan(p.y, p.x);
    float irregularity = sin(angle * 7.0 + time * 0.16) * 0.012
      + sin(angle * 17.0 - time * 0.09) * 0.006;
    float ringRadius = 0.742 + irregularity;
    float width = 0.014;
    float ring = 1.0 - smoothstep(width, width * 3.4, abs(radius - ringRadius));
    float outerEcho = (1.0 - smoothstep(0.012, 0.034, abs(radius - ringRadius * 1.085))) * 0.2;
    float beaming = 0.42 + 0.58 * smoothstep(-0.85, 0.72, p.x);
    float fracture = 0.72 + 0.28 * sin(angle * 11.0 - time * 0.38);
    float spark = pow(max(0.0, sin(angle * 29.0 + time * 0.22)), 18.0) * 0.38;
    vec3 color = mix(ember, whiteHeat, clamp(beaming + spark, 0.0, 1.0));
    float alpha = (ring + outerEcho) * beaming * fracture;
    if (alpha < 0.008) discard;
    gl_FragColor = vec4(color * (1.2 + spark), alpha);
  }
`;

const ACCRETION_VERTEX_SHADER = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const ACCRETION_FRAGMENT_SHADER = `
  uniform float time;
  uniform float frontPass;
  uniform float phase;
  uniform vec3 ember;
  uniform vec3 whiteHeat;
  uniform vec3 bloodCloud;
  varying vec2 vUv;

  float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
  }

  void main() {
    vec2 p = (vUv - vec2(0.5)) * 2.0;
    float radius = length(p);
    float angle = atan(p.y, p.x);
    float annulus = smoothstep(0.34, 0.43, radius) * (1.0 - smoothstep(0.9, 1.0, radius));
    float innerHeat = 1.0 - smoothstep(0.36, 0.74, radius);
    float spiral = 0.5 + 0.5 * sin(angle * 4.0 - log(radius + 0.08) * 18.0 - time * 0.34 + phase);
    float fineBands = 0.5 + 0.5 * sin(radius * 96.0 - angle * 5.0 + time * 0.16);
    float cells = hash21(floor(vec2(angle * 12.0, radius * 44.0)) + phase);
    float broken = smoothstep(0.12, 0.88, spiral * 0.58 + fineBands * 0.23 + cells * 0.34);
    float split = smoothstep(-0.045, 0.075, p.y);
    float sideMask = mix(1.0 - split, split, frontPass);
    float beaming = 0.3 + 0.7 * smoothstep(-0.96, 0.82, p.x);
    vec3 color = mix(bloodCloud, ember, 0.48 + innerHeat * 0.32);
    color = mix(color, whiteHeat, innerHeat * beaming * 0.78 + fineBands * 0.12);
    float alpha = annulus * sideMask * broken * (0.34 + beaming * 0.62);
    alpha *= 0.52 + innerHeat * 0.48;
    if (alpha < 0.012) discard;
    gl_FragColor = vec4(color * (0.82 + beaming * 0.68), alpha);
  }
`;

const INFALL_VERTEX_SHADER = `
  uniform float time;
  uniform float innerRadius;
  uniform float outerRadius;
  uniform float pointScale;
  attribute float orbitPhase;
  attribute float orbitSpeed;
  attribute float orbitHeight;
  attribute float orbitSize;
  varying float vEnergy;

  void main() {
    float progress = fract(orbitPhase + time * orbitSpeed);
    float collapse = pow(progress, 0.72);
    float radius = mix(outerRadius, innerRadius, collapse);
    float acceleration = 0.32 + 2.4 * collapse * collapse;
    float angle = orbitPhase * 6.2831853 + progress * 8.0 + time * acceleration;
    vec3 transformed = vec3(
      cos(angle) * radius,
      sin(angle) * radius * 0.34,
      orbitHeight * (1.0 - collapse) + sin(angle * 2.0) * innerRadius * 0.05
    );
    vec4 mvPosition = modelViewMatrix * vec4(transformed, 1.0);
    gl_Position = projectionMatrix * mvPosition;
    gl_PointSize = orbitSize * pointScale * (260.0 / max(80.0, -mvPosition.z));
    vEnergy = smoothstep(0.08, 0.88, progress) * (1.0 - smoothstep(0.9, 1.0, progress));
  }
`;

const INFALL_FRAGMENT_SHADER = `
  uniform vec3 ember;
  uniform vec3 whiteHeat;
  varying float vEnergy;
  void main() {
    vec2 p = gl_PointCoord - vec2(0.5);
    float glow = 1.0 - smoothstep(0.05, 0.5, length(p));
    vec3 color = mix(ember, whiteHeat, vEnergy);
    gl_FragColor = vec4(color, glow * (0.18 + vEnergy * 0.72));
  }
`;

const GRAVITY_STORM_VERTEX_SHADER = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const GRAVITY_STORM_FRAGMENT_SHADER = `
  uniform float time;
  uniform float phase;
  uniform float layer;
  uniform vec3 ember;
  uniform vec3 bloodCloud;
  varying vec2 vUv;

  void main() {
    vec2 p = (vUv - vec2(0.5)) * 2.0;
    p.x *= 0.9 + layer * 0.08;
    float radius = length(p);
    float angle = atan(p.y, p.x);
    float envelope = smoothstep(0.26, 0.48, radius) * (1.0 - smoothstep(0.78, 1.0, radius));
    float armA = pow(0.5 + 0.5 * sin(angle * (3.0 + layer) - radius * 13.0 + time * (0.055 + layer * 0.018) + phase), 5.0);
    float armB = pow(0.5 + 0.5 * sin(angle * 7.0 + radius * 18.0 - time * 0.034 - phase), 9.0);
    float turbulence = 0.58 + sin(p.x * 17.0 + p.y * 11.0 + phase) * 0.18
      + sin(p.x * 31.0 - p.y * 19.0 - phase) * 0.1;
    float alpha = envelope * turbulence * (armA * 0.12 + armB * 0.045 + 0.016);
    vec3 color = mix(bloodCloud, ember, armA * 0.48 + layer * 0.08);
    if (alpha < 0.004) discard;
    gl_FragColor = vec4(color, alpha);
  }
`;

export function blackHoleProfileFor(definition = {}, qualityLevel = "high") {
  const horizonRadius = Math.max(1, Number(definition.radius || 196));
  const highQuality = qualityLevel === "high";
  return {
    horizonRadius,
    photonRadius: horizonRadius * 1.09,
    discInnerRadius: horizonRadius * 1.08,
    discOuterRadius: horizonRadius * 2.02,
    stormOuterRadius: horizonRadius * 2.78,
    infallCount: highQuality ? 560 : 290,
    stormLayers: highQuality ? 3 : 2,
    segments: highQuality ? 96 : 64,
  };
}

export function createBossBlackHole(THREE, definition, qualityLevel = "high") {
  const profile = blackHoleProfileFor(definition, qualityLevel);
  const group = new THREE.Group();
  group.position.set(...definition.position);
  group.userData.id = definition.id;

  const colors = {
    ember: new THREE.Color(0xc83b16),
    whiteHeat: new THREE.Color(0xffbf72),
    bloodCloud: new THREE.Color(0x4d070b),
  };
  const storm = createGravitationalStorm(THREE, profile, colors, definition.id);
  const discs = createAccretionDisc(THREE, profile, colors);
  const horizon = createEventHorizon(THREE, profile, qualityLevel);
  const photonRing = createPhotonRing(THREE, profile, colors);
  const infall = createInfallField(THREE, profile, colors, definition.id);

  group.add(...storm.meshes, discs.backDisc, horizon.mesh, discs.frontDisc, photonRing.mesh, infall.points);
  const light = new THREE.PointLight(0xe04a1f, qualityLevel === "high" ? 54 : 34, profile.stormOuterRadius * 3.4, 1.7);
  light.position.set(profile.horizonRadius * 0.8, profile.horizonRadius * 0.24, profile.horizonRadius * 0.9);
  group.add(light);

  const shaderMaterials = [
    photonRing.material,
    discs.frontMaterial,
    discs.backMaterial,
    infall.material,
    ...storm.materials,
  ];
  const node = {
    ...definition,
    group,
    materials: [horizon.material, ...shaderMaterials],
    baseScale: 1,
    userData: {
      shaderMaterials,
      rotors: [discs.frontDisc, discs.backDisc, ...storm.meshes],
      coronas: [...storm.meshes],
      beacon: null,
      horizon: horizon.mesh,
      photonRing: photonRing.mesh,
      frontDisc: discs.frontDisc,
      backDisc: discs.backDisc,
      stormLayers: storm.meshes,
    },
  };
  node.userData.blackHole = true;
  node.userData.boss = true;
  return node;
}

export function createEventHorizon(THREE, profile, qualityLevel = "high") {
  const geometry = new THREE.SphereGeometry(
    profile.horizonRadius,
    qualityLevel === "high" ? 96 : 64,
    qualityLevel === "high" ? 72 : 48,
  );
  const material = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: false,
    depthWrite: true,
    depthTest: true,
    toneMapped: false,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.renderOrder = 5;
  mesh.frustumCulled = false;
  return { mesh, material };
}

export function createPhotonRing(THREE, profile, colors) {
  const diameter = profile.photonRadius * 2.72;
  const geometry = new THREE.PlaneGeometry(diameter, diameter, 1, 1);
  const material = new THREE.ShaderMaterial({
    uniforms: {
      time: { value: 0 },
      ember: { value: colors.ember },
      whiteHeat: { value: colors.whiteHeat },
    },
    vertexShader: PHOTON_RING_VERTEX_SHADER,
    fragmentShader: PHOTON_RING_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    depthTest: true,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.z = profile.horizonRadius * 0.12;
  mesh.renderOrder = 7;
  mesh.frustumCulled = false;
  return { mesh, material };
}

export function createAccretionDisc(THREE, profile, colors) {
  const diameter = profile.discOuterRadius * 2.08;
  const geometry = new THREE.PlaneGeometry(diameter, diameter, 1, 1);
  const baseUniforms = {
    time: { value: 0 },
    phase: { value: 1.73 },
    ember: { value: colors.ember },
    whiteHeat: { value: colors.whiteHeat },
    bloodCloud: { value: colors.bloodCloud },
  };
  const materialFor = (frontPass, phase) => new THREE.ShaderMaterial({
    uniforms: {
      ...baseUniforms,
      time: { value: 0 },
      phase: { value: phase },
      frontPass: { value: frontPass },
    },
    vertexShader: ACCRETION_VERTEX_SHADER,
    fragmentShader: ACCRETION_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    depthTest: true,
    side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const backMaterial = materialFor(0, 1.73);
  const frontMaterial = materialFor(1, 2.41);
  const backDisc = new THREE.Mesh(geometry, backMaterial);
  const frontDisc = new THREE.Mesh(geometry.clone(), frontMaterial);
  [backDisc, frontDisc].forEach((disc) => {
    disc.rotation.x = 1.08;
    disc.rotation.z = -0.24;
    disc.scale.y = 0.78;
    disc.frustumCulled = false;
  });
  backDisc.renderOrder = 3;
  frontDisc.renderOrder = 6;
  return { frontDisc, backDisc, frontMaterial, backMaterial };
}

export function createInfallField(THREE, profile, colors, seedValue) {
  const count = profile.infallCount;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);
  const orbitPhase = new Float32Array(count);
  const orbitSpeed = new Float32Array(count);
  const orbitHeight = new Float32Array(count);
  const orbitSize = new Float32Array(count);
  const random = mulberry32(hashNumber(seedValue));
  for (let index = 0; index < count; index += 1) {
    orbitPhase[index] = random();
    orbitSpeed[index] = 0.012 + random() * 0.026;
    orbitHeight[index] = (random() - 0.5) * profile.horizonRadius * 0.62;
    orbitSize[index] = profile.horizonRadius * (0.012 + random() * 0.026);
  }
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("orbitPhase", new THREE.BufferAttribute(orbitPhase, 1));
  geometry.setAttribute("orbitSpeed", new THREE.BufferAttribute(orbitSpeed, 1));
  geometry.setAttribute("orbitHeight", new THREE.BufferAttribute(orbitHeight, 1));
  geometry.setAttribute("orbitSize", new THREE.BufferAttribute(orbitSize, 1));
  const material = new THREE.ShaderMaterial({
    uniforms: {
      time: { value: 0 },
      innerRadius: { value: profile.horizonRadius * 1.04 },
      outerRadius: { value: profile.discOuterRadius * 1.22 },
      pointScale: { value: 1 },
      ember: { value: colors.ember },
      whiteHeat: { value: colors.whiteHeat },
    },
    vertexShader: INFALL_VERTEX_SHADER,
    fragmentShader: INFALL_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    depthTest: true,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const points = new THREE.Points(geometry, material);
  points.rotation.x = 0.96;
  points.rotation.z = -0.18;
  points.renderOrder = 8;
  points.frustumCulled = false;
  return { points, material };
}

export function createGravitationalStorm(THREE, profile, colors, seedValue) {
  const meshes = [];
  const materials = [];
  const random = mulberry32(hashNumber(seedValue) ^ 0x9e3779b9);
  for (let layer = 0; layer < profile.stormLayers; layer += 1) {
    const diameter = profile.stormOuterRadius * (1.88 + layer * 0.14);
    const geometry = new THREE.PlaneGeometry(diameter, diameter, 1, 1);
    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        phase: { value: random() * Math.PI * 2 },
        layer: { value: layer / Math.max(1, profile.stormLayers - 1) },
        ember: { value: colors.ember },
        bloodCloud: { value: colors.bloodCloud },
      },
      vertexShader: GRAVITY_STORM_VERTEX_SHADER,
      fragmentShader: GRAVITY_STORM_FRAGMENT_SHADER,
      transparent: true,
      depthWrite: false,
      depthTest: true,
      blending: THREE.AdditiveBlending,
      toneMapped: false,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.z = -profile.horizonRadius * (0.46 + layer * 0.18);
    mesh.rotation.z = random() * Math.PI;
    mesh.scale.y = 0.78 + layer * 0.08;
    mesh.renderOrder = layer;
    mesh.frustumCulled = false;
    mesh.userData.baseScale = mesh.scale.clone();
    meshes.push(mesh);
    materials.push(material);
  }
  return { meshes, materials };
}

export function updateBossBlackHole(node, elapsed, delta, isFocused = false) {
  if (!node?.userData?.blackHole) return;
  node.userData.shaderMaterials.forEach((material) => {
    if (material.uniforms?.time) material.uniforms.time.value = elapsed;
  });
  node.userData.frontDisc.rotation.z -= delta * 0.021;
  node.userData.backDisc.rotation.z += delta * 0.014;
  node.userData.photonRing.rotation.z += delta * 0.008;
  node.userData.stormLayers.forEach((storm, index) => {
    storm.rotation.z += delta * (0.003 + index * 0.0015) * (index % 2 ? -1 : 1);
    const focusPulse = isFocused ? 1 + Math.sin(elapsed * 0.38 + index) * 0.012 : 1;
    storm.scale.copy(storm.userData.baseScale).multiplyScalar(focusPulse);
  });
}

function hashNumber(value = "black-hole") {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function mulberry32(seed) {
  return function random() {
    let value = seed += 0x6d2b79f5;
    value = Math.imul(value ^ value >>> 15, value | 1);
    value ^= value + Math.imul(value ^ value >>> 7, value | 61);
    return ((value ^ value >>> 14) >>> 0) / 4294967296;
  };
}

