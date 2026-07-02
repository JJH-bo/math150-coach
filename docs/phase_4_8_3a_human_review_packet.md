# Phase 4.8.3A Human Review Packet Export

Status: packet exported. No review, scoring, ranking, candidate selection, formal publish, catalog write, code change, or scoring integration is performed in this phase.

> This review packet contains trusted-only authoring material. It must not be exposed through learner API, Local Trainer public question output, public prompts, or learner-facing docs.

This packet is for internal human review only. It is not a learner-facing artifact. It does not publish, select, rank, score, or register any candidate.

Review fields are intentionally left blank for Phase 4.8.3B. No candidate selection was performed. No candidate scoring was performed.

## 1. Executive Decision

Phase 4.8.3A exports a human review packet for the 8 Phase 4.8 authoring-only ODE candidate drafts.

The packet gives a future reviewer the materials needed to inspect each candidate:

- public learner-facing fields;
- trusted expected answer fields;
- rubric fields;
- validator config;
- source metadata;
- validation report location and dry-run preview information;
- blank review template from the Phase 4.8.2 plan.

This phase does not evaluate the candidates.

## 2. Scope And Non-goals

In scope:

- read Phase 4.8 planning, implementation, freeze, and review-plan documents;
- read authoring-only draft YAML files;
- read authoring-only dry-run preview JSON files;
- read authoring-only validation reports;
- export a markdown review packet;
- update README stage status and next phase label.

Out of scope:

- modifying draft YAML;
- modifying previews;
- modifying validation reports;
- modifying the batch manifest;
- modifying the formal catalog;
- adding formal question YAML;
- formal import or formal publish;
- candidate scoring, ranking, recommendation, or selection;
- engine, API, learner projector, Local Trainer, coach output, CatalogValidator, or authoring CLI changes;
- endpoint, history, frontend, database, auth, LLM, mastery, review, formal persistence, or scoring integration.

## 3. Candidate List

| Question ID | Draft ID | Node ID | Packet status |
| --- | --- | --- | --- |
| `ode-sep-cand-001` | `draft-ode-sep-cand-001` | `ode_separable` | included |
| `ode-sep-cand-002` | `draft-ode-sep-cand-002` | `ode_separable` | included |
| `ode-sep-cand-003` | `draft-ode-sep-cand-003` | `ode_separable` | included |
| `ode-hom-cand-001` | `draft-ode-hom-cand-001` | `ode_homogeneous_first_order` | included |
| `ode-hom-cand-002` | `draft-ode-hom-cand-002` | `ode_homogeneous_first_order` | included |
| `ode-linear-cand-001` | `draft-ode-linear-cand-001` | `ode_first_order_linear` | included |
| `ode-linear-cand-002` | `draft-ode-linear-cand-002` | `ode_first_order_linear` | included |
| `ode-mixed-cand-001` | `draft-ode-mixed-cand-001` | `ode_first_order_linear` | included |

## 4. Source Files Used

- `docs/phase_4_8_2_human_review_selection_plan.md`
- `docs/phase_4_8_implementation_report.md`
- `docs/phase_4_8_1_freeze_report.md`
- `backend/catalog_authoring/phase_4_8/import_manifest.yaml`
- `backend/catalog_authoring/phase_4_8/drafts/*.yaml`
- `backend/catalog_authoring/phase_4_8/previews/phase_4_8/*.preview.json`
- `backend/catalog_authoring/phase_4_8/reports/phase_4_8/*.json`
- `README.md`

## 5. Review Rubric Reference

The review rubric is defined in `docs/phase_4_8_2_human_review_selection_plan.md`.

Review dimensions:

1. Mathematical correctness.
2. Trigger clarity.
3. Training value.
4. Difficulty fit.
5. Node match.
6. Rubric reliability.
7. Validator reliability.
8. Learner-safe boundary.
9. Source/copyright status.
10. Publish risk.

Weighted dimensions from the Phase 4.8.2 plan:

| Dimension | Weight |
| --- | ---: |
| Mathematical correctness | 20 |
| Trigger clarity | 15 |
| Training value | 15 |
| Rubric reliability | 15 |
| Validator reliability | 10 |
| Node match | 10 |
| Difficulty fit | 5 |
| Learner-safe boundary | 5 |
| Source/copyright safety | 5 |

The packet below does not fill any score field.

## 6. Per-candidate Review Packet

## Candidate Packet: `ode-sep-cand-001`

- Candidate ID: `draft-ode-sep-cand-001`
- Question ID: `ode-sep-cand-001`
- Node ID: `ode_separable`
- Difficulty: `basic`
- Response step mode: `optional`
- Answer format: `expression_with_reasoning`
- Tags: `ode`, `separable`, `general-solution`, `phase-4-8`
- Source status: `ai_assisted_original`
- Draft file path: `backend/catalog_authoring/phase_4_8/drafts/ode-sep-cand-001.yaml`
- Preview file path: `backend/catalog_authoring/phase_4_8/previews/phase_4_8/ode-sep-cand-001.preview.json`
- Validation report path: `backend/catalog_authoring/phase_4_8/reports/phase_4_8/ode-sep-cand-001.validate.json`
- Content hash from dry-run preview: `sha256:a3ed215102371252c8a9ee5f1a507c8a24cf42f06b6d9479b6fb46a3d24e32ec`

### A. Public learner-facing fields

- title: Direct separable equation
- stem: Solve a direct separable first-order differential equation.
- prompt_markdown: Solve dy/dx = 3xy. State the method trigger, separate variables, integrate, and give the general solution.
- hints_public:
  - Check whether all y terms can be moved to one side and all x terms to the other side.
- difficulty: `basic`
- answer_format: `expression_with_reasoning`
- response_step_mode: `optional`

### B. Trusted answer fields

- expected_answer: `ln|y|=3x^2/2+C`
- answer_aliases:
  - `y=Ce^(3x^2/2)`
  - `ln|y| = 3x^2/2 + C`
- solution_outline: Separate dy/y = 3x dx and integrate to ln|y| = 3x^2/2 + C.

### C. Rubric fields

- rubric dimensions covered: `trigger`, `method`, `transformation`, `calculation`, `final_answer`
- rubric version: `1.0`
- required rubric items:
  - `trigger_separable` -> dimensions `trigger`; weight `1.0`; keywords `separable`; patterns `None`
  - `method_separate_variables` -> dimensions `method`; weight `1.0`; keywords `separate variables`; patterns `None`
  - `transform_separated_form` -> dimensions `transformation`; weight `1.0`; keywords `dy/y`, `3x`; patterns `None`
  - `calculation_integrate` -> dimensions `calculation`; weight `1.0`; keywords `integrate`; patterns `None`
  - `final_answer_general_solution` -> dimensions `final_answer`; weight `1.0`; keywords `ln|y|`, `3x^2/2`, `C`; patterns `None`
- optional rubric items:
  - None recorded in draft

### D. Validator fields

- validator_config:
  - `requires_constant`: `True`
  - `answer_equivalence_mode`: `normalized`
- answer_equivalence_mode: `normalized`
- requires_constant: `True`
- requires_initial_condition: `not set`

### E. Authoring/source metadata

- source_type: `generated_variant`
- source_name: `Math150 Coach Phase 4.8 original ODE batch`
- source_status: `ai_assisted_original`
- copyright note: Authoring-only original candidate.
- authoring notes: Original same-type practice item for separable equations.

### F. Dry-run / validation status

- validate-draft result: `validation_report.passed=True`; issues count `0`
- validate-batch result: status `validation_passed`; human_review_status `ready`
- dry_run_only status: `True`
- content_hash boundary note: content hash is present only in the dry-run preview and does not register or publish the candidate.

### G. Blank review template

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

## Candidate Packet: `ode-sep-cand-002`

- Candidate ID: `draft-ode-sep-cand-002`
- Question ID: `ode-sep-cand-002`
- Node ID: `ode_separable`
- Difficulty: `standard`
- Response step mode: `optional`
- Answer format: `expression_with_reasoning`
- Tags: `ode`, `separable`, `rearrangement`, `general-solution`, `phase-4-8`
- Source status: `ai_assisted_original`
- Draft file path: `backend/catalog_authoring/phase_4_8/drafts/ode-sep-cand-002.yaml`
- Preview file path: `backend/catalog_authoring/phase_4_8/previews/phase_4_8/ode-sep-cand-002.preview.json`
- Validation report path: `backend/catalog_authoring/phase_4_8/reports/phase_4_8/ode-sep-cand-002.validate.json`
- Content hash from dry-run preview: `sha256:d965f39f55f93703217fe25c4f0072276b9d0c05d92e7e745db109ae4a864e00`

### A. Public learner-facing fields

- title: Rearrange before separating variables
- stem: Solve a separable equation that first needs simple rearrangement.
- prompt_markdown: Solve (1+x^2) dy/dx = 2xy. Explain why it becomes separable after rearrangement, then give the general solution.
- hints_public:
  - First divide by the coefficient of dy/dx before separating variables.
- difficulty: `standard`
- answer_format: `expression_with_reasoning`
- response_step_mode: `optional`

### B. Trusted answer fields

- expected_answer: `ln|y|=ln(1+x^2)+C`
- answer_aliases:
  - `y=C(1+x^2)`
  - `ln|y| = ln(1+x^2) + C`
- solution_outline: Divide by 1+x^2 and y to get dy/y = 2x/(1+x^2) dx, then integrate to ln|y| = ln(1+x^2) + C.

### C. Rubric fields

- rubric dimensions covered: `trigger`, `method`, `transformation`, `calculation`, `final_answer`
- rubric version: `1.0`
- required rubric items:
  - `trigger_after_rearrangement` -> dimensions `trigger`; weight `1.0`; keywords `separable`; patterns `None`
  - `method_separate_variables` -> dimensions `method`; weight `1.0`; keywords `separate variables`; patterns `None`
  - `transform_rearranged_form` -> dimensions `transformation`; weight `1.0`; keywords `dy/y`, `2x/(1+x^2)`; patterns `None`
  - `calculation_log_integral` -> dimensions `calculation`; weight `1.0`; keywords `integrate`, `ln(1+x^2)`; patterns `None`
  - `final_answer_general_solution` -> dimensions `final_answer`; weight `1.0`; keywords `ln|y|`, `ln(1+x^2)`, `C`; patterns `None`
- optional rubric items:
  - None recorded in draft

### D. Validator fields

- validator_config:
  - `requires_constant`: `True`
  - `answer_equivalence_mode`: `normalized`
- answer_equivalence_mode: `normalized`
- requires_constant: `True`
- requires_initial_condition: `not set`

### E. Authoring/source metadata

- source_type: `generated_variant`
- source_name: `Math150 Coach Phase 4.8 original ODE batch`
- source_status: `ai_assisted_original`
- copyright note: Authoring-only original candidate.
- authoring notes: Original rearrangement-before-separation item.

### F. Dry-run / validation status

- validate-draft result: `validation_report.passed=True`; issues count `0`
- validate-batch result: status `validation_passed`; human_review_status `ready`
- dry_run_only status: `True`
- content_hash boundary note: content hash is present only in the dry-run preview and does not register or publish the candidate.

### G. Blank review template

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

## Candidate Packet: `ode-sep-cand-003`

- Candidate ID: `draft-ode-sep-cand-003`
- Question ID: `ode-sep-cand-003`
- Node ID: `ode_separable`
- Difficulty: `standard`
- Response step mode: `required`
- Answer format: `expression_with_reasoning`
- Tags: `ode`, `separable`, `initial-condition`, `phase-4-8`
- Source status: `ai_assisted_original`
- Draft file path: `backend/catalog_authoring/phase_4_8/drafts/ode-sep-cand-003.yaml`
- Preview file path: `backend/catalog_authoring/phase_4_8/previews/phase_4_8/ode-sep-cand-003.preview.json`
- Validation report path: `backend/catalog_authoring/phase_4_8/reports/phase_4_8/ode-sep-cand-003.validate.json`
- Content hash from dry-run preview: `sha256:def46ae6c01084eb7928c0c0a4cec2ff839b11c1311ebb5fd496ba57bd8c88a7`

### A. Public learner-facing fields

- title: Separable equation with initial condition
- stem: Solve a separable equation and use the initial condition.
- prompt_markdown: Solve dy/dx = 2xy with y(0)=3. State the separation step and give the particular solution.
- hints_public:
  - Find the general solution first, then use the given value to determine the constant.
- difficulty: `standard`
- answer_format: `expression_with_reasoning`
- response_step_mode: `required`

### B. Trusted answer fields

- expected_answer: `y=3e^(x^2)`
- answer_aliases:
  - `y = 3e^(x^2)`
  - `y=3 exp(x^2)`
- solution_outline: Separate dy/y = 2x dx, integrate to y = C e^(x^2), then use y(0)=3 to get C=3.

### C. Rubric fields

- rubric dimensions covered: `trigger`, `method`, `transformation`, `calculation`, `final_answer`
- rubric version: `1.0`
- required rubric items:
  - `trigger_separable` -> dimensions `trigger`; weight `1.0`; keywords `separable`; patterns `None`
  - `method_separate_variables` -> dimensions `method`; weight `1.0`; keywords `separate variables`; patterns `None`
  - `transform_separated_form` -> dimensions `transformation`; weight `1.0`; keywords `dy/y`, `2x`; patterns `None`
  - `calculation_integrate_and_resolve_constant` -> dimensions `calculation`; weight `1.0`; keywords `integrate`, `C=3`; patterns `None`
  - `final_answer_particular_solution` -> dimensions `final_answer`; weight `1.0`; keywords `3e^(x^2)`; patterns `None`
- optional rubric items:
  - None recorded in draft

### D. Validator fields

- validator_config:
  - `requires_initial_condition`: `True`
  - `answer_equivalence_mode`: `normalized`
- answer_equivalence_mode: `normalized`
- requires_constant: `not set`
- requires_initial_condition: `True`

### E. Authoring/source metadata

- source_type: `generated_variant`
- source_name: `Math150 Coach Phase 4.8 original ODE batch`
- source_status: `ai_assisted_original`
- copyright note: Authoring-only original candidate.
- authoring notes: Original separable IVP candidate.

### F. Dry-run / validation status

- validate-draft result: `validation_report.passed=True`; issues count `0`
- validate-batch result: status `validation_passed`; human_review_status `ready`
- dry_run_only status: `True`
- content_hash boundary note: content hash is present only in the dry-run preview and does not register or publish the candidate.

### G. Blank review template

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

## Candidate Packet: `ode-hom-cand-001`

- Candidate ID: `draft-ode-hom-cand-001`
- Question ID: `ode-hom-cand-001`
- Node ID: `ode_homogeneous_first_order`
- Difficulty: `standard`
- Response step mode: `optional`
- Answer format: `expression_with_reasoning`
- Tags: `ode`, `homogeneous-first-order`, `y-vx`, `phase-4-8`
- Source status: `ai_assisted_original`
- Draft file path: `backend/catalog_authoring/phase_4_8/drafts/ode-hom-cand-001.yaml`
- Preview file path: `backend/catalog_authoring/phase_4_8/previews/phase_4_8/ode-hom-cand-001.preview.json`
- Validation report path: `backend/catalog_authoring/phase_4_8/reports/phase_4_8/ode-hom-cand-001.validate.json`
- Content hash from dry-run preview: `sha256:5c6dbe85b7882ea3b5dbee579f2c852cade324eba1f1c5c25d5122da06a36c5d`

### A. Public learner-facing fields

- title: Homogeneous equation with y over x
- stem: Solve a first-order homogeneous equation using substitution.
- prompt_markdown: Solve dy/dx = 1 + y/x. Explain the homogeneous trigger and use a y=vx substitution.
- hints_public:
  - Look for a right side that depends on the ratio y/x.
- difficulty: `standard`
- answer_format: `expression_with_reasoning`
- response_step_mode: `optional`

### B. Trusted answer fields

- expected_answer: `y=x(ln|x|+C)`
- answer_aliases:
  - `y = x(ln|x| + C)`
  - `y/x=ln|x|+C`
- solution_outline: Let y=vx, so y'=v+xv'. Then v+xv'=1+v, so dv/dx=1/x and v=ln|x|+C. Hence y=x(ln|x|+C).

### C. Rubric fields

- rubric dimensions covered: `trigger`, `method`, `transformation`, `calculation`, `final_answer`
- rubric version: `1.0`
- required rubric items:
  - `trigger_ratio_structure` -> dimensions `trigger`; weight `1.0`; keywords `y/x`; patterns `None`
  - `method_y_equals_vx` -> dimensions `method`; weight `1.0`; keywords `y=vx`; patterns `None`
  - `transformation_derivative` -> dimensions `transformation`; weight `1.0`; keywords `v+xv'`; patterns `None`
  - `calculation_integrate_ratio` -> dimensions `calculation`; weight `1.0`; keywords `ln|x|`; patterns `None`
  - `final_answer_restore_y` -> dimensions `final_answer`; weight `1.0`; keywords `x`, `ln|x|`, `C`; patterns `None`
- optional rubric items:
  - None recorded in draft

### D. Validator fields

- validator_config:
  - `requires_constant`: `True`
  - `answer_equivalence_mode`: `normalized`
- answer_equivalence_mode: `normalized`
- requires_constant: `True`
- requires_initial_condition: `not set`

### E. Authoring/source metadata

- source_type: `generated_variant`
- source_name: `Math150 Coach Phase 4.8 original ODE batch`
- source_status: `ai_assisted_original`
- copyright note: Authoring-only original candidate.
- authoring notes: Original homogeneous y/x substitution item.

### F. Dry-run / validation status

- validate-draft result: `validation_report.passed=True`; issues count `0`
- validate-batch result: status `validation_passed`; human_review_status `ready`
- dry_run_only status: `True`
- content_hash boundary note: content hash is present only in the dry-run preview and does not register or publish the candidate.

### G. Blank review template

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

## Candidate Packet: `ode-hom-cand-002`

- Candidate ID: `draft-ode-hom-cand-002`
- Question ID: `ode-hom-cand-002`
- Node ID: `ode_homogeneous_first_order`
- Difficulty: `standard`
- Response step mode: `required`
- Answer format: `expression_with_reasoning`
- Tags: `ode`, `homogeneous-first-order`, `recognition`, `phase-4-8`
- Source status: `ai_assisted_original`
- Draft file path: `backend/catalog_authoring/phase_4_8/drafts/ode-hom-cand-002.yaml`
- Preview file path: `backend/catalog_authoring/phase_4_8/previews/phase_4_8/ode-hom-cand-002.preview.json`
- Validation report path: `backend/catalog_authoring/phase_4_8/reports/phase_4_8/ode-hom-cand-002.validate.json`
- Content hash from dry-run preview: `sha256:c656030f14ba09e8d24fc6affaa3043273841add2415844890d61b0b5bb1e11c`

### A. Public learner-facing fields

- title: Identify homogeneity before substitution
- stem: Identify a homogeneous first-order equation and solve it.
- prompt_markdown: Solve dy/dx = (x^2+y^2)/(xy). First explain why the equation is homogeneous, then use a ratio substitution.
- hints_public:
  - Rewrite the right side in terms of y/x or x/y before choosing the substitution.
- difficulty: `standard`
- answer_format: `expression_with_reasoning`
- response_step_mode: `required`

### B. Trusted answer fields

- expected_answer: `(y/x)^2=2ln|x|+C`
- answer_aliases:
  - `y^2=x^2(2ln|x|+C)`
  - `(y/x)^2 = 2ln|x| + C`
- solution_outline: Rewrite as dy/dx = x/y + y/x. Let y=vx, so v+xv' = 1/v + v. Then v dv = dx/x, giving (y/x)^2 = 2ln|x| + C.

### C. Rubric fields

- rubric dimensions covered: `trigger`, `method`, `transformation`, `calculation`, `final_answer`
- rubric version: `1.0`
- required rubric items:
  - `trigger_homogeneous_structure` -> dimensions `trigger`; weight `1.0`; keywords `homogeneous`; patterns `None`
  - `method_ratio_substitution` -> dimensions `method`; weight `1.0`; keywords `y=vx`; patterns `None`
  - `transformation_reduced_equation` -> dimensions `transformation`; weight `1.0`; keywords `v dv`, `dx/x`; patterns `None`
  - `calculation_integrate_reduced_form` -> dimensions `calculation`; weight `1.0`; keywords `2ln|x|`; patterns `None`
  - `final_answer_ratio_form` -> dimensions `final_answer`; weight `1.0`; keywords `(y/x)^2`, `2ln|x|`, `C`; patterns `None`
- optional rubric items:
  - None recorded in draft

### D. Validator fields

- validator_config:
  - `requires_constant`: `True`
  - `answer_equivalence_mode`: `normalized`
- answer_equivalence_mode: `normalized`
- requires_constant: `True`
- requires_initial_condition: `not set`

### E. Authoring/source metadata

- source_type: `generated_variant`
- source_name: `Math150 Coach Phase 4.8 original ODE batch`
- source_status: `ai_assisted_original`
- copyright note: Authoring-only original candidate.
- authoring notes: Original homogeneous recognition item.

### F. Dry-run / validation status

- validate-draft result: `validation_report.passed=True`; issues count `0`
- validate-batch result: status `validation_passed`; human_review_status `ready`
- dry_run_only status: `True`
- content_hash boundary note: content hash is present only in the dry-run preview and does not register or publish the candidate.

### G. Blank review template

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

## Candidate Packet: `ode-linear-cand-001`

- Candidate ID: `draft-ode-linear-cand-001`
- Question ID: `ode-linear-cand-001`
- Node ID: `ode_first_order_linear`
- Difficulty: `standard`
- Response step mode: `optional`
- Answer format: `expression_with_reasoning`
- Tags: `ode`, `first-order-linear`, `integrating-factor`, `phase-4-8`
- Source status: `ai_assisted_original`
- Draft file path: `backend/catalog_authoring/phase_4_8/drafts/ode-linear-cand-001.yaml`
- Preview file path: `backend/catalog_authoring/phase_4_8/previews/phase_4_8/ode-linear-cand-001.preview.json`
- Validation report path: `backend/catalog_authoring/phase_4_8/reports/phase_4_8/ode-linear-cand-001.validate.json`
- Content hash from dry-run preview: `sha256:ff0bbde30656ab6443978677478a3ea4d5879c019757dcb9a8425c4796a56f6a`

### A. Public learner-facing fields

- title: First-order linear equation in standard form
- stem: Solve a first-order linear differential equation already in standard form.
- prompt_markdown: Solve y' + 2y = e^x. State the first-order linear trigger and use an integrating factor.
- hints_public:
  - Identify P(x) in the standard form before choosing the integrating factor.
- difficulty: `standard`
- answer_format: `expression_with_reasoning`
- response_step_mode: `optional`

### B. Trusted answer fields

- expected_answer: `y=e^x/3+Ce^(-2x)`
- answer_aliases:
  - `y = e^x/3 + C e^(-2x)`
  - `y=Ce^(-2x)+e^x/3`
- solution_outline: Use integrating factor e^(2x), so (e^(2x)y)' = e^(3x). Integrate to e^(2x)y = e^(3x)/3 + C, hence y=e^x/3+Ce^(-2x).

### C. Rubric fields

- rubric dimensions covered: `trigger`, `method`, `transformation`, `calculation`, `final_answer`
- rubric version: `1.0`
- required rubric items:
  - `trigger_first_order_linear` -> dimensions `trigger`; weight `1.0`; keywords `linear`; patterns `None`
  - `method_integrating_factor` -> dimensions `method`; weight `1.0`; keywords `integrating factor`; patterns `None`
  - `transformation_factor` -> dimensions `transformation`; weight `1.0`; keywords `e^(2x)`; patterns `None`
  - `calculation_integrate_product` -> dimensions `calculation`; weight `1.0`; keywords `e^(3x)`, `1/3`; patterns `None`
  - `final_answer_linear_general` -> dimensions `final_answer`; weight `1.0`; keywords `e^x/3`, `Ce^(-2x)`; patterns `None`
- optional rubric items:
  - None recorded in draft

### D. Validator fields

- validator_config:
  - `requires_constant`: `True`
  - `answer_equivalence_mode`: `normalized`
- answer_equivalence_mode: `normalized`
- requires_constant: `True`
- requires_initial_condition: `not set`

### E. Authoring/source metadata

- source_type: `generated_variant`
- source_name: `Math150 Coach Phase 4.8 original ODE batch`
- source_status: `ai_assisted_original`
- copyright note: Authoring-only original candidate.
- authoring notes: Original first-order linear standard-form candidate.

### F. Dry-run / validation status

- validate-draft result: `validation_report.passed=True`; issues count `0`
- validate-batch result: status `validation_passed`; human_review_status `ready`
- dry_run_only status: `True`
- content_hash boundary note: content hash is present only in the dry-run preview and does not register or publish the candidate.

### G. Blank review template

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

## Candidate Packet: `ode-linear-cand-002`

- Candidate ID: `draft-ode-linear-cand-002`
- Question ID: `ode-linear-cand-002`
- Node ID: `ode_first_order_linear`
- Difficulty: `standard`
- Response step mode: `required`
- Answer format: `expression_with_reasoning`
- Tags: `ode`, `first-order-linear`, `standard-form`, `phase-4-8`
- Source status: `ai_assisted_original`
- Draft file path: `backend/catalog_authoring/phase_4_8/drafts/ode-linear-cand-002.yaml`
- Preview file path: `backend/catalog_authoring/phase_4_8/previews/phase_4_8/ode-linear-cand-002.preview.json`
- Validation report path: `backend/catalog_authoring/phase_4_8/reports/phase_4_8/ode-linear-cand-002.validate.json`
- Content hash from dry-run preview: `sha256:29489ec9f7e68f8feb68987dbb539d67d7ad72c8e2e752f0307189b8ff442619`

### A. Public learner-facing fields

- title: Rearrange into first-order linear standard form
- stem: Rearrange a first-order equation into standard linear form and solve it.
- prompt_markdown: Solve 2y' + 4y = 6x. First rewrite it in first-order linear standard form, then use an integrating factor.
- hints_public:
  - Divide the equation first so the coefficient of y' is one.
- difficulty: `standard`
- answer_format: `expression_with_reasoning`
- response_step_mode: `required`

### B. Trusted answer fields

- expected_answer: `y=3x/2-3/4+Ce^(-2x)`
- answer_aliases:
  - `y = 3x/2 - 3/4 + C e^(-2x)`
  - `y=Ce^(-2x)+3x/2-3/4`
- solution_outline: Divide by 2 to get y'+2y=3x. Use integrating factor e^(2x), or solve the linear equation to get y=3x/2-3/4+Ce^(-2x).

### C. Rubric fields

- rubric dimensions covered: `trigger`, `method`, `transformation`, `calculation`, `final_answer`
- rubric version: `1.0`
- required rubric items:
  - `trigger_linear_after_rewrite` -> dimensions `trigger`; weight `1.0`; keywords `linear`; patterns `None`
  - `method_integrating_factor` -> dimensions `method`; weight `1.0`; keywords `integrating factor`; patterns `None`
  - `transformation_standard_form` -> dimensions `transformation`; weight `1.0`; keywords `y'+2y=3x`; patterns `None`
  - `calculation_linear_solution` -> dimensions `calculation`; weight `1.0`; keywords `3x/2`, `-3/4`; patterns `None`
  - `final_answer_linear_general` -> dimensions `final_answer`; weight `1.0`; keywords `3x/2`, `-3/4`, `Ce^(-2x)`; patterns `None`
- optional rubric items:
  - None recorded in draft

### D. Validator fields

- validator_config:
  - `requires_constant`: `True`
  - `answer_equivalence_mode`: `normalized`
- answer_equivalence_mode: `normalized`
- requires_constant: `True`
- requires_initial_condition: `not set`

### E. Authoring/source metadata

- source_type: `generated_variant`
- source_name: `Math150 Coach Phase 4.8 original ODE batch`
- source_status: `ai_assisted_original`
- copyright note: Authoring-only original candidate.
- authoring notes: Original linear-standard-form rearrangement candidate.

### F. Dry-run / validation status

- validate-draft result: `validation_report.passed=True`; issues count `0`
- validate-batch result: status `validation_passed`; human_review_status `ready`
- dry_run_only status: `True`
- content_hash boundary note: content hash is present only in the dry-run preview and does not register or publish the candidate.

### G. Blank review template

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

## Candidate Packet: `ode-mixed-cand-001`

- Candidate ID: `draft-ode-mixed-cand-001`
- Question ID: `ode-mixed-cand-001`
- Node ID: `ode_first_order_linear`
- Difficulty: `standard`
- Response step mode: `required`
- Answer format: `expression_with_reasoning`
- Tags: `ode`, `recognition`, `first-order-linear`, `phase-4-8`
- Source status: `ai_assisted_original`
- Draft file path: `backend/catalog_authoring/phase_4_8/drafts/ode-mixed-cand-001.yaml`
- Preview file path: `backend/catalog_authoring/phase_4_8/previews/phase_4_8/ode-mixed-cand-001.preview.json`
- Validation report path: `backend/catalog_authoring/phase_4_8/reports/phase_4_8/ode-mixed-cand-001.validate.json`
- Content hash from dry-run preview: `sha256:e42be0f4aa76372903d4bc361efc090ed2266c7c7005c8f1c44b643dae0e048c`

### A. Public learner-facing fields

- title: Decide method before solving
- stem: Decide whether the equation should be handled as separable or first-order linear.
- prompt_markdown: Solve y' + (1/x)y = x for x>0. First decide why first-order linear form is the reliable method here, then solve.
- hints_public:
  - Compare the equation with the standard form y' + P(x)y = Q(x).
- difficulty: `standard`
- answer_format: `expression_with_reasoning`
- response_step_mode: `required`

### B. Trusted answer fields

- expected_answer: `y=x^2/3+C/x`
- answer_aliases:
  - `y = x^2/3 + C/x`
  - `xy=x^3/3+C`
- solution_outline: The equation is y' + (1/x)y = x, with integrating factor x on x>0. Then (xy)' = x^2, so xy = x^3/3 + C and y = x^2/3 + C/x.

### C. Rubric fields

- rubric dimensions covered: `trigger`, `method`, `transformation`, `calculation`, `final_answer`
- rubric version: `1.0`
- required rubric items:
  - `trigger_linear_not_separable_first` -> dimensions `trigger`; weight `1.0`; keywords `linear`; patterns `None`
  - `method_integrating_factor` -> dimensions `method`; weight `1.0`; keywords `integrating factor`; patterns `None`
  - `transformation_integrating_factor_x` -> dimensions `transformation`; weight `1.0`; keywords `integrating factor`, `x`; patterns `None`
  - `calculation_integrate_x_squared` -> dimensions `calculation`; weight `1.0`; keywords `x^3/3`; patterns `None`
  - `final_answer_linear_solution` -> dimensions `final_answer`; weight `1.0`; keywords `x^2/3`, `C/x`; patterns `None`
- optional rubric items:
  - None recorded in draft

### D. Validator fields

- validator_config:
  - `requires_constant`: `True`
  - `answer_equivalence_mode`: `normalized`
- answer_equivalence_mode: `normalized`
- requires_constant: `True`
- requires_initial_condition: `not set`

### E. Authoring/source metadata

- source_type: `generated_variant`
- source_name: `Math150 Coach Phase 4.8 original ODE batch`
- source_status: `ai_assisted_original`
- copyright note: Authoring-only original candidate.
- authoring notes: Original mixed-recognition item bound to existing first-order linear node.

### F. Dry-run / validation status

- validate-draft result: `validation_report.passed=True`; issues count `0`
- validate-batch result: status `validation_passed`; human_review_status `ready`
- dry_run_only status: `True`
- content_hash boundary note: content hash is present only in the dry-run preview and does not register or publish the candidate.

### G. Blank review template

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

## 7. Trusted-material Boundary Warning

This document includes trusted-only expected answers, aliases, solution outlines, rubric items, validator config, source metadata, dry-run preview paths, validation report paths, and content hashes.

It must not be exposed through:

- learner API;
- Local Trainer public question output;
- public prompts;
- learner-facing docs;
- frontend or public training views.

The packet is for internal human review only. It does not publish or register any candidate.

## 8. Formal Catalog Boundary Check

Phase 4.8.1 already recorded the formal catalog boundary. Phase 4.8.3A did not modify code or catalog data, so the boundary remains unchanged.

Recorded baseline:

- formal catalog manifest unchanged;
- no candidate appears in formal catalog manifest;
- no formal question YAML was added;
- dry-run preview status does not imply publish;
- content hash does not imply publish.

Formal manifest still lists only the existing formal catalog files from the Phase 4.8.1 baseline.

## 9. Learner API Boundary Check

Phase 4.8.1 already recorded learner API isolation:

- Local Trainer list returned only `ode-sep-001`;
- candidate direct lookup returned 404 for representative candidate IDs;
- reports and previews are not learner-visible.

Phase 4.8.3A did not modify code, catalog, API routes, Local Trainer, previews, reports, or formal manifest, so the learner API boundary remains unchanged from that baseline.

## 10. Next Step

Next authorized phase label:

```text
Phase 4.8.3B Actual Human Review Of Authoring Candidates
```

Phase 4.8.3B should fill the blank review templates using the Phase 4.8.2 review rubric. It should still avoid formal publish unless a later phase explicitly approves publish planning and catalog writes.
