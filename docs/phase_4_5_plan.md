# Phase 4.5 P0 Minimal Local Trainer Core

Status: P0 implementation complete. Frozen by Phase 4.5.1.

Phase 4.5 P0 adds a minimal local learner practice loop on top of the existing learner-safe API. It is intentionally small: list learner-visible questions, show a public question, submit an answer through `/api/learner/v1`, and append a lightweight local JSONL session log.

It does not add endpoints, database persistence, frontend UI, auth, LLM integration, mastery/review scheduling, next-question selection, formal catalog writes, formal publish/export, or broad catalog expansion.

## Scope

Implemented command entry:

```text
cd backend
python -m app.training.local_trainer ...
```

Implemented commands:

- `list`
- `show <question_id>`
- `submit <question_id> --answer "..."`

History browsing is not part of P0. The JSONL log exists only as a local learner-session aid and is not a formal attempt store.

Future P1/P2 ideas remain reserved only:

- `history`
- next-question recommendation
- review scheduling
- mastery updates
- frontend UI
- database-backed attempts

## Engine Boundary

The local trainer does not call scoring, diagnosis, rollback, forward, or orchestration engines directly.

The fixed call path is:

```text
local_trainer -> create_app("learner") TestClient -> /api/learner/v1/* -> existing learner API
```

This preserves Phase 1-4.4 boundaries:

- `CompositeScoringEngine` owns scoring;
- `DiagnosisEngine` owns diagnosis and learner explanation;
- `RollbackEngine` owns rollback nodes;
- `ForwardEngine` owns forward nodes;
- `LearningOrchestrator` owns the fixed engine order;
- learner API owns server-side trusted catalog hydration.

## Learner-safe Output

`list` may return only:

- `question_id`
- `node_id`
- `title`
- `difficulty`
- `answer_format`
- `response_step_mode`

`show` may return only:

- `question_id`
- `node_id`
- `title`
- `stem`
- `prompt_markdown`
- `answer_format`
- `response_step_mode`
- `difficulty`
- `hints_public`
- `display_assets`

`submit` returns only:

- `question_id`
- `pass_state`
- `score_vector_summary`
- `learner_explanation`
- `recommended_actions`
- `rollback_required`
- `rollback_nodes`
- `forward_allowed`
- `forward_nodes`
- `next_action_hint`
- `session_log_written`
- `session_id`

The trainer and session log deny these trusted/internal fields recursively:

- `expected_answer`
- `answer_aliases`
- `rubric`
- `solution_outline`
- `validator_config`
- `trusted_scoring`
- `answer_key`
- `scorer_results`
- `diagnosis_trace`
- `debug_trace`
- `evidence_sources`
- `raw_rollback_level`
- `raw_forward_level`
- `score_overrides`
- `evidence_overrides`
- `manual_override`
- `scenario`
- `include_debug`
- `source_metadata`
- `validation_report`
- `review_checklist`

## Session Log

Default root:

```text
training_sessions/
```

The default root is resolved relative to the current working directory.

`--session-root` may be supplied for local testing or controlled local use, but it is rejected when it:

- uses parent traversal such as `../outside`;
- points into the formal catalog directory;
- points into docs or tests;
- points into authoring/catalog protected project areas.

`session_id` may contain only letters, digits, underscore, dot, or hyphen. The session file is:

```text
<session_root>/<session_id>.jsonl
```

Each JSONL row may include timestamp, session id, question/node ids, learner answer, optional steps, optional self-explanation, projected scoring summary, learner explanation, recommended actions, movement booleans/nodes, and next action hint.

## Verification

Phase 4.5 P0 adds local-trainer tests for:

- learner-visible question listing;
- public question display;
- learner-safe submit output;
- local JSONL append;
- session id safety;
- session root safety;
- trusted field denylist;
- stdout JSON behavior;
- formal catalog manifest unchanged;
- learner API and APP_PROFILE regression boundaries.

## Non-goals

Still not implemented:

- full learner history browser;
- frontend landing page;
- database-backed attempts;
- user accounts;
- long-term mastery/review;
- next-question recommendation;
- formal catalog writes;
- real LLM integration.

## Phase 4.5.1 Freeze

Phase 4.5.1 freezes the P0 command contract, learner-safe output contract, debug boundary, session log contract, session path-safety contract, and trusted-field denylist.

It does not implement history or expand product behavior.
