# Catalog Import CLI Spec

Status: Phase 4.4 minimal dry-run CLI. Frozen by Phase 4.4.1.

The import CLI is an authoring-side tool. It validates drafts and builds dry-run publish candidate previews without writing the formal catalog.

## Entry Point

```text
python -m app.catalog.authoring_cli ...
```

The CLI is implemented as a package module so tests can call command handlers directly.

## Frozen Stdout JSON

`main(argv)` always prints JSON to stdout.

The stdout payload is parseable with `json.loads()` and is never Python `repr`.

When `--output` writes a report or preview, stdout includes `output_path`.

## Import Manifest

`ImportManifest` fields:

- `import_batch_id`
- `batch_name`
- `source_summary`
- `created_by`
- `created_at`
- `default_source_metadata`
- `drafts`
- `output_report_dir`
- `strict_mode`

Each draft entry has:

- `draft_id`
- `path`
- optional `expected_question_id`
- optional `source_metadata_override`
- optional `review_checklist_path`
- optional `ai_assisted`

Rules:

- `draft_id` values must be unique;
- draft paths must stay under the authoring root;
- review checklist paths must stay under the authoring root;
- `expected_question_id`, when present, must match the draft candidate record;
- source metadata merge order is default first, override second;
- import manifests are not formal catalog manifests;
- learner API must not scan import manifests.

## Draft YAML

Phase 4.4 uses full `AuthoringDraft` YAML.

The draft contains:

- `draft_id`
- authoring `status`
- `candidate_record`
- optional source metadata;
- optional validation report;
- optional review checklist;
- optional `ai_assisted`.

Draft YAML is authoring-only. It is not a formal catalog question YAML.

## Commands

### validate-draft

Validates one draft and returns a validation report.

Human review is not required.

Exit codes:

- `0` validation passed;
- `1` validation failed;
- `2` schema / parse error;
- `3` path / file access error;
- `5` unexpected error.

### validate-batch

Validates all drafts in an import manifest and emits a batch report.

It reports review readiness but does not require review completion.

Strict mode:

- `strict_mode=true`: failed drafts make exit code `1`;
- `strict_mode=false`: mixed reports may exit code `0`.

Mixed non-strict reports must still show `failed > 0`.

### build-candidate-dry-run

Builds an in-memory publish candidate preview.

Requirements:

- draft validation passed;
- human review complete;
- `publish_approved=true`;
- draft not rejected;
- AI-assisted draft still has human review.

This command does not write formal catalog files.

## Batch Report

`BatchReport` fields:

- `import_batch_id`
- `total`
- `passed`
- `failed`
- `candidates_built`
- `dry_run_only`
- `issues`
- `per_draft_results`
- `generated_at`
- `tool_version`

Each draft result includes:

- `draft_id`
- `question_id`
- `status`
- `validation_report`
- `human_review_status`
- optional `content_hash`
- optional `publish_candidate_preview_path`

`dry_run_only: true` is mandatory.

## Human Review Behavior

- `validate-draft` does not require review.
- `validate-batch` reports review readiness.
- `build-candidate-dry-run` requires complete review.
- AI-assisted drafts cannot bypass review.
- Rejected drafts cannot build candidates.
- There is no `--allow-unreviewed-preview`.

## Path Safety

All input paths must stay inside the authoring root.

All report output paths must stay inside `authoring_root/reports`.

For `validate-batch`, `output_report_dir` is interpreted only as a subdirectory under `authoring_root/reports`. It may not be an absolute path, may not include `../outside`, and may not point at the formal catalog.

All preview output paths must stay inside the previews root.

The CLI must not output to the formal catalog directory.

## Known Limits

Still not implemented:

- formal publish/export;
- diff / backup / rollback;
- database persistence;
- authoring UI;
- permission/audit system;
- persistent authoring history;
- PDF/PPT/OCR import;
- retire/supersede formal chain.

## Source / Copyright Boundary

Source metadata is internal-only.

Reports may include short source references in future phases, but must not include long copyrighted source text.

Learner API never returns source metadata.

Future UI must separate source/internal views from learner/public views.

## Future Reserved Commands

Reserved for future phases:

- `hash-record`
- `export-report`
- `export-publish-candidate`
- `apply-to-formal-catalog`
- `retire-question`
- `supersede-question`
- `verify-supersession-chain`
- `regenerate-content-hash`

Formal publish/export must be a separate phase with preview, diff, backup, review gate, and tests.
