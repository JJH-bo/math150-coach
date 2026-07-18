# Teaching Model and Preview Loop Design

> Date: 2026-07-18
> Status: approved by the user's standing instruction to continue Route Two
> Parent design: `2026-07-18-ai-classroom-redesign-design.md`
> Project: B

## 1. Outcome

Project B gives the Custom GPT a controlled teaching-model workshop and a
real-browser preview loop. GPT can create or revise model source, validate its
declared teaching vocabulary, render a scenario in an isolated browser,
inspect a screenshot and diagnostics, register an immutable model version,
bind classroom content to that version, publish the classroom, and replay the
same states in the learner runtime.

The project still does not score, diagnose, recommend, infer mastery, schedule
review, or create challenge gates.

## 2. Alternatives Considered

### Adapt the existing Three.js challenge universe

Rejected. Its scene graph, controls, labels, progression, Boss visuals, and
runtime calls are coupled to the legacy Challenge API. Reusing it as the model
host would make the new classroom depend on training state.

### Store only model manifests and return a manual preview URL

Rejected. A schema-only registry would let GPT describe models but would not
prove that source code mounts, renders, replays, or disposes correctly. It
would also provide no durable screenshot or runtime evidence.

### Isolated model registry, sandbox host, and browser capture worker

Selected. Models use a small browser contract, execute in a sandboxed iframe,
and can be captured by a replaceable Playwright worker. The backend owns
immutable source and metadata, jobs, artifacts, validation, registration, and
runtime delivery without importing the legacy engine.

## 3. Model Contract

A teaching-model draft contains:

- a strict, self-describing manifest;
- one UTF-8 JavaScript ES module;
- an expected draft revision and deterministic content hash.

The manifest declares:

- stable model ID, title, purpose, domains, and contract version;
- typed parameters with defaults and optional numeric limits or choices;
- named states;
- actions with typed payload fields;
- bindable visual targets;
- allowed learner interactions;
- supported viewport modes and quality profiles;
- deterministic preview scenarios;
- a readable fallback description.

The ES module exports:

```javascript
export function createTeachingModel(context) {
  return {
    mount(initialState) {},
    update(nextState) {},
    perform(action, payload) {},
    pause() {},
    resume() {},
    reset() {},
    snapshot() {},
    dispose() {},
  };
}
```

`context` exposes only the sandbox root, a tracked animation-frame scheduler,
tracked event-listener helpers, viewport information, and a structured log
function. The model does not receive authentication credentials, server file
access, learner records, or legacy challenge state.

All lifecycle methods are required except `snapshot`, which remains required
for registered Project B models so deterministic replay can be checked.

## 4. Registry and Authoring

Model drafts are mutable JSON and source artifacts stored under the classroom
data root. Updates use expected revisions and Studio idempotency keys.

Registration:

1. parses and validates the manifest;
2. statically checks the JavaScript export and forbidden server-oriented
   capabilities;
3. validates scenario states, actions, parameters, and target references;
4. requires a successful real preview for the current draft content hash;
5. writes an immutable version `m-<sha256 prefix>`;
6. returns a receipt containing model ID, version, hashes, and runtime URLs.

Registered versions are never overwritten. Rollback is achieved by binding a
classroom draft to an older immutable version and publishing that classroom
release; model source history remains intact.

The Studio exposes stable Action operations to list and inspect registered
models, create/read/update/validate model drafts, request and inspect preview
jobs, download artifacts, and register versions.

## 5. Content-to-Model Binding

`ClassroomPackage` gains typed model instances and bindings.

A model instance pins:

- `model_id` and immutable `model_version`;
- initial state;
- parameter overrides;
- viewport mode and quality profile;
- allowed learner interactions;
- fallback presentation.

A binding connects one stable content block to one model instance. Project B
supports these triggers:

- block enter and leave;
- block activation;
- detail branch open and close;
- explicit classroom control;
- learner parameter change.

It supports these effects:

- set state;
- perform a declared action;
- update parameters;
- play, pause, reset, or step;
- highlight or clear a declared target;
- save or restore a state snapshot.

Every temporary trigger must declare `restore_previous` or a return effect.
Validation rejects missing content targets, unknown instances, unregistered
versions, invalid parameters, unknown states/actions/targets, and missing
return behavior. Bindings describe teaching synchronization only; they do not
record or interpret learner performance.

## 6. Real Preview Jobs

Creating a preview writes a durable job record and returns immediately. A
background worker:

1. snapshots the exact draft hash and scenario;
2. builds a self-contained preview document;
3. opens it in a fresh browser context with networking blocked;
4. waits for the model host readiness contract;
5. captures a PNG at the requested viewport;
6. collects console messages, lifecycle state, snapshot output, timing, and
   active tracked resources;
7. disposes the model and verifies tracked frames/listeners return to zero;
8. writes `request.json`, `preview.html`, `screenshot.png`, and `report.json`;
9. atomically marks the job succeeded or failed.

Jobs remain queryable after request timeouts. Artifact responses are
authenticated Studio operations. A missing Node, browser, or Playwright
installation produces a structured failed job with a retryable environment
error rather than a fake preview.

Model source runs only inside a sandboxed iframe with a restrictive content
security policy. Preview networking is blocked. The browser uses an ephemeral
profile. Timeouts and payload limits prevent a faulty animation from holding a
worker indefinitely.

## 7. Learner Runtime

The Classroom Runtime exposes immutable registered model manifests and source
modules by exact ID and version. Module responses include only the model
instances and bindings referenced by that module.

The reusable browser model host is independent of Studio and legacy Challenge
code. It:

- validates the module export;
- owns mount, update, action, pause/resume, reset, snapshot, and disposal;
- tracks animation frames and event listeners;
- reports runtime errors without exposing Studio internals;
- falls back to the model's readable description when rendering fails.

Project B provides two registered reference paths:

- `limit-neighborhood-2d`: a canvas model connecting a limit formula to
  neighborhoods, approach points, a removable hole, and the target value;
- `binary-search-array`: an algorithmic canvas model exposing low, high, mid,
  compare, found, and reset states.

These are reference teaching instruments, not exercises.

## 8. Data and API Boundaries

New data lives under:

```text
<CLASSROOM_DATA_ROOT>/
  model-drafts/
  models/<model-id>/versions/<version>/
  preview-jobs/
  preview-artifacts/
```

New Studio operations remain under `/api/studio/v1`. Registered learner-safe
model reads remain under `/api/classroom/v1`.

The default application never executes model JavaScript in the Python process.
The only execution path is the isolated browser preview or learner browser
host.

## 9. Validation and Failure Semantics

Validation issues contain severity, code, object path, and a concrete message.
Preview jobs contain status, timestamps, source hashes, exact viewport and
scenario, artifact names, retryability, and structured errors.

Registration fails when:

- validation has any error;
- no successful preview matches the current draft hash;
- lifecycle disposal leaked tracked resources;
- the preview reported uncaught errors;
- the expected draft revision is stale.

Warnings do not block registration but remain in the receipt and immutable
version metadata.

## 10. Testing

Python tests cover strict schemas, deterministic versions, atomic persistence,
idempotent updates, registration gates, binding validation, runtime
projections, API authentication, and stable operation IDs.

Node tests cover the generic host contract and deterministic model math/state
logic without a browser.

Browser verification uses the real preview worker for desktop and mobile
viewports, inspects the generated PNG dimensions, checks console/runtime
reports, and verifies zero tracked resources after disposal.

The full Python suite and retained legacy evals must stay green. New classroom
and model code must not import challenge, diagnosis, scoring, mastery, review,
or training modules.

## 11. Project B Completion Gate

Project B is complete when:

1. GPT can create, edit, validate, preview, inspect, and register model code
   through stable Studio operations.
2. Registered versions are immutable and learner-readable by exact version.
3. A classroom package can pin model instances and validated bindings.
4. The 2D limit and algorithmic binary-search reference models both replay
   deterministic scenarios.
5. At least one desktop and one mobile real-browser artifact are generated.
6. Preview reports contain exact source context and lifecycle disposal
   evidence.
7. Registration refuses stale, unvalidated, unpreviewed, or leaking models.
8. No new code depends on the legacy learner-analysis or challenge product.

