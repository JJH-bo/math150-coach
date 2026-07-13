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

const DOMAIN_COLORS = [0x77dff8, 0x7cddb9, 0xa996dc, 0xd6a769, 0x8fb8e9];

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

  macroSpecs.forEach((macro, macroIndex) => {
    const center = domainCenter(macroIndex, macroSpecs.length);
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
      const position = progressionPosition(center, microIndex, micros.length, macroIndex);
      addObject(makeObject({
        ...micro,
        kind: "micro",
        role,
        status: progress.status || "locked",
        position,
        radius: role === "repair" ? 12 : 14,
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
        position: [center[0] + 370, center[1] + 56, center[2] - 510],
        radius: 52,
        interactionRadius: 250,
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
      interactionRadius: 38,
      color: role === "repair" ? 0xaa718a : 0xc8e8ed,
      macroId: anchor.macroId,
      trainable: false,
    }), objects, byId);
  });

  const runtimeEdges = (network.typed_edges || [])
    .filter((edge) => edge.visible !== false)
    .map((edge) => normalizeEdge(edge))
    .filter((edge) => byId.has(edge.sourceId) && byId.has(edge.targetId));
  const logicEdges = (logicOverlay.logic_edges || [])
    .filter((edge) => edge.visible !== false)
    .map((edge) => normalizeEdge(edge))
    .filter((edge) => byId.has(edge.sourceId) && byId.has(edge.targetId));
  const edges = dedupeEdges([...runtimeEdges, ...logicEdges]);

  return {
    chapterId: challenge.chapter_id || network.chapter_id || "knowledge-cosmos",
    title: network.title || "知识宇宙",
    objects,
    byId,
    domains,
    edges,
    currentTaskId: challenge.current_task?.task_id || null,
  };
}

export function deriveNextDestinations(graph, currentId, challenge = {}) {
  if (!graph) return [];
  const nextTaskId = challenge.current_task?.task_id || null;
  const outgoing = graph.edges
    .filter((edge) => edge.sourceId === currentId)
    .map((edge) => ({ object: graph.byId.get(edge.targetId), edge }))
    .filter((item) => item.object);
  const candidates = [];

  if (nextTaskId && nextTaskId !== currentId && graph.byId.has(nextTaskId)) {
    candidates.push({
      object: graph.byId.get(nextTaskId),
      edge: { edgeType: "recommended", label: "系统推荐的下一项训练" },
      recommended: true,
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

  return candidates.slice(0, 3).map(({ object, edge, recommended }) => ({
    id: object.id,
    title: object.title,
    description: object.description,
    status: object.status,
    relation: edge.label || edge.edgeType,
    edgeType: edge.edgeType,
    recommended: Boolean(recommended),
    enterable: object.trainable && ["active", "available"].includes(object.status),
  }));
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
    derived: false,
  };
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
