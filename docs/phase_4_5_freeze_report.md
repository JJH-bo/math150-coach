# Phase 4.5.1 Freeze Report: Local Trainer Boundary Audit

Status: Phase 4.5 P0 frozen by Phase 4.5.1.

This freeze pack records the boundary for the Minimal Local Trainer Core. It does not add product functionality, endpoints, database persistence, frontend UI, auth, LLM integration, mastery/review, formal attempt persistence, next-question recommendation, formal publish/export, formal catalog writes, or broad catalog expansion.

## 1. Phase 4.5 P0 Status

Frozen complete:

- Minimal Local Trainer Core complete.
- `list` complete.
- `show` complete.
- `submit` complete.
- stdout JSON complete.
- local JSONL session log append complete.
- trusted field denylist complete.
- `session_id` validation complete.
- `session_root` path safety complete.
- learner-safe API reuse complete.
- no engine direct calls.
- no endpoint added.
- no API contract changed.
- no formal catalog write.
- no database/frontend/auth/mastery/review/formal persistence.
- `history` not implemented and reserved as future P1.

## 2. Verification Baseline

Frozen verification baseline:

- pytest: `435 passed`
- scoring eval: `30/30 passed`
- diagnosis eval: `25/25 passed`
- movement eval: `12/12 passed`

## 3. Frozen Local Trainer Command Contract

Entry:

```text
cd backend
python -m app.training.local_trainer ...
```

Implemented commands:

```text
list
show <question_id>
submit <question_id> --answer "..."
```

Not implemented:

```text
history
next-question
review
mastery
export
sync
frontend
database persistence
```

## 4. Frozen Architecture Contract

Primary data path:

```text
local_trainer -> create_app("learner") + TestClient -> /api/learner/v1/* -> existing learner API
```

The Local Trainer must not:

- directly call scoring engine;
- directly call diagnosis engine;
- directly call rollback or forward engines;
- directly call `LearningOrchestrator`;
- directly read trusted scoring fields;
- recompute `pass_state`;
- recompute rollback or forward;
- choose `next_action`;
- read authoring drafts;
- read import manifests;
- write formal catalog files.

Audit note: `list` currently uses `load_node_catalog()` only to enumerate known node ids before calling learner-safe node question listing routes. Learner-visible question data still comes from `/api/learner/v1/*`; trusted catalog scoring fields are not read.

## 5. Frozen `list` Contract

`list` may output only:

- `question_id`
- `node_id`
- `title`
- `difficulty`
- `answer_format`
- `response_step_mode`

It must not output trusted, internal, or debug fields.

## 6. Frozen `show` Contract

`show` may output only:

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

It must not output trusted, internal, or debug fields.

## 7. Frozen `submit` Contract

Input:

- `question_id`
- `--answer`, required
- `--steps`, optional repeatable
- `--explanation`, optional
- `--session-id`, optional
- `--session-root`, optional
- `--debug`, optional

Behavior:

- build learner-safe payload;
- call `/api/learner/v1/attempts/submit`;
- project the already learner-safe response into the CLI payload;
- append lightweight JSONL session log;
- print stdout JSON.

Output may include only:

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
- optional local-only debug metadata.

## 8. Frozen Debug Boundary

`--debug` may include only Local Trainer metadata, for example:

- `local_trainer: learner_api_only`
- `session_root_custom: true/false`

`--debug` must not:

- request learner API internal debug;
- expose `scorer_results`;
- expose `diagnosis_trace`;
- expose `evidence_sources`;
- expose raw rollback or forward levels;
- expose `expected_answer`, `rubric`, or `solution_outline`;
- expose internal projector data.

## 9. Frozen Session Log Contract

Default root:

```text
training_sessions/
```

This is:

- lightweight local log;
- local-only learner aid;
- not a database;
- not formal attempt persistence;
- not mastery history;
- not review scheduler;
- not cross-device sync;
- not user account storage.

JSONL row may include:

- `timestamp`
- `session_id`
- `question_id`
- `node_id`
- `user_answer`
- `response_steps`
- `self_explanation`
- `pass_state`
- `score_vector_summary`
- `learner_explanation`
- `recommended_actions`
- `rollback_required`
- `rollback_nodes`
- `forward_allowed`
- `forward_nodes`
- `next_action_hint`

JSONL row must not include trusted, internal, or debug fields.

## 10. Frozen Session Path Safety Contract

Current frozen behavior:

- default session root is `training_sessions/` relative to the current working directory;
- custom `--session-root` is allowed for local/testing use;
- custom absolute `--session-root` outside the repository is explicitly allowed as controlled local output, as long as it is not a protected project area and contains no parent traversal;
- `--session-root` must not contain parent traversal such as `../outside`;
- `--session-root` must not point into protected project areas currently enforced by implementation:
  - `backend/catalog_data`
  - `backend/catalog_authoring`
  - `docs`
  - `backend/tests`
  - `tests`
- `session_id` must match safe pattern:
  - letters
  - digits
  - underscore
  - dot
  - hyphen
  - maximum length 80
- session filename is derived from safe `session_id`;
- session log write runs trusted field denylist before writing;
- formal catalog manifest remains unchanged after submit.

Known audit note: the implementation enforces the concrete protected roots above. It does not use a broad path-part deny rule for every possible directory named `catalog_authoring` outside those roots. If repo-wide or system-wide path-part blocking is desired, handle it as Phase 4.5.2 micro-hardening rather than changing this freeze.

## 11. Frozen Trusted Field Denylist

The Local Trainer/session log denylist covers:

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

## 12. Frozen Error / Stdout Contract

Frozen stdout behavior:

- stdout is always JSON;
- stdout is parseable with `json.loads()`;
- error stdout is also JSON;
- normal errors do not print stack traces;
- Python repr must not appear in stdout;
- unknown question returns structured JSON error;
- argument errors return structured JSON error.

## 13. Unchanged Boundaries

Unchanged in Phase 4.5.1:

- core engines unchanged;
- `/api/v1` unchanged;
- `/api/learner/v1` unchanged;
- APP_PROFILE gating unchanged;
- CatalogValidator unchanged;
- authoring/import CLI unchanged;
- formal catalog samples unchanged;
- ODE nodes YAML unchanged;
- scoring/diagnosis/movement golden eval cases unchanged;
- no endpoint added;
- no database;
- no frontend;
- no auth;
- no LLM;
- no mastery/review;
- no formal attempt persistence;
- no formal catalog write;
- no broad catalog expansion.

## 14. Known Limits

Known limits:

- no `history` command yet;
- no frontend;
- no database-backed attempts;
- no user accounts;
- no mastery/review scheduler;
- no next-question recommendation;
- no full Mathematics I catalog;
- no formal publish/export;
- no formal attempt persistence;
- TestClient local client is acceptable for MVP but may need service-layer refactor later;
- session log default root depends on current working directory;
- custom absolute session roots outside the repository are allowed as controlled local output;
- session log is local-only and not a long-term learning model;
- `list` uses node id enumeration from the existing node catalog helper because there is no learner API endpoint for listing all nodes yet.

## 15. Local Trainer Boundary Audit Checklist

Audit result:

1. Local Trainer only implements `list` / `show` / `submit`: pass.
2. `history` is not implemented: pass.
3. Local Trainer uses `create_app("learner") + TestClient`: pass.
4. Local Trainer calls learner API routes for question display and submission: pass.
5. Local Trainer does not call core engines directly: pass.
6. Local Trainer does not call `LearningOrchestrator` directly: pass.
7. Local Trainer does not recompute `pass_state`: pass.
8. Local Trainer does not recompute rollback/forward: pass.
9. Local Trainer does not choose `next_action` itself: pass.
10. `list` output contains only allowed public summary fields: pass.
11. `show` output contains only allowed public fields: pass.
12. `submit` output contains only learner-safe fields: pass.
13. `submit` writes JSONL session log: pass.
14. session log includes `user_answer` only as local learner record: pass.
15. session log does not include `expected_answer`: pass.
16. session log does not include `rubric`: pass.
17. session log does not include `solution_outline`: pass.
18. session log does not include `diagnosis_trace`: pass.
19. session log does not include `scorer_results`: pass.
20. unsafe `session_id` chars rejected: pass.
21. parent traversal `session_root` rejected: pass.
22. protected project areas rejected: pass for currently enforced roots.
23. formal catalog path rejected: pass.
24. formal catalog manifest unchanged after submit: pass.
25. stdout JSON parseable for `list`: pass.
26. stdout JSON parseable for `show`: pass.
27. stdout JSON parseable for `submit`: pass.
28. stdout JSON parseable for errors: pass.
29. Python repr not returned: pass.
30. debug output is local-only and safe: pass.
31. learner API leak regression still passes: pass.
32. APP_PROFILE gating regression still passes: pass.
33. default formal catalog still validates: pass.
34. scoring eval 30/30 passes: pass.
35. diagnosis eval 25/25 passes: pass.
36. movement eval 12/12 passes: pass.

## 16. Recommended Next Step

Recommended next step:

```text
Phase 4.6 Plan: Usability Trial / Real Training Run Protocol
```

This should be a planning phase only at first. It should use the frozen Local Trainer to run a real learner-flow trial and collect usability findings before expanding history, catalog size, UI, persistence, mastery, or review behavior.

Alternative next steps, only with explicit approval:

- Phase 4.5.2 Micro-hardening if the custom absolute `--session-root` policy or broad protected-directory matching should be tightened.
- Phase 4.6 Plan: Local Trainer History P1.
- Phase 4.6 Plan: Minimal Catalog Expansion for Real Practice.

