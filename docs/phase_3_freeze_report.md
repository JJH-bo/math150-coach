# Phase 3 Freeze Report

Phase 3 is frozen as an internal/dev API orchestration layer. It exposes existing Phase 1-2.2 capabilities without adding scoring, diagnosis, movement, storage, frontend, or LLM behavior.

## Current Status

- Phase 3.1 internal/dev API: complete.
- Phase 3.2 HTTP red-team hardening: complete.
- Phase 3.3 freeze pack: complete after this report and final verification.

## Final Verification Baseline

Latest verification target for this freeze:

- pytest: 178 passed.
- scoring eval: 30/30 passed.
- diagnosis eval: 25/25 passed.
- movement eval: 12/12 passed.

These results must be rerun after any future change that claims to preserve Phase 3 contracts.

## Frozen Contracts

### LearningOrchestrator

The training loop is fixed:

1. receive or load `KnowledgeNode`;
2. receive `Question`;
3. receive `Attempt`;
4. call `CompositeScoringEngine.evaluate_detailed(question, attempt, node)`;
5. call `DiagnosisEngine.diagnose_detailed(score_result, question, attempt, node)`;
6. call `RollbackEngine.decide_rollback(error_vector, node)`;
7. call `ForwardEngine.decide_forward(score_vector, error_vector, node)`;
8. assemble response sections.

The orchestrator does not create scoring, diagnosis, rollback, forward, or next-action policy. It also checks that explicit RollbackEngine and ForwardEngine decisions match the compatibility movement fields in `DiagnosisResult`.

### API Endpoints

- `/api/v1/score/evaluate` returns scoring only.
- `/api/v1/attempts/submit` is the full training-loop entry point.
- `/api/v1/diagnosis/get` is an orchestration view and does not rejudge movement.
- `/api/v1/next-action/get` is an orchestration view and does not rejudge movement.
- `/api/v1/nodes` and `/api/v1/nodes/{node_id}` read the ODE node catalog only.
- `/api/v1/health` reports service status and capabilities only.

### Response Layers

Learner-safe default responses include only:

- score-vector summary;
- `pass_state`;
- `learner_explanation`;
- recommended actions;
- `rollback_required`;
- `rollback_nodes`;
- `forward_allowed`;
- `forward_nodes`;
- `next_action_hint`.

`include_debug=false` is the default and must not return debug data.

`include_debug=true` may return:

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

Internal-only fields must not appear in public API responses:

- `score_overrides`;
- `evidence_overrides`;
- `manual_override`;
- raw rubric answer keys;
- `expected_answer`;
- `solution_outline`;
- answer-leaking rubric details.

### Public Request Rejection

Public API request payloads recursively reject:

- `score_overrides`;
- `evidence_overrides`;
- `manual_override`;
- `scenario`.

These fields are not allowed at the top level, inside `question.metadata`, inside `attempt.metadata`, inside `options`, or inside any nested object/list.

### Movement Display

Learner-facing movement is boolean-first:

- `rollback_nodes == []` means `rollback_required=false`.
- `forward_nodes == []` means `forward_allowed=false`.

Raw `rollback_level` and `forward_level` are debug-only audit fields.

No-signal, rule-only, and false-pass outcomes are valid business results, not API errors.

## Boundaries That Must Not Be Broken

- API must not become a fourth decision engine.
- API must not recalculate `pass_state`.
- API must not reselect `rollback_nodes`.
- API must not reselect `forward_nodes`.
- API must not make `next_action` a new policy engine.
- API must not allow final-answer correctness to bypass multi-dimensional evidence.
- API must not bypass RollbackEngine or ForwardEngine.
- Learner-safe responses must not leak `expected_answer`, rubric content, or `solution_outline`.
- Future changes must not modify the Phase 3 API contract without a migration plan and new red-team tests.

## Current Known Limits

- Phase 3 is still an internal/dev API.
- There is no database.
- There is no formal question catalog.
- There is no permission system.
- There are no user accounts.
- The trusted `Question` payload may still include `expected_answer`, `rubric`, and `solution_outline`.
- The current API must not be treated as the final public learner API.
- A future public learner API must load answer keys, rubric, and solution outlines server-side from a trusted catalog. Student clients must not submit those fields.

## Recommended Next Phase

The recommended next phase is not frontend, real LLM, mastery modeling, or review scheduling.

Recommended next phase:

```text
Phase 4.0: Server-side Question Catalog + Safe Learner Attempt Flow
```

Phase 4.0 goals:

- remove `expected_answer`, `rubric`, and `solution_outline` from student-submitted request payloads;
- accept only `question_id`, `user_answer`, and optional `self_explanation` from the learner side;
- load trusted `Question` payload server-side by `question_id`;
- preserve the frozen Phase 3 API contract;
- establish a safe foundation for a future frontend, question bank, review loop, and mastery model.
