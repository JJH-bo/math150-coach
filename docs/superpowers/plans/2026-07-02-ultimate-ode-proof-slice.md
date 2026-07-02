# Ultimate ODE Proof Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build Phase U1 of the ultimate blueprint by proving the multi-subject cosmic experience and strict diagnostic display on the existing `ode_network_mvp` slice, without adding new chapter content.

**Architecture:** Keep the current backend ownership boundaries intact: scoring stays in `CompositeScoringEngine`, diagnosis stays in `DiagnosisEngine`, movement stays in `RollbackEngine` / `ForwardEngine`, and challenge state stays in `ChallengeEngine`. Add learner-safe quality and visual projection data to the challenge API, then upgrade the existing static frontend to render a stronger cosmic atlas, chapter map, training pod, and diagnostic verdict.

**Tech Stack:** Python, FastAPI, Pydantic, pytest, YAML-backed challenge data, vanilla HTML/CSS/JavaScript frontend served at `/trainer/`.

---

## Scope Boundary

This plan implements `Phase U1: ODE Proof Slice` from `docs/superpowers/specs/2026-07-02-ultimate-knowledge-universe-design.md`.

It intentionally does not:

- add concrete chapter content;
- publish authoring drafts;
- add database persistence;
- add authentication;
- connect a real LLM;
- write formal catalog entries;
- make frontend/API decide rollback or forward movement.

The current workspace may not be a Git repository. Before each commit step, run:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' rev-parse --is-inside-work-tree
```

If it exits non-zero, record the changed files in the task notes and skip the commit command.

## File Structure

- `backend/app/api/challenge/v1/router.py`: add a learner-safe runtime graph-quality endpoint.
- `backend/app/challenge/atlas.py`: enrich the atlas payload with visual grammar and chapter-nebula projection fields while keeping it lightweight.
- `backend/tests/test_ultimate_u1_runtime_contract.py`: new backend contract tests for runtime quality and visual grammar.
- `backend/tests/test_ultimate_frontend_contract.py`: extend static frontend contract tests for U1 UI hooks.
- `frontend/index.html`: add a graph quality HUD region.
- `frontend/app.js`: fetch runtime quality, render quality summary, use atlas visual roles, and render a diagnostic verdict block.
- `frontend/styles.css`: add cosmic visual grammar, graph quality HUD, diagnostic verdict, repair beacon, and responsive polishing.
- `README.md`: add a short Phase U1 run/verify note after implementation.
- `docs/phase_u1_implementation_report.md`: record what U1 changed and what remains out of scope.

## Task 1: Runtime Graph Quality Endpoint

**Files:**
- Create: `backend/tests/test_ultimate_u1_runtime_contract.py`
- Modify: `backend/app/api/challenge/v1/router.py`

- [ ] **Step 1: Write the failing runtime quality endpoint test**

Create `backend/tests/test_ultimate_u1_runtime_contract.py` with:

```python
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import create_app
from app.training.session_log import ensure_no_trusted_fields


def test_runtime_quality_report_endpoint_is_read_only_and_learner_safe() -> None:
    client = TestClient(create_app("mixed"))

    response = client.get("/api/challenge/v1/quality/ode_network_mvp")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "runtime_graph_quality"
    assert payload["publish_state"] == "read_only"
    assert payload["chapter_id"] == "ode_network_mvp"
    assert payload["report"]["passed"] is True
    assert payload["report"]["error_count"] == 0
    assert isinstance(payload["report"]["issues"], list)
    text = json.dumps(payload, ensure_ascii=False)
    assert "logic_overlay" not in text
    assert "current_question" not in text
    assert "expected_answer" not in text
    assert "solution_outline" not in text
    ensure_no_trusted_fields(payload)
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run:

```powershell
cd C:\Users\jjh\OneDrive\文档\数学闯关\math150-coach
python -m pytest backend/tests/test_ultimate_u1_runtime_contract.py::test_runtime_quality_report_endpoint_is_read_only_and_learner_safe -q
```

Expected: FAIL with HTTP 404 because `/api/challenge/v1/quality/ode_network_mvp` is not implemented.

- [ ] **Step 3: Add the endpoint imports**

Modify the imports in `backend/app/api/challenge/v1/router.py`:

```python
from app.logic_graph.quality_validator import KnowledgeGraphQualityValidator
from app.logic_graph.repository import LogicGraphRepository
```

- [ ] **Step 4: Add the runtime quality endpoint**

Add this endpoint below `challenge_atlas()` in `backend/app/api/challenge/v1/router.py`:

```python
@router.get("/quality/{chapter_id}")
def challenge_quality(chapter_id: str) -> dict[str, Any]:
    try:
        graph = ChallengeEngine().repository.load_graph(chapter_id)
        logic_graph = LogicGraphRepository().try_load_graph(chapter_id)
        report = KnowledgeGraphQualityValidator().validate(graph, logic_graph)
        return {
            "mode": "runtime_graph_quality",
            "publish_state": "read_only",
            "chapter_id": graph.chapter_id,
            "report": report.model_dump(mode="json"),
        }
    except ChallengeRepositoryError as exc:
        raise api_error(400, "challenge_error", str(exc))
```

- [ ] **Step 5: Run the focused test and verify it passes**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_u1_runtime_contract.py::test_runtime_quality_report_endpoint_is_read_only_and_learner_safe -q
```

Expected: PASS.

- [ ] **Step 6: Commit or record changed files**

If inside a Git repository:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' add backend/app/api/challenge/v1/router.py backend/tests/test_ultimate_u1_runtime_contract.py
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' commit -m "feat: expose runtime graph quality report"
```

If not inside a Git repository, record these changed files in `docs/phase_u1_implementation_report.md` during Task 7.

## Task 2: Atlas Visual Grammar Projection

**Files:**
- Modify: `backend/app/challenge/atlas.py`
- Modify: `backend/tests/test_ultimate_u1_runtime_contract.py`

- [ ] **Step 1: Add the failing atlas visual grammar test**

Append to `backend/tests/test_ultimate_u1_runtime_contract.py`:

```python
def test_atlas_exposes_cosmic_visual_grammar_without_detail_graph() -> None:
    client = TestClient(create_app("mixed"))

    response = client.get("/api/challenge/v1/atlas")

    assert response.status_code == 200
    payload = response.json()
    assert payload["visual_grammar"]["subject_role"] == "subject_galaxy"
    assert payload["visual_grammar"]["chapter_role"] == "chapter_nebula"
    assert payload["visual_grammar"]["detail_role"] == "knowledge_constellation"
    region = payload["regions"][0]
    assert region["visual_role"]["celestial_role"] == "chapter_nebula"
    assert region["visual_role"]["primary_tone"] in {"cyan", "gold", "green"}
    assert region["visual_role"]["detail_entry"] == "lazy_drilldown"
    text = json.dumps(payload, ensure_ascii=False)
    assert "logic_overlay" not in text
    assert "current_question" not in text
    ensure_no_trusted_fields(payload)
```

- [ ] **Step 2: Run the atlas test and verify it fails**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_u1_runtime_contract.py::test_atlas_exposes_cosmic_visual_grammar_without_detail_graph -q
```

Expected: FAIL with missing `visual_grammar`.

- [ ] **Step 3: Add atlas-level visual grammar**

Modify the return payload in `backend/app/challenge/atlas.py`:

```python
        return {
            "atlas_version": "course_atlas_v1",
            "title": "Math150 Coach 课程星图",
            "visual_grammar": {
                "subject_role": "subject_galaxy",
                "chapter_role": "chapter_nebula",
                "detail_role": "knowledge_constellation",
                "edge_role": "light_language",
                "pod_role": "diagnostic_dock",
            },
            "render_policy": {
                "default_layer": "chapter_summary",
                "detail_loading": "lazy",
                "do_not_embed_detail_graph": True,
            },
            "regions": regions,
            "bridges": self._bridges(regions),
            "warnings": warnings,
        }
```

- [ ] **Step 4: Add region visual roles**

Inside the region dict in `backend/app/challenge/atlas.py`, add this field after `position`:

```python
                    "visual_role": {
                        "celestial_role": "chapter_nebula",
                        "primary_tone": self._tone_for_index(index),
                        "density": self._density_label(macro_count, micro_count),
                        "detail_entry": "lazy_drilldown",
                    },
```

Add these static methods to `ChallengeAtlasBuilder`:

```python
    @staticmethod
    def _tone_for_index(index: int) -> str:
        return ["cyan", "gold", "green"][index % 3]

    @staticmethod
    def _density_label(macro_count: int, micro_count: int) -> str:
        if macro_count >= 6 or micro_count >= 36:
            return "dense"
        if macro_count >= 3 or micro_count >= 18:
            return "medium"
        return "light"
```

- [ ] **Step 5: Run the atlas test and verify it passes**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_u1_runtime_contract.py::test_atlas_exposes_cosmic_visual_grammar_without_detail_graph -q
```

Expected: PASS.

- [ ] **Step 6: Commit or record changed files**

If inside a Git repository:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' add backend/app/challenge/atlas.py backend/tests/test_ultimate_u1_runtime_contract.py
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' commit -m "feat: add cosmic atlas visual grammar"
```

If not inside a Git repository, record these changed files in `docs/phase_u1_implementation_report.md` during Task 7.

## Task 3: Runtime Quality HUD In The Trainer

**Files:**
- Modify: `backend/tests/test_ultimate_frontend_contract.py`
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`

- [ ] **Step 1: Add the failing frontend quality HUD contract test**

Append to `backend/tests/test_ultimate_frontend_contract.py`:

```python
def test_frontend_fetches_and_renders_runtime_quality_summary() -> None:
    index_html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert 'id="qualitySummary"' in index_html
    assert "/quality/" in app_js
    assert "loadRuntimeQuality" in app_js
    assert "renderQualitySummary" in app_js
    assert ".quality-summary" in styles
```

- [ ] **Step 2: Run the frontend contract test and verify it fails**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_frontend_contract.py::test_frontend_fetches_and_renders_runtime_quality_summary -q
```

Expected: FAIL because `qualitySummary` does not exist.

- [ ] **Step 3: Add the quality HUD container**

Modify `frontend/index.html`. Place this after `<div id="overallStats" class="stats-grid"></div>`:

```html
        <div id="qualitySummary" class="quality-summary" aria-live="polite"></div>
```

- [ ] **Step 4: Add frontend quality state and selector**

In `frontend/app.js`, add this selector near the other DOM selectors:

```javascript
const qualitySummary = document.querySelector("#qualitySummary");
```

Add this state variable near `let atlasPayload = null;`:

```javascript
let qualityPayload = null;
```

- [ ] **Step 5: Fetch quality after challenge render**

In `frontend/app.js`, inside `render(payload, options = {})`, after `renderStats(challenge);`, add:

```javascript
  if (qualityPayload?.chapter_id === challenge.chapter_id) {
    renderQualitySummary(qualityPayload);
  } else {
    loadRuntimeQuality(challenge.chapter_id).catch(() => renderQualitySummary(null));
  }
```

- [ ] **Step 6: Add quality fetch and render functions**

Add these functions in `frontend/app.js` after `renderStats(challenge)`:

```javascript
async function loadRuntimeQuality(chapterId) {
  if (!chapterId) return null;
  const payload = await request(`/quality/${encodeURIComponent(chapterId)}`);
  qualityPayload = payload;
  renderQualitySummary(payload);
  return payload;
}

function renderQualitySummary(payload) {
  if (!qualitySummary) return;
  if (!payload?.report) {
    qualitySummary.innerHTML = `
      <span class="quality-dot unknown"></span>
      <span>图谱质量暂不可用</span>
    `;
    return;
  }
  const report = payload.report;
  const passed = Boolean(report.passed);
  const warnings = Number(report.warning_count || 0);
  const errors = Number(report.error_count || 0);
  const tone = passed ? (warnings ? "warn" : "pass") : "fail";
  const label = passed
    ? (warnings ? `${warnings} 个质量提醒` : "图谱质量通过")
    : `${errors} 个阻断问题`;
  qualitySummary.innerHTML = `
    <span class="quality-dot ${tone}"></span>
    <span>${escapeHtml(label)}</span>
  `;
}
```

- [ ] **Step 7: Add quality HUD styles**

Add to `frontend/styles.css` near the HUD styles:

```css
.quality-summary {
  min-height: 40px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
  padding: 0 12px;
  border: 1px solid rgba(210, 231, 255, 0.16);
  border-radius: 8px;
  background: rgba(8, 13, 24, 0.66);
  color: rgba(232, 243, 255, 0.84);
  white-space: nowrap;
}

.quality-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(141, 154, 172, 0.8);
  box-shadow: 0 0 16px rgba(141, 154, 172, 0.24);
}

.quality-dot.pass {
  background: var(--green);
  box-shadow: 0 0 18px rgba(104, 224, 180, 0.36);
}

.quality-dot.warn {
  background: var(--gold);
  box-shadow: 0 0 18px rgba(255, 210, 122, 0.36);
}

.quality-dot.fail {
  background: var(--red);
  box-shadow: 0 0 18px rgba(255, 124, 134, 0.36);
}
```

- [ ] **Step 8: Run the frontend contract test and verify it passes**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_frontend_contract.py::test_frontend_fetches_and_renders_runtime_quality_summary -q
```

Expected: PASS.

- [ ] **Step 9: Commit or record changed files**

If inside a Git repository:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' add backend/tests/test_ultimate_frontend_contract.py frontend/index.html frontend/app.js frontend/styles.css
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' commit -m "feat: show runtime graph quality in trainer"
```

If not inside a Git repository, record these changed files in `docs/phase_u1_implementation_report.md` during Task 7.

## Task 4: Cosmic Atlas And Light-Language Styling

**Files:**
- Modify: `backend/tests/test_ultimate_frontend_contract.py`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`

- [ ] **Step 1: Add the failing cosmic visual contract test**

Append to `backend/tests/test_ultimate_frontend_contract.py`:

```python
def test_frontend_uses_cosmic_visual_language_hooks() -> None:
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert "visual_role" in app_js
    assert "visualClassForRegion" in app_js
    assert "cosmic-subject-galaxy" in styles
    assert "chapter-nebula" in styles
    assert "light-language" in styles
    assert "repair-beam" in styles
```

- [ ] **Step 2: Run the cosmic visual contract test and verify it fails**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_frontend_contract.py::test_frontend_uses_cosmic_visual_language_hooks -q
```

Expected: FAIL because the new visual hooks do not exist.

- [ ] **Step 3: Use region visual role classes**

Modify `renderAtlasRegion(region)` in `frontend/app.js`. Replace the `class` attribute with:

```javascript
      class="atlas-region chapter-nebula ${visualClassForRegion(region)} ${region.id === currentChapterId ? "selected" : ""}"
```

Add this attribute under `data-chapter-id`:

```javascript
      data-celestial-role="${escapeHtml(region.visual_role?.celestial_role || "chapter_nebula")}"
```

- [ ] **Step 4: Add the visual class helper**

Add this function after `atlasRegionMeta(region)` in `frontend/app.js`:

```javascript
function visualClassForRegion(region) {
  const role = region.visual_role || {};
  const tone = role.primary_tone || "cyan";
  const density = role.density || "medium";
  return `tone-${tone} density-${density}`;
}
```

- [ ] **Step 5: Add light-language classes to rendered edges**

Modify `svgEdgeAttrs(from, to)` in `frontend/app.js` so it remains the owner of source and target IDs. Then update edge rendering call sites to include semantic classes:

```javascript
lines.push(svgOrbitCurve(source, target, `logic_edge light-language ${edge.edge_type}${active ? " active" : ""}`));
```

For repair edges, add this conditional where logic edges are rendered:

```javascript
const repairClass = edge.edge_type === "repairs" ? " repair-beam" : "";
lines.push(svgOrbitCurve(source, target, `logic_edge light-language ${edge.edge_type}${repairClass}${active ? " active" : ""}`));
```

- [ ] **Step 6: Add cosmic visual CSS**

Add to `frontend/styles.css` near atlas styles:

```css
.atlas-layer::before,
.map-viewport::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    radial-gradient(circle, rgba(255, 255, 255, 0.48) 0 1px, transparent 1.5px),
    radial-gradient(circle, rgba(127, 241, 231, 0.28) 0 1px, transparent 1.4px);
  background-size: 84px 84px, 137px 137px;
  opacity: 0.18;
}

.cosmic-subject-galaxy {
  border: 1px solid rgba(127, 241, 231, 0.22);
  box-shadow: inset 0 0 42px rgba(127, 241, 231, 0.08), 0 0 58px rgba(118, 199, 255, 0.12);
}

.atlas-region.chapter-nebula {
  border-radius: 42% 58% 52% 48%;
}

.atlas-region.tone-cyan {
  --region-tone: var(--cyan);
}

.atlas-region.tone-gold {
  --region-tone: var(--gold);
}

.atlas-region.tone-green {
  --region-tone: var(--green);
}

.atlas-region.density-dense .atlas-region-ring {
  opacity: 0.82;
}

.atlas-region.density-light .atlas-region-ring {
  opacity: 0.38;
}

.edge.light-language {
  stroke-linecap: round;
  filter: drop-shadow(0 0 8px rgba(118, 199, 255, 0.2));
}

.edge.repair-beam {
  stroke: rgba(255, 124, 134, 0.68);
  filter: drop-shadow(0 0 10px rgba(255, 124, 134, 0.28));
}
```

- [ ] **Step 7: Run the cosmic visual contract test and verify it passes**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_frontend_contract.py::test_frontend_uses_cosmic_visual_language_hooks -q
```

Expected: PASS.

- [ ] **Step 8: Commit or record changed files**

If inside a Git repository:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' add backend/tests/test_ultimate_frontend_contract.py frontend/app.js frontend/styles.css
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' commit -m "feat: add cosmic atlas visual language"
```

If not inside a Git repository, record these changed files in `docs/phase_u1_implementation_report.md` during Task 7.

## Task 5: Diagnostic Verdict And Repair Beacon

**Files:**
- Modify: `backend/tests/test_ultimate_frontend_contract.py`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`

- [ ] **Step 1: Add the failing diagnostic verdict contract test**

Append to `backend/tests/test_ultimate_frontend_contract.py`:

```python
def test_frontend_renders_diagnostic_verdict_and_repair_beacon() -> None:
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert "renderDiagnosticVerdict" in app_js
    assert "diagnostic-verdict" in app_js
    assert "repair-target-beacon" in app_js
    assert ".diagnostic-verdict" in styles
    assert ".repair-target-beacon" in styles
```

- [ ] **Step 2: Run the diagnostic verdict test and verify it fails**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_frontend_contract.py::test_frontend_renders_diagnostic_verdict_and_repair_beacon -q
```

Expected: FAIL because the diagnostic verdict hook does not exist.

- [ ] **Step 3: Insert diagnostic verdict into coach output**

In `frontend/app.js`, inside `renderCoach(payload)`, add this line immediately after the first coach summary block:

```javascript
    ${renderDiagnosticVerdict(payload)}
```

The resulting start of `coachView.innerHTML` should be:

```javascript
  coachView.innerHTML = `
    <section class="coach-block ${tone}">
      <strong>${escapeHtml(statusText(passState))}</strong>
      <p>${escapeHtml(payload.coach_summary || payload.learner_explanation || "已收到本次作答。")}</p>
    </section>
    ${renderDiagnosticVerdict(payload)}
    ${renderAbilityState(payload)}
    ${renderLogicInsight(payload.logic_insight)}
```

- [ ] **Step 4: Add the diagnostic verdict function**

Add this function before `renderAbilityState(payload)` in `frontend/app.js`:

```javascript
function renderDiagnosticVerdict(payload) {
  const attempt = payload.challenge_attempt || {};
  const insight = payload.logic_insight || {};
  const root = attempt.root_cause || payload.root_cause;
  const repairTarget = insight.primary_target_node_id || attempt.repair_target_node_id;
  if (!root && !repairTarget && !payload.progression_advice && !payload.next_step_plan) return "";
  const rootLabel = root ? (errorLabels[root] || root) : "证据不足";
  const repairHtml = repairTarget
    ? `<span class="repair-target-beacon">修复目标：${escapeHtml(logicNodeTitle(payload.challenge, repairTarget))}</span>`
    : `<span class="repair-target-beacon muted">等待更多证据</span>`;
  return `
    <section class="coach-block diagnostic-verdict">
      <div class="diagnostic-verdict-head">
        <strong>根因裁决：${escapeHtml(rootLabel)}</strong>
        ${repairHtml}
      </div>
      <p>${escapeHtml(payload.progression_advice || "系统会优先收集足够证据，再决定是否推进。")}</p>
      <p>${escapeHtml(payload.next_step_plan || "补充步骤和自我说明，可以让诊断更可靠。")}</p>
    </section>
  `;
}
```

- [ ] **Step 5: Add diagnostic verdict styles**

Add to `frontend/styles.css` near coach styles:

```css
.diagnostic-verdict {
  border-color: rgba(255, 210, 122, 0.28);
  background:
    radial-gradient(circle at 12% 0%, rgba(255, 210, 122, 0.14), transparent 42%),
    rgba(255, 210, 122, 0.06);
}

.diagnostic-verdict-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.repair-target-beacon {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 10px;
  border: 1px solid rgba(255, 124, 134, 0.34);
  border-radius: 999px;
  background: rgba(255, 124, 134, 0.1);
  color: rgba(255, 226, 230, 0.96);
  box-shadow: 0 0 22px rgba(255, 124, 134, 0.12);
}

.repair-target-beacon.muted {
  border-color: rgba(210, 231, 255, 0.16);
  background: rgba(210, 231, 255, 0.06);
  color: rgba(226, 238, 255, 0.7);
  box-shadow: none;
}
```

- [ ] **Step 6: Run the diagnostic verdict test and verify it passes**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_frontend_contract.py::test_frontend_renders_diagnostic_verdict_and_repair_beacon -q
```

Expected: PASS.

- [ ] **Step 7: Commit or record changed files**

If inside a Git repository:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' add backend/tests/test_ultimate_frontend_contract.py frontend/app.js frontend/styles.css
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' commit -m "feat: improve diagnostic verdict display"
```

If not inside a Git repository, record these changed files in `docs/phase_u1_implementation_report.md` during Task 7.

## Task 6: Browser Verification Pass

**Files:**
- Modify: `docs/phase_u1_implementation_report.md`

- [ ] **Step 1: Start the local trainer**

Run:

```powershell
cd C:\Users\jjh\OneDrive\文档\数学闯关\math150-coach
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Expected: server starts and serves `/trainer/`.

If port 8000 is occupied, use:

```powershell
python -m uvicorn app.main:app --app-dir backend --reload --port 8001
```

- [ ] **Step 2: Verify the learner surface in browser**

Open:

```text
http://127.0.0.1:8000/trainer/
```

or, if using port 8001:

```text
http://127.0.0.1:8001/trainer/
```

Expected:

- start screen loads;
- atlas preview loads;
- entering chapter loads the ODE network;
- quality summary appears in the HUD;
- node click opens the bottom training pod;
- node count does not grow after repeated selections;
- diagnostic verdict appears after submit;
- map remains readable with pod open.

- [ ] **Step 3: Run a 30-click smoke check manually**

In the browser console, run:

```javascript
const before = document.querySelectorAll(".map-node").length;
for (const node of [...document.querySelectorAll(".map-node")].slice(0, 30)) {
  node.click();
}
const after = document.querySelectorAll(".map-node").length;
console.log({ before, after, stable: before === after });
```

Expected: `stable: true`.

- [ ] **Step 4: Record browser verification results**

Create or update `docs/phase_u1_implementation_report.md` with:

```markdown
# Phase U1 Implementation Report

Status: browser verification recorded.

## Browser Verification

- Trainer URL: record the exact URL used, normally `http://127.0.0.1:8000/trainer/`.
- Atlas loaded: record `PASS` or `FAIL` plus one sentence of evidence.
- Chapter graph loaded: record `PASS` or `FAIL` plus the visible chapter title.
- Runtime quality HUD visible: record `PASS` or `FAIL` plus the displayed label.
- Node click opens training pod: record `PASS` or `FAIL` plus the clicked node id.
- 30-click node count stable: record the console object, for example `{ before: 42, after: 42, stable: true }`.
- Diagnostic verdict visible after submit: record `PASS` or `FAIL` plus the verdict label.
- Mobile viewport checked: record viewport size and `PASS` or `FAIL`.

## Changed Files

- `backend/app/api/challenge/v1/router.py`
- `backend/app/challenge/atlas.py`
- `backend/tests/test_ultimate_u1_runtime_contract.py`
- `backend/tests/test_ultimate_frontend_contract.py`
- `frontend/index.html`
- `frontend/app.js`
- `frontend/styles.css`
```

- [ ] **Step 5: Stop the local server**

Stop the foreground server with `Ctrl+C`. If a hidden process was used, stop that specific process only.

## Task 7: Full Verification And Report

**Files:**
- Modify: `README.md`
- Create/Modify: `docs/phase_u1_implementation_report.md`

- [ ] **Step 1: Add a short README note**

In `README.md`, add a short section after the browser trainer instructions:

```markdown
## Phase U1 Ultimate ODE Proof Slice

Phase U1 keeps the runtime content on the current `ode_network_mvp` slice while improving the ultimate architecture proof: runtime graph quality projection, cosmic atlas visual grammar, quality HUD, and diagnostic verdict display. It does not add new chapter content, publish authoring drafts, add a database, connect a real LLM, or change scoring/diagnosis/movement ownership.
```

- [ ] **Step 2: Run focused backend and frontend tests**

Run:

```powershell
python -m pytest backend/tests/test_ultimate_u1_runtime_contract.py backend/tests/test_ultimate_frontend_contract.py backend/tests/test_ultimate_atlas_and_chapter_import.py -q
```

Expected: all selected tests pass.

- [ ] **Step 3: Run the full pytest suite**

Run:

```powershell
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 4: Run golden evals**

Run:

```powershell
python evals/run_evals.py
```

Expected:

```text
Scoring 30/30 passed
Diagnosis 25/25 passed
Movement 12/12 passed
```

If the exact counts changed because new eval cases were intentionally added, record the new counts and why in `docs/phase_u1_implementation_report.md`.

- [ ] **Step 5: Run synthetic diagnosis lab**

Run:

```powershell
python evals/run_synthetic_diagnosis_lab.py
```

Expected:

```text
Synthetic diagnosis lab 16/16 passed
```

If the exact count changed because new synthetic cases were intentionally added, record the new count and why in `docs/phase_u1_implementation_report.md`.

- [ ] **Step 6: Final report update**

Update `docs/phase_u1_implementation_report.md` with:

```markdown
## Verification

- Focused pytest: record exact command and observed pass/fail output.
- Full pytest: record exact command and observed pass/fail output.
- Golden evals: record exact command and scoring/diagnosis/movement counts.
- Synthetic diagnosis lab: record exact command and pass count.
- Browser verification: record trainer URL and the 30-click stability object.

## Boundary Confirmation

- No concrete chapter content added: record `CONFIRMED` or list file paths that changed content.
- No formal catalog publish: record `CONFIRMED` or list catalog files touched.
- No database/auth/LLM added: record `CONFIRMED` or list introduced dependencies.
- Scoring ownership unchanged: record `CONFIRMED` or list changed scoring files.
- Diagnosis ownership unchanged: record `CONFIRMED` or list changed diagnosis files.
- Rollback/forward ownership unchanged: record `CONFIRMED` or list changed movement files.
- Frontend/API did not become decision engines: record `CONFIRMED` and cite the changed frontend/API behavior.
```

- [ ] **Step 7: Commit or record changed files**

If inside a Git repository:

```powershell
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' add README.md docs/phase_u1_implementation_report.md
& 'C:\Users\jjh\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe' commit -m "docs: record phase u1 verification"
```

If not inside a Git repository, leave the implementation report as the source of changed-file and verification evidence.

## Final Verification Checklist

Before claiming Phase U1 complete, verify:

- [ ] `python -m pytest backend/tests/test_ultimate_u1_runtime_contract.py backend/tests/test_ultimate_frontend_contract.py backend/tests/test_ultimate_atlas_and_chapter_import.py -q` passes.
- [ ] `python -m pytest -q` passes.
- [ ] `python evals/run_evals.py` passes.
- [ ] `python evals/run_synthetic_diagnosis_lab.py` passes.
- [ ] Browser trainer loads at `/trainer/`.
- [ ] Runtime quality HUD is visible.
- [ ] Atlas visual grammar is visible and lightweight.
- [ ] Node click does not rebuild the graph.
- [ ] Diagnostic verdict and repair beacon appear after submit.
- [ ] No trusted fields are exposed in learner-visible payloads.
- [ ] `docs/phase_u1_implementation_report.md` records verification evidence.
