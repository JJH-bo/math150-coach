# Phase 4.2 Catalog Validation Hardening

Status: implementation complete and frozen by Phase 4.2.1.

Phase 4.2 adds a lightweight `CatalogValidator` for server-side YAML catalog validation. It does not add product features, endpoints, database persistence, frontend, LLM integration, mastery, review scheduling, attempt persistence, catalog authoring UI, or new scoring/diagnosis/movement rules.

## Architecture

`YamlQuestionCatalogRepository` still owns:

- YAML `safe_load`;
- manifest path loading;
- path escape protection;
- record loading;
- in-memory indexing.

`CatalogValidator` owns:

- identity and manifest validation;
- public presentation validation;
- trusted scoring validation;
- rubric validation;
- dimension and node consistency validation;
- public/trusted leak boundary checks;
- `content_hash` format validation.

Runtime behavior remains fail-fast through `CatalogValidationError`.

## Error Behavior

Phase 4.2 keeps runtime validation simple:

- fail fast on the first catalog error;
- no UI messages;
- no internationalization;
- no full `CatalogValidationReport`.

`CatalogValidationError` now carries an `error_code` for tests and future tooling.

Error code families:

- `catalog_identity_error`
- `catalog_public_layer_error`
- `catalog_trusted_layer_error`
- `catalog_rubric_error`
- `catalog_dimension_error`
- `catalog_leak_error`
- `catalog_version_error`
- `catalog_hash_error`

A full `CatalogValidationReport` remains deferred to a future authoring/import workflow.

## Rule Groups

Implemented rule groups:

- identity and manifest consistency;
- public layer nonblank and enum validation;
- trusted scoring completeness for published learner questions;
- rubric item id, description, dimension, weight, required, and evidence validation;
- validator config whitelist and reserved-key protection;
- node core dimension coverage with limited extension dimensions;
- exact expected-answer leak detection for public prompt and public hints;
- trusted field-name leak detection in public payloads and display assets;
- semver-like version field validation;
- `content_hash` format validation.

## Validator Config Whitelist

Allowed keys:

- `requires_constant: bool`
- `requires_initial_condition: bool`
- `answer_equivalence_mode: "exact" | "normalized" | "symbolic"`

Unknown keys fail fast. New validator keys must be added intentionally with tests and docs.

## Content Hash

Phase 4.2 does not enforce content hash correctness.

If `content_hash` exists, it must match:

```text
sha256:<64 lowercase hex chars>
```

The validator does not calculate, compare, or generate hashes. Strong hash verification is deferred to a future authoring/import workflow.

Recommended future hash input:

- manifest identity, version, status, audience, and tags;
- full presentation;
- full trusted scoring;
- excluding `content_hash` itself;
- excluding `authoring_metadata`.

## Compatibility Notes

One formal catalog sample was corrected because it violated the new dimension rule: `ode-sep-001` moved its integration rubric item from `process` to `calculation`, since `ode_separable` does not include `process` in `node.core_dimensions` and `process` is not an allowed extension dimension.

Unchanged:

- core engines;
- `/api/v1` endpoint behavior;
- `/api/learner/v1` endpoint behavior;
- APP_PROFILE gating;
- learner-safe projector;
- ODE nodes YAML;
- golden eval cases.

## Verification

Phase 4.2 verification:

- pytest: `315 passed`;
- scoring eval: `30/30 passed`;
- diagnosis eval: `25/25 passed`;
- movement eval: `12/12 passed`.

## Next Step

Recommended next step is Phase 4.2.1 freeze pack. Do not enter frontend, persistence, mastery, review, or LLM work without explicit scope approval.

## Phase 4.2.1 Freeze Status

Phase 4.2.1 adds no product feature. It records the catalog validation contract audit and freezes the validator boundary.

Frozen points:

- `CatalogValidator` is the server-side catalog quality gate;
- runtime catalog validation is fail-fast;
- `CatalogValidationError.error_code` is the structured error hook;
- `content_hash` remains format-only;
- public leak detection remains exact-match only;
- no API endpoint, engine, APP_PROFILE, learner projector, ODE node, or golden eval behavior changed.

See `docs/phase_4_2_freeze_report.md` for the freeze record.
