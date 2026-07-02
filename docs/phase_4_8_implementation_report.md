# Phase 4.8 Implementation Report: Authoring-only Minimal Catalog Expansion Drafts

## Scope

Phase 4.8 created an authoring-only minimal catalog expansion batch for existing ODE nodes. It did not publish to the formal catalog and did not change learner-facing API behavior.

Allowed scope used:

- Authoring draft YAML files under `backend/catalog_authoring/phase_4_8/drafts/`
- Authoring batch manifest under `backend/catalog_authoring/phase_4_8/import_manifest.yaml`
- Validation reports under `backend/catalog_authoring/phase_4_8/reports/`
- Dry-run previews under `backend/catalog_authoring/phase_4_8/previews/`
- This implementation report

Explicitly unchanged:

- `backend/catalog_data/manifest.yaml`
- `backend/catalog_data/questions/*.yaml`
- ODE node graph YAML
- scoring, diagnosis, rollback, forward, API, learner projector, Local Trainer, coach output, golden evals, APP_PROFILE gating, CatalogValidator, and authoring CLI code

## Created Drafts

Eight authoring-only draft candidates were added.

| Draft ID | Question ID | Node | Type |
| --- | --- | --- | --- |
| `draft-ode-sep-cand-001` | `ode-sep-cand-001` | `ode_separable` | direct separable general solution |
| `draft-ode-sep-cand-002` | `ode-sep-cand-002` | `ode_separable` | rearrange then separate |
| `draft-ode-sep-cand-003` | `ode-sep-cand-003` | `ode_separable` | separable initial-value problem |
| `draft-ode-hom-cand-001` | `ode-hom-cand-001` | `ode_homogeneous_first_order` | ratio trigger with `y=vx` |
| `draft-ode-hom-cand-002` | `ode-hom-cand-002` | `ode_homogeneous_first_order` | ratio substitution and implicit solution |
| `draft-ode-linear-cand-001` | `ode-linear-cand-001` | `ode_first_order_linear` | standard-form first-order linear |
| `draft-ode-linear-cand-002` | `ode-linear-cand-002` | `ode_first_order_linear` | rewrite into standard linear form |
| `draft-ode-mixed-cand-001` | `ode-mixed-cand-001` | `ode_first_order_linear` | mixed recognition, linear over forced separation |

## Candidate Question Matrix

| Question ID | Public prompt summary | Trusted scoring coverage |
| --- | --- | --- |
| `ode-sep-cand-001` | Solve `dy/dx = 3xy` and explain the separable trigger. | trigger, method, transformation, calculation, final_answer |
| `ode-sep-cand-002` | Solve `(1+x^2) dy/dx = 2xy` after rearrangement. | trigger, method, transformation, calculation, final_answer |
| `ode-sep-cand-003` | Solve `dy/dx = 2xy`, `y(0)=3`, and give the particular solution. | trigger, method, transformation, calculation, final_answer |
| `ode-hom-cand-001` | Solve `dy/dx = 1 + y/x` with `y=vx`. | trigger, method, transformation, calculation, final_answer |
| `ode-hom-cand-002` | Solve `dy/dx = (x^2+y^2)/(xy)` with a ratio substitution. | trigger, method, transformation, calculation, final_answer |
| `ode-linear-cand-001` | Solve `y' + 2y = e^x` by integrating factor. | trigger, method, transformation, calculation, final_answer |
| `ode-linear-cand-002` | Solve `2y' + 4y = 6x` after rewriting standard form. | trigger, method, transformation, calculation, final_answer |
| `ode-mixed-cand-001` | Solve `y' + (1/x)y = x`, `x>0`, after choosing a reliable method. | trigger, method, transformation, calculation, final_answer |

## Node Coverage

- `ode_separable`: 3 drafts
- `ode_homogeneous_first_order`: 2 drafts
- `ode_first_order_linear`: 3 drafts

No new nodes were added. No Bernoulli, second-order, Euler, or application-modeling drafts were added in this P0 batch.

## Source And Copyright Status

All drafts are marked as generated variants with original authoring metadata:

- `source_type: generated_variant`
- `source_name: Math150 Coach Phase 4.8 original ODE batch`
- `source_status: ai_assisted_original`
- copyright note states that the candidates are authoring-only originals

No external textbook, PDF, lecture, past-exam, or copyrighted source problem was copied.

## Validation Results

Individual `validate-draft` results:

- 8/8 passed
- 0 issues
- Reports written under `backend/catalog_authoring/phase_4_8/reports/phase_4_8/`

Batch `validate-batch` result:

- Total: 8
- Passed: 8
- Failed: 0
- `human_review_status: ready` for each draft
- Report written to `backend/catalog_authoring/phase_4_8/reports/phase_4_8/batch_validate.json`

## Dry-run Preview Results

`build-candidate-dry-run` succeeded for all 8 candidates. Each preview is dry-run only and written under `backend/catalog_authoring/phase_4_8/previews/phase_4_8/`.

| Question ID | Content hash |
| --- | --- |
| `ode-sep-cand-001` | `sha256:a3ed215102371252c8a9ee5f1a507c8a24cf42f06b6d9479b6fb46a3d24e32ec` |
| `ode-sep-cand-002` | `sha256:d965f39f55f93703217fe25c4f0072276b9d0c05d92e7e745db109ae4a864e00` |
| `ode-sep-cand-003` | `sha256:def46ae6c01084eb7928c0c0a4cec2ff839b11c1311ebb5fd496ba57bd8c88a7` |
| `ode-hom-cand-001` | `sha256:5c6dbe85b7882ea3b5dbee579f2c852cade324eba1f1c5c25d5122da06a36c5d` |
| `ode-hom-cand-002` | `sha256:c656030f14ba09e8d24fc6affaa3043273841add2415844890d61b0b5bb1e11c` |
| `ode-linear-cand-001` | `sha256:ff0bbde30656ab6443978677478a3ea4d5879c019757dcb9a8425c4796a56f6a` |
| `ode-linear-cand-002` | `sha256:29489ec9f7e68f8feb68987dbb539d67d7ad72c8e2e752f0307189b8ff442619` |
| `ode-mixed-cand-001` | `sha256:e42be0f4aa76372903d4bc361efc090ed2266c7c7005c8f1c44b643dae0e048c` |

Preview manifests use `status: published` only inside the dry-run candidate shape. No formal catalog file was written.

## Human Review Gate Status

Each draft includes a complete review checklist to satisfy the dry-run workflow. This is not formal publish approval.

Formal publish planning still requires a separate human review and candidate selection step.

## Formal Catalog Unchanged Check

Formal catalog manifest content remains:

```yaml
catalog_schema_version: "1.0"
questions:
  - questions/ode-sep-001.yaml
  - questions/ode-sep-draft-001.yaml
  - questions/ode-sep-retired-001.yaml
  - questions/ode-sep-internal-001.yaml
```

Formal catalog question files remain the existing four files:

- `ode-sep-001.yaml`
- `ode-sep-draft-001.yaml`
- `ode-sep-internal-001.yaml`
- `ode-sep-retired-001.yaml`

No formal catalog manifest entry or formal question YAML was added for Phase 4.8 candidates.

## Learner API Isolation Check

Learner API check:

- `GET /api/learner/v1/nodes/ode_separable/questions` returned count `1`.
- The only visible learner question remained `ode-sep-001`.
- `GET /api/learner/v1/questions/ode-sep-cand-001` returned `404 question_not_found`.

This confirms Phase 4.8 drafts are not visible to learner-facing APIs.

## Regression Results

Full pytest:

- `467 passed`

Golden eval:

- Scoring eval: `30/30 passed`
- Diagnosis eval: `25/25 passed`
- Movement eval: `12/12 passed`

## Known Issues And Risks

- These drafts are only authored and validated; they have not been selected for real learner use.
- Mathematical quality still needs human review before any formal publish planning.
- Content hashes are available from dry-run previews, but no formal content-addressed publish step was executed.
- The current batch is intentionally small and covers only three existing ODE nodes.
- No scoring integration was performed against these drafts in a live attempt flow.

## Go / No-Go For Formal Publish Planning

Go for a follow-up human review and candidate selection plan.

No-go for direct formal publish. Phase 4.8 did not perform publish/export and did not modify the formal catalog.

## Recommended Next Step

Recommended next step: Phase 4.8.1 Freeze / Authoring Draft Boundary Audit, or a Human Review And Candidate Selection Plan.

Do not enter Phase 4.9 or formal publish without an explicit separate approval.
