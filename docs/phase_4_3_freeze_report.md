# Phase 4.3 Freeze Report

Status: Phase 4.3.1 freeze complete.

Phase 4.3 delivered the Catalog Authoring / Import Workflow Skeleton. Phase 4.3.1 freezes that boundary and records the final authoring audit. This is not Phase 4.4 and does not add product features.

## Phase Status

Complete:

- Catalog Authoring / Import Workflow Skeleton.
- Authoring-only models.
- `CatalogValidationReport`.
- Deterministic authoring-side `content_hash` utility.
- Dry-run authoring workflow.
- Human review gate.
- AI-assisted draft cannot auto-publish boundary.
- Draft isolation from learner API.
- No API behavior changed.
- No engine behavior changed.
- No formal catalog write.

## Verification Baseline

Verified baseline for the Phase 4.3 freeze:

- pytest: 355 passed.
- scoring eval: 30/30 passed.
- diagnosis eval: 25/25 passed.
- movement eval: 12/12 passed.

## Frozen Authoring Models Contract

`AuthoringStatus` is independent from runtime `CatalogStatus`.

`SourceMetadata` is internal-only authoring provenance. It is not part of `PublicQuestionView`, learner GET question responses, learner submit responses, or runtime hash input.

`HumanReviewChecklist` is the human gate for publish candidate creation. A publish candidate requires all required checklist fields and `publish_approved=true`.

`AuthoringDraft` is only an authoring wrapper around a candidate `CatalogQuestionRecord`. It is not a runtime catalog record and is not scanned by learner routes.

The following authoring-side fields must not enter learner responses:

- `source_metadata`
- `validation_report`
- `review_checklist`

`AuthoringStatus` must not pollute formal `CatalogStatus`.

## Frozen Validation Report Contract

`CatalogValidationReport` is authoring-side only.

Runtime `CatalogValidator` remains fail-fast through `CatalogValidationError`. Phase 4.3 does not convert runtime validation into multi-error collection.

Current reports can contain only one issue because they wrap the first fail-fast validator error. Future import tooling may extend reports to collect multiple errors, but that is not part of the frozen runtime validator contract.

Report fields:

- `candidate_id`
- optional `batch_id`
- `passed`
- `issues`
- optional `validator_version`

Issue fields:

- `error_code`
- `message`
- `severity`
- optional `field_path`
- optional `candidate_id`
- optional `batch_id`

## Frozen content_hash Contract

`compute_runtime_content_hash()` is only for authoring publish candidates.

Return format:

```text
sha256:<64 lowercase hex chars>
```

The hash is deterministic and uses a canonical runtime artifact payload.

Included:

- runtime manifest identity, node binding, audience, status, versions, tags, and supersession fields;
- full public presentation;
- full trusted scoring except excluded authoring metadata.

Excluded:

- `manifest.content_hash`;
- `trusted_scoring.authoring_metadata`;
- authoring `SourceMetadata`;
- validation report;
- review checklist;
- timestamps.

Frozen behavior:

- changing presentation changes hash;
- changing trusted scoring changes hash;
- changing source metadata does not change hash;
- runtime `CatalogValidator` still validates only `content_hash` format;
- runtime validation does not calculate, compare, or auto-update hashes.

## Frozen Human Review Gate

`build_publish_candidate()` must require:

- passed `CatalogValidator` validation report;
- complete `HumanReviewChecklist`;
- `publish_approved=true`;
- draft not rejected.

Incomplete review cannot build a publish candidate.

Rejected drafts cannot build a publish candidate.

`ai_assisted=True` grants no publishing privilege. AI-assisted drafts still require normal validation and human review.

There is no real permission system, reviewer identity system, or persistent audit ledger in Phase 4.3.

## Frozen Dry-run Publish Candidate Contract

Phase 4.3 only builds an in-memory publish candidate.

It does not:

- write formal `backend/catalog_data/manifest.yaml`;
- write formal question YAML;
- register with learner API;
- persist authoring history;
- generate database records.

A publish candidate:

- has runtime manifest status set to `published`;
- receives a generated `content_hash`;
- passes `CatalogValidator`;
- excludes `source_metadata`;
- excludes `validation_report`;
- excludes `review_checklist`.

## Frozen Draft Isolation Contract

Learner API reads only the formal server-side catalog.

`YamlQuestionCatalogRepository` does not scan authoring drafts.

Authoring drafts are not served by learner API.

Learner GET question responses do not expose source metadata.

Learner submit responses do not expose source metadata.

Validation reports and review checklists do not enter learner responses.

## AI-assisted Authoring Boundary

AI may assist with:

- draft generation;
- rubric suggestions;
- `node_id` suggestions;
- `validator_config` suggestions;
- review checklist draft generation;
- public leak checking suggestions.

AI must not:

- auto-publish;
- bypass `CatalogValidator`;
- bypass human review;
- claim answer correctness without validation;
- copy large copyrighted source passages into public prompts;
- modify frozen engine rules;
- modify learner API behavior.

## Supersedes / Retire Current Limit

Retire and supersede remain future reserved directions.

The current workflow does not write a formal revision chain.

Current `_validate_record()` can validate candidate shape, but it does not prove that `supersedes` points to an existing record in the formal catalog for a single draft outside the runtime repository.

Before formal publish / retire / supersede is implemented, supersession chain validation must be added and tested.

## Unchanged Boundaries

Unchanged:

- core engines;
- `/api/v1` frozen contract;
- `/api/learner/v1` learner contract;
- APP_PROFILE gating;
- `CatalogValidator` contract;
- learner-safe projector;
- ODE nodes YAML;
- golden eval cases;
- formal catalog samples.

Not added:

- endpoints;
- database;
- frontend;
- real LLM;
- auth;
- mastery/review;
- attempt persistence;
- real PDF/PPT/OCR import;
- import CLI;
- formal catalog write path.

## Authoring Boundary Audit

Audit conclusions:

1. `AuthoringStatus` is independent from `CatalogStatus`.
2. `CatalogValidationReport` does not change runtime `CatalogValidator` fail-fast behavior.
3. Hash utility is deterministic.
4. Hash excludes `content_hash` itself.
5. Hash excludes `authoring_metadata`.
6. Hash excludes `SourceMetadata`.
7. `build_publish_candidate()` requires validation passed.
8. `build_publish_candidate()` requires human review passed.
9. Rejected drafts cannot publish.
10. AI-assisted drafts cannot bypass human review.
11. Publish candidates are built only in memory.
12. Publish candidates are not written to formal catalog files.
13. Learner API cannot read authoring drafts.
14. Source metadata does not appear in learner GET question.
15. Source metadata does not appear in learner submit response.
16. Validation reports and review checklists do not enter runtime candidates.
17. Default formal catalog still validates.
18. Learner API leak regression still passes.
19. Learner/internal profile gating regression still passes.
20. Scoring, diagnosis, and movement evals all pass.
21. Supersedes chain validation is not fully implemented and is recorded as a known limit.

## Known Limits

Current limits:

- still skeleton / dry-run;
- no real import CLI;
- no PDF/PPT/OCR import;
- no database persistence;
- no authoring UI;
- no real permission or reviewer identity system;
- no persistent authoring history;
- no formal catalog write;
- no retire/supersede write chain;
- no complete source copyright workflow;
- no semantic leak detection;
- no full symbolic verification;
- no broader Mathematics I catalog expansion.

## Recommended Next Phase

Do not jump directly to frontend, database, mastery, review, LLM, or broad catalog expansion.

The next phase should be Phase 4.4 Plan only, not implementation.

Candidate planning directions:

- minimal import CLI / dry-run batch workflow plan;
- formal publish/export workflow plan;
- attempt persistence plan;
- mastery/review model research;
- broader catalog expansion plan.

Any Phase 4.4 scope requires explicit user approval.
