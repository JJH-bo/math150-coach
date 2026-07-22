import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function loadSource(relativePath) {
  const source = await readFile(new URL(relativePath, import.meta.url), "utf8");
  return import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
}

test("limit model snapshot connects neighborhood and target", async () => {
  const model = await loadSource("../../backend/classroom_data/model_seed/limit-neighborhood-2d/source.js");

  assert.deepEqual(model.computeLimitSnapshot("approach", { delta: 0.5, theme: "cyan" }), {
    state: "approach",
    delta: 0.5,
    epsilon: 0.35,
    targetX: 1,
    targetY: 2,
    theme: "cyan",
    highlightedTarget: null,
  });
});

test("binary search model advances deterministically", async () => {
  const model = await loadSource("../../backend/classroom_data/model_seed/binary-search-array/source.js");
  let state = model.createSearchState([2, 5, 8, 12, 16, 23, 38], 23);

  state = model.advanceSearch(state);
  state = model.advanceSearch(state);

  assert.equal(state.status, "found");
  assert.equal(state.mid, 5);
  assert.equal(state.steps, 2);
});

test("Fourier model snapshot exposes every learner-controlled dimension", async () => {
  const model = await loadSource("../../backend/classroom_data/model_seed/fourier-series-explorer/source.js");

  assert.deepEqual(
    model.computeFourierSnapshot(
      "partial-sum",
      {"harmonic-count": 9, view: "even-extension", amplitude: 1.5},
      "jump-average",
    ),
    {
      state: "partial-sum",
      harmonicCount: 9,
      view: "even-extension",
      amplitude: 1.5,
      highlightedTarget: "jump-average",
    },
  );
});
