const TYPE_COLORS = {
  concept: 0x8fdcff,
  trigger: 0xffd37c,
  method: 0x72e0b8,
  transformation: 0x9fb5ff,
  calculation: 0xd6a7ff,
  expression: 0xffb19c,
  condition: 0xa8dfff,
  example: 0xd8c08f,
  mistake: 0xb77989,
  proof: 0xb8d8ff,
  comparison: 0xc8a7ff,
  review: 0x9ee6bd,
};

const TYPE_DIFFICULTY = {
  concept: 0.24,
  trigger: 0.34,
  method: 0.48,
  transformation: 0.62,
  calculation: 0.74,
  expression: 0.82,
  condition: 0.56,
  example: 0.38,
  mistake: 0.58,
  proof: 0.86,
  comparison: 0.52,
  review: 0.3,
};

const DOMAIN_COLORS = [0x77dff8, 0x7cddb9, 0xa996dc, 0xd6a769, 0x8fb8e9];
const BOSS_RADIUS = 78;
const PROGRESSION_DEPTH_SPACING = 290;
const PROGRESSION_CHAPTER_GAP = 220;
const PROGRESSION_BOSS_APPROACH_GAP = 150;
const PROGRESSION_ENTRY_Z = -520;
const PROGRESSION_LANE_RADIUS = 220;
const STELLAR_PILOT_MACRO_ID = "ode_separable";
const STELLAR_PILOT_BOSS_ID = "ode_separable.macro_challenge";
const STELLAR_PILOT_LEARNING_IDS = Object.freeze([
  "ode_separable.concept",
  "ode_separable.trigger",
  "ode_separable.method",
  "ode_separable.transformation",
  "ode_separable.calculation",
  "ode_separable.expression",
]);
const STELLAR_SYSTEM_POSITIONS = new Map([
  ["ode_separable.concept", [-260, 65, -680]],
  ["ode_separable.trigger", [-80, -95, -740]],
  ["ode_separable.method", [90, 95, -805]],
  ["ode_separable.transformation", [220, -25, -870]],
  ["ode_separable.calculation", [40, -145, -935]],
  ["ode_separable.expression", [-150, 40, -1000]],
  [STELLAR_PILOT_BOSS_ID, [430, 30, -1130]],
]);

export function buildStellarSystemPilotLayout(network = {}) {
  const macroExists = (network.macro_nodes || []).some((node) => node.id === STELLAR_PILOT_MACRO_ID);
  const microIds = new Set((network.micro_nodes || []).map((node) => node.id));
  const bossExists = (network.macro_challenges || []).some((node) => node.id === STELLAR_PILOT_BOSS_ID);
  const active = macroExists
    && bossExists
    && STELLAR_PILOT_LEARNING_IDS.every((nodeId) => microIds.has(nodeId));
  if (!active) return { active: false };

  const visibleIds = new Set([...STELLAR_PILOT_LEARNING_IDS, STELLAR_PILOT_BOSS_ID]);
  const positions = new Map(
    [...STELLAR_SYSTEM_POSITIONS].map(([nodeId, position]) => [nodeId, {
      position: [...position],
      rank: STELLAR_PILOT_LEARNING_IDS.indexOf(nodeId),
      row: 0,
    }]),
  );
  return {
    active: true,
    macroId: STELLAR_PILOT_MACRO_ID,
    learningIds: [...STELLAR_PILOT_LEARNING_IDS],
    bossId: STELLAR_PILOT_BOSS_ID,
    visibleIds,
    positions,
    progressionSequence: [...STELLAR_PILOT_LEARNING_IDS, STELLAR_PILOT_BOSS_ID],
    frontFrame: {
      macroId: STELLAR_PILOT_MACRO_ID,
      entryId: STELLAR_PILOT_LEARNING_IDS[0],
      center: [0, -10, -860],
      camera: [0, 80, 60],
      lookAt: [20, -10, -860],
      width: 960,
      height: 650,
    },
  };
}

export function buildCosmosGraph(challenge = {}) {
  const network = challenge.network || {};
  const macroSpecs = network.macro_nodes || [];
  const microSpecs = network.micro_nodes || [];
  const atomSpecs = network.atom_nodes || [];
  const bossSpecs = network.macro_challenges || [];
  const compareSpecs = network.compare_nodes || [];
  const guideSpecs = network.guide_nodes || [];
  const logicOverlay = challenge.logic_overlay || {};
  const objects = [];
  const byId = new Map();
  const domains = [];
  const stellarPilotLayout = buildStellarSystemPilotLayout(network);
  const progressionLayout = stellarPilotLayout.active
    ? stellarPilotLayout
    : buildProgressionLayout(network);

  macroSpecs.forEach((macro, macroIndex) => {
    const center = progressionLayout.positions.get(macro.id)?.position
      || domainCenter(macroIndex, macroSpecs.length);
    const color = DOMAIN_COLORS[macroIndex % DOMAIN_COLORS.length];
    const domain = makeObject({
      id: macro.id,
      title: macro.title,
      description: "章节知识域，进入后展开真实训练链与辅助知识。",
      kind: "domain",
      role: "domain",
      status: challenge.macro_nodes?.[macro.id]?.status || "locked",
      position: center,
      radius: 28,
      difficulty: 0.42,
      interactionRadius: 128,
      color,
      macroId: macro.id,
      trainable: false,
    });
    addObject(domain, objects, byId);
    domains.push({ id: macro.id, center, color });

    const micros = microSpecs.filter((item) => item.macro_node_id === macro.id);
    micros.forEach((micro, microIndex) => {
      const progress = challenge.micro_nodes?.[micro.id] || {};
      const mastery = challenge.mastery?.[micro.id] || {};
      const role = progress.status === "failed" || mastery.visual_state === "repair"
        ? "repair"
        : "training";
      const position = progressionLayout.positions.get(micro.id)?.position
        || progressionPosition(center, microIndex, micros.length, macroIndex);
      addObject(makeObject({
        ...micro,
        kind: "micro",
        role,
        status: progress.status || "locked",
        position,
        radius: role === "repair" ? 12 : 14,
        difficulty: role === "repair" ? Math.max(0.58, TYPE_DIFFICULTY[micro.type] || 0.5) : TYPE_DIFFICULTY[micro.type] || 0.5,
        interactionRadius: 122,
        color: TYPE_COLORS[micro.type] || color,
        macroId: macro.id,
        trainable: true,
      }), objects, byId);
    });

    const boss = bossSpecs.find((item) => item.macro_node_id === macro.id);
    if (boss) {
      const progress = challenge.macro_challenges?.[boss.id] || {};
      addObject(makeObject({
        ...boss,
        description: "章节综合验收。进入灾变核心，完成整条知识链的最终挑战。",
        kind: "boss",
        role: "boss",
        status: progress.status || "locked",
        position: progressionLayout.positions.get(boss.id)?.position
          || [center[0] + 370, center[1] + 56, center[2] - 510],
        radius: stellarPilotLayout.active && boss.id === stellarPilotLayout.bossId ? 118 : BOSS_RADIUS,
        difficulty: 1,
        interactionRadius: 360,
        color: 0x9f351d,
        macroId: macro.id,
        trainable: true,
      }), objects, byId);
    }
  });

  atomSpecs.forEach((atom, atomIndex) => {
    const parent = byId.get(atom.micro_node_id);
    if (!parent) return;
    const angle = hashUnit(atom.id) * Math.PI * 2;
    const orbit = 45 + (atomIndex % 3) * 9;
    addObject(makeObject({
      ...atom,
      kind: "atom",
      role: "auxiliary",
      status: parent.status === "mastered" ? "mastered" : parent.status === "locked" ? "locked" : "available",
      position: [
        parent.position[0] + Math.cos(angle) * orbit,
        parent.position[1] + Math.sin(angle * 1.7) * 18,
        parent.position[2] + Math.sin(angle) * orbit,
      ],
      radius: 5.2,
      difficulty: 0.12,
      interactionRadius: 36,
      color: 0xcfeaf0,
      macroId: parent.macroId,
      trainable: false,
    }), objects, byId);
  });

  compareSpecs.forEach((compare, index) => {
    const anchors = (compare.node_ids || []).map((id) => byId.get(id)).filter(Boolean);
    const position = averagePosition(anchors, [(-1 + index) * 260, 150, -760 - index * 330]);
    position[1] += 86;
    addObject(makeObject({
      ...compare,
      kind: "compare",
      role: "repair",
      status: "available",
      position,
      radius: 10,
      difficulty: 0.52,
      interactionRadius: 54,
      color: 0xb68ecb,
      trainable: false,
    }), objects, byId);
  });

  guideSpecs.forEach((guide, index) => {
    const fallback = domains[index % Math.max(domains.length, 1)]?.center || [0, 0, -500];
    addObject(makeObject({
      ...guide,
      kind: "guide",
      role: "auxiliary",
      status: "available",
      position: [fallback[0] - 250 + (index % 2) * 80, fallback[1] + 130, fallback[2] + 180 - index * 36],
      radius: 7,
      difficulty: 0.16,
      interactionRadius: 42,
      color: 0xe4f5f6,
      trainable: false,
    }), objects, byId);
  });

  const currentTaskId = challenge.current_task?.task_id || null;
  const repairTargetIds = new Set(
    Object.entries(challenge.mastery || {})
      .filter(([, mastery]) => mastery.visual_state === "repair")
      .map(([nodeId]) => nodeId),
  );
  const relevantLogicNodes = (logicOverlay.logic_nodes || [])
    .filter((logic) => {
      const anchors = [logic.owner_node_id, logic.anchor_node_id, logic.repair_target_node_id];
      return anchors.includes(currentTaskId)
        || anchors.some((nodeId) => repairTargetIds.has(nodeId))
        || logic.visibility_policy === "always";
    })
    .slice(0, 12);
  relevantLogicNodes.forEach((logic, index) => {
    const anchor = byId.get(logic.anchor_node_id)
      || byId.get(logic.owner_node_id)
      || byId.get(logic.repair_target_node_id);
    if (!anchor) return;
    const angle = hashUnit(logic.id) * Math.PI * 2;
    const role = logic.decision_role === "repair" || logic.node_kind === "error_node" ? "repair" : "auxiliary";
    addObject(makeObject({
      ...logic,
      description: logic.why_exists || "用于解释当前知识关系与诊断证据。",
      kind: "logic",
      role,
      status: "available",
      position: [
        anchor.position[0] + Math.cos(angle) * (68 + index * 3),
        anchor.position[1] + 32 + Math.sin(angle * 1.4) * 24,
        anchor.position[2] + Math.sin(angle) * (68 + index * 3),
      ],
      radius: role === "repair" ? 7.5 : 4.8,
      difficulty: role === "repair" ? 0.56 : 0.14,
      interactionRadius: 38,
      color: role === "repair" ? 0xaa718a : 0xc8e8ed,
      macroId: anchor.macroId,
      trainable: false,
    }), objects, byId);
  });

  const presentationObjects = stellarPilotLayout.active
    ? objects.filter((object) => stellarPilotLayout.visibleIds.has(object.id))
    : objects;
  const presentationById = stellarPilotLayout.active
    ? new Map(presentationObjects.map((object) => [object.id, object]))
    : byId;
  const runtimeEdges = (network.typed_edges || [])
    .filter((edge) => edge.visible !== false)
    .map((edge) => normalizeEdge(edge))
    .filter((edge) => presentationById.has(edge.sourceId) && presentationById.has(edge.targetId));
  const logicEdges = (logicOverlay.logic_edges || [])
    .filter((edge) => edge.visible !== false)
    .map((edge) => normalizeEdge(edge))
    .filter((edge) => presentationById.has(edge.sourceId) && presentationById.has(edge.targetId));
  const edges = dedupeEdges([...runtimeEdges, ...logicEdges]);
  const presentedCurrentTaskId = presentationById.has(currentTaskId)
    ? currentTaskId
    : stellarPilotLayout.active ? stellarPilotLayout.frontFrame.entryId : currentTaskId;

  return {
    chapterId: challenge.chapter_id || network.chapter_id || "knowledge-cosmos",
    title: network.title || "知识宇宙",
    objects: presentationObjects,
    byId: presentationById,
    domains: stellarPilotLayout.active ? [] : domains,
    edges,
    currentTaskId: presentedCurrentTaskId,
    frontFrame: progressionLayout.frontFrame,
    presentationMode: stellarPilotLayout.active ? "stellar-system-pilot" : "progression-layout",
    systemMeta: stellarPilotLayout.active ? {
      macroId: stellarPilotLayout.macroId,
      learningIds: [...stellarPilotLayout.learningIds],
      bossId: stellarPilotLayout.bossId,
    } : null,
  };
}

export function deriveNextDestinations(graph, currentId, challenge = {}) {
  if (!graph) return [];
  const nextTaskId = challenge.current_task?.task_id || null;
  const outgoing = graph.edges
    .filter((edge) => edge.sourceId === currentId)
    .map((edge) => ({
      object: graph.byId.get(edge.targetId),
      edge,
      transitPath: isForwardProgressionEdge(graph, edge) ? [currentId, edge.targetId] : null,
    }))
    .filter((item) => item.object);
  const candidates = [];

  if (nextTaskId && nextTaskId !== currentId && graph.byId.has(nextTaskId)) {
    const transitPath = findProgressionPath(graph, currentId, nextTaskId);
    const progressionEdge = transitPath?.length === 2
      ? graph.edges.find((edge) => edge.sourceId === currentId && edge.targetId === nextTaskId)
      : transitPath
        ? {
          edgeType: "progression_path",
          label: "沿前置知识通道进入下一阶段",
          decisionRole: "progression",
        }
        : null;
    candidates.push({
      object: graph.byId.get(nextTaskId),
      edge: progressionEdge || {
        edgeType: "recommended",
        label: "系统推荐的下一项训练",
        decisionRole: "navigation",
      },
      recommended: true,
      transitPath,
    });
  }
  outgoing.forEach((item) => {
    if (!candidates.some((candidate) => candidate.object.id === item.object.id)) candidates.push(item);
  });
  graph.objects
    .filter((object) => object.id !== currentId && ["active", "available"].includes(object.status))
    .forEach((object) => {
      if (!candidates.some((candidate) => candidate.object.id === object.id)) {
        candidates.push({ object, edge: { edgeType: "explore", label: "已解锁，可自由探索" } });
      }
    });

  return candidates.slice(0, 3).map(({ object, edge, recommended, transitPath }) => ({
    id: object.id,
    title: object.title,
    description: object.description,
    status: object.status,
    relation: edge.label || edge.edgeType,
    edgeType: edge.edgeType,
    recommended: Boolean(recommended),
    rapidTransit: Boolean(transitPath?.length > 1),
    transitPath: transitPath || null,
    enterable: object.trainable && ["active", "available"].includes(object.status),
  }));
}

export function findProgressionPath(graph, sourceId, targetId) {
  if (sourceId === targetId) return [sourceId];
  const queue = [[sourceId]];
  const visited = new Set([sourceId]);
  while (queue.length > 0) {
    const path = queue.shift();
    const currentId = path.at(-1);
    const nextIds = graph.edges
      .filter((edge) => edge.sourceId === currentId && isForwardProgressionEdge(graph, edge))
      .map((edge) => edge.targetId);
    for (const nextId of nextIds) {
      if (visited.has(nextId)) continue;
      const nextPath = [...path, nextId];
      if (nextId === targetId) return nextPath;
      visited.add(nextId);
      queue.push(nextPath);
    }
  }
  return null;
}

function isForwardProgressionEdge(graph, edge) {
  if (edge.decisionRole !== "progression") return false;
  const source = graph.byId.get(edge.sourceId);
  const target = graph.byId.get(edge.targetId);
  if (!source?.position || !target?.position) return true;
  return Number(target.position[2]) < Number(source.position[2]) - 0.001;
}

function makeObject(definition) {
  return {
    id: definition.id,
    title: definition.title || definition.id,
    description: definition.description || definition.why_exists || "知识节点",
    type: definition.type || definition.node_kind || definition.kind,
    kind: definition.kind,
    role: definition.role,
    status: definition.status,
    position: [...definition.position],
    radius: definition.radius,
    difficulty: Number(definition.difficulty ?? 0.5),
    interactionRadius: definition.interactionRadius,
    color: definition.color,
    macroId: definition.macroId || null,
    trainable: Boolean(definition.trainable),
  };
}

function addObject(object, objects, byId) {
  if (!object?.id || byId.has(object.id)) return;
  objects.push(object);
  byId.set(object.id, object);
}

function normalizeEdge(edge) {
  return {
    id: edge.id,
    sourceId: edge.source_id,
    targetId: edge.target_id,
    edgeType: edge.edge_type || "support",
    label: edge.label || edge.edge_type || "知识关系",
    reason: edge.reason || "",
    weight: Number(edge.semantic_weight || 1),
    decisionRole: edge.decision_role || "navigation",
    derived: false,
  };
}

export function buildProgressionLayout(network = {}) {
  const macros = network.macro_nodes || [];
  const microSpecs = network.micro_nodes || [];
  const bossSpecs = network.macro_challenges || [];
  const typedEdges = network.typed_edges || [];
  const orderedMacros = orderProgressionMacros(macros, microSpecs, bossSpecs, typedEdges);
  const positions = new Map();
  const progressionSequence = [];
  let depthCursor = 0;
  let depthRank = 0;

  orderedMacros.forEach((macro, macroIndex) => {
    const micros = microSpecs.filter((item) => item.macro_node_id === macro.id);
    const boss = bossSpecs.find((item) => item.macro_node_id === macro.id);
    const candidateIds = [macro.id, ...micros.map((item) => item.id), ...(boss ? [boss.id] : [])];
    const ordered = orderProgressionNodes(candidateIds, typedEdges);
    const bossLast = boss
      ? [...ordered.filter((nodeId) => nodeId !== boss.id), boss.id]
      : ordered;

    if (macroIndex > 0) depthCursor += PROGRESSION_CHAPTER_GAP;

    bossLast.forEach((nodeId, index) => {
      const isBoss = nodeId === boss?.id;
      if (isBoss) depthCursor += PROGRESSION_BOSS_APPROACH_GAP;
      const phase = depthRank * 0.88;
      const chapterBias = Math.sin(macroIndex * 1.73) * 48;
      const x = Math.sin(phase) * PROGRESSION_LANE_RADIUS + chapterBias;
      const y = Math.cos(phase * 0.72) * 86 + Math.sin(macroIndex * 1.4) * 34;
      const z = PROGRESSION_ENTRY_Z - depthCursor;
      positions.set(nodeId, {
        position: [x, y, z],
        rank: index,
        row: macroIndex,
        depthRank,
      });
      progressionSequence.push(nodeId);
      depthRank += 1;
      depthCursor += PROGRESSION_DEPTH_SPACING;
    });
  });

  const entryId = progressionSequence[0] || null;
  const entry = positions.get(entryId)?.position || [0, 0, PROGRESSION_ENTRY_Z];
  const next = positions.get(progressionSequence[1])?.position || [entry[0], entry[1], entry[2] - 320];
  const lookAt = entry.map((value, index) => value + (next[index] - value) * 0.58);

  return {
    positions,
    progressionSequence,
    frontFrame: {
      macroId: orderedMacros[0]?.id || null,
      entryId,
      center: [...entry],
      camera: [entry[0] - 150, entry[1] + 72, entry[2] + 470],
      lookAt,
      width: 760,
      height: 520,
    },
  };
}

export function orderProgressionMacros(macros, microSpecs = [], bossSpecs = [], typedEdges = []) {
  const macroIds = macros.map((macro) => macro.id);
  const ownerByNodeId = new Map(macroIds.map((macroId) => [macroId, macroId]));
  microSpecs.forEach((micro) => ownerByNodeId.set(micro.id, micro.macro_node_id));
  bossSpecs.forEach((boss) => ownerByNodeId.set(boss.id, boss.macro_node_id));

  const chapterEdges = typedEdges
    .filter((edge) => edge.decision_role === "progression")
    .map((edge) => ({
      source_id: ownerByNodeId.get(edge.source_id),
      target_id: ownerByNodeId.get(edge.target_id),
      decision_role: "progression",
    }))
    .filter((edge) => edge.source_id && edge.target_id && edge.source_id !== edge.target_id);
  const macroById = new Map(macros.map((macro) => [macro.id, macro]));

  return orderProgressionNodes(macroIds, chapterEdges)
    .map((macroId) => macroById.get(macroId))
    .filter(Boolean);
}

export function orderProgressionNodes(nodeIds, typedEdges = []) {
  const originalOrder = new Map(nodeIds.map((nodeId, index) => [nodeId, index]));
  const nodeSet = new Set(nodeIds);
  const outgoing = new Map(nodeIds.map((nodeId) => [nodeId, []]));
  const indegree = new Map(nodeIds.map((nodeId) => [nodeId, 0]));

  typedEdges
    .filter((edge) => edge.decision_role === "progression")
    .filter((edge) => nodeSet.has(edge.source_id) && nodeSet.has(edge.target_id))
    .forEach((edge) => {
      outgoing.get(edge.source_id).push(edge.target_id);
      indegree.set(edge.target_id, indegree.get(edge.target_id) + 1);
    });

  const ready = nodeIds.filter((nodeId) => indegree.get(nodeId) === 0);
  const ordered = [];
  while (ready.length > 0) {
    ready.sort((left, right) => originalOrder.get(left) - originalOrder.get(right));
    const nodeId = ready.shift();
    ordered.push(nodeId);
    outgoing.get(nodeId).forEach((targetId) => {
      indegree.set(targetId, indegree.get(targetId) - 1);
      if (indegree.get(targetId) === 0) ready.push(targetId);
    });
  }

  nodeIds.forEach((nodeId) => {
    if (!ordered.includes(nodeId)) ordered.push(nodeId);
  });
  return ordered;
}

function dedupeEdges(edges) {
  const seen = new Set();
  return edges.filter((edge) => {
    const key = `${edge.sourceId}:${edge.targetId}:${edge.edgeType}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function domainCenter(index, count) {
  const spread = Math.max(1, count - 1);
  const x = (index - spread / 2) * 680;
  return [x, Math.sin(index * 1.6) * 72, -560 - index * 690];
}

function progressionPosition(center, index, count, macroIndex) {
  const t = count <= 1 ? 0.5 : index / (count - 1);
  const angle = -1.1 + t * 2.3 + macroIndex * 0.22;
  const radius = 170 + index * 48;
  return [
    center[0] + Math.cos(angle) * radius,
    center[1] + Math.sin(index * 1.34) * 52 + (t - 0.5) * 34,
    center[2] + Math.sin(angle) * radius - index * 86,
  ];
}

function averagePosition(objects, fallback) {
  if (!objects.length) return [...fallback];
  const total = objects.reduce((sum, object) => [
    sum[0] + object.position[0],
    sum[1] + object.position[1],
    sum[2] + object.position[2],
  ], [0, 0, 0]);
  return total.map((value) => value / objects.length);
}

function hashUnit(value) {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0) / 4294967295;
}
