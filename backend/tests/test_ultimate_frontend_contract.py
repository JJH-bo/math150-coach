from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_node_selection_does_not_rerender_whole_graph() -> None:
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    body = _function_body(app_js, "selectMapNode")

    assert "refreshGraphSelection(lastPayload.challenge)" in body
    assert "renderNodePanel(lastPayload.challenge, lastPayload)" in body
    assert "renderGraph(" not in body
    assert "data-source-id" in app_js
    assert "data-target-id" in app_js


def test_frontend_has_atlas_and_chapter_import_entrypoints() -> None:
    index_html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

    assert 'id="atlasLayer"' in index_html
    assert 'id="importModal"' in index_html
    assert "/atlas" in app_js
    assert "/authoring/chapter-draft/validate" in app_js
    assert "publish_state" in app_js


def test_styles_pause_motion_when_node_sheet_is_open() -> None:
    styles = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert ".map-world.motion-budget" in styles
    assert "animation-play-state: paused" in styles
    assert ".map-world.sheet-open .edge:not(.active)" in styles
    assert ".node-modal.is-open" in styles
    assert re.search(r"\.node-modal\.is-open\s*\{[^}]*backdrop-filter:\s*none", styles, re.DOTALL)


def test_frontend_fetches_and_renders_runtime_quality_summary() -> None:
    index_html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert 'id="qualitySummary"' in index_html
    assert "/quality/" in app_js
    assert "loadRuntimeQuality" in app_js
    assert "renderQualitySummary" in app_js
    assert ".quality-summary" in styles


def test_frontend_uses_cosmic_visual_language_hooks() -> None:
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert "visual_role" in app_js
    assert "visualClassForRegion" in app_js
    assert "cosmic-subject-galaxy" in styles
    assert "chapter-nebula" in styles
    assert "light-language" in styles
    assert "repair-beam" in styles


def test_frontend_renders_diagnostic_verdict_and_repair_beacon() -> None:
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert "renderDiagnosticVerdict" in app_js
    assert "diagnostic-verdict" in app_js
    assert "repair-target-beacon" in app_js
    assert ".diagnostic-verdict" in styles
    assert ".repair-target-beacon" in styles


def test_frontend_renders_authoring_readiness_projection() -> None:
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert "renderAuthoringReadiness" in app_js
    assert "authoring-readiness" in app_js
    assert "quality-gate-list" in app_js
    assert ".authoring-readiness" in styles
    assert ".quality-gate-list" in styles


def test_frontend_renders_draft_preview_graph() -> None:
    app_js = (ROOT / "frontend" / "app.js").read_text(encoding="utf-8")
    styles = (ROOT / "frontend" / "styles.css").read_text(encoding="utf-8")

    assert "renderDraftPreviewGraph" in app_js
    assert "draft-preview-graph" in app_js
    assert "draft-preview-node" in app_js
    assert "draft-preview-edge" in app_js
    assert ".draft-preview-graph" in styles
    assert ".draft-preview-node" in styles
    assert ".draft-preview-edge" in styles


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


def _function_body(source: str, name: str) -> str:
    match = re.search(rf"function {name}\([^)]*\) \{{", source)
    assert match is not None
    start = match.end()
    depth = 1
    index = start
    while index < len(source) and depth:
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
        index += 1
    return source[start : index - 1]
