const RESTORE_TRIGGER = Object.freeze({
  detail_branch_close: "detail_branch_open",
  block_leave: "block_enter",
});

function matches(binding, kind, context) {
  if (binding.trigger.kind !== kind) return false;
  if (binding.content_id !== context.contentId) return false;
  return !binding.trigger.detail_branch_id
    || binding.trigger.detail_branch_id === context.detailBranchId;
}

function applyEffect(controller, effect) {
  const payload = effect.payload || {};
  if (effect.kind === "set_state") controller.update({ state: effect.target });
  else if (effect.kind === "perform_action") controller.perform(effect.target, payload);
  else if (effect.kind === "update_parameters") controller.update({ parameters: payload });
  else if (effect.kind === "pause") controller.pause?.();
  else if (effect.kind === "play") controller.resume?.();
  else if (effect.kind === "reset") controller.reset?.();
  else if (effect.kind === "step") controller.perform("step", payload);
  else if (effect.kind === "highlight_target") controller.perform("highlight-target", { target: effect.target, ...payload });
  else if (effect.kind === "clear_highlight") controller.perform("clear-highlight", payload);
  else if (effect.kind === "restore_snapshot") controller.update(payload);
}

export function createBindingRuntime(bindings, controller, instanceId) {
  const relevant = bindings.filter((binding) => binding.instance_id === instanceId);
  const active = [];
  let baseSnapshot = null;
  return {
    dispatch(kind, context) {
      const openingKind = RESTORE_TRIGGER[kind];
      if (openingKind) {
        const removed = active.filter((binding) =>
          matches(binding, openingKind, context)
        );
        if (removed.length) {
          for (const binding of removed) {
            active.splice(active.indexOf(binding), 1);
          }
          controller.update(baseSnapshot);
          for (const binding of active) applyEffect(controller, binding.effect);
          for (const binding of removed) {
            if (binding.return_effect) applyEffect(controller, binding.return_effect);
          }
          if (!active.length) baseSnapshot = null;
        }
      }
      for (const binding of relevant) {
        if (!matches(binding, kind, context)) continue;
        if (binding.restore_previous && !active.includes(binding)) {
          if (!active.length) baseSnapshot = controller.snapshot();
          active.push(binding);
        }
        applyEffect(controller, binding.effect);
      }
    },
    snapshot() {
      return controller.snapshot();
    },
    dispose() {
      active.length = 0;
      baseSnapshot = null;
      controller.dispose();
    },
  };
}
