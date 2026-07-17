# U2D Structured Authoring Issues Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make chapter draft validation issues structured, stable, and useful for human review, frontend graph focus, and assistant repair workflows.

**Architecture:** Keep the draft importer as the source of truth for issue objects. Preserve legacy `target` and `message` fields while adding `code`, `severity`, `target_kind`, and `suggested_fix`. The frontend renders these fields as compact authoring metadata and keeps the existing U2C focus behavior.

**Tech Stack:** Python draft importer and pytest backend tests; vanilla JavaScript frontend and static contract tests; existing local browser verification.

---

## File Structure

- Modify: `backend/app/challenge/chapter_draft_importer.py`
  - Upgrade `_issue()` to return structured issue dictionaries.
  - Add deterministic issue profile classification.
  - Mark warning call sites with `severity="warning"`.
  - Let readiness repair-target checks prefer issue code when present.
- Modify: `backend/tests/test_ultimate_atlas_and_chapter_import.py`
  - Add backend contract tests for structured error and warning issues.
- Modify: `backend/tests/test_ultimate_frontend_contract.py`
  - Add static contract expectations for issue code, severity, kind, suggested fix, and existing focus controls.
- Modify: `frontend/app.js`
  - Render structured issue metadata.
  - Keep fallback rendering for legacy issue objects.
- Modify: `frontend/styles.css`
  - Add compact styling for structured issue metadata.
- Create: `docs/phase_u2d_implementation_report.md`
  - Record scope, files changed, tests, browser verification, and exclusions.

---

### Task 1: Backend Structured Error Contract

**Files:**
- Modify: `backend/tests/test_ultimate_atlas_and_chapter_import.py`
- Modify: `backend/app/challenge/chapter_draft_importer.py`

- [ ] **Step 1: Write the failing backend error contract test**

Add this test to `backend/tests/test_ultimate_atlas_and_chapter_import.py`:

```python
def test_markdown_chapter_import_returns_structured_error_issues():
    markdown = VALID_CHAPTER_MARKDOWN.replace(
        "| method_error | import_demo.macro.method |",
        "| method_error | import_demo.unknown_method |",
    )

    payload = validate_chapter_markdown(markdown)

    issues_by_code = {issue["code"]: issue for issue in payload["report"]["errors"]}
    issue = issues_by_code["invalid_repair_target"]
    assert issue["target"] == "method_error"
    assert issue["severity"] == "error"
    assert issue["target_kind"] == "error_repair_map"
    assert issue["message"]
    assert issue["suggested_fix"]
```

- [ ] **Step 2: Run the new test and verify RED**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py::test_markdown_chapter_import_returns_structured_error_issues -q
```

Expected: FAIL because existing issues do not contain `code`.

- [ ] **Step 3: Implement structured `_issue()`**

Replace the current `_issue()` helper with a helper that returns all contract
fields while preserving `target` and `message`:

```python
    @classmethod
    def _issue(
        cls,
        target: str,
        message: str,
        *,
        severity: str = "error",
        code: str | None = None,
        target_kind: str | None = None,
        suggested_fix: str | None = None,
    ) -> dict[str, str]:
        profile = cls._issue_profile(target, message, severity)
        return {
            "target": target,
            "message": message,
            "code": code or profile["code"],
            "severity": severity,
            "target_kind": target_kind or profile["target_kind"],
            "suggested_fix": suggested_fix or profile["suggested_fix"],
        }
```

Add `_issue_profile()` below it with deterministic classification based on
target, message text, and severity.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py::test_markdown_chapter_import_returns_structured_error_issues -q
```

Expected: PASS.

---

### Task 2: Backend Warning Contract

**Files:**
- Modify: `backend/tests/test_ultimate_atlas_and_chapter_import.py`
- Modify: `backend/app/challenge/chapter_draft_importer.py`

- [ ] **Step 1: Write the failing backend warning contract test**

Add this test:

```python
def test_markdown_chapter_import_returns_structured_warning_issues():
    markdown = VALID_CHAPTER_MARKDOWN.replace(
        "| e5 | contrasts_with | import_demo.compare.concept_vs_method | import_demo.macro.concept | contrast edge |",
        "",
    )

    payload = validate_chapter_markdown(markdown)

    issue = payload["report"]["warnings"][0]
    assert issue["severity"] == "warning"
    assert issue["code"] == "orphan_logic_node"
    assert issue["target_kind"] == "logic_edges"
    assert issue["target"] == "logic_edges"
    assert issue["suggested_fix"]
```

- [ ] **Step 2: Run the new warning test and verify RED**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py::test_markdown_chapter_import_returns_structured_warning_issues -q
```

Expected: FAIL because warnings currently inherit no structured severity.

- [ ] **Step 3: Mark warning call sites**

Update each warning append in `chapter_draft_importer.py` to call:

```python
self._issue(target, message, severity="warning")
```

The warning call sites are missing edge reason, visible node budget warning, and
orphan logic node warning.

- [ ] **Step 4: Run backend focused tests and verify GREEN**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py::test_markdown_chapter_import_returns_structured_error_issues backend/tests/test_ultimate_atlas_and_chapter_import.py::test_markdown_chapter_import_returns_structured_warning_issues -q
```

Expected: PASS.

---

### Task 3: Frontend Structured Issue Rendering

**Files:**
- Modify: `backend/tests/test_ultimate_frontend_contract.py`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`

- [ ] **Step 1: Write the failing frontend contract test**

Add a static contract test that asserts the frontend knows about:

```python
def test_frontend_renders_structured_authoring_issues():
    assert "issue-code" in APP_JS
    assert "issue-severity" in APP_JS
    assert "issue-kind" in APP_JS
    assert "suggested_fix" in APP_JS
    assert "suggested-fix" in STYLES_CSS
    assert "issue-focus" in APP_JS
```

- [ ] **Step 2: Run the frontend contract test and verify RED**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_frontend_contract.py::test_frontend_renders_structured_authoring_issues -q
```

Expected: FAIL because the frontend still renders only target and message.

- [ ] **Step 3: Render structured issue metadata**

Update `renderIssueList()` to:

- read `issue.code || "draft_issue"`.
- read `issue.severity || "issue"`.
- read `issue.target_kind || "draft"`.
- read `issue.suggested_fix || ""`.
- render target as the existing `.issue-focus` button.
- render code, severity, kind, message, and suggested fix inside the list item.

- [ ] **Step 4: Add CSS for compact metadata**

Add styles for `.issue-item`, `.issue-copy`, `.issue-severity`, `.issue-code`,
`.issue-kind`, and `.suggested-fix`.

- [ ] **Step 5: Run the frontend contract test and verify GREEN**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_frontend_contract.py::test_frontend_renders_structured_authoring_issues -q
```

Expected: PASS.

---

### Task 4: Readiness Compatibility and Regression

**Files:**
- Modify: `backend/app/challenge/chapter_draft_importer.py`

- [ ] **Step 1: Prefer issue code in repair readiness**

Update the repair readiness filter to treat these codes as repair blocking:

```python
{"invalid_repair_target", "missing_repair_map", "invalid_root_cause"}
```

Keep the old message fallback so legacy payloads still work.

- [ ] **Step 2: Run focused U2 backend tests**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_atlas_and_chapter_import.py backend/tests/test_ultimate_frontend_contract.py -q
```

Expected: PASS.

---

### Task 5: Verification and Report

**Files:**
- Create: `docs/phase_u2d_implementation_report.md`

- [ ] **Step 1: Run full regression**

Run:

```powershell
python -m pytest backend/tests -q
python evals/run_evals.py
python evals/run_synthetic_diagnosis_lab.py
C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --check frontend/app.js
```

Expected: all pass.

- [ ] **Step 2: Browser verify import report**

Start or reuse the local app, open `http://127.0.0.1:8000/trainer/`, validate a
bad draft, and verify:

- issue code is visible.
- severity is visible.
- suggested fix is visible.
- clicking the issue target still focuses the draft preview graph.

- [ ] **Step 3: Write U2D implementation report**

Create `docs/phase_u2d_implementation_report.md` with:

- implemented scope.
- changed files.
- issue contract fields.
- verification evidence.
- explicit non-goals.

- [ ] **Step 4: Commit and push**

Run:

```powershell
git add backend/app/challenge/chapter_draft_importer.py backend/tests/test_ultimate_atlas_and_chapter_import.py backend/tests/test_ultimate_frontend_contract.py frontend/app.js frontend/styles.css docs/superpowers/specs/2026-07-03-u2d-structured-authoring-issues-design.md docs/superpowers/plans/2026-07-03-u2d-structured-authoring-issues.md docs/phase_u2d_implementation_report.md
git commit -m "feat: structure authoring validation issues"
git push origin ultimate-ode-proof-slice
```

Expected: branch pushed to GitHub.
