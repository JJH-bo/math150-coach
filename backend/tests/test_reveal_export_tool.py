from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

import pytest
from PIL import Image, ImageStat
from pypdf import PdfReader

from app.tools.adapters.reveal_export import RevealExportAdapter, RevealExportError
from app.tools.contracts import ToolExecutionContext
from test_semantic_lesson import lesson_payload


def require_runtime() -> None:
    if not (os.getenv("MODEL_PREVIEW_NODE") or shutil.which("node")):
        pytest.skip("Node runtime is unavailable")
    if not os.getenv("NODE_PATH"):
        pytest.skip("NODE_PATH is unavailable")


def execute(tmp_path: Path, arguments: dict):
    require_runtime()
    return RevealExportAdapter().execute(
        arguments,
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def visible_text_x_positions(pdf_path: Path, page_index: int) -> list[float]:
    positions: list[float] = []

    def collect(text, current_matrix, text_matrix, _font, _font_size) -> None:
        if not text.strip() or text.strip().isdigit():
            return
        positions.append(
            current_matrix[0] * text_matrix[4]
            + current_matrix[2] * text_matrix[5]
            + current_matrix[4]
        )

    PdfReader(pdf_path).pages[page_index].extract_text(visitor_text=collect)
    return positions


def test_definition_is_verified_reveal_export() -> None:
    definition = RevealExportAdapter().definition

    assert definition.tool_id == "export.reveal"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.render"
    assert definition.input_schema["title"] == "SemanticLesson"


def test_reveal_export_is_self_contained_rendered_and_printable(
    tmp_path: Path,
) -> None:
    output = execute(tmp_path, lesson_payload())

    assert output.result["slide_count"] == 4
    assert output.result["render_report"]["passed"] is True
    assert output.result["render_report"]["failed_requests"] == []
    assert output.result["render_report"]["console_errors"] == []
    assert output.result["render_report"]["overflow_findings"] == []
    assert output.result["render_report"]["minimum_font_sizes"] == {
        "deck_title": 50,
        "slide_title": 35,
        "subheading": 24,
        "body": 16,
    }
    names = [artifact.name for artifact in output.artifacts]
    assert names == [
        "lesson-spec.json",
        "lesson.html",
        "lesson.pdf",
        "render-report.json",
        "slide-001.png",
        "slide-002.png",
        "slide-003.png",
        "slide-004.png",
    ]
    html = (tmp_path / "lesson.html").read_text(encoding="utf-8")
    assert "class=\"reveal\"" in html
    assert "Reveal.initialize" in html
    assert re.search(r"<(?:script|link)[^>]+(?:src|href)=\"https?://", html) is None
    assert "<svg" in html
    assert "aria-label" in html
    pdf_path = tmp_path / "lesson.pdf"
    assert len(PdfReader(pdf_path).pages) == 4
    for page_index in range(4):
        positions = visible_text_x_positions(pdf_path, page_index)
        assert positions
        assert min(positions) >= 36  # half-inch safe area on the 72-point PDF grid
    for index in range(1, 5):
        with Image.open(tmp_path / f"slide-{index:03d}.png") as image:
            assert image.size == (1280, 720)
            assert sum(ImageStat.Stat(image.convert("RGB")).var) > 1


def test_reveal_result_uses_the_normalized_lesson_hash(tmp_path: Path) -> None:
    first = execute(tmp_path / "first", lesson_payload())
    changed = lesson_payload()
    changed["slides"][1]["primary_claim"] = (
        "The output tolerance fixes a concrete requirement for the input distance."
    )
    second = execute(tmp_path / "second", changed)

    assert first.result["content_hash"].startswith("sha256:")
    assert first.result["content_hash"] != second.result["content_hash"]


def test_worker_failure_is_bounded_and_does_not_expose_environment(
    tmp_path: Path, monkeypatch
) -> None:
    require_runtime()
    monkeypatch.setenv("MODEL_PREVIEW_BROWSER", str(tmp_path / "missing-browser"))

    with pytest.raises(RevealExportError) as caught:
        RevealExportAdapter().execute(
            lesson_payload(),
            ToolExecutionContext(
                job_id="tj-000000000000000000000000",
                work_dir=tmp_path,
            ),
        )

    message = str(caught.value)
    assert "render" in message.lower()
    assert "STUDIO_API_KEY" not in message
    assert len(message) <= 4000
