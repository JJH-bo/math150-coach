# Phase 4.7.3: Response Evidence Display Integration

Status: implemented.

Phase 4.7.3 is a narrow Local Trainer / coach-output display fix. It does not integrate `response_steps` or `self_explanation` into scoring.

## Goal

Phase 4.7.2 confirmed that `response_steps` and `self_explanation` are transported correctly from Local Trainer into the learner API, domain `Attempt`, and `LearningOrchestrator`. The missing part is scorer consumption: current active scorers still read only `attempt.user_answer`.

Before a scoring integration phase exists, Local Trainer output must avoid saying that the learner did not write steps, concept explanation, or rigorous expression when the learner did submit steps/explanation but the current rubric/scorer path did not score those fields.

## Frozen Non-Goals

Phase 4.7.3 does not:

- modify `CompositeScoringEngine`;
- modify `RubricScorer`;
- modify `RuleScorer`;
- modify `MathValidatorScorer`;
- modify `DiagnosisEngine`;
- modify `RollbackEngine`;
- modify `ForwardEngine`;
- modify `LearningOrchestrator` behavior;
- modify learner API schema or endpoints;
- modify learner response projector;
- modify catalog YAML;
- modify golden eval cases;
- modify `APP_PROFILE` gating;
- modify `CatalogValidator`;
- add endpoint, database, frontend, auth, LLM, mastery/review, history, next-question recommendation, formal persistence, or catalog expansion.

## Display-Only Fields

Local Trainer submit output now includes:

- `response_evidence_present`
- `unscored_dimensions`

`response_evidence_present` is local display metadata:

```json
{
  "has_response_steps": true,
  "response_step_count": 3,
  "has_self_explanation": true
}
```

It contains only booleans and counts. It does not include raw response steps or raw self explanation. It is not a new scoring signal.

`unscored_dimensions` separates unscored dimensions from actionable learner gaps:

```json
[
  {
    "dimension": "process",
    "label": "过程完整性",
    "reason": "当前评分还没有把提交的步骤/解释转成过程完整性分数；这不等于学习者没有写过程。"
  }
]
```

It is a display explanation, not a `ScoreVector` change.

## Evidence Gap Policy

`evidence_gaps` should contain true action gaps such as:

- low trigger evidence;
- low method evidence;
- low transformation evidence;
- low calculation evidence;
- low final-answer evidence;
- missing process/concept/expression only when the learner did not submit steps/explanation.

When the learner did submit `response_steps` or `self_explanation`, `concept`, `process`, and `expression` dimensions that are still `None` move into `unscored_dimensions` instead of being phrased as "you did not write this."

`migration=None` is not shown as a required current action gap. It can appear in `unscored_dimensions` because a single current-node practice question may not assess variation transfer.

## Preserved Decisions

Phase 4.7.3 must not change:

- `pass_state`;
- `score_vector_summary` numeric values;
- `rollback_required`;
- `rollback_nodes`;
- `forward_allowed`;
- `forward_nodes`;
- `recommended_actions`;
- `next_action_hint`;
- scoring eval results;
- diagnosis eval results;
- movement eval results.

## Session Log

Submit JSONL rows include:

- `response_evidence_present`;
- `unscored_dimensions`.

The local session log remains local-only. It is not history browsing, formal attempt persistence, mastery, review scheduling, or a database.

## Future Scoring Integration

If a future phase should make `response_steps` or `self_explanation` actually affect `process`, `concept`, or `expression` scores, that must be planned as a separate scoring integration phase.

Possible future names:

- Phase 4.8 Scoring Input Integration Plan;
- Phase 4.9 Attempt Evidence Scorer Plan.

That future work would need scorer design, red-team tests, and golden eval updates. It is intentionally not part of Phase 4.7.3.
