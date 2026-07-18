# Teaching Model and Preview Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the Custom GPT author, validate, real-browser preview, register, bind, publish, and replay immutable teaching models without any legacy challenge dependency.

**Architecture:** Add a strict model contract and atomic registry beside the existing classroom repository. Run authored JavaScript only inside a sandboxed browser host; a replaceable Playwright worker produces durable preview jobs and artifacts. Extend classroom packages with typed model instances and bindings, then expose authoring through Studio and exact-version reads through Classroom Runtime.

**Tech Stack:** Python 3, FastAPI, Pydantic v2, pytest, browser ES modules, Canvas 2D, Node.js, Playwright, Chrome or Edge.

## Global Constraints

- New model, preview, binding, and runtime code must not import challenge, diagnosis, scoring, mastery, question-bank, review, rollback/forward, or training modules.
- Python never evaluates authored JavaScript.
- Preview JavaScript runs in a sandboxed iframe with networking blocked and an ephemeral browser context.
- Model drafts are revisioned; registered versions are immutable and named `m-<sha256 prefix>`.
- Registration requires validation plus a successful preview matching the current draft content hash.
- Temporary bindings require explicit return behavior.
- Preview jobs and artifacts are durable and recoverable after an Action request ends.
- Runtime reads expose registered exact versions only; Studio draft source and preview artifacts remain authenticated.
- Reference models are teaching instruments, not exercises, tests, or learner-analysis features.
- The accepted design is `docs/superpowers/specs/2026-07-18-teaching-model-preview-loop-design.md`.

---

### Task 1: Teaching Model Contract

**Files:**
- Create: `backend/app/classroom/model_contracts.py`
- Test: `backend/tests/test_teaching_model_contracts.py`

**Interfaces:**
- Produces `TeachingModelManifest`, `ModelParameterSpec`, `ModelStateSpec`,
  `ModelActionSpec`, `ModelScenario`, `ModelDraftRecord`,
  `RegisteredModelRecord`, `PreviewJobRecord`, and `model_version()`.

- [ ] **Step 1: Write failing contract tests**

Test strict manifest parsing, invalid parameter defaults, duplicate state/action
IDs, deterministic version hashing, required lifecycle export names, and
preview-job status fields.

- [ ] **Step 2: Verify RED**

Run:

```powershell
python -m pytest backend/tests/test_teaching_model_contracts.py -q
```

Expected: import failure for `app.classroom.model_contracts`.

- [ ] **Step 3: Implement strict contracts**

Use Pydantic `extra="forbid"` models. Parameters support `number`, `integer`,
`boolean`, `string`, and `choice`; numeric bounds and choices are optional but
validated against defaults. State, action, target, scenario, interaction,
viewport, and quality identifiers are stable strings. `model_version()` hashes
the canonical `{manifest, source}` value.

- [ ] **Step 4: Verify GREEN and commit**

Run the contract tests and commit:

```powershell
git add backend/app/classroom/model_contracts.py backend/tests/test_teaching_model_contracts.py
git commit -m "Define teaching model contract"
```

### Task 2: Atomic Model Draft and Registry Repository

**Files:**
- Create: `backend/app/classroom/model_repository.py`
- Test: `backend/tests/test_teaching_model_repository.py`

**Interfaces:**
- Produces `TeachingModelRepository`.
- Draft methods: `create_draft`, `get_draft`, `update_draft`.
- Registry methods: `register`, `get_registered`, `list_registered`.
- Preview methods: `put_preview_job`, `get_preview_job`,
  `artifact_path`, and `find_successful_preview`.

- [ ] **Step 1: Write failing repository tests**

Cover atomic UTF-8 writes, revision conflicts, path-safe IDs, immutable
registration, primary plus checked-in seed lookup, preview-job persistence, and
matching preview lookup by draft content hash.

- [ ] **Step 2: Verify RED**

Run the repository test file and expect an import failure.

- [ ] **Step 3: Implement repository**

Store drafts under `model-drafts`, registered versions under
`models/<model-id>/versions/<version>`, jobs under `preview-jobs`, and artifacts
under `preview-artifacts/<job-id>`. Reuse canonical hashing and atomic
temporary-file replacement patterns from `ClassroomRepository`.

- [ ] **Step 4: Verify GREEN and commit**

```powershell
python -m pytest backend/tests/test_teaching_model_repository.py -q
git add backend/app/classroom/model_repository.py backend/tests/test_teaching_model_repository.py
git commit -m "Persist teaching model versions"
```

### Task 3: Model Validation and Registration Gate

**Files:**
- Create: `backend/app/classroom/model_validation.py`
- Create: `backend/app/classroom/model_authoring.py`
- Test: `backend/tests/test_teaching_model_authoring.py`

**Interfaces:**
- Produces `TeachingModelValidator.validate(manifest, source)`.
- Produces `TeachingModelAuthoringService` draft CRUD, validation, and
  registration methods.

- [ ] **Step 1: Write failing authoring tests**

Cover JavaScript lifecycle export checks, forbidden Node/server primitives,
scenario state/action/parameter references, idempotent draft creation/update,
stale revisions, registration without preview, preview hash mismatch,
registration with a successful leak-free preview, and immutable repeated
registration.

- [ ] **Step 2: Verify RED**

Run the test file and expect missing validation/authoring modules.

- [ ] **Step 3: Implement validation**

Validation requires the `createTeachingModel` export, all lifecycle method
names, valid scenario references, and no `require(`, `process.`, `child_process`,
`fs.`, `Deno.`, or dynamic network APIs. It returns field-level issues rather
than rewriting source.

- [ ] **Step 4: Implement authoring**

Use `IdempotencyLedger` for mutable operations. Registration checks expected
revision, validation, a successful preview for the exact content hash, zero
tracked resources after disposal, and no uncaught preview error.

- [ ] **Step 5: Verify GREEN and commit**

```powershell
python -m pytest backend/tests/test_teaching_model_authoring.py -q
git add backend/app/classroom/model_validation.py backend/app/classroom/model_authoring.py backend/tests/test_teaching_model_authoring.py
git commit -m "Gate teaching model registration"
```

### Task 4: Typed Instances and Content Bindings

**Files:**
- Modify: `backend/app/classroom/models.py`
- Modify: `backend/app/classroom/validation.py`
- Modify: `backend/app/classroom/authoring.py`
- Modify: `backend/tests/classroom_fixtures.py`
- Create: `backend/tests/test_classroom_model_bindings.py`

**Interfaces:**
- Produces `ContentModelBinding`, `BindingTrigger`, `BindingEffect`, expanded
  `ModelInstanceReference`, and `ClassroomPackage.model_bindings`.
- `ClassroomPackageValidator` optionally consumes a registered-model resolver.

- [ ] **Step 1: Write failing binding tests**

Test a valid block-enter/set-state binding, arbitrary instance counts, unknown
content targets, unknown instances, unregistered versions, invalid parameters,
unknown states/actions/targets, and a temporary detail-open binding without
return behavior.

- [ ] **Step 2: Verify RED**

Run the binding tests and expect missing binding models.

- [ ] **Step 3: Implement typed binding models**

Triggers and effects use enums plus strict payload fields. Instance fields
include parameters, viewport mode, quality profile, interactions, and readable
fallback. Temporary triggers expose `restore_previous` and optional
`return_effect`.

- [ ] **Step 4: Extend validation and authoring wiring**

Collect all recursive content IDs, resolve every pinned model, and validate
instance and binding vocabulary against the immutable manifest. The default
Studio authoring service receives the model registry rooted at
`CLASSROOM_DATA_ROOT`.

- [ ] **Step 5: Verify GREEN and commit**

```powershell
python -m pytest backend/tests/test_classroom_model_bindings.py backend/tests/test_classroom_validation.py backend/tests/test_classroom_authoring.py -q
git add backend/app/classroom backend/tests/classroom_fixtures.py backend/tests/test_classroom_model_bindings.py backend/tests/test_classroom_validation.py backend/tests/test_classroom_authoring.py
git commit -m "Bind classroom content to teaching models"
```

### Task 5: Sandboxed Browser Host and Reference Models

**Files:**
- Create: `frontend/model-runtime/host.js`
- Create: `frontend/model-runtime/preview.html`
- Create: `frontend/model-runtime/preview.js`
- Create: `frontend/model-runtime/preview.css`
- Create: `frontend/model-runtime/host.test.mjs`
- Create: `backend/classroom_data/model_seed/limit-neighborhood-2d/manifest.json`
- Create: `backend/classroom_data/model_seed/limit-neighborhood-2d/source.js`
- Create: `backend/classroom_data/model_seed/binary-search-array/manifest.json`
- Create: `backend/classroom_data/model_seed/binary-search-array/source.js`
- Create: `frontend/model-runtime/reference-models.test.mjs`

**Interfaces:**
- Browser host consumes source, manifest, scenario, and viewport.
- Browser host produces readiness, snapshot, logs, timing, and disposal metrics.

- [ ] **Step 1: Write failing Node tests**

Load pure helpers from `host.js`; verify lifecycle method detection, parameter
merging, scenario command validation, and resource-counter behavior. Load the
two reference modules and verify deterministic snapshots for declared
scenarios.

- [ ] **Step 2: Verify RED**

Run with the bundled or system Node executable:

```powershell
node --test frontend/model-runtime/*.test.mjs
```

- [ ] **Step 3: Implement the generic host**

The parent preview page creates a CSP-restricted `sandbox="allow-scripts"`
iframe. The iframe imports model source from a Blob URL, provides tracked RAF
and listener helpers, runs the scenario, posts a ready report, and exposes a
dispose command. It never calls Studio or Challenge APIs.

- [ ] **Step 4: Implement both reference models**

`limit-neighborhood-2d` uses Canvas 2D to show the function, removable hole,
target value, and adjustable neighborhood. `binary-search-array` renders the
active interval, midpoint, comparisons, and found state. Both use the complete
lifecycle contract and readable fallback.

- [ ] **Step 5: Verify GREEN and commit**

```powershell
node --test frontend/model-runtime/*.test.mjs
git add frontend/model-runtime backend/classroom_data/model_seed
git commit -m "Build sandboxed teaching model host"
```

### Task 6: Durable Real-Browser Preview Worker

**Files:**
- Create: `tools/capture_model_preview.cjs`
- Create: `backend/app/classroom/preview.py`
- Test: `backend/tests/test_teaching_model_preview.py`

**Interfaces:**
- Produces `TeachingModelPreviewService.request_preview`,
  `run_preview`, `get_preview`, and `artifact`.
- Node worker consumes a request JSON path and writes PNG/report artifacts.

- [ ] **Step 1: Write failing preview tests**

Use a fake runner for durable queued/succeeded/failed transitions and artifact
path safety. Add an environment-gated real-browser test that runs the checked-in
limit model at `1280x800`, checks PNG dimensions/signature, then verifies the
report contains a deterministic snapshot and zero active resources after
disposal.

- [ ] **Step 2: Verify RED**

Run the preview test file and expect missing preview service.

- [ ] **Step 3: Implement preview service and worker**

The service writes the exact manifest, source, scenario, viewport, draft hash,
and preview document before invoking the worker. The worker uses Playwright
with an explicit browser executable when configured, blocks network requests,
waits for `window.__teachingPreviewReady`, screenshots, calls disposal, and
writes structured JSON. Failures atomically update the durable job.

- [ ] **Step 4: Verify fake and real GREEN**

Set:

```powershell
$env:MODEL_PREVIEW_NODE = "<node executable>"
$env:NODE_PATH = "<directory containing playwright>"
$env:MODEL_PREVIEW_BROWSER = "<chrome or edge executable>"
python -m pytest backend/tests/test_teaching_model_preview.py -q
```

- [ ] **Step 5: Commit**

```powershell
git add tools/capture_model_preview.cjs backend/app/classroom/preview.py backend/tests/test_teaching_model_preview.py
git commit -m "Generate durable browser model previews"
```

### Task 7: Studio and Runtime APIs

**Files:**
- Modify: `backend/app/api/studio/v1/schemas.py`
- Modify: `backend/app/api/studio/v1/router.py`
- Modify: `backend/app/api/classroom/v1/router.py`
- Modify: `backend/app/classroom/runtime.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_teaching_model_studio_api.py`
- Create: `backend/tests/test_teaching_model_runtime_api.py`

**Interfaces:**
- Studio adds stable model draft, validation, preview, artifact, and
  registration operation IDs.
- Runtime adds exact-version model manifest and JavaScript source reads.

- [ ] **Step 1: Write failing API tests**

Verify Studio bearer authentication, idempotency headers, expected revisions,
202 preview receipts, job lookup, artifact media types, registration errors,
stable OpenAPI operation IDs, exact-version runtime source, and module
projection filtering of instances/bindings.

- [ ] **Step 2: Verify RED**

Run both API test files and expect route failures.

- [ ] **Step 3: Implement Studio routes**

Inject model authoring and preview service factories. Use `BackgroundTasks` for
preview execution. Return bounded receipts and existing structured API errors.

- [ ] **Step 4: Implement runtime routes**

Serve registered manifests as JSON and source as
`application/javascript; charset=utf-8`. Extend module projection with only
relevant instances and bindings.

- [ ] **Step 5: Verify GREEN and commit**

```powershell
python -m pytest backend/tests/test_teaching_model_studio_api.py backend/tests/test_teaching_model_runtime_api.py backend/tests/test_studio_api.py backend/tests/test_classroom_runtime_api.py -q
git add backend/app/api backend/app/classroom/runtime.py backend/app/main.py backend/tests/test_teaching_model_studio_api.py backend/tests/test_teaching_model_runtime_api.py
git commit -m "Expose teaching model workshop APIs"
```

### Task 8: Seed Registration, Documentation, and Verification

**Files:**
- Create: `tools/register_seed_models.py`
- Modify: `backend/classroom_data/seed/calculus-foundations.json`
- Modify: `README.md`
- Test: `backend/tests/test_teaching_model_seed.py`

**Interfaces:**
- Produces two deterministic checked-in registered model versions and one
  sample classroom binding.

- [ ] **Step 1: Add seed registration test and tool**

The test loads both manifests/source files, validates them, derives versions,
registers them in a temporary registry, runs deterministic scenarios, and
validates the sample classroom's exact-version binding.

- [ ] **Step 2: Update the sample classroom**

Bind the limit formula/explanation block to a `limit-neighborhood-2d` instance.
Include readable fallback and explicit return behavior.

- [ ] **Step 3: Document the environment**

Document Node, Playwright, browser, preview environment variables, Action
operation groups, sandbox boundary, artifact locations, and local commands.

- [ ] **Step 4: Run Project B tests**

```powershell
python -m pytest backend/tests/test_teaching_model_contracts.py backend/tests/test_teaching_model_repository.py backend/tests/test_teaching_model_authoring.py backend/tests/test_classroom_model_bindings.py backend/tests/test_teaching_model_preview.py backend/tests/test_teaching_model_studio_api.py backend/tests/test_teaching_model_runtime_api.py backend/tests/test_teaching_model_seed.py -q
```

- [ ] **Step 5: Generate desktop and mobile artifacts**

Run the real worker for the limit model at `1280x800` and binary-search model at
`390x844`. Inspect both PNGs and reports.

- [ ] **Step 6: Run all regressions and isolation checks**

```powershell
python -m pytest -q
python evals/run_evals.py
rg -n "from app\\.(challenge|services|training|logic_graph)|import app\\.(challenge|services|training|logic_graph)" backend/app/classroom backend/app/api/studio backend/app/api/classroom
git diff --check
```

- [ ] **Step 7: Commit and push**

```powershell
git add README.md backend/classroom_data/seed/calculus-foundations.json tools/register_seed_models.py backend/tests/test_teaching_model_seed.py
git commit -m "Document teaching model preview workflow"
git push origin HEAD
```

## Project B Completion Gate

- Model source is authored only through revisioned Studio drafts.
- Validation and preview failures are structured and recoverable.
- A successful matching browser preview is required before registration.
- Registered model source and manifests are immutable and version pinned.
- Content bindings are typed, target checked, and return safe.
- Desktop and mobile PNG artifacts come from a real browser.
- Lifecycle reports show zero tracked resources after disposal.
- The 2D and algorithmic reference paths replay deterministically.
- Runtime model reads and module projections contain no Studio secret or
  learner-analysis state.
- Full Python, Node, legacy eval, and import-isolation checks pass.

