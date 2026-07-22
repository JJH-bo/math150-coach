from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pytest
from PIL import Image, ImageStat

from app.tools.adapters.pptx_export import PptxExportAdapter, PptxExportError
from app.tools.contracts import ToolExecutionContext
from test_semantic_lesson import lesson_payload


DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def require_runtime() -> None:
    if not (os.getenv("MODEL_PREVIEW_NODE") or shutil.which("node")):
        pytest.skip("Node runtime is unavailable")
    if not os.getenv("NODE_PATH"):
        pytest.skip("NODE_PATH is unavailable")


def execute(tmp_path: Path, arguments: dict):
    require_runtime()
    return PptxExportAdapter().execute(
        arguments,
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def xml_text(payload: bytes) -> str:
    root = ElementTree.fromstring(payload)
    return " ".join(
        (node.text or "").strip()
        for node in root.iter(f"{{{DRAWING_NS}}}t")
        if (node.text or "").strip()
    )


def test_definition_is_verified_editable_pptx_export() -> None:
    definition = PptxExportAdapter().definition

    assert definition.tool_id == "export.pptx"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.render"
    assert definition.input_schema["title"] == "SemanticLesson"


def test_pptx_export_is_editable_noted_rendered_and_validated(tmp_path: Path) -> None:
    payload = lesson_payload()
    output = execute(tmp_path, payload)

    assert output.result["slide_count"] == 4
    assert output.result["layout_report"]["passed"] is True
    assert output.result["layout_report"]["overflow_findings"] == []
    assert output.result["layout_report"]["overlap_findings"] == []
    assert output.result["ooxml_report"]["passed"] is True
    assert output.result["ooxml_report"]["editable_text_shape_count"] >= 12
    assert output.result["ooxml_report"]["speaker_notes_count"] == 4
    assert output.result["ooxml_report"]["formula_svg_valid_count"] == 2
    assert output.result["ooxml_report"]["minimum_font_sizes"] == {
        "deck_title": 50,
        "slide_title": 35,
        "subheading": 24,
        "body": 16,
    }

    names = [artifact.name for artifact in output.artifacts]
    assert names == [
        "lesson-spec.json",
        "lesson.pptx",
        "layout-report.json",
        "ooxml-report.json",
        "montage.png",
        "slide-001.png",
        "slide-002.png",
        "slide-003.png",
        "slide-004.png",
    ]

    pptx_path = tmp_path / "lesson.pptx"
    with zipfile.ZipFile(pptx_path) as archive:
        parts = set(archive.namelist())
        slide_parts = sorted(
            name
            for name in parts
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        )
        notes_parts = sorted(
            name
            for name in parts
            if name.startswith("ppt/notesSlides/notesSlide")
            and name.endswith(".xml")
        )
        assert len(slide_parts) == 4
        assert len(notes_parts) == 4
        formula_parts = sorted(
            name
            for name in parts
            if name.startswith("ppt/media/") and name.endswith(".svg")
        )
        assert len(formula_parts) == 2
        formula_payloads = [
            archive.read(name).decode("utf-8") for name in formula_parts
        ]
        assert all(payload.lstrip().startswith("<svg") for payload in formula_payloads)
        assert all("<mjx-container" not in payload for payload in formula_payloads)
        assert all("data-latex" not in payload for payload in formula_payloads)
        assert all(ElementTree.fromstring(payload) is not None for payload in formula_payloads)
        assert all("#E5EBF3" in payload for payload in formula_payloads)
        slide_text = " ".join(xml_text(archive.read(name)) for name in slide_parts)
        note_text = " ".join(xml_text(archive.read(name)) for name in notes_parts)
        for slide in payload["slides"]:
            assert slide["title"] in slide_text
            assert slide["primary_claim"] in slide_text
            assert slide["speaker_notes"] in note_text
        core = archive.read("docProps/core.xml").decode("utf-8")
        assert output.result["content_hash"] in core

    with Image.open(tmp_path / "montage.png") as montage:
        assert montage.width == 1280
        assert montage.height == 720
        assert sum(ImageStat.Stat(montage.convert("RGB")).var) > 1
    for index in range(1, 5):
        with Image.open(tmp_path / f"slide-{index:03d}.png") as image:
            assert image.size == (1280, 720)
            assert sum(ImageStat.Stat(image.convert("RGB")).var) > 1


def test_pptx_content_hash_changes_with_lesson_content(tmp_path: Path) -> None:
    first = execute(tmp_path / "first", lesson_payload())
    changed = lesson_payload()
    changed["slides"][2]["primary_claim"] = (
        "For the same line, epsilon fixes a direct half-sized delta choice."
    )
    second = execute(tmp_path / "second", changed)

    assert first.result["content_hash"].startswith("sha256:")
    assert first.result["content_hash"] != second.result["content_hash"]


def test_pptx_worker_failure_is_bounded_and_hides_environment(
    tmp_path: Path, monkeypatch
) -> None:
    require_runtime()
    monkeypatch.setenv("MODEL_PREVIEW_BROWSER", str(tmp_path / "missing-browser"))

    with pytest.raises(PptxExportError) as caught:
        PptxExportAdapter().execute(
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
