# Phase U2D Implementation Report

Date: 2026-07-03

## Scope

U2D upgrades chapter draft validation issues into structured authoring feedback.
It keeps the existing `target` and `message` fields and adds:

- `code`
- `severity`
- `target_kind`
- `suggested_fix`

This makes draft validation output usable by human reviewers, the draft preview
graph focus layer, and assistant repair workflows without parsing free-form
messages.

## Changed Files

- `backend/app/challenge/chapter_draft_importer.py`
  - Structured `_issue()` output.
  - Deterministic issue profile classification.
  - Warning severity at existing warning call sites.
  - Readiness repair checks now prefer stable repair issue codes while keeping
    legacy message fallback.
- `backend/tests/test_ultimate_atlas_and_chapter_import.py`
  - Added structured error issue contract test.
  - Added structured warning issue contract test.
- `backend/tests/test_ultimate_frontend_contract.py`
  - Added frontend static contract test for structured issue rendering.
- `frontend/app.js`
  - Renders issue severity, code, target kind, message, suggested fix, and the
    existing focus target button.
- `frontend/styles.css`
  - Adds compact metadata styling for structured authoring issues.
- `docs/superpowers/specs/2026-07-03-u2d-structured-authoring-issues-design.md`
  - U2D design spec.
- `docs/superpowers/plans/2026-07-03-u2d-structured-authoring-issues.md`
  - U2D implementation plan.

## Verification

- TDD RED:
  - `test_markdown_chapter_import_returns_structured_error_issues` failed on
    missing `code`.
  - `test_markdown_chapter_import_returns_structured_warning_issues` failed on
    missing `severity`.
  - `test_markdown_chapter_import_marks_visible_budget_warning_as_macro_target`
    failed before the visible budget warning was classified ahead of generic
    MicroNode/MacroNode reference rules.
  - `test_frontend_renders_structured_authoring_issues` failed on missing
    frontend rendering hooks.
- Focused U2 tests:
  - `python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py backend/tests/test_ultimate_frontend_contract.py -q`
  - Observed `19 passed`.
- Full backend regression:
  - `python -m pytest backend/tests -q`
  - Observed `549 passed`.
- Golden evals:
  - `python evals/run_evals.py`
  - Observed scoring `30/30`, diagnosis `25/25`, movement `12/12`.
- Synthetic diagnosis lab:
  - `python evals/run_synthetic_diagnosis_lab.py`
  - Observed `16/16 passed`.
- JavaScript syntax:
  - `C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --check frontend/app.js`
  - Observed exit code `0`.
- Browser verification:
  - Opened `http://127.0.0.1:8000/trainer/`.
  - Validated a draft with missing HiddenAbility `evidence_sources`.
  - Observed issue code `missing_evidence_sources`.
  - Observed severity `error`.
  - Observed target kind `logic_nodes`.
  - Observed suggested fix text.
  - Clicked target `import_demo.hidden.concept_reason`.
  - Observed the matching draft preview node focused and one related edge
    focused.
  - Checked mobile width `390x844`; structured issue item did not overflow and
    target button did not overlap issue copy.

## Non-Goals

U2D does not add chapter content, formal publishing, automatic repair, human
review storage, candidate builds, content hashes, persistence, auth, deployment,
LLM integration, or runtime scoring and diagnosis changes.
