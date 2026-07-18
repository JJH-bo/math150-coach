import { mountTeachingModel } from "./host.js";

const request = window.__TEACHING_PREVIEW_REQUEST__;
const root = document.querySelector("#modelRoot");
const errorView = document.querySelector("#error");
let controller = null;

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
