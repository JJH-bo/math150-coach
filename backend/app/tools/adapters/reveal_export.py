from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat
from pypdf import PdfReader

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


class RevealExportError(ValueError):
    pass


class RevealExportAdapter:
    definition = ToolDefinition(
        tool_id="export.reveal",
        version="1.0.0",
        title="Verified Reveal lesson and PDF export",
        description=(
            "Render one semantic lesson as a self-contained keyboard-navigable "
            "Reveal presentation, print PDF, per-slide PNG evidence, and strict "
            "browser quality report."
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
                "render_report",
                "pdf_page_count",
            ],
            "properties": {
                "schema_version": {"type": "string"},
                "content_hash": {"type": "string"},
                "slide_count": {"type": "integer"},
                "template": {"type": "string"},
                "narrative_validation": {"type": "object"},
                "render_report": {"type": "object"},
                "pdf_page_count": {"type": "integer"},
            },
        },
        output_media_types=[
            "application/json",
            "text/html",
            "application/pdf",
            "image/png",
        ],
        quality_gates=[
            "semantic_lesson_contract",
            "self_contained_no_external_requests",
            "minimum_presentation_font_sizes",
            "zero_slide_overflow",
            "zero_console_errors",
            "nonblank_slide_pixels",
            "pdf_page_count_matches_slides",
        ],
        upstream_project="https://revealjs.com/ and https://playwright.dev/",
        license="MIT and Apache-2.0",
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
        report_path = work_dir / "render-report.json"
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RevealExportError(f"render report is missing or invalid: {exc}") from exc
        if not report.get("passed"):
            raise RevealExportError("render quality report did not pass")
        pdf_path = work_dir / "lesson.pdf"
        try:
            pdf_page_count = len(PdfReader(pdf_path).pages)
        except Exception as exc:
            raise RevealExportError(f"PDF structure validation failed: {exc}") from exc
        if pdf_page_count != len(lesson.slides):
            raise RevealExportError(
                f"PDF page count {pdf_page_count} does not match slide count {len(lesson.slides)}"
            )
        screenshot_paths = [
            work_dir / f"slide-{index:03d}.png"
            for index in range(1, len(lesson.slides) + 1)
        ]
        for screenshot in screenshot_paths:
            self._validate_screenshot(screenshot)
        html_path = work_dir / "lesson.html"
        for required in (html_path, pdf_path, report_path, *screenshot_paths):
            if not required.is_file() or required.stat().st_size == 0:
                raise RevealExportError(f"required export artifact is missing: {required.name}")
        result = {
            "schema_version": lesson.schema_version,
            "content_hash": content_hash,
            "slide_count": len(lesson.slides),
            "template": lesson.template.value,
            "narrative_validation": narrative_validation,
            "render_report": report,
            "pdf_page_count": pdf_page_count,
        }
        paths = [spec_path, html_path, pdf_path, report_path, *screenshot_paths]
        media_types = {
            ".json": "application/json",
            ".html": "text/html",
            ".pdf": "application/pdf",
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
                "pdf_page_count": pdf_page_count,
                "html_bytes": html_path.stat().st_size,
                "pdf_bytes": pdf_path.stat().st_size,
            },
        )

    def _run_worker(self, spec_path: Path, work_dir: Path) -> None:
        node = os.getenv("MODEL_PREVIEW_NODE") or shutil.which("node")
        if not node or not Path(node).is_file():
            raise RevealExportError("render worker requires a configured Node executable")
        worker = Path(__file__).resolve().parents[4] / "tools" / "render_semantic_lesson.cjs"
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
            raise RevealExportError(f"render worker could not complete: {exc}") from exc
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "render worker failed")[:3500]
            message = message.replace(str(work_dir), "<job-work-dir>")
            message = message.replace(str(node), "<node>")
            if browser:
                message = message.replace(browser, "<browser>")
            raise RevealExportError(f"render worker failed: {message}")

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
            raise RevealExportError(f"slide screenshot is missing: {path.name}")
        with Image.open(path) as image:
            if image.size != (1280, 720):
                raise RevealExportError(
                    f"slide screenshot {path.name} has invalid dimensions {image.size}"
                )
            sampled = image.convert("RGB")
            sampled.thumbnail((160, 90))
            if sum(float(value) for value in ImageStat.Stat(sampled).var) <= 1:
                raise RevealExportError(f"slide screenshot is blank: {path.name}")
