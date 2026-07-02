# Phase 4.8.2 Plan: Human Review And Candidate Selection

Status: plan complete. No candidate selection, formal publish, catalog write, code change, or scoring integration is performed in this phase.

## 1. Executive Decision

Phase 4.8.2 defines the human review and candidate selection plan for the 8 Phase 4.8 authoring-only ODE candidates.

Decision:

- Proceed to a later actual human review only after explicit approval.
- Use a 1-5 human review rubric with weighted total score out of 100.
- In the later review phase, select only 3-5 candidates for possible formal publish planning.
- Do not select candidates in Phase 4.8.2.
- Do not publish candidates in Phase 4.8.2.
- Do not modify authoring drafts, previews, reports, formal catalog files, engines, APIs, Local Trainer, coach output, or validator code.

Recommended next phase:

```text
Phase 4.8.3 Actual Human Review Of Authoring Candidates
```

## 2. Current Candidate Baseline

Phase 4.8 created 8 authoring-only candidates under:

```text
backend/catalog_authoring/phase_4_8/
```

All candidates are original same-type ODE practice items with authoring-only source metadata. Phase 4.8.1 froze the boundary:

- `validate-draft`: 8/8 passed.
- `validate-batch`: 8 passed, 0 failed.
- `build-candidate-dry-run`: 8/8 succeeded.
- Dry-run previews are preview-only.
- Content hashes belong only to dry-run previews.
- Formal catalog manifest is unchanged.
- Formal question YAML is unchanged.
- Learner API still exposes only `ode-sep-001`.
- Candidate direct lookup through learner API returns 404.

Current candidates:

| Question ID | Node | Difficulty | Response mode | Design intent |
| --- | --- | --- | --- | --- |
| `ode-sep-cand-001` | `ode_separable` | basic | optional | direct separable general solution |
| `ode-sep-cand-002` | `ode_separable` | standard | optional | rearrange before separating variables |
| `ode-sep-cand-003` | `ode_separable` | standard | required | separable initial-value problem |
| `ode-hom-cand-001` | `ode_homogeneous_first_order` | standard | optional | homogeneous trigger with `y=vx` |
| `ode-hom-cand-002` | `ode_homogeneous_first_order` | standard | required | identify homogeneity before ratio substitution |
| `ode-linear-cand-001` | `ode_first_order_linear` | standard | optional | first-order linear standard form |
| `ode-linear-cand-002` | `ode_first_order_linear` | standard | required | rewrite into first-order linear standard form |
| `ode-mixed-cand-001` | `ode_first_order_linear` | standard | required | mixed recognition: linear method over forced separation |

The current review checklist embedded in drafts is only a dry-run workflow gate. It is not a final human selection result.

## 3. Why Human Review Comes Before Formal Publish

Validation passing is necessary but not sufficient for learner-facing publication.

Human review must come before formal publish because it checks qualities that the current validator cannot fully judge:

- whether the equation and solution are mathematically correct;
- whether the intended node truly matches the problem's trigger;
- whether the prompt trains a useful examination skill rather than only mechanical computation;
- whether the rubric can reliably score real learner answers;
- whether answer aliases cover common equivalent forms without over-accepting wrong answers;
- whether source and copyright status is safe;
- whether the learner-safe presentation hides trusted scoring material;
- whether a small P0 catalog remains balanced instead of overloading one node or one difficulty.

No candidate should enter formal publish planning only because the authoring CLI produced a preview or a content hash.

## 4. Non-goals

Phase 4.8.2 does not:

- modify the 8 draft YAML files;
- modify the batch manifest;
- modify reports or previews;
- modify `backend/catalog_data/manifest.yaml`;
- add formal question YAML;
- execute formal import or formal publish;
- choose actual candidates for publication;
- change scoring, diagnosis, rollback, forward, orchestration, API, learner projector, Local Trainer, coach output, CatalogValidator, or authoring CLI behavior;
- add endpoint, frontend, database, auth, LLM, mastery, review, history, or formal persistence;
- perform scoring integration for `response_steps` or `self_explanation`;
- enter Phase 4.8.3 or Phase 4.9.

## 5. Review Dimensions

Each candidate should receive a 1-5 score for each dimension.

Scoring scale:

- 5: excellent, ready for formal publish planning on this dimension;
- 4: good, only minor review notes;
- 3: usable but needs revision or second review;
- 2: weak, likely defer unless strategically important;
- 1: unacceptable for this phase or triggers serious revision;
- 0: hard fail, if the dimension violates a non-negotiable safety or correctness rule.

Review dimensions:

1. Mathematical correctness: equation validity, solution correctness, answer clarity, no hidden ambiguity.
2. Trigger clarity: whether the problem trains a clear ODE entry point, such as separable, homogeneous first-order, first-order linear, or mixed recognition.
3. Training value: whether the item improves exam-relevant ODE ability rather than only mechanical algebra.
4. Difficulty fit: whether it suits P0 catalog expansion without being too hard, too broad, or too narrow.
5. Node match: whether `node_id` genuinely matches the problem's required method.
6. Rubric reliability: whether rubric items can support trigger, method, transformation, calculation, and final answer scoring.
7. Validator reliability: whether expected answer, aliases, and validator config can support reasonable grading.
8. Learner-safe boundary: whether public fields avoid answer, rubric, solution outline, and trusted scoring leakage.
9. Source / copyright safety: whether the candidate is original or clearly authorized and not copied from protected material.
10. Publish risk: whether formal catalog entry could mislead learners, pollute the API, or create maintenance risk.

## 6. Review Scoring Rubric

Recommended weighted score, total 100:

| Dimension | Weight | Reason |
| --- | ---: | --- |
| Mathematical correctness | 20 | A mathematically wrong item must not enter formal publish planning. |
| Trigger clarity | 15 | The system trains node entry and recognition, not only final answers. |
| Training value | 15 | The P0 catalog should improve real ODE practice quality. |
| Rubric reliability | 15 | Scoring depends on reliable rubric signals before broader integration exists. |
| Validator reliability | 10 | Lightweight validation must not over-reject or over-accept common answers. |
| Node match | 10 | Movement and diagnosis depend on correct node alignment. |
| Difficulty fit | 5 | P0 should remain compact and usable, not exhaustive. |
| Learner-safe boundary | 5 | Public/trusted separation remains non-negotiable. |
| Source / copyright safety | 5 | Formal publish planning requires clean source status. |

Publish risk is reviewed separately as a go/no-go modifier. If publish risk is high, the candidate should be revised, deferred, or rejected even if the numeric score is acceptable.

Weighted score conversion:

```text
weighted_points = (dimension_score / 5) * dimension_weight
```

Hard-fail dimensions should override the numeric score.

## 7. Candidate Review Template

Use the following template for each candidate in Phase 4.8.3. Do not fill it in during Phase 4.8.2.

```text
Candidate ID:
Question ID:
Node:
Reviewer:
Review date:

1. Mathematical correctness score:
Notes:

2. Trigger clarity score:
Notes:

3. Training value score:
Notes:

4. Difficulty fit score:
Notes:

5. Node match score:
Notes:

6. Rubric reliability score:
Notes:

7. Validator reliability score:
Notes:

8. Learner-safe boundary score:
Notes:

9. Source/copyright status score:
Notes:

10. Publish risk score:
Notes:

Total weighted score:

Hard fail triggered: yes/no
Hard fail reason:

Recommendation:
- strong_candidate
- revise_then_review
- defer
- reject

Required changes before publish planning:

Reviewer final note:
```

## 8. Selection Rules

Numeric score bands:

- 85-100: strong candidate; can enter formal publish planning if no hard fail exists.
- 75-84: keep for revision or second review; do not publish without changes or confirmation.
- 60-74: defer; useful idea but not ready for P0 formal planning.
- Below 60: reject for formal publish planning.

Hard fail conditions:

Any one of the following makes the candidate no-go regardless of numeric score:

- mathematical error;
- `node_id` mismatch;
- public prompt leaks the expected answer;
- public prompt leaks trusted field wording, rubric content, or solution outline;
- source/copyright status is unclear or unsafe;
- expected answer is clearly unreliable;
- rubric cannot support basic scoring;
- validator config uses illegal keys;
- problem requires a node that does not exist;
- problem is outside current P0 scope;
- formal publish would expose a candidate that still needs authoring-only revision.

Selection target for Phase 4.8.3:

- Do not choose all 8 candidates by default.
- Prefer 3-5 selected candidates.
- Require at least 1 candidate for `ode_separable`.
- Require at least 1 candidate for `ode_homogeneous_first_order`.
- Require at least 1 candidate for `ode_first_order_linear`.
- Include `ode-mixed-cand-001` only if rubric and validator reliability are strong enough.
- Include an initial-value candidate only if reviewer confirms that expected answer, aliases, and validator config can handle initial condition resolution.

## 9. Minimum Publish-readiness Criteria

A candidate is minimally ready for formal publish planning only if all are true:

- no hard fail condition is present;
- weighted score is at least 85, or the candidate has an explicit second-review exception;
- mathematical correctness score is at least 4;
- node match score is at least 4;
- rubric reliability score is at least 4;
- validator reliability score is at least 4 for calculation or final-answer items;
- learner-safe boundary score is 5;
- source/copyright safety score is 5;
- source metadata is present and credible;
- public prompt does not contain answer key, solution outline, or trusted scoring wording;
- all trusted scoring fields remain server-side only;
- reviewer records required changes before any later formal publish planning.

## 10. Rejection / Defer Criteria

Reject a candidate if:

- it has mathematical errors that require rewriting the problem;
- the intended node is wrong or unclear;
- the public prompt leaks the answer or trusted scoring;
- the expected answer is unusable;
- the rubric cannot score the intended skill;
- it copies or appears to copy an external source without authorization;
- it requires a missing node or out-of-scope method;
- it would likely create learner confusion if published as-is.

Defer a candidate if:

- the problem idea is valuable but needs substantial rewrite;
- it requires better answer aliases;
- it needs stronger validator support;
- it depends on future response-step scoring integration;
- it is too similar to an already selected item;
- it would unbalance the small P0 catalog.

## 11. Node Coverage Policy

The Phase 4.8.3 review should protect minimal node coverage.

Recommended selected set:

- 1-2 `ode_separable` candidates.
- 1 `ode_homogeneous_first_order` candidate.
- 1 `ode_first_order_linear` candidate.
- optional 1 mixed recognition candidate if reliable.

Do not select only separable items, even if they score well. The goal is real practice across nearby ODE entry points.

Do not select a candidate that requires a missing node or new graph behavior.

## 12. Difficulty Balance Policy

The selected 3-5 candidates should include:

- at least one basic or low-standard item to keep the trainer approachable;
- at least two standard items to test real ODE recognition and transformation;
- no comprehensive item in P0 unless it is clearly bounded and easy to validate.

Avoid:

- selecting too many near-identical computation drills;
- selecting only required-response-mode items;
- selecting items whose difficulty depends on hidden algebra complexity instead of ODE reasoning.

## 13. Rubric Reliability Policy

Human review must check whether each rubric supports the actual scoring contract.

Rubric review requirements:

- Does it cover `trigger`?
- Does it cover `method`?
- Does it cover `transformation`?
- Does it cover `calculation`?
- Does it cover `final_answer` where the prompt asks for a solution?
- Are required keywords or expected patterns too broad?
- Are required keywords or expected patterns too narrow?
- Could keyword stuffing be misread as real understanding?
- Could reasonable equivalent expressions be missed?
- Do answer aliases cover common equivalent forms?
- Does validator config support the expected answer without illegal keys?
- Should `concept`, `process`, or `expression` remain unscored for this item?

Phase 4.8.3 should not force `concept`, `process`, or `expression` scoring unless the prompt and rubric can support them reliably.

## 14. Source / Copyright Review Policy

Human review must confirm:

- the item is original or explicitly authorized;
- it is not copied from a textbook, PDF, lecture note, exam-prep source, or past exam;
- source metadata is present;
- copyright notes are present;
- no long external passage appears in public prompt, trusted scoring, or notes;
- AI-assisted original status is clearly recorded when applicable.

If source status is unclear, the candidate is no-go for formal publish planning.

## 15. Learner Training Value Policy

A candidate has high training value when it helps the learner practice at least one of:

- recognizing the method trigger;
- choosing between nearby ODE methods;
- transforming the equation into a solvable standard form;
- avoiding a common ODE error;
- carrying calculation through to a correct general or particular solution;
- explaining why a method applies.

Low training value indicators:

- pure mechanical integration with no meaningful ODE entry decision;
- prompt gives away the method too strongly for the intended node;
- rubric rewards surface keywords more than correct reasoning;
- answer form is so narrow that correct learners may be penalized;
- item duplicates another selected candidate without adding a new skill.

## 16. Risk Analysis

1. Selecting all 8 candidates: this would overrun P0 and reduce review quality. Mitigation: cap selection at 3-5.
2. Publishing because validation passed: validation is not human math review. Mitigation: require explicit human review and later publish approval.
3. Mixed recognition node mismatch: mixed items can be useful but easy to misalign. Mitigation: include only if node match and rubric reliability are strong.
4. Initial-value validation risk: particular-solution checks can be brittle. Mitigation: require validator reliability review before selection.
5. Keyword-based rubric weakness: current rubric may reward surface text. Mitigation: inspect required keywords and expected patterns manually.
6. Equivalent answer miss: aliases may be incomplete. Mitigation: review common equivalent forms.
7. Public/trusted leakage: prompt or hints might reveal too much. Mitigation: learner-safe boundary review is mandatory.
8. Copyright uncertainty: generated variants still need source review. Mitigation: source/copyright score is mandatory and hard fail eligible.
9. Formal catalog pollution: accidental manifest edit would expose unfinished candidates. Mitigation: Phase 4.8.3 remains review-only unless separately approved.
10. Scope creep: review can turn into rewriting, scoring integration, or publish. Mitigation: separate those into later explicit phases.

## 17. P0 / P1 / P2 Cutline

P0:

- Human review the existing 8 candidates.
- Score each candidate using the review rubric.
- Select 3-5 candidates for possible formal publish planning.
- Record hard fail, revision, defer, and rejection reasons.
- Do not publish.

P1:

- Revise selected or near-selected candidates.
- Improve aliases or rubric wording.
- Consider adding carefully bounded `concept`, `process`, or `expression` rubric items where reliable.
- Prepare a formal publish planning proposal for the selected subset.

P2:

- Formal publish/export workflow.
- Broader ODE catalog expansion.
- Stronger runtime content-hash verification.
- Attempt evidence scoring integration.
- History, review scheduler, frontend, database, mastery, or next-question behavior.

## 18. Go / No-Go For Phase 4.8.3 Actual Human Review

Go for Phase 4.8.3 if the requested work is:

- review the 8 existing authoring-only candidates;
- use the rubric in this document;
- fill one review record per candidate;
- recommend 3-5 candidates for later formal publish planning;
- do not edit draft YAML during review;
- do not publish or write formal catalog files.

No-go if the request includes:

- direct formal catalog write;
- manifest edit;
- formal import or publish;
- new candidate creation;
- draft rewriting during review;
- scoring engine changes;
- API changes;
- Local Trainer changes;
- frontend, database, history, auth, LLM, mastery, review scheduling, or formal persistence.

## 19. Proposed Phase 4.8.3 Instruction Summary

Suggested future instruction:

```text
Execute Phase 4.8.3 Actual Human Review Of Authoring Candidates.

Review the 8 Phase 4.8 authoring-only candidates using docs/phase_4_8_2_human_review_selection_plan.md.
Do not modify draft YAML, previews, reports, formal catalog manifest, formal question YAML, engines, API, Local Trainer, coach output, or validator code.
For each candidate, fill the review template with scores, notes, hard-fail status, and recommendation.
Recommend 3-5 candidates for later formal publish planning, but do not publish and do not write formal catalog files.
```

The output of Phase 4.8.3 should be review records and a candidate recommendation summary only.
