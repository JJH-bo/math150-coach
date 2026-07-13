import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const moduleUrl = new URL("./cosmos-graph.js", import.meta.url);
const moduleSource = await readFile(moduleUrl, "utf8");
const graphModule = await import(`data:text/javascript;base64,${Buffer.from(moduleSource).toString("base64")}`);

const { buildProgressionLayout, orderProgressionNodes } = graphModule;

function progressionEdge(sourceId, targetId) {
  return {
    source_id: sourceId,
    target_id: targetId,
    decision_role: "progression",
  };
}

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
  assert.equal(layout.positions.get("chapter-a").position[2], layout.positions.get("a-boss").position[2]);
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
