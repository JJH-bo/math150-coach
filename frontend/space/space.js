const apiBase = "/api/challenge/v1";
const threeModuleUrl = "three";

const macroDefinitions = [
  {
    id: "ode_separable",
    title: "可分离变量方程",
    position: [-76, 6, -136],
    color: 0x76e4ff,
    summary: "先判断变量是否真的能分到两侧，再进入积分链。",
  },
  {
    id: "ode_first_order_linear",
    title: "一阶线性方程",
    position: [4, 18, -230],
    color: 0x72e0b8,
    summary: "标准形、积分因子和乘积导数结构构成这片星域的主航道。",
  },
  {
    id: "ode_homogeneous_first_order",
    title: "一阶齐次方程",
    position: [92, -4, -324],
    color: 0xb99cff,
    summary: "通过比值结构和换元视角，把未知区域重新化为可分离航道。",
  },
];

const microTypes = [
  { type: "concept", title: "概念", color: 0x8fdcff },
  { type: "trigger", title: "题眼", color: 0xffd37c },
  { type: "method", title: "方法", color: 0x72e0b8 },
  { type: "transformation", title: "转化", color: 0x9fb5ff },
  { type: "calculation", title: "计算", color: 0xf4a7ff },
  { type: "expression", title: "表达", color: 0xff9cae },
];

const realisticBodyProfiles = [
  {
    surface: 0x6f7c84,
    shadow: 0x18232a,
    highlight: 0xc3c9c4,
    atmosphere: 0x9ebbd1,
    ring: 0xb8b0a0,
  },
  {
    surface: 0x8d7657,
    shadow: 0x231a14,
    highlight: 0xd0b991,
    atmosphere: 0xc49b6d,
    ring: 0xb49464,
  },
  {
    surface: 0x465a62,
    shadow: 0x10161a,
    highlight: 0xaab8ba,
    atmosphere: 0x7fa9bd,
    ring: 0x8c9aa0,
  },
  {
    surface: 0x716b63,
    shadow: 0x1a1715,
    highlight: 0xbdb3a3,
    atmosphere: 0x9a958e,
    ring: 0xa89a82,
  },
];

const realisticMoonProfiles = [
  {
    surface: 0x777b80,
    shadow: 0x191c20,
    highlight: 0xc6c7c2,
    atmosphere: 0x8da4b8,
    ring: 0x8fa2ad,
  },
  {
    surface: 0x5d5148,
    shadow: 0x16120f,
    highlight: 0xb29f88,
    atmosphere: 0x9e8568,
    ring: 0x9b876f,
  },
  {
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
    position: [-38, 34, -178],
    color: 0xffd37c,
  },
  {
    id: "ode.compare.linear_vs_homogeneous",
    title: "一阶线性 vs 一阶齐次",
    position: [48, 32, -272],
    color: 0xffd37c,
  },
  {
    id: "ode.compare.separable_vs_homogeneous",
    title: "可分离 vs 一阶齐次",
    position: [8, -28, -236],
    color: 0xffd37c,
  },
];

const guideDefinitions = [
  {
    id: "ode.guide.first_order_foundation",
    title: "一阶方程入口锚点",
    position: [-8, -18, -108],
    color: 0x76e4ff,
  },
  {
    id: "ode.guide.boss_readiness_gate",
    title: "Boss 验收门槛",
    position: [52, 6, -390],
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

init();

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
  scene.fog = new THREE.FogExp2(0x061022, 0.00155);

  const camera = new THREE.PerspectiveCamera(72, window.innerWidth / window.innerHeight, 0.1, 1400);
  camera.position.set(-48, 13, -76);
  camera.rotation.order = "YXZ";
  camera.lookAt(new THREE.Vector3(-72, 6, -136));
  state.yaw = camera.rotation.y;
  state.pitch = camera.rotation.x;

  state.renderer = renderer;
  state.scene = scene;
  state.camera = camera;
  state.clock = new THREE.Clock();
  state.velocity = new THREE.Vector3();

  addCinematicLighting(THREE, scene);

  createMilkyWayBackdrop(THREE, scene);
  createRealisticStarField(THREE, scene);
  buildOdeSector(THREE, scene);

  const composer = new state.post.EffectComposer(renderer);
  composer.addPass(new state.post.RenderPass(scene, camera));
  const bloomPass = new state.post.UnrealBloomPass(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    0.44,
    0.58,
    0.23,
  );
  composer.addPass(bloomPass);
  state.composer = composer;
  state.bloomPass = bloomPass;

  window.addEventListener("resize", resizeRenderer);
}

function addCinematicLighting(THREE, scene) {
  const ambient = new THREE.AmbientLight(0x789cff, 0.1);
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

function buildOdeSector(THREE, scene) {
  const macroPositions = new Map();
  for (const macro of macroDefinitions) {
    const macroObject = createSpaceObject(THREE, {
      ...macro,
      kind: "macro",
      role: "知识星体",
      radius: 7.4,
      interactionRadius: 42,
    });
    scene.add(macroObject.group);
    registerObject(macroObject);
    macroPositions.set(macro.id, new THREE.Vector3(...macro.position));

    const satellitePositions = [];
    microTypes.forEach((micro, index) => {
      const angle = (Math.PI * 2 * index) / microTypes.length + 0.32;
      const orbit = 24 + (index % 2) * 3;
      const position = [
        macro.position[0] + Math.cos(angle) * orbit,
        macro.position[1] + Math.sin(index * 1.7) * 7,
        macro.position[2] + Math.sin(angle) * orbit,
      ];
      const object = createSpaceObject(THREE, {
        id: `${macro.id}.${micro.type}`,
        title: `${macro.title} · ${micro.title}`,
        kind: "micro",
        role: "能力卫星",
        position,
        color: micro.color,
        radius: 2.7,
        interactionRadius: 30,
        summary: `${micro.title}能力点，靠近后可进入当前训练遭遇。`,
      });
      scene.add(object.group);
      registerObject(object);
      satellitePositions.push(new THREE.Vector3(...position));
      addRoute(THREE, scene, macro.position, position, micro.color, 0.24);
      if (index > 0) addRoute(THREE, scene, satellitePositions[index - 1], position, 0x6f8ea8, 0.12);
    });

    const bossPosition = [macro.position[0] + 12, macro.position[1] + 18, macro.position[2] - 42];
    const boss = createSpaceObject(THREE, {
      id: `${macro.id}.macro_challenge`,
      title: `${macro.title} · Boss 星门`,
      kind: "boss",
      role: "综合星门",
      position: bossPosition,
      color: 0xb99cff,
      radius: 6,
      interactionRadius: 38,
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
      macroDefinitions[index].position,
      macroDefinitions[index + 1].position,
      0x76e4ff,
      0.28,
    );
  }

  for (const compare of compareDefinitions) {
    const object = createSpaceObject(THREE, {
      ...compare,
      kind: "compare",
      role: "易混双星",
      radius: 3.4,
      interactionRadius: 28,
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
      radius: 3.1,
      interactionRadius: 28,
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
  const profile = profiles[hashString(`${definition.id}-${definition.kind}`) % profiles.length];
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
    const surfaceTexture = createPlanetTexture(THREE, profile, definition.kind, definition.id);
    const material = new THREE.MeshPhysicalMaterial({
      color: 0xffffff,
      map: surfaceTexture,
      bumpMap: surfaceTexture,
      bumpScale: definition.kind === "macro" ? 0.42 : 0.22,
      emissive: profile.atmosphere,
      emissiveIntensity: 0.015,
      roughness: definition.kind === "macro" ? 0.82 : 0.9,
      metalness: 0.01,
      clearcoat: definition.kind === "macro" ? 0.08 : 0.04,
      clearcoatRoughness: 0.72,
    });
    material.userData.preserveSurfaceColor = true;
    primaryMesh = new THREE.Mesh(new THREE.SphereGeometry(definition.radius, 72, 36), material);
    primaryMesh.castShadow = true;
    primaryMesh.receiveShadow = true;
    group.add(primaryMesh);
    materials.push(material);

    const atmosphere = createAtmosphereShell(THREE, definition.radius, profile.atmosphere, definition.kind);
    group.add(atmosphere);

    const halo = createHaloSprite(THREE, definition.radius, profile.atmosphere, definition.kind);
    group.add(halo);

    if (definition.kind === "macro" || definition.kind === "compare") {
      const ringMaterial = new THREE.MeshBasicMaterial({
        color: profile.ring,
        transparent: true,
        opacity: definition.kind === "macro" ? 0.18 : 0.14,
        depthWrite: false,
        blending: THREE.AdditiveBlending,
      });
      ringMaterial.userData.statusAccent = true;
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(definition.radius * 1.44, 0.055, 12, 144),
        ringMaterial,
      );
      ring.rotation.x = Math.PI / 2.25;
      ring.rotation.z = Math.PI / 7;
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

  const pointLight = new THREE.PointLight(profile.atmosphere, definition.kind === "macro" ? 0.18 : 0.08, 64);
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
  const mid = from.clone().lerp(to, 0.5);
  mid.y += 9;
  const curve = new THREE.QuadraticBezierCurve3(from.clone(), mid, to.clone());
  const geometry = new THREE.TubeGeometry(curve, 56, 0.11, 8, false);
  const material = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: opacity * 0.66,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  material.userData.baseOpacity = opacity * 0.66;
  const tube = new THREE.Mesh(geometry, material);
  scene.add(tube);
  state.lines.push(tube);

  const haloGeometry = new THREE.TubeGeometry(curve, 40, 0.38, 8, false);
  const haloMaterial = new THREE.MeshBasicMaterial({
    color,
    transparent: true,
    opacity: opacity * 0.16,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  haloMaterial.userData.baseOpacity = opacity * 0.16;
  const halo = new THREE.Mesh(haloGeometry, haloMaterial);
  scene.add(halo);
  state.lines.push(halo);
}

function createRealisticStarField(THREE, scene) {
  addStarLayer(THREE, scene, {
    count: 5200,
    minRadius: 360,
    maxRadius: 980,
    size: 0.82,
    opacity: 0.72,
    palette: [0xf5f7ff, 0xd9e5ff, 0xfff2d2],
  });
  addStarLayer(THREE, scene, {
    count: 1100,
    minRadius: 250,
    maxRadius: 760,
    size: 1.15,
    opacity: 0.34,
    palette: [0xffffff, 0xd7e7ff, 0xffe3b3],
  });
  addStarLayer(THREE, scene, {
    count: 260,
    minRadius: 480,
    maxRadius: 1100,
    size: 1.7,
    opacity: 0.22,
    palette: [0xffffff, 0xe6efff],
  });
}

function createMilkyWayBackdrop(THREE, scene) {
  const material = new THREE.SpriteMaterial({
    map: createMilkyWayTexture(THREE),
    color: 0xffffff,
    transparent: true,
    opacity: 0.22,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  });
  const sprite = new THREE.Sprite(material);
  sprite.position.set(-40, 28, -520);
  sprite.scale.set(900, 240, 1);
  sprite.rotation.z = -0.18;
  scene.add(sprite);

  addStarLayer(THREE, scene, {
    count: 1500,
    minRadius: 180,
    maxRadius: 620,
    size: 0.72,
    opacity: 0.2,
    palette: [0xc7d2dd, 0xd8d4c8],
    banded: true,
  });
}

function addStarLayer(THREE, scene, options) {
  const {
    count,
    minRadius,
    maxRadius,
    size,
    opacity,
    palette,
    banded = false,
  } = options;
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  for (let index = 0; index < count; index += 1) {
    const radius = minRadius + Math.random() * (maxRadius - minRadius);
    const theta = Math.random() * Math.PI * 2;
    const phi = banded
      ? (Math.PI / 2) + (Math.random() - 0.5) * 0.32
      : Math.acos(2 * Math.random() - 1);
    positions[index * 3] = radius * Math.sin(phi) * Math.cos(theta);
    positions[index * 3 + 1] = radius * Math.cos(phi) * (banded ? 0.26 : 0.72);
    positions[index * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta) - 220;

    const starColor = new THREE.Color(palette[index % palette.length]);
    const brightness = 0.74 + Math.random() * 0.26;
    colors[index * 3] = starColor.r * brightness;
    colors[index * 3 + 1] = starColor.g * brightness;
    colors[index * 3 + 2] = starColor.b * brightness;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const material = new THREE.PointsMaterial({
    size,
    map: createStarTexture(THREE),
    transparent: true,
    opacity,
    depthWrite: false,
    alphaTest: 0.04,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true,
    vertexColors: true,
  });
  scene.add(new THREE.Points(geometry, material));
}

function createStarTexture(THREE) {
  if (state.starTexture) return state.starTexture;
  const canvas = document.createElement("canvas");
  canvas.width = 64;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  const gradient = ctx.createRadialGradient(32, 32, 0, 32, 32, 32);
  gradient.addColorStop(0, "rgba(255,255,255,1)");
  gradient.addColorStop(0.16, "rgba(255,255,255,0.82)");
  gradient.addColorStop(0.44, "rgba(255,255,255,0.16)");
  gradient.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 64, 64);
  state.starTexture = new THREE.CanvasTexture(canvas);
  state.starTexture.colorSpace = THREE.SRGBColorSpace;
  return state.starTexture;
}

function createMilkyWayTexture(THREE) {
  if (state.milkyWayTexture) return state.milkyWayTexture;
  const canvas = document.createElement("canvas");
  canvas.width = 1024;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  const rng = mulberry32(187293);

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let band = 0; band < 9; band += 1) {
    const y = canvas.height * (0.48 + (rng() - 0.5) * 0.18);
    const height = 20 + rng() * 54;
    const gradient = ctx.createLinearGradient(0, y - height, 0, y + height);
    gradient.addColorStop(0, "rgba(0,0,0,0)");
    gradient.addColorStop(0.44, `rgba(172,185,198,${0.025 + rng() * 0.04})`);
    gradient.addColorStop(0.5, `rgba(230,226,210,${0.03 + rng() * 0.05})`);
    gradient.addColorStop(0.56, `rgba(148,170,194,${0.02 + rng() * 0.035})`);
    gradient.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = gradient;
    ctx.beginPath();
    ctx.ellipse(canvas.width * 0.5, y, canvas.width * (0.42 + rng() * 0.16), height, (rng() - 0.5) * 0.06, 0, Math.PI * 2);
    ctx.fill();
  }

  for (let index = 0; index < 2200; index += 1) {
    const x = rng() * canvas.width;
    const y = canvas.height * (0.5 + (rng() - 0.5) * 0.42);
    const alpha = 0.02 + rng() * 0.12;
    const radius = 0.25 + rng() * 0.9;
    ctx.fillStyle = `rgba(230,235,240,${alpha})`;
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
  }

  state.milkyWayTexture = new THREE.CanvasTexture(canvas);
  state.milkyWayTexture.colorSpace = THREE.SRGBColorSpace;
  return state.milkyWayTexture;
}

function createPlanetTexture(THREE, profile, kind, seedValue) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  const base = new THREE.Color(profile.surface);
  const shadow = new THREE.Color(profile.shadow);
  const highlight = new THREE.Color(profile.highlight);
  const rng = mulberry32(hashString(`${seedValue}-${kind}`));

  const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
  gradient.addColorStop(0, colorStyle(highlight, 0.78));
  gradient.addColorStop(0.42, colorStyle(base, 0.98));
  gradient.addColorStop(1, colorStyle(shadow, 1.1));
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const bands = kind === "macro" ? 22 : 12;
  for (let index = 0; index < bands; index += 1) {
    const y = Math.floor(rng() * canvas.height);
    const height = 3 + rng() * (kind === "macro" ? 16 : 8);
    const alpha = 0.035 + rng() * 0.06;
    const bandColor = rng() > 0.48 ? highlight : shadow;
    ctx.fillStyle = colorStyle(bandColor, rng() > 0.48 ? 0.9 : 1.25, alpha);
    ctx.beginPath();
    ctx.ellipse(canvas.width * 0.5, y, canvas.width * (0.34 + rng() * 0.5), height, rng() * 0.12, 0, Math.PI * 2);
    ctx.fill();
  }

  for (let index = 0; index < 1800; index += 1) {
    const x = rng() * canvas.width;
    const y = rng() * canvas.height;
    const radius = rng() * (kind === "macro" ? 1.7 : 1.05);
    const noiseColor = rng() > 0.55 ? highlight : shadow;
    const alpha = 0.018 + rng() * 0.06;
    ctx.fillStyle = colorStyle(noiseColor, 0.8 + rng() * 0.35, alpha);
    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fill();
  }

  if (kind !== "macro") {
    for (let index = 0; index < 34; index += 1) {
      const x = rng() * canvas.width;
      const y = rng() * canvas.height;
      const radius = 1.4 + rng() * 5.6;
      ctx.strokeStyle = colorStyle(shadow, 1.28, 0.08 + rng() * 0.08);
      ctx.lineWidth = 0.5 + rng() * 0.8;
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, Math.PI * 2);
      ctx.stroke();
      ctx.fillStyle = colorStyle(shadow, 1.05, 0.035);
      ctx.beginPath();
      ctx.arc(x - radius * 0.18, y + radius * 0.18, radius * 0.7, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  const vignette = ctx.createRadialGradient(256, 128, 20, 256, 128, 260);
  vignette.addColorStop(0, "rgba(255,255,255,0.055)");
  vignette.addColorStop(0.64, "rgba(255,255,255,0)");
  vignette.addColorStop(1, "rgba(0,0,0,0.52)");
  ctx.fillStyle = vignette;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  texture.anisotropy = 8;
  return texture;
}

function createAtmosphereShell(THREE, radius, color, kind) {
  const atmosphere = new THREE.Mesh(
    new THREE.SphereGeometry(radius * (kind === "macro" ? 1.075 : 1.13), 72, 36),
    new THREE.ShaderMaterial({
      uniforms: {
        glowColor: { value: new THREE.Color(color) },
        intensity: { value: kind === "macro" ? 0.34 : 0.22 },
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
    opacity: kind === "macro" ? 0.055 : 0.026,
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
      if (material.emissive) material.emissive.setHex(palette.emissive);
      if ("emissiveIntensity" in material) material.emissiveIntensity = object.isCurrent ? 0.055 : 0.012;
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
  updateObjectMotion(delta);
  updateNearestObject();
  if (state.composer) state.composer.render(delta);
  else state.renderer.render(state.scene, state.camera);
  requestAnimationFrame(animate);
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

  const speed = state.keys.has("ShiftLeft") || state.keys.has("ShiftRight") ? 72 : 34;
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
  let nearestRatio = Infinity;

  for (const object of state.objects) {
    const distance = cameraPosition.distanceTo(object.group.position);
    const ratio = distance / object.interactionRadius;
    if (ratio < 1 && ratio < nearestRatio) {
      nearest = object;
      nearestRatio = ratio;
    }
  }

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
  const approachDistance = Math.max(object.radius * 4.8, Math.min(object.interactionRadius * 0.86, 42));
  const approachHeight = Math.max(7, Math.min(object.radius * 2, object.interactionRadius * 0.42));
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
  dom.fallbackReason.textContent = reason;
  dom.fallbackPanel.classList.remove("is-hidden");
}

function hideLoading() {
  dom.loadingOverlay.classList.add("is-hidden");
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
