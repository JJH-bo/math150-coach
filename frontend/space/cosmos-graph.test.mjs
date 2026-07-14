import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const moduleUrl = new URL("./cosmos-graph.js", import.meta.url);
const moduleSource = await readFile(moduleUrl, "utf8");
const graphModule = await import(`data:text/javascript;base64,${Buffer.from(moduleSource).toString("base64")}`);

const {
  buildCosmosGraph,
  buildProgressionLayout,
  deriveNextDestinations,
  orderProgressionNodes,
} = graphModule;

const SEPARABLE_LEARNING_IDS = [
  "ode_separable.concept",
  "ode_separable.trigger",
  "ode_separable.method",
  "ode_separable.transformation",
  "ode_separable.calculation",
  "ode_separable.expression",
];

function progressionEdge(sourceId, targetId) {
  return {
    source_id: sourceId,
    target_id: targetId,
    decision_role: "progression",
  };
}

test("ODE pilot projects one compact six-star system with exactly one oppressive boss", () => {
  const macroIds = ["ode_separable", "ode_first_order_linear", "ode_homogeneous_first_order"];
  const microNodes = [
    ...SEPARABLE_LEARNING_IDS.map((id, index) => ({
      id,
      macro_node_id: "ode_separable",
      type: ["concept", "trigger", "method", "transformation", "calculation", "expression"][index],
      title: id,
    })),
    { id: "ode_first_order_linear.concept", macro_node_id: "ode_first_order_linear", type: "concept" },
    { id: "ode_homogeneous_first_order.concept", macro_node_id: "ode_homogeneous_first_order", type: "concept" },
  ];
  const sequence = ["ode_separable", ...SEPARABLE_LEARNING_IDS, "ode_separable.macro_challenge"];
  const challenge = {
    chapter_id: "ode_network_mvp",
    current_task: { task_id: "ode_separable.concept" },
    network: {
      chapter_id: "ode_network_mvp",
      title: "ODE",
      macro_nodes: macroIds.map((id) => ({ id, title: id })),
      micro_nodes: microNodes,
      macro_challenges: macroIds.map((macroId) => ({
        id: `${macroId}.macro_challenge`,
        macro_node_id: macroId,
        title: `${macroId} boss`,
      })),
      typed_edges: sequence.slice(1).map((targetId, index) => ({
        id: `edge-${index}`,
        source_id: sequence[index],
        target_id: targetId,
        edge_type: index === sequence.length - 2 ? "synthesis" : "transfers_to",
        decision_role: "progression",
      })),
    },
  };

  const graph = buildCosmosGraph(challenge);
  const learningNodes = graph.objects.filter((node) => node.kind === "micro");
  const bosses = graph.objects.filter((node) => node.role === "boss");

  assert.equal(graph.presentationMode, "stellar-system-pilot");
  assert.equal(graph.objects.length, 7);
  assert.deepEqual(learningNodes.map((node) => node.id).sort(), [...SEPARABLE_LEARNING_IDS].sort());
  assert.equal(bosses.length, 1);
  assert.equal(bosses[0].id, "ode_separable.macro_challenge");
  assert.ok(bosses[0].radius >= 188);
  assert.ok(bosses[0].interactionRadius >= 520);
  assert.ok(bosses[0].position[2] >= -980);
  assert.ok(Math.abs(bosses[0].position[0]) <= 360);
  learningNodes.forEach((node) => {
    const distanceToBoss = Math.hypot(
      node.position[0] - bosses[0].position[0],
      node.position[1] - bosses[0].position[1],
      node.position[2] - bosses[0].position[2],
    );
    assert.ok(distanceToBoss >= bosses[0].radius * 1.18, `${node.id} overlaps the boss horizon`);
  });
  assert.ok(new Set(learningNodes.map((node) => node.position[0])).size >= 5);
  assert.ok(learningNodes.some((node) => node.position[1] < 0));
  assert.ok(learningNodes.some((node) => node.position[1] > 0));
  const learningYs = learningNodes.map((node) => node.position[1]);
  assert.ok(Math.max(...learningYs) - Math.min(...learningYs) >= 320);
  assert.equal(graph.frontFrame.entryId, "ode_separable.concept");
  assert.ok(graph.frontFrame.camera[2] <= -220);
  assert.ok(graph.frontFrame.camera[2] > graph.frontFrame.lookAt[2]);
});

test("cross-chapter progression overrides reversed input and keeps each boss last", () => {
  const network = {
    macro_nodes: [
      { id: "chapter-b" },
      { id: "chapter-a" },
    ],
    micro_nodes: [
      { id: "b-concept", macro_node_id: "chapter-b" },
      { id: "a-concept", macro_node_id: "chapter-a" },
    ],
    macro_challenges: [
      { id: "b-boss", macro_node_id: "chapter-b" },
      { id: "a-boss", macro_node_id: "chapter-a" },
    ],
    typed_edges: [
      progressionEdge("chapter-a", "a-concept"),
      progressionEdge("a-concept", "a-boss"),
      progressionEdge("a-boss", "chapter-b"),
      progressionEdge("chapter-b", "b-concept"),
      progressionEdge("b-concept", "b-boss"),
    ],
  };

  const layout = buildProgressionLayout(network);

  assert.equal(layout.positions.get("chapter-a").row, 0);
  assert.equal(layout.positions.get("chapter-b").row, 1);
  assert.equal(layout.positions.get("a-boss").rank, 2);
  assert.equal(layout.positions.get("b-boss").rank, 2);
  assert.equal(layout.frontFrame.macroId, "chapter-a");
  const depthSequence = ["chapter-a", "a-concept", "a-boss", "chapter-b", "b-concept", "b-boss"]
    .map((nodeId) => layout.positions.get(nodeId).position[2]);
  depthSequence.slice(1).forEach((depth, index) => {
    assert.ok(depth < depthSequence[index], `${depth} must be deeper than ${depthSequence[index]}`);
  });
  assert.equal(layout.frontFrame.entryId, "chapter-a");
  assert.ok(layout.frontFrame.lookAt[2] < layout.frontFrame.camera[2]);
});

test("unconnected chapters retain author order", () => {
  const layout = buildProgressionLayout({
    macro_nodes: [{ id: "chapter-b" }, { id: "chapter-a" }],
    micro_nodes: [],
    macro_challenges: [],
    typed_edges: [],
  });

  assert.equal(layout.positions.get("chapter-b").row, 0);
  assert.equal(layout.positions.get("chapter-a").row, 1);
});

test("cycles remain deterministic instead of dropping nodes", () => {
  const ordered = orderProgressionNodes(
    ["chapter", "concept", "boss"],
    [
      progressionEdge("chapter", "concept"),
      progressionEdge("concept", "chapter"),
      progressionEdge("concept", "boss"),
    ],
  );

  assert.deepEqual(ordered, ["chapter", "concept", "boss"]);
});

test("recommended next task retains its real progression tunnel metadata", () => {
  const nextObject = {
    id: "method",
    title: "Method",
    description: "Next training step",
    status: "available",
    trainable: true,
  };
  const graph = {
    edges: [{
      sourceId: "concept",
      targetId: "method",
      edgeType: "transfers_to",
      decisionRole: "progression",
      label: "Concept to method",
    }],
    byId: new Map([[nextObject.id, nextObject]]),
    objects: [nextObject],
  };

  const [choice] = deriveNextDestinations(graph, "concept", {
    current_task: { task_id: "method" },
  });

  assert.equal(choice.id, "method");
  assert.equal(choice.recommended, true);
  assert.equal(choice.edgeType, "transfers_to");
  assert.equal(choice.rapidTransit, true);
  assert.deepEqual(choice.transitPath, ["concept", "method"]);
});

test("recommended task can traverse a multi-hop progression path across chapters", () => {
  const boss = { id: "a-boss", title: "Boss A", status: "mastered", trainable: true, position: [0, 0, -300] };
  const chapter = { id: "chapter-b", title: "Chapter B", status: "available", trainable: false, position: [0, 0, -600] };
  const concept = { id: "b-concept", title: "Concept B", status: "available", trainable: true, position: [0, 0, -900] };
  const graph = {
    edges: [
      { sourceId: "a-boss", targetId: "chapter-b", edgeType: "unlock", decisionRole: "progression" },
      { sourceId: "chapter-b", targetId: "b-concept", edgeType: "contains", decisionRole: "progression" },
    ],
    byId: new Map([[boss.id, boss], [chapter.id, chapter], [concept.id, concept]]),
    objects: [boss, chapter, concept],
  };

  const [choice] = deriveNextDestinations(graph, "a-boss", {
    current_task: { task_id: "b-concept" },
  });

  assert.equal(choice.id, "b-concept");
  assert.equal(choice.rapidTransit, true);
  assert.deepEqual(choice.transitPath, ["a-boss", "chapter-b", "b-concept"]);
});

test("a cyclic progression edge that points toward the player is not offered as rapid transit", () => {
  const source = { id: "deep", title: "Deep", status: "available", trainable: true, position: [0, 0, -800] };
  const target = { id: "front", title: "Front", status: "available", trainable: true, position: [0, 0, -300] };
  const graph = {
    edges: [{ sourceId: "deep", targetId: "front", edgeType: "transfers_to", decisionRole: "progression" }],
    byId: new Map([[source.id, source], [target.id, target]]),
    objects: [source, target],
  };

  const [choice] = deriveNextDestinations(graph, "deep", {
    current_task: { task_id: "front" },
  });

  assert.equal(choice.rapidTransit, false);
  assert.equal(choice.transitPath, null);
});
