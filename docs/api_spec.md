# API Spec

Phase 3 exposes the existing Phase 1-2.2 engines through a minimal internal/dev API.

Phase 4.0-lite keeps that frozen `/api/v1` contract and adds a separate learner-safe public API under `/api/learner/v1`. Learner routes no longer accept trusted `Question` payloads; they load trusted question data from the server-side catalog by `question_id`.

Phase 4.1 adds `APP_PROFILE` route gating and OpenAPI separation. It does not change endpoint internals or engine decisions.

Phase 4.2 adds catalog validation hardening. It does not add endpoints or change API response contracts.

Phase 4.3 adds an authoring/import workflow skeleton outside the API layer. It does not add endpoints and does not change `/api/v1` or `/api/learner/v1` request/response contracts.

Phase 4.5 P0 adds a local trainer CLI outside the API layer. It does not add endpoints and does not change `/api/v1` or `/api/learner/v1` request/response contracts.

Phase 4.5.1 freezes that Local Trainer boundary. It does not add endpoints and does not change API contracts.

## API Boundary

The API layer only:

- validates request shape;
- rejects public override injection;
- loads ODE sample nodes;
- calls existing engines;
- assembles learner-safe and debug responses.

The API layer never:

- creates scoring rules;
- creates diagnosis rules;
- creates rollback or forward rules;
- changes `pass_state`;
- changes `rollback_nodes` or `forward_nodes`;
- calls an LLM;
- persists attempts;
- updates mastery or review schedules.

## Fixed Orchestration

`LearningOrchestrator` runs one fixed loop:

1. receive `KnowledgeNode`;
2. receive `Question`;
3. receive `Attempt`;
4. call `CompositeScoringEngine.evaluate_detailed(question, attempt, node)`;
5. call `DiagnosisEngine.diagnose_detailed(score_result, question, attempt, node)`;
6. call `RollbackEngine.decide_rollback(error_vector, node)`;
7. call `ForwardEngine.decide_forward(score_vector, error_vector, node)`;
8. assemble the response.

Rollback and forward outputs must match the explicit RollbackEngine and ForwardEngine decisions. The orchestrator raises an internal error if those compatibility fields diverge.

## Endpoints

Base prefix:

```text
/api/v1
```

Endpoints:

```text
GET  /health
GET  /nodes
GET  /nodes/{node_id}
POST /score/evaluate
POST /diagnosis/get
POST /next-action/get
POST /attempts/submit
```

`/score/evaluate` only calls `CompositeScoringEngine`. It does not call diagnosis or movement engines and does not return root cause, rollback, forward, or next action.

`/diagnosis/get`, `/next-action/get`, and `/attempts/submit` use the orchestrator and return partitioned scoring, diagnosis, movement, and action views.

## Learner Endpoints

Base prefix:

```text
/api/learner/v1
```

Endpoints:

```text
GET  /health
GET  /questions/{question_id}
GET  /nodes/{node_id}/questions
POST /attempts/submit
```

Learner routes are Phase 4.0-lite routes. They are public-safe, deterministic, and catalog-backed. They do not replace or mutate `/api/v1`.

## APP_PROFILE Route Gating

Supported profiles:

- `learner`: registers only `/api/learner/v1/*`;
- `internal`: registers only `/api/v1/*`;
- `mixed`: registers both surfaces.

Unset `APP_PROFILE` defaults to `mixed` for local development and existing tests. Production learner deployments should set `APP_PROFILE=learner`.

Invalid values fail fast and do not silently fall back to `mixed`.

`create_app(profile=...)` can be used to construct a profile-specific app without changing environment variables. `app = create_app()` keeps `from app.main import app` compatible.

Root `/health` is available in all profiles as a minimal deployment health check. It is not an API surface and does not list route capabilities.

Profile-owned health routes are gated:

- `/api/v1/health` exists in `internal` and `mixed`;
- `/api/learner/v1/health` exists in `learner` and `mixed`.

## Request Contract

`AttemptEvaluationRequest`:

- `node_id`
- `question`
- `attempt`
- `options.include_debug`

Validation:

- `node_id` must exist in ODE nodes.
- `question.node_id` must match `node_id`.
- `attempt.question_id` must match `question.id`.
- public requests recursively reject forbidden fields anywhere in the payload.

Forbidden public API fields:

- `score_overrides`
- `evidence_overrides`
- `manual_override`
- `scenario`

Manual override remains available only for tests, golden evals, or trusted internal imports outside this public API contract.

## Learner Request Contract

`LearnerAttemptRequest` accepts only:

- `question_id`;
- `user_answer`;
- optional `response_steps`;
- optional `self_explanation`.

The learner request never accepts:

- `Question` object payloads;
- `expected_answer`;
- `rubric`;
- `solution_outline`;
- answer aliases or answer keys;
- validator config;
- score overrides or evidence overrides;
- manual override or scenario;
- include_debug or debug;
- scorer results, diagnosis trace, evidence sources, or raw movement levels.

Sensitive fields are rejected recursively, including inside nested objects, arrays, and response steps.

## Response Layers

Learner-safe default fields:

- score vector summary;
- `pass_state`;
- `learner_explanation`;
- recommended actions;
- `rollback_required`;
- `rollback_nodes`;
- `forward_allowed`;
- `forward_nodes`;
- `next_action_hint`.

The Phase 4.0-lite learner API always returns learner-safe fields only. It does not support `include_debug`.

Debug-only fields, returned only when `include_debug=true`:

- scorer results;
- evidence sources;
- diagnosis trace;
- error chain;
- debug explanation;
- policy hits;
- merge notes;
- raw rollback level;
- raw forward level;
- explicit rollback and forward decision objects.

Internal-only fields, never returned by public API:

- score overrides;
- evidence overrides;
- manual override flags;
- raw rubric answer keys;
- `expected_answer`;
- `solution_outline`;
- answer-leaking rubric details.

## Movement Display

Learner-facing movement is boolean-first:

- `rollback_nodes == []` means `rollback_required=false`.
- `forward_nodes == []` means `forward_allowed=false`.

Raw `rollback_level` and `forward_level` are debug/audit data only. The learner-facing response must not imply a rollback is required just because an internal level is `r1_internal`.

## Next Action

`next_action_hint` is deterministic extraction from engine-owned outputs. It uses the first recommended action when available and does not read learner explanation, debug explanation, frontend hints, or LLM output.

No new action policy engine is introduced in Phase 3.1.

## Error Handling

API error shape:

- `error_code`
- `message`
- `field_path`
- `request_id` optional

Codes:

- `node_not_found`: 404
- `request_schema_invalid`: 422
- `question_node_mismatch`: 422
- `attempt_question_mismatch`: 422
- `forbidden_public_api_field`: 400
- `internal_engine_error`: 500

Low-evidence business states are not API errors:

- rule-only returns 200 with `need_more_evidence`;
- no-signal returns 200 with `fail` / `need_more_evidence`;
- false-pass returns 200 with no strong forward movement.

## Current Non-Goals

Phase 3.1 does not implement:

- database persistence;
- frontend;
- real LLM API;
- long-term mastery;
- review scheduler;
- user accounts or permissions;
- full Mathematics I graph;
- complete symbolic ODE verification.

## Phase 3.2 HTTP Contract Hardening

Phase 3.2 adds real FastAPI `TestClient` HTTP red-team coverage. These tests exercise the actual HTTP layer rather than direct route function calls.

The HTTP contract tests cover:

- `/api/v1` route registration in OpenAPI;
- learner-safe default response shape;
- `include_debug=true` debug field gating;
- recursive rejection of override and scenario fields;
- false-pass, rule-only, and no-signal behavior over HTTP;
- node, question, and attempt validation errors;
- malformed request bodies;
- consistency between HTTP responses and `LearningOrchestrator` output;
- `MovementConsistencyError` handling without stack trace leakage.

No new endpoint or engine decision rule is introduced in Phase 3.2.

## Phase 3.3 Freeze Status

Phase status:

- Phase 3.1 internal/dev API: complete.
- Phase 3.2 HTTP contract hardening: complete.
- Phase 3.3 freeze pack: complete.

The Phase 3 API contract is frozen. Future work must not modify this contract unless a new migration plan, explicit compatibility note, and red-team test suite are added.

Frozen contract highlights:

- `/score/evaluate` returns scoring only.
- `/attempts/submit` is the full training-loop entry point.
- `/diagnosis/get` and `/next-action/get` are orchestration views and do not rejudge movement.
- public API payloads recursively reject override and scenario fields.
- learner-safe responses do not expose answer keys, rubric details, or solution outlines.
- debug data is gated behind `include_debug=true`.
- rollback and forward remain owned by RollbackEngine and ForwardEngine.

Current public API warning:

- `/api/v1` remains internal/dev and frozen;
- `/api/learner/v1` is the Phase 4.0-lite learner-safe surface;
- `APP_PROFILE` route gating is implemented in Phase 4.1;
- student clients must not submit `expected_answer`, `rubric`, or `solution_outline` in learner flow.

## Phase 4.0.1 Freeze Status

Phase 4.0.1 freezes the Phase 4.0-lite learner catalog boundary.

No Phase 3 `/api/v1` endpoint is changed. No new scoring, diagnosis, rollback, forward, next-question, mastery, database, frontend, LLM, or profile-gating behavior is added.

Catalog micro-hardening:

- trusted `validator_config` may provide validator flags such as `requires_constant`;
- trusted `validator_config` may not contain reserved metadata, answer, rubric, override, debug, trace, or raw movement keys;
- invalid catalog records fail server-side catalog validation before learner routes can use them.

## Phase 4.1 Status

Phase 4.1 is complete.

No Phase 3 `/api/v1` endpoint behavior changed. No Phase 4.0 `/api/learner/v1` endpoint behavior changed. The app now controls which router groups are registered:

- learner profile hides `/api/v1/*` from HTTP and OpenAPI;
- internal profile hides `/api/learner/v1/*` from HTTP and OpenAPI;
- mixed profile preserves local behavior with both surfaces.

## Phase 4.1.1 Freeze Status

Phase 4.1.1 freezes the profile-gating boundary.

The freeze does not alter Phase 3 `/api/v1` or Phase 4.0 `/api/learner/v1` contracts. It records that profile gating is route registration and OpenAPI separation, not an authentication or authorization system.

Deployment notes:

- learner-facing deployment must set `APP_PROFILE=learner`;
- mixed profile is only for local development and tests;
- future auth or permission work must not replace profile gating.

## Phase 4.2 Status

Phase 4.2 is complete.

No `/api/v1` or `/api/learner/v1` endpoint behavior changed. The catalog loader now delegates server-side catalog validation to `CatalogValidator`.

Catalog validation now checks identity, public presentation, trusted scoring, rubric integrity, validator config whitelist, dimension/node consistency, leak boundaries, version formatting, and `content_hash` format.

`content_hash` is not strongly enforced: the system validates only the `sha256:<64 lowercase hex chars>` shape and defers actual hash calculation/comparison to a future authoring/import workflow.

## Phase 4.2.1 Freeze Status

Phase 4.2.1 freezes the catalog validation contract.

No API endpoint changed. Catalog validation is a server-side catalog quality gate and does not change request or response contracts for `/api/v1` or `/api/learner/v1`.

The freeze records that `CatalogValidator` is fail-fast, `CatalogValidationError` carries `error_code`, `content_hash` remains format-only, and public leak detection is exact-match rather than semantic.

## Phase 4.3 Status

Phase 4.3 is complete.

No API endpoint changed. No endpoint was added. The authoring workflow is not an API surface and is not scanned by learner routes.

Learner API behavior remains:

- read only the formal server-side catalog;
- return only learner-safe fields;
- reject trusted payload injection;
- never read authoring drafts;
- never expose source metadata, validation reports, review checklists, answer keys, rubrics, or solution outlines.

`APP_PROFILE` gating remains unchanged.

## Phase 4.3.1 Freeze Status

Phase 4.3.1 freezes the authoring/import workflow skeleton.

No endpoint changed and no endpoint was added. `/api/v1` and `/api/learner/v1` request/response contracts remain unchanged.

The authoring workflow remains outside the API layer:

- learner API does not read authoring drafts;
- learner API does not expose source metadata;
- learner API does not expose validation reports;
- learner API does not expose review checklists;
- authoring publish candidates are in-memory dry-run artifacts only.

APP_PROFILE gating remains unchanged.

## Phase 4.4 Status

Phase 4.4 is complete.

No endpoint changed and no endpoint was added. The import CLI is not an API surface.

The learner API continues to:

- read only the formal server-side catalog;
- ignore authoring drafts and import manifests;
- reject trusted learner payload injection;
- hide source metadata, validation reports, review checklists, answer keys, rubrics, and solution outlines.

The CLI does not modify `/api/v1`, `/api/learner/v1`, APP_PROFILE registration, or API response contracts.

## Phase 4.4.1 Freeze Status

Phase 4.4.1 freezes the CLI dry-run boundary.

No endpoint changed and no endpoint was added. The import CLI is not an API surface.

Learner routes do not read authoring drafts, import manifests, reports, previews, or dry-run publish candidates.

Request/response contracts for `/api/v1` and `/api/learner/v1` remain unchanged.

## Phase 4.5 P0 Local Trainer Status

Phase 4.5 P0 adds:

```text
python -m app.training.local_trainer list
python -m app.training.local_trainer show <question_id>
python -m app.training.local_trainer submit <question_id> --answer "..."
```

The local trainer is not an API surface. It uses `create_app("learner")` and FastAPI `TestClient` to call existing learner routes:

- `GET /api/learner/v1/nodes/{node_id}/questions`
- `GET /api/learner/v1/questions/{question_id}`
- `POST /api/learner/v1/attempts/submit`

The trainer does not call scoring, diagnosis, rollback, forward, or orchestration engines directly. It does not read trusted catalog scoring fields and does not recompute pass state, movement, next action, or diagnosis.

The trainer writes a lightweight local JSONL session log under `training_sessions/` by default. This is not a database, formal attempt persistence, mastery history, or review scheduler.

No endpoint changed and no endpoint was added. APP_PROFILE registration remains unchanged.

## Phase 4.5.1 Freeze Status

Phase 4.5.1 freezes the Local Trainer command and boundary contract.

No endpoint changed and no endpoint was added. The Local Trainer remains outside the API surface.

The frozen Local Trainer path is:

```text
local_trainer -> create_app("learner") + TestClient -> /api/learner/v1/* -> existing learner API
```

The Local Trainer does not alter:

- `/api/v1`;
- `/api/learner/v1`;
- APP_PROFILE route gating;
- learner response projector behavior;
- `LearningOrchestrator` call order;
- scoring, diagnosis, rollback, forward, or next-action engine behavior.

The Local Trainer stdout and session log are learner-safe projections only. They must not expose answer keys, aliases, rubrics, solution outlines, validator config, trusted scoring blocks, scorer results, diagnosis trace, evidence sources, raw movement levels, source metadata, validation reports, review checklists, or internal debug responses.
