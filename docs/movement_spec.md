# Movement Contract Spec

Phase 2.2-lite hardens the movement contract before any Phase 3 API is exposed.

Movement means the coordinated result of:

- `pass_state`
- `root_cause` and primary errors
- `rollback_level` / `rollback_nodes`
- `forward_level` / `forward_nodes`
- `recommended_actions`
- `next_action_hint`

It does not introduce persistent state, mastery updates, attempt history, review scheduling, or node-status changes.

## Ownership

- `RollbackEngine` is the final owner of `rollback_level` and `rollback_nodes`.
- `ForwardEngine` is the final owner of `forward_level` and `forward_nodes`.
- `DiagnosisEngine` owns root cause, error chain, evidence, confidence, and recommended training actions.
- `DiagnosisEngine` may call RollbackEngine and ForwardEngine to populate compatibility fields, but it must not invent rollback or forward nodes by itself.
- Future API layers may orchestrate these outputs, but must not create a fourth movement decision center.

## Next Action Priority

`next_action_hint` and `recommended_actions` must not contradict rollback or forward decisions.

Priority rules:

1. `fail` and `false_pass` prioritize targeted rollback, local repair, or evidence collection. They must not strong-forward.
2. `rule-only` and no-signal attempts prioritize `need_more_evidence`.
3. `calculation_error` prioritizes `calculation_repair` or R1 current-node repair. It must not expand into concept or method prerequisites when trigger/method/transformation evidence is stable.
4. Only `pass` may allow P2/P3 successor unlock.
5. `partial_pass` allows only P1 local review or same-node variant work, never strong unlock of synthesis or migration nodes.
6. Derived errors cannot upgrade movement. Movement should follow root cause and primary errors, not downstream final-answer failure.

## Rollback Safety

Rollback must select the smallest useful target set.

- Ordinary calculation, expression, and process errors stay on the current node.
- Method and transformation errors may use one direct prerequisite or a configured target.
- Returning all prerequisites is only valid for an allowed R4 framework rollback.
- R4 is reserved for `knowledge_confusion` and `synthesis_failure`, and still goes through RollbackEngine safety checks.

## Forward Safety

Forward movement is blocked by:

- false-pass signal;
- non-soft primary errors;
- missing required dimensions;
- insufficient non-answer evidence;
- rule-only or no-signal scoring paths.

P3 requires strong trigger, method, transformation, and calculation evidence, with no primary or secondary blocker.

## Phase 2.2-lite Boundaries

This phase does not add:

- `node_status_suggestions`;
- mastery updates;
- attempt history;
- review scheduler;
- database persistence;
- API endpoints;
- frontend behavior.

Any state-like idea remains documentation-only until a real persistence and mastery model exists.
