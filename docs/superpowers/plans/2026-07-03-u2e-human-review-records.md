# U2E Human Review Records Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add authoring-only human review records for chapter drafts without persistence, candidate builds, or formal publishing.

**Architecture:** Extend the existing chapter draft importer with a deterministic human review packet and review-record builder. Add one challenge authoring endpoint for review submission. Render a small frontend review panel inside the import modal after validation.

**Tech Stack:** Python, FastAPI, Pydantic, pytest, vanilla JavaScript, CSS.

---

## File Structure

- Modify: `backend/app/challenge/chapter_draft_importer.py`
  - Add `HUMAN_REVIEW_CHECKS`.
  - Add `record_chapter_human_review()`.
  - Add `_human_review_packet()` and `_human_review_record()`.
- Modify: `backend/app/api/challenge/v1/schemas.py`
  - Add `ChapterDraftHumanReviewRequest`.
- Modify: `backend/app/api/challenge/v1/router.py`
  - Add `POST /authoring/chapter-draft/human-review`.
- Modify: `backend/tests/test_ultimate_atlas_and_chapter_import.py`
  - Add backend review packet, review block, review allow, and API tests.
- Modify: `backend/tests/test_ultimate_frontend_contract.py`
  - Add frontend human review panel static contract test.
- Modify: `frontend/app.js`
  - Render review panel and submit review records.
- Modify: `frontend/styles.css`
  - Add compact review panel styles.
- Create: `docs/phase_u2e_implementation_report.md`

---

### Task 1: Backend Validation Human Review Packet

- [ ] **Step 1: Write failing test**

Add:

```python
def test_chapter_draft_validation_returns_human_review_packet() -> None:
    payload = validate_chapter_markdown(VALID_CHAPTER_MARKDOWN)

    review = payload["human_review"]
    assert review["required"] is True
    assert review["status"] == "pending"
    assert review["candidate_build_allowed"] is False
    assert review["formal_publish_allowed"] is False
    assert {item["code"] for item in review["required_checklist"]} >= {
        "math_scope_checked",
        "macro_micro_structure_checked",
        "repair_targets_checked",
        "hidden_abilities_checked",
        "semantic_edges_checked",
        "boss_coverage_checked",
        "learner_surface_safe",
    }
```

- [ ] **Step 2: Run RED**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py::test_chapter_draft_validation_returns_human_review_packet -q
```

Expected: FAIL because validation output has no `human_review`.

- [ ] **Step 3: Implement packet**

Add `HUMAN_REVIEW_CHECKS` and include `human_review` in `validate()`.

- [ ] **Step 4: Run GREEN**

Run the same test and expect PASS.

---

### Task 2: Backend Review Record Rules

- [ ] **Step 1: Write failing tests**

Add tests for:

- validation errors block `approve_for_candidate`.
- complete checklist allows candidate build only in review response.
- formal publish is always false.

- [ ] **Step 2: Run RED**

Run the new tests and expect missing function/import failures.

- [ ] **Step 3: Implement `record_chapter_human_review()`**

Rules:

- validation errors -> `status: blocked_by_validation`, candidate false.
- incomplete checklist -> `status: review_incomplete`, candidate false.
- `request_changes` -> `status: changes_requested`, candidate false.
- complete approve -> `status: approved_for_candidate`, candidate true.
- formal publish always false.

- [ ] **Step 4: Run GREEN**

Run the backend U2 tests and expect PASS.

---

### Task 3: API Endpoint

- [ ] **Step 1: Write failing API test**

Post to `/api/challenge/v1/authoring/chapter-draft/human-review` with valid
Markdown, reviewer, `approve_for_candidate`, and a complete checklist.

Expected fields:

- `workflow_stage == "human_review"`
- `candidate_build_allowed is True`
- `formal_publish_allowed is False`

- [ ] **Step 2: Run RED**

Expected: 404 or schema missing.

- [ ] **Step 3: Add request schema and route**

Use Pydantic with `extra="forbid"`.

- [ ] **Step 4: Run GREEN**

Run the API test and expect PASS.

---

### Task 4: Frontend Review Panel

- [ ] **Step 1: Write failing contract test**

Add assertions for:

- `/authoring/chapter-draft/human-review`
- `renderHumanReviewPanel`
- `submitHumanReviewRecord`
- `human-review-panel`
- `review-check`
- `candidate_build_allowed`

- [ ] **Step 2: Run RED**

Expected: FAIL because the frontend has no review panel.

- [ ] **Step 3: Implement frontend panel**

Render after validation:

- reviewer input.
- checklist checkboxes from `human_review.required_checklist`.
- notes textarea.
- request changes button.
- approve for candidate button.
- result area.

- [ ] **Step 4: Add styles**

Add `.human-review-panel`, `.review-check`, `.review-actions`, and
`.human-review-result`.

- [ ] **Step 5: Run GREEN**

Run frontend contract test and U2 focused tests.

---

### Task 5: Verification and Commit

- [ ] **Step 1: Run verification**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py backend/tests/test_ultimate_frontend_contract.py -q
python -m pytest backend/tests -q
python evals/run_evals.py
python evals/run_synthetic_diagnosis_lab.py
C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --check frontend/app.js
```

- [ ] **Step 2: Browser verify**

Open `http://127.0.0.1:8000/trainer/`, validate a draft, complete the human
review checklist, submit approve, and verify candidate build is allowed while
formal publish remains locked.

- [ ] **Step 3: Write report**

Create `docs/phase_u2e_implementation_report.md`.

- [ ] **Step 4: Commit and push**

Commit:

```powershell
git commit -m "feat: add chapter draft human review records"
git push origin ultimate-ode-proof-slice
```
