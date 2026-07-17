import { buildCosmosGraph, deriveNextDestinations } from "./cosmos-graph.js?v=20260714-directional-abyss-1";
import {
  buildCombinedTransitControlPoints,
  buildGuidedTransitWaypoints,
  buildRapidTransitControlPoints,
  isRapidTransitEdge,
} from "./transit-route.js?v=20260713-depth-route-3";
import {
  applyCelestialStatus,
  createAuxiliaryStar,
  createCelestialNode,
  createKnowledgeSingularity,
  createRepairSingularity,
  detectQualityLevel,
  updateCelestialObject,
} from "./singularity-renderer.js?v=20260713-depth-layout-8";
import {
  createKnowledgeStar,
  createStellarSystemEnvironment,
  isStellarMaterialPilotNode,
} from "./stellar-renderer.js?v=20260714-directional-abyss-1";
import {
  createBossBlackHole,
  updateBossBlackHole,
} from "./black-hole-renderer.js?v=20260714-directional-abyss-1";

const apiBase = "/api/challenge/v1";
const threeModuleUrl = "three";
const BOSS_SCALE = 1.6;
const PORTAL_APPROACH_DIRECTION = Object.freeze([0, 0, 1]);
const MOVEMENT_KEYS = new Set([
  "KeyW", "KeyA", "KeyS", "KeyD", "Space", "ControlLeft", "ControlRight", "ShiftLeft", "ShiftRight",
]);
const dom = {};

const state = {
  THREE: null,
  renderer: null,
  composer: null,
  bloomPass: null,
  scene: null,
  camera: null,
  clock: null,
  velocity: null,
  keys: new Set(),
  objects: [],
  objectById: new Map(),
  routes: [],
  systemEnvironment: null,
  graph: null,
  nearest: null,
  activeObject: null,
  currentTaskId: null,
  navigationTargetId: null,
  lastPayload: null,
  started: false,
  experienceMode: "flight",
  flightMode: "guided",
  qualityLevel: "balanced",
  yaw: 0,
  pitch: -0.08,
  pointerLocked: false,
  touchLook: null,
  hasFramedInitialTask: false,
  flightTween: null,
  renderedTaskId: null,
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
  localStorage.setItem("math150-space-session-id", state.sessionId);

  if (!webglAvailable()) {
    showFallback("当前浏览器无法建立 WebGL 环境。可以先返回二维训练器继续学习。");
    return;
  }

  const THREE = await loadThree();
  if (!THREE) return;
  state.qualityLevel = detectQualityLevel();
  createKnowledgeUniverse(THREE);
  await bootChallengeState();
  hideLoading();
  animate();
}

async function loadThree() {
  try {
    const THREE = await import(threeModuleUrl);
    state.THREE = THREE;
    const [{ EffectComposer }, { RenderPass }, { UnrealBloomPass }] = await Promise.all([
      import("three/addons/postprocessing/EffectComposer.js"),
      import("three/addons/postprocessing/RenderPass.js"),
      import("three/addons/postprocessing/UnrealBloomPass.js"),
    ]);
    state.post = { EffectComposer, RenderPass, UnrealBloomPass };
    return THREE;
  } catch (error) {
    showFallback("Three.js 没有加载成功。请检查网络后刷新，或返回二维训练器。");
    return null;
  }
}

function createKnowledgeUniverse(THREE) {
  const renderer = new THREE.WebGLRenderer({
    canvas: dom.canvas,
    antialias: true,
    alpha: false,
    powerPreference: "high-performance",
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, state.qualityLevel === "high" ? 1.8 : 1.35));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 0.88;
  if ("outputColorSpace" in renderer) renderer.outputColorSpace = THREE.SRGBColorSpace;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x010306);
  scene.fog = new THREE.FogExp2(0x02070d, 0.00012);

  const camera = new THREE.PerspectiveCamera(68, window.innerWidth / window.innerHeight, 0.1, 12000);
  camera.position.set(-180, 58, 120);
  camera.rotation.order = "YXZ";
  camera.lookAt(new THREE.Vector3(-280, 0, -520));

  state.renderer = renderer;
  state.scene = scene;
  state.camera = camera;
  state.clock = new THREE.Clock();
  state.velocity = new THREE.Vector3();
  state.yaw = camera.rotation.y;
  state.pitch = camera.rotation.x;

  addCinematicLighting(THREE, scene);
  createWorldLockedSky(THREE, scene);
  createSolarLightSource(THREE, scene);

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
  scene.add(new THREE.AmbientLight(0x6e8fa8, 0.12));
  const hemisphere = new THREE.HemisphereLight(0x8dcde0, 0x010204, 0.28);
  scene.add(hemisphere);
  const key = new THREE.DirectionalLight(0xeaf8ff, 1.1);
  key.position.set(-300, 420, 180);
  scene.add(key);
  const warmRim = new THREE.DirectionalLight(0xa24c2c, 0.34);
  warmRim.position.set(600, -120, -1300);
  scene.add(warmRim);
}

function createWorldLockedSky(THREE, scene) {
  scene.background = createDeepSpaceTexture(THREE);
  const loader = new THREE.TextureLoader();
  loader.load(
    "/trainer/space/assets/milky-way-eso-6000.jpg",
    (texture) => {
      texture.mapping = THREE.EquirectangularReflectionMapping;
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.magFilter = THREE.LinearFilter;
      texture.minFilter = THREE.LinearMipmapLinearFilter;
      scene.background = texture;
      scene.backgroundIntensity = 0.62;
      scene.backgroundRotation.set(-0.16, 0, -0.14);
    },
    undefined,
    () => showToast("高分辨率星空未加载，已启用本地深空背景。"),
  );
}

function createDeepSpaceTexture(THREE) {
  const canvas = document.createElement("canvas");
  canvas.width = 2048;
  canvas.height = 1024;
  const ctx = canvas.getContext("2d");
  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gradient.addColorStop(0, "#010205");
  gradient.addColorStop(0.48, "#07101b");
  gradient.addColorStop(1, "#010205");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  const rng = seededRandom(9137);
  for (let index = 0; index < 3400; index += 1) {
    const x = rng() * canvas.width;
    const y = rng() * canvas.height;
    const size = rng() > 0.985 ? 1.6 : rng() > 0.88 ? 0.8 : 0.42;
    const warmth = rng();
    ctx.fillStyle = warmth > 0.93
      ? `rgba(255,224,186,${0.32 + rng() * 0.5})`
      : `rgba(${190 + Math.floor(rng() * 65)},${210 + Math.floor(rng() * 45)},255,${0.2 + rng() * 0.62})`;
    ctx.fillRect(x, y, size, size);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.mapping = THREE.EquirectangularReflectionMapping;
  texture.colorSpace = THREE.SRGBColorSpace;
  return texture;
}

function createSolarLightSource(THREE, scene) {
  const light = new THREE.DirectionalLight(0xffe2b0, 0.82);
  light.position.set(-900, 260, -1100);
  scene.add(light);
}

function createRenderedKnowledgeObject(definition) {
  if (definition.role === "boss") {
    return createBossBlackHole(state.THREE, definition, state.qualityLevel);
  }
  if (isStellarMaterialPilotNode(definition)) {
    return createKnowledgeStar(state.THREE, definition, state.qualityLevel);
  }
  return createCelestialNode(state.THREE, definition, state.qualityLevel);
}

function rebuildKnowledgeUniverse(challenge) {
  clearKnowledgeUniverse();
  state.graph = buildCosmosGraph(challenge);
  state.currentTaskId = state.graph.currentTaskId;
  dom.universeTitle.textContent = state.graph.title || "知识宇宙";

  state.graph.objects.forEach((definition) => {
    const node = createRenderedKnowledgeObject(definition);
    state.scene.add(node.group);
    state.objects.push(node);
    state.objectById.set(node.id, node);
    applyCelestialStatus(state.THREE, node, definition.status, definition.id === state.currentTaskId);
  });
  if (state.graph.presentationMode === "stellar-system-pilot") {
    state.systemEnvironment = createStellarSystemEnvironment(
      state.THREE,
      state.graph.objects,
      state.qualityLevel,
    );
    state.scene.add(state.systemEnvironment);
  }
  if (state.navigationTargetId && !state.objectById.has(state.navigationTargetId)) {
    state.navigationTargetId = null;
  }

  state.graph.edges.forEach((edge) => addSemanticRoute(edge));
  updateRouteVisibility();
  updateMissionHud();

  if (!state.hasFramedInitialTask && state.currentTaskId) {
    const requestedFocusId = new URLSearchParams(window.location.search).get("focus");
    const current = state.objectById.get(requestedFocusId) || state.objectById.get(state.currentTaskId);
    if (current) {
      state.hasFramedInitialTask = true;
      if (requestedFocusId) flyToObject(current, { immediate: true });
      else frameLearningPathFront(current);
    }
  }
}

function clearKnowledgeUniverse() {
  disposeObject(state.systemEnvironment);
  state.objects.forEach((object) => disposeObject(object.group));
  state.routes.forEach((route) => disposeObject(route.group || route.line));
  state.objects = [];
  state.objectById = new Map();
  state.routes = [];
  state.systemEnvironment = null;
  state.nearest = null;
}

function disposeObject(group) {
  if (!group) return;
  state.scene?.remove(group);
  group.traverse((child) => {
    child.geometry?.dispose?.();
    if (Array.isArray(child.material)) child.material.forEach(disposeMaterial);
    else disposeMaterial(child.material);
  });
}

function disposeMaterial(material) {
  if (!material) return;
  ["map", "alphaMap", "bumpMap", "normalMap", "roughnessMap", "emissiveMap"].forEach((key) => {
    disposeTexture(material[key]);
  });
  Object.values(material.uniforms || {}).forEach((uniform) => disposeTexture(uniform?.value));
  material.dispose?.();
}

function disposeTexture(texture) {
  if (!texture || texture.userData?.sharedPortalTexture) return;
  texture.dispose?.();
}

function addSemanticRoute(edge) {
  const source = state.objectById.get(edge.sourceId);
  const target = state.objectById.get(edge.targetId);
  if (!source || !target) return;
  const THREE = state.THREE;
  const start = source.group.position.clone();
  const end = target.group.position.clone();
  const rapid = isRapidTransitEdge(edge, start.toArray(), end.toArray());
  let controlPoints = rapid
    ? buildRapidTransitControlPoints(start.toArray(), end.toArray(), {
      sourceRadius: source.radius,
      targetRadius: target.radius,
      seed: ((edge.id?.length || 7) % 17) / 17,
    }).map((point) => new THREE.Vector3(...point))
    : null;
  if (rapid && target.userData.blackHole) {
    controlPoints = bendFilamentTowardBlackHole(THREE, controlPoints, target, ((edge.id?.length || 7) % 17) / 17);
  }
  const curve = rapid
    ? new THREE.CatmullRomCurve3(controlPoints, false, "centripetal", 0.36)
    : createSemanticCurve(THREE, start, end);
  const color = rapid ? (target.color || 0x77dff8) : routeColor(edge.edgeType);
  const visual = rapid
    ? createRapidTransitFilament(THREE, curve, color, state.qualityLevel)
    : createSemanticLine(THREE, curve, color, edge.edgeType);

  state.scene.add(visual.group);
  state.routes.push({
    edge,
    curve,
    controlPoints,
    rapid,
    ...visual,
  });
}

function createSemanticCurve(THREE, start, end) {
  const distance = start.distanceTo(end);
  const midpoint = start.clone().lerp(end, 0.5);
  midpoint.y += Math.min(120, 18 + distance * 0.12);
  return new THREE.QuadraticBezierCurve3(start, midpoint, end);
}

function createSemanticLine(THREE, curve, color, edgeType) {
  const geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(72));
  const dashed = ["confusion", "repair", "bridge", "unlock", "prerequisite"].includes(edgeType);
  const material = dashed
    ? new THREE.LineDashedMaterial({ color, transparent: true, opacity: 0.08, dashSize: 8, gapSize: 12, depthWrite: false, toneMapped: false })
    : new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.08, depthWrite: false, toneMapped: false });
  const line = new THREE.Line(geometry, material);
  if (dashed) line.computeLineDistances();
  line.renderOrder = 1;
  return {
    group: line,
    line,
    layers: [{ material, baseOpacity: dashed ? 0.075 : 0.09, maxOpacity: 0.62 }],
    baseOpacity: dashed ? 0.075 : 0.09,
  };
}

function createRapidTransitFilament(THREE, curve, color, qualityLevel) {
  const group = new THREE.Group();
  const highQuality = qualityLevel === "high";
  const segments = highQuality ? 92 : 56;
  const coreMaterial = new THREE.LineDashedMaterial({
    color,
    transparent: true,
    opacity: 0.095,
    dashSize: 3.8,
    gapSize: 7.4,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const core = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(curve.getPoints(segments)),
    coreMaterial,
  );
  core.computeLineDistances();
  core.renderOrder = 3;
  group.add(core);

  const frames = curve.computeFrenetFrames(segments, false);
  const strandPositions = [];
  const strandCount = highQuality ? 4 : 2;
  for (let strand = 0; strand < strandCount; strand += 1) {
    const angle = (strand / strandCount) * Math.PI * 2;
    for (let index = 0; index < segments; index += 1) {
      [index, index + 1].forEach((sampleIndex) => {
        const t = sampleIndex / segments;
        const point = curve.getPointAt(t);
        const envelope = Math.sin(Math.PI * t);
        const drift = 0.72 + Math.sin(t * Math.PI * (5 + strand) + angle) * 0.34;
        const offset = envelope * drift * (1.1 + strand * 0.26);
        point.addScaledVector(frames.normals[sampleIndex], Math.cos(angle + t * 8.0) * offset);
        point.addScaledVector(frames.binormals[sampleIndex], Math.sin(angle + t * 6.4) * offset);
        strandPositions.push(point.x, point.y, point.z);
      });
    }
  }
  const strandGeometry = new THREE.BufferGeometry();
  strandGeometry.setAttribute("position", new THREE.Float32BufferAttribute(strandPositions, 3));
  const strandMaterial = new THREE.LineBasicMaterial({
    color,
    transparent: true,
    opacity: 0.036,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const strands = new THREE.LineSegments(strandGeometry, strandMaterial);
  strands.renderOrder = 3;
  group.add(strands);

  const flowPoints = [];
  for (let index = 2; index < segments; index += highQuality ? 4 : 6) {
    const point = curve.getPointAt(index / segments);
    flowPoints.push(point.x, point.y, point.z);
  }
  const flowGeometry = new THREE.BufferGeometry();
  flowGeometry.setAttribute("position", new THREE.Float32BufferAttribute(flowPoints, 3));
  const flowMaterial = new THREE.PointsMaterial({
    color,
    size: highQuality ? 1.15 : 0.9,
    sizeAttenuation: true,
    transparent: true,
    opacity: 0.12,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    toneMapped: false,
  });
  const flow = new THREE.Points(flowGeometry, flowMaterial);
  flow.renderOrder = 4;
  group.add(flow);

  return {
    group,
    line: core,
    layers: [
      { material: coreMaterial, baseOpacity: 0.095, maxOpacity: 0.34 },
      { material: strandMaterial, baseOpacity: 0.036, maxOpacity: 0.17 },
      { material: flowMaterial, baseOpacity: 0.12, maxOpacity: 0.38 },
    ],
    baseOpacity: 0.095,
  };
}

function bendFilamentTowardBlackHole(THREE, controlPoints, target, seed = 0.5) {
  if (!controlPoints || controlPoints.length < 4 || !target?.userData?.blackHole) return controlPoints;
  const bent = controlPoints.map((point) => point.clone());
  const penultimate = bent.length - 2;
  const inward = bent[penultimate].clone().sub(target.group.position).normalize();
  const tangent = new THREE.Vector3(-inward.y, inward.x, inward.z * 0.16).normalize();
  bent[penultimate].addScaledVector(tangent, target.radius * (0.16 + seed * 0.1));
  return bent;
}

function routeColor(edgeType) {
  const colors = {
    progression: 0x77dff8,
    prerequisite: 0x88aaba,
    support: 0xc8e5e9,
    bridge: 0x94a5c8,
    confusion: 0xa982b7,
    repair: 0xa85c70,
    synthesis: 0xc47a45,
    gateway: 0xb99767,
    unlock: 0x77c8a5,
  };
  return colors[edgeType] || 0x789baa;
}

function updateRouteVisibility(focusId = state.nearest?.id || state.currentTaskId) {
  state.routes.forEach((route) => {
    const edge = route.edge;
    const focusRelevant = edge.sourceId === focusId || edge.targetId === focusId;
    const navigationRelevant = state.navigationTargetId
      && (edge.sourceId === state.navigationTargetId || edge.targetId === state.navigationTargetId);
    const relevant = focusRelevant || navigationRelevant;
    const currentRelevant = edge.sourceId === state.currentTaskId || edge.targetId === state.currentTaskId;
    const targetOpacity = relevant
      ? route.rapid ? 0.19 : 0.46
      : currentRelevant && state.flightMode === "guided"
        ? route.rapid ? 0.145 : 0.28
        : state.flightMode === "guided"
          ? route.baseOpacity * (route.rapid ? 0.74 : 0.22)
          : route.baseOpacity;
    setRouteOpacity(route, targetOpacity);
    if ("dashOffset" in route.line.material) route.line.material.dashOffset = relevant ? -0.8 : 0;
  });
}

function setRouteOpacity(route, targetOpacity) {
  const intensity = targetOpacity / Math.max(route.baseOpacity, 0.001);
  route.layers.forEach((layer) => {
    layer.material.opacity = Math.min(layer.maxOpacity, layer.baseOpacity * intensity);
  });
}

async function bootChallengeState() {
  try {
    const payload = await request(`/status/${encodeURIComponent(state.sessionId)}`);
    applyChallengePayload(payload);
  } catch {
    const payload = await request("/start", {
      method: "POST",
      body: JSON.stringify({ chapter_id: "ode_network_mvp", session_id: state.sessionId }),
    });
    state.started = true;
    applyChallengePayload(payload);
  }
}

async function syncChallengeState() {
  dom.syncBtn.disabled = true;
  try {
    const payload = await request(`/status/${encodeURIComponent(state.sessionId)}`);
    applyChallengePayload(payload);
    showToast("学习状态已同步。" );
  } catch (error) {
    showToast(error.message || "同步失败。" );
  } finally {
    dom.syncBtn.disabled = false;
  }
}

function applyChallengePayload(payload) {
  state.lastPayload = payload;
  if (!payload?.challenge) throw new Error("后端没有返回可用的知识图。" );
  rebuildKnowledgeUniverse(payload.challenge);
  if (state.activeObject) state.activeObject = state.objectById.get(state.activeObject.id) || null;
}

async function request(path, options = {}) {
  const response = await fetch(`${apiBase}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail;
    throw new Error(typeof detail === "string" ? detail : detail?.message || `请求失败 (${response.status})`);
  }
  return payload;
}

function updateMissionHud() {
  const current = state.objectById.get(state.currentTaskId);
  dom.currentTaskBadge.textContent = current ? current.title : "当前没有训练任务";
  dom.routeReason.textContent = current
    ? "沿高亮快速通道深入知识链，进入奇点完成当前训练"
    : "可以切换到自由模式探索已发现知识域";
}

function animate() {
  requestAnimationFrame(animate);
  const delta = Math.min(state.clock.getDelta(), 0.05);
  const elapsed = state.clock.elapsedTime;
  updateFlight(delta);
  updateCosmicMotion(elapsed, delta);
  updateNearestObject();
  updateTransitTween();
  state.routes.forEach((route) => {
    if ("dashOffset" in route.line.material) {
      route.line.material.dashOffset -= delta * (route.rapid ? 8.5 : 1.5);
    }
  });
  state.composer.render();
}

function updateCosmicMotion(elapsed, delta) {
  state.objects.forEach((object) => {
    const focused = object.id === state.nearest?.id || object.id === state.currentTaskId;
    if (object.userData.blackHole) updateBossBlackHole(object, elapsed, delta, focused);
    else updateCelestialObject(object, elapsed, delta, focused);
  });
}

function updateFlight(delta) {
  if (state.experienceMode !== "flight") return;
  const hasManualMovement = [...MOVEMENT_KEYS].some((key) => state.keys.has(key));
  if (hasManualMovement) cancelAutopilotForManualControl();
  if (state.flightTween) return;
  const THREE = state.THREE;
  const camera = state.camera;
  const direction = new THREE.Vector3();
  const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
  const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
  const up = new THREE.Vector3(0, 1, 0);
  if (state.keys.has("KeyW")) direction.add(forward);
  if (state.keys.has("KeyS")) direction.sub(forward);
  if (state.keys.has("KeyD")) direction.add(right);
  if (state.keys.has("KeyA")) direction.sub(right);
  if (state.keys.has("Space")) direction.add(up);
  if (state.keys.has("ControlLeft") || state.keys.has("ControlRight")) direction.sub(up);
  if (direction.lengthSq() > 0) direction.normalize();

  const boost = state.keys.has("ShiftLeft") || state.keys.has("ShiftRight");
  const acceleration = boost ? 440 : 230;
  state.velocity.addScaledVector(direction, acceleration * delta);
  state.velocity.multiplyScalar(Math.exp(-2.35 * delta));
  const maxSpeed = boost ? 310 : 150;
  if (state.velocity.length() > maxSpeed) state.velocity.setLength(maxSpeed);
  camera.position.addScaledVector(state.velocity, delta);
  camera.rotation.set(state.pitch, state.yaw, 0);
}

function cancelAutopilotForManualControl() {
  if (!state.flightTween) return;
  state.flightTween = null;
  syncCameraAngles();
}

function updateNearestObject() {
  if (state.experienceMode !== "flight" || !state.camera) return;
  let nearest = null;
  let nearestRatio = Infinity;
  let currentCandidate = null;
  state.objects.forEach((object) => {
    const distance = state.camera.position.distanceTo(object.group.position);
    const ratio = distance / object.interactionRadius;
    if (object.id === state.currentTaskId && ratio < 1.4) currentCandidate = object;
    if (ratio < 1 && ratio < nearestRatio) {
      nearest = object;
      nearestRatio = ratio;
    }
  });
  if (currentCandidate) nearest = currentCandidate;
  if (nearest?.id !== state.nearest?.id) {
    state.nearest = nearest;
    renderNearestObject();
    updateRouteVisibility(nearest?.id || state.currentTaskId);
  }
}

function renderNearestObject() {
  const nearest = state.nearest;
  if (!nearest) {
    dom.nearestRole.textContent = "Deep space";
    dom.nearestStatus.textContent = "巡航";
    dom.nearestTitle.textContent = "寻找知识奇点";
    dom.nearestMeta.textContent = "锁定航线后，目标关系和学习状态会显示在这里。";
    dom.engageBtn.disabled = true;
    dom.engageBtn.textContent = "进入知识域";
    return;
  }
  const current = nearest.id === state.currentTaskId;
  dom.nearestRole.textContent = roleLabel(nearest.role);
  dom.nearestStatus.textContent = statusLabel(nearest.status);
  dom.nearestTitle.textContent = nearest.title;
  dom.nearestMeta.textContent = nearest.description;
  dom.engageBtn.disabled = nearest.status === "locked";
  dom.engageBtn.textContent = current ? "穿越并开始学习" : nearest.trainable ? "进入并观察" : "查看知识关系";
}

function enterKnowledgeDomain(object = state.nearest) {
  if (!object || state.experienceMode !== "flight") {
    if (!object) showToast("请先接近或锁定一个知识天体。" );
    return;
  }
  if (object.status === "locked") {
    showToast("这个知识奇点尚未开放。先完成它的前置航线。" );
    return;
  }
  state.activeObject = object;
  if (state.navigationTargetId === object.id) state.navigationTargetId = null;
  state.experienceMode = "transit";
  document.exitPointerLock?.();
  dom.transitOverlay.classList.remove("is-hidden");
  dom.transitOverlay.setAttribute("aria-hidden", "false");
  flyToObject(object, { approach: true });
  window.setTimeout(() => {
    dom.transitOverlay.classList.add("is-hidden");
    dom.transitOverlay.setAttribute("aria-hidden", "true");
    state.experienceMode = "interior";
    document.body.classList.add("is-learning");
    dom.learningObservatory.classList.remove("is-hidden");
    renderLearningObservatory();
  }, prefersReducedMotion() ? 80 : 920);
}

function exitKnowledgeDomain() {
  if (state.experienceMode === "flight") return;
  dom.learningObservatory.classList.add("is-hidden");
  dom.branchChoices.classList.add("is-hidden");
  document.body.classList.remove("is-learning");
  state.experienceMode = "flight";
  state.activeObject = null;
  state.nearest = null;
  renderNearestObject();
  updateRouteVisibility();
}

function renderLearningObservatory() {
  const object = state.activeObject;
  const challenge = state.lastPayload?.challenge;
  const question = challenge?.current_question || null;
  const isCurrent = object?.id === state.currentTaskId;
  const canTrain = Boolean(isCurrent && question && object?.trainable);

  dom.podRole.textContent = roleLabel(object?.role);
  dom.podTitle.textContent = object?.title || "知识内部空间";
  dom.podMeta.textContent = object?.description || "正在建立稳定观测层。";
  dom.observatoryObject.classList.toggle("is-boss", object?.role === "boss");
  dom.answerForm.setAttribute("aria-disabled", canTrain ? "false" : "true");
  dom.answerInput.disabled = !canTrain;
  dom.explanationInput.disabled = !canTrain;
  dom.submitBtn.disabled = !canTrain;
  dom.branchChoices.classList.add("is-hidden");
  dom.coachOutput.innerHTML = "";

  if (!object) {
    dom.taskBrief.innerHTML = "<p>没有锁定知识对象。</p>";
    return;
  }
  if (!isCurrent) {
    dom.taskBrief.innerHTML = `
      <p class="eyebrow">Observed knowledge</p>
      <h3>${escapeHtml(object.title)}</h3>
      <p>${escapeHtml(object.description)}</p>
      <p>当前训练目标是 <strong>${escapeHtml(titleForNode(state.currentTaskId))}</strong>。你可以观察这里，但不能绕过知识前置条件提交训练。</p>
    `;
    return;
  }
  if (state.renderedTaskId !== object.id) {
    dom.answerInput.value = "";
    dom.explanationInput.value = "";
    state.renderedTaskId = object.id;
  }
  dom.taskBrief.innerHTML = `
    <p class="eyebrow">Current problem</p>
    <h3>${escapeHtml(question?.title || object.title)}</h3>
    <p>${escapeHtml(question?.stem || "请完成当前知识节点的判断与推理。")}</p>
    <p>${escapeHtml(question?.prompt_markdown || "")}</p>
  `;
}

async function submitEncounter(event) {
  event.preventDefault();
  if (state.experienceMode !== "interior" || !state.activeObject || state.activeObject.id !== state.currentTaskId) return;
  const answer = dom.answerInput.value.trim();
  const explanation = dom.explanationInput.value.trim();
  if (!answer) {
    showToast("请先写出你的回答。" );
    return;
  }
  dom.submitBtn.disabled = true;
  const completedNodeId = state.activeObject.id;
  try {
    const payload = await request("/submit", {
      method: "POST",
      body: JSON.stringify({
        session_id: state.sessionId,
        answer,
        steps: [],
        explanation: explanation || null,
      }),
    });
    applyChallengePayload(payload);
    state.activeObject = state.objectById.get(completedNodeId) || null;
    renderCoachOutput(payload);
    const passState = payload.pass_state || payload.challenge_attempt?.pass_state;
    if (passState === "pass") {
      renderBranchChoices(completedNodeId, payload.challenge);
      dom.answerForm.setAttribute("aria-disabled", "true");
      dom.answerInput.disabled = true;
      dom.explanationInput.disabled = true;
    } else {
      emphasizeRepairTarget(
        payload.repair_target_node_id
        || payload.challenge_attempt?.repair_target_node_id
        || payload.diagnostic_insight?.primary_target_node_id,
      );
    }
  } catch (error) {
    showToast(error.message || "提交失败，答案仍保留在当前空间。" );
  } finally {
    dom.submitBtn.disabled = dom.answerInput.disabled;
  }
}

function renderCoachOutput(payload) {
  const passState = payload.pass_state || payload.challenge_attempt?.pass_state || "unknown";
  const title = passState === "pass" ? "知识结构已稳定" : "检测到不稳定环节";
  const advice = payload.progression_advice || payload.next_action_hint || payload.coach_summary || "继续完成当前训练。";
  dom.coachOutput.innerHTML = `<h3>${escapeHtml(title)}</h3><p>${escapeHtml(String(advice))}</p>`;
}

function renderBranchChoices(completedNodeId, challenge) {
  const choices = deriveNextDestinations(state.graph, completedNodeId, challenge);
  dom.branchChoiceList.innerHTML = "";
  choices.forEach((choice) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "branch-choice";
    button.disabled = choice.status === "locked";
    button.innerHTML = `
      <span><strong>${escapeHtml(choice.title)}</strong><span>${escapeHtml(choice.relation)} · ${escapeHtml(choice.description)}</span></span>
      <em>${choice.status === "locked" ? "未解锁" : choice.rapidTransit && state.flightMode === "guided" ? "快速通道" : "设为目标"}</em>
    `;
    button.addEventListener("click", () => {
      const target = state.objectById.get(choice.id);
      exitKnowledgeDomain();
      if (!target) return;
      if (state.flightMode === "guided") {
        window.setTimeout(() => flyToObject(target, { viaTunnelPath: choice.transitPath }), 120);
      } else {
        state.navigationTargetId = target.id;
        updateRouteVisibility(target.id);
        showToast(`自由航行目标已标记：${target.title}`);
      }
    });
    dom.branchChoiceList.append(button);
  });
  if (!choices.length) {
    const empty = document.createElement("p");
    empty.textContent = "当前章节没有新的开放航线，可以返回宇宙自由探索。";
    dom.branchChoiceList.append(empty);
  }
  dom.branchChoices.classList.remove("is-hidden");
}

function emphasizeRepairTarget(nodeId) {
  const target = state.objectById.get(nodeId);
  if (!target) return;
  state.routes.forEach((route) => {
    if (route.edge.sourceId === nodeId || route.edge.targetId === nodeId) setRouteOpacity(route, 0.58);
  });
  showToast(`修复航线已指向：${target.title}`);
}

function flyToObject(object, options = {}) {
  if (!object || !state.camera) return;
  const THREE = state.THREE;
  const radius = object.radius || 12;
  const tunnelRoutes = state.flightMode === "guided"
    ? findRapidTransitRoutes(options.viaTunnelPath)
    : null;
  const distance = options.approach
    ? Math.max(radius * 0.78, 5)
    : tunnelRoutes?.length
      ? object.role === "boss" ? radius * 2.8 : Math.max(radius * 4.2, 70)
    : object.role === "boss"
      ? radius * (BOSS_SCALE + 1)
      : object.role === "auxiliary"
        ? Math.max(radius * 8, 62)
        : Math.max(radius * 7.8, 104);
  const viewDirection = new THREE.Vector3(...PORTAL_APPROACH_DIRECTION);
  const destination = object.group.position.clone().addScaledVector(viewDirection, distance);
  state.velocity?.set(0, 0, 0);
  if (options.immediate || prefersReducedMotion()) {
    state.camera.position.copy(destination);
    state.camera.lookAt(object.group.position);
    syncCameraAngles();
    return;
  }
  if (tunnelRoutes?.length) {
    const controlPoints = buildCombinedTransitControlPoints(
      tunnelRoutes.map((route) => route.controlPoints.map((point) => point.toArray())),
    );
    const waypoints = buildGuidedTransitWaypoints(
      state.camera.position.toArray(),
      controlPoints,
      destination.toArray(),
    ).map((point) => new THREE.Vector3(...point));
    const path = new THREE.CatmullRomCurve3(waypoints, false, "centripetal", 0.34);
    const routeLength = tunnelRoutes.reduce((sum, route) => sum + route.curve.getLength(), 0);
    state.flightTween = {
      startedAt: performance.now(),
      duration: clamp(routeLength * 4.2, 1450, 5200),
      start: state.camera.position.clone(),
      destination,
      target: object.group.position.clone(),
      path,
    };
    showToast(`快速通道已锁定：${object.title}`);
    return;
  }
  state.flightTween = {
    startedAt: performance.now(),
    duration: options.approach ? 780 : 1050,
    start: state.camera.position.clone(),
    destination,
    target: object.group.position.clone(),
  };
}

function findRapidTransitRoutes(nodeIds) {
  if (!Array.isArray(nodeIds) || nodeIds.length < 2) return null;
  const routes = [];
  for (let index = 0; index < nodeIds.length - 1; index += 1) {
    const route = state.routes.find((candidate) => (
      candidate.rapid
      && candidate.edge.sourceId === nodeIds[index]
      && candidate.edge.targetId === nodeIds[index + 1]
    ));
    if (!route) return null;
    routes.push(route);
  }
  return routes;
}

function frameLearningPathFront(currentObject) {
  if (!state.camera || !state.graph?.frontFrame) {
    flyToObject(currentObject, { immediate: true });
    return;
  }
  const THREE = state.THREE;
  const frame = state.graph.frontFrame;
  const currentPosition = currentObject.group.position;
  const nextRoute = state.routes.find((route) => route.rapid && route.edge.sourceId === currentObject.id);
  const nextTarget = nextRoute ? state.objectById.get(nextRoute.edge.targetId)?.group.position : null;
  const isEntry = currentObject.id === frame.entryId;
  const cameraPosition = isEntry
    ? new THREE.Vector3(...frame.camera)
    : currentPosition.clone().add(new THREE.Vector3(-150, 72, 470));
  const lookAt = isEntry
    ? new THREE.Vector3(...frame.lookAt)
    : nextTarget ? currentPosition.clone().lerp(nextTarget, 0.54) : currentPosition.clone();
  state.camera.position.copy(cameraPosition);
  state.camera.lookAt(lookAt);
  state.velocity?.set(0, 0, 0);
  syncCameraAngles();
}

function updateTransitTween() {
  const tween = state.flightTween;
  if (!tween) return;
  const raw = (performance.now() - tween.startedAt) / tween.duration;
  const t = clamp(raw, 0, 1);
  const eased = 1 - Math.pow(1 - t, 3);
  if (tween.path) {
    state.camera.position.copy(tween.path.getPointAt(eased));
    const lookAhead = tween.path.getPointAt(Math.min(1, eased + 0.035));
    state.camera.lookAt(eased > 0.94 ? tween.target : lookAhead);
  } else {
    state.camera.position.lerpVectors(tween.start, tween.destination, eased);
    state.camera.lookAt(tween.target);
  }
  if (t >= 1) {
    state.flightTween = null;
    syncCameraAngles();
  }
}

function syncCameraAngles() {
  state.camera.rotation.order = "YXZ";
  state.yaw = state.camera.rotation.y;
  state.pitch = state.camera.rotation.x;
}

function setFlightMode(mode) {
  cancelAutopilotForManualControl();
  state.flightMode = mode;
  if (mode === "guided") state.navigationTargetId = null;
  dom.guidedModeBtn.classList.toggle("is-active", mode === "guided");
  dom.exploreModeBtn.classList.toggle("is-active", mode === "explore");
  dom.routeReason.textContent = mode === "guided"
    ? "前置快速通道已激活，完成训练后可直接跃迁"
    : "自由航行已激活，选择目标后由你亲自飞行";
  updateRouteVisibility();
}

function wireDom() {
  dom.canvas.addEventListener("click", () => {
    if (state.experienceMode === "flight" && matchMedia("(pointer: fine)").matches) {
      dom.canvas.requestPointerLock?.();
    }
  });
  document.addEventListener("pointerlockchange", () => {
    state.pointerLocked = document.pointerLockElement === dom.canvas;
  });
  document.addEventListener("mousemove", (event) => {
    if (!state.pointerLocked || state.experienceMode !== "flight") return;
    cancelAutopilotForManualControl();
    state.yaw -= event.movementX * 0.0018;
    state.pitch -= event.movementY * 0.0018;
    state.pitch = clamp(state.pitch, -Math.PI * 0.48, Math.PI * 0.48);
  });
  dom.canvas.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "mouse" || state.experienceMode !== "flight") return;
    state.touchLook = { pointerId: event.pointerId, x: event.clientX, y: event.clientY };
    cancelAutopilotForManualControl();
    dom.canvas.setPointerCapture?.(event.pointerId);
    event.preventDefault();
  });
  dom.canvas.addEventListener("pointermove", (event) => {
    const touchLook = state.touchLook;
    if (!touchLook || event.pointerId !== touchLook.pointerId || state.experienceMode !== "flight") return;
    state.yaw -= (event.clientX - touchLook.x) * 0.006;
    state.pitch -= (event.clientY - touchLook.y) * 0.006;
    state.pitch = clamp(state.pitch, -Math.PI * 0.48, Math.PI * 0.48);
    touchLook.x = event.clientX;
    touchLook.y = event.clientY;
    event.preventDefault();
  });
  const endTouchLook = (event) => {
    if (state.touchLook?.pointerId === event.pointerId) state.touchLook = null;
  };
  dom.canvas.addEventListener("pointerup", endTouchLook);
  dom.canvas.addEventListener("pointercancel", endTouchLook);
  window.addEventListener("keydown", (event) => {
    if (state.experienceMode === "interior") {
      if (event.code === "Escape") exitKnowledgeDomain();
      return;
    }
    if (MOVEMENT_KEYS.has(event.code)) cancelAutopilotForManualControl();
    state.keys.add(event.code);
    if (event.code === "KeyE") enterKnowledgeDomain();
  });
  window.addEventListener("keyup", (event) => state.keys.delete(event.code));
  dom.engageBtn.addEventListener("click", () => enterKnowledgeDomain());
  dom.closePodBtn.addEventListener("click", exitKnowledgeDomain);
  dom.answerForm.addEventListener("submit", submitEncounter);
  dom.syncBtn.addEventListener("click", syncChallengeState);
  dom.focusCurrentBtn.addEventListener("click", () => {
    const current = state.objectById.get(state.currentTaskId);
    if (!current) return showToast("当前任务还没有可定位对象。" );
    flyToObject(current);
  });
  dom.guidedModeBtn.addEventListener("click", () => setFlightMode("guided"));
  dom.exploreModeBtn.addEventListener("click", () => setFlightMode("explore"));
  document.querySelectorAll("[data-key]").forEach((button) => {
    const key = button.dataset.key;
    const release = () => state.keys.delete(key);
    button.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      cancelAutopilotForManualControl();
      state.keys.add(key);
    });
    button.addEventListener("pointerup", release);
    button.addEventListener("pointercancel", release);
    button.addEventListener("pointerleave", release);
  });
}

function cacheDom() {
  dom.canvas = document.querySelector("#spaceCanvas");
  dom.universeTitle = document.querySelector("#universeTitle");
  dom.loadingOverlay = document.querySelector("#loadingOverlay");
  dom.fallbackPanel = document.querySelector("#fallbackPanel");
  dom.fallbackReason = document.querySelector("#fallbackReason");
  dom.currentTaskBadge = document.querySelector("#currentTaskBadge");
  dom.routeReason = document.querySelector("#routeReason");
  dom.nearestRole = document.querySelector("#nearestRole");
  dom.nearestStatus = document.querySelector("#nearestStatus");
  dom.nearestTitle = document.querySelector("#nearestTitle");
  dom.nearestMeta = document.querySelector("#nearestMeta");
  dom.engageBtn = document.querySelector("#engageBtn");
  dom.learningObservatory = document.querySelector("#learningObservatory");
  dom.closePodBtn = document.querySelector("#closePodBtn");
  dom.podRole = document.querySelector("#podRole");
  dom.podTitle = document.querySelector("#podTitle");
  dom.podMeta = document.querySelector("#podMeta");
  dom.observatoryObject = document.querySelector("#observatoryObject");
  dom.taskBrief = document.querySelector("#taskBrief");
  dom.answerForm = document.querySelector("#answerForm");
  dom.answerInput = document.querySelector("#answerInput");
  dom.explanationInput = document.querySelector("#explanationInput");
  dom.submitBtn = document.querySelector("#submitBtn");
  dom.coachOutput = document.querySelector("#coachOutput");
  dom.branchChoices = document.querySelector("#branchChoices");
  dom.branchChoiceList = document.querySelector("#branchChoiceList");
  dom.transitOverlay = document.querySelector("#transitOverlay");
  dom.syncBtn = document.querySelector("#syncBtn");
  dom.focusCurrentBtn = document.querySelector("#focusCurrentBtn");
  dom.guidedModeBtn = document.querySelector("#guidedModeBtn");
  dom.exploreModeBtn = document.querySelector("#exploreModeBtn");
  dom.toast = document.querySelector("#toast");
}

function resizeRenderer() {
  if (!state.camera || !state.renderer) return;
  state.camera.aspect = window.innerWidth / window.innerHeight;
  state.camera.updateProjectionMatrix();
  state.renderer.setSize(window.innerWidth, window.innerHeight);
  state.composer?.setSize(window.innerWidth, window.innerHeight);
  state.bloomPass?.setSize(window.innerWidth, window.innerHeight);
}

function titleForNode(nodeId) {
  return state.objectById.get(nodeId)?.title || nodeId || "未知节点";
}

function roleLabel(role) {
  const labels = {
    domain: "Knowledge domain",
    training: "Training singularity",
    auxiliary: "Support star",
    repair: "Unstable singularity",
    boss: "Boss cataclysm",
  };
  return labels[role] || "Knowledge object";
}

function statusLabel(status) {
  const labels = { locked: "未解锁", available: "可探索", active: "当前任务", mastered: "已掌握", failed: "需要修复" };
  return labels[status] || status || "未知";
}

function showRenderFallback(error) {
  showFallback(error instanceof Error ? error.message : String(error || "未知渲染错误"));
}

function showFallback(reason) {
  hideLoading();
  dom.fallbackReason.textContent = reason;
  dom.fallbackPanel.classList.remove("is-hidden");
}

function hideLoading() { dom.loadingOverlay?.classList.add("is-hidden"); }

function showToast(message) {
  dom.toast.textContent = message;
  dom.toast.classList.add("show");
  window.clearTimeout(state.toastTimer);
  state.toastTimer = window.setTimeout(() => dom.toast.classList.remove("show"), 2800);
}

function webglAvailable() {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(window.WebGLRenderingContext && (canvas.getContext("webgl2") || canvas.getContext("webgl")));
  } catch {
    return false;
  }
}

function makeSessionId() {
  return `space-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

function seededRandom(seed) {
  let value = seed >>> 0;
  return () => {
    value = (Math.imul(value, 1664525) + 1013904223) >>> 0;
    return value / 4294967296;
  };
}

function prefersReducedMotion() { return matchMedia("(prefers-reduced-motion: reduce)").matches; }
function clamp(value, min, max) { return Math.min(max, Math.max(min, value)); }

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
