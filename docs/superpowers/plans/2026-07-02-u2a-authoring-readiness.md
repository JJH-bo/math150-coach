# U2A Authoring Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a draft-only authoring readiness projection so future chapter expansion can be reviewed through clear quality gates before any publish workflow exists.

**Architecture:** Keep `ChapterDraftImporter` as the owner of structured Markdown validation and preview projection. Add a learner-safe, draft-only `workflow_stage` and `readiness` object to its response, then render that projection in the existing import modal. Do not write runtime chapter data, formal catalog files, scoring logic, diagnosis logic, movement logic, database state, auth state, or LLM integration.

**Tech Stack:** Python, FastAPI, pytest, vanilla HTML/CSS/JavaScript.

---

## Task 1: Backend Authoring Readiness Projection

**Files:**
- Modify: `backend/app/challenge/chapter_draft_importer.py`
- Modify: `backend/tests/test_ultimate_atlas_and_chapter_import.py`

- [x] **Step 1: Write failing readiness tests**

Add tests that require `validate_chapter_markdown()` and the authoring API to return:

```python
payload["workflow_stage"] == "draft_preview"
payload["readiness"]["status"] in {"blocked", "review_ready"}
payload["readiness"]["publish_allowed"] is False
payload["readiness"]["checks"]
```

For the valid fixture, assert status is `review_ready` and checks include `graph_valid`, `visible_budget`, `repair_targets`, `human_review_required`, and `formal_publish_locked`.

For an invalid fixture, assert status is `blocked`, `blocking_error_count` is greater than zero, and no formal publish is allowed.

- [x] **Step 2: Run the focused backend tests and verify they fail**

Run:

```powershell
python -m pytest backend\tests\test_ultimate_atlas_and_chapter_import.py -q
```

Expected: FAIL because `workflow_stage` and `readiness` do not exist.

- [x] **Step 3: Implement readiness projection**

Add `_readiness(draft, report, preview)` to `ChapterDraftImporter`. It should derive quality-gate checks from the existing report and preview only. It must not mutate draft data or publish anything.

Required check codes:

- `graph_valid`
- `visible_budget`
- `repair_targets`
- `human_review_required`
- `formal_publish_locked`

Required top-level readiness fields:

- `status`
- `publish_allowed`
- `blocking_error_count`
- `warning_count`
- `checks`
- `next_action`

- [x] **Step 4: Run backend tests and verify green**

Run:

```powershell
python -m pytest backend\tests\test_ultimate_atlas_and_chapter_import.py -q
```

Expected: all tests pass.

## Task 2: Frontend Authoring Readiness Display

**Files:**
- Modify: `backend/tests/test_ultimate_frontend_contract.py`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`

- [x] **Step 1: Write failing frontend contract test**

Add a test requiring:

```python
assert "renderAuthoringReadiness" in app_js
assert "authoring-readiness" in app_js
assert "quality-gate-list" in app_js
assert ".authoring-readiness" in styles
assert ".quality-gate-list" in styles
```

- [x] **Step 2: Run the focused frontend test and verify it fails**

Run:

```powershell
python -m pytest backend\tests\test_ultimate_frontend_contract.py::test_frontend_renders_authoring_readiness_projection -q
```

Expected: FAIL because the frontend does not render readiness yet.

- [x] **Step 3: Render readiness in import modal**

In `renderImportReport(payload)`, render readiness after the draft counts and before errors/warnings. The display should show status, next action, and each quality gate. It must stay display-only.

- [x] **Step 4: Add styles**

Add compact, readable styles for `.authoring-readiness` and `.quality-gate-list`, with pass/warn/fail/locked gate tones.

- [x] **Step 5: Run frontend checks**

Run:

```powershell
python -m pytest backend\tests\test_ultimate_frontend_contract.py -q
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --check frontend\app.js
```

Expected: tests pass and JS syntax check exits 0.

## Task 3: Verification And Commit

**Files:**
- Modify: `docs\phase_u1_implementation_report.md` or create a U2A report if needed.

- [x] **Step 1: Run focused tests**

Run:

```powershell
python -m pytest backend\tests\test_ultimate_atlas_and_chapter_import.py backend\tests\test_ultimate_frontend_contract.py -q
```

Expected: all selected tests pass.

- [x] **Step 2: Run full verification**

Run:

```powershell
python -m pytest -q
python evals\run_evals.py
python evals\run_synthetic_diagnosis_lab.py
```

Expected: all pass with no scoring, diagnosis, or movement regressions.

- [x] **Step 3: Commit**

Run:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' add backend\app\challenge\chapter_draft_importer.py backend\tests\test_ultimate_atlas_and_chapter_import.py backend\tests\test_ultimate_frontend_contract.py frontend\app.js frontend\styles.css docs\superpowers\plans\2026-07-02-u2a-authoring-readiness.md
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' commit -m "feat: add authoring readiness projection"
```
