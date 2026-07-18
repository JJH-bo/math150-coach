import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function loadModule(name) {
  const source = await readFile(new URL(name, import.meta.url), "utf8");
  return import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
}

test("host validates the complete lifecycle contract", async () => {
  const { validateLifecycle } = await loadModule("./host.js");
  const complete = Object.fromEntries(
    ["mount", "update", "perform", "pause", "resume", "reset", "snapshot", "dispose"]
      .map((name) => [name, () => {}]),
  );

  assert.deepEqual(validateLifecycle(complete), []);
  assert.deepEqual(validateLifecycle({ mount() {} }), [
    "update", "perform", "pause", "resume", "reset", "snapshot", "dispose",
  ]);
});

test("host merges only declared parameters", async () => {
  const { mergeParameters } = await loadModule("./host.js");
  const specs = [
    { id: "delta", default: 0.5 },
    { id: "theme", default: "cyan" },
  ];

  assert.deepEqual(mergeParameters(specs, { delta: 0.25, ignored: true }), {
    delta: 0.25,
    theme: "cyan",
  });
});

test("resource tracker releases frames and listeners", async () => {
  const { createResourceTracker } = await loadModule("./host.js");
  const listeners = new Set();
  const target = {
    addEventListener(type, listener) { listeners.add(`${type}:${listener.name}`); },
    removeEventListener(type, listener) { listeners.delete(`${type}:${listener.name}`); },
  };
  const cancelled = [];
  const tracker = createResourceTracker({
    requestAnimationFrame: () => 17,
    cancelAnimationFrame: (id) => cancelled.push(id),
  });
  function onClick() {}

  tracker.requestFrame(() => {});
  tracker.listen(target, "click", onClick);
  assert.deepEqual(tracker.counts(), { frames: 1, listeners: 1 });

  tracker.dispose();
  assert.deepEqual(tracker.counts(), { frames: 0, listeners: 0 });
  assert.deepEqual(cancelled, [17]);
  assert.equal(listeners.size, 0);
});
