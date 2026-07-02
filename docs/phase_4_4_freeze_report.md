# Phase 4.4 Freeze Report

Status: Phase 4.4.1 freeze complete.

Phase 4.4 delivered the Minimal Import CLI / Dry-run Batch Workflow. Phase 4.4.1 freezes the CLI dry-run boundary and records the final audit. This is not Phase 4.5 and does not add product features.

## Phase Status

Complete:

- Minimal Import CLI / Dry-run Batch Workflow.
- `validate-draft`.
- `validate-batch`.
- `build-candidate-dry-run`.
- CLI stdout JSON output.
- `output_report_dir` micro-hardening.
- path escape protection.
- `dry_run_only` report and preview marker.
- human review gate.
- AI-assisted draft cannot auto-publish boundary.
- formal catalog unchanged.
- no API behavior changed.
- no engine behavior changed.

## Verification Baseline

Verified baseline for the Phase 4.4 freeze:

- pytest: 410 passed.
- scoring eval: 30/30 passed.
- diagnosis eval: 25/25 passed.
- movement eval: 12/12 passed.

## Frozen CLI Command Contract

Package entry:

```text
python -m app.catalog.authoring_cli
```

Implemented commands:

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

No formal publish/export command exists in Phase 4.4.

## Frozen validate-draft Contract

`validate-draft` reads one `AuthoringDraft` YAML, runs schema validation, runs `CatalogAuthoringWorkflow.validate_draft`, emits a `CatalogValidationReport`, does not require human review, does not build a publish candidate, does not write the formal catalog, and returns a structured JSON payload.

Exit codes:

- `0` if validation passed;
- `1` if validation failed;
- `2` for schema / parse error;
- `3` for path / file access error;
- `5` for unexpected internal error.

## Frozen validate-batch Contract

`validate-batch` reads `ImportManifest`, loads authoring drafts, merges source metadata, attaches sidecar review checklist if configured, validates each draft, reports review readiness, does not build publish candidates, and does not write formal catalog files.

Batch behavior:

- `strict_mode=true`: any failed draft exits `1`;
- `strict_mode=false`: mixed pass/fail may exit `0`;
- non-strict reports must still clearly show `failed > 0`;
- batch report includes `total`, `passed`, and `failed`;
- batch report includes `dry_run_only=true`.

## Frozen build-candidate-dry-run Contract

`build-candidate-dry-run` reads one draft directly or through manifest + `draft_id`, requires validation success, requires complete `HumanReviewChecklist`, requires `publish_approved=true`, rejects rejected drafts, blocks AI-assisted drafts from bypassing review, builds an in-memory publish candidate only, generates `content_hash`, emits preview with `dry_run_only=true`, does not write the formal catalog, and does not register the candidate with learner API.

Learner API cannot fetch dry-run candidates.

## Frozen Exit Code Contract

- `0`: success
- `1`: validation failed
- `2`: schema / parse error
- `3`: path / file access error
- `4`: human review gate failed
- `5`: internal unexpected error

Normal output must not expose stack traces.

Debug mode may include a `debug` field in the JSON payload.

## Frozen Stdout JSON Contract

`main(argv)` outputs JSON payload to stdout.

The stdout payload:

- is parseable with `json.loads()`;
- is not Python `repr`;
- exists even when `--output` is not provided;
- includes `output_path` when a report or preview file is written;
- returns errors as JSON payloads.

## Frozen Path Safety Contract

Input paths:

- draft paths must stay under authoring root;
- import manifest path must stay under authoring root;
- review checklist path must stay under authoring root.

Output paths:

- `validate-draft` report output must stay under `authoring_root/reports`;
- `validate-batch` `output_report_dir` must resolve under `authoring_root/reports/<optional_subdir>`;
- `build-candidate-dry-run` preview output must stay under `authoring_root/previews`.

Rejected:

- `../outside`;
- absolute outside paths;
- formal catalog paths;
- preview output escaping `authoring_root/previews`;
- report output escaping `authoring_root/reports`.

The formal catalog manifest remains unchanged after CLI commands.

## Frozen Dry-run Boundary

Every report and preview includes:

```text
dry_run_only: true
```

The CLI can read authoring drafts and read the formal catalog as validation context.

The CLI cannot write `backend/catalog_data/manifest.yaml`, write formal question YAML, change repository default root, register learner API, publish to learner catalog, or create persistent authoring history.

## Frozen Source / Copyright Boundary

Source metadata is internal-only.

Reports must not include long source or copyright text.

Learner API never returns source metadata, `copyright_note`, validation reports, or review checklists.

Public prompt should contain only necessary problem statement text.

Future UI must separate source/internal content from learner/public content.

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
- formal catalog expansion;
- real PDF/PPT/OCR import;
- formal publish/export.

## CLI Dry-run Boundary Audit

Audit conclusions:

1. CLI implements only `validate-draft`, `validate-batch`, and `build-candidate-dry-run`.
2. `hash-record`, `export-report`, and formal publish/export commands are not implemented.
3. `main(argv)` outputs JSON to stdout.
4. stdout is parseable with `json.loads()`.
5. `validate-draft` with or without `--output` still returns a payload.
6. `build-candidate-dry-run` with or without `--output` still returns a content-hash payload.
7. `validate-batch strict_mode=true` exits `1` on failed drafts.
8. `validate-batch strict_mode=false` can exit `0` with mixed results, but report `failed > 0`.
9. `output_report_dir` cannot escape `authoring_root/reports`.
10. `output_report_dir="../outside"` is rejected.
11. absolute outside `output_report_dir` is rejected.
12. formal catalog output paths are rejected.
13. preview output cannot escape `authoring_root/previews`.
14. draft path escape is rejected.
15. review checklist path escape is rejected.
16. `build-candidate-dry-run` requires human review.
17. AI-assisted drafts cannot bypass human review.
18. rejected drafts cannot build candidates.
19. every report/preview has `dry_run_only=true`.
20. formal catalog manifest remains unchanged.
21. learner API cannot fetch dry-run candidates.
22. learner API leak regression passes.
23. APP_PROFILE learner/internal gating regression passes.
24. default formal catalog validates.
25. scoring, diagnosis, and movement evals all pass.

## Known Limits

Current limits:

- still dry-run CLI;
- no formal publish/export;
- no diff / backup / rollback;
- no database persistence;
- no authoring UI;
- no real permission or audit system;
- no persistent authoring history;
- no PDF/PPT/OCR import;
- no actual catalog write path;
- no retire/supersede formal chain;
- no full source copyright workflow;
- no semantic leak detection;
- no full symbolic verification;
- no broader Mathematics I catalog expansion.

## Recommended Next Phase

Do not jump directly to frontend, database, mastery/review, LLM, attempt persistence, or broad catalog expansion.

The next phase should be Phase 4.5 Plan only, not implementation.

Candidate planning directions:

- Formal Publish / Export Workflow Plan;
- Attempt Persistence Plan;
- Mastery / Review Model Research;
- Broader Catalog Expansion Plan;
- Frontend Authoring UI Plan.

Any Phase 4.5 scope requires explicit user approval.
