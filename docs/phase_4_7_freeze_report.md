# Phase 4.7.1 Freeze Pack + Coach Output Boundary Audit

Status: complete. Phase 4.7 P0 is frozen.

This freeze pack audits the Local Trainer coach-output projection introduced in Phase 4.7 P0. It does not add learner features, API behavior, engine behavior, catalog behavior, persistence, frontend UI, LLM integration, or new training logic.

## Verification Baseline

Expected baseline after this freeze:

- `pytest`: all tests pass.
- Scoring eval: `30/30 passed`.
- Diagnosis eval: `25/25 passed`.
- Movement eval: `12/12 passed`.

No test was added in this freeze pack because the existing Phase 4.7 P0 tests already cover the coach-output boundary needed for this audit.

## Frozen Architecture Contract

The Local Trainer flow remains:

```text
local_trainer
  -> create_app("learner") + TestClient
  -> /api/learner/v1/*
  -> learner-safe API payload
  -> app.training.coach_output deterministic projection
  -> stdout and local JSONL session log
```

Frozen rules:

- `coach_output.py` is a pure projection layer.
- It must not call scoring, diagnosis, rollback, forward, orchestration, catalog validation, or authoring code.
- It must not change `pass_state`, rollback decisions, forward decisions, or `next_action_hint`.
- It must not read trusted catalog fields such as answer keys, rubric, solution outline, validator config, or source metadata.
- It must not introduce a new decision engine.

## Frozen Coach Fields Contract

Phase 4.7 P0 freezes these learner-facing fields in Local Trainer submit stdout and session logs:

- `coach_summary`
- `status_label`
- `progression_advice`
- `evidence_gaps`
- `friendly_score_summary`
- `next_step_plan`

These fields explain existing learner-safe API outputs. They do not replace or modify the raw decision fields:

- `pass_state`
- `rollback_required`
- `rollback_nodes`
- `forward_allowed`
- `forward_nodes`
- `next_action_hint`
- `recommended_actions`

## Frozen Status Label Policy

`status_label` is a deterministic mapping from `pass_state`:

- `pass`: stable pass wording.
- `fail`: not passed wording.
- `false_pass`: suspicious answer or insufficient evidence wording.
- `partial_pass`: partial pass wording.
- missing or unknown: unclear status wording.

The original `pass_state` remains present for contract stability.

## Frozen Progression Advice Policy

`progression_advice` follows fixed display rules:

- `rollback_required=true`: repair the current issue first.
- `false_pass + forward_allowed=true`: explain that any forward movement is weak or preparatory and that evidence completion is still required.
- `pass + forward_allowed=true`: allow moving forward while preserving review awareness.
- `forward_allowed=false`: do not recommend moving forward.
- `fail`: never present as a pass.

This policy does not recompute movement. It only describes movement already returned by the learner-safe API.

## Frozen Evidence Gap Policy

`evidence_gaps` maps missing or weak score dimensions into learner-facing improvement tasks:

- missing `process`: show key steps, not only a conclusion.
- missing `concept`: explain why the method applies.
- missing `expression`: write the solution form, arbitrary constants, and necessary explanation carefully.
- missing `migration`: current answer does not prove transfer to variations yet.
- low `trigger`: add trigger recognition evidence.
- low `method`: explain method choice.
- low `transformation`: repair transformation or standard-form conversion.
- low `calculation`: check local calculation chain.
- low `final_answer`: check final answer form.

Thresholds remain deterministic:

- `None`: missing evidence.
- `< 60`: weak.
- `60 <= score < 80`: needs reinforcement.

## Frozen Friendly Score Summary Policy

`friendly_score_summary` preserves learner-visible dimension scores while cleaning known raw scorer implementation names from notes.

Frozen P0 cleanup scope:

- `RubricScorer` is rewritten into learner-facing wording.
- `MathValidatorScorer` is rewritten into learner-facing wording.
- `RuleScorer` is rewritten into learner-facing wording.

This scope is intentionally narrow. It covers the current learner-safe payload shape and current scorer names. Future scorer names or new nested payload structures require explicit tests before they are considered covered.

## Frozen Session Log Impact

Submit JSONL rows include the same Phase 4.7 learner-facing fields:

- `coach_summary`
- `status_label`
- `progression_advice`
- `evidence_gaps`
- `friendly_score_summary`
- `next_step_plan`

The local JSONL log remains local-only. It is not:

- database persistence;
- formal attempt persistence;
- mastery history;
- review scheduling;
- next-question recommendation;
- account/session management.

## Frozen Trusted And Raw Leak Boundary

The Local Trainer output and session logs must not expose:

- answer keys;
- expected answer aliases;
- rubric;
- solution outline;
- validator config;
- trusted scoring blocks;
- scorer results;
- diagnosis trace;
- debug trace;
- evidence sources;
- raw rollback or forward levels;
- score overrides;
- evidence overrides;
- manual override;
- scenario;
- source metadata;
- validation reports;
- review checklists.

Known raw scorer names must not appear in Local Trainer stdout or session logs.

## Unchanged Boundaries

Phase 4.7.1 does not modify:

- `CompositeScoringEngine`;
- `DiagnosisEngine`;
- `RollbackEngine`;
- `ForwardEngine`;
- `LearningOrchestrator`;
- `/api/v1`;
- `/api/learner/v1`;
- learner response projector;
- `APP_PROFILE` route gating;
- catalog validator;
- formal catalog samples;
- ODE node YAML;
- golden eval cases;
- authoring CLI;
- Local Trainer command set.

Phase 4.7.1 does not add:

- endpoints;
- frontend;
- database;
- auth;
- LLM calls;
- mastery or review scheduling;
- attempt persistence;
- formal catalog writes;
- history browsing;
- next-question recommendation;
- broad catalog expansion.

## Boundary Audit Checklist

1. Coach output is generated after learner-safe API response.
2. Coach output does not call core engines.
3. Coach output does not call authoring or catalog validation.
4. Coach output does not read trusted catalog fields.
5. Coach output does not change `pass_state`.
6. Coach output does not change `rollback_required`.
7. Coach output does not change `rollback_nodes`.
8. Coach output does not change `forward_allowed`.
9. Coach output does not change `forward_nodes`.
10. Coach output does not change `next_action_hint`.
11. Coach output does not create a new decision engine.
12. `status_label` is deterministic.
13. `progression_advice` is deterministic.
14. `evidence_gaps` is deterministic.
15. `friendly_score_summary` is deterministic.
16. Known raw scorer names are cleaned from stdout.
17. Known raw scorer names are cleaned from session logs.
18. False-pass forward wording is weak or preparatory, not stable mastery.
19. Session log remains local-only JSONL.
20. Session log does not become history browsing.
21. Session log does not become review scheduling.
22. Session log does not become mastery persistence.
23. No learner API contract is changed.
24. No internal API contract is changed.
25. No golden eval behavior is changed.

Audit conclusion: pass.

## Known Limits

- Coach wording is deterministic and template-based, not LLM-generated.
- The wording still needs subjective usability testing with real learner answers.
- Raw scorer-name cleanup is scoped to current known scorer names and current payload shape.
- Windows terminal display may require UTF-8 configuration to show Chinese text cleanly.
- The catalog remains intentionally small.
- There is no history browser, next-question recommendation, persistence, review scheduler, frontend, or account system.

## Recommended Next Step

Recommended next step:

```text
Phase 4.7.2 Subjective Usability Trial for Coach Output
```

The next step should test whether the frozen coach-output fields are actually understandable and actionable to a learner. It should not be P1/P2 feature expansion unless the usability trial shows that the current P0 wording is insufficient.
