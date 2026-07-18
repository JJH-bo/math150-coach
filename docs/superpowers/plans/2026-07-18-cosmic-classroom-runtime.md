# Cosmic Classroom Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the learner-facing cosmic atlas and reading-first classroom stage over the published Classroom Runtime and teaching-model contracts.

**Architecture:** Keep data projection, scene persistence, binding transitions, semantic block rendering, and application orchestration in separate browser modules. Mount a build-free static application at `/classroom` for learner/mixed profiles. Use the Project B model host for exact-version models and verify the full experience in real Chrome at desktop and mobile sizes.

**Tech Stack:** HTML, CSS, browser ES modules, Canvas 2D, FastAPI StaticFiles, Node test runner, Playwright, pytest.

## Global Constraints

- The learner frontend calls only `/api/classroom/v1`.
- No answer input, scoring, diagnosis, mastery, review, recommendation, challenge, Boss, or performance progress appears in new code.
- Core modules are complete destinations, never visible task chains.
- Detail branches open in place and restore binding state.
- Persist only keys declared by `classroom_scene_v1`.
- Dispose the active model before mounting another.
- Desktop and mobile browser evidence is mandatory.
- The accepted design is `docs/superpowers/specs/2026-07-18-cosmic-classroom-runtime-design.md`.

### Task 1: Pure Atlas, Scene, and Binding Modules

**Files:**
- Create: `frontend/classroom/atlas.js`
- Create: `frontend/classroom/scene-store.js`
- Create: `frontend/classroom/bindings.js`
- Create: `frontend/classroom/runtime-core.test.mjs`

**Interfaces:**
- `projectAtlas(package)` returns course/chapter/module destinations and relations.
- `sanitizeSceneSnapshot(value)` and `createSceneStore(storage)`.
- `createBindingRuntime(bindings, controller)` applies triggers with snapshot stacks.

- [ ] Write Node tests for arbitrary module counts, non-clickable decoration
  separation, forbidden snapshot-key removal, version mismatch reset, block
  enter state effects, detail open/close restore, and controller disposal.
- [ ] Run Node tests and verify missing-module RED.
- [ ] Implement the three pure modules without DOM dependencies.
- [ ] Run Node tests GREEN and commit `Build classroom runtime core`.

### Task 2: Semantic Content Renderer

**Files:**
- Create: `frontend/classroom/content-renderer.js`
- Create: `frontend/classroom/content-renderer.test.mjs`

**Interfaces:**
- `renderModule(module)` returns trusted application-owned HTML with escaped
  authored strings, stable `data-content-id` targets, and recursive details.

- [ ] Write RED tests for prose, formula adjacency, derivation steps, worked
  examples, comparisons, code, tables, groups, model references, recursive
  detail branches, and HTML escaping.
- [ ] Implement one focused renderer per block kind plus readable unknown-kind
  fallback.
- [ ] Run GREEN and commit `Render AI classroom content blocks`.

### Task 3: Classroom Application and Visual System

**Files:**
- Create: `frontend/classroom/index.html`
- Create: `frontend/classroom/styles.css`
- Create: `frontend/classroom/app.js`
- Copy: `frontend/model-runtime/host.js` to `frontend/classroom/model-runtime/host.js`
- Create: `frontend/classroom/static-contract.test.mjs`

**Interfaces:**
- Atlas screen loads catalog/package and opens module.
- Stage mounts content, exact-version models, bindings, details, full-screen
  viewport, preferences, and scene restoration.

- [ ] Write static-contract RED tests for landmarks, module buttons, model
  viewport, detail event hooks, reduced motion, full-screen return, runtime-only
  API base, and forbidden product language.
- [ ] Implement accessible HTML shell and responsive CSS.
- [ ] Implement application orchestration with `IntersectionObserver`,
  `details.toggle`, model source fetch, Blob import through the host, local
  storage restoration, and disposal.
- [ ] Run all frontend Node tests GREEN and commit `Build cosmic classroom stage`.

### Task 4: Static Mount and Demo Bootstrap

**Files:**
- Modify: `backend/app/main.py`
- Create: `tools/bootstrap_ai_classroom.py`
- Create: `backend/tests/test_cosmic_classroom_mount.py`

**Interfaces:**
- Learner/mixed expose `/classroom`; internal does not.
- Bootstrap installs model seeds, creates the sample classroom draft, validates
  it against the registry, publishes it, and is idempotent for the same release.

- [ ] Write pytest RED for profile mounting, static assets, no `/api/challenge`
  reference, bootstrap catalog availability, and active bound module response.
- [ ] Implement conditional static mount and bootstrap tool.
- [ ] Run GREEN and commit `Mount learner AI classroom`.

### Task 5: Browser End-to-End Evidence

**Files:**
- Create: `tools/capture_cosmic_classroom.cjs`
- Create: `tools/generate_project_c_evidence.py`
- Create: `backend/tests/test_cosmic_classroom_browser.py`
- Generate: `docs/preview-artifacts/project-c/*`

**Interfaces:**
- Browser runner launches a temporary mixed-profile server over bootstrapped
  data and returns screenshots plus structured interaction reports.

- [ ] Write environment-gated browser RED test.
- [ ] Implement capture for desktop atlas, desktop module/detail/full-screen,
  restored reload, and mobile module/model dock.
- [ ] Assert zero console/page errors, no horizontal overflow, correct model
  snapshot transitions, preserved scroll/detail state, and no challenge API
  request.
- [ ] Generate and visually inspect checked-in PNG/report evidence.
- [ ] Run GREEN and commit `Verify cosmic classroom experience`.

### Task 6: Project C Completion

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-07-18-cosmic-classroom-runtime-design.md` only if evidence requires a documented correction.

- [ ] Document bootstrap, run, learner URL, snapshot boundary, model fallback,
  reduced motion, and browser evidence commands.
- [ ] Run all Python tests with real browser environment.
- [ ] Run all frontend Node tests.
- [ ] Run retained legacy evals and new-code legacy-import/text searches.
- [ ] Run `git diff --check`, inspect evidence, commit, and push.

## Completion Gate

- Course, chapter, and complete-module navigation works.
- The sample module renders content plus exact-version model.
- Local details and temporary bindings restore context.
- Full-screen model return and reload continuity work.
- Snapshot contains only scene-continuity keys.
- Desktop/mobile evidence is readable and error-free.
- No new learner path uses legacy challenge or learner-analysis behavior.

