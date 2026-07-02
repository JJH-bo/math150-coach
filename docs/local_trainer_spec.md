# Local Trainer Spec

Status: Phase 4.5 P0 frozen by Phase 4.5.1. Phase 4.7 P0 learner-facing output refinement complete and frozen by Phase 4.7.1. Phase 4.7.3 response-evidence display integration complete.

The local trainer is a command-line wrapper over the learner-safe API. It exists to exercise the MVP learner flow locally before a frontend or database exists.

## Entry Point

```text
cd backend
python -m app.training.local_trainer ...
```

Commands:

```text
python -m app.training.local_trainer list
python -m app.training.local_trainer show ode-sep-001
python -m app.training.local_trainer submit ode-sep-001 --answer "..."
```

Optional submit flags:

- `--steps`, repeatable;
- `--explanation`;
- `--session-id`;
- `--session-root`;
- `--debug`.

`--debug` may include local trainer debug metadata only. It must not expose scorer results, diagnosis trace, evidence sources, answer keys, rubric, solution outline, or raw movement levels.

Frozen debug output may include only local metadata such as:

- `local_trainer: learner_api_only`
- `session_root_custom: true/false`

It must not request or expose learner API internal debug data.

## Stdout Contract

Every command prints JSON to stdout.

The output must be parseable with `json.loads()` and must not be Python `repr`.

Errors also print JSON:

```json
{
  "error_code": "question_not_found",
  "field_path": "question_id",
  "message": "Question not found."
}
```

## Public Question Flow

`list` calls the learner-safe node question listing route and returns a small public summary.

`show` calls the learner-safe public question route and returns only public question presentation fields.

The trainer does not read trusted catalog scoring fields.

## Submit Flow

`submit` calls:

```text
POST /api/learner/v1/attempts/submit
```

with:

- `question_id`
- `user_answer`
- optional `response_steps`
- optional `self_explanation`

The trainer then projects the already learner-safe response into a CLI payload and appends a local JSONL row.

It does not recompute pass state, rollback, forward, next action, diagnosis, or scores.

Phase 4.7 P0 adds learner-facing projection fields to submit output:

- `coach_summary`
- `status_label`
- `progression_advice`
- `evidence_gaps`
- `friendly_score_summary`
- `next_step_plan`

Phase 4.7.3 adds display-only response-evidence fields:

- `response_evidence_present`
- `unscored_dimensions`

These fields explain existing engine/API decisions. They do not change the original `pass_state`, `rollback_required`, `rollback_nodes`, `forward_allowed`, `forward_nodes`, `recommended_actions`, or `next_action_hint`.

`score_vector_summary` remains available, but Local Trainer output rewrites current known internal scorer names into learner-friendly notes. Raw names such as `RubricScorer`, `MathValidatorScorer`, and `RuleScorer` must not appear in stdout or session logs.

This cleanup is frozen for the current known scorer names and current Local Trainer payload shape. Future scorer names or new nested payload structures need explicit new tests before they are considered covered.

For `false_pass + forward_allowed=true`, Local Trainer must explain the movement as weak or preparatory. It must not describe the result as stable mastery or a full pass.

`response_evidence_present` contains only booleans and counts. It records whether the learner submitted steps or self explanation, but it does not include the raw content and does not change scoring.

`unscored_dimensions` explains dimensions that are currently `None` because the current rubric/scorer path did not form a score. It is not a scoring result. Its purpose is to avoid treating "unscored" as "learner did not write it."

When `response_steps` or `self_explanation` are present, `concept`, `process`, and `expression` dimensions that remain `None` should be explained as unscored rather than shown as direct learner action gaps. `migration=None` should not be shown as a required current action gap.

## Session Log Boundary

The local JSONL log is lightweight and local only. It is not a formal attempt persistence system.

Allowed log content:

- timestamp;
- session id;
- question id;
- node id;
- user answer;
- response steps;
- self explanation;
- pass state;
- score vector summary;
- learner explanation;
- recommended actions;
- rollback/forward booleans and nodes;
- next action hint.
- coach summary;
- status label;
- progression advice;
- evidence gaps;
- friendly score summary;
- next step plan.
- response evidence present;
- unscored dimensions.

The Phase 4.7 coach fields in the session log mirror stdout. They are learner-facing summaries, not additional scoring, diagnosis, movement, mastery, or review decisions.

Forbidden log content:

- answer keys;
- expected answer aliases;
- rubric;
- solution outline;
- validator config;
- trusted scoring block;
- scorer results;
- diagnosis trace;
- debug trace;
- evidence sources;
- raw rollback or forward levels;
- score overrides;
- evidence overrides;
- manual override;
- scenario;
- include debug flags;
- source metadata;
- validation reports;
- review checklists.

## Path Safety

Default session root is:

```text
training_sessions/
```

The default root is resolved relative to the current working directory.

Custom roots are rejected if they contain parent traversal or point into protected project areas such as the formal catalog, docs, tests, or authoring catalog directories.

Custom absolute roots outside the repository are currently allowed as controlled local output when they do not contain parent traversal and do not point into protected project areas. If this policy should become repo-confined, that belongs in a future micro-hardening phase.

## Current Limits

The local trainer intentionally does not include:

- history browsing;
- next-question recommendation;
- account/session management beyond a local session id;
- database writes;
- formal attempt persistence;
- frontend UI;
- auth;
- LLM calls.

Phase 4.7 still does not add history, frontend, persistence, mastery, review scheduling, next-question recommendation, or catalog expansion.

Phase 4.7.1 freezes this boundary and records the audit in `docs/phase_4_7_freeze_report.md`.

Future reserved command:

- `history`

`history` is not implemented in P0 and remains reserved for a future approved phase.
