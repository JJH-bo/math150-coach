import { projectAtlas } from "./atlas.js";
import { createBindingRuntime } from "./bindings.js";
import { typesetMath } from "./content-renderer.js";
import { mountModelControls } from "./model-controls.js";
import { createSceneStore } from "./scene-store.js";
import { createSessionClient } from "./session-client.js";
import { renderLearningSession } from "./scene-renderer.js";
import { mountTeachingModel } from "/classroom-runtime/host.js";

const apiBase = "/api/classroom/v1";
const sceneStore = createSceneStore();
const sessionClient = createSessionClient({ apiBase });
const dom = Object.fromEntries([
  "loadingView", "atlasView", "atlasTitle", "courseSelect", "chapterSelect",
  "motionToggle", "chapterRegion", "chapterTitle", "chapterQuestion", "chapterRoute", "decorativeStars",
  "moduleDestinations", "classroomStage", "backToAtlas", "breadcrumbs",
  "fullscreenModel", "closeFullscreenModel", "lessonContent", "modelDock",
  "modelTitle", "modelControls", "modelRoot", "modelFallback", "emptyView", "toast",
].map((id) => [id, document.querySelector(`#${id}`)]));

const state = {
  release: null,
  package: null,
  atlas: null,
  courseId: null,
  chapterId: null,
  moduleId: null,
  modelRuntime: null,
  modelControls: null,
  observer: null,
  activeContentId: null,
  scrollTimer: null,
  focusTimer: null,
  fullscreenScrollTop: null,
  modulePayload: null,
  learningSession: null,
  sessionAccess: null,
  sessionEvents: null,
  openDetailIds: [],
};

start().catch(showFatal);

async function start() {
  wireShell();
  const catalog = await request(`${apiBase}/catalog`);
  if (!catalog.packages?.length) {
    showOnly(dom.emptyView);
    return;
  }
  const requestedPackageId = new URLSearchParams(window.location.search)
    .get("package_id");
  const selectedPackage = requestedPackageId
    ? catalog.packages.find((item) => item.package_id === requestedPackageId)
    : catalog.packages[0];
  if (!selectedPackage) {
    throw new Error(`课堂不存在：${requestedPackageId}`);
  }
  await loadPackage(selectedPackage.package_id);
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
    state.sessionEvents?.close();
    state.modelControls?.dispose();
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
  dom.chapterQuestion.textContent = chapter.overview?.essentialQuestion
    || "这一章要解决什么？";
  dom.chapterRoute.textContent = chapter.overview?.learningRouteSummary
    || "每个发光目的地代表一个完整核心模块。进入后在连续课堂中展开知识。";
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
  state.modulePayload = payload;
  state.courseId = payload.course.id;
  state.chapterId = payload.chapter.id;
  state.openDetailIds = [...(saved?.open_detail_ids || [])];
  dom.breadcrumbs.textContent = `${payload.course.title} / ${payload.chapter.title} / ${payload.module.title}`;
  const access = await ensureLearningSession(payload);
  state.sessionAccess = access;
  state.learningSession = access.session;
  renderSessionContent();
  showOnly(dom.classroomStage);
  await mountModel(payload, saved);
  reapplyOpenDetailBindings();
  observeContent();
  watchLearningSession();
  requestAnimationFrame(() => {
    if (saved?.scroll_top) window.scrollTo({ top: saved.scroll_top, behavior: "instant" });
    else window.scrollTo({ top: 0, behavior: "instant" });
  });
  saveScene();
}

function sessionStorageKey(payload) {
  return [
    "math150-learning-session-v1",
    payload.package_id,
    payload.version,
    payload.module.id,
  ].join(":");
}

async function ensureLearningSession(payload) {
  const storageKey = sessionStorageKey(payload);
  let savedAccess = null;
  try {
    savedAccess = JSON.parse(localStorage.getItem(storageKey) || "null");
  } catch {
    localStorage.removeItem(storageKey);
  }
  if (savedAccess?.sessionId && savedAccess?.accessToken) {
    try {
      const session = await sessionClient.get(savedAccess);
      if (
        session.package_id === payload.package_id
        && session.release_version === payload.version
        && session.module_id === payload.module.id
      ) {
        return { ...savedAccess, session };
      }
    } catch {
      localStorage.removeItem(storageKey);
    }
  }
  const created = await sessionClient.create({
    packageId: payload.package_id,
    moduleId: payload.module.id,
  });
  localStorage.setItem(storageKey, JSON.stringify({
    sessionId: created.sessionId,
    accessToken: created.accessToken,
  }));
  return created;
}

function renderSessionContent() {
  if (!state.learningSession || !state.modulePayload) return;
  const scrollTop = window.scrollY;
  const currentlyOpen = [...dom.lessonContent.querySelectorAll(
    "details[open][data-detail-id]",
  )].map((detail) => detail.dataset.detailId);
  if (currentlyOpen.length) state.openDetailIds = currentlyOpen;
  dom.lessonContent.innerHTML = renderLearningSession(
    state.learningSession,
    state.modulePayload.module,
  );
  wireDetails(state.openDetailIds);
  wireLearningControls();
  scheduleMathTypeset();
  if (state.observer) observeContent();
  requestAnimationFrame(() => window.scrollTo({ top: scrollTop, behavior: "instant" }));
}

function scheduleMathTypeset(attempt = 0) {
  if (globalThis.MathJax?.tex2chtmlPromise) {
    void typesetMath(dom.lessonContent);
    return;
  }
  if (attempt < 20) {
    setTimeout(() => scheduleMathTypeset(attempt + 1), 150);
  }
}

function wireLearningControls() {
  const reveal = dom.lessonContent.querySelector("#revealNextStep");
  reveal?.addEventListener("click", async () => {
    reveal.disabled = true;
    reveal.textContent = "正在展开已发布的下一步…";
    try {
      state.learningSession = await sessionClient.reveal(
        state.sessionAccess,
        state.learningSession.revision,
      );
      renderSessionContent();
      showToast("已展开基础路线的下一步");
    } catch (error) {
      await recoverSessionConflict(error);
    }
  });
  const returnButton = dom.lessonContent.querySelector("#returnFromExpansion");
  returnButton?.addEventListener("click", async () => {
    returnButton.disabled = true;
    try {
      state.learningSession = await sessionClient.returnToParent(
        state.sessionAccess,
        state.learningSession.revision,
        `return-${crypto.randomUUID()}`,
      );
      renderSessionContent();
      showToast("已回到上一层解释");
    } catch (error) {
      await recoverSessionConflict(error);
    }
  });
}

function watchLearningSession() {
  state.sessionEvents?.close();
  state.sessionEvents = sessionClient.watch(
    state.sessionAccess,
    state.learningSession.revision,
    async (event) => {
      if (event.revision <= state.learningSession.revision) return;
      state.learningSession = await sessionClient.get(state.sessionAccess);
      renderSessionContent();
      if (event.kind === "scene.expanded") {
        showToast("GPT 已把新的详细解释插入当前学习位置");
      }
      watchLearningSession();
    },
  );
}

async function recoverSessionConflict(error) {
  if (error.status === 409) {
    state.learningSession = await sessionClient.get(state.sessionAccess);
    renderSessionContent();
    watchLearningSession();
    return;
  }
  showToast(error.message);
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
    const savedSnapshot = saved?.model_snapshot || {};
    const initialParameters = {
      ...Object.fromEntries(
        (metadata.manifest.parameters || []).map((spec) => [spec.id, spec.default]),
      ),
      ...instance.parameters,
      ...(savedSnapshot.parameters || {}),
    };
    dom.modelTitle.textContent = metadata.manifest.title;
    dom.modelFallback.classList.add("is-hidden");
    dom.modelRoot.classList.remove("is-hidden");
    const mounted = await mountTeachingModel({
      source,
      manifest: metadata.manifest,
      scenario: {
        initial_state: savedSnapshot.state || instance.initial_state,
        parameters: initialParameters,
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
    state.modelControls = mountModelControls({
      root: dom.modelControls,
      manifest: metadata.manifest,
      instance: { ...instance, parameters: initialParameters },
      onParameter(_parameterId, _value, parameters) {
        mounted.model.update({ parameters });
        saveScene();
      },
      onAction(actionId, actionPayload) {
        mounted.model.perform(actionId, actionPayload);
        saveScene();
      },
    });
    toggleFullscreen(saved?.viewport_mode === "fullscreen");
  } catch (error) {
    showModelFallback(`${instance.fallback_description}\n\n模型运行信息：${error.message}`);
  }
}

function wireDetails(openIds) {
  dom.lessonContent.querySelectorAll("details[data-detail-id]").forEach((detail) => {
    detail.open = openIds.includes(detail.dataset.detailId);
    detail.addEventListener("toggle", () => {
      if (detail.open) {
        state.openDetailIds = [...new Set([
          ...state.openDetailIds,
          detail.dataset.detailId,
        ])];
      } else {
        state.openDetailIds = state.openDetailIds.filter(
          (id) => id !== detail.dataset.detailId,
        );
      }
      const kind = detail.open ? "detail_branch_open" : "detail_branch_close";
      state.modelRuntime?.dispatch(kind, {
        contentId: detail.dataset.parentContentId,
        detailBranchId: detail.dataset.detailId,
      });
      saveScene();
    });
  });
}

function reapplyOpenDetailBindings() {
  dom.lessonContent.querySelectorAll("details[open][data-detail-id]")
    .forEach((detail) => {
      state.modelRuntime?.dispatch("detail_branch_open", {
        contentId: detail.dataset.parentContentId,
        detailBranchId: detail.dataset.detailId,
      });
    });
  saveScene();
}

function observeContent() {
  state.observer?.disconnect();
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
    scheduleSessionFocus(nextId);
    saveScene();
  }, { threshold: [0.35, 0.6, 0.85], rootMargin: "-80px 0px -35% 0px" });
  dom.lessonContent.querySelectorAll("[data-content-id]").forEach((element) =>
    state.observer.observe(element)
  );
}

function scheduleSessionFocus(contentId) {
  const visibleIds = new Set();
  for (const step of state.learningSession?.baseline_steps || []) {
    if (!state.learningSession.revealed_step_ids.includes(step.id)) continue;
    visibleIds.add(step.id);
    for (const block of step.blocks) visibleIds.add(block.id);
  }
  for (const expansion of state.learningSession?.expansions || []) {
    visibleIds.add(expansion.id);
    for (const block of expansion.blocks) visibleIds.add(block.id);
  }
  if (
    !visibleIds.has(contentId)
    || contentId === state.learningSession?.active_content_id
  ) return;
  clearTimeout(state.focusTimer);
  state.focusTimer = setTimeout(async () => {
    try {
      state.learningSession = await sessionClient.focus(
        state.sessionAccess,
        state.learningSession.revision,
        contentId,
      );
      renderSessionContent();
      watchLearningSession();
    } catch (error) {
      await recoverSessionConflict(error);
    }
  }, 450);
}

function closeModule() {
  disposeActiveModule();
  state.moduleId = null;
  saveScene();
  showOnly(dom.atlasView);
  window.scrollTo({ top: 0, behavior: "instant" });
}

function disposeActiveModule() {
  state.observer?.disconnect();
  state.observer = null;
  state.modelRuntime?.dispose();
  state.modelRuntime = null;
  state.modelControls?.dispose();
  state.modelControls = null;
  state.sessionEvents?.close();
  state.sessionEvents = null;
  state.learningSession = null;
  state.sessionAccess = null;
  state.modulePayload = null;
  state.activeContentId = null;
  state.openDetailIds = [];
  dom.modelRoot.replaceChildren();
  dom.modelControls.replaceChildren();
  dom.modelControls.classList.add("is-hidden");
}

function toggleFullscreen(active) {
  if (active) state.fullscreenScrollTop = window.scrollY;
  dom.modelDock.classList.toggle("is-fullscreen", active);
  document.body.style.overflow = active ? "hidden" : "";
  if (!active && state.fullscreenScrollTop !== null) {
    const restoreTop = state.fullscreenScrollTop;
    state.fullscreenScrollTop = null;
    window.scrollTo({ top: restoreTop, behavior: "instant" });
    requestAnimationFrame(() => {
      window.scrollTo({ top: restoreTop, behavior: "instant" });
    });
  }
  saveScene();
}

function showModelFallback(message) {
  state.modelControls?.dispose();
  state.modelControls = null;
  dom.modelControls.replaceChildren();
  dom.modelControls.classList.add("is-hidden");
  dom.modelRoot.classList.add("is-hidden");
  dom.modelFallback.classList.remove("is-hidden");
  dom.modelFallback.textContent = message;
}

function saveScene() {
  if (!state.release || !state.package) return;
  sceneStore.save({
    schema_version: "classroom_scene_v1",
    package_id: state.package.package_id,
    release_version: state.release.version,
    course_id: state.courseId,
    chapter_id: state.chapterId,
    module_id: state.moduleId || undefined,
    content_id: state.activeContentId || undefined,
    scroll_top: state.moduleId ? Math.round(window.scrollY) : 0,
    open_detail_ids: state.openDetailIds,
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

function showToast(message) {
  dom.toast.textContent = message;
  dom.toast.classList.add("is-visible");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => dom.toast.classList.remove("is-visible"), 2600);
}

function escapeText(value) {
  const element = document.createElement("span");
  element.textContent = String(value ?? "");
  return element.innerHTML;
}

function escapeAttribute(value) {
  return escapeText(value).replaceAll('"', "&quot;");
}
