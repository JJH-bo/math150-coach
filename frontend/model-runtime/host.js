export const REQUIRED_LIFECYCLE = Object.freeze([
  "mount", "update", "perform", "pause", "resume", "reset", "snapshot", "dispose",
]);

export function validateLifecycle(model) {
  return REQUIRED_LIFECYCLE.filter((name) => typeof model?.[name] !== "function");
}

export function mergeParameters(specs, overrides = {}) {
  return Object.fromEntries(specs.map((spec) => [
    spec.id,
    Object.hasOwn(overrides, spec.id) ? overrides[spec.id] : spec.default,
  ]));
}

export function createResourceTracker(environment = globalThis) {
  const frames = new Set();
  const listeners = new Set();
  return {
    requestFrame(callback) {
      const id = environment.requestAnimationFrame((time) => {
        frames.delete(id);
        callback(time);
      });
      frames.add(id);
      return id;
    },
    cancelFrame(id) {
      if (frames.delete(id)) environment.cancelAnimationFrame(id);
    },
    listen(target, type, listener, options) {
      target.addEventListener(type, listener, options);
      listeners.add({ target, type, listener, options });
    },
    counts() {
      return { frames: frames.size, listeners: listeners.size };
    },
    dispose() {
      frames.forEach((id) => environment.cancelAnimationFrame(id));
      frames.clear();
      listeners.forEach(({ target, type, listener, options }) => {
        target.removeEventListener(type, listener, options);
      });
      listeners.clear();
    },
  };
}

export async function mountTeachingModel({ source, manifest, scenario, root, viewport }) {
  const tracker = createResourceTracker(globalThis);
  const logs = [];
  const moduleUrl = URL.createObjectURL(new Blob([source], { type: "text/javascript" }));
  try {
    const modelModule = await import(moduleUrl);
    if (typeof modelModule.createTeachingModel !== "function") {
      throw new Error("Model source does not export createTeachingModel(context).");
    }
    const model = modelModule.createTeachingModel({
      root,
      viewport,
      requestFrame: tracker.requestFrame,
      cancelFrame: tracker.cancelFrame,
      listen: tracker.listen,
      log(level, message, context = {}) { logs.push({ level, message, context }); },
    });
    const missing = validateLifecycle(model);
    if (missing.length) throw new Error(`Missing lifecycle methods: ${missing.join(", ")}`);
    const parameters = mergeParameters(manifest.parameters || [], scenario.parameters || {});
    model.mount({ state: scenario.initial_state, parameters });
    for (const command of scenario.commands || []) {
      if (command.kind === "set_state") model.update({ state: command.target, parameters });
      else if (command.kind === "perform_action") model.perform(command.target, command.payload || {});
      else if (command.kind === "update_parameters") {
        Object.assign(parameters, command.payload || {});
        model.update({ parameters });
      } else if (command.kind === "pause") model.pause();
      else if (command.kind === "resume") model.resume();
      else if (command.kind === "reset") model.reset();
    }
    return {
      model,
      logs,
      snapshot: () => model.snapshot(),
      resourceCounts: () => tracker.counts(),
      dispose() {
        model.dispose();
        tracker.dispose();
        URL.revokeObjectURL(moduleUrl);
        return tracker.counts();
      },
    };
  } catch (error) {
    tracker.dispose();
    URL.revokeObjectURL(moduleUrl);
    throw error;
  }
}
