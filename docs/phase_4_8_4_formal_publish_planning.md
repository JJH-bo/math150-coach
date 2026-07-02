# Phase 4.8.4 Formal Publish Planning For Selected Candidates

Status: planning complete. No direct publish, formal import, formal catalog write, manifest edit, candidate edit, code change, or scoring integration is performed in this phase.

## 1. Executive Decision

Phase 4.8.4 plans how to safely move the human-review-recommended Top 3 authoring-only candidates toward a later publish workflow.

Planning scope is limited to:

1. `ode-linear-cand-002`
2. `ode-mixed-cand-001`
3. `ode-sep-cand-002`

The optional candidates are recorded only as backup context:

4. `ode-sep-cand-003`
5. `ode-hom-cand-002`

This phase does not publish, import, edit the formal catalog, edit authoring drafts, edit previews, edit reports, regenerate questions, re-score candidates, re-review candidates, or re-select candidates.

Recommended next phase:

```text
Phase 4.8.5 Authoring-only Revision Plan / Implementation For Top 3
```

Phase 4.8.5 should still operate in the authoring-only area first. Direct formal publish remains out of scope until a later explicit publish phase.

## 2. Scope And Non-goals

In scope:

- define publish-readiness plans for the Top 3 candidates;
- record optional candidates as backups only;
- define required authoring revisions before publish planning can continue;
- define rubric and answer alias review plans;
- define learner-safe and formal catalog boundary plans;
- define validation and dry-run plan for a future authoring-only revision phase;
- define go/no-go criteria for a later true publish workflow.

Out of scope:

- modifying authoring draft YAML;
- modifying dry-run previews;
- modifying validation reports;
- modifying the batch manifest;
- modifying `backend/catalog_data/manifest.yaml`;
- adding formal question YAML;
- executing formal publish or formal import;
- writing candidates into learner-visible catalog;
- modifying candidate content;
- regenerating questions;
- re-reviewing or re-scoring candidates;
- selecting a different candidate set;
- modifying engines, API, learner projector, Local Trainer, coach output, CatalogValidator, or authoring/import CLI;
- adding endpoint, history, frontend, database, auth, LLM, mastery, review, or formal persistence;
- scoring integration;
- entering Phase 4.8.5 or Phase 4.9.

## 3. Human Review Baseline

Phase 4.8.3B recorded the human reviewer results:

- 8/8 candidates reviewed.
- hard fail: 0.
- `strong_candidate`: 4.
- `revise_then_review`: 4.
- `defer`: 0.
- `reject`: 0.

Human reviewer recommended Top 3 for later formal publish planning:

1. `ode-linear-cand-002`
2. `ode-mixed-cand-001`
3. `ode-sep-cand-002`

Optional Top 5 additions if later needed:

4. `ode-sep-cand-003`
5. `ode-hom-cand-002`

This is a human reviewer recommendation summary only. It is not a formal catalog selection, manifest change, import, or publish.

## 4. Planning Candidate Set

P0 planning candidate set:

| Candidate | Node | Human score | Human recommendation | P0 planning status |
| --- | --- | ---: | --- | --- |
| `ode-linear-cand-002` | `ode_first_order_linear` | 89.5 | `strong_candidate` | in Top 3 scope |
| `ode-mixed-cand-001` | `ode_first_order_linear` | 91.5 | `strong_candidate` | in Top 3 scope |
| `ode-sep-cand-002` | `ode_separable` | 86 | `strong_candidate` | in Top 3 scope |

Optional backup candidates:

| Candidate | Node | Human score | Human recommendation | P0 planning status |
| --- | --- | ---: | --- | --- |
| `ode-sep-cand-003` | `ode_separable` | 85.5 | `strong_candidate` | backup only |
| `ode-hom-cand-002` | `ode_homogeneous_first_order` | 82.5 | `revise_then_review` | backup only |

## 5. Why Top 3 Only

Top 3 only is the safest P0 publish-planning scope because:

- Phase 4.8.3B selected them as the strongest human-reviewed set.
- The set keeps the next phase small enough for controlled authoring-only revisions.
- It includes method recognition and standard-form transformation, not just direct computation.
- It avoids promoting every strong candidate before validator and alias behavior are rechecked.
- It avoids bringing initial-condition and homogeneous-equivalence risks into the first publish-planning pass.

The optional candidates remain useful but are not part of the current P0 publish plan.

## 6. Candidate-specific Publish-readiness Plans

### `ode-linear-cand-002`

Human reviewer baseline:

- recommendation: `strong_candidate`
- score: 89.5
- core value: trains rewriting into standard form `y' + 2y = 3x` before applying first-order linear method.

Publish-readiness plan:

- Check and strengthen answer aliases.
- Allow equivalent ordering of `3x/2 - 3/4 + C e^(-2x)`.
- Allow spaces, explicit multiplication, omitted multiplication, and term-order variation.
- Keep standard-form transformation as the core scoring point.
- Do not weaken the transformation rubric.
- Confirm `expected_answer` and aliases are not too narrow.
- Confirm final answer forms with the homogeneous term before or after the particular term are accepted.
- Confirm public prompt is not further expanded with direct scoring clues.

Draft areas to inspect in a future authoring-only revision:

- `trusted_scoring.expected_answer`
- `trusted_scoring.answer_aliases`
- rubric item `transformation_standard_form`
- rubric item `final_answer_linear_general`
- `solution_outline`
- `validator_config`

### `ode-mixed-cand-001`

Human reviewer baseline:

- recommendation: `strong_candidate`
- score: 91.5
- core value: trains method recognition; learners should not force separation and should identify first-order linear form.

Publish-readiness plan:

- Add a trigger/diagnostic rubric item in the future authoring-only revision.
- Check whether the learner explains the equation has the form `y' + P(x)y = Q(x)`.
- Check whether the learner explains why forced separation is not the reliable method.
- Avoid giving high scores for only writing `linear` or `integrating factor`.
- Preserve answer aliases for both `xy=x^3/3+C` and `y=x^2/3+C/x`.
- Confirm the `x>0` condition is consistent in prompt, solution outline, and integrating factor usage.
- Confirm the integrating factor `x` is recognized as valid under `x>0`.
- Confirm rubric separates method recognition from final computation.

Draft areas to inspect in a future authoring-only revision:

- public prompt and hint wording;
- trigger rubric item;
- new diagnostic rubric item;
- method rubric item;
- transformation rubric item for integrating factor `x`;
- answer aliases;
- solution outline;
- validator config.

### `ode-sep-cand-002`

Human reviewer baseline:

- recommendation: `strong_candidate`
- score: 86
- core value: trains rearrangement before separating variables.

Publish-readiness plan:

- Reduce method prompting in the public prompt.
- Do not directly say "becomes separable" in the public prompt.
- Ask the learner to decide the method from the equation.
- Change preferred main answer to `y=C(1+x^2)` in the future authoring-only revision.
- Preserve `ln|y|=ln(1+x^2)+C` as an alias or trusted equivalent form.
- Check whether zero-solution and arbitrary-constant absorption need to be mentioned in the solution outline.
- Keep rearrangement and transformation as core scoring points.
- Confirm rubric still checks the separated form after prompt wording is weakened.

Draft areas to inspect in a future authoring-only revision:

- public prompt wording;
- trusted expected answer;
- answer aliases;
- solution outline;
- trigger and method rubric items;
- transformation rubric item;
- validator config.

## 7. Required Authoring Revisions

Future authoring-only revisions should be performed only after explicit Phase 4.8.5 approval.

Required revision themes:

- reduce public prompt over-hinting;
- strengthen answer aliases for equivalent forms;
- keep trusted solution details out of public fields;
- preserve or strengthen transformation scoring;
- avoid rubric rules that reward keyword stuffing;
- avoid rubric rules that are too narrow for equivalent expressions;
- keep all changes inside the authoring-only workspace until a later publish phase is explicitly approved.

Candidate-specific required revisions:

| Candidate | Required revision summary |
| --- | --- |
| `ode-linear-cand-002` | strengthen aliases for equivalent ordering and formatting; preserve standard-form transformation scoring |
| `ode-mixed-cand-001` | add diagnostic trigger item for why it is linear and not forced separation; avoid keyword-only high score |
| `ode-sep-cand-002` | reduce public method hinting; use `y=C(1+x^2)` as preferred answer and keep log form as alias |

## 8. Rubric Revision Plan

Future rubric revision should be conservative and authoring-only.

Rules:

- Preserve current scoring dimensions: `trigger`, `method`, `transformation`, `calculation`, `final_answer`.
- Do not add `concept`, `process`, or `expression` scoring unless a separate scoring integration phase approves it.
- Prefer expected patterns for structural evidence when keywords alone are too weak.
- Do not let a single keyword produce high score when method evidence is missing.
- Keep transformation as a first-class rubric dimension for `ode-linear-cand-002` and `ode-sep-cand-002`.
- Add diagnostic trigger evidence for `ode-mixed-cand-001`.

Candidate focus:

- `ode-linear-cand-002`: keep `transformation_standard_form` central; consider patterns for `y'+2y=3x` formatting variants.
- `ode-mixed-cand-001`: add item that captures `y' + P(x)y = Q(x)` recognition and non-separability reasoning.
- `ode-sep-cand-002`: make trigger/method rubric compatible with a less over-hinted prompt.

## 9. Validator / Answer Alias Review Plan

Future validator and alias review should check:

- equivalent answer ordering;
- spacing and multiplication variants;
- exponential notation variants where relevant;
- log-form and explicit-form equivalence for separable answers;
- arbitrary constant absorption;
- consistency of conditions such as `x>0`;
- avoidance of overly broad aliases that accept wrong answers.

Candidate focus:

- `ode-linear-cand-002`: accept term order variants such as `Ce^(-2x)+3x/2-3/4`; check spaces and multiplication.
- `ode-mixed-cand-001`: keep both `xy=x^3/3+C` and `y=x^2/3+C/x`; preserve `x>0` consistency.
- `ode-sep-cand-002`: use `y=C(1+x^2)` as preferred form; keep `ln|y|=ln(1+x^2)+C` as trusted equivalent form.

## 10. Learner-safe Boundary Plan

Before any candidate moves toward publish workflow, future reviewers must confirm:

- public prompt contains no expected answer;
- public prompt contains no solution outline;
- public prompt does not expose rubric wording;
- hints guide strategy without revealing the answer;
- trusted fields remain server-side only;
- review records and this planning document are not learner-facing artifacts;
- dry-run previews and validation reports are not learner-visible;
- Local Trainer public output must not expose trusted material.

For Top 3, public prompt revisions should reduce over-hinting without making the prompt ambiguous.

## 11. Formal Catalog Boundary Plan

Formal catalog boundary for Phase 4.8.4:

- no formal catalog write;
- no manifest edit;
- no formal question YAML added;
- no candidate registered in learner-visible catalog;
- no formal import;
- no formal publish.

Future boundary:

- Phase 4.8.5 may revise authoring-only drafts only if explicitly approved.
- A later publish workflow phase must be explicitly approved before any formal catalog files are considered.
- Formal publish should have its own freeze/audit step.
- Formal catalog writes must not be mixed with scoring integration, frontend, database, history, LLM, mastery, or review scheduling work.

## 12. Validation And Dry-run Plan

Future safe workflow:

```text
1. Revise selected authoring drafts in authoring-only area.
2. Run validate-draft.
3. Run validate-batch.
4. Run build-candidate-dry-run.
5. Human inspect revised preview.
6. Confirm learner-safe/trusted boundary.
7. Only after explicit later approval, prepare formal publish/import phase.
8. Only in that later phase may formal catalog writes be considered.
```

This Phase 4.8.4 document does not execute the workflow above.

Expected validation checks in the future revision phase:

- all Top 3 revised drafts pass `validate-draft`;
- Top 3 batch or full batch passes `validate-batch`;
- dry-run previews are regenerated under authoring previews;
- revised previews remain `dry_run_only=true`;
- formal catalog manifest remains unchanged until a later publish phase;
- learner API still cannot see revised candidates before formal publish.

## 13. Risk Analysis

1. Human review recommendation may be misread as formal catalog selection.
   - Mitigation: this document states recommendations are planning input only.
2. Planning may be accidentally executed as publish.
   - Mitigation: publish is explicitly out of scope; future workflow is listed but not executed.
3. Direct formal catalog edits may pollute learner API.
   - Mitigation: keep Phase 4.8.5 authoring-only and require later explicit publish approval.
4. Prompt revisions may desync training value and scoring rules.
   - Mitigation: revise public prompt and rubric together in authoring-only drafts, then dry-run.
5. Rubric strengthening may become too broad or too narrow.
   - Mitigation: human review revised rubric and check both keyword-stuffing and equivalent-expression cases.
6. Answer aliases may be incomplete and reject correct answers.
   - Mitigation: review equivalent forms and formatting variants for each Top 3 candidate.
7. Mixed recognition rubric may fail to detect why forced separation is not reliable.
   - Mitigation: add diagnostic trigger item and inspect revised preview manually.
8. Initial-value candidate is not in Top 3 because validator stability needs more confirmation.
   - Mitigation: keep `ode-sep-cand-003` as backup for a later focused validator review.
9. Homogeneous candidate is not in Top 3 because equivalent substitution and ratio-form support need more work.
   - Mitigation: keep `ode-hom-cand-002` as backup for a later alias/pattern strengthening pass.
10. Trusted-only review content may leak into learner-facing docs or outputs.
    - Mitigation: keep review packets, planning docs, answer keys, rubrics, and solution outlines internal.

## 14. Go / No-Go Criteria For Later Publish

Go criteria before entering a true publish workflow:

- Top 3 required changes are completed in authoring-only drafts.
- Top 3 revised drafts pass `validate-draft`.
- Batch validation passes.
- Dry-run previews are generated successfully.
- Public prompts do not leak answers or over-prompt the method.
- Expected answers and aliases are manually confirmed.
- Rubrics support `trigger`, `method`, `transformation`, `calculation`, and `final_answer`.
- Learner-safe/trusted boundary is manually confirmed.
- Formal catalog manifest remains unchanged until the formal publish phase.
- Human reviewer explicitly approves entering publish workflow.

No-go criteria:

- mathematical error;
- node mismatch;
- public prompt leaks answer or trusted logic;
- trusted material leaks into learner-facing fields;
- answer aliases are unreliable;
- validator config is unreliable or illegal;
- rubric keywords are too narrow and cause obvious false negatives;
- rubric keywords are too broad and reward keyword stuffing;
- draft still needs substantial rewrite;
- any attempt is made to edit the formal catalog without explicit approval.

## 15. P0 / P1 / P2 Cutline

P0 planning, current phase:

- Plan Top 3 only.
- Do not edit drafts.
- Do not publish.
- Do not write formal catalog.
- Do not perform scoring integration.
- Output this formal publish planning document.

P1 future implementation:

- Revise Top 3 drafts in the authoring-only area.
- Run validation and dry-run commands.
- Generate revised previews.
- Have human reviewer inspect revised previews.
- Keep learner API unable to see revised candidates.

P2 future publish workflow:

- After explicit approval, design formal publish/import.
- Formal catalog YAML and manifest changes may be considered only in that later phase.
- Add a separate freeze/audit after any publish workflow.
- Do not combine with scoring integration, history, frontend, database, LLM, mastery, or review scheduling.

## 16. Proposed Next Phase Instruction Summary

Suggested future instruction:

```text
Execute Phase 4.8.5 Authoring-only Revision Plan / Implementation For Top 3.

Revise only the Top 3 authoring-only drafts: ode-linear-cand-002, ode-mixed-cand-001, and ode-sep-cand-002.
Apply the Phase 4.8.4 publish-readiness plan.
Do not modify formal catalog files, manifest, engines, API, Local Trainer, coach output, CatalogValidator, or authoring CLI.
Run validate-draft, validate-batch, and build-candidate-dry-run after authoring-only revisions.
Keep revised previews dry-run only.
Do not publish and do not write formal catalog files.
```

The output of Phase 4.8.5 should be revised authoring-only drafts, validation reports, dry-run previews, and a revision report only, if explicitly approved.
