const apiBase = "/api/challenge/v1";
const threeModuleUrl = "three";
const GALAXY_SCALE = 1.95;
const macroRadii = [56, 48, 52, 42, 46, 50, 44, 40];

const macroDefinitions = [
  {
    id: "ode_separable",
    title: "可分离变量方程",
    position: [-210, 4, -260],
    color: 0x76e4ff,
    summary: "先判断变量是否真的能分到两侧，再进入积分链。",
  },
  {
    id: "ode_first_order_linear",
    title: "一阶线性方程",
    position: [60, 34, -470],
    color: 0x72e0b8,
    summary: "标准形、积分因子和乘积导数结构构成这片星域的主航道。",
  },
  {
    id: "ode_homogeneous_first_order",
    title: "一阶齐次方程",
    position: [330, -20, -700],
    color: 0xb99cff,
    summary: "通过比值结构和换元视角，把未知区域重新化为可分离航道。",
  },
  {
    id: "ode_exact_equation",
    title: "恰当方程星域",
    position: [-40, -88, -860],
    color: 0x8fdcff,
    visualOnly: true,
    summary: "视觉星域：用于承载恰当性检查、势函数和微分形式。",
  },
  {
    id: "ode_bernoulli",
    title: "伯努利变换星域",
    position: [590, 52, -980],
    color: 0xffd37c,
    visualOnly: true,
    summary: "视觉星域：用于承载代换、指数结构和可化为线性方程的入口。",
  },
  {
    id: "ode_second_order_constant",
    title: "二阶常系数线性星域",
    position: [-430, 68, -980],
    color: 0x9fb5ff,
    visualOnly: true,
    summary: "视觉星域：用于承载特征根、齐次解和受迫响应。",
  },
  {
    id: "ode_nonhom_resonance",
    title: "非齐次共振星域",
    position: [760, -82, -1260],
    color: 0xf4a7ff,
    visualOnly: true,
    summary: "视觉星域：用于承载试探形式、共振检查和待定系数法。",
  },
  {
    id: "ode_reducible_order",
    title: "降阶结构星域",
    position: [-720, -44, -1300],
    color: 0x72e0b8,
    visualOnly: true,
    summary: "视觉星域：用于承载降阶、代换和隐藏的一阶结构。",
  },
];

const nodeTypeDefinitions = [
  { type: "concept", title: "概念", color: 0x8fdcff },
  { type: "trigger", title: "题眼", color: 0xffd37c },
  { type: "method", title: "方法", color: 0x72e0b8 },
  { type: "transformation", title: "转化", color: 0x9fb5ff },
  { type: "calculation", title: "计算", color: 0xf4a7ff },
  { type: "expression", title: "表达", color: 0xff9cae },
  { type: "condition", title: "条件", color: 0x93d5ff },
  { type: "example", title: "例题", color: 0xd6b77a },
  { type: "mistake", title: "易错", color: 0xff8fa3 },
  { type: "proof", title: "证明", color: 0xb8d8ff },
  { type: "comparison", title: "对比", color: 0xc8a7ff },
  { type: "review", title: "复盘", color: 0x9ee6bd },
];

const microTypes = nodeTypeDefinitions;

const realisticBodyProfiles = [
  {
    terrain: "rocky",
    surface: 0x766a5d,
    shadow: 0x221d18,
    highlight: 0xc9bba4,
    atmosphere: 0x7da5c4,
    ring: 0xafa18a,
  },
  {
    terrain: "gas",
    surface: 0x8d7657,
    shadow: 0x231a14,
    highlight: 0xd0b991,
    atmosphere: 0xc49b6d,
    ring: 0xb49464,
  },
  {
    terrain: "oceanic",
    surface: 0x4f6268,
    shadow: 0x141d22,
    highlight: 0xb1beb8,
    atmosphere: 0x7fa9bd,
    ring: 0x8c9aa0,
  },
  {
    terrain: "volcanic",
    surface: 0x716b63,
    shadow: 0x1a1715,
    highlight: 0xbdb3a3,
    atmosphere: 0x9a958e,
    ring: 0xa89a82,
  },
];

const realisticMoonProfiles = [
  {
    terrain: "moon",
    surface: 0x777b80,
    shadow: 0x191c20,
    highlight: 0xc6c7c2,
    atmosphere: 0x8da4b8,
    ring: 0x8fa2ad,
  },
  {
    terrain: "moon",
    surface: 0x5d5148,
    shadow: 0x16120f,
    highlight: 0xb29f88,
    atmosphere: 0x9e8568,
    ring: 0x9b876f,
  },
  {
    terrain: "ice",
    surface: 0x56626e,
    shadow: 0x11171d,
    highlight: 0xb4c0c8,
    atmosphere: 0x8cb0c8,
    ring: 0x8798a4,
  },
];

const compareDefinitions = [
  {
    id: "ode.compare.separable_vs_linear",
    title: "可分离 vs 一阶线性",
    position: [-120, 72, -380],
    color: 0xffd37c,
  },
  {
    id: "ode.compare.linear_vs_homogeneous",
    title: "一阶线性 vs 一阶齐次",
    position: [230, 76, -610],
    color: 0xffd37c,
  },
  {
    id: "ode.compare.separable_vs_homogeneous",
    title: "可分离 vs 一阶齐次",
    position: [90, -102, -560],
    color: 0xffd37c,
  },
];

const guideDefinitions = [
  {
    id: "ode.guide.first_order_foundation",
    title: "一阶方程入口锚点",
    position: [-260, -86, -170],
    color: 0x76e4ff,
  },
  {
    id: "ode.guide.boss_readiness_gate",
    title: "Boss 验收门槛",
    position: [680, 30, -1420],
    color: 0xffffff,
  },
];

const statusLabels = {
  locked: "未解锁",
  available: "可探索",
  active: "当前任务",
  mastered: "已点亮",
  failed: "受损",
};

const dom = {};
const state = {
  THREE: null,
  renderer: null,
  composer: null,
  bloomPass: null,
  scene: null,
  camera: null,
  clock: null,
  keys: new Set(),
  velocity: null,
  objects: [],
  objectById: new Map(),
  lines: [],
  surfaceMapCache: new Map(),
  nebulaSprites: [],
  nearest: null,
  activeObject: null,
  currentTaskId: null,
  lastPayload: null,
  started: false,
  yaw: 0,
  pitch: -0.08,
  hasFramedInitialTask: false,
  pointerLocked: false,
  sessionId: localStorage.getItem("math150-space-session-id") || makeSessionId(),
  toastTimer: null,
};

startSpaceExperience();

async function startSpaceExperience() {
  try {
    await init();
  } catch (error) {
    console.error(error);
    showRenderFallback(error);
  }
}

async function init() {
  cacheDom();
  wireDom();
  dom.sessionBadge.textContent = state.sessionId;
  localStorage.setItem("math150-space-session-id", state.sessionId);

  if (!webglAvailable()) {
    showFallback("当前浏览器没有可用的 WebGL 上下文。");
    return;
  }

  const THREE = await loadThree();
  if (!THREE) return;

  createKnowledgeUniverse(THREE);
  await bootChallengeState();
  hideLoading();
  animate();
}

function showRenderFallback(error) {
  const message = error instanceof Error ? error.message : String(error || "未知渲染错误");
  showFallback(message);
}

async function loadThree() {
  try {
    const module = await import(threeModuleUrl);
    state.THREE = module;
    const [{ EffectComposer }, { RenderPass }, { UnrealBloomPass }] = await Promise.all([
      import("three/addons/postprocessing/EffectComposer.js"),
      import("three/addons/postprocessing/RenderPass.js"),
      import("three/addons/postprocessing/UnrealBloomPass.js"),
    ]);
    state.post = { EffectComposer, RenderPass, UnrealBloomPass };
    return module;
  } catch (error) {
    showFallback("Three.js 没有加载成功。请检查网络后刷新，或先返回 2D 训练器。");
    return null;
  }
}

function createKnowledgeUniverse(THREE) {
  const canvas = dom.canvas;
  const renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: true,
    alpha: false,
    powerPreference: "high-performance",
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.8));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.9;
  if ("outputColorSpace" in renderer) renderer.outputColorSpace = THREE.SRGBColorSpace;
  if (renderer.shadowMap) {
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  }

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x020511);
  scene.fog = new THREE.FogExp2(0x061022, 0.00034);

  const camera = new THREE.PerspectiveCamera(70, window.innerWidth / window.innerHeight, 0.1, 5200);
  camera.position.set(-120, 36, 40);
  camera.rotation.order = "YXZ";
  camera.lookAt(new THREE.Vector3(-210, 8, -260));
  state.yaw = camera.rotation.y;
  state.pitch = camera.rotation.x;

  state.renderer = renderer;
  state.scene = scene;
  state.camera = camera;
  state.clock = new THREE.Clock();
  state.velocity = new THREE.Vector3();

  addCinematicLighting(THREE, scene);

  createWorldLockedSky(THREE, scene);
  createSolarLightSource(THREE, scene);
  buildOdeSector(THREE, scene);

  const composer = new state.post.EffectComposer(renderer);
  composer.addPass(new state.post.RenderPass(scene, camera));
  const bloomPass = new state.post.UnrealBloomPass(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    0.32,
    0.38,
    0.72,
  );
  composer.addPass(bloomPass);
  state.composer = composer;
  state.bloomPass = bloomPass;

  window.addEventListener("resize", resizeRenderer);
}

function addCinematicLighting(THREE, scene) {
  const ambient = new THREE.AmbientLight(0x789cff, 0.22);
  scene.add(ambient);

  const hemisphere = new THREE.HemisphereLight(0x9edcff, 0x050714, 0.64);
  scene.add(hemisphere);

  const keyLight = new THREE.DirectionalLight(0xffffff, 3.45);
  keyLight.position.set(-80, 120, 90);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(2048, 2048);
  keyLight.shadow.camera.near = 1;
  keyLight.shadow.camera.far = 520;
  keyLight.shadow.camera.left = -210;
  keyLight.shadow.camera.right = 210;
  keyLight.shadow.camera.top = 210;
  keyLight.shadow.camera.bottom = -210;
  scene.add(keyLight);

  const rimLight = new THREE.DirectionalLight(0x76e4ff, 1.6);
  rimLight.position.set(120, 42, -280);
  scene.add(rimLight);

  const violetFill = new THREE.PointLight(0xb99cff, 1.65, 430);
  violetFill.position.set(36, -40, -238);
  scene.add(violetFill);

  const nebulaCore = new THREE.PointLight(0x72e0b8, 1, 300);
  nebulaCore.position.set(-92, 18, -172);
  scene.add(nebulaCore);
}

function addNebulaVeils(THREE, scene) {
  const veils = [
    { color: 0x164d75, position: [-90, 12, -260], scale: [280, 132, 1], opacity: 0.3 },
    { color: 0x4f3488, position: [78, -26, -360], scale: [306, 164, 1], opacity: 0.26 },
    { color: 0x2d7c6a, position: [-10, -42, -190], scale: [238, 108, 1], opacity: 0.19 },
    { color: 0x185e95, position: [-38, 24, -148], scale: [164, 76, 1], opacity: 0.17 },
    { color: 0x6f3c9d, position: [42, 28, -250], scale: [190, 84, 1], opacity: 0.14 },
  ];
  for (const veil of veils) {
    const material = new THREE.SpriteMaterial({
      map: createNebulaTexture(THREE, veil.color),
      color: veil.color,
      transparent: true,
      opacity: veil.opacity,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
    });
    const sprite = new THREE.Sprite(material);
    sprite.position.set(...veil.position);
    sprite.scale.set(...veil.scale);
    scene.add(sprite);
  }
}

function scaledKnowledgePosition(position) {
  return [position[0] * GALAXY_SCALE, position[1] * 1.45, position[2] * GALAXY_SCALE];
}

function macroRadiusFor(index) {
  return macroRadii[index % macroRadii.length];
}

function buildOdeSector(THREE, scene) {
  const macroPositions = new Map();
  for (const [macroIndex, macro] of macroDefinitions.entries()) {
    const macroPosition = scaledKnowledgePosition(macro.position);
    const macroRadius = macroRadiusFor(macroIndex);
    const macroObject = createSpaceObject(THREE, {
      ...macro,
      kind: "macro",
      role: "知识星体",
      position: macroPosition,
      radius: macroRadius,
      interactionRadius: macroRadius * 3.6,
    });
    scene.add(macroObject.group);
    registerObject(macroObject);
    macroPositions.set(macro.id, new THREE.Vector3(...macroPosition));

    const satellitePositions = [];
    microTypes.forEach((micro, index) => {
      const angle = (Math.PI * 2 * index) / microTypes.length + 0.32;
      const orbitBase = 120;
      const orbit = orbitBase + (index % 4) * 30;
      const position = [
        macroPosition[0] + Math.cos(angle) * orbit,
        macroPosition[1] + Math.sin(index * 1.7) * (24 + (index % 3) * 5),
        macroPosition[2] + Math.sin(angle) * orbit,
      ];
      const moonRadius = 4.8 + (index % 4) * 1.1;
      const object = createSpaceObject(THREE, {
        id: `${macro.id}.${micro.type}`,
        title: `${macro.title} · ${micro.title}`,
        kind: "micro",
        role: "能力卫星",
        position,
        color: micro.color,
        radius: moonRadius,
        interactionRadius: 42 + moonRadius * 2.8,
        summary: `${micro.title}能力点，靠近后可进入当前训练遭遇。`,
      });
      scene.add(object.group);
      registerObject(object);
      satellitePositions.push(new THREE.Vector3(...position));
      if (index === 0) addRoute(THREE, scene, macroPosition, position, micro.color, 0.18);
      if (index > 0) addRoute(THREE, scene, satellitePositions[index - 1], position, micro.color, 0.16);
    });

    const bossPosition = [macroPosition[0] + 82, macroPosition[1] + 68, macroPosition[2] - 196];
    const boss = createSpaceObject(THREE, {
      id: `${macro.id}.macro_challenge`,
      title: `${macro.title} · Boss 星门`,
      kind: "boss",
      role: "综合星门",
      position: bossPosition,
      color: 0xb99cff,
      radius: 18,
      interactionRadius: 112,
      summary: "完成能力卫星后，通过 Boss 星门验证整条推理链。",
    });
    scene.add(boss.group);
    registerObject(boss);
    addRoute(THREE, scene, satellitePositions[satellitePositions.length - 1], bossPosition, 0xb99cff, 0.34);
  }

  for (let index = 0; index < macroDefinitions.length - 1; index += 1) {
    addRoute(
      THREE,
      scene,
      scaledKnowledgePosition(macroDefinitions[index].position),
      scaledKnowledgePosition(macroDefinitions[index + 1].position),
      0x76e4ff,
      0.16,
    );
  }

  for (const compare of compareDefinitions) {
    const object = createSpaceObject(THREE, {
      ...compare,
      kind: "compare",
      role: "易混双星",
      position: scaledKnowledgePosition(compare.position),
      radius: 9,
      interactionRadius: 62,
      summary: "这里不是新题目，而是用来区分相邻入口和方法的对比航标。",
    });
    scene.add(object.group);
    registerObject(object);
  }

  for (const guide of guideDefinitions) {
    const object = createSpaceObject(THREE, {
      ...guide,
      kind: "guide",
      role: "导航信标",
      position: scaledKnowledgePosition(guide.position),
      radius: 8,
      interactionRadius: 58,
      summary: "导航信标帮助你理解星域结构，不消耗训练机会。",
    });
    scene.add(object.group);
    registerObject(object);
  }
}

function realisticBodyProfile(definition) {
  const profiles = definition.kind === "micro" || definition.kind === "guide"
    ? realisticMoonProfiles
    : realisticBodyProfiles;
  const macroIndex = definition.kind === "macro"
    ? macroDefinitions.findIndex((macro) => macro.id === definition.id)
    : -1;
  const profileIndex = macroIndex >= 0
    ? macroIndex % profiles.length
    : hashString(`${definition.id}-${definition.kind}`) % profiles.length;
  const profile = profiles[profileIndex];
  return {
    ...profile,
    accent: definition.color || profile.atmosphere,
  };
}

function createSpaceObject(THREE, definition) {
  const group = new THREE.Group();
  group.position.set(...definition.position);
  group.userData.id = definition.id;

  const materials = [];
  const color = definition.color || 0x76e4ff;
  const profile = realisticBodyProfile(definition);
  let primaryMesh;

  if (definition.kind === "boss") {
    const gateMaterial = new THREE.MeshPhysicalMaterial({
      color,
      emissive: color,
      emissiveIntensity: 1.25,
      roughness: 0.18,
      metalness: 0.72,
      clearcoat: 0.8,
      clearcoatRoughness: 0.16,
      transparent: true,
      opacity: 0.92,
    });
    const gate = new THREE.Mesh(new THREE.TorusGeometry(definition.radius, 0.42, 24, 144), gateMaterial);
    gate.rotation.y = Math.PI / 2;
    gate.castShadow = true;
    gate.receiveShadow = true;
    group.add(gate);
    materials.push(gateMaterial);
    primaryMesh = gate;

    const innerGateMaterial = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.18,
      depthWrite: false,
      blending: THREE.AdditiveBlending,
      side: THREE.DoubleSide,
    });
    const innerGate = new THREE.Mesh(new THREE.CircleGeometry(definition.radius * 0.72, 96), innerGateMaterial);
    innerGate.rotation.y = Math.PI / 2;
    group.add(innerGate);
    materials.push(innerGateMaterial);

    const coreMaterial = new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      emissive: color,
      emissiveIntensity: 1.55,
      roughness: 0.08,
      metalness: 0.24,
      transmission: 0.18,
      thickness: 0.8,
    });
    const core = new THREE.Mesh(new THREE.IcosahedronGeometry(definition.radius * 0.26, 3), coreMaterial);
    core.castShadow = true;
    group.add(core);
    materials.push(coreMaterial);
  } else {
    const surfaceMaps = createPlanetSurfaceMaps(THREE, profile, definition.kind, definition.id);
    const material = new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      map: surfaceMaps.colorMap,
      bumpMap: surfaceMaps.bumpMap,
      bumpScale: definition.kind === "macro" ? definition.radius * 0.018 : definition.radius * 0.01,
      roughnessMap: surfaceMaps.roughnessMap,
      emissiveMap: surfaceMaps.emissiveMap,
      emissive: 0xd3a26c,
      emissiveIntensity: definition.kind === "macro" ? 0.11 : 0.015,
      roughness: definition.kind === "macro" ? 0.72 : 0.88,
      metalness: 0.02,
      clearcoat: profile.terrain === "oceanic" ? 0.18 : 0.025,
      clearcoatRoughness: 0.78,
    });
    material.userData.preserveSurfaceColor = true;
    material.userData.surfaceEmissiveIntensity = material.emissiveIntensity;
    const widthSegments = definition.kind === "macro" ? 96 : 64;
    primaryMesh = new THREE.Mesh(new THREE.SphereGeometry(definition.radius, widthSegments, widthSegments / 2), material);
    primaryMesh.castShadow = true;
    primaryMesh.receiveShadow = true;
    group.add(primaryMesh);
    materials.push(material);

    const atmosphere = createAtmosphereShell(THREE, definition.radius, profile.atmosphere, definition.kind);
    group.add(atmosphere);

    const halo = createHaloSprite(THREE, definition.radius, profile.atmosphere, definition.kind);
    group.add(halo);

    if (definition.kind === "macro" && hashString(definition.id) % 3 === 0) {
      const ringMaterial = new THREE.MeshPhysicalMaterial({
        color: profile.ring,
        transparent: true,
        opacity: 0.16,
        roughness: 0.88,
        metalness: 0.02,
        depthWrite: false,
        side: THREE.DoubleSide,
      });
      const ring = new THREE.Mesh(
        new THREE.RingGeometry(definition.radius * 1.3, definition.radius * 1.92, 192, 4),
        ringMaterial,
      );
      ring.rotation.x = Math.PI / 2.45;
      ring.rotation.z = Math.PI / 8;
      group.add(ring);
      materials.push(ringMaterial);
    }
  }

  const markerMaterial = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: 0.0,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  markerMaterial.userData.statusAccent = true;
  const marker = new THREE.Mesh(
    new THREE.TorusGeometry(definition.radius * 1.45, 0.035, 8, 128),
    markerMaterial,
  );
  marker.rotation.x = Math.PI / 8;
  marker.rotation.z = -Math.PI / 7;
  group.add(marker);
  materials.push(markerMaterial);

  const pointLight = new THREE.PointLight(
    0xffe1bc,
    definition.kind === "macro" ? 1.8 : 0.45,
    definition.radius * 14,
    0,
  );
  pointLight.position.set(-definition.radius * 3, definition.radius * 2.1, definition.radius * 4.4);
  group.add(pointLight);

  return {
    ...definition,
    group,
    primaryMesh,
    marker,
    markerMaterial,
    materials,
    baseScale: 1,
    status: "available",
    isCurrent: false,
  };
}

function registerObject(object) {
  state.objects.push(object);
  state.objectById.set(object.id, object);
}

function addRoute(THREE, scene, fromValue, toValue, color, opacity) {
  const from = Array.isArray(fromValue) ? new THREE.Vector3(...fromValue) : fromValue;
  const to = Array.isArray(toValue) ? new THREE.Vector3(...toValue) : toValue;
  const distance = from.distanceTo(to);
  const mid = from.clone().lerp(to, 0.5);
  mid.y += Math.max(16, distance * 0.11);
  const curve = new THREE.QuadraticBezierCurve3(from.clone(), mid, to.clone());
  const geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(96));
  const material = new THREE.LineDashedMaterial({
    color,
    transparent: true,
    opacity: Math.min(0.42, 0.12 + opacity * 1.5),
    dashSize: Math.max(2.4, distance * 0.012),
    gapSize: Math.max(3.8, distance * 0.018),
    depthWrite: false,
    toneMapped: false,
  });
  material.userData.baseOpacity = material.opacity;
  const route = new THREE.Line(geometry, material);
  route.computeLineDistances();
  scene.add(route);
  state.lines.push(route);
}

function createWorldLockedSky(THREE, scene) {
  scene.background = createDeepSpaceTexture(THREE);

  const panorama = new THREE.TextureLoader().load(
    "/trainer/space/assets/milky-way-eso-6000.jpg",
    (texture) => {
      scene.background = texture;
    },
  );
  panorama.mapping = THREE.EquirectangularReflectionMapping;
  panorama.colorSpace = THREE.SRGBColorSpace;
  panorama.minFilter = THREE.LinearMipmapLinearFilter;
  panorama.magFilter = THREE.LinearFilter;
  panorama.generateMipmaps = true;
  scene.backgroundIntensity = 0.62;
  if (scene.backgroundRotation) scene.backgroundRotation.set(-0.16, 0, -0.14);
}

function createSolarLightSource(THREE, scene) {
  const sunTexture = createSolarFlareTexture(THREE);
  const material = new THREE.SpriteMaterial({
    map: sunTexture,
    color: 0xffd6a0,
    transparent: true,
    opacity: 0.72,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const sun = new THREE.Sprite(material);
  sun.position.set(-610, 78, -330);
  sun.scale.set(210, 210, 1);
  scene.add(sun);
  state.nebulaSprites.push({
    sprite: sun,
    material,
    baseOpacity: material.opacity,
    baseY: sun.position.y,
    pulseSpeed: 0.28,
    pulseAmount: 0.08,
    driftSpeed: 0.12,
    driftAmount: 2.8,
    rotationSpeed: 0.012,
    phase: 0.4,
  });

  const warmKey = new THREE.PointLight(0xffc48a, 2.1, 820);
  warmKey.position.copy(sun.position);
  scene.add(warmKey);
}

function createDeepSpaceTexture(THREE) {
  if (state.deepSpaceTexture) return state.deepSpaceTexture;
  const canvas = document.createElement("canvas");
  canvas.width = 2048;
  canvas.height = 1024;
  const ctx = canvas.getContext("2d");
  const rng = mulberry32(90210);

  const base = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
  base.addColorStop(0, "#020306");
  base.addColorStop(0.42, "#050a12");
  base.addColorStop(0.72, "#070912");
  base.addColorStop(1, "#010204");
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  drawMilkyDustBand(ctx, canvas, rng, {
    y: canvas.height * 0.34,
    width: canvas.width * 0.62,
    height: 88,
    rotation: -0.17,
    warm: true,
    alpha: 0.42,
  });
  drawMilkyDustBand(ctx, canvas, rng, {
    y: canvas.height * 0.62,
    width: canvas.width * 0.5,
    height: 120,
    rotation: 0.09,
    warm: false,
    alpha: 0.24,
  });

  for (let index = 0; index < 220; index += 1) {
    const x = rng() * canvas.width;
    const y = rng() * canvas.height;
    const radius = 38 + rng() * 180;
    const color = rng() > 0.45 ? [70, 112, 170] : [120, 80, 145];
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
    gradient.addColorStop(0, `rgba(${color[0]},${color[1]},${color[2]},${0.018 + rng() * 0.036})`);
    gradient.addColorStop(0.48, `rgba(${color[0]},${color[1]},${color[2]},${0.008 + rng() * 0.014})`);
    gradient.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
  }

  for (let index = 0; index < 8200; index += 1) {
    const x = rng() * canvas.width;
    const y = rng() * canvas.height;
    const radius = rng() > 0.985 ? 1.25 + rng() * 1.4 : 0.25 + rng() * 0.72;
    const tint = rng();
    const alpha = rng() > 0.985 ? 0.72 : 0.16 + rng() * 0.38;
    const color = tint > 0.78 ? "255,225,185" : tint > 0.54 ? "205,222,255" : "245,248,255";
    ctx.fillStyle = `rgba(${color},${alpha})`;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
  }

  state.deepSpaceTexture = new THREE.CanvasTexture(canvas);
  state.deepSpaceTexture.colorSpace = THREE.SRGBColorSpace;
  return state.deepSpaceTexture;
}

function createSolarFlareTexture(THREE) {
  if (state.solarFlareTexture) return state.solarFlareTexture;
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext("2d");
  const gradient = ctx.createRadialGradient(80, 256, 0, 80, 256, 250);
  gradient.addColorStop(0, "rgba(255,244,214,1)");
  gradient.addColorStop(0.18, "rgba(255,202,132,0.78)");
  gradient.addColorStop(0.46, "rgba(255,165,85,0.22)");
  gradient.addColorStop(1, "rgba(255,150,60,0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = "rgba(255,225,180,0.22)";
  for (let index = 0; index < 22; index += 1) {
    const angle = (Math.PI * 2 * index) / 22;
    const length = 140 + (index % 5) * 28;
    ctx.beginPath();
    ctx.moveTo(80 + Math.cos(angle) * 24, 256 + Math.sin(angle) * 24);
    ctx.lineTo(80 + Math.cos(angle) * length, 256 + Math.sin(angle) * length);
    ctx.stroke();
  }

  state.solarFlareTexture = new THREE.CanvasTexture(canvas);
  state.solarFlareTexture.colorSpace = THREE.SRGBColorSpace;
  return state.solarFlareTexture;
}

function createPlanetSurfaceMaps(THREE, profile, kind, seedValue) {
  const isMacro = kind === "macro";
  const cacheKey = `${profile.terrain}-${profile.surface}-${isMacro ? "macro" : "minor"}`;
  if (state.surfaceMapCache.has(cacheKey)) return state.surfaceMapCache.get(cacheKey);

  const width = isMacro ? 1024 : 512;
  const height = width / 2;
  const colorCanvas = document.createElement("canvas");
  const bumpCanvas = document.createElement("canvas");
  const roughnessCanvas = document.createElement("canvas");
  const emissiveCanvas = document.createElement("canvas");
  for (const canvas of [colorCanvas, bumpCanvas, roughnessCanvas, emissiveCanvas]) {
    canvas.width = width;
    canvas.height = height;
  }

  const colorContext = colorCanvas.getContext("2d");
  const bumpContext = bumpCanvas.getContext("2d");
  const roughnessContext = roughnessCanvas.getContext("2d");
  const emissiveContext = emissiveCanvas.getContext("2d");
  const colorImage = colorContext.createImageData(width, height);
  const bumpImage = bumpContext.createImageData(width, height);
  const roughnessImage = roughnessContext.createImageData(width, height);
  const emissiveImage = emissiveContext.createImageData(width, height);
  const base = colorChannels(THREE, profile.surface);
  const shadow = colorChannels(THREE, profile.shadow);
  const highlight = colorChannels(THREE, profile.highlight);
  const seed = hashString(`${profile.terrain}-${seedValue}`);

  for (let y = 0; y < height; y += 1) {
    const v = y / (height - 1);
    const latitude = Math.abs(v - 0.5) * 2;
    for (let x = 0; x < width; x += 1) {
      const u = x / (width - 1);
      const broad = periodicFbm(u, v, seed, 5);
      const detail = periodicFbm(u, v, seed + 1931, 4, 14, 7);
      const ridge = 1 - Math.abs(periodicFbm(u, v, seed + 7727, 3, 9, 5) * 2 - 1);
      let elevation = broad * 0.62 + detail * 0.22 + ridge * 0.16;

      if (profile.terrain === "oceanic") elevation = elevation * 1.18 - 0.08;
      if (profile.terrain === "ice") elevation = elevation * 0.76 + latitude * 0.24;
      if (profile.terrain === "volcanic") elevation = broad * 0.72 + ridge * 0.28;
      if (profile.terrain === "gas") {
        const bands = Math.sin(v * Math.PI * 38 + broad * 3.4) * 0.5 + 0.5;
        elevation = bands * 0.72 + detail * 0.28;
      }

      const color = terrainColor(profile.terrain, elevation, latitude, shadow, base, highlight);
      const index = (y * width + x) * 4;
      colorImage.data[index] = color[0];
      colorImage.data[index + 1] = color[1];
      colorImage.data[index + 2] = color[2];
      colorImage.data[index + 3] = 255;

      const bump = Math.round(clamp01(elevation) * 255);
      bumpImage.data[index] = bump;
      bumpImage.data[index + 1] = bump;
      bumpImage.data[index + 2] = bump;
      bumpImage.data[index + 3] = 255;

      const roughness = Math.round((0.72 + detail * 0.24) * 255);
      roughnessImage.data[index] = roughness;
      roughnessImage.data[index + 1] = roughness;
      roughnessImage.data[index + 2] = roughness;
      roughnessImage.data[index + 3] = 255;

      const cityNoise = latticeHash(x, y, seed + 4201);
      const city = isMacro
        && profile.terrain !== "ice"
        && profile.terrain !== "gas"
        && elevation > 0.55
        && cityNoise > 0.9965;
      const fissure = profile.terrain === "volcanic" && ridge > 0.91 && detail > 0.62;
      const emission = city ? 230 : fissure ? 104 : 0;
      emissiveImage.data[index] = emission;
      emissiveImage.data[index + 1] = emission;
      emissiveImage.data[index + 2] = emission;
      emissiveImage.data[index + 3] = 255;
    }
  }

  colorContext.putImageData(colorImage, 0, 0);
  bumpContext.putImageData(bumpImage, 0, 0);
  roughnessContext.putImageData(roughnessImage, 0, 0);
  emissiveContext.putImageData(emissiveImage, 0, 0);

  const colorMap = configurePlanetTexture(THREE, colorCanvas, true);
  const bumpMap = configurePlanetTexture(THREE, bumpCanvas, false);
  const roughnessMap = configurePlanetTexture(THREE, roughnessCanvas, false);
  const emissiveMap = configurePlanetTexture(THREE, emissiveCanvas, false);
  const maps = { colorMap, bumpMap, roughnessMap, emissiveMap };
  state.surfaceMapCache.set(cacheKey, maps);
  return maps;
}

function configurePlanetTexture(THREE, canvas, useSrgb) {
  const texture = new THREE.CanvasTexture(canvas);
  if (useSrgb) texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  texture.anisotropy = 8;
  return texture;
}

function colorChannels(THREE, value) {
  const color = new THREE.Color(value);
  return [color.r * 255, color.g * 255, color.b * 255];
}

function terrainColor(terrain, elevation, latitude, shadow, base, highlight) {
  let t = clamp01((elevation - 0.18) / 0.72);
  if (terrain === "oceanic" && elevation < 0.5) t *= 0.48;
  if (terrain === "volcanic") t *= 0.72;
  const low = t < 0.55 ? shadow : base;
  const high = t < 0.55 ? base : highlight;
  const mix = t < 0.55 ? t / 0.55 : (t - 0.55) / 0.45;
  const polar = terrain === "ice" || terrain === "oceanic"
    ? clamp01((latitude - 0.68) / 0.3) * (terrain === "ice" ? 0.72 : 0.42)
    : 0;
  return low.map((channel, index) => Math.round(
    channel + (high[index] - channel) * mix + (highlight[index] - channel) * polar,
  ));
}

function periodicFbm(u, v, seed, octaves, baseX = 5, baseY = 3) {
  let value = 0;
  let amplitude = 0.56;
  let total = 0;
  for (let octave = 0; octave < octaves; octave += 1) {
    const periodX = baseX * (2 ** octave);
    const periodY = baseY * (2 ** octave);
    value += periodicValueNoise(u * periodX, v * periodY, seed + octave * 1013, periodX) * amplitude;
    total += amplitude;
    amplitude *= 0.5;
  }
  return value / total;
}

function periodicValueNoise(x, y, seed, periodX) {
  const x0 = Math.floor(x);
  const y0 = Math.floor(y);
  const tx = x - x0;
  const ty = y - y0;
  const sx = tx * tx * (3 - 2 * tx);
  const sy = ty * ty * (3 - 2 * ty);
  const wrapX = (value) => ((value % periodX) + periodX) % periodX;
  const a = latticeHash(wrapX(x0), y0, seed);
  const b = latticeHash(wrapX(x0 + 1), y0, seed);
  const c = latticeHash(wrapX(x0), y0 + 1, seed);
  const d = latticeHash(wrapX(x0 + 1), y0 + 1, seed);
  const top = a + (b - a) * sx;
  const bottom = c + (d - c) * sx;
  return top + (bottom - top) * sy;
}

function latticeHash(x, y, seed) {
  let value = Math.imul(x + seed, 374761393) ^ Math.imul(y - seed, 668265263);
  value = Math.imul(value ^ (value >>> 13), 1274126177);
  return ((value ^ (value >>> 16)) >>> 0) / 4294967295;
}

function clamp01(value) {
  return Math.max(0, Math.min(1, value));
}

function createAtmosphereShell(THREE, radius, color, kind) {
  const atmosphere = new THREE.Mesh(
    new THREE.SphereGeometry(radius * (kind === "macro" ? 1.028 : 1.055), 72, 36),
    new THREE.ShaderMaterial({
      uniforms: {
        glowColor: { value: new THREE.Color(color) },
        intensity: { value: kind === "macro" ? 0.1 : 0.055 },
      },
      vertexShader: `
        varying vec3 vNormal;
        varying vec3 vWorldPosition;
        void main() {
          vNormal = normalize(normalMatrix * normal);
          vec4 worldPosition = modelMatrix * vec4(position, 1.0);
          vWorldPosition = worldPosition.xyz;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 glowColor;
        uniform float intensity;
        varying vec3 vNormal;
        varying vec3 vWorldPosition;
        void main() {
          vec3 viewDirection = normalize(cameraPosition - vWorldPosition);
          float rim = pow(1.0 - max(dot(vNormal, viewDirection), 0.0), 2.35);
          float core = pow(max(dot(vNormal, viewDirection), 0.0), 9.0) * 0.05;
          gl_FragColor = vec4(glowColor, clamp((rim + core) * intensity, 0.0, 0.72));
        }
      `,
      transparent: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.BackSide,
    }),
  );
  atmosphere.renderOrder = 2;
  return atmosphere;
}

function createHaloSprite(THREE, radius, color, kind) {
  const material = new THREE.SpriteMaterial({
    map: createSoftParticleTexture(THREE),
    color,
    transparent: true,
    opacity: kind === "macro" ? 0.006 : 0.003,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const sprite = new THREE.Sprite(material);
  const scale = radius * (kind === "macro" ? 4.8 : 4.1);
  sprite.scale.set(scale, scale, 1);
  return sprite;
}

function createSoftParticleTexture(THREE) {
  if (state.softParticleTexture) return state.softParticleTexture;
  const canvas = document.createElement("canvas");
  canvas.width = 96;
  canvas.height = 96;
  const ctx = canvas.getContext("2d");
  const gradient = ctx.createRadialGradient(48, 48, 0, 48, 48, 48);
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(0.22, "rgba(255,255,255,0.82)");
  gradient.addColorStop(0.58, "rgba(255,255,255,0.18)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 96, 96);
  state.softParticleTexture = new THREE.CanvasTexture(canvas);
  state.softParticleTexture.colorSpace = THREE.SRGBColorSpace;
  return state.softParticleTexture;
}

function createNebulaTexture(THREE, color) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  const base = new THREE.Color(color);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let index = 0; index < 42; index += 1) {
    const x = Math.random() * canvas.width;
    const y = Math.random() * canvas.height;
    const radius = 42 + Math.random() * 130;
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, radius);
    gradient.addColorStop(0, colorStyle(base, 1.4, 0.16));
    gradient.addColorStop(0.38, colorStyle(base, 0.8, 0.075));
    gradient.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

async function bootChallengeState() {
  const knownSession = localStorage.getItem("math150-space-session-known") === "1";
  if (!knownSession) {
    await startChallenge({ quiet: true });
    return;
  }
  try {
    const payload = await request(`/status/${encodeURIComponent(state.sessionId)}`);
    applyChallengeState(payload);
    showToast("已恢复宇宙训练状态");
  } catch {
    await startChallenge({ quiet: true });
  }
}

async function startChallenge(options = {}) {
  const payload = await request("/start", {
    method: "POST",
    body: {
      chapter_id: "ode_network_mvp",
      session_id: state.sessionId,
    },
  });
  state.started = true;
  localStorage.setItem("math150-space-session-known", "1");
  applyChallengeState(payload);
  if (!options.quiet) showToast("已同步当前训练星域");
}

async function loadStatus() {
  const payload = await request(`/status/${encodeURIComponent(state.sessionId)}`);
  applyChallengeState(payload);
  showToast("星域状态已刷新");
}

async function resetChallenge() {
  const payload = await request("/reset", {
    method: "POST",
    body: {
      session_id: state.sessionId,
      reset_all: true,
    },
  });
  state.hasFramedInitialTask = false;
  applyChallengeState(payload);
  showToast("训练星域已重置");
}

async function submitAnswer(event) {
  event.preventDefault();
  if (!state.activeObject || state.activeObject.id !== state.currentTaskId) {
    showToast("请先靠近当前任务节点，再提交遭遇。");
    return;
  }
  const answer = dom.answerInput.value.trim();
  if (!answer) {
    showToast("先写下你的判断或步骤。");
    return;
  }

  dom.submitBtn.disabled = true;
  try {
    const payload = await request("/submit", {
      method: "POST",
      body: {
        session_id: state.sessionId,
        answer,
        steps: [],
        explanation: dom.explanationInput.value.trim() || null,
      },
    });
    dom.answerInput.value = "";
    dom.explanationInput.value = "";
    applyChallengeState(payload);
    renderCoachOutput(payload);
    showToast("遭遇已提交，宇宙状态已更新");
  } finally {
    dom.submitBtn.disabled = false;
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    method: options.method || "GET",
    headers: options.body ? { "Content-Type": "application/json" } : undefined,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.detail?.message || payload.message || "请求失败";
    throw new Error(message);
  }
  return payload;
}

function applyChallengeState(payload) {
  state.lastPayload = payload;
  const challenge = payload.challenge || {};
  state.currentTaskId = challenge.current_task?.task_id || null;
  dom.currentTaskBadge.textContent = state.currentTaskId
    ? `当前任务：${titleForNode(state.currentTaskId)}`
    : "当前没有任务";

  for (const object of state.objects) {
    const status = statusForObject(challenge, object);
    object.status = object.id === state.currentTaskId ? "active" : status;
    object.isCurrent = object.id === state.currentTaskId;
    applyVisualState(object);
  }
  if (!state.hasFramedInitialTask && state.currentTaskId) {
    const object = state.objectById.get(state.currentTaskId);
    if (object) {
      flyToObject(object);
      state.nearest = object;
      state.hasFramedInitialTask = true;
    }
  }
  updateNearestPanel();
  if (!dom.encounterPod.classList.contains("is-hidden")) renderEncounterPod();
}

function statusForObject(challenge, object) {
  const progress =
    challenge.micro_nodes?.[object.id]
    || challenge.macro_nodes?.[object.id]
    || challenge.macro_challenges?.[object.id];
  if (progress?.status) return progress.status;
  if (object.kind === "compare" || object.kind === "guide") return "available";
  return "available";
}

function applyVisualState(object) {
  const palette = visualPalette(object.status, object.kind, object.color);
  for (const material of object.materials) {
    if (material.userData.preserveSurfaceColor) {
      if ("emissiveIntensity" in material) {
        const baseIntensity = material.userData.surfaceEmissiveIntensity || 0;
        material.emissiveIntensity = object.isCurrent ? baseIntensity * 1.35 : baseIntensity;
      }
      continue;
    }
    if (material.color && material.userData.statusAccent) material.color.setHex(palette.color);
    if (material.color && !material.userData.statusAccent && !material.userData.fixedRealisticColor) {
      material.color.setHex(palette.color);
    }
    if (material.emissive) material.emissive.setHex(palette.emissive);
    if ("emissiveIntensity" in material) material.emissiveIntensity = palette.intensity;
  }
  object.markerMaterial.opacity = object.isCurrent ? 0.18 : 0;
}

function visualPalette(status, kind, fallbackColor) {
  if (status === "active") return { color: 0x6bd7f4, emissive: 0x46c1dc, intensity: 0.24 };
  if (status === "mastered") return { color: 0x72e0b8, emissive: 0x72e0b8, intensity: 0.32 };
  if (status === "locked") return { color: 0x5a6574, emissive: 0x18202c, intensity: 0.06 };
  if (status === "failed") return { color: 0xff7f96, emissive: 0xff335c, intensity: 0.46 };
  if (kind === "boss") return { color: 0xb99cff, emissive: 0xb99cff, intensity: 0.38 };
  return { color: fallbackColor || 0x76e4ff, emissive: fallbackColor || 0x76e4ff, intensity: 0.22 };
}

function animate() {
  const delta = Math.min(state.clock.getDelta(), 0.05);
  updateFlight(delta);
  updateCosmicMotion(delta);
  updateObjectMotion(delta);
  updateNearestObject();
  if (state.composer) state.composer.render(delta);
  else state.renderer.render(state.scene, state.camera);
  requestAnimationFrame(animate);
}

function updateCosmicMotion(delta) {
  const time = performance.now() * 0.001;
  for (const layer of state.nebulaSprites) {
    layer.sprite.position.y = layer.baseY + Math.sin(time * layer.driftSpeed + layer.phase) * layer.driftAmount;
    layer.material.opacity = Math.max(
      0.02,
      layer.baseOpacity + Math.sin(time * layer.pulseSpeed + layer.phase) * layer.pulseAmount,
    );
    if ("rotation" in layer.material) layer.material.rotation += delta * layer.rotationSpeed;
  }
}

function updateFlight(delta) {
  if (!state.camera || !state.velocity) return;
  if (!dom.encounterPod.classList.contains("is-hidden")) {
    state.velocity.multiplyScalar(0.82);
    return;
  }

  const THREE = state.THREE;
  const forward = new THREE.Vector3();
  state.camera.getWorldDirection(forward);
  forward.y = 0;
  if (forward.lengthSq() > 0) forward.normalize();
  const right = new THREE.Vector3().crossVectors(forward, state.camera.up).normalize();
  const target = new THREE.Vector3();

  if (state.keys.has("KeyW")) target.add(forward);
  if (state.keys.has("KeyS")) target.sub(forward);
  if (state.keys.has("KeyD")) target.add(right);
  if (state.keys.has("KeyA")) target.sub(right);
  if (state.keys.has("Space")) target.y += 1;
  if (state.keys.has("ControlLeft") || state.keys.has("ControlRight")) target.y -= 1;

  const speed = state.keys.has("ShiftLeft") || state.keys.has("ShiftRight") ? 128 : 52;
  if (target.lengthSq() > 0) target.normalize().multiplyScalar(speed);
  state.velocity.lerp(target, 0.12);
  state.camera.position.addScaledVector(state.velocity, delta);
}

function updateObjectMotion(delta) {
  const time = performance.now() * 0.001;
  for (const object of state.objects) {
    object.group.rotation.y += delta * (object.kind === "boss" ? 0.35 : 0.09);
    const pulse = object.isCurrent ? 1 + Math.sin(time * 3.2) * 0.055 : 1;
    const nearestPulse = state.nearest?.id === object.id ? 1.08 : 1;
    object.group.scale.setScalar(object.baseScale * pulse * nearestPulse);
  }
  for (const line of state.lines) {
    const baseOpacity = line.material.userData.baseOpacity ?? line.material.opacity;
    line.material.opacity = Math.max(0.04, baseOpacity + Math.sin(time * 0.85) * baseOpacity * 0.16);
  }
}

function updateNearestObject() {
  const cameraPosition = state.camera.position;
  let nearest = null;
  let currentCandidate = null;
  let nearestRatio = Infinity;

  for (const object of state.objects) {
    const distance = cameraPosition.distanceTo(object.group.position);
    const ratio = distance / object.interactionRadius;
    if (object.id === state.currentTaskId && ratio < 1.18) currentCandidate = object;
    if (ratio < 1 && ratio < nearestRatio) {
      nearest = object;
      nearestRatio = ratio;
    }
  }

  if (currentCandidate) nearest = currentCandidate;
  if (nearest?.id !== state.nearest?.id) {
    state.nearest = nearest;
    updateNearestPanel();
  }
}

function updateNearestPanel() {
  const nearest = state.nearest;
  if (!nearest) {
    dom.nearestTitle.textContent = "深空巡航中";
    dom.nearestMeta.textContent = "靠近知识星体、卫星或星门后，这里会显示可交互目标。";
    dom.nearestBadge.textContent = "未接近知识体";
    dom.engageBtn.disabled = true;
    return;
  }
  const current = nearest.id === state.currentTaskId;
  dom.nearestTitle.textContent = nearest.title;
  dom.nearestMeta.textContent = `${nearest.role} · ${statusLabels[nearest.status] || nearest.status} · ${nearest.summary}`;
  dom.nearestBadge.textContent = current ? "已接近当前任务" : `接近：${nearest.title}`;
  dom.engageBtn.disabled = false;
}

function openEncounter() {
  if (!state.nearest) {
    showToast("先飞近一个知识对象。");
    return;
  }
  state.activeObject = state.nearest;
  document.exitPointerLock?.();
  dom.encounterPod.classList.remove("is-hidden");
  renderEncounterPod();
}

function closeEncounter() {
  dom.encounterPod.classList.add("is-hidden");
  state.activeObject = null;
}

function renderEncounterPod() {
  const object = state.activeObject || state.nearest;
  const challenge = state.lastPayload?.challenge || {};
  const question = challenge.current_question || null;
  const taskId = challenge.current_task?.task_id || state.currentTaskId;
  const isCurrent = object?.id === taskId;

  dom.podTitle.textContent = object ? object.title : "知识遭遇";
  dom.podMeta.textContent = object
    ? `${object.role} · ${statusLabels[object.status] || object.status}`
    : "当前没有锁定知识对象。";

  if (!object) {
    dom.taskBrief.textContent = "靠近一个知识对象后再进入遭遇。";
    setFormEnabled(false);
    return;
  }

  if (!isCurrent) {
    dom.taskBrief.innerHTML = `
      <h3>观察对象</h3>
      <p>${escapeHtml(object.summary)}</p>
      <p>当前后端训练目标是 <strong>${escapeHtml(titleForNode(taskId))}</strong>。你可以观察这里，但提交训练必须回到当前任务节点。</p>
    `;
    setFormEnabled(false);
    return;
  }

  dom.taskBrief.innerHTML = `
    <h3>${escapeHtml(question?.title || titleForNode(taskId))}</h3>
    <p>${escapeHtml(question?.stem || "当前任务需要你给出判断和关键理由。")}</p>
    <p>${escapeHtml(question?.prompt_markdown || "")}</p>
  `;
  setFormEnabled(true);
}

function renderCoachOutput(payload) {
  const attempt = payload.challenge_attempt || {};
  const challenge = payload.challenge || {};
  const repairTarget =
    attempt.repair_target_node_id
    || payload.repair_target_node_id
    || challenge.current_task?.task_id
    || state.currentTaskId;
  const feedback =
    payload.coach_summary
    || payload.progression_advice
    || payload.learner_explanation
    || "系统已根据本次回答更新训练状态。";
  dom.coachOutput.innerHTML = `
    <h3>诊断回波</h3>
    <p>${escapeHtml(feedback)}</p>
    <p>修复方向：<strong>${escapeHtml(titleForNode(repairTarget))}</strong></p>
  `;
  if (repairTarget) emphasizeRepairTarget(repairTarget);
}

function emphasizeRepairTarget(nodeId) {
  const object = state.objectById.get(nodeId);
  if (!object) return;
  object.markerMaterial.opacity = 0.1;
  flyToObject(object);
}

function setFormEnabled(enabled) {
  dom.answerForm.setAttribute("aria-disabled", enabled ? "false" : "true");
  dom.answerInput.disabled = !enabled;
  dom.explanationInput.disabled = !enabled;
  dom.submitBtn.disabled = !enabled;
}

function focusCurrentTask() {
  const object = state.objectById.get(state.currentTaskId);
  if (!object) {
    showToast("当前任务还没有可定位对象。");
    return;
  }
  flyToObject(object);
  showToast(`已跃迁到 ${object.title}`);
}

function flyToObject(object) {
  const THREE = state.THREE;
  const isMacro = object.kind === "macro";
  const approachDistance = isMacro
    ? object.radius * 3.35
    : Math.max(object.radius * 4.8, Math.min(object.interactionRadius * 0.86, 150));
  const approachHeight = Math.max(14, Math.min(object.radius * (isMacro ? 0.82 : 2.2), object.interactionRadius * 0.46));
  const sideOffset = object.kind === "micro" ? object.radius * 1.9 : object.radius * 1.4;
  const offset = new THREE.Vector3(sideOffset, approachHeight, approachDistance);
  const destination = object.group.position.clone().add(offset);
  state.camera.position.copy(destination);
  state.camera.lookAt(object.group.position);
  state.camera.rotation.order = "YXZ";
  state.yaw = state.camera.rotation.y;
  state.pitch = state.camera.rotation.x;
  state.velocity.set(0, 0, 0);
}

function wireDom() {
  dom.canvas.addEventListener("click", () => {
    if (dom.encounterPod.classList.contains("is-hidden")) dom.canvas.requestPointerLock?.();
  });
  document.addEventListener("pointerlockchange", () => {
    state.pointerLocked = document.pointerLockElement === dom.canvas;
    dom.flightHint.textContent = state.pointerLocked
      ? "WASD 飞行，Space/Ctrl 升降，Shift 加速，E 进入遭遇，Esc 释放视角。"
      : "点击宇宙开始自由飞行，靠近星体后按 E 进入遭遇。";
  });
  document.addEventListener("mousemove", handleMouseMove);
  document.addEventListener("keydown", handleKeyDown);
  document.addEventListener("keyup", handleKeyUp);

  dom.syncBtn.addEventListener("click", () => loadStatus().catch((error) => showToast(error.message)));
  dom.resetBtn.addEventListener("click", () => resetChallenge().catch((error) => showToast(error.message)));
  dom.focusCurrentBtn.addEventListener("click", focusCurrentTask);
  dom.engageBtn.addEventListener("click", openEncounter);
  dom.closePodBtn.addEventListener("click", closeEncounter);
  dom.answerForm.addEventListener("submit", submitAnswer);

  for (const button of document.querySelectorAll("[data-key]")) {
    const key = button.getAttribute("data-key");
    button.addEventListener("pointerdown", () => state.keys.add(key));
    button.addEventListener("pointerup", () => state.keys.delete(key));
    button.addEventListener("pointercancel", () => state.keys.delete(key));
    button.addEventListener("pointerleave", () => state.keys.delete(key));
  }
}

function handleMouseMove(event) {
  if (!state.pointerLocked || !dom.encounterPod.classList.contains("is-hidden")) return;
  state.yaw -= event.movementX * 0.002;
  state.pitch -= event.movementY * 0.002;
  state.pitch = clamp(state.pitch, -1.28, 1.28);
  state.camera.rotation.y = state.yaw;
  state.camera.rotation.x = state.pitch;
}

function handleKeyDown(event) {
  if (isTypingTarget(event.target)) return;
  if (event.code === "KeyE") {
    openEncounter();
    return;
  }
  if (event.code === "Escape" && !dom.encounterPod.classList.contains("is-hidden")) {
    closeEncounter();
    return;
  }
  state.keys.add(event.code);
}

function handleKeyUp(event) {
  state.keys.delete(event.code);
}

function isTypingTarget(target) {
  return ["TEXTAREA", "INPUT", "SELECT"].includes(target?.tagName);
}

function resizeRenderer() {
  if (!state.renderer || !state.camera) return;
  state.camera.aspect = window.innerWidth / window.innerHeight;
  state.camera.updateProjectionMatrix();
  state.renderer.setSize(window.innerWidth, window.innerHeight);
  state.composer?.setSize(window.innerWidth, window.innerHeight);
  state.bloomPass?.setSize(window.innerWidth, window.innerHeight);
}

function cacheDom() {
  dom.canvas = document.querySelector("#spaceCanvas");
  dom.loadingOverlay = document.querySelector("#loadingOverlay");
  dom.fallbackPanel = document.querySelector("#fallbackPanel");
  dom.fallbackReason = document.querySelector("#fallbackReason");
  dom.flightHint = document.querySelector("#flightHint");
  dom.sessionBadge = document.querySelector("#sessionBadge");
  dom.currentTaskBadge = document.querySelector("#currentTaskBadge");
  dom.nearestBadge = document.querySelector("#nearestBadge");
  dom.nearestTitle = document.querySelector("#nearestTitle");
  dom.nearestMeta = document.querySelector("#nearestMeta");
  dom.engageBtn = document.querySelector("#engageBtn");
  dom.encounterPod = document.querySelector("#encounterPod");
  dom.closePodBtn = document.querySelector("#closePodBtn");
  dom.podTitle = document.querySelector("#podTitle");
  dom.podMeta = document.querySelector("#podMeta");
  dom.taskBrief = document.querySelector("#taskBrief");
  dom.answerForm = document.querySelector("#answerForm");
  dom.answerInput = document.querySelector("#answerInput");
  dom.explanationInput = document.querySelector("#explanationInput");
  dom.submitBtn = document.querySelector("#submitBtn");
  dom.coachOutput = document.querySelector("#coachOutput");
  dom.syncBtn = document.querySelector("#syncBtn");
  dom.resetBtn = document.querySelector("#resetBtn");
  dom.focusCurrentBtn = document.querySelector("#focusCurrentBtn");
  dom.toast = document.querySelector("#toast");
}

function titleForNode(nodeId) {
  if (!nodeId) return "未知节点";
  const object = state.objectById.get(nodeId);
  if (object) return object.title;
  const macro = macroDefinitions.find((item) => item.id === nodeId);
  if (macro) return macro.title;
  const [macroId, type] = nodeId.split(".");
  const macroDef = macroDefinitions.find((item) => item.id === macroId);
  const micro = microTypes.find((item) => item.type === type);
  if (macroDef && micro) return `${macroDef.title} · ${micro.title}`;
  return nodeId;
}

function showFallback(reason) {
  hideLoading();
  const fallbackReason = dom.fallbackReason || document.querySelector("#fallbackReason");
  const fallbackPanel = dom.fallbackPanel || document.querySelector("#fallbackPanel");
  if (fallbackReason) fallbackReason.textContent = reason;
  if (fallbackPanel) fallbackPanel.classList.remove("is-hidden");
}

function hideLoading() {
  const loadingOverlay = dom.loadingOverlay || document.querySelector("#loadingOverlay");
  loadingOverlay?.classList.add("is-hidden");
}

function showToast(message) {
  dom.toast.textContent = message;
  dom.toast.classList.add("show");
  window.clearTimeout(state.toastTimer);
  state.toastTimer = window.setTimeout(() => dom.toast.classList.remove("show"), 2600);
}

function webglAvailable() {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(
      window.WebGLRenderingContext
      && (canvas.getContext("webgl") || canvas.getContext("experimental-webgl")),
    );
  } catch {
    return false;
  }
}

function makeSessionId() {
  return `space-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function colorStyle(color, multiplier, alpha = 1) {
  const adjusted = color.clone().multiplyScalar(multiplier);
  const r = Math.round(clamp(adjusted.r, 0, 1) * 255);
  const g = Math.round(clamp(adjusted.g, 0, 1) * 255);
  const b = Math.round(clamp(adjusted.b, 0, 1) * 255);
  return `rgba(${r},${g},${b},${alpha})`;
}

function drawMilkyDustBand(ctx, canvas, rng, options) {
  ctx.save();
  ctx.translate(canvas.width * 0.5, options.y);
  ctx.rotate(options.rotation);
  const warm = options.warm;
  for (let layer = 0; layer < 34; layer += 1) {
    const x = (rng() - 0.5) * options.width;
    const y = (rng() - 0.5) * options.height;
    const radiusX = options.width * (0.08 + rng() * 0.16);
    const radiusY = options.height * (0.16 + rng() * 0.55);
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, radiusX);
    const color = warm
      ? [176 + Math.floor(rng() * 44), 135 + Math.floor(rng() * 46), 92 + Math.floor(rng() * 34)]
      : [76 + Math.floor(rng() * 50), 100 + Math.floor(rng() * 64), 152 + Math.floor(rng() * 56)];
    gradient.addColorStop(0, `rgba(${color[0]},${color[1]},${color[2]},${options.alpha * (0.14 + rng() * 0.18)})`);
    gradient.addColorStop(0.48, `rgba(${color[0]},${color[1]},${color[2]},${options.alpha * (0.04 + rng() * 0.08)})`);
    gradient.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.ellipse(x, y, radiusX, radiusY, (rng() - 0.5) * 0.18, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function hashString(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function mulberry32(seed) {
  return function nextRandom() {
    let value = seed += 0x6d2b79f5;
    value = Math.imul(value ^ (value >>> 15), value | 1);
    value ^= value + Math.imul(value ^ (value >>> 7), value | 61);
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
