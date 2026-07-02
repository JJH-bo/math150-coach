# Phase 4.7.2 Response Evidence Integration Audit

Status: audit complete. No implementation was performed.

Follow-up: Phase 4.7.3 implemented the recommended display-only fix. It did not change scoring, diagnosis, movement, API, catalog, or eval behavior.

This audit traces `response_steps` and `self_explanation` from Local Trainer submit through learner API, `LearningOrchestrator`, scoring, diagnosis, and `coach_output`. The goal is to explain why a learner can submit steps/explanation while `process`, `concept`, and `expression` remain `null`, causing `evidence_gaps` to still ask for process, concept, and expression evidence.

## Scope And Non-Changes

This audit did not modify:

- engines;
- API routes;
- Local Trainer;
- `coach_output.py`;
- catalog data;
- tests;
- endpoints;
- frontend, database, auth, LLM, mastery, review, or history behavior.

No tests were run because this was a documentation-only audit.

## Evidence Chain Summary

```text
Local Trainer submit args
  -> LearnerLocalClient.submit_attempt()
  -> POST /api/learner/v1/attempts/submit
  -> LearnerAttemptRequest
  -> LearnerAttemptAssembler.to_attempt()
  -> Attempt(response_steps, self_explanation)
  -> LearningOrchestrator.process()
  -> CompositeScoringEngine.evaluate_detailed()
  -> RubricScorer / MathValidatorScorer / RuleScorer
  -> DiagnosisEngine.diagnose_detailed()
  -> LearnerResponseProjector.from_orchestrated()
  -> Local Trainer _submit_payload()
  -> coach_output.build_coach_output()
  -> stdout and local JSONL session log
```

The transport path exists through `Attempt`. The scoring path does not currently consume `response_steps` or `self_explanation`.

## Findings

### 1. Does Local Trainer correctly send `response_steps`?

Yes.

`backend/app/training/local_trainer.py` accepts repeated `--steps`, passes them into `LearnerLocalClient.submit_attempt()`, and sends:

```python
"response_steps": steps or []
```

The local session log also stores submitted `response_steps`.

Conclusion: Local Trainer does not drop `response_steps`.

### 2. Do `response_steps` enter the learner API request?

Yes.

`backend/app/api/learner/v1/schemas.py` defines:

```python
response_steps: list[str] = Field(default_factory=list)
self_explanation: str | None = None
```

`backend/app/api/learner/v1/attempts.py` forwards both fields into `LearnerAttemptAssembler`.

Conclusion: the learner API request model accepts and validates both fields.

### 3. Do `response_steps` enter the orchestrator?

Yes.

`backend/app/catalog/learner_projector.py` creates:

```python
Attempt(
    ...,
    response_steps=response_steps or [],
    self_explanation=self_explanation,
    metadata={},
)
```

`backend/app/services/learning_orchestrator.py` passes this same `Attempt` into:

```python
CompositeScoringEngine.evaluate_detailed(question, attempt, node)
DiagnosisEngine.diagnose_detailed(score_result, question, attempt, node)
```

Conclusion: the orchestrator receives an `Attempt` that contains the learner's steps and explanation.

### 4. Do `response_steps` enter the scoring engine?

They enter as fields on `Attempt`, but current scorers do not read them.

Current Phase 4.7 scorer consumption:

- `RubricScorer` reads only `attempt.user_answer`.
- `RuleScorer` reads only `attempt.user_answer`.
- `MathValidatorScorer` reads only `attempt.user_answer`.
- `ManualOverrideScorer` reads only `attempt.metadata.score_overrides`, which learner API does not allow.
- `LLMScorerStub` is inactive.

Repository search confirms no active scorer reads:

```text
attempt.response_steps
attempt.self_explanation
```

Conclusion: scoring receives an `Attempt` object with response evidence attached, but the response evidence is not integrated into scorer input text or scoring rules.

### 5. Is `self_explanation` used?

Only for transport and session logging. It is not used for scoring, diagnosis, or coach output.

Observed behavior:

- Local Trainer sends `self_explanation` when `--explanation` is provided.
- Learner API accepts it.
- `LearnerAttemptAssembler` stores it on `Attempt`.
- `LearningOrchestrator` passes the `Attempt` onward.
- Current active scorers do not read it.
- `DiagnosisEngine` receives the `Attempt`, but current detailed diagnosis is driven by `CompositeScoreResult` and scorer evidence, not the raw learner explanation.
- Local Trainer session log records it.
- `coach_output.build_coach_output()` receives only the projected submit payload, which does not include `self_explanation`.

Conclusion: `self_explanation` is preserved but not semantically consumed.

## Dimension Ownership In Current Scoring

Current dimensions are decided by scorer contributions:

| Dimension | Current sources |
| --- | --- |
| `concept` | Only if rubric/key points/patterns target `concept`, or manual override in non-learner/internal paths |
| `trigger` | Rubric items, weak RuleScorer keywords |
| `method` | Rubric items, weak RuleScorer keywords |
| `transformation` | Rubric items, weak RuleScorer keywords |
| `process` | Only if rubric/key points/patterns target `process`, or manual override in non-learner/internal paths |
| `calculation` | Rubric items, MathValidator final-answer support, missing-C checks |
| `final_answer` | MathValidator expected answer / alias / missing-C / initial-value checks |
| `expression` | Only if rubric/key points/patterns target `expression`, or manual override in non-learner/internal paths |
| `migration` | Only if rubric/key points/patterns target `migration`, or manual override in non-learner/internal paths |

For `backend/catalog_data/questions/ode-sep-001.yaml`, trusted rubric items target:

- `trigger`;
- `method`;
- `transformation`;
- `calculation`.

The expected answer and aliases allow MathValidator to affect:

- `calculation`;
- `final_answer`.

There are no rubric items targeting:

- `concept`;
- `process`;
- `expression`;
- `migration`.

Therefore, for this seed question, `concept`, `process`, `expression`, and `migration` can remain `null` even when the learner submits separate `response_steps` and `self_explanation`.

## Why `process` / `concept` / `expression` Are `null`

This is not a Local Trainer send failure.

This is not a learner API request failure.

This is not an orchestrator transport failure.

The actual causes are:

1. The seed catalog question does not define rubric items for `concept`, `process`, or `expression`.
2. The current active scorers only read `attempt.user_answer`.
3. The current active scorers do not fold `response_steps` or `self_explanation` into the text they grade.
4. `CompositeScoringEngine` intentionally leaves dimensions as `None` when no scorer contributes a score.

So the best classification is:

```text
Pipeline transport: connected.
Scoring consumption: not connected.
Catalog rubric coverage: missing for these dimensions in ode-sep-001.
Coach wording: overstates null as learner omission.
```

## Diagnosis Input And Output

`DiagnosisEngine.diagnose_detailed()` receives the `Attempt`, but its detailed path is based on:

- `CompositeScoreResult.score_vector`;
- active scorer names;
- dimension sources;
- scorer evidence;
- rubric `required_missed` / `optional_missed`;
- MathValidator missed items;
- node policy;
- score patterns.

It does not currently create concept/process/expression evidence from `response_steps` or `self_explanation`.

When those dimensions are `None`, diagnosis generally treats them as absent scorer evidence, not as proof that the learner wrote nothing.

## Coach Output Behavior

`backend/app/training/local_trainer.py` reduces the learner API response to:

- `question_id`;
- `pass_state`;
- `score_vector_summary`;
- `learner_explanation`;
- `recommended_actions`;
- movement booleans/nodes;
- `next_action_hint`.

It does not pass `response_steps` or `self_explanation` into `coach_output`.

`backend/app/training/coach_output.py` then builds:

```python
evidence_gaps = build_evidence_gaps(score_vector_summary)
```

`build_evidence_gaps()` treats a `None` dimension as a missing evidence gap. For `process`, `concept`, and `expression`, the messages say, in learner-facing terms, "please write steps / explain concept / write rigorously."

This creates a semantic mismatch:

- Engine meaning: this dimension was not scored or no scorer produced a score.
- Learner-facing wording: you did not provide this kind of evidence.

Conclusion: `coach_output` can currently mislabel an unscored dimension as if the learner omitted the evidence.

## Audit Answers

### 1. Was `response_steps` correctly sent by Local Trainer?

Yes.

### 2. Did `response_steps` enter learner API request?

Yes.

### 3. Did `response_steps` enter orchestrator?

Yes, as part of domain `Attempt`.

### 4. Did `response_steps` enter scoring engine?

Only structurally. It is present on `Attempt`, but current active scorers do not read it.

### 5. Is `self_explanation` used?

It is accepted, transported, and logged. It is not currently used for scoring, diagnosis, or coach output.

### 6. Which score dimensions are currently decided only by rubric/math/rule scorers?

All learner-visible dimensions are decided by scorer output. In learner API flow, there is no manual override. Specifically:

- Rubric controls whichever dimensions catalog rubric targets.
- MathValidator controls `final_answer` and `calculation`.
- RuleScorer provides weak signals for `trigger`, `method`, and `transformation`.
- Dimensions without scorer contribution remain `None`.

### 7. Is `process/concept/expression = null` design, missing data, or pipeline gap?

It is a combination:

- designed behavior: `CompositeScoringEngine` leaves unscored dimensions as `None`;
- catalog coverage gap: `ode-sep-001` has no rubric items for `concept`, `process`, or `expression`;
- scorer integration gap: `response_steps` and `self_explanation` are not consumed by scorers.

It is not missing transport data.

### 8. Does `coach_output.evidence_gaps` mistake "unscored dimension" for "learner did not write it"?

Yes, at the wording level.

`coach_output` only sees `score_vector_summary`. It cannot distinguish:

- learner did not provide evidence;
- learner provided evidence in `response_steps`;
- rubric did not score that dimension;
- scorer ignored the field;
- question did not intend to test that dimension.

So current gap wording is too strong when it says or implies that the learner failed to write steps/concept/expression.

### 9. What is the minimal safe fix?

Recommended minimal safe fix for a future implementation phase:

1. Do not change scoring first.
2. Keep engine decisions unchanged.
3. Pass a learner-response evidence summary into the Local Trainer projection layer, for example:

```text
response_evidence_present:
  has_response_steps
  response_step_count
  has_self_explanation
```

4. Update `coach_output` wording so `None` dimensions are described as "not yet scored / not enough scored evidence" rather than "you did not write it" when response evidence is present.
5. Keep the original `score_vector_summary`, `pass_state`, rollback, forward, and next action untouched.
6. Add narrow tests proving:
   - steps/explanation are not lost;
   - `None` dimensions no longer accuse the learner of omitting content when evidence was submitted;
   - no trusted fields leak;
   - no engine/API decision changes.

This would be a Local Trainer / coach-output display fix, not a scoring-engine fix.

If the desired product behavior is that steps and self-explanation actually change `process`, `concept`, or `expression` scores, that is a larger scoring phase. It would require explicitly designing an `AttemptEvidenceScorer` or extending `RubricScorer` / `RuleScorer` to grade a combined answer text:

```text
user_answer + response_steps + self_explanation
```

That larger fix must come with scoring red-team tests and golden eval updates, because it changes engine behavior.

### 10. Should we enter Phase 4.7.3 Implementation?

Yes, but only if Phase 4.7.3 is scoped narrowly as:

```text
Response Evidence Display Integration
```

Recommended Phase 4.7.3 scope:

- no engine changes;
- no API contract changes unless explicitly approved;
- no scoring behavior changes;
- no diagnosis behavior changes;
- no movement behavior changes;
- only improve Local Trainer / coach-output wording using locally available response evidence metadata;
- add tests for the current confusion case.

Do not enter a scoring integration phase under the name Phase 4.7.3 unless explicitly approved. Scoring integration of `response_steps` and `self_explanation` should be planned separately.

## Recommended Decision

Proceed to a narrow Phase 4.7.3 implementation only for coach-output display correctness.

Do not change the engines yet.

The immediate user-facing bug is not that the answer cannot be scored at all; it is that Local Trainer output cannot distinguish "unscored by current rubric/scorer path" from "learner did not provide the evidence."
