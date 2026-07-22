from __future__ import annotations

import json
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from PIL import Image, ImageStat

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
from app.tools.lesson_validation import (
    lesson_content_hash,
    normalize_lesson,
    validate_lesson,
)


DRAWING_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"


class PptxExportError(ValueError):
    pass


class PptxExportAdapter:
    definition = ToolDefinition(
        tool_id="export.pptx",
        version="1.0.0",
        title="Verified editable PowerPoint lesson export",
        description=(
            "Render one semantic lesson as an editable widescreen PPTX with "
            "native text and shapes, SVG mathematics, speaker notes, per-slide "
            "preview evidence, and independent OOXML and layout reports."
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
            "required": [
                "schema_version",
                "content_hash",
                "slide_count",
                "template",
                "narrative_validation",
                "layout_report",
                "ooxml_report",
            ],
            "properties": {
                "schema_version": {"type": "string"},
                "content_hash": {"type": "string"},
                "slide_count": {"type": "integer"},
                "template": {"type": "string"},
                "narrative_validation": {"type": "object"},
                "layout_report": {"type": "object"},
                "ooxml_report": {"type": "object"},
            },
        },
        output_media_types=[
            "application/json",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "image/png",
        ],
        quality_gates=[
            "semantic_lesson_contract",
            "editable_native_text_and_shapes",
            "speaker_notes_present",
            "svg_math_present",
            "minimum_presentation_font_sizes",
            "zero_slide_overflow",
            "zero_unintended_overlap",
            "valid_ooxml_package",
            "nonblank_slide_pixels",
        ],
        upstream_project="https://gitbrent.github.io/PptxGenJS/",
        license="MIT",
    )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        lesson = normalize_lesson(arguments)
        narrative_validation = validate_lesson(lesson)
        content_hash = lesson_content_hash(lesson)
        work_dir = context.work_dir
        work_dir.mkdir(parents=True, exist_ok=True)
        spec_path = work_dir / "lesson-spec.json"
        spec_path.write_text(
            json.dumps(
                {
                    "content_hash": content_hash,
                    "lesson": lesson.model_dump(mode="json", exclude_none=True),
                },
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self._run_worker(spec_path, work_dir)
        layout_path = work_dir / "layout-report.json"
        try:
            layout_report = json.loads(layout_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PptxExportError(f"layout report is missing or invalid: {exc}") from exc
        if not layout_report.get("passed"):
            raise PptxExportError("render layout quality report did not pass")

        pptx_path = work_dir / "lesson.pptx"
        ooxml_report = self._inspect_ooxml(pptx_path, lesson, content_hash)
        ooxml_path = work_dir / "ooxml-report.json"
        ooxml_path.write_text(
            json.dumps(ooxml_report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        if not ooxml_report["passed"]:
            raise PptxExportError("PPTX OOXML quality report did not pass")

        screenshot_paths = [
            work_dir / f"slide-{index:03d}.png"
            for index in range(1, len(lesson.slides) + 1)
        ]
        for screenshot in screenshot_paths:
            self._validate_screenshot(screenshot)
        montage_path = work_dir / "montage.png"
        self._build_montage(screenshot_paths, montage_path)
        self._validate_screenshot(montage_path)

        result = {
            "schema_version": lesson.schema_version,
            "content_hash": content_hash,
            "slide_count": len(lesson.slides),
            "template": lesson.template.value,
            "narrative_validation": narrative_validation,
            "layout_report": layout_report,
            "ooxml_report": ooxml_report,
        }
        paths = [
            spec_path,
            pptx_path,
            layout_path,
            ooxml_path,
            montage_path,
            *screenshot_paths,
        ]
        media_types = {
            ".json": "application/json",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".png": "image/png",
        }
        artifacts = [
            ToolProducedArtifact(
                name=path.name,
                media_type=media_types[path.suffix],
                source_path=path.name,
            )
            for path in paths
        ]
        return ToolExecutionResult(
            result=result,
            artifacts=artifacts,
            metrics={
                "slide_count": len(lesson.slides),
                "pptx_bytes": pptx_path.stat().st_size,
                "editable_text_shape_count": ooxml_report[
                    "editable_text_shape_count"
                ],
                "speaker_notes_count": ooxml_report["speaker_notes_count"],
            },
        )

    def _run_worker(self, spec_path: Path, work_dir: Path) -> None:
        node = os.getenv("MODEL_PREVIEW_NODE") or shutil.which("node")
        if not node or not Path(node).is_file():
            raise PptxExportError("render worker requires a configured Node executable")
        worker = Path(__file__).resolve().parents[4] / "tools" / "render_pptx_lesson.cjs"
        command = [str(node), str(worker), "--input", str(spec_path), "--output", str(work_dir)]
        browser = self._browser_path()
        if browser is not None:
            command.extend(["--browser", browser])
        environment = {
            key: os.environ[key]
            for key in ("NODE_PATH", "PATH", "SYSTEMROOT", "HOME", "TMP", "TEMP")
            if os.environ.get(key)
        }
        try:
            completed = subprocess.run(
                command,
                cwd=worker.parent.parent,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PptxExportError(f"render worker could not complete: {exc}") from exc
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "render worker failed")[:3500]
            message = message.replace(str(work_dir), "<job-work-dir>")
            message = message.replace(str(node), "<node>")
            if browser:
                message = message.replace(browser, "<browser>")
            raise PptxExportError(f"render worker failed: {message}")

    @staticmethod
    def _inspect_ooxml(
        pptx_path: Path,
        lesson: SemanticLesson,
        content_hash: str,
    ) -> dict[str, Any]:
        findings: list[dict[str, Any]] = []
        editable_text_shape_count = 0
        speaker_notes_count = 0
        font_sizes: list[float] = []
        formula_svg_count = 0
        formula_svg_valid_count = 0
        try:
            with zipfile.ZipFile(pptx_path) as archive:
                names = set(archive.namelist())
                slide_parts = sorted(
                    name
                    for name in names
                    if name.startswith("ppt/slides/slide") and name.endswith(".xml")
                )
                note_parts = sorted(
                    name
                    for name in names
                    if name.startswith("ppt/notesSlides/notesSlide")
                    and name.endswith(".xml")
                )
                speaker_notes_count = len(note_parts)
                formula_parts = sorted(
                    name
                    for name in names
                    if name.startswith("ppt/media/") and name.lower().endswith(".svg")
                )
                formula_svg_count = len(formula_parts)
                for part in formula_parts:
                    payload = archive.read(part)
                    try:
                        formula_root = ElementTree.fromstring(payload)
                    except ElementTree.ParseError:
                        findings.append({"code": "formula_svg_invalid_xml", "part": part})
                        continue
                    if not formula_root.tag.endswith("}svg") or b"data-latex" in payload:
                        findings.append({"code": "formula_svg_not_portable", "part": part})
                        continue
                    formula_svg_valid_count += 1
                if len(slide_parts) != len(lesson.slides):
                    findings.append(
                        {
                            "code": "slide_count_mismatch",
                            "actual": len(slide_parts),
                            "expected": len(lesson.slides),
                        }
                    )
                if speaker_notes_count != len(lesson.slides):
                    findings.append(
                        {
                            "code": "speaker_notes_count_mismatch",
                            "actual": speaker_notes_count,
                            "expected": len(lesson.slides),
                        }
                    )
                expected_formula_count = sum(
                    slide.formula is not None for slide in lesson.slides
                )
                if formula_svg_count < expected_formula_count:
                    findings.append(
                        {
                            "code": "formula_svg_missing",
                            "actual": formula_svg_count,
                            "expected": expected_formula_count,
                        }
                    )
                slide_text = ""
                for part in slide_parts:
                    root = ElementTree.fromstring(archive.read(part))
                    for shape in root.iter(f"{{{PRESENTATION_NS}}}sp"):
                        if any(
                            (node.text or "").strip()
                            for node in shape.iter(f"{{{DRAWING_NS}}}t")
                        ):
                            editable_text_shape_count += 1
                    for node in root.iter(f"{{{DRAWING_NS}}}t"):
                        slide_text += f" {(node.text or '').strip()}"
                    for node in root.iter():
                        if node.tag in {
                            f"{{{DRAWING_NS}}}rPr",
                            f"{{{DRAWING_NS}}}defRPr",
                            f"{{{DRAWING_NS}}}endParaRPr",
                        } and node.get("sz"):
                            font_sizes.append(int(node.get("sz", "0")) / 100)
                for slide in lesson.slides:
                    for expected in (slide.title, slide.primary_claim):
                        if expected not in slide_text:
                            findings.append(
                                {"code": "editable_text_missing", "slide_id": slide.slide_id}
                            )
                core = archive.read("docProps/core.xml").decode("utf-8", "replace")
                if content_hash not in core:
                    findings.append({"code": "content_hash_missing"})
        except (OSError, zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc:
            raise PptxExportError(f"PPTX structure validation failed: {exc}") from exc
        if editable_text_shape_count < len(lesson.slides) * 2:
            findings.append(
                {
                    "code": "insufficient_editable_text_shapes",
                    "actual": editable_text_shape_count,
                }
            )
        if not font_sizes or min(font_sizes) < 16:
            findings.append(
                {
                    "code": "font_below_minimum",
                    "actual": min(font_sizes) if font_sizes else None,
                }
            )
        return {
            "passed": not findings,
            "slide_count": len(lesson.slides),
            "editable_text_shape_count": editable_text_shape_count,
            "speaker_notes_count": speaker_notes_count,
            "formula_svg_count": formula_svg_count,
            "formula_svg_valid_count": formula_svg_valid_count,
            "actual_minimum_font_pt": min(font_sizes) if font_sizes else None,
            "minimum_font_sizes": {
                "deck_title": 50,
                "slide_title": 35,
                "subheading": 24,
                "body": 16,
            },
            "findings": findings,
        }

    @staticmethod
    def _build_montage(paths: list[Path], output_path: Path) -> None:
        canvas = Image.new("RGB", (1280, 720), "#081018")
        columns = 2
        rows = max(1, (len(paths) + columns - 1) // columns)
        cell_width = 620
        cell_height = min(340, (700 - (rows - 1) * 16) // rows)
        for index, path in enumerate(paths):
            with Image.open(path) as source:
                preview = source.convert("RGB")
                preview.thumbnail((cell_width, cell_height))
                column = index % columns
                row = index // columns
                x = 12 + column * 636 + (cell_width - preview.width) // 2
                y = 10 + row * (cell_height + 16) + (cell_height - preview.height) // 2
                canvas.paste(preview, (x, y))
        canvas.save(output_path, format="PNG", optimize=True)

    @staticmethod
    def _browser_path() -> str | None:
        configured = os.getenv("MODEL_PREVIEW_BROWSER")
        if configured:
            return configured
        candidates = [
            shutil.which("google-chrome"),
            shutil.which("chromium"),
            shutil.which("msedge"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "/usr/bin/chromium",
            "/usr/bin/google-chrome",
        ]
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return str(Path(candidate))
        return None

    @staticmethod
    def _validate_screenshot(path: Path) -> None:
        if not path.is_file():
            raise PptxExportError(f"slide preview is missing: {path.name}")
        with Image.open(path) as image:
            if image.size != (1280, 720):
                raise PptxExportError(
                    f"slide preview {path.name} has invalid dimensions {image.size}"
                )
            sampled = image.convert("RGB")
            sampled.thumbnail((160, 90))
            if sum(float(value) for value in ImageStat.Stat(sampled).var) <= 1:
                raise PptxExportError(f"slide preview is blank: {path.name}")
