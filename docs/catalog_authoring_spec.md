# Catalog Authoring Spec

Status: Phase 4.3 authoring/import workflow skeleton. Frozen by Phase 4.3.1.

This spec describes how draft question material can become a validated runtime catalog candidate without letting drafts leak into learner API behavior.

## Workflow

### 1. Source Intake

Record provenance in `SourceMetadata`.

Supported source types:

- `textbook`
- `lecture_notes`
- `past_exam`
- `generated_variant`
- `manual`
- `unknown`

Source metadata is internal-only. It must not enter `PublicQuestionView`, learner responses, or the runtime content hash by default.

### 2. Draft Creation

Create an `AuthoringDraft` with:

- `draft_id`
- optional `import_batch_id`
- `status`
- `candidate_record`
- optional `source_metadata`
- optional `validation_report`
- optional `review_checklist`
- `ai_assisted`

The candidate is a normal `CatalogQuestionRecord`, but the wrapper is authoring-only. Drafts must not be scanned by `YamlQuestionCatalogRepository`.

### 3. Pre-Validation

`CatalogAuthoringWorkflow.validate_draft()` runs the candidate record through the existing `CatalogValidator`.

On success:

- returns `CatalogValidationReport(passed=true)`;
- marks the draft `validated`.

On failure:

- catches `CatalogValidationError`;
- returns `CatalogValidationReport(passed=false)`;
- includes the validator `error_code`;
- marks the draft `validation_failed`.

This does not change runtime fail-fast validation.

### 4. Human Review

Before a publish candidate can be built, a human checklist must pass.

Required checklist fields:

- math I scope confirmed;
- module/topic/type confirmed;
- node id confirmed;
- public prompt clear;
- expected answer checked;
- aliases checked;
- solution outline checked;
- rubric checked;
- target dimensions checked;
- validator config checked;
- no public leak confirmed;
- question id/version checked;
- publish approved.

AI can assist draft creation, but `ai_assisted=true` never permits automatic publication.

### 5. Publish Candidate

`build_publish_candidate()` creates an in-memory runtime `CatalogQuestionRecord` candidate only when:

- validation passed;
- human review passed;
- the draft is not rejected.

The candidate receives a generated `content_hash` and is validated again by `CatalogValidator`.

The workflow does not write the formal catalog and does not register the candidate with learner routes.

The Phase 4.3.1 freeze records this as a hard boundary: publish candidates are dry-run, in-memory artifacts until a later explicit publish/export phase is approved.

### 6. Reject

`reject_draft()` marks a draft rejected and records a reason. Rejected drafts cannot become publish candidates.

### 7. Retire / Supersede

Retire and supersede are reserved for a later implementation. The current skeleton can validate a candidate with runtime `supersedes`, but it does not write a revision chain.

Current single-draft validation does not prove that a `supersedes` target exists in the formal catalog. A later formal publish/retire/supersede phase must add supersession chain validation before writing catalog artifacts.

## Hash Strategy

The authoring hash utility computes:

```text
sha256:<64 lowercase hex chars>
```

Hash input is the canonical runtime artifact:

- manifest without `content_hash`;
- presentation;
- trusted scoring without `authoring_metadata`.

It excludes authoring-side source metadata, validation reports, review checklists, and timestamps.

## Draft Isolation

Learner API isolation rules:

- learner routes read only the formal catalog repository;
- authoring drafts are never served by learner routes;
- source metadata never appears in learner GET question;
- source metadata never appears in learner submit response;
- validation reports and review checklists never enter runtime records.

## Future Reserved Interfaces

Future database tables may include:

- authoring batches;
- authoring drafts;
- validation reports;
- review records;
- published catalog artifacts;
- supersession links.

Future UI surfaces may include:

- draft editor;
- rubric editor;
- validator config editor;
- source metadata editor;
- validation report view;
- review checklist;
- publish candidate preview.

Future CLI commands may include:

- dry-run import;
- validate draft;
- compute hash;
- build publish candidate;
- export validation report.

These are reserved interfaces only. Phase 4.3 does not implement DB, UI, auth, or CLI.

Phase 4.3.1 freezes these as non-goals for the current implementation.

## Phase 4.4 Import CLI

Phase 4.4 adds a minimal authoring-side CLI:

```text
python -m app.catalog.authoring_cli ...
```

Implemented commands:

- `validate-draft`
- `validate-batch`
- `build-candidate-dry-run`

The CLI remains dry-run only. It reads authoring drafts and import manifests, emits validation reports and candidate previews, and never writes the formal catalog.

Formal publish/export commands remain reserved for later phases.

Phase 4.4.1 freezes this CLI as dry-run only. It does not support formal publish/export and does not create persistent authoring history.
