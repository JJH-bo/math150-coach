# Phase 4.8.5 Authoring-only Revision Report

Status: complete. Top 3 authoring-only drafts were revised, validated, and rebuilt as dry-run previews. No formal publish, formal import, formal catalog write, manifest edit, code change, endpoint change, or scoring integration was performed.

## 1. Executive Decision

Phase 4.8.5 revised only the human-review-recommended Top 3 authoring drafts:

1. `ode-linear-cand-002`
2. `ode-mixed-cand-001`
3. `ode-sep-cand-002`

The revisions move these candidates closer to publish-readiness while keeping them strictly inside the authoring workspace.

This phase does not approve publication. It creates revised authoring drafts, validation reports, and dry-run previews for later human/freeze review.

Recommended next step:

```text
Phase 4.8.5.1 Authoring Revision Boundary Freeze
```

Do not directly enter formal publish from this report.

## 2. Scope And Non-goals

In scope:

- revise only the Top 3 authoring draft YAML files;
- strengthen answer aliases and existing rubric items;
- reduce over-explicit public prompt wording where required;
- generate Phase 4.8.5 validation reports;
- generate Phase 4.8.5 dry-run previews;
- confirm formal catalog and learner API boundaries.

Out of scope:

- modifying non-Top-3 candidate drafts;
- modifying `backend/catalog_data/manifest.yaml`;
- modifying `backend/catalog_data/questions/*.yaml`;
- adding formal question YAML;
- formal publish or formal import;
- modifying engines, APIs, LearningOrchestrator, Local Trainer, coach output, CatalogValidator, or authoring CLI;
- adding endpoints, history, frontend, database, auth, LLM, mastery, review, attempt persistence, or scoring integration;
- entering Phase 4.8.5.1, Phase 4.8.6, or Phase 4.9.

## 3. Revised Candidate Set

| Candidate | Node | Revision status |
| --- | --- | --- |
| `ode-linear-cand-002` | `ode_first_order_linear` | revised, validated, dry-run preview generated |
| `ode-mixed-cand-001` | `ode_first_order_linear` | revised, validated, dry-run preview generated |
| `ode-sep-cand-002` | `ode_separable` | revised, validated, dry-run preview generated |

Optional candidates remain unchanged and were not revised:

- `ode-sep-cand-003`
- `ode-hom-cand-002`

Other non-Top-3 drafts also remain unchanged.

## 4. Files Modified

Modified authoring drafts:

- `backend/catalog_authoring/phase_4_8/drafts/ode-linear-cand-002.yaml`
- `backend/catalog_authoring/phase_4_8/drafts/ode-mixed-cand-001.yaml`
- `backend/catalog_authoring/phase_4_8/drafts/ode-sep-cand-002.yaml`

Modified documentation:

- `README.md`

Added documentation:

- `docs/phase_4_8_5_authoring_revision_report.md`

Generated validation reports:

- `backend/catalog_authoring/phase_4_8/reports/phase_4_8_5/ode-linear-cand-002.validate.json`
- `backend/catalog_authoring/phase_4_8/reports/phase_4_8_5/ode-mixed-cand-001.validate.json`
- `backend/catalog_authoring/phase_4_8/reports/phase_4_8_5/ode-sep-cand-002.validate.json`

Generated dry-run previews:

- `backend/catalog_authoring/phase_4_8/previews/phase_4_8_5/ode-linear-cand-002.preview.json`
- `backend/catalog_authoring/phase_4_8/previews/phase_4_8_5/ode-mixed-cand-001.preview.json`
- `backend/catalog_authoring/phase_4_8/previews/phase_4_8_5/ode-sep-cand-002.preview.json`

No code files were modified.

## 5. Candidate-specific Revision Summary

### `ode-linear-cand-002`

Question ID: `ode-linear-cand-002`

Draft path: `backend/catalog_authoring/phase_4_8/drafts/ode-linear-cand-002.yaml`

What changed:

- Public prompt now asks the learner to rewrite to first-order linear standard form and solve, without directly naming the integrating factor method.
- Answer aliases now include additional equivalent term orders and formatting forms.
- `transformation_standard_form` now accepts pattern variants of `y' + 2y = 3x` and `dy/dx + 2y = 3x`.
- `calculation_linear_solution` now uses patterns for `3x/2` and `-3/4`.
- `final_answer_linear_general` now uses order-tolerant patterns for `3x/2`, `-3/4`, and `C e^(-2x)`.
- Solution outline explicitly records equivalent term orders as acceptable.

What did not change:

- `node_id` remains `ode_first_order_linear`.
- Core equation remains `2y' + 4y = 6x`.
- Standard-form transformation remains a required scoring point.
- Expected answer remains `y=3x/2-3/4+Ce^(-2x)`.
- No public expected answer or solution outline was added.

Public prompt safety:

- The prompt does not contain the final answer.
- The hint still only suggests dividing to make the coefficient of `y'` equal to one.

Trusted scoring changes:

- Existing dimensions remain `trigger`, `method`, `transformation`, `calculation`, and `final_answer`.
- No new scoring dimension was added.

Rubric changes:

- Transformation, calculation, and final-answer rubric items were made less brittle through existing `expected_patterns`.
- Standard-form transformation was not weakened.

Validator / alias changes:

- Added term-order and formatting aliases for the same solution family.
- No unsupported `validator_config` key was added.

Validation result:

- `validate-draft`: passed.

Dry-run preview path:

- `backend/catalog_authoring/phase_4_8/previews/phase_4_8_5/ode-linear-cand-002.preview.json`

Content hash:

- `sha256:502de673cf0993c758b39033d3385c2c4b749856d3dfe1104e01fbd2c6e728e1`

Remaining risk:

- Lightweight normalization still does not prove symbolic equivalence; human review should inspect the alias set before any formal publish phase.

### `ode-mixed-cand-001`

Question ID: `ode-mixed-cand-001`

Draft path: `backend/catalog_authoring/phase_4_8/drafts/ode-mixed-cand-001.yaml`

What changed:

- Public stem and prompt were softened so the learner must decide the method rather than being directly told to use first-order linear form.
- Added a required diagnostic rubric item for explaining why the equation should not be forced into standard separable-variable handling.
- Strengthened trigger rubric so `linear` alone is not enough without standard-form evidence.
- Strengthened method rubric so `integrating factor` alone is not enough without multiplier/product-form evidence.
- Added answer alias `y=C/x+x^2/3`.
- Solution outline now records `x>0`, the first-order linear structure, why not standard separation, and integrating factor `x`.

What did not change:

- `node_id` remains `ode_first_order_linear`.
- Core equation remains `y' + (1/x)y = x, x>0`.
- Expected answer remains `y=x^2/3+C/x`.
- Alias `xy=x^3/3+C` remains.
- Integrating factor `x` remains a transformation scoring point.

Public prompt safety:

- Public prompt asks the learner to decide the equation type and compare separation, but does not reveal the final answer or solution outline.
- Public hint mentions standard form only, not the final integrating factor or answer.

Trusted scoring changes:

- Existing dimensions remain `trigger`, `method`, `transformation`, `calculation`, and `final_answer`.
- The new diagnostic item uses only supported dimensions.

Rubric changes:

- Added `diagnostic_not_standard_separable`.
- Strengthened trigger/method/transformation items with existing `expected_patterns`.
- Removed the non-ASCII `µ` pattern variant after local stdout showed an encoding issue; ASCII `mu` remains supported.

Validator / alias changes:

- Added one additional y-form alias with term order changed.
- Kept `answer_equivalence_mode: normalized` and `requires_constant: true`.

Validation result:

- `validate-draft`: passed.

Dry-run preview path:

- `backend/catalog_authoring/phase_4_8/previews/phase_4_8_5/ode-mixed-cand-001.preview.json`

Content hash:

- `sha256:7254ef262c09f8dff92d6a5e6b3c327a75144d6f75e88bbffa5de620a7991b62`

Remaining risk:

- The diagnostic pattern is intentionally conservative. Human review should check that it does not reject valid learner explanations phrased without the word `separable`.

### `ode-sep-cand-002`

Question ID: `ode-sep-cand-002`

Draft path: `backend/catalog_authoring/phase_4_8/drafts/ode-sep-cand-002.yaml`

What changed:

- Public prompt no longer directly says the equation becomes separable.
- Public hint now asks the learner to isolate `dy/dx` and decide the rearranged structure.
- Preferred expected answer changed to `y=C(1+x^2)`.
- Log form `ln|y| = ln(1+x^2) + C` remains as an alias.
- Final-answer rubric now accepts the explicit form or the trusted log form.
- Solution outline now records constant absorption and that the zero solution is included by `C=0`.

What did not change:

- `node_id` remains `ode_separable`.
- Core equation remains `(1+x^2) dy/dx = 2xy`.
- Rearrangement and separated-form transformation remain required scoring points.
- No trusted solution was copied into public prompt or hint.

Public prompt safety:

- The prompt asks the learner to decide the method after rearranging.
- The hint does not reveal the separated form.

Trusted scoring changes:

- Existing dimensions remain `trigger`, `method`, `transformation`, `calculation`, and `final_answer`.
- Expected answer now uses the explicit general solution as preferred form.

Rubric changes:

- Final answer item now accepts either explicit or trusted log form by pattern.
- Rearrangement/transformation rubric remains intact.

Validator / alias changes:

- Main expected answer changed to `y=C(1+x^2)`.
- Log form preserved as alias.
- Duplicate whitespace-only alias was intentionally not kept, because the publish-candidate validator rejects normalized duplicate aliases.

Validation result:

- `validate-draft`: passed.

Dry-run preview path:

- `backend/catalog_authoring/phase_4_8/previews/phase_4_8_5/ode-sep-cand-002.preview.json`

Content hash:

- `sha256:2d27bbf603c84374b5b08d2ceb76d62ebe3a4c9322f5aa687e8901cc2c070296`

Remaining risk:

- The log-form alias is accepted by string normalization, not symbolic proof. A later formal publish phase should inspect whether more equivalent explicit forms are needed.

## 6. Rubric Revision Summary

Rubric changes were limited to supported `RubricItem` fields:

- `required_keywords`
- `expected_patterns`
- `weight`
- `required`
- `target_dimensions`
- `evidence_on_hit`
- `evidence_on_miss`

No unsupported schema key was added.

No unsupported scoring dimension was added.

The main rubric improvements were:

- less brittle final-answer patterns for `ode-linear-cand-002`;
- explicit mixed-recognition diagnostic evidence for `ode-mixed-cand-001`;
- reduced public prompt hinting while preserving separable transformation scoring for `ode-sep-cand-002`.

## 7. Answer Alias / Validator Revision Summary

`ode-linear-cand-002`:

- Added aliases for equivalent term order and formatting variants.
- Kept normalized validator mode and arbitrary constant requirement.

`ode-mixed-cand-001`:

- Kept `y=x^2/3+C/x` and `xy=x^3/3+C`.
- Added `y=C/x+x^2/3`.
- Kept `x>0` logic in trusted solution outline and transformation rubric.

`ode-sep-cand-002`:

- Preferred answer changed to `y=C(1+x^2)`.
- Log form preserved as alias.
- Kept arbitrary constant requirement.

No new validator behavior was assumed. No `CatalogValidator`, `MathValidatorScorer`, or scoring engine code was changed.

## 8. Public Prompt Safety Summary

Public prompt and hint changes were checked against these boundaries:

- no expected answer in public prompt;
- no solution outline in public prompt;
- no trusted rubric wording copied into public prompt;
- no answer key in public hint;
- prompts remain learner-facing and method-discovery oriented.

`ode-sep-cand-002` received the most important public prompt safety revision because its prior prompt directly said it becomes separable.

## 9. Validation Command Summary

Successful `validate-draft` commands:

```text
python -m app.catalog.authoring_cli --authoring-root catalog_authoring/phase_4_8 validate-draft drafts/ode-linear-cand-002.yaml --output phase_4_8_5/ode-linear-cand-002.validate.json
python -m app.catalog.authoring_cli --authoring-root catalog_authoring/phase_4_8 validate-draft drafts/ode-mixed-cand-001.yaml --output phase_4_8_5/ode-mixed-cand-001.validate.json
python -m app.catalog.authoring_cli --authoring-root catalog_authoring/phase_4_8 validate-draft drafts/ode-sep-cand-002.yaml --output phase_4_8_5/ode-sep-cand-002.validate.json
```

Results:

- `ode-linear-cand-002`: passed.
- `ode-mixed-cand-001`: passed.
- `ode-sep-cand-002`: passed.

Successful `validate-batch` command:

```text
python -m app.catalog.authoring_cli --authoring-root catalog_authoring/phase_4_8 validate-batch import_manifest.yaml
```

Result:

- total: 8
- passed: 8
- failed: 0
- issues: []

Note: the existing import manifest still uses `output_report_dir: phase_4_8`. Because this phase forbids manifest edits, batch validation was run to stdout without an output file to avoid overwriting old Phase 4.8 batch reports.

## 10. Dry-run Preview Summary

Successful `build-candidate-dry-run` commands:

```text
python -m app.catalog.authoring_cli --authoring-root catalog_authoring/phase_4_8 build-candidate-dry-run --draft-path drafts/ode-linear-cand-002.yaml --output phase_4_8_5/ode-linear-cand-002.preview.json
python -m app.catalog.authoring_cli --authoring-root catalog_authoring/phase_4_8 build-candidate-dry-run --draft-path drafts/ode-mixed-cand-001.yaml --output phase_4_8_5/ode-mixed-cand-001.preview.json
python -m app.catalog.authoring_cli --authoring-root catalog_authoring/phase_4_8 build-candidate-dry-run --draft-path drafts/ode-sep-cand-002.yaml --output phase_4_8_5/ode-sep-cand-002.preview.json
```

Dry-run preview results:

| Candidate | dry_run_only | Content hash |
| --- | --- | --- |
| `ode-linear-cand-002` | true | `sha256:502de673cf0993c758b39033d3385c2c4b749856d3dfe1104e01fbd2c6e728e1` |
| `ode-mixed-cand-001` | true | `sha256:7254ef262c09f8dff92d6a5e6b3c327a75144d6f75e88bbffa5de620a7991b62` |
| `ode-sep-cand-002` | true | `sha256:2d27bbf603c84374b5b08d2ceb76d62ebe3a4c9322f5aa687e8901cc2c070296` |

## 11. Formal Catalog Boundary Confirmation

Confirmed:

- `backend/catalog_data/manifest.yaml` was not modified.
- `backend/catalog_data/questions/*.yaml` was not modified.
- No formal question YAML was added.
- No formal import was executed.
- No formal publish was executed.
- No Top 3 candidate was registered in the formal catalog.

The formal manifest still contains only:

```text
questions/ode-sep-001.yaml
questions/ode-sep-draft-001.yaml
questions/ode-sep-retired-001.yaml
questions/ode-sep-internal-001.yaml
```

Search under `backend/catalog_data` found no Top 3 candidate ids.

## 12. Learner API Boundary Confirmation

Learner-safe listing still exposes only:

```text
ode-sep-001
```

The revised Top 3 candidates remain absent from learner-visible catalog output.

## 13. Known Risks

1. The answer alias and rubric pattern support is string/pattern based, not symbolic ODE equivalence.
2. `ode-mixed-cand-001` diagnostic wording may still be too conservative for learners who explain non-separability in different words.
3. `ode-linear-cand-002` aliases cover common term orders but do not exhaust every algebraic equivalent.
4. `ode-sep-cand-002` accepts the trusted log form and preferred explicit form, but not every possible constant-renaming style.
5. The current human review checklist still uses the earlier placeholder reviewer metadata; a later freeze/human audit should inspect the revised drafts before publish planning continues.
6. Batch validation was run without writing a Phase 4.8.5 batch output file because the existing manifest controls `output_report_dir` and this phase forbids manifest edits.

## 14. Recommended Next Step

Recommended next phase:

```text
Phase 4.8.5.1 Authoring Revision Boundary Freeze
```

The freeze should audit:

- only Top 3 drafts changed;
- non-Top-3 drafts remain unchanged;
- revised prompts are learner-safe;
- trusted scoring remains server-side;
- validation reports and dry-run previews are present;
- formal catalog and learner API exposure remain unchanged;
- no accidental code, manifest, endpoint, engine, or catalog-data modification occurred.

Do not proceed directly to formal publish. Formal publish/import must remain a later explicitly approved phase.
