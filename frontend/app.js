const apiBase = "/api/challenge/v1";

const macroTitles = {
  ode_separable: "可分离变量方程",
  ode_first_order_linear: "一阶线性微分方程",
  ode_homogeneous_first_order: "一阶齐次方程",
};
const macroOrder = ["ode_separable", "ode_first_order_linear", "ode_homogeneous_first_order"];
const microTitles = {
  concept: "概念",
  trigger: "题眼",
  method: "方法",
  transformation: "转化",
  calculation: "计算",
  expression: "表达",
};
const statusLabels = {
  locked: "未解锁",
  available: "可挑战",
  active: "当前",
  mastered: "已点亮",
  failed: "失败",
};
const visualLabels = {
  locked: "未解锁",
  available: "可挑战",
  active: "正在训练",
  lit_unstable: "已点亮但不稳",
  stable_mastery: "稳定掌握",
  repair: "需要修复",
  failed: "挑战失败",
};
const dimensionLabels = {
  concept: "概念",
  trigger: "题眼",
  method: "方法",
  transformation: "转化",
  process: "过程",
  calculation: "计算",
  final_answer: "答案",
  expression: "表达",
  migration: "迁移",
};
const errorLabels = {
  concept_gap: "概念漏洞",
  trigger_failure: "题眼识别失败",
  method_error: "方法选择错误",
  transformation_error: "条件转化失败",
  process_gap: "过程断裂",
  calculation_error: "计算错误",
  condition_miss: "审题遗漏",
  formula_memory_error: "公式记忆不牢",
  knowledge_confusion: "知识点混淆",
  expression_weakness: "表达不严谨",
  migration_failure: "迁移失败",
  synthesis_failure: "综合拆解失败",
};

const startScreen = document.querySelector("#startScreen");
const mapWorld = document.querySelector("#mapWorld");
const mapViewport = document.querySelector("#mapViewport");
const nodeModal = document.querySelector("#nodeModal");
const mapCameraSurface = document.querySelector("#mapCameraSurface");
const closeNodePanelBtn = document.querySelector("#closeNodePanelBtn");
const sessionInput = document.querySelector("#sessionId");
const startBtn = document.querySelector("#startBtn");
const statusBtn = document.querySelector("#statusBtn");
const resetBtn = document.querySelector("#resetBtn");
const worldRefreshBtn = document.querySelector("#worldRefreshBtn");
const worldResetBtn = document.querySelector("#worldResetBtn");
const hudSession = document.querySelector("#hudSession");
const answerForm = document.querySelector("#answerForm");
const submitBtn = document.querySelector("#submitBtn");
const answerInput = document.querySelector("#answerInput");
const explanationInput = document.querySelector("#explanationInput");
const graphView = document.querySelector("#graphView");
const selectedNodeView = document.querySelector("#selectedNodeView");
const taskCard = document.querySelector("#taskCard");
const coachView = document.querySelector("#coachView");
const overallStats = document.querySelector("#overallStats");
const toast = document.querySelector("#toast");
const atlasLayer = document.querySelector("#atlasLayer");
const startAtlas = document.querySelector("#startAtlas");
const startAtlasBtn = document.querySelector("#startAtlasBtn");
const startImportBtn = document.querySelector("#startImportBtn");
const atlasModeBtn = document.querySelector("#atlasModeBtn");
const graphModeBtn = document.querySelector("#graphModeBtn");
const openImportBtn = document.querySelector("#openImportBtn");
const importModal = document.querySelector("#importModal");
const closeImportBtn = document.querySelector("#closeImportBtn");
const chapterDraftInput = document.querySelector("#chapterDraftInput");
const validateDraftBtn = document.querySelector("#validateDraftBtn");
const loadTemplateBtn = document.querySelector("#loadTemplateBtn");
const importReport = document.querySelector("#importReport");

let lastPayload = null;
let atlasPayload = null;
let selectedNodeId = null;
let currentChapterId = localStorage.getItem("math150-current-chapter-id") || "ode_network_mvp";
let panelCloseTimer = null;
const panelTransitionMs = 360;
const mapCamera = {
  zoom: 1,
  targetZoom: 1,
  minZoom: 0.54,
  maxZoom: 1.9,
  dragging: false,
  pointerActive: false,
  pointerX: 0,
  pointerY: 0,
  dragStartX: 0,
  dragStartY: 0,
  dragStartLeft: 0,
  dragStartTop: 0,
  edgePanFrame: null,
  baseWidth: 1400,
  baseHeight: 1780,
  wheelFrame: null,
  wheelDelta: 0,
  wheelX: 0,
  wheelY: 0,
  zoomFrame: null,
  zoomAnchorContentX: 0,
  zoomAnchorContentY: 0,
  zoomAnchorPointerX: 0,
  zoomAnchorPointerY: 0,
  movingTimer: null,
  spaceFrame: null,
};

init();

function init() {
  sessionInput.value = localStorage.getItem("math150-session-id") || makeSessionId();
  localStorage.setItem("math150-session-id", sessionInput.value);
  startBtn.addEventListener("click", () => startChallenge());
  statusBtn.addEventListener("click", () => loadStatus());
  resetBtn.addEventListener("click", () => resetChallenge());
  worldRefreshBtn.addEventListener("click", () => loadStatus());
  worldResetBtn.addEventListener("click", () => resetChallenge());
  startAtlasBtn?.addEventListener("click", () => {
    showMapWorld();
    showAtlasMode();
  });
  startImportBtn?.addEventListener("click", openImportPanel);
  atlasModeBtn?.addEventListener("click", showAtlasMode);
  graphModeBtn?.addEventListener("click", showGraphMode);
  openImportBtn?.addEventListener("click", openImportPanel);
  closeImportBtn?.addEventListener("click", closeImportPanel);
  loadTemplateBtn?.addEventListener("click", loadDraftTemplate);
  validateDraftBtn?.addEventListener("click", validateChapterDraft);
  closeNodePanelBtn.addEventListener("click", closeNodePanel);
  graphView.addEventListener("click", handleGraphClick);
  setupMapCamera();
  answerForm.addEventListener("submit", (event) => {
    event.preventDefault();
    submitAnswer();
  });
  window.selectMapNode = selectMapNode;
  window.startAtlasChapter = startAtlasChapter;
  loadAtlas().catch(() => {
    renderAtlasFallback();
  });
  loadStatus({ quiet: true, keepStartOnFailure: true }).catch(() => showStartScreen());
}

function setupMapCamera() {
  mapViewport.addEventListener("wheel", handleMapWheel, { passive: false });
  mapViewport.addEventListener("scroll", scheduleSpaceParallax, { passive: true });
  mapViewport.addEventListener("pointerdown", startMapDrag);
  mapViewport.addEventListener("pointermove", updateEdgePanPointer);
  mapViewport.addEventListener("pointerenter", updateEdgePanPointer);
  mapViewport.addEventListener("pointerleave", stopEdgePan);
  window.addEventListener("pointermove", moveMapDrag);
  window.addEventListener("pointerup", stopMapDrag);
  window.addEventListener("resize", () => {
    mapCamera.targetZoom = mapCamera.zoom;
    applyMapCamera();
  });
  window.addEventListener("blur", () => {
    stopMapDrag();
    stopEdgePan();
  });
  applyMapCamera();
  scheduleSpaceParallax();
}

async function loadAtlas() {
  const payload = await request("/atlas");
  atlasPayload = payload;
  renderAtlas(payload);
  return payload;
}

function renderAtlas(payload) {
  if (!payload) return;
  const regions = payload.regions || [];
  const atlasHtml = `
    <div class="atlas-copy">
      <p class="eyebrow">Course Atlas</p>
      <h2>${escapeHtml(payload.title || "课程星图")}</h2>
      <p>只加载章节摘要。点击星系后，再进入该章节的详细知识网。</p>
    </div>
    <div class="atlas-galaxy">
      ${regions.map((region) => renderAtlasRegion(region)).join("")}
    </div>
  `;
  if (atlasLayer) atlasLayer.innerHTML = atlasHtml;
  if (startAtlas) startAtlas.innerHTML = `
    <div class="atlas-mini-title">
      <span>课程星图</span>
      <strong>${regions.length} 个章节区域</strong>
    </div>
    <div class="atlas-mini-list">
      ${regions.map((region) => `
        <button type="button" class="atlas-mini-region" data-chapter-id="${escapeHtml(region.id)}" onclick="startAtlasChapter('${escapeHtml(region.id)}')">
          <strong>${escapeHtml(region.title)}</strong>
          <span>${escapeHtml(atlasRegionMeta(region))}</span>
        </button>
      `).join("")}
    </div>
  `;
}

function renderAtlasFallback() {
  const fallback = {
    title: "Math150 Coach 课程星图",
    regions: [{
      id: currentChapterId,
      title: "一阶微分方程知识网",
      position: { x: 50, y: 48 },
      summary: { macro_count: 3, micro_count: 18, boss_count: 3 },
      macro_regions: [],
    }],
  };
  atlasPayload = fallback;
  renderAtlas(fallback);
}

function renderAtlasRegion(region) {
  const x = region.position?.x ?? 50;
  const y = region.position?.y ?? 50;
  return `
    <button
      type="button"
      class="atlas-region ${region.id === currentChapterId ? "selected" : ""}"
      style="left:${x}%;top:${y}%"
      data-chapter-id="${escapeHtml(region.id)}"
      onclick="startAtlasChapter('${escapeHtml(region.id)}')"
    >
      <span class="atlas-region-core"></span>
      <span class="atlas-region-title">${escapeHtml(region.title)}</span>
      <span class="atlas-region-meta">${escapeHtml(atlasRegionMeta(region))}</span>
      <span class="atlas-region-ring"></span>
    </button>
  `;
}

function atlasRegionMeta(region) {
  const summary = region.summary || {};
  return `${summary.macro_count || 0} 大节点 · ${summary.micro_count || 0} 小节点 · ${summary.boss_count || 0} Boss`;
}

function startAtlasChapter(chapterId) {
  currentChapterId = chapterId || currentChapterId;
  localStorage.setItem("math150-current-chapter-id", currentChapterId);
  startChallenge(currentChapterId);
}

function showAtlasMode() {
  closeNodePanel();
  mapWorld.classList.add("atlas-mode");
  mapWorld.classList.remove("graph-mode");
  atlasModeBtn?.classList.add("is-active");
  graphModeBtn?.classList.remove("is-active");
  if (!atlasPayload) loadAtlas().catch(() => renderAtlasFallback());
}

function showGraphMode() {
  mapWorld.classList.add("graph-mode");
  mapWorld.classList.remove("atlas-mode");
  graphModeBtn?.classList.add("is-active");
  atlasModeBtn?.classList.remove("is-active");
  requestAnimationFrame(() => {
    applyMapCamera();
    scheduleSpaceParallax();
  });
}

async function startChallenge(chapterId = currentChapterId) {
  currentChapterId = chapterId || currentChapterId;
  localStorage.setItem("math150-current-chapter-id", currentChapterId);
  const payload = await request("/start", {
    method: "POST",
    body: {
      chapter_id: currentChapterId,
      session_id: currentSessionId(),
    },
  });
  selectedNodeId = currentNodeId(payload.challenge);
  closeNodePanel();
  showToast("训练已开始");
  render(payload, { enterWorld: true, focusCurrent: true });
}

async function loadStatus(options = {}) {
  try {
    const payload = await request(`/status/${encodeURIComponent(currentSessionId())}`);
    if (!options.quiet) showToast("进度已刷新");
    render(payload, { enterWorld: true, focusCurrent: !isNodePanelOpen() });
  } catch (error) {
    if (options.keepStartOnFailure) showStartScreen();
    throw error;
  }
}

async function submitAnswer() {
  if (!lastPayload?.challenge || !canTrainSelected(lastPayload.challenge)) {
    showToast("请先点击当前高亮节点");
    return;
  }
  const answer = answerInput.value.trim();
  if (!answer) {
    showToast("请先填写答案");
    return;
  }
  submitBtn.disabled = true;
  try {
    const payload = await request("/submit", {
      method: "POST",
      body: {
        session_id: currentSessionId(),
        answer,
        steps: [],
        explanation: explanationInput.value.trim() || null,
      },
    });
    answerInput.value = "";
    explanationInput.value = "";
    selectedNodeId = currentNodeId(payload.challenge) || selectedNodeId;
    showToast("本次作答已提交");
    render(payload, { enterWorld: true, focusCurrent: true });
    openNodePanel();
  } finally {
    submitBtn.disabled = false;
  }
}

async function resetChallenge() {
  const payload = await request("/reset", {
    method: "POST",
    body: {
      session_id: currentSessionId(),
      reset_all: true,
    },
  });
  selectedNodeId = currentNodeId(payload.challenge);
  closeNodePanel();
  showToast("训练已重置");
  render(payload, { enterWorld: true, focusCurrent: true });
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
    showToast(message);
    throw new Error(message);
  }
  return payload;
}

function openImportPanel() {
  importModal?.classList.remove("is-hidden", "is-closing");
  requestAnimationFrame(() => importModal?.classList.add("is-open"));
  if (chapterDraftInput && !chapterDraftInput.value.trim()) loadDraftTemplate();
}

function closeImportPanel() {
  importModal?.classList.remove("is-open");
  importModal?.classList.add("is-closing");
  window.setTimeout(() => {
    importModal?.classList.add("is-hidden");
    importModal?.classList.remove("is-closing");
  }, 220);
}

function loadDraftTemplate() {
  if (!chapterDraftInput) return;
  chapterDraftInput.value = `# 新章节名称
chapter_id: math_section_demo
title: 新章节名称

## MacroNodes
| id | title | knowledge_node_id |
| --- | --- | --- |
| math_section_demo.core | 核心大节点 | math_section_demo.core |

## MicroNodes
| id | macro_node_id | type | title | description |
| --- | --- | --- | --- | --- |
| math_section_demo.core.concept | math_section_demo.core | concept | 概念判断 | 说明这个训练节点要求学生掌握什么 |
| math_section_demo.core.method | math_section_demo.core | method | 方法选择 | 说明方法选择依据 |

## MacroChallenges
| id | macro_node_id | title | covers_micro_nodes |
| --- | --- | --- | --- |
| math_section_demo.core.macro_challenge | math_section_demo.core | 综合验收 | math_section_demo.core.concept, math_section_demo.core.method |

## HiddenAbilities
| id | owner_node_id | title | dimensions | why_exists | evidence_sources | failure_modes | repair_target_node_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| math_section_demo.hidden.concept_reason | math_section_demo.core.concept | 概念依据说清 | concept | 防止只会背关键词 | rubric,self_explanation,response_steps | 只出现关键词 | math_section_demo.core.concept |

## CompareGuards
| id | title | node_ids | contrast |
| --- | --- | --- | --- |
| math_section_demo.compare.concept_method | 概念与方法对比 | math_section_demo.core.concept, math_section_demo.core.method | 概念判断回答为什么，方法节点回答怎么做 |

## TransferNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| math_section_demo.transfer.variant | 变式迁移 | math_section_demo.core.method | math_section_demo.core.method | 防止只会原题 |

## SynthesisNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| math_section_demo.synthesis.boss | 综合拆解 | math_section_demo.core.macro_challenge | math_section_demo.core.method | Boss 前检查能否拆解综合题 |

## Edges
| id | edge_type | source_id | target_id | reason |
| --- | --- | --- | --- | --- |
| e1 | supports | math_section_demo.hidden.concept_reason | math_section_demo.core.concept | 隐藏能力支撑可见训练节点 |
| e2 | requires | math_section_demo.core.concept | math_section_demo.core.method | 先会判断，再选方法 |
| e3 | boss_checks | math_section_demo.synthesis.boss | math_section_demo.core.macro_challenge | 综合验收检查拆解能力 |

## ErrorRepairMap
| root_cause | repair_target_node_id |
| --- | --- |
| concept_gap | math_section_demo.core.concept |
| method_error | math_section_demo.core.method |
`;
}

async function validateChapterDraft() {
  if (!chapterDraftInput?.value.trim()) {
    showToast("请先粘贴章节 Markdown");
    return;
  }
  validateDraftBtn.disabled = true;
  importReport.className = "import-report";
  importReport.textContent = "正在校验章节草稿...";
  try {
    const payload = await request("/authoring/chapter-draft/validate", {
      method: "POST",
      body: { markdown: chapterDraftInput.value },
    });
    renderImportReport(payload);
  } finally {
    validateDraftBtn.disabled = false;
  }
}

function renderImportReport(payload) {
  const report = payload.report || {};
  const preview = payload.preview || {};
  const counts = preview.counts || {};
  const tone = report.passed ? "pass" : "fail";
  importReport.className = `import-report ${tone}`;
  importReport.innerHTML = `
    <div class="import-report-head">
      <strong>${report.passed ? "草稿校验通过" : "草稿需要修正"}</strong>
      <span>${report.error_count || 0} 个错误 · ${report.warning_count || 0} 个提醒</span>
    </div>
    <div class="draft-counts">
      <span>${counts.macro_nodes || 0} 大节点</span>
      <span>${counts.micro_nodes || 0} 小节点</span>
      <span>${counts.logic_nodes || 0} 逻辑节点</span>
      <span>${counts.logic_edges || 0} 语义边</span>
    </div>
    ${renderIssueList("必须修正", report.errors || [])}
    ${renderIssueList("建议优化", report.warnings || [])}
    <p class="draft-note">当前状态：${escapeHtml(payload.publish_state || "draft_only")}。草稿不会自动发布到正式训练库。</p>
  `;
}

function renderIssueList(title, issues) {
  if (!issues.length) return "";
  return `
    <div class="issue-list">
      <strong>${escapeHtml(title)}</strong>
      <ul>
        ${issues.map((issue) => `<li><span>${escapeHtml(issue.target || "draft")}</span>${escapeHtml(issue.message || "")}</li>`).join("")}
      </ul>
    </div>
  `;
}

function render(payload, options = {}) {
  lastPayload = payload;
  localStorage.setItem("math150-session-id", currentSessionId());
  const challenge = payload.challenge;
  if (!challenge) {
    showStartScreen();
    return;
  }
  if (!selectedNodeId) selectedNodeId = currentNodeId(challenge);
  if (options.enterWorld) showMapWorld();
  if (options.enterWorld) showGraphMode();
  hudSession.textContent = currentSessionId();
  renderStats(challenge);
  renderGraph(challenge, { focusCurrent: options.focusCurrent });
  renderNodePanel(challenge, payload);
}

function showStartScreen() {
  startScreen.classList.remove("is-hidden");
  mapWorld.classList.add("is-hidden");
  mapWorld.classList.remove("world-entered", "sheet-open");
  closeNodePanel();
}

function showMapWorld() {
  startScreen.classList.add("is-hidden");
  mapWorld.classList.remove("is-hidden");
  requestAnimationFrame(() => mapWorld.classList.add("world-entered"));
}

function openNodePanel() {
  stopEdgePan();
  if (panelCloseTimer) {
    clearTimeout(panelCloseTimer);
    panelCloseTimer = null;
  }
  nodeModal.classList.remove("is-hidden", "is-closing");
  requestAnimationFrame(() => {
    mapWorld.classList.add("sheet-open", "motion-budget");
    nodeModal.classList.add("is-open");
  });
}

function closeNodePanel() {
  if (panelCloseTimer) clearTimeout(panelCloseTimer);
  nodeModal.classList.remove("is-open");
  nodeModal.classList.add("is-closing");
  mapWorld.classList.remove("sheet-open", "motion-budget");
  panelCloseTimer = setTimeout(() => {
    nodeModal.classList.add("is-hidden");
    nodeModal.classList.remove("is-closing");
    panelCloseTimer = null;
  }, panelTransitionMs);
}

function isNodePanelOpen() {
  return nodeModal.classList.contains("is-open");
}

function renderStats(challenge) {
  const macros = Object.values(challenge.macro_nodes || {});
  const micros = Object.values(challenge.micro_nodes || {});
  const masteredMacros = macros.filter((item) => item.status === "mastered").length;
  const masteredMicros = micros.filter((item) => item.status === "mastered").length;
  const averageMastery = average(
    Object.values(challenge.mastery || {}).map((item) => item.mastery_score || 0),
  );
  const repairCount = Object.values(challenge.mastery || {}).filter((item) => item.visual_state === "repair").length;
  overallStats.innerHTML = [
    statBlock(`${masteredMacros}/${macros.length}`, "大节点点亮"),
    statBlock(`${masteredMicros}/${micros.length}`, "小节点点亮"),
    statBlock(`${Math.round(averageMastery)}`, "平均掌握度"),
    statBlock(repairCount ? `${repairCount} 个` : "无", "需要修复"),
  ].join("");
}

function renderGraph(challenge, options = {}) {
  const layout = buildMapLayout(challenge);
  const svg = renderEdges(layout, challenge);
  const nodes = Object.values(layout.nodes).map((node) => renderMapNode(node, challenge)).join("");
  graphView.innerHTML = `
    ${svg}
    ${nodes}
    <div class="map-legend">
      <span class="legend-item"><span class="legend-dot active"></span>当前</span>
      <span class="legend-item"><span class="legend-dot boss"></span>Boss</span>
      <span class="legend-item"><span class="legend-dot logic"></span>逻辑层</span>
      <span class="legend-item"><span class="legend-line derives_to"></span>推导</span>
      <span class="legend-item"><span class="legend-line transforms_to"></span>转化</span>
      <span class="legend-item"><span class="legend-line repairs"></span>修复</span>
      <span class="legend-item"><span class="legend-line transfers_to"></span>迁移</span>
      <span class="legend-item"><span class="legend-line confusion"></span>易混</span>
      <span class="legend-item"><span class="legend-line synthesis"></span>汇入</span>
      <span class="legend-item"><span class="legend-dot unstable"></span>初亮</span>
      <span class="legend-item"><span class="legend-dot stable"></span>稳亮</span>
      <span class="legend-item"><span class="legend-dot repair"></span>修复</span>
      <span class="legend-item"><span class="legend-dot locked"></span>未解锁</span>
    </div>
  `;
  if (options.focusCurrent && !isNodePanelOpen()) {
    const defaultZoom = defaultMapZoom();
    mapCamera.zoom = defaultZoom;
    mapCamera.targetZoom = defaultZoom;
  }
  applyMapCamera();
  if (options.focusCurrent) focusCurrentNode();
}

function handleGraphClick(event) {
  const nodeButton = event.target.closest("[data-node-id]");
  if (!nodeButton || !graphView.contains(nodeButton) || !lastPayload?.challenge) return;
  selectMapNode(nodeButton.getAttribute("data-node-id"));
}

function selectMapNode(nodeId) {
  if (!nodeId || !lastPayload?.challenge) return;
  selectedNodeId = nodeId;
  refreshGraphSelection(lastPayload.challenge);
  renderNodePanel(lastPayload.challenge, lastPayload);
  openNodePanel();
  focusMapNode(nodeId, { panelAware: true });
}

function refreshGraphSelection(challenge) {
  const current = currentNodeId(challenge);
  graphView.querySelectorAll(".map-node").forEach((node) => {
    const nodeId = node.getAttribute("data-node-id");
    const logic = logicNodeById(challenge, nodeId);
    node.classList.toggle("selected", selectedNodeId === nodeId);
    if (logic) {
      node.classList.toggle("logic-dimmed", !logicNodeRelevant(challenge, logic));
    }
  });
  graphView.querySelectorAll(".edge").forEach((edge) => {
    const sourceId = edge.getAttribute("data-source-id");
    const targetId = edge.getAttribute("data-target-id");
    const active = edgeEndpointActive(challenge, sourceId, current)
      || edgeEndpointActive(challenge, targetId, current)
      || sourceId === selectedNodeId
      || targetId === selectedNodeId
      || sourceId === current
      || targetId === current;
    edge.classList.toggle("active", Boolean(active));
  });
}

function edgeEndpointActive(challenge, nodeId, current) {
  const logic = logicNodeById(challenge, nodeId);
  if (!logic) return false;
  const related = [logic.id, logic.owner_node_id, logic.repair_target_node_id, logic.anchor_node_id];
  return related.includes(selectedNodeId) || related.includes(current);
}

function buildMapLayout(challenge) {
  const network = challenge.network || {};
  const networkMacroIds = (network.macro_nodes || []).map((node) => node.id);
  const macroIds = macroOrder
    .filter((macroId) => challenge.macro_nodes?.[macroId])
    .concat(networkMacroIds.filter((macroId) => challenge.macro_nodes?.[macroId] && !macroOrder.includes(macroId)))
    .concat(Object.keys(challenge.macro_nodes || {}).filter((macroId) => !macroOrder.includes(macroId) && !networkMacroIds.includes(macroId)));
  const nodes = {};
  const width = mapViewport.clientWidth || graphView.getBoundingClientRect().width || 1400;
  const compact = width < 1120;
  const branchMin = compact ? 18 : 13;
  const branchMax = compact ? 82 : 87;
  const branchSpan = macroIds.length > 1 ? branchMax - branchMin : 0;
  const entryFan = compact ? 10.5 : 11.8;
  const crownFan = compact ? 9.4 : 10.6;
  const layerY = compact
    ? {
        macro: 91,
        concept: 77,
        trigger: 77,
        method: 63,
        transformation: 50,
        calculation: 36,
        expression: 36,
        boss: 17,
      }
    : {
        macro: 91,
        concept: 77,
        trigger: 77,
        method: 63,
        transformation: 50,
        calculation: 36,
        expression: 36,
        boss: 17,
      };
  const microXOffset = {
    concept: -entryFan,
    trigger: entryFan,
    method: 0,
    transformation: 0,
    calculation: -crownFan,
    expression: crownFan,
  };

  macroIds.forEach((macroId, index) => {
    const x = macroIds.length > 1 ? branchMin + (branchSpan * index) / (macroIds.length - 1) : 50;
    nodes[macroId] = { id: macroId, kind: "macro", x, y: layerY.macro, treeIndex: index };
    const bossId = `${macroId}.macro_challenge`;
    if (challenge.macro_challenges?.[bossId]) {
      nodes[bossId] = {
        id: bossId,
        kind: "boss",
        macroId,
        x,
        y: layerY.boss,
        treeIndex: index,
      };
    }
    Object.keys(challenge.micro_nodes || {})
      .filter((microId) => microId.startsWith(`${macroId}.`))
      .forEach((microId) => {
        const type = microType(microId);
        nodes[microId] = {
          id: microId,
          kind: "micro",
          macroId,
          type,
          x: clamp(x + (microXOffset[type] || 0), 5, 95),
          y: layerY[type] || layerY.method,
          treeIndex: index,
        };
      });
  });
  const compareNodes = network.compare_nodes || [];
  compareNodes.forEach((compare, index) => {
    const referenced = (compare.node_ids || []).map((id) => nodes[id]).filter(Boolean);
    if (!referenced.length) return;
    const avgX = average(referenced.map((node) => node.x));
    const avgY = average(referenced.map((node) => node.y));
    const spread = compact ? 5.8 : 5.2;
    const compareLevel = avgY > layerY.method ? layerY.concept + 8 : avgY + 10;
    nodes[compare.id] = {
      id: compare.id,
      kind: "compare",
      x: clamp(avgX, 9, 91),
      y: clamp(compareLevel + (index - (compareNodes.length - 1) / 2) * spread, 54, 86),
    };
  });
  placeLogicOverlayNodes(nodes, challenge, compact, layerY);
  return { macroIds, nodes, layerY };
}

function placeLogicOverlayNodes(nodes, challenge, compact, layerY) {
  const overlay = challenge.logic_overlay || {};
  if (!overlay.active) return;
  const current = currentNodeId(challenge);
  const perAnchor = {};
  (overlay.logic_nodes || []).forEach((logic) => {
    const anchorId = logic.anchor_node_id || logic.owner_node_id || logic.repair_target_node_id;
    const kind = logic.node_kind || "hidden_ability";
    const relatedIds = [logic.id, logic.owner_node_id, logic.repair_target_node_id, anchorId];
    if (compact && kind === "hidden_ability" && !relatedIds.includes(current) && !relatedIds.includes(selectedNodeId)) return;
    if (compact && kind === "compare_guard" && !relatedIds.includes(selectedNodeId)) return;
    const anchor = nodes[anchorId] || nodes[logic.repair_target_node_id];
    if (!anchor) return;
    const count = perAnchor[anchor.id] || 0;
    perAnchor[anchor.id] = count + 1;
    const kindCount = Object.values(nodes).filter((node) => node.kind === "logic" && node.logicKind === kind).length;
    let x = anchor.x;
    let y = anchor.y;

    if (kind === "boss_criterion") {
      const side = anchor.treeIndex === 0 ? 1 : anchor.treeIndex === 2 ? -1 : count % 2 === 0 ? -1 : 1;
      x = anchor.x + side * (compact ? 8.2 : 9.5);
      y = anchor.y + 10 + count * 5.2;
    } else if (kind === "compare_guard") {
      x = anchor.x;
      y = anchor.y - 8 - count * 6.2;
    } else if (kind === "transfer_node") {
      x = [36, 64, 50][kindCount % 3];
      y = layerY.method - 10 - Math.floor(kindCount / 3) * 5.5;
    } else if (kind === "synthesis_node") {
      x = 50;
      y = layerY.boss + 10 + kindCount * 5;
    } else {
      const macro = nodes[anchor.macroId] || nodes[macroIdFromMicro(anchorId)] || anchor;
      const outerSide = macro.x < 35 ? -1 : macro.x > 65 ? 1 : anchor.x < macro.x ? -1 : 1;
      const offset = compact ? 11.8 : 9.6;
      const row = count % 3;
      const stack = Math.floor(count / 3);
      x = anchor.x + outerSide * (offset + stack * 4.4);
      y = anchor.y + (row - 1) * 4.8;
    }

    nodes[logic.id] = {
      id: logic.id,
      kind: "logic",
      logicKind: kind,
      logic,
      anchorId,
      x: clamp(x, 4, 96),
      y: clamp(y, 6, 94),
    };
  });
}

function renderEdges(layout, challenge) {
  const lines = [];
  const treeLines = [];
  layout.macroIds.forEach((macroId, index) => {
    const macro = layout.nodes[macroId];
    const concept = layout.nodes[`${macroId}.concept`];
    const trigger = layout.nodes[`${macroId}.trigger`];
    const method = layout.nodes[`${macroId}.method`];
    const transformation = layout.nodes[`${macroId}.transformation`];
    const calculation = layout.nodes[`${macroId}.calculation`];
    const expression = layout.nodes[`${macroId}.expression`];
    const boss = layout.nodes[`${macroId}.macro_challenge`];
    [
      [macro, concept],
      [macro, trigger],
      [concept, method],
      [trigger, method],
      [method, transformation],
      [transformation, calculation],
      [transformation, expression],
      [calculation, boss],
      [expression, boss],
    ].forEach(([source, target]) => {
      if (!source || !target) return;
      const active = isCurrentNode(challenge, source.id)
        || isCurrentNode(challenge, target.id)
        || selectedNodeId === source.id
        || selectedNodeId === target.id;
      treeLines.push(svgCurve(source, target, `contains tree-branch${active ? " active" : ""}`));
    });
    const nextMacroId = layout.macroIds[index + 1];
    if (nextMacroId) {
      const mastered = challenge.macro_nodes?.[macroId]?.status === "mastered";
      treeLines.push(svgLine(macro, layout.nodes[nextMacroId], `unlock foundation-line${mastered ? " active" : ""}`));
    }
  });
  (challenge.network?.typed_edges || [])
    .filter((edge) => edge.visible !== false && edge.edge_type !== "prerequisite")
    .forEach((edge) => {
      const source = layout.nodes[edge.source_id];
      const target = layout.nodes[edge.target_id];
      if (!source || !target) return;
      const active = isCurrentNode(challenge, edge.source_id) || isCurrentNode(challenge, edge.target_id) || selectedNodeId === edge.source_id || selectedNodeId === edge.target_id;
      lines.push(svgOrbitCurve(source, target, `${edge.edge_type} secondary-network${active ? " active" : ""}`));
    });
  const overlay = challenge.logic_overlay || {};
  if (overlay.active) {
    (overlay.logic_nodes || []).forEach((logic) => {
      const source = layout.nodes[logic.id];
      const target = layout.nodes[logic.anchor_node_id || logic.owner_node_id];
      if (!source || !target) return;
      const active = logicNodeRelevant(challenge, { logic }) || selectedNodeId === target.id;
      lines.push(svgCurve(source, target, `logic_anchor ${logic.node_kind || "hidden_ability"}${active ? " active" : ""}`));
    });
    (overlay.logic_edges || [])
      .filter((edge) => edge.visible !== false)
      .forEach((edge) => {
        const source = layout.nodes[edge.source_id];
        const target = layout.nodes[edge.target_id];
        if (!source || !target) return;
        const active = selectedNodeId === edge.source_id || selectedNodeId === edge.target_id || logicEdgeTouchesCurrent(challenge, edge);
        lines.push(svgOrbitCurve(source, target, `logic_edge ${edge.edge_type}${active ? " active" : ""}`));
      });
  }

  return `
    <svg class="network-svg" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <marker id="arrow-teal" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
          <path d="M 0 0 L 8 4 L 0 8 z" fill="rgba(127, 241, 231, 0.72)"></path>
        </marker>
        <marker id="arrow-blue" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
          <path d="M 0 0 L 8 4 L 0 8 z" fill="rgba(118, 199, 255, 0.72)"></path>
        </marker>
        <marker id="arrow-red" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
          <path d="M 0 0 L 8 4 L 0 8 z" fill="rgba(255, 124, 134, 0.78)"></path>
        </marker>
        <marker id="arrow-green" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
          <path d="M 0 0 L 8 4 L 0 8 z" fill="rgba(104, 224, 180, 0.76)"></path>
        </marker>
        <marker id="arrow-violet" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth">
          <path d="M 0 0 L 8 4 L 0 8 z" fill="rgba(185, 156, 255, 0.78)"></path>
        </marker>
      </defs>
      ${lines.join("")}
      ${treeLines.join("")}
    </svg>
  `;
}

function renderMapNode(node, challenge) {
  const progress = nodeProgress(challenge, node);
  const mastery = masteryFor(challenge, node.id);
  const title = nodeTitle(challenge, node);
  const isCurrent = isCurrentNode(challenge, node.id);
  const isSelected = selectedNodeId === node.id && !nodeModal.classList.contains("is-hidden");
  const challengeReady = node.kind === "macro" && currentMacroChallengeIsActive(challenge, node.id);
  const isLogicNode = node.kind === "logic";
  const status = isLogicNode ? "available" : progress?.status || "locked";
  const visualState = isLogicNode ? node.logicKind : mastery.visual_state || status;
  const meta = nodeMeta(challenge, node, progress, mastery);
  const classes = [
    "map-node",
    node.kind,
    node.type ? `tree-${node.type}` : "",
    isLogicNode ? `logic-${node.logicKind || "hidden_ability"}` : "",
    status,
    visualState,
    isCurrent ? "current" : "",
    isSelected ? "selected" : "",
    challengeReady ? "challenge-ready" : "",
    isLogicNode && !logicNodeRelevant(challenge, node) ? "logic-dimmed" : "",
  ].filter(Boolean).join(" ");
  return `
    <button
      type="button"
      class="${classes}"
      data-node-id="${escapeHtml(node.id)}"
      data-node-kind="${escapeHtml(node.kind)}"
      data-logic-kind="${escapeHtml(node.logicKind || "")}"
      data-owner-id="${escapeHtml(node.logic?.owner_node_id || "")}"
      data-repair-target-id="${escapeHtml(node.logic?.repair_target_node_id || "")}"
      style="${nodeInlineStyle(node, mastery)}"
    >
      <span class="node-energy" aria-hidden="true"></span>
      <span class="node-title">${escapeHtml(title)}</span>
      <span class="node-meta">${escapeHtml(meta)}</span>
    </button>
  `;
}

function nodeInlineStyle(node, mastery) {
  const score = clamp(Number(mastery.mastery_score || 0), 0, 100);
  const confidence = clamp(Number(mastery.confidence || 0), 0, 1);
  const evidence = Math.min(Number(mastery.evidence_count || 0), 5);
  const baseGlow = node.kind === "logic"
    ? {
        compare_guard: 0.34,
        transfer_node: 0.33,
        synthesis_node: 0.34,
        boss_criterion: 0.38,
        hidden_ability: 0.24,
      }[node.logicKind] || 0.24
    : node.kind === "compare" ? 0.28 : 0.16;
  const glow = clamp(baseGlow + (score / 100) * 0.58 + confidence * 0.18 + evidence * 0.025, 0.12, 0.92);
  const delay = -((stableHash(node.id) % 4200) / 1000).toFixed(2);
  return [
    `left:${node.x}%`,
    `top:${node.y}%`,
    `--mastery:${(score / 100).toFixed(3)}`,
    `--node-glow:${glow.toFixed(3)}`,
    `--energy:${score.toFixed(1)}%`,
    `--pulse-delay:${delay}s`,
  ].join("; ");
}

function stableHash(value) {
  return String(value).split("").reduce((hash, char) => {
    return (hash * 31 + char.charCodeAt(0)) >>> 0;
  }, 7);
}

function renderNodePanel(challenge, payload) {
  const info = selectedNodeInfo(challenge, selectedNodeId);
  if (!info) {
    selectedNodeView.className = "selected-node empty-state";
    selectedNodeView.textContent = "选择一个节点查看状态。";
    renderUnavailableTask("请选择地图上的节点。");
    renderCoach(payload);
    return;
  }
  selectedNodeView.className = "selected-node";
  selectedNodeView.innerHTML = `
    <div>
      <p class="eyebrow">${escapeHtml(info.kindLabel)}</p>
      <h3 id="nodePanelTitle">${escapeHtml(info.title)}</h3>
      <p>${escapeHtml(info.description)}</p>
    </div>
    ${statusPill(info.status, info.visualState)}
    ${info.logicInfo ? "" : renderMasteryPanel(info.mastery)}
    ${renderLogicNodePanel(info.logicInfo)}
    ${renderLogicChainPanel(info.logicChain)}
    ${renderBossCoveragePanel(info.bossCoverage)}
    ${renderAtomHints(info.atomHints || [])}
    ${renderComparePanel(info.compareInfo)}
  `;
  if (canTrainSelected(challenge)) renderTask(challenge);
  else renderUnavailableTask(info.blockedReason);
  renderCoach(payload);
}

function selectedNodeInfo(challenge, nodeId) {
  if (!nodeId) return null;
  if (challenge.macro_nodes?.[nodeId]) {
    const microIds = Object.keys(challenge.micro_nodes || {}).filter((microId) => microId.startsWith(`${nodeId}.`));
    const mastered = microIds.filter((microId) => challenge.micro_nodes[microId].status === "mastered").length;
    const challengeId = `${nodeId}.macro_challenge`;
    const challengeStatus = challenge.macro_challenges?.[challengeId]?.status;
    const isCurrent = isCurrentNode(challenge, nodeId);
    const mastery = masteryFor(challenge, nodeId);
    return {
      title: macroTitles[nodeId] || nodeId,
      status: challenge.macro_nodes[nodeId].status,
      visualState: mastery.visual_state,
      mastery,
      kindLabel: isCurrent && challenge.current_task?.task_type === "macro_challenge" ? "Macro Challenge" : "MacroNode",
      description: `已点亮 ${mastered}/${microIds.length} 个小节点；综合验收状态：${statusLabels[challengeStatus] || "未开放"}。`,
      blockedReason: isCurrent
        ? "这个大节点正在进行综合验收。"
        : "先点亮它包含的小节点；综合验收开放后可在这里训练。",
    };
  }
  if (challenge.macro_challenges?.[nodeId]) {
    const challengeProgress = challenge.macro_challenges[nodeId];
    const spec = networkNodeById(challenge, nodeId, "macro_challenges");
    const macroId = spec?.macro_node_id || nodeId.replace(".macro_challenge", "");
    const isCurrent = isCurrentNode(challenge, nodeId);
    return {
      title: spec?.title || `${macroTitles[macroId] || macroId} · Boss 验收`,
      status: challengeProgress.status,
      visualState: challengeProgress.status === "active" ? "active" : challengeProgress.status,
      mastery: masteryFor(challenge, macroId),
      kindLabel: "Boss Challenge",
      bossCoverage: bossCoverageFor(challenge, nodeId),
      description: "这是绑定到大知识节点的综合验收任务。通过后点亮大节点；失败后只按根因拉起一个目标小节点修复。",
      blockedReason: isCurrent ? "这个 Boss 综合验收正在训练。" : nodeBlockedReason(challengeProgress.status),
    };
  }
  if (challenge.micro_nodes?.[nodeId]) {
    const progress = challenge.micro_nodes[nodeId];
    const type = microType(nodeId);
    const mastery = masteryFor(challenge, nodeId);
    const isCurrent = isCurrentNode(challenge, nodeId);
    const atomHints = atomHintsForMicro(challenge, nodeId);
    return {
      title: networkNodeById(challenge, nodeId, "micro_nodes")?.title || `${macroTitles[macroIdFromMicro(nodeId)] || macroIdFromMicro(nodeId)} · ${microTitles[type] || type}`,
      status: progress.status,
      visualState: mastery.visual_state,
      mastery,
      kindLabel: "MicroNode",
      description: `${networkNodeById(challenge, nodeId, "micro_nodes")?.description || "小节点只做通过点亮；失败会留在本节点。"} 当前已用 ${progress.attempts_used || 0}/5 次机会，失败循环 ${progress.failed_cycles || 0} 次。`,
      atomHints,
      logicChain: logicChainForOwner(challenge, nodeId),
      blockedReason: isCurrent ? "这个小节点正在训练。" : nodeBlockedReason(progress.status),
    };
  }
  const logic = logicNodeById(challenge, nodeId);
  if (logic) {
    return {
      title: logic.title,
      status: "available",
      visualState: logic.node_kind || "hidden_ability",
      mastery: masteryFor(challenge, nodeId),
      kindLabel: logicKindLabel(logic.node_kind),
      description: logic.why_exists || "这个隐藏能力用于支撑诊断和知识网逻辑，不直接作为训练关卡。",
      logicInfo: logic,
      blockedReason: "这是逻辑支撑节点，不消耗训练机会；它解释能力链、修复目标和诊断依据。",
    };
  }
  const compare = networkNodeById(challenge, nodeId, "compare_nodes");
  if (compare) {
    return {
      title: compare.title,
      status: "available",
      visualState: "available",
      mastery: masteryFor(challenge, nodeId),
      kindLabel: "CompareNode",
      description: compare.description || "这是相邻知识点的对比节点，不直接消耗机会，用来提醒你区分题眼和方法。",
      compareInfo: compare,
      logicChain: logicChainForOwner(challenge, nodeId),
      blockedReason: "对比节点暂不直接训练；它会在相关小节点错误时作为辨析提示出现。",
    };
  }
  const guide = networkNodeById(challenge, nodeId, "guide_nodes");
  if (guide) {
    return {
      title: guide.title,
      status: "available",
      visualState: "available",
      mastery: masteryFor(challenge, nodeId),
      kindLabel: guide.kind || "GuideNode",
      description: guide.description || guide.map_hint || "这是知识网的非训练导航节点，用来表达桥接、关口或警示关系。",
      blockedReason: guide.map_hint || "导航节点不消耗训练机会；它只帮助你理解这片知识网的前后逻辑。",
    };
  }
  return null;
}

function renderMasteryPanel(mastery) {
  const score = Math.round(mastery.mastery_score || 0);
  const confidence = Math.round((mastery.confidence || 0) * 100);
  const stability = Math.round((mastery.stability || 0) * 100);
  const weak = (mastery.weak_dimensions || []).map((dim) => dimensionLabels[dim] || dim);
  const roots = (mastery.recent_root_causes || []).map((item) => errorLabels[item] || item);
  return `
    <div class="mastery-panel">
      <div class="mastery-head">
        <strong>${score}</strong>
        <span>${escapeHtml(visualLabels[mastery.visual_state] || mastery.visual_state || "未评估")}</span>
      </div>
      <div class="mastery-bar"><span style="width:${clamp(score, 0, 100)}%"></span></div>
      <div class="mastery-metrics">
        <span>信心 ${confidence}%</span>
        <span>稳定 ${stability}%</span>
        <span>证据 ${mastery.evidence_count || 0} 次</span>
      </div>
      <p class="mastery-note">${escapeHtml(masteryText(mastery, weak, roots))}</p>
    </div>
  `;
}

function renderLogicNodePanel(logic) {
  if (!logic) return "";
  const upstream = logicEdgesForNode(lastPayload?.challenge, logic.id, "target")
    .map((edge) => `${logicEdgeLabel(edge.edge_type)}：${logicNodeTitle(lastPayload?.challenge, edge.source_id)}`);
  const downstream = logicEdgesForNode(lastPayload?.challenge, logic.id, "source")
    .map((edge) => `${logicEdgeLabel(edge.edge_type)}：${logicNodeTitle(lastPayload?.challenge, edge.target_id)}`);
  return `
    <div class="logic-detail-panel">
      <p class="eyebrow">Logic ability</p>
      <h4>${escapeHtml(logicKindLabel(logic.node_kind))}</h4>
      <div class="logic-detail-grid">
        <span>支撑训练点</span><strong>${escapeHtml(logic.owner_node_id || "none")}</strong>
        <span>修复目标</span><strong>${escapeHtml(logic.repair_target_node_id || "none")}</strong>
        <span>显示策略</span><strong>${escapeHtml(logic.visibility_policy || "diagnosis_only")}</strong>
      </div>
      <p>${escapeHtml(logic.why_exists || "这个隐藏能力只服务诊断和图谱解释，不直接成为训练任务。")}</p>
      <div class="logic-mini-columns">
        <div><strong>依赖/来源</strong>${renderList(upstream.slice(0, 4))}</div>
        <div><strong>支撑/去向</strong>${renderList(downstream.slice(0, 4))}</div>
      </div>
      <div class="logic-mini-columns">
        <div><strong>常见失败</strong>${renderList((logic.failure_modes || []).slice(0, 4))}</div>
        <div><strong>修复动作</strong>${renderList((logic.repair_cues || []).slice(0, 4))}</div>
      </div>
    </div>
  `;
}

function renderLogicChainPanel(chain) {
  if (!chain || !chain.nodes?.length) return "";
  const nodeItems = chain.nodes.slice(0, 6).map((node) => `${logicKindLabel(node.node_kind)}：${node.title}`);
  const edgeItems = chain.edges.slice(0, 6).map((edge) => `${logicEdgeLabel(edge.edge_type)}：${logicNodeTitle(lastPayload?.challenge, edge.source_id)} → ${logicNodeTitle(lastPayload?.challenge, edge.target_id)}`);
  return `
    <div class="logic-chain-panel">
      <p class="eyebrow">Hidden logic chain</p>
      <h4>背后的能力支撑</h4>
      <div class="logic-mini-columns">
        <div><strong>隐藏能力</strong>${renderList(nodeItems)}</div>
        <div><strong>语义连接</strong>${renderList(edgeItems)}</div>
      </div>
    </div>
  `;
}

function renderBossCoveragePanel(coverage) {
  if (!coverage || !coverage.length) return "";
  return `
    <div class="boss-coverage-panel">
      <p class="eyebrow">Boss coverage</p>
      <h4>综合验收覆盖矩阵</h4>
      <div class="coverage-grid">
        ${coverage.map((item) => `
          <span class="${item.covered ? "covered" : "missing"}">
            ${escapeHtml(dimensionLabels[item.dimension] || item.dimension)}
          </span>
        `).join("")}
      </div>
    </div>
  `;
}

function renderAtomHints(atomHints) {
  if (!atomHints.length) return "";
  return `
    <div class="atom-panel">
      <p class="eyebrow">Atomic prerequisites</p>
      <h4>背后的原子能力</h4>
      <ul>
        ${atomHints.map((atom) => `
          <li class="${atom.repair_focus ? "repair-focus" : ""}">
            <strong>${escapeHtml(atom.title)}</strong>
            <span>${escapeHtml(atom.description || "这个原子能力支撑当前小节点。")}</span>
            ${renderList(atom.repair_cues || [])}
          </li>
        `).join("")}
      </ul>
    </div>
  `;
}

function renderComparePanel(compareInfo) {
  if (!compareInfo) return "";
  return `
    <div class="compare-panel">
      <p class="eyebrow">Compare node</p>
      <h4>易混边界</h4>
      ${renderList(compareInfo.confusion_cues || [])}
    </div>
  `;
}

function masteryText(mastery, weak, roots) {
  if ((mastery.evidence_count || 0) === 0) return "还没有你的作答证据，系统暂时只知道它的图谱位置。";
  if (mastery.visual_state === "repair") {
    return `当前需要修复：${weak.join("、") || "当前节点"}；最近错因：${roots.join("、") || "未记录"}。`;
  }
  if (mastery.visual_state === "stable_mastery") return "这个节点已有较稳定证据，可以作为后续节点的基础。";
  if (mastery.visual_state === "lit_unstable") return "这个节点已经点亮，但证据还不够稳定，后续可以用变式题确认。";
  if (weak.length) return `薄弱维度：${weak.join("、")}。`;
  return "当前没有明显薄弱维度。";
}

function renderTask(challenge) {
  const question = challenge.current_question;
  const task = challenge.current_task;
  if (!question || !task) {
    renderUnavailableTask(challenge.completed ? "本章节闯关已完成。" : "当前没有可用任务。");
    return;
  }
  submitBtn.disabled = false;
  answerForm.classList.remove("is-hidden");
  answerForm.classList.add("training-form");
  const taskType = task.task_type === "macro_challenge" ? "大节点综合验收" : "小节点训练";
  const progress = taskProgressInfo(challenge, task);
  taskCard.className = "task-card";
  taskCard.innerHTML = `
    <div class="task-head">
      <div>
        <p class="eyebrow">${task.task_type === "macro_challenge" ? "Boss Challenge" : "Node Training"}</p>
        <h3>${escapeHtml(question.title || question.question_id)}</h3>
      </div>
      <span class="status-pill status-active">${taskType}</span>
    </div>
    <div class="attempt-strip" aria-label="机会进度">
      <span>${escapeHtml(progress.label)}</span>
      <div class="attempt-dots">${renderAttemptDots(progress.used, progress.limit)}</div>
    </div>
    <div class="task-meta">
      <span class="status-pill">${escapeHtml(question.difficulty || "standard")}</span>
      <span class="status-pill">${escapeHtml(question.answer_format || "text")}</span>
    </div>
    <div class="question-body">
      <p class="task-stem">${escapeHtml(question.stem || "")}</p>
      <div class="task-prompt">${escapeHtml(question.prompt_markdown || "")}</div>
    </div>
    ${renderHints(question.hints_public || [])}
  `;
}

function renderUnavailableTask(reason) {
  submitBtn.disabled = true;
  answerForm.classList.add("is-hidden");
  answerForm.classList.remove("training-form");
  taskCard.className = "task-card empty-state";
  taskCard.textContent = reason;
}

function taskProgressInfo(challenge, task) {
  if (task.task_type === "macro_challenge") {
    const progress = challenge.macro_challenges?.[task.task_id] || {};
    return {
      used: progress.attempts_used || 0,
      limit: 3,
      label: `Boss 机会 ${progress.attempts_used || 0}/3`,
    };
  }
  const progress = challenge.micro_nodes?.[task.task_id] || {};
  return {
    used: progress.attempts_used || 0,
    limit: 5,
    label: `小节点机会 ${progress.attempts_used || 0}/5`,
  };
}

function renderAttemptDots(used, limit) {
  return Array.from({ length: limit }, (_, index) => {
    const spent = index < used;
    return `<span class="attempt-dot ${spent ? "spent" : "available"}"></span>`;
  }).join("");
}

function renderCoach(payload) {
  if (!payload?.challenge_attempt && !payload?.coach_summary && !payload?.pass_state) {
    coachView.className = "coach-view empty-state";
    coachView.textContent = "提交后会看到本次评分摘要、诊断解释、证据缺口和下一步动作。";
    return;
  }
  coachView.className = "coach-view";
  const passState = payload.pass_state || payload.challenge_attempt?.pass_state || "unknown";
  const tone = passState === "pass" ? "success" : passState === "partial_pass" ? "warning" : "fail";
  const scores = payload.friendly_score_summary || payload.score_vector_summary || {};
  coachView.innerHTML = `
    <section class="coach-block ${tone}">
      <h3>${escapeHtml(payload.status_label || statusText(passState))}</h3>
      <p>${escapeHtml(payload.coach_summary || payload.learner_explanation || "已收到本次作答。")}</p>
    </section>
    ${renderAbilityState(payload)}
    ${renderLogicInsight(payload.logic_insight)}
    <section class="coach-block">
      <h3>下一步</h3>
      <p>${escapeHtml(payload.progression_advice || payload.next_action_hint || "继续按当前任务训练。")}</p>
      ${renderList(payload.next_step_plan || [])}
    </section>
    <section class="coach-block">
      <h3>评分摘要</h3>
      <div class="score-grid">${renderScores(scores)}</div>
    </section>
    <section class="coach-block">
      <h3>证据缺口</h3>
      ${renderList(payload.evidence_gaps || [])}
    </section>
  `;
}

function renderAbilityState(payload) {
  if (!payload?.ability_state_label && !payload?.ability_state_explanation) return "";
  return `
    <section class="coach-block ability-block">
      <h3>能力判断</h3>
      <p><strong>${escapeHtml(payload.ability_state_label || "当前能力状态")}</strong></p>
      <p>${escapeHtml(payload.ability_state_explanation || "")}</p>
    </section>
  `;
}

function renderLogicInsight(insight) {
  if (!insight?.active) return "";
  const primary = insight.primary_ability_id
    ? `<p><strong>${escapeHtml(insight.primary_ability_id)}</strong></p>`
    : "";
  const focus = insight.primary_target_node_id
    ? `<p class="logic-target">修复目标：${escapeHtml(insight.primary_target_node_id)}</p>`
    : "";
  const abilities = Array.isArray(insight.ability_evidence)
    ? insight.ability_evidence.slice(0, 3).map((item) => `
        <li>
          <span>${escapeHtml(item.title || item.ability_id || "隐藏能力")}</span>
          <em>${escapeHtml(item.status || "unknown")}</em>
        </li>
      `).join("")
    : "";
  const cues = Array.isArray(insight.repair_cues)
    ? insight.repair_cues.slice(0, 3).map((cue) => `<li>${escapeHtml(cue)}</li>`).join("")
    : "";
  return `
    <section class="coach-block logic-block">
      <h3>隐藏能力链</h3>
      <p>${escapeHtml(insight.learner_message || "系统已把本次作答映射到背后的能力证据。")}</p>
      ${primary}
      ${focus}
      ${abilities ? `<ul class="logic-ability-list">${abilities}</ul>` : ""}
      ${cues ? `<ul class="logic-cue-list">${cues}</ul>` : ""}
    </section>
  `;
}

function renderScores(scores) {
  const entries = Object.entries(scores);
  if (!entries.length) return '<div class="empty-state">暂无可展示评分。</div>';
  return entries.map(([dimension, value]) => {
    const label = value?.label || dimensionLabels[dimension] || dimension;
    if (value === null || value === undefined || (typeof value === "object" && value.score === null)) {
      return `<div class="score-item"><strong>未评分</strong>${escapeHtml(label)}</div>`;
    }
    const score = typeof value === "object" ? value.score : value;
    const status = typeof value === "object" && value.status ? `<span>${escapeHtml(value.status)}</span>` : "";
    return `<div class="score-item"><strong>${escapeHtml(String(Math.round(Number(score))))}</strong>${escapeHtml(label)}${status}</div>`;
  }).join("");
}

function renderHints(hints) {
  if (!hints.length) return "";
  return `<ul class="hints">${hints.map((hint) => `<li>${escapeHtml(hint)}</li>`).join("")}</ul>`;
}

function renderList(items) {
  if (!items.length) return '<p class="empty-state">暂无。</p>';
  if (Array.isArray(items)) return `<ul>${items.map((item) => `<li>${escapeHtml(listText(item))}</li>`).join("")}</ul>`;
  return `<p>${escapeHtml(listText(items))}</p>`;
}

function listText(item) {
  if (typeof item === "string") return item;
  return item.text || item.reason || JSON.stringify(item);
}

function statBlock(value, label) {
  return `<div class="stat"><strong>${escapeHtml(String(value))}</strong><span>${escapeHtml(label)}</span></div>`;
}

function statusPill(status, visualState = "") {
  const label = visualLabels[visualState] || statusLabels[status] || status;
  return `<span class="status-pill status-${escapeHtml(status)} status-${escapeHtml(visualState || status)}">${escapeHtml(label)}</span>`;
}

function statusText(passState) {
  if (passState === "pass") return "本次通过";
  if (passState === "partial_pass") return "部分通过";
  if (passState === "false_pass") return "答案不足以证明掌握";
  return "本次未通过";
}

function currentSessionId() {
  const value = sessionInput.value.trim() || makeSessionId();
  sessionInput.value = value;
  return value;
}

function makeSessionId() {
  return `web-${Date.now().toString(36)}`;
}

function currentNodeId(challenge) {
  if (!challenge?.current_task) return null;
  return challenge.current_task.task_id;
}

function canTrainSelected(challenge) {
  const task = challenge.current_task;
  if (!task || !selectedNodeId) return false;
  if (task.task_id === selectedNodeId) return true;
  return task.task_type === "macro_challenge" && task.macro_node_id === selectedNodeId;
}

function currentMacroChallengeIsActive(challenge, macroId) {
  const task = challenge.current_task;
  return task?.task_type === "macro_challenge" && task.macro_node_id === macroId;
}

function isCurrentNode(challenge, nodeId) {
  const task = challenge.current_task;
  if (!task) return false;
  if (task.task_id === nodeId) return true;
  return task.task_type === "macro_challenge" && task.macro_node_id === nodeId;
}

function logicNodeById(challenge, nodeId) {
  return (challenge.logic_overlay?.logic_nodes || []).find((node) => node.id === nodeId);
}

function logicNodeTitle(challenge, nodeId) {
  return logicNodeById(challenge, nodeId)?.title
    || networkNodeById(challenge, nodeId, "micro_nodes")?.title
    || networkNodeById(challenge, nodeId, "macro_nodes")?.title
    || networkNodeById(challenge, nodeId, "macro_challenges")?.title
    || networkNodeById(challenge, nodeId, "compare_nodes")?.title
    || nodeId;
}

function logicKindLabel(kind) {
  return {
    hidden_ability: "隐藏能力",
    compare_guard: "易混对比守卫",
    transfer_node: "迁移变式节点",
    synthesis_node: "综合拆解节点",
    boss_criterion: "Boss 验收标准",
  }[kind] || "逻辑能力";
}

function logicEdgeLabel(edgeType) {
  return {
    requires: "前置依赖",
    supports: "支撑",
    derives_to: "推导到",
    transforms_to: "转化为",
    contrasts_with: "对比",
    commonly_confused_with: "易混",
    checks: "检查",
    repairs: "修复指向",
    transfers_to: "迁移到",
    boss_checks: "Boss 检查",
    blocks: "阻断",
  }[edgeType] || edgeType;
}

function logicEdgesForNode(challenge, nodeId, direction = "both") {
  return (challenge?.logic_overlay?.logic_edges || []).filter((edge) => {
    if (direction === "source") return edge.source_id === nodeId;
    if (direction === "target") return edge.target_id === nodeId;
    return edge.source_id === nodeId || edge.target_id === nodeId;
  });
}

function logicChainForOwner(challenge, ownerId) {
  const nodes = (challenge.logic_overlay?.logic_nodes || []).filter((node) => node.owner_node_id === ownerId || node.repair_target_node_id === ownerId);
  if (!nodes.length) return null;
  const ids = new Set(nodes.map((node) => node.id));
  const edges = (challenge.logic_overlay?.logic_edges || []).filter((edge) => ids.has(edge.source_id) || ids.has(edge.target_id));
  return { nodes, edges };
}

function bossCoverageFor(challenge, bossId) {
  const spec = networkNodeById(challenge, bossId, "macro_challenges");
  if (!spec) return [];
  const overlayNodes = challenge.logic_overlay?.logic_nodes || [];
  const coveredTypes = new Set((spec.covers_micro_nodes || []).map((id) => microType(id)));
  const bossLogicIds = new Set(
    overlayNodes
      .filter((node) => node.owner_node_id === bossId || node.node_kind === "boss_criterion" || node.node_kind === "synthesis_node")
      .map((node) => node.id)
  );
  const hasBossChecks = (challenge.logic_overlay?.logic_edges || []).some((edge) => {
    return edge.edge_type === "boss_checks" && (bossLogicIds.has(edge.source_id) || bossLogicIds.has(edge.target_id));
  });
  const hasSynthesisNode = overlayNodes.some((node) => node.node_kind === "synthesis_node");
  return ["concept", "trigger", "method", "transformation", "calculation", "expression", "compare", "transfer", "synthesis"].map((dimension) => ({
    dimension,
    covered: coveredTypes.has(dimension)
      || (dimension === "synthesis" && (hasBossChecks || hasSynthesisNode))
      || (dimension === "transfer" && overlayNodes.some((node) => node.node_kind === "transfer_node"))
      || (dimension === "compare" && overlayNodes.some((node) => node.node_kind === "compare_guard")),
  }));
}

function logicNodeRelevant(challenge, node) {
  const logic = node.logic || node;
  const current = currentNodeId(challenge);
  const selected = selectedNodeId;
  return [logic.id, logic.owner_node_id, logic.repair_target_node_id, logic.anchor_node_id].includes(current)
    || [logic.id, logic.owner_node_id, logic.repair_target_node_id, logic.anchor_node_id].includes(selected);
}

function logicEdgeTouchesCurrent(challenge, edge) {
  const source = logicNodeById(challenge, edge.source_id);
  const target = logicNodeById(challenge, edge.target_id);
  return Boolean((source && logicNodeRelevant(challenge, source)) || (target && logicNodeRelevant(challenge, target)));
}

function masteryFor(challenge, nodeId) {
  const logic = logicNodeById(challenge, nodeId);
  if (logic) {
    return {
      mastery_score: 0,
      confidence: 0,
      stability: 0,
      evidence_count: 0,
      weak_dimensions: logic.dimensions || [],
      recent_root_causes: [],
      visual_state: logic.node_kind || "hidden_ability",
    };
  }
  const compare = networkNodeById(challenge, nodeId, "compare_nodes");
  if (compare) {
    return {
      mastery_score: 0,
      confidence: 0,
      stability: 0,
      evidence_count: 0,
      weak_dimensions: compare.focus_dimensions || [],
      recent_root_causes: [],
      visual_state: "available",
    };
  }
  const guide = networkNodeById(challenge, nodeId, "guide_nodes");
  if (guide) {
    return {
      mastery_score: 0,
      confidence: 0,
      stability: 0,
      evidence_count: 0,
      weak_dimensions: guide.focus_dimensions || [],
      recent_root_causes: [],
      visual_state: "available",
    };
  }
  if (challenge.macro_challenges?.[nodeId]) {
    const macroId = networkNodeById(challenge, nodeId, "macro_challenges")?.macro_node_id || nodeId.replace(".macro_challenge", "");
    return masteryFor(challenge, macroId);
  }
  return challenge.mastery?.[nodeId] || {
    mastery_score: 0,
    confidence: 0,
    stability: 0,
    evidence_count: 0,
    weak_dimensions: [],
    recent_root_causes: [],
    visual_state: challenge.micro_nodes?.[nodeId]?.status || challenge.macro_nodes?.[nodeId]?.status || "locked",
  };
}

function nodeProgress(challenge, node) {
  if (node.kind === "macro") return challenge.macro_nodes[node.id];
  if (node.kind === "micro") return challenge.micro_nodes[node.id];
  if (node.kind === "boss") return challenge.macro_challenges[node.id];
  return { status: "available" };
}

function nodeTitle(challenge, node) {
  if (node.kind === "macro") return networkNodeById(challenge, node.id, "macro_nodes")?.title || macroTitles[node.id] || node.id;
  if (node.kind === "micro") return networkNodeById(challenge, node.id, "micro_nodes")?.title || microTitles[node.type] || node.type;
  if (node.kind === "logic") return node.logic?.title || node.id;
  if (node.kind === "boss") return networkNodeById(challenge, node.id, "macro_challenges")?.title || "Boss 综合验收";
  if (node.kind === "compare") return networkNodeById(challenge, node.id, "compare_nodes")?.title || "易混对比";
  if (node.kind === "guide") return networkNodeById(challenge, node.id, "guide_nodes")?.title || "导航节点";
  return node.id;
}

function nodeMeta(challenge, node, progress, mastery) {
  if (node.kind === "macro") return macroMeta(challenge, node.id);
  if (node.kind === "logic") return `${logicKindLabel(node.logicKind)} · 不消耗机会`;
  if (node.kind === "boss") return `Boss · ${progress?.attempts_used || 0}/3 · ${statusLabels[progress?.status] || progress?.status || "未开放"}`;
  if (node.kind === "compare") return "易混对比 · 不消耗机会";
  if (node.kind === "guide") return "导航标记 · 不消耗机会";
  return microMeta(progress, mastery);
}

function networkNodeById(challenge, nodeId, collection) {
  return (challenge.network?.[collection] || []).find((node) => node.id === nodeId);
}

function atomHintsForMicro(challenge, microId) {
  const active = challenge.active_atom_hints || [];
  const activeById = new Map(active.map((atom) => [atom.id, atom]));
  return (challenge.network?.atom_nodes || [])
    .filter((atom) => atom.micro_node_id === microId)
    .map((atom) => ({ ...atom, repair_focus: Boolean(activeById.get(atom.id)?.repair_focus) }));
}

function macroMeta(challenge, macroId) {
  const microIds = Object.keys(challenge.micro_nodes || {}).filter((microId) => microId.startsWith(`${macroId}.`));
  const mastered = microIds.filter((microId) => challenge.micro_nodes[microId].status === "mastered").length;
  const mastery = masteryFor(challenge, macroId);
  if (currentMacroChallengeIsActive(challenge, macroId)) return `综合验收 · 掌握 ${Math.round(mastery.mastery_score || 0)}`;
  return `大节点 · ${mastered}/${microIds.length} 小节点 · 掌握 ${Math.round(mastery.mastery_score || 0)}`;
}

function microMeta(progress, mastery) {
  const status = progress?.status || "locked";
  return `${visualLabels[mastery.visual_state] || statusLabels[status] || status} · ${progress?.attempts_used || 0}/5 · ${Math.round(mastery.mastery_score || 0)}`;
}

function nodeBlockedReason(status) {
  if (status === "locked") return "这个节点还未解锁。";
  if (status === "mastered") return "这个节点已经点亮。";
  if (status === "failed") return "这个节点已失败，需要重置后重新开始。";
  if (status === "available") return "当前系统按知识网顺序推进；先完成高亮节点。";
  return "当前训练入口是地图上的高亮节点。";
}

function microType(microId) {
  return microId.split(".").at(-1);
}

function macroIdFromMicro(microId) {
  return microId.split(".").slice(0, -1).join(".");
}

function svgLine(from, to, className) {
  return `<line class="edge ${className}" ${svgEdgeAttrs(from, to)} x1="${from.x}" y1="${from.y}" x2="${to.x}" y2="${to.y}" />`;
}

function svgCurve(from, to, className) {
  const midY = (from.y + to.y) / 2;
  return `<path class="edge ${className}" ${svgEdgeAttrs(from, to)} d="M ${from.x} ${from.y} C ${from.x} ${midY}, ${to.x} ${midY}, ${to.x} ${to.y}" />`;
}

function svgOrbitCurve(from, to, className) {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const distance = Math.sqrt(dx * dx + dy * dy);
  const bend = clamp(distance * 0.11, 2.2, 6) * (dx >= 0 ? 1 : -1);
  const c1x = from.x + dx * 0.34 + bend;
  const c1y = from.y + dy * 0.22;
  const c2x = from.x + dx * 0.74 + bend;
  const c2y = from.y + dy * 0.82;
  return `<path class="edge ${className}" ${svgEdgeAttrs(from, to)} d="M ${from.x} ${from.y} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${to.x} ${to.y}" />`;
}

function svgEdgeAttrs(from, to) {
  return `data-source-id="${escapeHtml(from.id)}" data-target-id="${escapeHtml(to.id)}"`;
}

function applyMapCamera() {
  const size = currentMapBaseSize();
  mapCamera.baseWidth = size.width;
  mapCamera.baseHeight = size.height;
  graphView.style.zoom = "";
  const graphWidth = `${size.width}px`;
  const graphHeight = `${size.height}px`;
  if (graphView.style.width !== graphWidth) graphView.style.width = graphWidth;
  if (graphView.style.height !== graphHeight) graphView.style.height = graphHeight;
  graphView.style.transform = `scale(${mapCamera.zoom.toFixed(4)})`;
  const surfaceWidth = `${Math.ceil(size.width * mapCamera.zoom)}px`;
  const surfaceHeight = `${Math.ceil(size.height * mapCamera.zoom)}px`;
  if (mapCameraSurface.style.width !== surfaceWidth) mapCameraSurface.style.width = surfaceWidth;
  if (mapCameraSurface.style.height !== surfaceHeight) mapCameraSurface.style.height = surfaceHeight;
  graphView.dataset.zoom = mapCamera.zoom.toFixed(2);
}

function currentMapBaseSize() {
  const viewportWidth = mapViewport.clientWidth || window.innerWidth;
  const viewportHeight = mapViewport.clientHeight || window.innerHeight;
  if (viewportWidth <= 720) return { width: 1580, height: 1900 };
  if (viewportWidth <= 1120) return { width: 2100, height: 2050 };
  return {
    width: Math.max(3300, Math.round(viewportWidth * 1.85)),
    height: Math.max(2300, Math.round(viewportHeight * 1.8)),
  };
}

function defaultMapZoom() {
  const viewportWidth = mapViewport.clientWidth || window.innerWidth;
  if (viewportWidth <= 720) return 0.74;
  if (viewportWidth <= 1120) return 0.8;
  return 0.86;
}

function handleMapWheel(event) {
  if (!lastPayload?.challenge) return;
  event.preventDefault();
  mapCamera.wheelDelta += event.deltaY;
  mapCamera.wheelX = event.clientX;
  mapCamera.wheelY = event.clientY;
  markCameraMoving();
  if (!mapCamera.wheelFrame) {
    mapCamera.wheelFrame = requestAnimationFrame(flushMapWheel);
  }
}

function flushMapWheel() {
  mapCamera.wheelFrame = null;
  const deltaY = mapCamera.wheelDelta;
  mapCamera.wheelDelta = 0;
  if (!deltaY) return;
  markCameraMoving();
  const rect = mapViewport.getBoundingClientRect();
  const pointerX = mapCamera.wheelX - rect.left;
  const pointerY = mapCamera.wheelY - rect.top;
  const currentZoom = mapCamera.zoom;
  mapCamera.zoomAnchorContentX = (mapViewport.scrollLeft + pointerX) / currentZoom;
  mapCamera.zoomAnchorContentY = (mapViewport.scrollTop + pointerY) / currentZoom;
  mapCamera.zoomAnchorPointerX = pointerX;
  mapCamera.zoomAnchorPointerY = pointerY;
  const baseZoom = mapCamera.targetZoom || currentZoom;
  const cappedDelta = Math.sign(deltaY) * Math.min(Math.abs(deltaY), 96);
  const nextTarget = clamp(baseZoom * Math.exp(-cappedDelta * 0.00044), mapCamera.minZoom, mapCamera.maxZoom);
  if (Math.abs(nextTarget - mapCamera.targetZoom) < 0.002 && Math.abs(nextTarget - currentZoom) < 0.002) return;
  mapCamera.targetZoom = nextTarget;
  startSmoothZoom();
}

function startSmoothZoom() {
  if (!mapCamera.zoomFrame) {
    mapCamera.zoomFrame = requestAnimationFrame(stepSmoothZoom);
  }
}

function stepSmoothZoom() {
  mapCamera.zoomFrame = null;
  const diff = mapCamera.targetZoom - mapCamera.zoom;
  if (Math.abs(diff) < 0.0015) {
    mapCamera.zoom = mapCamera.targetZoom;
    applyZoomAtAnchor();
    return;
  }
  mapCamera.zoom += diff * 0.12;
  applyZoomAtAnchor();
  markCameraMoving();
  mapCamera.zoomFrame = requestAnimationFrame(stepSmoothZoom);
}

function applyZoomAtAnchor() {
  applyMapCamera();
  mapViewport.scrollLeft = mapCamera.zoomAnchorContentX * mapCamera.zoom - mapCamera.zoomAnchorPointerX;
  mapViewport.scrollTop = mapCamera.zoomAnchorContentY * mapCamera.zoom - mapCamera.zoomAnchorPointerY;
  scheduleSpaceParallax();
}

function scheduleSpaceParallax() {
  if (mapCamera.spaceFrame) return;
  mapCamera.spaceFrame = requestAnimationFrame(applySpaceParallax);
}

function applySpaceParallax() {
  mapCamera.spaceFrame = null;
  const x = mapViewport.scrollLeft || 0;
  const y = mapViewport.scrollTop || 0;
  mapViewport.style.setProperty("--space-near-x", `${(-x * 0.14).toFixed(1)}px`);
  mapViewport.style.setProperty("--space-near-y", `${(-y * 0.11).toFixed(1)}px`);
  mapViewport.style.setProperty("--space-mid-x", `${(-x * 0.075).toFixed(1)}px`);
  mapViewport.style.setProperty("--space-mid-y", `${(-y * 0.06).toFixed(1)}px`);
  mapViewport.style.setProperty("--space-far-x", `${(-x * 0.032).toFixed(1)}px`);
  mapViewport.style.setProperty("--space-far-y", `${(-y * 0.026).toFixed(1)}px`);
  mapViewport.style.setProperty("--space-veil-x", `${(-x * 0.018).toFixed(1)}px`);
  mapViewport.style.setProperty("--space-veil-y", `${(-y * 0.014).toFixed(1)}px`);
}

function startMapDrag(event) {
  if (event.button !== 0 || event.target.closest("[data-node-id]") || event.target.closest(".map-legend")) return;
  mapCamera.dragging = true;
  markCameraMoving();
  mapCamera.dragStartX = event.clientX;
  mapCamera.dragStartY = event.clientY;
  mapCamera.dragStartLeft = mapViewport.scrollLeft;
  mapCamera.dragStartTop = mapViewport.scrollTop;
  mapViewport.classList.add("is-dragging");
  mapViewport.setPointerCapture?.(event.pointerId);
  event.preventDefault();
}

function moveMapDrag(event) {
  if (!mapCamera.dragging) return;
  markCameraMoving();
  const dx = event.clientX - mapCamera.dragStartX;
  const dy = event.clientY - mapCamera.dragStartY;
  mapViewport.scrollLeft = mapCamera.dragStartLeft - dx;
  mapViewport.scrollTop = mapCamera.dragStartTop - dy;
  scheduleSpaceParallax();
}

function stopMapDrag(event) {
  if (!mapCamera.dragging) return;
  mapCamera.dragging = false;
  mapViewport.classList.remove("is-dragging");
  if (event?.pointerId !== undefined) mapViewport.releasePointerCapture?.(event.pointerId);
}

function updateEdgePanPointer(event) {
  if (!lastPayload?.challenge || mapCamera.dragging) return;
  mapCamera.pointerActive = true;
  mapCamera.pointerX = event.clientX;
  mapCamera.pointerY = event.clientY;
  startEdgePanLoop();
}

function stopEdgePan() {
  mapCamera.pointerActive = false;
  if (mapCamera.edgePanFrame) {
    cancelAnimationFrame(mapCamera.edgePanFrame);
    mapCamera.edgePanFrame = null;
  }
}

function startEdgePanLoop() {
  if (!mapCamera.edgePanFrame) {
    mapCamera.edgePanFrame = requestAnimationFrame(edgePanTick);
  }
}

function edgePanTick() {
  mapCamera.edgePanFrame = null;
  if (!mapCamera.pointerActive || mapCamera.dragging || mapWorld.classList.contains("is-hidden")) return;
  const rect = mapViewport.getBoundingClientRect();
  const x = mapCamera.pointerX - rect.left;
  const y = mapCamera.pointerY - rect.top;
  const threshold = 92;
  const maxSpeed = isNodePanelOpen() ? 5 : 13;
  const vx = edgePanVelocity(x, rect.width, threshold, maxSpeed);
  const vy = edgePanVelocity(y, rect.height, threshold, maxSpeed);
  if (vx || vy) {
    markCameraMoving();
    mapViewport.scrollBy(vx, vy);
    scheduleSpaceParallax();
    mapCamera.edgePanFrame = requestAnimationFrame(edgePanTick);
  }
}

function edgePanVelocity(position, size, threshold, maxSpeed) {
  if (position < 0 || position > size) return 0;
  if (position < threshold) {
    const strength = (threshold - position) / threshold;
    return -Math.ceil(strength * strength * maxSpeed);
  }
  if (position > size - threshold) {
    const strength = (position - (size - threshold)) / threshold;
    return Math.ceil(strength * strength * maxSpeed);
  }
  return 0;
}

function markCameraMoving() {
  mapViewport.classList.add("is-camera-moving");
  window.clearTimeout(mapCamera.movingTimer);
  mapCamera.movingTimer = window.setTimeout(() => {
    if (!mapCamera.dragging && !mapCamera.wheelFrame && !mapCamera.zoomFrame && !mapCamera.edgePanFrame) {
      mapViewport.classList.remove("is-camera-moving");
    }
  }, 320);
}

function average(values) {
  const usable = values.filter((value) => Number.isFinite(value));
  if (!usable.length) return 0;
  return usable.reduce((sum, value) => sum + value, 0) / usable.length;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function focusCurrentNode() {
  const current = graphView.querySelector(".map-node.current");
  if (current) focusMapNode(current.getAttribute("data-node-id"));
}

function focusMapNode(nodeId, options = {}) {
  window.requestAnimationFrame(() => {
    const node = graphView.querySelector(`[data-node-id="${cssEscape(nodeId)}"]`);
    if (!node) return;
    const horizontalAnchor = 0.5;
    const verticalAnchor = options.panelAware ? 0.28 : 0.66;
    const left = Math.max(0, node.offsetLeft * mapCamera.zoom - mapViewport.clientWidth * horizontalAnchor);
    const top = Math.max(0, node.offsetTop * mapCamera.zoom - mapViewport.clientHeight * verticalAnchor);
    const behavior = options.panelAware || isNodePanelOpen() ? "auto" : "smooth";
    mapViewport.scrollTo({ left, top, behavior });
    scheduleSpaceParallax();
  });
}

function cssEscape(value) {
  if (window.CSS?.escape) return CSS.escape(value);
  return String(value).replaceAll('"', '\\"');
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("show"), 2600);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
