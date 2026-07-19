# Live Learning Session Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a production-capable classroom in which published module content unfolds as a stable baseline route and the Custom GPT can insert a newly designed detailed expansion at the learner's exact active point.

**Architecture:** Keep immutable V1 classroom releases as the initial baseline-content source, add a typed session/scene layer beside them, and expose learner and Studio session operations through the existing API namespaces so the deployed Custom GPT Action schema updates automatically. The browser renders one revealed baseline route, subscribes to session events, and inserts session-specific detailed expansions without republishing the classroom.

**Tech Stack:** Python 3.12, FastAPI, Pydantic 2, SQLite WAL, browser ES modules, Server-Sent Events, KaTeX, Node test runner, Playwright browser evidence.

## Global Constraints

- Ordinary `展开` reveals the next published baseline step and does not generate content.
- `这里没懂` creates a session-scoped detailed expansion at the exact active content target.
- No diagnosis, scoring, mastery, review scheduling, Boss, or training systems.
- Studio writes require Bearer authentication, idempotency keys, and expected revisions.
- Learner JavaScript never receives the Studio credential.
- Structural tests alone are insufficient; browser evidence must exercise a real baseline reveal and detailed expansion.

---

### Task 1: Typed Learning Session Domain and SQLite Repository

**Files:**
- Create: `backend/app/classroom/session_models.py`
- Create: `backend/app/classroom/session_repository.py`
- Test: `backend/tests/test_learning_session_repository.py`

**Interfaces:**
- Produces: `LearningSession`, `DetailedExpansion`, `ScenePatch`, `SessionRepository.create()`, `get()`, `reveal()`, `apply_patch()`, and `list_recent()`.

- [ ] Write repository tests for creation, stable baseline IDs, reveal, exact-target expansion, revision conflicts, idempotent retry, nested expansion, and forbidden learner-analysis fields.
- [ ] Run the tests and confirm failure because the session modules do not exist.
- [ ] Implement strict Pydantic models and transactional SQLite storage in WAL mode.
- [ ] Run repository tests and the complete Python suite.
- [ ] Commit the domain and repository.

### Task 2: Session Service and API Surfaces

**Files:**
- Create: `backend/app/classroom/sessions.py`
- Modify: `backend/app/api/classroom/v1/router.py`
- Modify: `backend/app/api/studio/v1/router.py`
- Modify: `backend/app/api/studio/v1/schemas.py`
- Modify: `backend/app/classroom/authoring.py`
- Test: `backend/tests/test_learning_session_api.py`
- Test: `backend/tests/test_studio_api.py`

**Interfaces:**
- Produces learner operations `createLearningSession`, `getLearningSession`, `revealLearningStep`, and `streamLearningSessionEvents`.
- Produces Studio operations `listLearningSessions`, `getStudioLearningSession`, `patchLearningSessionScene`, and `returnLearningSessionExpansion`.

- [ ] Write failing learner API tests for session creation, reveal, snapshot restore, and SSE replay.
- [ ] Write failing Studio API tests for discovery, authenticated patching, automatic target location, conflict recovery data, and Action operation IDs.
- [ ] Implement services, routers, error mapping, and workspace session summaries.
- [ ] Run focused API tests and the complete Python suite.
- [ ] Commit the API surface.

### Task 3: Stable Baseline Scene Renderer

**Files:**
- Create: `frontend/classroom/session-client.js`
- Create: `frontend/classroom/scene-runtime.js`
- Create: `frontend/classroom/scene-renderer.js`
- Test: `frontend/classroom/session-runtime.test.mjs`
- Modify: `frontend/classroom/app.js`
- Modify: `frontend/classroom/index.html`
- Modify: `frontend/classroom/styles.css`

**Interfaces:**
- Consumes learner session snapshots and events.
- Produces a module header, revealed baseline steps, one `继续展开` control, exact active-target tracking, detailed expansion branches, and parent return.

- [ ] Write failing Node tests for baseline projection, one-step reveal, exact expansion placement, nested expansion, and parent return.
- [ ] Run tests and confirm missing modules fail.
- [ ] Implement pure scene projection and patch functions.
- [ ] Wire session creation, active-target updates, SSE reconnect, and DOM rendering into the classroom.
- [ ] Run all Node and Python tests.
- [ ] Commit the session frontend.

### Task 4: Reliable Content and Mathematics Rendering

**Files:**
- Modify: `frontend/classroom/content-renderer.js`
- Modify: `frontend/classroom/content-renderer.test.mjs`
- Modify: `frontend/classroom/index.html`
- Modify: `frontend/classroom/styles.css`
- Modify: `backend/app/classroom/models.py`
- Modify: `backend/app/classroom/validation.py`
- Test: `backend/tests/test_classroom_validation.py`

**Interfaces:**
- Produces deterministic rendering for all accepted block payloads and KaTeX-backed formula rendering with readable fallback.

- [ ] Add failing tests for GPT-shaped `comparison.items`, multi-formula explanation payloads, nested LaTeX, empty required fields, and unknown payload keys.
- [ ] Confirm current blank output and validation gaps.
- [ ] Add compatible typed payload validation without breaking stored V1 releases.
- [ ] Replace handwritten formula formatting with KaTeX hooks and safe fallback text.
- [ ] Run complete test suites.
- [ ] Commit rendering and validation.

### Task 5: Teaching Model Visibility Gate

**Files:**
- Modify: `tools/capture_model_preview.cjs`
- Modify: `backend/app/classroom/model_authoring.py`
- Modify: `backend/tests/test_teaching_model_authoring.py`
- Modify: `backend/tests/test_teaching_model_preview.py`

**Interfaces:**
- Produces preview report fields `visible_element_count`, `painted_bounds`, and `state_visual_delta`.

- [ ] Add failing tests that reject a lifecycle-complete no-op model.
- [ ] Extend browser preview measurements and registration checks.
- [ ] Verify reference models remain registerable.
- [ ] Run complete suites and commit.

### Task 6: End-to-End Classroom Evidence and Production Cutover

**Files:**
- Create: `tools/generate_live_learning_session_evidence.py`
- Create: `docs/preview-artifacts/live-learning-session/`
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-07-19-live-learning-session-design.md`

**Interfaces:**
- Produces browser screenshots and a machine-readable report covering atlas entry, fixed reveal, GPT-style detailed expansion, nested expansion, return, formula rendering, and visible model state.

- [ ] Write the evidence scenario against a temporary real server and real browser.
- [ ] Run it and fix every visible blank, overflow, formula, or state-continuity failure.
- [ ] Run complete Python and Node suites plus the production integration tests.
- [ ] Mark the design implemented only after evidence passes.
- [ ] Commit, push the branch, deploy the saved result, and verify the production URL.
