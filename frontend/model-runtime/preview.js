import { mountTeachingModel } from "./host.js";

const request = window.__TEACHING_PREVIEW_REQUEST__;
const root = document.querySelector("#modelRoot");
const errorView = document.querySelector("#error");
let controller = null;

function alternateParameterValue(spec, current) {
  if (spec.type === "boolean") return !Boolean(current);
  if (spec.type === "choice") {
    const choices = spec.choices || [];
    return choices.find((choice) => choice !== current) ?? current;
  }
  if (spec.type === "integer" || spec.type === "number") {
    const candidates = [spec.minimum, spec.maximum, Number(current) + 1]
      .filter((value) => value !== undefined && value !== null);
    const next = candidates.find((value) => Number(value) !== Number(current));
    return spec.type === "integer" ? Math.round(next ?? Number(current)) : (next ?? Number(current));
  }
  return `${current ?? ""} preview-change`;
}

async function start() {
  if (!request) throw new Error("Preview request was not injected.");
  document.querySelector("#title").textContent = request.manifest.title;
  controller = await mountTeachingModel({ ...request, root, viewport: { width: innerWidth, height: innerHeight } });
  window.__teachingPreviewReady = {
    ready: true,
    snapshot: controller.snapshot(),
    logs: controller.logs,
    resources_before_dispose: controller.resourceCounts(),
  };
  window.__exerciseTeachingPreview = () => {
    const before = controller.snapshot();
    const performed = [];
    const parameter = request.manifest.parameters?.[0];
    if (parameter) {
      const currentParameters = {
        ...Object.fromEntries(
          (request.manifest.parameters || []).map((spec) => [spec.id, spec.default]),
        ),
        ...(request.scenario.parameters || {}),
      };
      const next = alternateParameterValue(parameter, currentParameters[parameter.id]);
      controller.model.update({
        parameters: { ...currentParameters, [parameter.id]: next },
      });
      performed.push({ kind: "parameter_change", target: parameter.id, value: next });
    } else if (request.manifest.actions?.[0]) {
      const action = request.manifest.actions[0];
      controller.model.perform(action.id, {});
      performed.push({ kind: "explicit_control", target: action.id });
    }
    return {
      performed,
      snapshot_before: before,
      snapshot_after: controller.snapshot(),
    };
  };
}

window.__disposeTeachingPreview = () => {
  const resources = controller?.dispose() || { frames: 0, listeners: 0 };
  const total = resources.frames + resources.listeners;
  window.__teachingPreviewDisposed = { resources_after_dispose: total, resources };
  return window.__teachingPreviewDisposed;
};

start().catch((error) => {
  errorView.hidden = false;
  errorView.textContent = error.stack || String(error);
  window.__teachingPreviewReady = { ready: false, error: String(error) };
});
