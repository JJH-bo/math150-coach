const PORTAL_VERTEX_SHADER = `
  varying vec2 vUv;
  varying vec3 vPosition;
  void main() {
    vUv = uv;
    vPosition = position;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const APERTURE_FRAGMENT_SHADER = `
  uniform vec3 accent;
  uniform vec3 coreColor;
  uniform float time;
  uniform float activity;
  varying vec2 vUv;
  void main() {
    vec2 p = vUv * 2.0 - 1.0;
    float radius = length(p);
    float angle = atan(p.y, p.x);
    float spiral = 0.5 + 0.5 * sin(angle * 7.0 - radius * 25.0 + time * (0.32 + activity * 0.28));
    float fineSpiral = 0.5 + 0.5 * sin(angle * 13.0 + radius * 43.0 - time * 0.18);
    float tunnel = pow(max(0.0, 1.0 - radius), 2.2);
    float rim = smoothstep(0.58, 0.98, radius) * (1.0 - smoothstep(0.9, 1.0, radius));
    float specks = pow(max(0.0, sin(p.x * 91.0 + time) * sin(p.y * 117.0 - time * 0.7)), 18.0);
    vec3 color = coreColor;
    color += accent * (spiral * 0.045 + fineSpiral * 0.018) * tunnel * activity;
    color += accent * rim * (0.08 + spiral * 0.12) * activity;
    color += accent * specks * 0.32 * activity;
    float alpha = 1.0 - smoothstep(0.96, 1.0, radius);
    gl_FragColor = vec4(color, alpha);
  }
`;

const THROAT_FRAGMENT_SHADER = `
  uniform vec3 accent;
  uniform vec3 coreColor;
  uniform float time;
  uniform float activity;
  varying vec2 vUv;
  void main() {
    float lane = pow(max(0.0, sin(vUv.x * 38.0 - vUv.y * 20.0 + time * 0.32)), 10.0);
    float depthFade = smoothstep(0.0, 0.82, vUv.y);
    vec3 color = coreColor + accent * lane * (0.025 + activity * 0.045) * (1.0 - depthFade * 0.7);
    color += accent * 0.018 * (1.0 - depthFade);
    gl_FragColor = vec4(color, 1.0);
  }
`;

const RIM_FRAGMENT_SHADER = `
  uniform vec3 accent;
  uniform float time;
  uniform float intensity;
  uniform float irregularity;
  varying vec2 vUv;
  void main() {
    vec2 p = vUv * 2.0 - 1.0;
    float radius = length(p);
    float angle = atan(p.y, p.x);
    float rimWidth = mix(0.055, 0.032, irregularity);
    float radial = 1.0 - smoothstep(rimWidth, rimWidth * 2.8, abs(radius - 0.9));
    float breakup = sin(angle * 5.0 + time * 0.45) + 0.65 * sin(angle * 11.0 - time * 0.3);
    float gaps = mix(0.72, smoothstep(-0.52, 0.42, breakup), irregularity);
    float hot = 0.18 + 0.82 * pow(max(0.0, cos(angle - 0.72 - sin(time * 0.17) * 0.12)), 4.0);
    hot += 0.34 * pow(max(0.0, cos(angle + 2.15)), 7.0);
    vec3 color = accent * (0.45 + hot * intensity * 1.35);
    float alpha = radial * gaps * (0.1 + intensity * (0.12 + hot * 0.34));
    gl_FragColor = vec4(color, alpha);
  }
`;

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
    gl_PointSize = (1.8 + seed.z * 2.8) * (260.0 / max(2.0, -viewPosition.z));
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
    seed: hashAngle(definition.id),
    distortion: 0.035 + difficulty * 0.035,
  });
  group.add(throat.group);

  const rim = createDistortedRim(THREE, definition.radius, accent, {
    intensity: 0.46 + difficulty * 0.46,
    irregularity: 0.18 + difficulty * 0.46,
    qualityLevel,
    seed: hashAngle(definition.id),
  });
  group.add(rim.mesh);
  const arcs = createLensingArcs(THREE, definition.radius, accent, {
    count: qualityLevel === "high" ? 2 + Math.round(difficulty * 2) : 2,
    thickness: 0.007 + difficulty * 0.004,
    intensity: 0.3 + difficulty * 0.2,
    seed: hashAngle(definition.id),
    qualityLevel,
  });
  group.add(...arcs.meshes);

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
    [...throat.materials, rim.material, infall.material],
    [...arcs.meshes, infall.points],
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
    openness: 0.76,
    seed: hashAngle(definition.id),
    distortion: 0.018,
  });
  group.add(throat.group);
  const rim = createDistortedRim(THREE, definition.radius, accent, {
    intensity: 0.35,
    irregularity: 0.08,
    qualityLevel,
    seed: hashAngle(definition.id),
  });
  group.add(rim.mesh);
  const arcs = createLensingArcs(THREE, definition.radius, accent, {
    count: 1,
    thickness: 0.006,
    intensity: 0.2,
    seed: hashAngle(definition.id),
    qualityLevel,
  });
  group.add(...arcs.meshes);
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
    [...throat.materials, rim.material, infall.material],
    [...arcs.meshes, infall.points],
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
    seed: hashAngle(definition.id),
    distortion: 0.085,
  });
  group.add(throat.group);
  const rim = createDistortedRim(THREE, definition.radius, accent, {
    intensity: 0.94,
    irregularity: 0.92,
    qualityLevel,
    seed: hashAngle(definition.id),
  });
  group.add(rim.mesh);
  const arcs = createLensingArcs(THREE, definition.radius, accent.clone().offsetHSL(-0.02, 0.06, 0.14), {
    count: qualityLevel === "high" ? 5 : 3,
    thickness: 0.012,
    intensity: 0.44,
    seed: hashAngle(definition.id),
    qualityLevel,
    fracture: true,
  });
  group.add(...arcs.meshes);
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
    [...throat.materials, rim.material, infall.material, ...arcs.materials],
    [...arcs.meshes, infall.points],
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
    openness: 0.54,
    seed: hashAngle(definition.id),
    distortion: 0.12,
  });
  group.add(throat.group);
  const rim = createDistortedRim(THREE, definition.radius, whiteHeat, {
    intensity: 1.08,
    irregularity: 0.98,
    qualityLevel,
    seed: hashAngle(definition.id),
  });
  group.add(rim.mesh);
  const innerArcs = createLensingArcs(THREE, definition.radius, whiteHeat, {
    count: qualityLevel === "high" ? 5 : 3,
    thickness: 0.012,
    intensity: 0.58,
    seed: hashAngle(definition.id),
    qualityLevel,
    fracture: true,
  });
  group.add(...innerArcs.meshes);
  const outerArcs = createLensingArcs(THREE, definition.radius * 1.38, ember, {
    count: qualityLevel === "high" ? 3 : 2,
    thickness: 0.008,
    intensity: 0.26,
    seed: hashAngle(definition.id) + 0.37,
    qualityLevel,
    wide: true,
  });
  group.add(...outerArcs.meshes);
  const infall = createInfallField(THREE, definition.radius * 1.42, depth, whiteHeat, {
    count: qualityLevel === "high" ? 340 : 190,
    speed: 0.13,
    seed: hashAngle(definition.id),
  });
  group.add(infall.points);

  const gasEnvelope = createBossGasEnvelope(THREE, definition.radius, [bloodCloud, ember, whiteHeat], qualityLevel);
  group.add(...gasEnvelope.clouds);
  const outerGasHalo = createGasCloudHalo(THREE, definition.radius * 6.7, bloodCloud, 0.78, {
    seed: hashAngle(definition.id),
    turbulence: 1.35,
    qualityLevel,
    boss: true,
  });
  outerGasHalo.position.z = -depth * 0.52;
  outerGasHalo.rotation.z = 0.46;
  const hotGasHalo = createGasCloudHalo(THREE, definition.radius * 4.8, whiteHeat, 0.42, {
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
    [...throat.materials, rim.material, infall.material, ...innerArcs.materials, ...outerArcs.materials, ...gasEnvelope.materials],
    [...innerArcs.meshes, ...outerArcs.meshes, infall.points, ...gasEnvelope.clouds],
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
    openness: 0.8,
    seed: hashAngle(definition.id),
    distortion: 0.028,
  });
  group.add(throat.group);
  const rim = createDistortedRim(THREE, definition.radius, accent, {
    intensity: 0.34,
    irregularity: 0.14,
    qualityLevel,
    seed: hashAngle(definition.id),
  });
  group.add(rim.mesh);
  const arcs = createLensingArcs(THREE, definition.radius * 1.12, accent, {
    count: 2,
    thickness: 0.012,
    intensity: 0.2,
    seed: hashAngle(definition.id),
    qualityLevel,
    wide: true,
  });
  group.add(...arcs.meshes);
  const halo = createCoronaSprite(THREE, definition.radius * 4.8, accent, 0.055);
  halo.position.z = -depth * 0.8;
  group.add(halo);
  const beacon = createStatusBeacon(THREE, definition.radius, accent);
  group.add(beacon);
  const node = finalizeNode(
    definition,
    group,
    [...throat.materials, rim.material, ...arcs.materials],
    arcs.meshes,
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
  const segments = qualityLevel === "high" ? 96 : 56;
  const openness = options.openness ?? 0.62;
  const coreColor = new THREE.Color(options.coreColor ?? 0x000205);
  const material = new THREE.ShaderMaterial({
    uniforms: {
      accent: { value: accent },
      coreColor: { value: coreColor },
      time: { value: 0 },
      activity: { value: options.activity ?? 0.7 },
    },
    vertexShader: PORTAL_VERTEX_SHADER,
    fragmentShader: THROAT_FRAGMENT_SHADER,
    side: THREE.BackSide,
    toneMapped: false,
  });
  const wallGeometry = new THREE.CylinderGeometry(radius * 0.96, radius * openness, depth, segments, 6, true);
  distortRadialGeometry(wallGeometry, "x", "z", options.distortion || 0, options.seed || 0);
  const wall = new THREE.Mesh(wallGeometry, material);
  wall.rotation.x = Math.PI * 0.5;
  wall.position.z = -depth * 0.5;
  wall.renderOrder = 1;
  group.add(wall);

  const aperture = createPortalAperture(THREE, radius * openness, accent, {
    activity: options.activity,
    coreColor,
    qualityLevel,
  });
  aperture.mesh.position.z = -depth;
  group.add(aperture.mesh);
  return { group, materials: [material, aperture.material], wall, aperture: aperture.mesh };
}

export function createPortalAperture(THREE, radius, accent, options = {}) {
  const qualityLevel = options.qualityLevel || "high";
  const material = new THREE.ShaderMaterial({
    uniforms: {
      accent: { value: accent },
      coreColor: { value: options.coreColor instanceof THREE.Color ? options.coreColor : new THREE.Color(options.coreColor ?? 0x000205) },
      time: { value: 0 },
      activity: { value: options.activity ?? 0.7 },
    },
    vertexShader: PORTAL_VERTEX_SHADER,
    fragmentShader: APERTURE_FRAGMENT_SHADER,
    transparent: true,
    depthWrite: true,
    side: THREE.DoubleSide,
    toneMapped: false,
  });
  const mesh = new THREE.Mesh(new THREE.CircleGeometry(radius, qualityLevel === "high" ? 128 : 72), material);
  mesh.renderOrder = 0;
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
    },
    vertexShader: PORTAL_VERTEX_SHADER,
    fragmentShader: RIM_FRAGMENT_SHADER,
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

export function createLensingArcs(THREE, radius, accent, options = {}) {
  const meshes = [];
  const materials = [];
  const count = options.count || 2;
  const seed = options.seed || 0;
  const qualityLevel = options.qualityLevel || "high";
  for (let index = 0; index < count; index += 1) {
    const phase = seed * Math.PI * 2 + index * 1.73;
    const span = options.wide ? 1.65 + (index % 2) * 0.72 : 0.78 + (index % 3) * 0.52;
    const arcRadius = radius * (1.02 + ((index % 3) - 1) * 0.085 + (options.fracture ? (index % 2) * 0.11 : 0));
    const points = [];
    const pointCount = qualityLevel === "high" ? 32 : 20;
    for (let pointIndex = 0; pointIndex <= pointCount; pointIndex += 1) {
      const t = pointIndex / pointCount;
      const angle = phase + t * span;
      const distortion = 1
        + Math.sin(angle * 2.7 + index) * (options.fracture ? 0.13 : 0.065)
        + Math.sin(t * Math.PI * 5.0 + phase) * 0.026;
      points.push(new THREE.Vector3(
        Math.cos(angle) * arcRadius * distortion,
        Math.sin(angle) * arcRadius * (0.82 + (index % 3) * 0.055),
        Math.sin(angle * 1.7 + index) * radius * (0.12 + index * 0.015) + radius * 0.09,
      ));
    }
    const curve = new THREE.CatmullRomCurve3(points);
    const material = new THREE.MeshBasicMaterial({
      color: accent,
      transparent: true,
      opacity: options.intensity ?? 0.55,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      toneMapped: false,
    });
    const mesh = new THREE.Mesh(
      new THREE.TubeGeometry(
        curve,
        qualityLevel === "high" ? 72 : 42,
        Math.max(radius * (options.thickness || 0.02), 0.06),
        qualityLevel === "high" ? 7 : 5,
        false,
      ),
      material,
    );
    mesh.renderOrder = 5;
    meshes.push(mesh);
    materials.push(material);
  }
  return { meshes, materials };
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
      opacity: 0.2 + (index % 3) * 0.055,
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
    const scale = radius * (1.75 + pseudoRandom(index + 101) * 1.15);
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
  const approachDirection = new THREE.Vector3(0.62, 0.24, 1).normalize();
  group.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), approachDirection);
  group.rotateZ((hashAngle(definition.id) - 0.5) * 0.36);
  return group;
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
