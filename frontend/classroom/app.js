import { projectAtlas } from "./atlas.js";
import { createBindingRuntime } from "./bindings.js";
import { renderModule } from "./content-renderer.js";
import { createSceneStore } from "./scene-store.js";
import { mountTeachingModel } from "/classroom-runtime/host.js";

const apiBase = "/api/classroom/v1";
const sceneStore = createSceneStore();
const dom = Object.fromEntries([
  "loadingView", "atlasView", "atlasTitle", "courseSelect", "chapterSelect",
  "motionToggle", "chapterRegion", "chapterTitle", "decorativeStars",
  "moduleDestinations", "classroomStage", "backToAtlas", "breadcrumbs",
  "fullscreenModel", "closeFullscreenModel", "lessonContent", "modelDock",
  "modelTitle", "modelRoot", "modelFallback", "emptyView", "toast",
].map((id) => [id, document.querySelector(`#${id}`)]));

const state = {
  release: null,
  package: null,
  atlas: null,
  courseId: null,
  chapterId: null,
  moduleId: null,
  modelRuntime: null,
  observer: null,
  activeContentId: null,
  scrollTimer: null,
};

start().catch(showFatal);

async function start() {
  wireShell();
  const catalog = await request(`${apiBase}/catalog`);
  if (!catalog.packages?.length) {
    showOnly(dom.emptyView);
    return;
  }
  await loadPackage(catalog.packages[0].package_id);
}

function wireShell() {
  dom.courseSelect.addEventListener("change", () => {
    state.courseId = dom.courseSelect.value;
    state.chapterId = state.atlas.courses.find((item) => item.id === state.courseId)?.chapters[0]?.id;
    renderAtlas();
  });
  dom.chapterSelect.addEventListener("change", () => {
    state.chapterId = dom.chapterSelect.value;
    renderChapter();
  });
  dom.backToAtlas.addEventListener("click", closeModule);
  dom.fullscreenModel.addEventListener("click", () => toggleFullscreen(true));
  dom.closeFullscreenModel.addEventListener("click", () => toggleFullscreen(false));
  dom.motionToggle.addEventListener("click", () => {
    const active = !document.body.classList.contains("reduced-motion");
    document.body.classList.toggle("reduced-motion", active);
    dom.motionToggle.setAttribute("aria-pressed", String(active));
    saveScene();
  });
  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && dom.modelDock.classList.contains("is-fullscreen")) {
      toggleFullscreen(false);
    }
  });
  window.addEventListener("scroll", scheduleSave, { passive: true });
  window.addEventListener("beforeunload", () => {
    saveScene();
    state.modelRuntime?.dispose();
  });
}

async function loadPackage(packageId) {
  const release = await request(`${apiBase}/packages/${encodeURIComponent(packageId)}`);
  state.release = release;
  state.package = release.package;
  state.atlas = projectAtlas(release.package);
  const saved = sceneStore.load({ packageId, releaseVersion: release.version });
  state.courseId = saved?.course_id || state.atlas.courses[0]?.id;
  const course = state.atlas.courses.find((item) => item.id === state.courseId);
  state.chapterId = saved?.chapter_id || course?.chapters[0]?.id;
  document.body.classList.toggle("reduced-motion", Boolean(saved?.reduced_motion));
  dom.motionToggle.setAttribute("aria-pressed", String(Boolean(saved?.reduced_motion)));
  renderAtlas();
  if (saved?.module_id) {
    await openModule(saved.module_id, saved);
  } else {
    showOnly(dom.atlasView);
  }
}

function renderAtlas() {
  dom.atlasTitle.textContent = state.atlas.title;
  dom.courseSelect.innerHTML = state.atlas.courses.map((course) =>
    `<option value="${escapeAttribute(course.id)}">${escapeText(course.title)}</option>`
  ).join("");
  dom.courseSelect.value = state.courseId;
  const course = currentCourse();
  dom.chapterSelect.innerHTML = (course?.chapters || []).map((chapter) =>
    `<option value="${escapeAttribute(chapter.id)}">${escapeText(chapter.title)}</option>`
  ).join("");
  dom.chapterSelect.value = state.chapterId;
  renderChapter();
}

function renderChapter() {
  const chapter = currentChapter();
  if (!chapter) return;
  dom.chapterTitle.textContent = chapter.title;
  dom.decorativeStars.innerHTML = state.atlas.decorations.map((star) =>
    `<span style="left:${star.x}%;top:${star.y}%;opacity:${star.opacity}"></span>`
  ).join("");
  dom.moduleDestinations.innerHTML = chapter.destinations.map((destination) => `
    <button class="module-destination" type="button"
      data-module-id="${escapeAttribute(destination.id)}"
      style="left:${destination.x}%;top:${destination.y}%;--scale:${destination.scale}">
      <strong>${escapeText(destination.title)}</strong>
      <span>${escapeText(destination.summary)}</span>
    </button>
  `).join("");
  dom.moduleDestinations.querySelectorAll("[data-module-id]").forEach((button) => {
    button.addEventListener("click", () => openModule(button.dataset.moduleId));
  });
  saveScene();
}

async function openModule(moduleId, saved = null) {
  disposeActiveModule();
  const payload = await request(
    `${apiBase}/packages/${encodeURIComponent(state.package.package_id)}/modules/${encodeURIComponent(moduleId)}`
  );
  state.moduleId = moduleId;
  state.courseId = payload.course.id;
  state.chapterId = payload.chapter.id;
  dom.breadcrumbs.textContent = `${payload.course.title} / ${payload.chapter.title} / ${payload.module.title}`;
  dom.lessonContent.innerHTML = renderModule(payload.module);
  showOnly(dom.classroomStage);
  wireDetails(saved?.open_detail_ids || []);
  await mountModel(payload, saved);
  observeContent();
  requestAnimationFrame(() => {
    if (saved?.scroll_top) window.scrollTo({ top: saved.scroll_top, behavior: "instant" });
    else window.scrollTo({ top: 0, behavior: "instant" });
  });
  saveScene();
}

async function mountModel(payload, saved) {
  const instance = payload.model_instances?.[0];
  if (!instance) {
    showModelFallback("本模块没有配置交互模型，课堂内容仍可完整阅读。");
    return;
  }
  try {
    const metadata = await request(
      `${apiBase}/models/${encodeURIComponent(instance.model_id)}/versions/${encodeURIComponent(instance.model_version)}`
    );
    const sourceResponse = await fetch(metadata.source_url);
    if (!sourceResponse.ok) throw new Error(`模型源代码读取失败：${sourceResponse.status}`);
    const source = await sourceResponse.text();
    dom.modelTitle.textContent = metadata.manifest.title;
    dom.modelFallback.classList.add("is-hidden");
    dom.modelRoot.classList.remove("is-hidden");
    const mounted = await mountTeachingModel({
      source,
      manifest: metadata.manifest,
      scenario: {
        initial_state: saved?.model_snapshot?.state || instance.initial_state,
        parameters: { ...instance.parameters, ...(saved?.model_snapshot || {}) },
        commands: [],
      },
      root: dom.modelRoot,
      viewport: { width: dom.modelRoot.clientWidth, height: dom.modelRoot.clientHeight },
    });
    const controller = {
      update(next) {
        mounted.model.update({
          state: next.state,
          parameters: next.parameters || next,
        });
        if (next.highlightedTarget === null) {
          mounted.model.perform("clear-highlight", {});
        }
      },
      perform(action, value) { mounted.model.perform(action, value); },
      pause() { mounted.model.pause(); },
      resume() { mounted.model.resume(); },
      reset() { mounted.model.reset(); },
      snapshot() { return mounted.snapshot(); },
      dispose() { mounted.dispose(); },
    };
    state.modelRuntime = createBindingRuntime(
      payload.model_bindings || [],
      controller,
      instance.instance_id,
    );
    toggleFullscreen(saved?.viewport_mode === "fullscreen");
  } catch (error) {
    showModelFallback(`${instance.fallback_description}\n\n模型运行信息：${error.message}`);
  }
}

function wireDetails(openIds) {
  dom.lessonContent.querySelectorAll("details[data-detail-id]").forEach((detail) => {
    detail.open = openIds.includes(detail.dataset.detailId);
    detail.addEventListener("toggle", () => {
      const kind = detail.open ? "detail_branch_open" : "detail_branch_close";
      state.modelRuntime?.dispatch(kind, {
        contentId: detail.dataset.parentContentId,
        detailBranchId: detail.dataset.detailId,
      });
      saveScene();
    });
  });
}

function observeContent() {
  state.observer = new IntersectionObserver((entries) => {
    const visible = entries
      .filter((entry) => entry.isIntersecting)
      .sort((left, right) => right.intersectionRatio - left.intersectionRatio)[0];
    if (!visible || visible.intersectionRatio < 0.35) return;
    const nextId = visible.target.dataset.contentId;
    if (!nextId || nextId === state.activeContentId) return;
    if (state.activeContentId) {
      state.modelRuntime?.dispatch("block_leave", { contentId: state.activeContentId });
    }
    state.activeContentId = nextId;
    state.modelRuntime?.dispatch("block_enter", { contentId: nextId });
    saveScene();
  }, { threshold: [0.35, 0.6, 0.85], rootMargin: "-80px 0px -35% 0px" });
  dom.lessonContent.querySelectorAll("[data-content-id]").forEach((element) =>
    state.observer.observe(element)
  );
}

function closeModule() {
  saveScene();
  disposeActiveModule();
  state.moduleId = null;
  showOnly(dom.atlasView);
  window.scrollTo({ top: 0, behavior: "instant" });
}

function disposeActiveModule() {
  state.observer?.disconnect();
  state.observer = null;
  state.modelRuntime?.dispose();
  state.modelRuntime = null;
  state.activeContentId = null;
  dom.modelRoot.replaceChildren();
}

function toggleFullscreen(active) {
  dom.modelDock.classList.toggle("is-fullscreen", active);
  document.body.style.overflow = active ? "hidden" : "";
  saveScene();
}

function showModelFallback(message) {
  dom.modelRoot.classList.add("is-hidden");
  dom.modelFallback.classList.remove("is-hidden");
  dom.modelFallback.textContent = message;
}

function saveScene() {
  if (!state.release || !state.package) return;
  const openDetailIds = [...dom.lessonContent.querySelectorAll("details[open][data-detail-id]")]
    .map((detail) => detail.dataset.detailId);
  sceneStore.save({
    schema_version: "classroom_scene_v1",
    package_id: state.package.package_id,
    release_version: state.release.version,
    course_id: state.courseId,
    chapter_id: state.chapterId,
    module_id: state.moduleId || undefined,
    content_id: state.activeContentId || undefined,
    scroll_top: state.moduleId ? Math.round(window.scrollY) : 0,
    open_detail_ids: openDetailIds,
    model_snapshot: state.modelRuntime?.snapshot(),
    viewport_mode: dom.modelDock.classList.contains("is-fullscreen") ? "fullscreen" : "inline",
    quality: "balanced",
    reduced_motion: document.body.classList.contains("reduced-motion"),
  });
}

function scheduleSave() {
  clearTimeout(state.scrollTimer);
  state.scrollTimer = setTimeout(saveScene, 120);
}

function currentCourse() {
  return state.atlas.courses.find((item) => item.id === state.courseId);
}

function currentChapter() {
  return currentCourse()?.chapters.find((item) => item.id === state.chapterId);
}

function showOnly(target) {
  [dom.loadingView, dom.atlasView, dom.classroomStage, dom.emptyView].forEach((view) =>
    view.classList.toggle("is-hidden", view !== target)
  );
}

async function request(url) {
  const response = await fetch(url, { headers: { Accept: "application/json" } });
  if (!response.ok) throw new Error(`课堂数据读取失败：${response.status}`);
  return response.json();
}

function showFatal(error) {
  showOnly(dom.emptyView);
  dom.emptyView.querySelector("h1").textContent = "课堂暂时无法载入";
  dom.emptyView.querySelector("p:last-child").textContent = error.message;
}

function escapeText(value) {
  const element = document.createElement("span");
  element.textContent = String(value ?? "");
  return element.innerHTML;
}

function escapeAttribute(value) {
  return escapeText(value).replaceAll('"', "&quot;");
}
