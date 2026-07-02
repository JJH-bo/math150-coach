# Phase 4.0 Freeze Report

Phase 4.0-lite is frozen after the Phase 4.0.1 catalog-boundary micro-hardening pass.

## Status

Complete:

- server-side YAML question catalog;
- learner-safe `/api/learner/v1` API;
- public learner submit no longer accepts trusted `Question` payloads;
- trusted scoring data is hydrated server-side from catalog records;
- catalog `validator_config` cannot override reserved domain metadata, override, debug, or trace keys.

## Verification Baseline

Final local verification for the freeze pack:

- pytest: `239 passed`;
- scoring eval: `30/30 passed`;
- diagnosis eval: `25/25 passed`;
- movement eval: `12/12 passed`.

## Frozen Contracts

Frozen and unchanged:

- `/api/v1` remains the Phase 3 internal/dev API;
- `/api/learner/v1` is the Phase 4.0-lite learner public API;
- learner request accepts only `question_id`, `user_answer`, optional `response_steps`, and optional `self_explanation`;
- learner router never accepts a full `Question` object;
- `expected_answer`, `rubric`, and `solution_outline` remain server-side only;
- learner responses do not expose debug, trace, internal, or trusted scoring fields;
- draft, retired, and internal-only catalog records are invisible to learner API;
- learner submit reuses `LearningOrchestrator` and does not make scoring, diagnosis, rollback, or forward decisions.

## Catalog Boundary

The catalog has three layers:

- `CatalogManifestEntry`: identity, status, audience, versions, and tags;
- `PublicQuestionView`: learner-visible question presentation;
- `TrustedQuestionSpec`: server-only scoring, answer, rubric, validator, and authoring data.

`PublicQuestionView` is the only learner-visible question model.

`TrustedQuestionSpec.validator_config` is trusted scoring configuration, but it must not contain reserved metadata, answer, rubric, override, debug, trace, or raw movement keys. This prevents catalog authors from overriding reserved `Question.metadata` fields during server-side hydration.

`content_hash` remains an optional placeholder and is not enforced in Phase 4.0-lite.

## Known Limits

Still not implemented:

- persistent database;
- `APP_PROFILE` route gating;
- mixed local behavior still exposes both `/api/v1` and `/api/learner/v1`;
- user or permission system;
- frontend;
- real LLM;
- mastery model;
- review scheduler;
- catalog authoring workflow;
- automatic question generation or next-question recommendation;
- full Mathematics I graph.

## Recommended Next Phase

Recommended next phase:

```text
Phase 4.1: APP_PROFILE route gating + public/internal OpenAPI separation
```

Do not jump to frontend or mastery before route-profile isolation is complete.

