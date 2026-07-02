# Phase 4.3 Catalog Authoring / Import Workflow Skeleton

Status: implementation complete. Frozen by Phase 4.3.1.

Phase 4.3 adds an authoring/import workflow skeleton for turning trusted draft question material into a validated publish candidate. It does not write the formal catalog, add endpoints, add a database, add UI, add auth, add LLM integration, add mastery/review behavior, or expand the question bank.

## Scope

Implemented:

- authoring-only models;
- lightweight authoring-side validation reports;
- deterministic runtime content-hash utility;
- dry-run catalog authoring workflow;
- human review gate before publish candidate creation;
- AI-assisted draft boundary requiring human review;
- regression tests for learner API isolation and route gating.

Not implemented:

- real PDF/PPT/OCR import;
- formal catalog writes;
- database persistence;
- authoring UI;
- permissions/auth;
- automatic question generation;
- automatic learner publication;
- new learner endpoints;
- new scoring, diagnosis, rollback, or forward rules.

## Authoring Status

`AuthoringStatus` is independent from runtime `CatalogStatus`.

Authoring-only statuses:

- `imported`
- `draft`
- `validation_failed`
- `validated`
- `review_required`
- `approved`
- `published`
- `rejected`
- `retired`

Only a runtime `CatalogQuestionRecord` publish candidate uses runtime manifest status such as `published`. The authoring workflow does not modify `CatalogStatus`.

## Validation Report

`CatalogValidationReport` is authoring-side only. It wraps the existing fail-fast `CatalogValidator` result.

The runtime validator still raises `CatalogValidationError` and still stops on the first error. Phase 4.3 does not convert runtime validation into multi-error collection.

Current report fields:

- `candidate_id`
- `batch_id`
- `passed`
- `issues`
- `validator_version`

Each issue carries:

- `error_code`
- `message`
- `severity`
- optional `field_path`
- optional `candidate_id`
- optional `batch_id`

## Content Hash

Phase 4.3 adds deterministic hash generation for authoring publish candidates only.

Included in the hash:

- runtime manifest identity, versions, status, audience, tags, node binding, and supersession fields;
- full public presentation;
- trusted scoring except `authoring_metadata`.

Excluded from the hash:

- `manifest.content_hash` itself;
- `trusted_scoring.authoring_metadata`;
- authoring `SourceMetadata`;
- validation reports;
- review checklists;
- timestamps.

Runtime `CatalogValidator` still validates only hash format. It does not calculate, compare, or auto-update hashes.

## Human Review Gate

`build_publish_candidate()` requires both:

- passed `CatalogValidator` report;
- complete `HumanReviewChecklist` with `publish_approved=true`.

AI-assisted drafts cannot bypass review. `ai_assisted=true` is metadata for stricter audit posture, not publish authority.

## Publish Candidate

Phase 4.3 can build a runtime `CatalogQuestionRecord` publish candidate in memory. It does not:

- write `backend/catalog_data/manifest.yaml`;
- write formal question YAML;
- register anything with learner API;
- persist attempts or authoring history.

The publish candidate:

- sets runtime manifest status to `published`;
- receives a generated `content_hash`;
- passes `CatalogValidator`;
- excludes source metadata, validation report, and review checklist.

## Draft Isolation

Authoring drafts live outside runtime catalog loading. The learner API continues to read only the formal server-side catalog through `YamlQuestionCatalogRepository`.

The learner API must not scan authoring drafts and must not expose source metadata, validation reports, review checklists, answer keys, rubrics, or solution outlines.

## Verification

Phase 4.3 adds tests for:

- authoring model separation;
- validation report behavior;
- deterministic hash behavior;
- human review gate;
- AI-assisted no-autopublish boundary;
- draft isolation from learner API;
- APP_PROFILE route-gating regression;
- default formal catalog validation.

Golden evals remain unchanged.

## Next Step

Recommended next phase:

```text
Phase 4.4 Plan
```

Do not enter database, UI, auth, LLM, mastery, review scheduling, or formal catalog expansion without a new explicit plan.
