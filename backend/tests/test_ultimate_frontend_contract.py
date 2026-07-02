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
