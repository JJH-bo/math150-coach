import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function load(name) {
  const source = await readFile(new URL(name, import.meta.url), "utf8");
  return import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
}

function packagePayload() {
  return {
    package_id: "calculus",
    title: "微积分课堂",
    courses: [{
      id: "math-1",
      title: "高等数学",
      chapters: [{
        id: "limits",
        title: "极限",
        modules: [
          { id: "limit-core", title: "极限核心", summary: "趋近机制" },
          { id: "continuity", title: "连续性", summary: "连续的语言" },
          { id: "applications", title: "极限应用", summary: "应用场景" },
          { id: "epsilon-delta", title: "严格定义", summary: "定义结构" },
          { id: "infinity", title: "无穷远", summary: "远处行为" },
          { id: "sequences", title: "数列极限", summary: "离散趋近" },
        ],
        relations: [{
          id: "r1",
          kind: "conceptual_dependency",
          source_module_id: "limit-core",
          target_module_id: "continuity",
        }],
      }],
    }],
  };
}

test("atlas keeps arbitrary complete modules as destinations", async () => {
  const { projectAtlas } = await load("./atlas.js");
  const atlas = projectAtlas(packagePayload());

  assert.equal(atlas.courses[0].chapters[0].destinations.length, 6);
  assert.equal(atlas.courses[0].chapters[0].destinations[0].kind, "core_module");
  assert.equal(atlas.courses[0].chapters[0].routes[0].kind, "conceptual_dependency");
  assert.ok(atlas.decorations.every((item) => item.interactive === false));
});

test("scene snapshot drops every non-continuity field", async () => {
  const { sanitizeSceneSnapshot } = await load("./scene-store.js");
  const snapshot = sanitizeSceneSnapshot({
    schema_version: "classroom_scene_v1",
    package_id: "calculus",
    release_version: "r-one",
    module_id: "limit-core",
    open_detail_ids: ["limit-detail"],
    model_snapshot: { state: "approach" },
    mastery: 0.8,
    score: 100,
    diagnosis: "none",
    recommended_next_step: "hidden",
  });

  assert.deepEqual(snapshot, {
    schema_version: "classroom_scene_v1",
    package_id: "calculus",
    release_version: "r-one",
    module_id: "limit-core",
    open_detail_ids: ["limit-detail"],
    model_snapshot: { state: "approach" },
  });
});

test("scene store rejects a snapshot from another immutable release", async () => {
  const { createSceneStore } = await load("./scene-store.js");
  const memory = new Map();
  const storage = {
    getItem: (key) => memory.get(key) ?? null,
    setItem: (key, value) => memory.set(key, value),
    removeItem: (key) => memory.delete(key),
  };
  const store = createSceneStore(storage);
  store.save({ package_id: "calculus", release_version: "r-old", module_id: "limit-core" });

  assert.equal(store.load({ packageId: "calculus", releaseVersion: "r-new" }), null);
  assert.equal(memory.size, 0);
});

test("binding runtime applies and restores temporary model state", async () => {
  const { createBindingRuntime } = await load("./bindings.js");
  const events = [];
  let snapshot = { state: "overview" };
  const controller = {
    snapshot: () => ({ ...snapshot }),
    update: (next) => { snapshot = { ...snapshot, ...next }; events.push(["update", next]); },
    perform: (action, payload) => events.push(["perform", action, payload]),
    dispose: () => events.push(["dispose"]),
  };
  const runtime = createBindingRuntime([{
    id: "detail-highlight",
    content_id: "intro",
    instance_id: "view",
    trigger: { kind: "detail_branch_open", detail_branch_id: "detail-1" },
    effect: { kind: "set_state", target: "approach" },
    restore_previous: true,
  }], controller, "view");

  runtime.dispatch("detail_branch_open", { contentId: "intro", detailBranchId: "detail-1" });
  assert.equal(snapshot.state, "approach");
  runtime.dispatch("detail_branch_close", { contentId: "intro", detailBranchId: "detail-1" });
  assert.equal(snapshot.state, "overview");
  runtime.dispose();
  assert.deepEqual(events.at(-1), ["dispose"]);
});

test("leaving one temporary binding preserves another active explanation", async () => {
  const { createBindingRuntime } = await load("./bindings.js");
  let snapshot = { state: "overview", highlightedTarget: null };
  const controller = {
    snapshot: () => ({ ...snapshot }),
    update: (next) => { snapshot = { ...next }; },
    perform: (action) => {
      if (action === "highlight-target") snapshot.highlightedTarget = "target-value";
    },
    dispose() {},
  };
  const runtime = createBindingRuntime([
    {
      id: "formula-state",
      content_id: "formula",
      instance_id: "view",
      trigger: { kind: "block_enter" },
      effect: { kind: "set_state", target: "approach" },
      restore_previous: true,
    },
    {
      id: "detail-highlight",
      content_id: "intro",
      instance_id: "view",
      trigger: { kind: "detail_branch_open", detail_branch_id: "detail-1" },
      effect: { kind: "perform_action", target: "highlight-target" },
      restore_previous: true,
    },
  ], controller, "view");

  runtime.dispatch("block_enter", { contentId: "formula" });
  runtime.dispatch("detail_branch_open", {
    contentId: "intro",
    detailBranchId: "detail-1",
  });
  runtime.dispatch("block_leave", { contentId: "formula" });

  assert.equal(snapshot.state, "overview");
  assert.equal(snapshot.highlightedTarget, "target-value");
});
