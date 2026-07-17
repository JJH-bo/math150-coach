import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function loadTransitModule() {
  let moduleSource = null;
  try {
    moduleSource = await readFile(new URL("./transit-route.js", import.meta.url), "utf8");
  } catch {
    // The first TDD run intentionally reaches the assertion below before the module exists.
  }
  assert.equal(typeof moduleSource, "string", "transit-route.js must exist");
  return import(`data:text/javascript;base64,${Buffer.from(moduleSource).toString("base64")}`);
}

test("progression edges become rapid transit corridors", async () => {
  const transit = await loadTransitModule();

  assert.equal(transit.isRapidTransitEdge({ decisionRole: "progression" }), true);
  assert.equal(transit.isRapidTransitEdge({ decisionRole: "navigation" }), false);
  assert.equal(transit.isRapidTransitEdge({ decisionRole: "progression" }, [0, 0, -200], [0, 0, -500]), true);
  assert.equal(transit.isRapidTransitEdge({ decisionRole: "progression" }, [0, 0, -500], [0, 0, -200]), false);
});

test("rapid transit control points advance from the source rim to the target rim", async () => {
  const transit = await loadTransitModule();
  const points = transit.buildRapidTransitControlPoints(
    [0, 0, 0],
    [120, 40, -800],
    { sourceRadius: 20, targetRadius: 40, seed: 0.73 },
  );

  assert.equal(points.length, 5);
  assert.ok(points[0][2] < 0);
  assert.ok(points.at(-1)[2] > -800);
  points.slice(1).forEach((point, index) => {
    assert.ok(point[2] < points[index][2], "corridor must keep moving deeper");
  });
});

test("guided transit joins the current camera position to the target approach point", async () => {
  const transit = await loadTransitModule();
  const corridor = transit.buildRapidTransitControlPoints([0, 0, 0], [0, 0, -600]);
  const waypoints = transit.buildGuidedTransitWaypoints([30, 10, 90], corridor, [0, 0, -520]);

  assert.deepEqual(waypoints[0], [30, 10, 90]);
  assert.deepEqual(waypoints.at(-1), [0, 0, -520]);
  assert.ok(waypoints.length > corridor.length);
});

test("guided transit stops at the approach point without overshooting and reversing", async () => {
  const transit = await loadTransitModule();
  const waypoints = transit.buildGuidedTransitWaypoints(
    [0, 0, 60],
    [[0, 0, -10], [0, 0, -70], [0, 0, -140], [0, 0, -220]],
    [0, 0, -110],
  );

  assert.deepEqual(waypoints.at(-1), [0, 0, -110]);
  waypoints.slice(1).forEach((point, index) => {
    assert.ok(point[2] <= waypoints[index][2], "camera path must never reverse toward the player");
  });
});

test("multi-hop corridors preserve the exit and entrance on both sides of an intermediate node", async () => {
  const transit = await loadTransitModule();
  assert.equal(typeof transit.buildCombinedTransitControlPoints, "function");
  const combined = transit.buildCombinedTransitControlPoints([
    [[0, 0, -10], [0, 0, -80]],
    [[0, 0, -120], [0, 0, -190]],
  ]);

  assert.deepEqual(combined, [
    [0, 0, -10],
    [0, 0, -80],
    [0, 0, -120],
    [0, 0, -190],
  ]);
});
