# Phase 4.4 Minimal Import CLI / Dry-run Batch Workflow

Status: implementation complete. Micro-hardening complete. Frozen by Phase 4.4.1.

Phase 4.4 adds a minimal authoring-side CLI for dry-run import validation. It does not write the formal catalog, add endpoints, add database persistence, add frontend, add auth, add LLM integration, add mastery/review behavior, or expand the formal question bank.

## Implemented Commands

Package entry:

```text
python -m app.catalog.authoring_cli ...
```

Implemented:

- `validate-draft`
- `validate-batch`
- `build-candidate-dry-run`

Planned but not implemented:

- `hash-record`
- `export-report`
- `export-publish-candidate`
- `apply-to-formal-catalog`
- `retire-question`
- `supersede-question`
- `verify-supersession-chain`
- `regenerate-content-hash`

Formal publish/export remains a future phase.

## Command Behavior

`validate-draft`:

- reads one `AuthoringDraft` YAML;
- runs Pydantic parsing and `CatalogAuthoringWorkflow.validate_draft`;
- emits a `CatalogValidationReport` payload;
- does not require human review;
- does not build a publish candidate;
- does not write formal catalog files.

`validate-batch`:

- reads an `ImportManifest`;
- loads authoring drafts;
- merges source metadata;
- attaches sidecar review checklist when configured;
- validates each draft;
- reports review readiness;
- does not build publish candidates;
- does not write formal catalog files.

`build-candidate-dry-run`:

- reads one draft directly or through manifest + draft id;
- requires validation success;
- requires complete human review;
- blocks rejected drafts;
- blocks AI-assisted drafts unless normal human review is complete;
- builds an in-memory publish candidate;
- generates a deterministic `content_hash`;
- emits a dry-run preview;
- does not write formal catalog files.

## Exit Codes

- `0`: success
- `1`: validation failed
- `2`: schema / parse error
- `3`: path / file access error
- `4`: human review gate failed
- `5`: internal unexpected error

Normal CLI results return structured payloads and avoid stack traces. Debug mode may include additional diagnostics.

## Strict / Non-strict Batch

`strict_mode=true`:

- any failed draft makes `validate-batch` exit with code `1`.

`strict_mode=false`:

- mixed pass/fail batches may exit with code `0`;
- the report still records `failed > 0`.

## Dry-run Safety

Every report and preview includes:

```text
dry_run_only: true
```

The CLI:

- can read authoring drafts;
- can read the formal catalog only for validation context;
- must not write `backend/catalog_data/manifest.yaml`;
- must not write formal question YAML;
- must not register learner API routes;
- must not change repository default root;
- must keep reports under authoring reports paths;
- must keep previews under authoring preview paths;
- rejects path escape.

## Verification

Phase 4.4 adds import CLI tests for:

- import manifest parsing;
- duplicate draft ids;
- expected question id mismatch;
- path escape;
- draft parsing;
- review checklist loading;
- source metadata merge;
- validate-draft exit codes;
- validate-batch strict and non-strict behavior;
- build-candidate dry-run human review gate;
- AI-assisted no-autopublish boundary;
- rejected draft blocking;
- content hash generation;
- formal catalog manifest unchanged;
- learner API cannot fetch dry-run candidates;
- learner leak and APP_PROFILE regressions.

## Next Step

Recommended next phase:

```text
Phase 4.4.1 Freeze Pack + CLI Dry-run Boundary Audit
```

Do not proceed to formal publish/export, database, frontend, auth, LLM, mastery/review, attempt persistence, or broader catalog expansion without an explicit plan.
