# Phase 4.2 Freeze Report

Phase 4.2 is frozen after the Phase 4.2.1 catalog validation contract audit.

## Status

Complete:

- Catalog Validation Hardening;
- `CatalogValidator`;
- repository delegation to `CatalogValidator`;
- default catalog validation under the new rules;
- no API behavior change;
- no engine behavior change.

## Verification Baseline

Final local verification for the freeze pack:

- pytest: `315 passed`;
- scoring eval: `30/30 passed`;
- diagnosis eval: `25/25 passed`;
- movement eval: `12/12 passed`.

## Frozen CatalogValidator Contract

The frozen validator contract covers:

- identity and manifest consistency validation;
- public presentation validation;
- trusted scoring completeness validation;
- rubric integrity validation;
- `validator_config` whitelist and reserved-key protection;
- node and dimension consistency validation;
- public/trusted leak boundary validation;
- version format validation;
- `content_hash` format-only validation.

## Error Behavior

Runtime catalog validation is fail-fast.

`CatalogValidationError` carries an `error_code`.

No `CatalogValidationReport` exists yet. A full multi-error report is deferred to a future authoring/import workflow.

Frozen error code families:

- `catalog_identity_error`
- `catalog_public_layer_error`
- `catalog_trusted_layer_error`
- `catalog_rubric_error`
- `catalog_dimension_error`
- `catalog_leak_error`
- `catalog_version_error`
- `catalog_hash_error`
- `catalog_validation_error` for Pydantic/schema-level errors

## Public Presentation Contract

Public presentation rules:

- `title`, `stem`, and `prompt_markdown` must be nonblank;
- `answer_format` allowed values are `expression`, `equation`, `free_text`, and `expression_with_reasoning`;
- `response_step_mode` allowed values are `none`, `optional`, and `required`;
- `difficulty` allowed values are `basic`, `standard`, and `comprehensive`;
- `display_assets` remains `list[dict]`, but cannot contain trusted field names;
- public layer payloads cannot contain trusted field names;
- exact expected-answer leak detection is lightweight and not semantic.

## Trusted Scoring Contract

For published learner questions:

- `expected_answer` is required;
- `solution_outline` is required;
- `rubric` is required;
- `answer_aliases` may be empty, but cannot contain blanks or duplicates;
- rubric items require id, description, target dimensions, positive weight, and hit/miss evidence;
- rubric item ids must be unique;
- at least one required rubric item is required;
- required items need `required_keywords` or `expected_patterns`.

## Validator Config Contract

Unknown keys fail fast.

Reserved keys fail fast.

Allowed keys:

- `requires_constant: bool`
- `requires_initial_condition: bool`
- `answer_equivalence_mode: exact | normalized | symbolic`

Adding new `validator_config` keys in the future requires tests and documentation updates.

## Dimension Contract

Rules:

- rubric `target_dimensions` must be valid `ScoreDimension` values;
- target dimensions should belong to `node.core_dimensions`;
- allowed extension dimensions are `calculation`, `final_answer`, and `expression`;
- published learner questions must cover at least one node core dimension.

## Version And Immutability Contract

Rules:

- `question_version`, `rubric_version`, `answer_key_version`, and `catalog_schema_version` must be nonblank;
- versions must be semver-like: `1`, `1.0`, or `1.0.0`;
- `question_id` is an immutable published artifact id;
- prompt, expected answer, rubric, or validator config changes that affect scoring require a new `question_id`;
- Phase 4.2 does not implement Git diff checks or historical version comparison.

## Content Hash Contract

Only format validation is implemented.

Accepted format:

```text
sha256:<64 lowercase hex chars>
```

Not implemented:

- hash calculation;
- hash comparison;
- automatic hash generation.

Strong `content_hash` verification is deferred to a future authoring/import workflow.

## Formal Catalog Sample Correction

The formal catalog sample `ode-sep-001` had its integration rubric item changed from `process` to `calculation`.

Reason:

- `ode_separable` node core dimensions do not include `process`;
- `calculation` is a core dimension for `ode_separable` and is also an allowed extension dimension;
- ODE nodes YAML and golden eval cases were not modified.

## Unchanged Boundaries

Unchanged:

- core engines;
- `/api/v1` frozen contract;
- `/api/learner/v1` learner contract;
- APP_PROFILE gating;
- learner-safe projector;
- ODE nodes YAML;
- golden eval cases;
- no new endpoints.

## Contract Audit

Audit conclusions:

1. `CatalogValidator` is called by `YamlQuestionCatalogRepository`.
2. `YamlQuestionCatalogRepository.validate_catalog()` remains available.
3. The default catalog passes the new validator.
4. Negative tests use `tmp_path` temporary fixtures and do not pollute formal catalog samples.
5. The formal catalog sample received only the necessary dimension correction described above.
6. `/api/v1` endpoint behavior is unchanged.
7. `/api/learner/v1` endpoint behavior is unchanged.
8. APP_PROFILE gating is unchanged.
9. Learner API leak regression tests pass.
10. Profile gating regression tests pass.
11. Scoring, diagnosis, and movement evals all pass.
12. `content_hash` is format-only.
13. `validator_config` unknown keys fail fast.
14. `validator_config` reserved keys fail fast.
15. Public/trusted leak boundary has catalog-level tests.

## Known Limits

Current limits:

- public leak detection is exact-match only;
- no semantic leak detection;
- `content_hash` is not strongly enforced;
- YAML catalog remains in-memory;
- no authoring/import workflow;
- no database;
- no frontend;
- no mastery or review scheduler;
- no real LLM;
- no complete Mathematics I graph.

## Recommended Next Phase

Do not jump directly to frontend, database, mastery, review, or LLM.

The next phase should be Phase 4.3 Plan only, not implementation.

Candidate directions:

- catalog authoring/import workflow plan;
- attempt persistence plan;
- mastery/review model research;
- broader question catalog expansion plan.

Scope requires explicit user approval.

