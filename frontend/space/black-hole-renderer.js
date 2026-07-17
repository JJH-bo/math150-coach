const PHOTON_RING_VERTEX_SHADER = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const PHOTON_RING_FRAGMENT_SHADER = `
  uniform float time;
  uniform float ringWidth;
  uniform vec3 ember;
  uniform vec3 whiteHeat;
  varying vec2 vUv;

  void main() {
    vec2 p = (vUv - vec2(0.5)) * 2.0;
    float radius = length(p);
    float angle = atan(p.y, p.x);
    float irregularity = sin(angle * 7.0 + time * 0.16) * 0.0045
      + sin(angle * 17.0 - time * 0.09) * 0.002;
    float ringRadius = 0.742 + irregularity;
    float width = ringWidth;
    float ring = 1.0 - smoothstep(width, width * 3.4, abs(radius - ringRadius));
    float outerEcho = (1.0 - smoothstep(0.007, 0.018, abs(radius - ringRadius * 1.055))) * 0.08;
    float beaming = 0.28 + 0.72 * smoothstep(-0.9, 0.78, p.x);
    float fractureWave = 0.5 + 0.5 * sin(angle * 13.0 - time * 0.26)
      + sin(angle * 31.0 + time * 0.12) * 0.18;
    float arcDropout = sin(angle * 3.0 + time * 0.045)
      + sin(angle * 8.0 - time * 0.07) * 0.62;
    float fracture = smoothstep(0.38, 0.82, fractureWave)
      * smoothstep(-0.28, 0.34, arcDropout);
    float spark = pow(max(0.0, sin(angle * 37.0 + time * 0.18)), 24.0) * 0.22;
    vec3 color = mix(ember, whiteHeat, clamp(beaming * 0.72 + spark, 0.0, 1.0));
    float alpha = (ring + outerEcho) * beaming * fracture * 0.62;
    if (alpha < 0.008) discard;
    gl_FragColor = vec4(color * (0.74 + spark * 0.46), alpha);
  }
`;

const ABYSS_VERTEX_SHADER = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const ABYSS_FRAGMENT_SHADER = `
  uniform float time;
  uniform float phase;
  uniform float depthLayer;
  uniform vec3 ember;
  uniform vec3 bloodCloud;
  uniform vec3 whiteHeat;
  varying vec2 vUv;

  float abyssHash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 34.45);
    return fract(p.x * p.y);
  }

  float abyssNoise(vec2 p) {
    vec2 cell = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(abyssHash(cell), abyssHash(cell + vec2(1.0, 0.0)), f.x),
      mix(abyssHash(cell + vec2(0.0, 1.0)), abyssHash(cell + vec2(1.0)), f.x),
      f.y
    );
  }

  float abyssFbm(vec2 p) {
    float value = 0.0;
    float amplitude = 0.55;
    for (int octave = 0; octave < 4; octave++) {
      value += abyssNoise(p) * amplitude;
      p = p * 2.04 + vec2(11.7, -7.3);
      amplitude *= 0.49;
    }
    return value;
  }

  void main() {
    vec2 point = (vUv - vec2(0.5)) * 2.0;
    vec2 ellipsePoint = vec2(point.x, point.y / 0.74);
    float boundaryNoise = (abyssFbm(ellipsePoint * 4.6 + vec2(time * 0.018, phase)) - 0.5) * 0.12;
    float boundary = length(ellipsePoint);
    float aperture = 1.0 - smoothstep(0.79 + boundaryNoise, 0.88 + boundaryNoise * 0.4, boundary);
    if (aperture < 0.008) discard;

    vec2 layerOffset = vec2(depthLayer * 0.055, sin(phase + time * 0.035) * 0.012 * depthLayer);
    vec2 depthPoint = (ellipsePoint - layerOffset) / (1.0 - depthLayer * 0.075);
    float depthRadius = length(depthPoint);
    float gas = abyssFbm(depthPoint * (5.4 + depthLayer * 2.2) + vec2(phase, -time * 0.022));
    float curtain = smoothstep(0.18, 0.78, gas) * smoothstep(0.12, 0.72, depthRadius);
    vec2 offsetCore = depthPoint - vec2(0.2 + depthLayer * 0.052, -0.045 + depthLayer * 0.018);
    float coreRadius = length(offsetCore * vec2(1.0, 1.18));
    float coreNoise = (abyssFbm(offsetCore * 8.8 - vec2(time * 0.011, phase)) - 0.5) * 0.065;
    float core = 1.0 - smoothstep(0.235 + coreNoise, 0.34 + coreNoise * 0.4, coreRadius);
    float foldWave = 0.5 + 0.5 * sin(
      coreRadius * (34.0 + depthLayer * 7.0)
      + gas * 6.2
      + phase * 1.7
      - time * (0.025 + depthLayer * 0.012)
    );
    float tornFold = smoothstep(0.58, 0.9, foldWave)
      * smoothstep(0.24, 0.39, coreRadius)
      * (1.0 - smoothstep(0.63, 0.79, coreRadius));
    float radialTear = smoothstep(
      0.36,
      0.76,
      abyssFbm(offsetCore * 13.0 + vec2(phase * 3.0, time * 0.009))
    );
    float contour = tornFold * (0.28 + radialTear * 0.72);
    if (depthLayer > 0.75 && core < 0.012 && contour < 0.05) discard;
    float fracturedRim = (1.0 - smoothstep(0.035, 0.11, abs(boundary - 0.79 - boundaryNoise)))
      * smoothstep(0.36, 0.83, gas);

    vec3 color = bloodCloud * (0.28 + curtain * 0.34) * (1.0 - core);
    color += ember * contour * (0.08 + (1.0 - depthLayer) * 0.1);
    color += mix(ember, whiteHeat, gas) * fracturedRim * 0.22;
    color *= 0.68 - depthLayer * 0.14;
    float alpha = aperture * (0.24 + depthLayer * 0.1 + core * 0.68 + contour * 0.2);
    gl_FragColor = vec4(color, min(0.98, alpha));
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
  uniform float noiseOctaves;
  uniform vec3 ember;
  uniform vec3 whiteHeat;
  uniform vec3 bloodCloud;
  varying vec2 vUv;

  float hash21(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
  }

  float valueNoise2D(vec2 p) {
    vec2 cell = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash21(cell);
    float b = hash21(cell + vec2(1.0, 0.0));
    float c = hash21(cell + vec2(0.0, 1.0));
    float d = hash21(cell + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
  }

  float fbm(vec2 p) {
    float sum = 0.0;
    float amplitude = 0.56;
    for (int octave = 0; octave < 4; octave++) {
      float enabled = step(float(octave) + 0.5, noiseOctaves);
      sum += valueNoise2D(p) * amplitude * enabled;
      p = p * 2.03 + vec2(13.7, -9.2);
      amplitude *= 0.49;
    }
    return sum;
  }

  void main() {
    vec2 p = (vUv - vec2(0.5)) * 2.0;
    float radius = length(p);
    float angle = atan(p.y, p.x);
    float annulus = smoothstep(0.34, 0.43, radius) * (1.0 - smoothstep(0.9, 1.0, radius));
    float innerHeat = 1.0 - smoothstep(0.36, 0.74, radius);
    vec2 swirlDirection = vec2(cos(angle), sin(angle));
    float flowNoise = fbm(p * 8.5 + swirlDirection * (time * 0.07 + phase));
    float fineNoise = fbm(p * 24.0 - swirlDirection * (time * 0.035 - phase * 0.4));
    float spiral = 0.5 + 0.5 * sin(angle * 4.0 - log(radius + 0.08) * 17.0 - time * 0.24 + flowNoise * 2.4 + phase);
    float fineBands = 0.5 + 0.5 * sin(radius * 118.0 - angle * 6.0 + time * 0.11 + fineNoise * 3.2);
    float broken = smoothstep(0.24, 0.83, spiral * 0.42 + flowNoise * 0.4 + fineBands * 0.18 + fineNoise * 0.12);
    float split = smoothstep(-0.045, 0.075, p.y);
    float frontHalf = 1.0 - split;
    float sideMask = mix(split, frontHalf, frontPass);
    float beaming = 0.3 + 0.7 * smoothstep(-0.96, 0.82, p.x);
    vec3 color = mix(bloodCloud, ember, 0.48 + innerHeat * 0.32);
    color = mix(color, whiteHeat, innerHeat * beaming * 0.62 + fineBands * 0.07);
    float alpha = annulus * sideMask * broken * (0.24 + beaming * 0.48);
    alpha *= 0.44 + innerHeat * 0.42;
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

const STORM_CLOUD_VERTEX_SHADER = `
  uniform float time;
  uniform float pointScale;
  attribute float orbitPhase;
  attribute float orbitRadius;
  attribute float orbitHeight;
  attribute float orbitSpeed;
  attribute float cloudSize;
  varying float vHeat;

  void main() {
    float angle = orbitPhase + time * orbitSpeed;
    float shear = sin(angle * 3.0 + orbitPhase * 2.0) * orbitRadius * 0.08;
    vec3 transformed = vec3(
      cos(angle) * orbitRadius,
      sin(angle) * orbitRadius * 0.74 + shear,
      orbitHeight + sin(angle * 2.0) * orbitRadius * 0.09
    );
    vec4 mvPosition = modelViewMatrix * vec4(transformed, 1.0);
    gl_Position = projectionMatrix * mvPosition;
    gl_PointSize = cloudSize * pointScale * (300.0 / max(90.0, -mvPosition.z));
    vHeat = 0.45 + 0.55 * sin(angle * 1.7 + orbitPhase);
  }
`;

const STORM_CLOUD_FRAGMENT_SHADER = `
  uniform vec3 ember;
  uniform vec3 bloodCloud;
  varying float vHeat;
  void main() {
    vec2 point = gl_PointCoord - vec2(0.5);
    float radius = length(point);
    float cloud = 1.0 - smoothstep(0.08, 0.5, radius);
    float torn = 0.72 + sin(point.x * 21.0 + point.y * 13.0) * 0.18;
    vec3 color = mix(bloodCloud, ember, vHeat * 0.52);
    gl_FragColor = vec4(color, cloud * torn * 0.16);
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

  float stormHash(vec2 p) {
    p = fract(p * vec2(127.13, 311.71));
    p += dot(p, p + 43.17);
    return fract(p.x * p.y);
  }

  float stormNoise(vec2 p) {
    vec2 cell = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
      mix(stormHash(cell), stormHash(cell + vec2(1.0, 0.0)), f.x),
      mix(stormHash(cell + vec2(0.0, 1.0)), stormHash(cell + vec2(1.0)), f.x),
      f.y
    );
  }

  float fbm(vec2 p) {
    float value = 0.0;
    float amplitude = 0.56;
    for (int octave = 0; octave < 4; octave++) {
      value += stormNoise(p) * amplitude;
      p = p * 2.03 + vec2(17.1, -12.4);
      amplitude *= 0.48;
    }
    return value;
  }

  void main() {
    vec2 p = (vUv - vec2(0.5)) * 2.0;
    p.x *= 0.9 + layer * 0.08;
    float radius = length(p);
    float angle = atan(p.y, p.x);
    float flow = fbm(p * (4.8 + layer * 1.7) + vec2(time * 0.015, phase));
    float fine = fbm(p * 12.0 - vec2(time * 0.009, phase * 0.7));
    float envelope = smoothstep(0.22, 0.42, radius) * (1.0 - smoothstep(0.74, 1.02, radius));
    float spiral = 0.5 + 0.5 * sin(
      angle * (2.6 + layer * 1.4)
      - radius * (12.0 + layer * 3.0)
      + time * (0.035 + layer * 0.012)
      + phase
      + flow * 3.2
    );
    float tornMask = smoothstep(0.42, 0.84, spiral * 0.5 + flow * 0.38 + fine * 0.2);
    float gasSheet = smoothstep(0.28, 0.78, flow) * (0.38 + fine * 0.62);
    float fracture = smoothstep(0.56, 0.88, fine + sin(angle * 17.0 + phase) * 0.16);
    float alpha = envelope * (tornMask * 0.09 + gasSheet * 0.045 + fracture * 0.018);
    alpha *= 0.72 + layer * 0.08;
    vec3 color = mix(bloodCloud, ember, tornMask * 0.52 + flow * 0.18 + layer * 0.06);
    if (alpha < 0.004) discard;
    gl_FragColor = vec4(color, alpha);
  }
`;

export function blackHoleProfileFor(definition = {}, qualityLevel = "high") {
  const abyssRadius = Math.max(1, Number(definition.radius || 224));
  const highQuality = qualityLevel === "high";
  return {
    abyssRadius,
    photonRadius: abyssRadius * 1.02,
    photonWidth: 0.006,
    discInnerRadius: abyssRadius * 1.02,
    discOuterRadius: abyssRadius * 1.9,
    stormOuterRadius: abyssRadius * 3.05,
    depthLayers: 3,
    infallCount: highQuality ? 560 : 290,
    stormLayers: highQuality ? 5 : 3,
    filamentCount: highQuality ? 18 : 10,
    stormCloudCount: highQuality ? 720 : 360,
    discTurbulenceOctaves: highQuality ? 4 : 3,
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
    whiteHeat: new THREE.Color(0xff9858),
    bloodCloud: new THREE.Color(0x4d070b),
  };
  const storm = createStormSheets(THREE, profile, colors, definition.id);
  const filaments = createShearFilaments(THREE, profile, colors, definition.id);
  const stormClouds = createStormCloudField(THREE, profile, colors, definition.id);
  const discs = createAccretionDisc(THREE, profile, colors);
  const abyss = createCollapsingAbyss(THREE, profile, colors);
  const photonRing = createPhotonRing(THREE, profile, colors);
  const infall = createInfallField(THREE, profile, colors, definition.id);

  group.add(
    ...storm.meshes,
    stormClouds.points,
    ...filaments.meshes,
    discs.backDisc,
    ...abyss.meshes,
    discs.frontDisc,
    photonRing.mesh,
    infall.points,
  );
  const light = new THREE.PointLight(0xe04a1f, qualityLevel === "high" ? 54 : 34, profile.stormOuterRadius * 3.4, 1.7);
  light.position.set(profile.abyssRadius * 0.8, profile.abyssRadius * 0.24, profile.abyssRadius * 0.9);
  group.add(light);

  const shaderMaterials = [
    photonRing.material,
    discs.frontMaterial,
    discs.backMaterial,
    infall.material,
    stormClouds.material,
    ...abyss.materials,
    ...storm.materials,
  ];
  const node = {
    ...definition,
    group,
    materials: [...filaments.materials, ...shaderMaterials],
    baseScale: 1,
    userData: {
      shaderMaterials,
      rotors: [discs.frontDisc, discs.backDisc, ...storm.meshes],
      coronas: [...storm.meshes],
      beacon: null,
      abyssCore: abyss.meshes[abyss.meshes.length - 1],
      abyssLayers: abyss.meshes,
      abyssOffsets: abyss.offsets,
      photonRing: photonRing.mesh,
      frontDisc: discs.frontDisc,
      backDisc: discs.backDisc,
      stormLayers: storm.meshes,
      shearFilaments: filaments.meshes,
      stormClouds: stormClouds.points,
    },
  };
  node.userData.blackHole = true;
  node.userData.boss = true;
  return node;
}

export function createCollapsingAbyss(THREE, profile, colors) {
  const diameter = profile.abyssRadius * 2.18;
  const geometry = new THREE.PlaneGeometry(diameter, diameter, 1, 1);
  const meshes = [];
  const materials = [];
  const offsets = [];
  for (let index = 0; index < profile.depthLayers; index += 1) {
    const depthLayer = index / Math.max(1, profile.depthLayers - 1);
    const abyssDepthMaterial = index === profile.depthLayers - 1
      ? { depthWrite: true }
      : { depthWrite: false };
    const material = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        phase: { value: 0.9 + index * 1.47 },
        depthLayer: { value: depthLayer },
        ember: { value: colors.ember },
        bloodCloud: { value: colors.bloodCloud },
        whiteHeat: { value: colors.whiteHeat },
      },
      vertexShader: ABYSS_VERTEX_SHADER,
      fragmentShader: ABYSS_FRAGMENT_SHADER,
      transparent: true,
      ...abyssDepthMaterial,
      depthTest: true,
      side: THREE.DoubleSide,
      blending: THREE.NormalBlending,
      toneMapped: false,
    });
    const mesh = new THREE.Mesh(index === 0 ? geometry : geometry.clone(), material);
    const offset = new THREE.Vector3(
      profile.abyssRadius * (0.018 + index * 0.035),
      profile.abyssRadius * (-0.006 + index * 0.008),
      profile.abyssRadius * (0.07 - index * 0.055),
    );
    mesh.position.copy(offset);
    mesh.scale.setScalar(1 - index * 0.055);
    mesh.renderOrder = 4 + (profile.depthLayers - 1 - index) * 0.25;
    mesh.frustumCulled = false;
    meshes.push(mesh);
    materials.push(material);
    offsets.push(offset);
  }
  return { meshes, materials, offsets };
}

export function createPhotonRing(THREE, profile, colors) {
  const diameter = profile.photonRadius * 2.72;
  const geometry = new THREE.PlaneGeometry(diameter, diameter, 1, 1);
  const material = new THREE.ShaderMaterial({
    uniforms: {
      time: { value: 0 },
      ringWidth: { value: profile.photonWidth },
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
  mesh.position.z = profile.abyssRadius * 0.12;
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
      noiseOctaves: { value: profile.discTurbulenceOctaves },
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
  backDisc.rotation.x = 1.08;
  frontDisc.rotation.x = -1.08;
  [backDisc, frontDisc].forEach((disc) => {
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
    orbitHeight[index] = (random() - 0.5) * profile.abyssRadius * 0.62;
    orbitSize[index] = profile.abyssRadius * (0.012 + random() * 0.026);
  }
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("orbitPhase", new THREE.BufferAttribute(orbitPhase, 1));
  geometry.setAttribute("orbitSpeed", new THREE.BufferAttribute(orbitSpeed, 1));
  geometry.setAttribute("orbitHeight", new THREE.BufferAttribute(orbitHeight, 1));
  geometry.setAttribute("orbitSize", new THREE.BufferAttribute(orbitSize, 1));
  const material = new THREE.ShaderMaterial({
    uniforms: {
      time: { value: 0 },
      innerRadius: { value: profile.abyssRadius * 1.04 },
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

export function createStormSheets(THREE, profile, colors, seedValue) {
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
    mesh.position.z = -profile.abyssRadius * (0.46 + layer * 0.18);
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

export function createShearFilaments(THREE, profile, colors, seedValue) {
  const meshes = [];
  const materials = [];
  const random = mulberry32(hashNumber(seedValue) ^ 0xa53c9e17);
  for (let index = 0; index < profile.filamentCount; index += 1) {
    const startAngle = random() * Math.PI * 2;
    const arc = 0.38 + random() * 1.06;
    const baseRadius = profile.abyssRadius * (1.02 + random() * 1.72);
    const direction = index % 2 === 0 ? 1 : -1;
    const points = [];
    for (let pointIndex = 0; pointIndex < 6; pointIndex += 1) {
      const progress = pointIndex / 5;
      const angle = startAngle + arc * progress * direction;
      const radius = baseRadius * (1 - progress * (0.12 + random() * 0.05));
      points.push(new THREE.Vector3(
        Math.cos(angle) * radius,
        Math.sin(angle) * radius * (0.62 + random() * 0.16),
        (random() - 0.5) * profile.abyssRadius * 0.9,
      ));
    }
    const curve = new THREE.CatmullRomCurve3(points);
    const geometry = new THREE.TubeGeometry(
      curve,
      profile.segments,
      profile.abyssRadius * (0.0025 + random() * 0.004),
      4,
      false,
    );
    const material = new THREE.MeshBasicMaterial({
      color: index % 4 === 0 ? colors.whiteHeat : colors.ember,
      transparent: true,
      opacity: 0.05 + random() * 0.1,
      depthWrite: false,
      depthTest: true,
      blending: THREE.AdditiveBlending,
      toneMapped: false,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.renderOrder = 2;
    mesh.frustumCulled = false;
    mesh.userData.spin = (0.0012 + random() * 0.0028) * direction;
    meshes.push(mesh);
    materials.push(material);
  }
  return { meshes, materials };
}

export function createStormCloudField(THREE, profile, colors, seedValue) {
  const count = profile.stormCloudCount;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);
  const orbitPhase = new Float32Array(count);
  const orbitRadius = new Float32Array(count);
  const orbitHeight = new Float32Array(count);
  const orbitSpeed = new Float32Array(count);
  const cloudSize = new Float32Array(count);
  const random = mulberry32(hashNumber(seedValue) ^ 0xc91f4a53);
  for (let index = 0; index < count; index += 1) {
    orbitPhase[index] = random() * Math.PI * 2;
    orbitRadius[index] = profile.abyssRadius * (1.16 + Math.pow(random(), 0.72) * 1.72);
    orbitHeight[index] = (random() - 0.5) * profile.abyssRadius * 1.12;
    orbitSpeed[index] = (0.006 + random() * 0.014) * (index % 2 === 0 ? 1 : -1);
    cloudSize[index] = profile.abyssRadius * (0.035 + random() * 0.075);
  }
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("orbitPhase", new THREE.BufferAttribute(orbitPhase, 1));
  geometry.setAttribute("orbitRadius", new THREE.BufferAttribute(orbitRadius, 1));
  geometry.setAttribute("orbitHeight", new THREE.BufferAttribute(orbitHeight, 1));
  geometry.setAttribute("orbitSpeed", new THREE.BufferAttribute(orbitSpeed, 1));
  geometry.setAttribute("cloudSize", new THREE.BufferAttribute(cloudSize, 1));
  const material = new THREE.ShaderMaterial({
    uniforms: {
      time: { value: 0 },
      pointScale: { value: 1 },
      ember: { value: colors.ember },
      bloodCloud: { value: colors.bloodCloud },
    },
    vertexShader: STORM_CLOUD_VERTEX_SHADER,
    fragmentShader: STORM_CLOUD_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: false,
    depthTest: true,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const points = new THREE.Points(geometry, material);
  points.position.z = -profile.abyssRadius * 0.28;
  points.renderOrder = 1.5;
  points.frustumCulled = false;
  return { points, material };
}

export function updateBossBlackHole(node, elapsed, delta, isFocused = false) {
  if (!node?.userData?.blackHole) return;
  node.userData.shaderMaterials.forEach((material) => {
    if (material.uniforms?.time) material.uniforms.time.value = elapsed;
  });
  node.userData.frontDisc.rotation.z -= delta * 0.021;
  node.userData.backDisc.rotation.z += delta * 0.014;
  node.userData.photonRing.rotation.z += delta * 0.008;
  node.userData.abyssLayers.forEach((layer, index) => {
    const offset = node.userData.abyssOffsets[index];
    layer.position.x = offset.x + Math.sin(elapsed * (0.08 + index * 0.025) + index) * 1.8;
    layer.position.y = offset.y + Math.cos(elapsed * 0.055 + index * 1.7) * 1.1;
  });
  node.userData.stormLayers.forEach((storm, index) => {
    storm.rotation.z += delta * (0.003 + index * 0.0015) * (index % 2 ? -1 : 1);
    const focusPulse = isFocused ? 1 + Math.sin(elapsed * 0.38 + index) * 0.012 : 1;
    storm.scale.copy(storm.userData.baseScale).multiplyScalar(focusPulse);
  });
  node.userData.shearFilaments.forEach((filament) => {
    filament.rotation.z += delta * filament.userData.spin;
  });
  node.userData.stormClouds.rotation.z -= delta * 0.0018;
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
