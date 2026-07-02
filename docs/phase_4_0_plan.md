# Phase 4.0-lite Implementation Notes

Phase 4.0-lite adds a server-side question catalog and a learner-safe public attempt flow without changing Phase 1-2.2 engines or the frozen Phase 3 `/api/v1` contract.

## Added Surface

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

## Request Contract

`LearnerAttemptRequest` accepts only:

- `question_id`;
- `user_answer`;
- optional `response_steps`;
- optional `self_explanation`.

It forbids extra fields and recursively rejects trusted scoring, debug, scenario, and override fields anywhere in the payload.

## Safe Response Contract

Learner attempt responses expose only:

- `scoring.score_vector`;
- `diagnosis.pass_state`;
- `diagnosis.learner_explanation`;
- `diagnosis.recommended_actions`;
- `movement.rollback_required`;
- `movement.rollback_nodes`;
- `movement.forward_allowed`;
- `movement.forward_nodes`;
- `action.next_action_hint`.

They do not expose expected answers, answer aliases, rubrics, solution outlines, validator config, scorer results, evidence sources, diagnosis trace, error chain, debug explanation, raw rollback level, or raw forward level.

## Frozen Boundaries

Unchanged:

- `CompositeScoringEngine`;
- `DiagnosisEngine`;
- `RollbackEngine`;
- `ForwardEngine`;
- `LearningOrchestrator` call order;
- `/api/v1` internal/dev behavior;
- scoring, diagnosis, and movement golden eval files.

The API layer remains a caller and assembler, not a fourth decision engine.

## Phase 4.0.1 Freeze Addendum

Phase 4.0.1 adds no product feature. It freezes the Phase 4.0-lite contract and adds one catalog-boundary hardening rule:

- `TrustedQuestionSpec.validator_config` cannot contain reserved metadata, answer, rubric, override, debug, trace, or raw movement keys.

This protects server-side `Question.metadata` hydration from reserved-key pollution while keeping normal validator flags, such as `requires_constant`, valid.

## Deferred

Phase 4.1 may add `APP_PROFILE=learner/internal/mixed` gating. Phase 4.0-lite intentionally keeps mixed local behavior: frozen `/api/v1` routes stay available and `/api/learner/v1` routes are added.
