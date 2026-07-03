# U2C Authoring Graph Focus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Link authoring readiness gates and validation issues to draft preview graph highlights.

**Architecture:** Keep all runtime decision ownership unchanged. The backend already returns draft-only `report`, `readiness`, and `preview`; U2C adds frontend-only focus projection so authoring users can click a gate or issue and see related draft nodes and edges highlighted in the preview graph.

**Tech Stack:** Python contract tests, vanilla JavaScript, CSS.

---

## File Structure

- Modify `backend/tests/test_ultimate_frontend_contract.py`
  - Add a contract test for U2C frontend hooks.
- Modify `frontend/app.js`
  - Change import-report rendering so readiness gates and issue rows carry focus metadata.
  - Add click delegation for `.quality-gate` and `.issue-focus`.
  - Add `focusDraftPreviewGraph()` and helpers to mark related `.draft-preview-node` and `.draft-preview-edge`.
- Modify `frontend/styles.css`
  - Add focused/dimmed states for gates, issues, preview nodes, and preview edges.
- Create `docs/phase_u2c_implementation_report.md`
  - Record scope and verification evidence.

## Task 1: Frontend Contract

**Files:**
- Modify: `backend/tests/test_ultimate_frontend_contract.py`

- [ ] **Step 1: Add failing contract test**

Add this test after `test_frontend_renders_draft_preview_graph`:

```python
def test_frontend_links_authoring_gates_and_issues_to_draft_preview_graph() -> None:
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert "handleImportReportClick" in app_js
    assert "focusDraftPreviewGraph" in app_js
    assert "data-gate-code" in app_js
    assert "data-focus-targets" in app_js
    assert "data-source-id" in app_js
    assert "data-target-id" in app_js
    assert ".draft-preview-node.focused" in styles
    assert ".draft-preview-edge.focused" in styles
    assert ".draft-preview-graph.has-focus" in styles
```

- [ ] **Step 2: Run focused test and verify RED**

Run:

```powershell
python -m pytest backend\tests\test_ultimate_frontend_contract.py::test_frontend_links_authoring_gates_and_issues_to_draft_preview_graph -q
```

Expected: FAIL because U2C hooks do not exist yet.

## Task 2: Gate And Issue Focus Metadata

**Files:**
- Modify: `frontend/app.js`

- [ ] **Step 1: Add import-report click delegation**

In the initialization block where existing import buttons are registered, add:

```javascript
importReport?.addEventListener("click", handleImportReportClick);
```

- [ ] **Step 2: Pass full payload into readiness injection**

Change:

```javascript
injectAuthoringReadiness(payload.readiness);
```

to:

```javascript
injectAuthoringReadiness(payload);
```

Change the function signature:

```javascript
function injectAuthoringReadiness(payload) {
  const readinessHtml = renderAuthoringReadiness(payload?.readiness, payload?.report);
  if (!readinessHtml) return;
  importReport.querySelector(".draft-counts")?.insertAdjacentHTML("afterend", readinessHtml);
}
```

- [ ] **Step 3: Render quality gates as focusable buttons**

Replace the gate item in `renderAuthoringReadiness` with this shape:

```javascript
${checks.map((check) => {
  const targets = focusTargetsForGate(check, report);
  return `
    <button
      type="button"
      class="quality-gate ${escapeHtml(check.state || "unknown")}"
      data-gate-code="${escapeHtml(check.code || "gate")}"
      data-focus-targets="${escapeHtml(targets.join(","))}"
    >
      <strong>${escapeHtml(check.label || check.code || "gate")}</strong>
      <em>${escapeHtml(check.summary || "")}</em>
    </button>
  `;
}).join("")}
```

- [ ] **Step 4: Render issue targets as focus controls**

Change `renderIssueList` item rendering to:

```javascript
${issues.map((issue) => {
  const target = issue.target || "draft";
  return `
    <li>
      <button type="button" class="issue-focus" data-focus-targets="${escapeHtml(target)}">
        ${escapeHtml(target)}
      </button>
      ${escapeHtml(issue.message || "")}
    </li>
  `;
}).join("")}
```

- [ ] **Step 5: Add gate target helper**

Add this function near `renderAuthoringReadiness`:

```javascript
function focusTargetsForGate(check, report) {
  const issues = [...(report?.errors || []), ...(report?.warnings || [])];
  if (check.code === "formal_publish_locked" || check.code === "human_review_required") return [];
  if (check.code === "graph_valid") return uniqueStrings((report?.errors || []).map((issue) => issue.target));
  if (check.code === "visible_budget") {
    return uniqueStrings(issues
      .filter((issue) => /MicroNode|visible|MacroNode/i.test(issue.message || ""))
      .map((issue) => issue.target));
  }
  if (check.code === "repair_targets") {
    return uniqueStrings(issues
      .filter((issue) => /repair|root_cause/i.test(`${issue.target || ""} ${issue.message || ""}`))
      .map((issue) => issue.target));
  }
  return [];
}
```

- [ ] **Step 6: Add shared unique helper**

Add:

```javascript
function uniqueStrings(values) {
  return [...new Set(values.filter(Boolean).map(String))];
}
```

## Task 3: Draft Preview Focus Behavior

**Files:**
- Modify: `frontend/app.js`

- [ ] **Step 1: Add data attributes to graph edges**

In `renderDraftPreviewGraph`, add these attributes to every `<line>`:

```javascript
data-edge-id="${escapeHtml(edge.id || "")}"
data-source-id="${escapeHtml(edge.source_id || "")}"
data-target-id="${escapeHtml(edge.target_id || "")}"
```

- [ ] **Step 2: Add data attributes to graph nodes**

In the node `<span>`, add:

```javascript
data-node-id="${escapeHtml(node.id)}"
```

- [ ] **Step 3: Implement click handler**

Add:

```javascript
function handleImportReportClick(event) {
  const focusControl = event.target.closest("[data-focus-targets]");
  if (!focusControl || !importReport.contains(focusControl)) return;
  const targets = (focusControl.getAttribute("data-focus-targets") || "")
    .split(",")
    .map((target) => target.trim())
    .filter(Boolean);
  focusDraftPreviewGraph(targets, focusControl);
}
```

- [ ] **Step 4: Implement graph focus**

Add:

```javascript
function focusDraftPreviewGraph(targets, activeControl) {
  const targetSet = new Set(targets);
  const graph = importReport.querySelector(".draft-preview-graph");
  if (!graph) return;
  const hasFocus = targetSet.size > 0;
  graph.classList.toggle("has-focus", hasFocus);
  importReport.querySelectorAll(".quality-gate, .issue-focus").forEach((control) => {
    control.classList.toggle("active", control === activeControl && hasFocus);
  });
  graph.querySelectorAll(".draft-preview-node").forEach((node) => {
    const nodeId = node.getAttribute("data-node-id") || "";
    node.classList.toggle("focused", targetSet.has(nodeId));
    node.classList.toggle("dimmed", hasFocus && !targetSet.has(nodeId));
  });
  graph.querySelectorAll(".draft-preview-edge").forEach((edge) => {
    const sourceId = edge.getAttribute("data-source-id") || "";
    const targetId = edge.getAttribute("data-target-id") || "";
    const focused = targetSet.has(sourceId) || targetSet.has(targetId);
    edge.classList.toggle("focused", focused);
    edge.classList.toggle("dimmed", hasFocus && !focused);
  });
}
```

## Task 4: Focus Styles

**Files:**
- Modify: `frontend/styles.css`

- [ ] **Step 1: Make gates and issue targets interactive**

Add:

```css
.quality-gate {
  appearance: none;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.quality-gate.active,
.issue-focus.active {
  outline: 2px solid rgba(127, 241, 231, 0.42);
  outline-offset: 2px;
}

.issue-focus {
  appearance: none;
  border: 1px solid rgba(210, 231, 255, 0.16);
  background: rgba(255, 255, 255, 0.045);
  color: var(--muted);
  border-radius: 8px;
  padding: 4px 7px;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}
```

- [ ] **Step 2: Add graph focus states**

Add:

```css
.draft-preview-graph.has-focus .draft-preview-node.dimmed {
  opacity: 0.36;
}

.draft-preview-graph.has-focus .draft-preview-edge.dimmed {
  opacity: 0.16;
}

.draft-preview-node.focused {
  border-color: rgba(127, 241, 231, 0.72);
  box-shadow:
    0 0 0 2px rgba(127, 241, 231, 0.18),
    0 14px 34px rgba(0, 0, 0, 0.32);
}

.draft-preview-edge.focused {
  stroke: rgba(127, 241, 231, 0.78);
  stroke-width: 0.85;
}
```

## Task 5: Verification And Report

**Files:**
- Create: `docs/phase_u2c_implementation_report.md`

- [ ] **Step 1: Run focused checks**

Run:

```powershell
python -m pytest backend\tests\test_ultimate_frontend_contract.py backend\tests\test_ultimate_atlas_and_chapter_import.py -q
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --check frontend\app.js
```

Expected:

```text
frontend and atlas/import tests pass
node syntax check exits 0
```

- [ ] **Step 2: Browser verify**

Open:

```text
http://127.0.0.1:8000/trainer/
```

Validate a draft in the import panel, then verify:

- readiness gates are clickable.
- issue target chips are clickable when errors/warnings exist.
- clicking a gate with targets adds `.has-focus` to `.draft-preview-graph`.
- related nodes receive `.focused`.
- unrelated nodes receive `.dimmed`.
- related edges receive `.focused`.

- [ ] **Step 3: Run full checks**

Run:

```powershell
python -m pytest -q
python evals\run_evals.py
python evals\run_synthetic_diagnosis_lab.py
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' diff --check
```

Expected:

```text
all tests and evals pass
diff check exits 0
```

- [ ] **Step 4: Write implementation report**

Create `docs/phase_u2c_implementation_report.md` with scope, delivered items, and verification output.

- [ ] **Step 5: Commit and push**

Run:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' add backend\tests\test_ultimate_frontend_contract.py frontend\app.js frontend\styles.css docs\phase_u2c_implementation_report.md docs\superpowers\plans\2026-07-03-u2c-authoring-graph-focus.md
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' commit -m "feat: link authoring report to draft graph"
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' push
```
