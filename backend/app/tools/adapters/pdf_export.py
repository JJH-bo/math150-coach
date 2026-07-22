from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat
from pypdf import PdfReader, PdfWriter

from app.tools.adapters.reveal_export import RevealExportAdapter
from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolProducedArtifact,
    ToolQualityTier,
    ToolScope,
)
from app.tools.lesson_contracts import SemanticLesson
from app.tools.lesson_validation import normalize_lesson


class PdfExportError(ValueError):
    pass


def normalized_extracted_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def normalize_pdf_metadata(path: Path, title: str, content_hash: str) -> None:
    reader = PdfReader(path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata(
        {
            "/Title": title,
            "/Author": "Math150 Coach",
            "/Subject": content_hash,
            "/Creator": "Math150 Coach verified lesson exporter",
            "/Producer": "pypdf",
            "/CreationDate": "D:20000101000000Z",
            "/ModDate": "D:20000101000000Z",
        }
    )
    temporary = path.with_suffix(".normalized.pdf")
    with temporary.open("wb") as stream:
        writer.write(stream)
    temporary.replace(path)


class PdfExportAdapter:
    definition = ToolDefinition(
        tool_id="export.pdf",
        version="1.0.0",
        title="Verified fixed-layout lesson PDF export",
        description=(
            "Create a print-ready lesson PDF with deterministic metadata, "
            "extractable audience-facing text, per-page PNG evidence, and a "
            "page-level validation report."
        ),
        category="export",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.RENDER,
        execution_mode=ToolExecutionMode.ASYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=120,
        max_artifacts=40,
        max_artifact_bytes=256 * 1024 * 1024,
        input_schema=SemanticLesson.model_json_schema(),
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["schema_version", "content_hash", "slide_count", "pdf_report"],
            "properties": {
                "schema_version": {"type": "string"},
                "content_hash": {"type": "string"},
                "slide_count": {"type": "integer"},
                "pdf_report": {"type": "object"},
            },
        },
        output_media_types=["application/json", "application/pdf", "image/png"],
        quality_gates=[
            "semantic_lesson_contract",
            "pdf_page_count_matches_slides",
            "audience_text_extractable",
            "deterministic_pdf_metadata",
            "nonblank_page_pixels",
        ],
        upstream_project="https://playwright.dev/ and https://pypdf.readthedocs.io/",
        license="Apache-2.0 and BSD-3-Clause",
    )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        lesson = normalize_lesson(arguments)
        reveal = RevealExportAdapter().execute(arguments, context)
        content_hash = reveal.result["content_hash"]
        pdf_path = context.work_dir / "lesson.pdf"
        normalize_pdf_metadata(pdf_path, lesson.title, content_hash)
        reader = PdfReader(pdf_path)
        missing_text: list[dict[str, str]] = []
        extracted_characters = 0
        for index, (page, slide) in enumerate(zip(reader.pages, lesson.slides, strict=True)):
            text = page.extract_text() or ""
            extracted_characters += len(text)
            searchable = normalized_extracted_text(text)
            for field, expected in (("title", slide.title), ("primary_claim", slide.primary_claim)):
                if normalized_extracted_text(expected) not in searchable:
                    missing_text.append(
                        {"slide_id": slide.slide_id, "field": field, "page": str(index + 1)}
                    )
        if len(reader.pages) != len(lesson.slides):
            raise PdfExportError("PDF page count does not match the semantic lesson")
        page_paths: list[Path] = []
        for index in range(1, len(lesson.slides) + 1):
            source = context.work_dir / f"slide-{index:03d}.png"
            destination = context.work_dir / f"page-{index:03d}.png"
            shutil.copyfile(source, destination)
            self._validate_png(destination)
            page_paths.append(destination)
        report = {
            "passed": not missing_text,
            "page_count": len(reader.pages),
            "extracted_character_count": extracted_characters,
            "missing_text": missing_text,
            "metadata": {
                "title": reader.metadata.title,
                "author": reader.metadata.author,
                "subject": reader.metadata.subject,
            },
            "source_render_report": reveal.result["render_report"],
        }
        report_path = context.work_dir / "pdf-report.json"
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        if not report["passed"]:
            raise PdfExportError("PDF text extraction quality report did not pass")
        paths = [context.work_dir / "lesson-spec.json", pdf_path, report_path, *page_paths]
        media_types = {".json": "application/json", ".pdf": "application/pdf", ".png": "image/png"}
        return ToolExecutionResult(
            result={
                "schema_version": lesson.schema_version,
                "content_hash": content_hash,
                "slide_count": len(lesson.slides),
                "pdf_report": report,
            },
            artifacts=[
                ToolProducedArtifact(
                    name=path.name,
                    media_type=media_types[path.suffix],
                    source_path=path.name,
                )
                for path in paths
            ],
            metrics={
                "page_count": len(reader.pages),
                "pdf_bytes": pdf_path.stat().st_size,
                "extracted_character_count": extracted_characters,
            },
        )

    @staticmethod
    def _validate_png(path: Path) -> None:
        with Image.open(path) as image:
            if image.size != (1280, 720):
                raise PdfExportError(f"page evidence has invalid dimensions: {path.name}")
            sampled = image.convert("RGB")
            sampled.thumbnail((160, 90))
            if sum(float(value) for value in ImageStat.Stat(sampled).var) <= 1:
                raise PdfExportError(f"page evidence is blank: {path.name}")
