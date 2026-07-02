# Phase 4.8 Plan: Minimal Catalog Expansion For Real Practice

Status: plan complete. No implementation performed.

Phase 4.8 should plan a small, controlled expansion of learner-visible ODE practice questions. It must not write formal catalog YAML, change the manifest, modify engines/API/Local Trainer/coach output, add endpoints, add persistence, or perform scoring integration.

## 1. Executive Decision

Recommended decision: proceed to a narrow Phase 4.8 Implementation only after explicit approval, and implement it through the existing authoring/import workflow rather than by directly editing the formal catalog.

Recommended route:

```text
authoring draft -> validate-draft / validate-batch -> build-candidate-dry-run -> human review -> later formal publish decision
```

Do not directly write `backend/catalog_data/manifest.yaml` or new formal `backend/catalog_data/questions/*.yaml` in the planning phase.

Recommended P0 question scope: 8 candidate questions, all bound to existing ODE nodes:

- 3 for `ode_separable`
- 2 for `ode_homogeneous_first_order`
- 2 for `ode_first_order_linear`
- 1 mixed recognition question using existing separable/linear node context

Keep `ode_bernoulli` as P1 unless P0 validation capacity is clearly sufficient.

Do not include exact equations in P0 because no `exact_equation` node currently exists in the ODE node catalog.

## 2. Current Catalog Baseline

### Formal Catalog Files

Current formal catalog root:

```text
backend/catalog_data/
```

Current manifest:

```text
catalog_schema_version: "1.0"
questions:
  - questions/ode-sep-001.yaml
  - questions/ode-sep-draft-001.yaml
  - questions/ode-sep-retired-001.yaml
  - questions/ode-sep-internal-001.yaml
```

There is no `backend/catalog_data/nodes/` directory. Runtime nodes are loaded from the existing ODE seed graph.

### Current Formal Catalog Records

| question_id | node_id | status | audience | learner-visible |
| --- | --- | --- | --- | --- |
| `ode-sep-001` | `ode_separable` | `published` | `learner` | yes |
| `ode-sep-draft-001` | `ode_separable` | `draft` | `learner` | no |
| `ode-sep-retired-001` | `ode_separable` | `retired` | `learner` | no |
| `ode-sep-internal-001` | `ode_separable` | `published` | `internal` | no |

Current learner-visible question count: 1.

### Existing Candidate Nodes

Current ODE seed graph includes:

- `ode_separable`
- `ode_homogeneous_first_order`
- `ode_first_order_linear`
- `ode_integrating_factor`
- `ode_bernoulli`
- many later ODE nodes

No `exact_equation` node exists, so exact equations should not be part of P0.

### Current `ode-sep-001` Structure

`ode-sep-001` is a learner-visible published question for `ode_separable`.

Public presentation:

- `title`: Separable equation basic check
- `stem`: solve a first-order ODE and explain the method trigger
- `prompt_markdown`: asks to solve `dy/dx = 2xy`, state why separable, separate variables, integrate, and give general solution
- `answer_format`: `expression_with_reasoning`
- `response_step_mode`: `optional`
- `difficulty`: `basic`
- `hints_public`: one public hint

Trusted scoring:

- `expected_answer`: `ln|y|=x^2+C`
- `answer_aliases`: includes `y=Ce^(x^2)` and normalized log form
- rubric items cover:
  - `trigger`
  - `method`
  - `transformation`
  - `calculation`
- validator config:
  - `requires_constant: true`

Current gap: it does not score `concept`, `process`, `expression`, or `migration`. Phase 4.7.3 already displays those as unscored dimensions instead of accusing the learner of omitting them.

## 3. Why Catalog Expansion Is Next

The Local Trainer can now:

- list public learner questions;
- show a public question;
- submit an answer;
- write local JSONL session logs;
- display coach-facing summaries and next-step guidance;
- separate true action gaps from unscored dimensions.

The main current blocker is no longer trainer execution or coach-output wording. The blocker is that one learner-visible question cannot support realistic repeated practice.

A minimal catalog expansion lets us test:

- repeated `list/show/submit` use;
- whether coach output remains understandable across nearby ODE types;
- whether rollback/forward behavior stays stable with multiple node contexts;
- whether authoring/import dry-run workflow is enough before formal publishing.

## 4. Non-goals

Phase 4.8 Plan and the proposed P0 do not:

- add formal question YAML during planning;
- modify `backend/catalog_data/manifest.yaml`;
- modify formal catalog samples during planning;
- modify ODE nodes YAML;
- modify scoring, diagnosis, rollback, forward, or orchestration engines;
- modify API routes or learner response projector;
- modify Local Trainer or `coach_output`;
- add endpoint, database, frontend, auth, LLM, mastery/review, history, next-question recommendation, or formal persistence;
- perform scoring integration for `response_steps` or `self_explanation`;
- change golden eval cases;
- copy textbook/PDF/lecture original questions into the catalog.

## 5. Candidate Node Scope

P0 should use only existing nodes:

| priority | node_id | reason |
| --- | --- | --- |
| P0 | `ode_separable` | current learner-visible node; easiest baseline expansion |
| P0 | `ode_homogeneous_first_order` | direct successor of separable; trains `y=vx` trigger/transformation |
| P0 | `ode_first_order_linear` | direct successor context; trains standard form and integrating factor path |
| P0 optional | mixed separable/linear recognition under existing node context | trains trigger contrast without adding a new node |
| P1 | `ode_integrating_factor` | useful subskill, but may be too narrow for first expansion |
| P1 | `ode_bernoulli` | exists, but adds more transformation complexity |
| Not P0 | exact equations | no current node; do not create graph scope in catalog expansion |

## 6. Candidate Question Matrix

These are planning candidates only. Do not write them to formal catalog in this phase.

| candidate_id | target node | design intent | difficulty | response mode | planned rubric dimensions | validator config |
| --- | --- | --- | --- | --- | --- | --- |
| `ode-sep-cand-001` | `ode_separable` | direct separable equation, general solution | basic | optional | trigger, method, transformation, calculation, final_answer | `requires_constant: true` |
| `ode-sep-cand-002` | `ode_separable` | simple rearrangement before separation | standard | optional | trigger, method, transformation, calculation, final_answer | `requires_constant: true` |
| `ode-sep-cand-003` | `ode_separable` | separable equation with initial condition | standard | required | trigger, method, transformation, calculation, final_answer | `requires_initial_condition: true` |
| `ode-hom-cand-001` | `ode_homogeneous_first_order` | standard `y/x` substitution | standard | optional | trigger, method, transformation, calculation | `requires_constant: true` |
| `ode-hom-cand-002` | `ode_homogeneous_first_order` | first identify homogeneity, then substitute | standard | required | trigger, method, transformation, calculation | `requires_constant: true` |
| `ode-linear-cand-001` | `ode_first_order_linear` | already in `y' + P(x)y = Q(x)` standard form | standard | optional | trigger, method, transformation, calculation, final_answer | `requires_constant: true` |
| `ode-linear-cand-002` | `ode_first_order_linear` | rearrange into standard form before integrating factor | standard | required | trigger, method, transformation, calculation, final_answer | `requires_constant: true` |
| `ode-mixed-cand-001` | `ode_separable` or `ode_first_order_linear` | decide separable vs first-order linear before solving | standard | required | trigger, method, transformation | depends on final selected prompt |

Optional P1 candidates:

| candidate_id | target node | design intent | reason deferred |
| --- | --- | --- | --- |
| `ode-if-cand-001` | `ode_integrating_factor` | compute and apply integrating factor | better after first-order linear basics stabilize |
| `ode-bern-cand-001` | `ode_bernoulli` | recognize Bernoulli and transform to linear | higher transformation complexity |

Suggested P0 count: 8 candidates. If implementation risk feels high, start with 6 by dropping `ode-hom-cand-002` and `ode-mixed-cand-001`.

## 7. Question Design Requirements

Each candidate question plan must include:

- `question_id`
- `logical_question_id`
- `question_family_id`
- `node_id`
- `status`
- `audience`
- `question_version`
- `rubric_version`
- `answer_key_version`
- `catalog_schema_version`
- `tags`
- `title`
- `difficulty`
- `stem`
- `prompt_markdown`
- `hints_public`
- `answer_format`
- `response_step_mode`
- trusted `expected_answer`
- `answer_aliases`
- rubric dimensions and rubric items
- `solution_outline`
- `validator_config`
- learner-safe fields
- trusted-only fields
- `source_status`
- authoring notes
- validation checklist

Public prompt rules:

- keep prompts original;
- no answer key in public prompt;
- no exact expected-answer leak;
- no rubric wording in public fields;
- hints can guide strategy but must not reveal the answer.

Trusted scoring rules:

- expected answer required for learner-visible questions;
- solution outline required;
- rubric required;
- at least one required rubric item;
- required rubric item must include `required_keywords` or `expected_patterns`;
- answer aliases should be normalized and non-duplicate;
- validator config keys must be whitelisted.

## 8. Rubric Coverage Policy

Phase 4.8 should not change scorer behavior.

P0 rubric should cover currently practical scoring dimensions:

- `trigger`
- `method`
- `transformation`
- `calculation`
- `final_answer`

Per-node nuance:

- `ode_separable`: cover all five dimensions where possible.
- `ode_homogeneous_first_order`: cover trigger/method/transformation/calculation; final answer can be included when expected answer validation is reliable.
- `ode_first_order_linear`: cover trigger/method/transformation/calculation/final_answer.
- mixed recognition: focus trigger/method/transformation; final answer may be optional if the prompt is a classification/selection task.

For `concept`, `process`, and `expression`:

- P0 should not promise full scoring support.
- They may remain unscored and appear in `unscored_dimensions`.
- Do not fake scoring by adding weak rubric items that cannot be reliably matched.
- P1 may consider carefully adding rubric-level concept/process/expression items for specific prompts.
- P2 should handle true `response_steps/self_explanation` scoring through a separate Attempt Evidence Scorer / Scoring Input Integration plan.

Answers to explicit rubric questions:

- No, every question does not need every dimension. It should cover dimensions genuinely assessed by the prompt.
- Yes, same-node difficulty variation is useful: at least basic and standard should exist for `ode_separable`; standard is enough for first P0 homogeneous/linear items.
- No, process/concept/expression scoring integration should not be rushed in Phase 4.8.

## 9. Learner-safe / Trusted Field Boundary

Learner-safe public fields:

- `question_id`
- `node_id`
- `title`
- `stem`
- `prompt_markdown`
- `answer_format`
- `response_step_mode`
- `difficulty`
- `display_assets`
- `hints_public`

Trusted-only fields:

- `expected_answer`
- `answer_aliases`
- `rubric`
- `solution_outline`
- `validator_config`
- `scoring_notes_internal`
- `golden_case_refs`
- `authoring_metadata`
- source metadata
- validation reports
- review checklists

Learner API must continue reading only published learner records from the formal catalog. Drafts, previews, reports, source metadata, and review checklists must not be visible to learner routes.

## 10. Authoring Workflow Recommendation

Compare the two routes:

### Route A: direct formal catalog YAML

Not recommended for P0 implementation.

Risks:

- pollutes formal catalog before review;
- bypasses Phase 4.3 / 4.4 authoring boundaries;
- encourages manual manifest edits;
- makes source/copyright review harder;
- increases risk of learner API accidentally seeing unfinished material.

### Route B: authoring/import workflow first

Recommended.

Process:

1. Create authoring drafts outside `backend/catalog_data`.
2. Run `validate-draft`.
3. Optionally run `validate-batch`.
4. Attach source metadata and human review checklist.
5. Run `build-candidate-dry-run` only after validation and review pass.
6. Inspect dry-run preview and validation report.
7. Decide in a later phase whether to publish a small selected subset.

Reasons:

- avoids contaminating formal catalog;
- preserves existing dry-run boundary;
- keeps learner API isolated from drafts;
- records source status before publish;
- forces human review before a publish candidate exists.

## 11. Copyright / Source Boundary

Rules:

- Do not copy textbook, PDF, lecture, or exam-prep source questions directly into the catalog.
- Candidate questions should be original, same-type practice items.
- If a source informed the design, record source metadata in authoring-only fields.
- Do not place long copyrighted passages in public prompts, trusted scoring, reports, or session logs.
- Formal catalog questions must be original or explicitly authorized by the user.
- AI-assisted drafts must still pass validation and human review.

Recommended `source_status` values for planning:

- `original`
- `user_authorized`
- `ai_assisted_original`
- `inspired_by_topic_only`

Avoid:

- `copied_from_textbook`
- `copied_from_pdf`
- `unknown_source`

## 12. Validation Requirements

CatalogValidator constraints to satisfy:

- manifest question id must match presentation question id;
- node id must exist in ODE node catalog;
- versions must be semver-like;
- public `title`, `stem`, and `prompt_markdown` must be nonblank;
- `answer_format` must be one of `expression`, `equation`, `free_text`, `expression_with_reasoning`;
- `response_step_mode` must be `none`, `optional`, or `required`;
- `difficulty` must be `basic`, `standard`, or `comprehensive`;
- learner-visible published questions must include `expected_answer`, `solution_outline`, and `rubric`;
- rubric item ids must be unique;
- required rubric items must have required keywords or patterns;
- rubric dimensions must be valid for the node or allowed extension dimensions;
- published learner questions must cover at least one node core dimension;
- `validator_config` may only use allowed keys:
  - `requires_constant`
  - `requires_initial_condition`
  - `answer_equivalence_mode`
- `validator_config` must not contain reserved keys;
- public fields must not leak exact expected answer or trusted field names;
- `content_hash`, if present, must match `sha256:<64 lowercase hex chars>`.

Authoring/import validation:

- `validate-draft` must pass before dry-run candidate build.
- `build-candidate-dry-run` requires validation passed and complete human review.
- every report/preview remains `dry_run_only=true`.
- reports stay under authoring reports root.
- previews stay under authoring previews root.
- formal catalog manifest remains unchanged.

## 13. P0 / P1 / P2 Cutline

### P0

Plan and, after explicit approval, draft 6-8 candidates through authoring/import workflow.

P0 should:

- use only existing ODE nodes;
- avoid exact equations because no node exists;
- avoid formal catalog writes at first;
- use authoring drafts and dry-run validation;
- preserve learner-safe boundary;
- avoid scoring engine changes;
- avoid API changes;
- avoid Local Trainer and coach output changes;
- avoid frontend/history/database/mastery/review;
- keep catalog expansion small enough for manual review.

### P1

After P0 dry-run review:

- select 3-5 validated candidates for possible formal publication in a later approved phase;
- improve authoring checklists;
- add concept/process/expression rubric items only where reliable and testable;
- consider one `ode_integrating_factor` or one `ode_bernoulli` candidate.

### P2

Defer:

- broad catalog expansion;
- full Mathematics I graph;
- scoring integration for response steps/self explanation;
- history browsing;
- frontend;
- database persistence;
- mastery/review scheduling;
- formal publish/export tooling.

## 14. Risk Analysis

1. Formal catalog pollution: direct YAML edits could expose unfinished questions. Mitigation: use authoring/import workflow first.
2. Authoring boundary breakage: direct manifest edits bypass validation and review. Mitigation: draft, validate, dry-run, review.
3. Too many questions: more than 10 candidates will exceed current manual review capacity. Mitigation: cap P0 at 6-8.
4. Too few questions: one question cannot support real practice. Mitigation: minimum useful target is 6.
5. `concept/process/expression` unscored dimensions: these will continue unless rubric or scorer integration improves. Mitigation: accept `unscored_dimensions` in P0 and do not pretend full support.
6. Premature scoring integration: making steps/explanation affect scores would change engine behavior. Mitigation: separate future scoring input integration plan.
7. New-node graph risk: adding unsupported nodes could break movement expectations. Mitigation: use existing nodes only.
8. Exact equation risk: no current node, so exact equations are out of P0.
9. Copyright risk: copying source problems is not allowed. Mitigation: use original same-type items and authoring source metadata.
10. Draft leakage: learner API must not read drafts. Mitigation: keep drafts outside formal catalog; rely on current repository boundary.
11. Validation weakness: current exact leak detection is lightweight, not semantic. Mitigation: human review must explicitly check source/copyright and public/trusted separation.
12. Content hash limitation: runtime only checks format. Mitigation: authoring workflow generates dry-run hashes; strong runtime enforcement remains future work.

## 15. Go / No-Go For Phase 4.8 Implementation

Go for Phase 4.8 Implementation only if the approved scope is:

- create authoring drafts, not formal catalog records;
- keep drafts outside `backend/catalog_data`;
- run dry-run validation;
- use only existing nodes;
- plan 6-8 candidates, not broad expansion;
- no engine/API/Local Trainer/coach output changes;
- no scoring integration;
- no frontend/history/database/mastery/review.

No-go if implementation request includes:

- direct formal catalog writes;
- manifest edits;
- new ODE nodes;
- exact-equation node creation;
- broad Math I expansion;
- scorer changes;
- learner API changes;
- Local Trainer feature changes;
- copyrighted source copying.

## 16. Proposed Phase 4.8 Implementation Instruction Summary

If approved, the next implementation instruction should say:

```text
Implement Phase 4.8 P0 as authoring-only minimal catalog expansion.

Create 6-8 original ODE candidate question drafts under the authoring workspace, not under backend/catalog_data.
Use existing nodes only: ode_separable, ode_homogeneous_first_order, ode_first_order_linear.
Do not edit formal catalog manifest or formal question YAML.
Do not add endpoints, engines, scoring integration, history, frontend, database, LLM, mastery, review, or catalog graph changes.
Run authoring CLI validate-draft / validate-batch and build-candidate-dry-run where review gates allow.
Produce validation reports and candidate previews only.
Keep learner API unable to see drafts.
Run pytest and evals only if implementation touches executable code or catalog-adjacent validation fixtures.
```

Recommended next step after this plan:

```text
Phase 4.8 Implementation: Authoring-only Minimal Catalog Expansion Drafts
```

Do not enter implementation until explicitly confirmed.
