# AI Classroom Learning Quality Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every uploaded chapter publish only when it is fully covered, organized by indispensable core questions, teachable to a first-time learner, equipped with substantive detailed expansions, correctly rendered, and backed by meaningful interaction where a model is used.

**Architecture:** Extend the immutable classroom package with a source-to-knowledge-to-content evidence graph and explicit pedagogical contracts. Enforce those contracts in the existing authoring validator, add browser and model semantic gates, render the richer contracts in the learner UI, then update the Custom GPT instructions and rebuild active releases under the new contract.

**Tech Stack:** FastAPI, Pydantic v2, pytest, vanilla ES modules, Node test runner, Playwright, MathJax, SQLite session store.

## Global Constraints

- No diagnosis, scoring, mastery, review scheduling, Boss challenges, training tasks, or learner profiles.
- Ordinary learning reveals only the next immutable baseline segment in the active module.
- Detailed expansion is local, substantive, nestable, and reconnects to the fixed route.
- Models are optional when they do not improve understanding; any declared model must be visible and genuinely interactive.
- Existing invalid active releases must not remain silently available.

---

### Task 1: Source coverage evidence graph

**Files:**
- Modify: `backend/app/classroom/models.py`
- Modify: `backend/app/classroom/validation.py`
- Modify: `backend/tests/classroom_fixtures.py`
- Modify: `backend/tests/test_classroom_validation.py`

**Interfaces:**
- Produces `SourceSection`, `KnowledgePoint`, `KnowledgeCoverage`, `CoverageAudit`, and chapter-level `source_manifest`.
- Validator emits stable error codes for every orphan, missing mapping, invalid excerpt, and unresolved audit item.

- [ ] Write failing model and validator tests for complete coverage and each missing edge.
- [ ] Run focused tests and confirm failures are caused by absent contracts.
- [ ] Implement strict models and graph validation.
- [ ] Update the canonical test fixture to a complete valid source graph.
- [ ] Run focused and full backend tests.

### Task 2: Core-module and novice-route teaching contract

**Files:**
- Modify: `backend/app/classroom/models.py`
- Modify: `backend/app/classroom/validation.py`
- Modify: `backend/app/classroom/sessions.py`
- Modify: `backend/tests/test_classroom_validation.py`
- Modify: `backend/tests/test_learning_session_repository.py`

**Interfaces:**
- Core modules expose `core_question`, `chapter_role`, `why_indispensable`, dependencies, responsible knowledge points, and `novice_bridge`.
- Baseline steps are projected from semantic learning segments rather than arbitrary top-level blocks.

- [ ] Write failing tests for overview-as-module, missing core problem, dependency cycles, empty bridges, heading-only steps, and uncovered core points.
- [ ] Verify every test fails for the intended missing rule.
- [ ] Implement models and teaching validator.
- [ ] Project one baseline step per learning segment and retain module orientation outside the step count.
- [ ] Run focused and full backend tests.

### Task 3: Static and live detailed-expansion quality

**Files:**
- Modify: `backend/app/classroom/models.py`
- Modify: `backend/app/classroom/session_models.py`
- Modify: `backend/app/classroom/validation.py`
- Modify: `backend/tests/test_classroom_validation.py`
- Modify: `backend/tests/test_learning_session_api.py`

**Interfaces:**
- Static and live expansions share trigger, obstacle, alternate representation, bridge steps, substantive blocks, and return connection.

- [ ] Write failing tests for one-sentence, same-representation, missing bridge, missing return, and module-without-detail cases.
- [ ] Implement the shared expansion quality checks.
- [ ] Update live patch schemas and API examples.
- [ ] Run focused and full backend tests.

### Task 4: Strict content renderer and learner layout

**Files:**
- Modify: `frontend/classroom/content-renderer.js`
- Modify: `frontend/classroom/scene-renderer.js`
- Modify: `frontend/classroom/app.js`
- Modify: `frontend/classroom/index.html`
- Modify: `frontend/classroom/styles.css`
- Modify: `frontend/test/content-renderer.test.mjs`
- Modify: `frontend/test/scene-renderer.test.mjs`

**Interfaces:**
- Every renderer consumes the same validated shape.
- Unsupported or malformed content raises a visible authoring error and fails browser verification instead of producing blank cards.
- Module header and route navigation expose the core question, role, prerequisites, and current segment.

- [ ] Add failing tests for string comparisons, model-reference instance IDs, empty rendered cards, semantic module headers, and route navigation.
- [ ] Implement strict normalization/rendering and accessible navigation.
- [ ] Run all Node tests and browser smoke tests.

### Task 5: Generated model controls and semantic preview gate

**Files:**
- Modify: `frontend/classroom/app.js`
- Create: `frontend/classroom/model-controls.js`
- Modify: `frontend/classroom/styles.css`
- Modify: `tools/capture_model_preview.cjs`
- Modify: `backend/app/classroom/model_authoring.py`
- Modify: `backend/app/classroom/model_contracts.py`
- Modify: `backend/tests/test_teaching_model_preview.py`
- Create: `frontend/test/model-controls.test.mjs`

**Interfaces:**
- `renderModelControls(manifest, instance, onChange)` generates controls for allowed parameters and actions.
- Preview reports initial/final visual hashes, pixel variance, initial/final snapshots, and `interaction_changed`.

- [ ] Write failing tests proving a no-op model, blank canvas, unchanged interaction, and missing learner controls are rejected.
- [ ] Implement generic controls and snapshot persistence.
- [ ] Capture before/after model evidence and require meaningful change.
- [ ] Run model, Node, and Playwright tests.

### Task 6: Custom GPT autonomous authoring contract

**Files:**
- Modify: `docs/custom-gpt-instructions.md`
- Modify: `backend/app/classroom/authoring.py`
- Modify: `backend/app/api/studio/v1/router.py`
- Modify: `backend/tests/test_studio_api.py`

**Interfaces:**
- Workspace and validation responses expose coverage and teaching error repair guidance.
- GPT instructions require two-pass source extraction and automated repair before publish.

- [ ] Add failing schema/capability tests for the new quality contract.
- [ ] Update workspace capabilities, action descriptions, and instructions.
- [ ] Regenerate and test the public Action schema.

### Task 7: Rebuild active classrooms and end-to-end verification

**Files:**
- Modify: `backend/classroom_data/seed/calculus-foundations.json`
- Create or modify: production migration/rebuild artifacts under `backend/classroom_data`
- Modify: `backend/tests/test_cosmic_classroom_browser.py`
- Create: `docs/preview-artifacts/learning-quality-contract/*`

**Interfaces:**
- All active packages conform to the current contract.
- Fourier teaching model has real rendering and controls or is removed until it does.

- [ ] Re-author calculus and Fourier releases with complete coverage evidence.
- [ ] Validate every release under the current contract.
- [ ] Verify desktop/mobile rendering, MathJax, no blank components, staged expansion, static/live details, model controls, and interaction deltas.
- [ ] Commit, push, deploy, update the Custom GPT configuration, and run a real upload-to-classroom smoke test.
