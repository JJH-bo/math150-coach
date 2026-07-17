# Work Handoff

Status: Ready
Owner: ChatGPT + Codex
Last updated: 2026-07-03

This file is the active work handoff area between ChatGPT and Codex.

## Handoff Acceptance Gate

Future ChatGPT-to-Codex handoffs must satisfy
`docs/ai_coordination/CODEX_HANDOFF_ACCEPTANCE_STANDARD.md`.

Codex should reject new handoffs that only ask Codex to implement work without
ChatGPT's concrete upstream development results, or that do not directly upgrade
a major final-version project block.

## Current Active Task

## Task: U2F Chapter Draft Candidate Build Dry-Run

Status: Ready for Codex
Owner: Codex
Created by: ChatGPT review recovery via Codex
Date: 2026-07-03

### Goal

Add an authoring-only candidate build dry-run for structured chapter Markdown drafts. The dry-run must generate a deterministic content hash for the approved chapter graph candidate while keeping formal publish locked.

### Background

U2D added structured authoring issue metadata. U2E added non-persistent human review records and a candidate-build gate. The next maturity step is U2F: when validation passes and human review approves, the system should produce a dry-run candidate artifact with a content hash.

This is not formal publishing. It is a reviewable preview artifact that proves the draft can become a stable runtime-shaped graph candidate later.

### Required Changes

Backend:

- Add a deterministic chapter candidate dry-run builder in the challenge authoring area.
- Add a request schema for candidate dry-run build.
- Add `POST /api/challenge/v1/authoring/chapter-draft/candidate-build-dry-run`.
- Require:
  - Markdown draft validation passes.
  - Human review record exists in the request.
  - Human review status is `approved_for_candidate`.
  - Human review checklist has no missing required codes.
- Return:
  - `mode: "chapter_draft_candidate_build_dry_run"`
  - `workflow_stage: "candidate_build_dry_run"`
  - `publish_state: "draft_only"`
  - `dry_run_only: true`
  - `candidate_build_allowed: true`
  - `formal_publish_allowed: false`
  - `content_hash: "sha256:<64 lowercase hex>"`
  - runtime-shaped candidate payload for the challenge graph draft and logic graph draft
  - review provenance snapshot
  - validation report snapshot
- Block and explain:
  - validation errors;
  - missing review record;
  - incomplete review checklist;
  - `request_changes`;
  - any attempt to treat dry-run as formal publish.

Frontend:

- After a successful human review approval, render a "Build dry-run candidate" action.
- Submit Markdown and review record to the new endpoint.
- Render dry-run result:
  - content hash;
  - dry-run-only label;
  - formal publish locked label;
  - candidate counts / graph summary.
- Do not expose trusted scoring fields or formal publish controls.

Docs:

- Add `docs/phase_u2f_implementation_report.md`.
- Record the dry-run hash contract and formal publish boundary.

### Files Likely Involved

- `backend/app/challenge/chapter_draft_importer.py`
- `backend/app/api/challenge/v1/schemas.py`
- `backend/app/api/challenge/v1/router.py`
- `backend/tests/test_ultimate_atlas_and_chapter_import.py`
- `backend/tests/test_ultimate_frontend_contract.py`
- `frontend/app.js`
- `frontend/styles.css`
- `docs/phase_u2f_implementation_report.md`

Optional if useful:

- a small helper module under `backend/app/challenge/` for content hashing, but do not introduce a broad abstraction unless it reduces real complexity.

### Non-Goals

- Do not write the formal runtime graph repository.
- Do not write the formal catalog.
- Do not add database persistence.
- Do not add auth.
- Do not add LLM integration.
- Do not add new chapter content.
- Do not change scoring, diagnosis, rollback, forward movement, or `ChallengeEngine`.
- Do not reuse question-catalog candidate build code blindly; chapter graph candidates need a graph-specific dry-run payload.

### Verification

Required commands:

```bash
python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py backend/tests/test_ultimate_frontend_contract.py -q
python -m pytest backend/tests -q
python evals/run_evals.py
python evals/run_synthetic_diagnosis_lab.py
C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --check frontend/app.js
```

Browser verification:

- Open `http://127.0.0.1:8000/trainer/`.
- Validate a passing structured draft.
- Complete human review approval.
- Build dry-run candidate.
- Confirm content hash is visible.
- Confirm dry-run-only and formal-publish-locked labels are visible.
- Confirm no mobile overflow in the dry-run result area.

### Acceptance Criteria

- Candidate dry-run endpoint rejects invalid drafts.
- Candidate dry-run endpoint rejects missing or incomplete review records.
- Candidate dry-run endpoint accepts complete `approved_for_candidate` review records.
- Returned content hash is deterministic for the same runtime candidate payload.
- Hash excludes `content_hash`, review notes, reviewer identity, and authoring-only metadata.
- Response remains dry-run only.
- Formal publish remains false/locked in every path.
- Frontend displays dry-run result without turning into a formal publish UI.

### Risks / Watchpoints

- The existing catalog authoring hash utilities are for question records. Reuse only the hashing idea or a shared canonical JSON pattern, not the catalog candidate model.
- U2E review records are non-persistent. U2F must receive review provenance in the request and revalidate the Markdown, not trust stale frontend state.
- A candidate-shaped payload can look like publish readiness. Labels and response fields must keep dry-run boundaries explicit.
- Do not let the frontend decide candidate eligibility; it only submits and renders backend decisions.

### Codex Report Required

Use `CODEX_REPORT_TEMPLATE.md`.

## How To Use

When ChatGPT prepares a task for Codex, replace or append an entry using this format:

```md
## Task: <short title>

Status: Ready for Codex / In Progress / Implemented / Under Review / Frozen / Rejected
Owner: Codex
Created by: ChatGPT
Date:

### Goal

### Background

### Required Changes

### Files Likely Involved

### Non-Goals

### Verification

### Acceptance Criteria

### Risks / Watchpoints

### Codex Report Required
Use `CODEX_REPORT_TEMPLATE.md`.
```

## Previous Recommendation

This section is superseded by the active U2F task above. It is retained only as
historical context from the initial coordination workspace setup.
