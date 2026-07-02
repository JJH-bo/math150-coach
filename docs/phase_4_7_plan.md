# Phase 4.7 P0: Learner Output / Coach Feedback Refinement

Status: P0 implementation complete and frozen by Phase 4.7.1. Phase 4.7.3 response-evidence display integration complete.

Phase 4.7 P0 improves Local Trainer learner-facing output without changing engines, APIs, learner projector, catalog, or golden eval cases.

Phase 4.7.1 freezes the P0 coach-output boundary and records the final boundary audit in `docs/phase_4_7_freeze_report.md`.

Phase 4.7.3 applies the Phase 4.7.2 audit finding as a display-only fix: Local Trainer now separates "learner submitted steps/explanation but the current scorer path did not score that dimension" from "learner did not provide the evidence."

## Goal

Phase 4.6 trial showed that the frozen Local Trainer can run `list` / `show` / `submit`, but the submit output was not always easy for a learner to understand.

The key issue was:

```text
false_pass + forward_allowed=true + need_more_evidence + high dimension scores
```

This may be valid internally, but it is confusing for a learner unless the output explains that this is weak or preparatory forward movement and that evidence completion remains the priority.

## Scope

Phase 4.7 P0 adds a deterministic learner-facing projection layer for Local Trainer submit output.

Implemented fields:

- `coach_summary`
- `status_label`
- `progression_advice`
- `evidence_gaps`
- `friendly_score_summary`
- `next_step_plan`
- `response_evidence_present`
- `unscored_dimensions`

Existing decision fields remain present:

- `pass_state`
- `rollback_required`
- `rollback_nodes`
- `forward_allowed`
- `forward_nodes`
- `next_action_hint`
- `recommended_actions`

## Architecture

Frozen input path remains:

```text
local_trainer -> create_app("learner") + TestClient -> /api/learner/v1/* -> existing learner API
```

Projection path:

```text
learner-safe submit payload -> app.training.coach_output pure functions -> stdout/session log
```

`coach_output.py` is deterministic and must not:

- call engines;
- call learner API debug;
- read trusted catalog fields;
- change pass/fail decisions;
- change rollback or forward decisions;
- choose a new next action policy;
- expose scorer results, diagnosis trace, rubric, answer key, or solution outline.

`response_evidence_present` is local display metadata. It contains only booleans and counts, and it does not feed scoring, diagnosis, rollback, forward, or next-action decisions.

`unscored_dimensions` is a learner-facing explanation for dimensions that have no score. It is not a `ScoreVector` field and does not change engine output.

## Output Policies

### Status Label

`status_label` maps internal pass state to learner-facing wording:

- `pass` -> stable pass wording.
- `fail` -> not passed wording.
- `false_pass` -> suspicious answer or insufficient evidence wording.
- `partial_pass` -> partial pass wording.
- unknown/null -> unclear status wording.

The original `pass_state` is retained.

### Progression Advice

Rules:

- `rollback_required=true`: tell the learner to repair the current node first.
- `false_pass + forward_allowed=true`: explain weak or preparatory forward movement and keep evidence completion as priority.
- `pass + forward_allowed=true`: allow forward movement but keep a review note.
- `forward_allowed=false`: do not recommend moving on.
- `fail`: never present as a pass.

### Evidence Gaps

The projection maps missing or low dimensions to learner tasks:

- missing `process`: write key steps, not only conclusion.
- missing `concept`: explain why the method applies.
- missing `expression`: write solution form, arbitrary constants, and necessary explanation carefully.
- missing `migration`: current answer does not prove variation transfer yet.
- low `transformation`: repair condition transformation / standard form.
- low `trigger`: add trigger recognition evidence.
- low `method`: explain method choice.
- low `calculation`: check calculation chain.
- low `final_answer`: check final answer form.

Thresholds:

- `< 60`: weak.
- `60 <= score < 80`: needs reinforcement.
- `None`: missing evidence.

Phase 4.7.3 narrows the `None` rule:

- if the learner did not submit steps/explanation, missing `process`, `concept`, or `expression` can remain an action gap;
- if the learner did submit steps/explanation, missing `process`, `concept`, or `expression` moves to `unscored_dimensions`;
- `migration=None` is not treated as a required current action gap.

### Friendly Score Summary

`friendly_score_summary` keeps scores and dimension labels but removes known raw scorer names.

Frozen raw scorer-name replacements:

- `RubricScorer` -> learner-facing rubric wording.
- `MathValidatorScorer` -> learner-facing answer/calculation validation wording.
- `RuleScorer` -> learner-facing keyword/structure signal wording.

Raw scorer names must not appear in stdout or session log.

This P0 cleanup scope covers current known scorer names and current Local Trainer payload shape. New scorer names or new nested payload structures require explicit future tests.

## Session Log Impact

Submit JSONL rows now include the same learner-facing fields:

- `coach_summary`
- `status_label`
- `progression_advice`
- `evidence_gaps`
- `friendly_score_summary`
- `next_step_plan`
- `response_evidence_present`
- `unscored_dimensions`

The session log remains local-only. It is not formal attempt persistence, mastery history, review scheduler, or database storage.

## P0 / P1 / P2 Cutline

P0 complete and frozen:

- deterministic `coach_output.py`;
- Local Trainer submit projection;
- session log friendly fields;
- raw scorer names removed from stdout/session log;
- false-pass forward explanation;
- no trusted field leaks;
- response-evidence display separation;
- pytest/evals green;
- Phase 4.7.1 boundary audit recorded.

P1 reserved:

- `review_priority`;
- `learner_warnings`;
- better session log summary;
- Windows terminal encoding guidance.

P2 reserved:

- pretty terminal output;
- rich tables;
- frontend;
- history;
- persistence;
- LLM rewrite;
- broad catalog expansion.

## Non-goals

Phase 4.7 P0 and Phase 4.7.1 do not:

- modify `CompositeScoringEngine`;
- modify `DiagnosisEngine`;
- modify `RollbackEngine`;
- modify `ForwardEngine`;
- modify `LearningOrchestrator`;
- modify `/api/v1`;
- modify `/api/learner/v1`;
- modify learner response projector;
- add endpoints;
- implement history;
- add frontend/database/auth/LLM/mastery/review/formal persistence;
- expand catalog;
- write formal catalog files.

## Recommended Next Step

Recommended next step:

```text
Phase 4.7.4 Subjective Usability Trial for Coach Output
```

The next step should evaluate whether the frozen coach-output fields are understandable and actionable for real learner attempts. It should not start P1/P2 expansion before that trial.
