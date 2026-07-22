from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from PIL import Image, ImageStat

from app.classroom.models import ContentBlock
from app.classroom.repository import ClassroomNotFoundError, ClassroomRepository
from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolProducedArtifact,
    ToolQualityTier,
    ToolScope,
)


FIELDS = {
    "package_id",
    "module_id",
    "viewports",
    "reveal_steps",
    "open_first_detail",
    "quality_profile",
}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,119}$")
VIEWPORTS = {
    "desktop": [{"name": "desktop", "width": 1440, "height": 960}],
    "mobile": [{"name": "mobile", "width": 390, "height": 844}],
    "both": [
        {"name": "desktop", "width": 1440, "height": 960},
        {"name": "mobile", "width": 390, "height": 844},
    ],
}


class PagePreviewInputError(ValueError):
    pass


class PagePreviewAdapter:
    definition = ToolDefinition(
        tool_id="page.preview",
        version="1.0.0",
        title="Preview a published classroom in the real learner runtime",
        description=(
            "Open one immutable published module in the project-owned learner UI at "
            "desktop and/or mobile size. Exercises progressive reveal and an optional "
            "detail branch, then verifies mathematics rendering, teaching models, "
            "overflow, clipping, accessibility, network requests, console output, and "
            "nonblank screenshots. The tool accepts no URL, HTML, CSS, or script."
        ),
        category="page",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.RENDER,
        execution_mode=ToolExecutionMode.ASYNC,
        deterministic=False,
        cacheable=False,
        timeout_seconds=120,
        max_artifacts=4,
        max_artifact_bytes=48 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["package_id", "module_id"],
            "properties": {
                "package_id": {
                    "type": "string",
                    "pattern": "^[a-z0-9][a-z0-9-]{0,79}$",
                },
                "module_id": {
                    "type": "string",
                    "pattern": "^[A-Za-z0-9][A-Za-z0-9_-]{0,119}$",
                },
                "viewports": {
                    "type": "string",
                    "enum": ["desktop", "mobile", "both"],
                    "default": "both",
                },
                "reveal_steps": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 20,
                    "default": 1,
                },
                "open_first_detail": {"type": "boolean", "default": True},
                "quality_profile": {
                    "type": "string",
                    "enum": ["standard", "high"],
                    "default": "standard",
                },
            },
        },
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": [
                "package_id",
                "release_version",
                "module_id",
                "viewport_count",
                "request_sha256",
                "validation",
            ],
            "properties": {
                "package_id": {"type": "string"},
                "release_version": {"type": "string"},
                "module_id": {"type": "string"},
                "viewport_count": {"type": "integer"},
                "request_sha256": {"type": "string"},
                "validation": {"type": "object"},
            },
        },
        output_media_types=["application/json", "image/png"],
        quality_gates=[
            "registered_immutable_release",
            "real_learner_runtime",
            "bounded_project_owned_origin",
            "desktop_mobile_viewports",
            "progressive_reveal_exercised",
            "mathematics_rendered",
            "declared_model_visible",
            "zero_horizontal_overflow",
            "zero_clipped_text",
            "accessible_controls_and_media",
            "zero_console_or_request_errors",
            "pixel_variance_nonblank",
        ],
        upstream_project="Project Classroom Runtime and Playwright 1.61.1",
        license="Project-owned / Apache-2.0",
    )

    def __init__(
        self,
        repository: ClassroomRepository,
        *,
        public_origin: str | None = None,
    ) -> None:
        self.repository = repository
        self.public_origin = public_origin

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        values = self._normalize(arguments)
        self._validated_origin()
        try:
            release = self.repository.get_active_release(values["package_id"])
        except ClassroomNotFoundError as exc:
            raise PagePreviewInputError("published package was not found") from exc
        module = None
        for course in release.package.courses:
            for chapter in course.chapters:
                for candidate in chapter.modules:
                    if candidate.id == values["module_id"]:
                        module = candidate
                        break
        if module is None:
            raise PagePreviewInputError("module was not found in the published package")

        content_ids = {module.id}
        for block in module.blocks:
            self._collect_content_ids(block, content_ids)
        for segment in module.segments:
            content_ids.add(segment.id)
            for block in segment.blocks:
                self._collect_content_ids(block, content_ids)
        model_expected = any(
            binding.content_id in content_ids
            for binding in release.package.model_bindings
        )
        request = {
            **values,
            "release_version": release.version,
            "model_expected": model_expected,
            "viewports": VIEWPORTS[values["viewports"]],
        }
        work_dir = context.work_dir
        work_dir.mkdir(parents=True, exist_ok=True)
        request_path = work_dir / "preview-request.json"
        report_path = work_dir / "preview-report.json"
        canonical = json.dumps(request, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        request_path.write_text(canonical, encoding="utf-8")
        self._run_worker(request_path, report_path, work_dir)
        validation, screenshot_paths = self._validate(request, report_path, work_dir)
        report_path.write_text(
            json.dumps(validation, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        artifacts = [self._artifact(request_path, "application/json")]
        artifacts.extend(self._artifact(path, "image/png") for path in screenshot_paths)
        artifacts.append(self._artifact(report_path, "application/json"))
        return ToolExecutionResult(
            result={
                "package_id": values["package_id"],
                "release_version": release.version,
                "module_id": values["module_id"],
                "viewport_count": len(request["viewports"]),
                "request_sha256": "sha256:" + hashlib.sha256(canonical.encode()).hexdigest(),
                "validation": validation,
            },
            artifacts=artifacts,
            metrics={
                "viewport_count": len(request["viewports"]),
                "reveal_steps": values["reveal_steps"],
                "model_expected": model_expected,
                "screenshot_bytes": sum(path.stat().st_size for path in screenshot_paths),
            },
        )

    def _normalize(self, arguments: Any) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise PagePreviewInputError("page preview arguments must be an object")
        unknown = set(arguments) - FIELDS
        if unknown:
            raise PagePreviewInputError(f"unsupported page preview fields: {sorted(unknown)}")
        package_id = arguments.get("package_id")
        module_id = arguments.get("module_id")
        if not isinstance(package_id, str) or re.fullmatch(
            r"[a-z0-9][a-z0-9-]{0,79}", package_id
        ) is None:
            raise PagePreviewInputError("package_id is invalid")
        if not isinstance(module_id, str) or SAFE_ID.fullmatch(module_id) is None:
            raise PagePreviewInputError("module_id is invalid")
        viewports = arguments.get("viewports", "both")
        if viewports not in VIEWPORTS:
            raise PagePreviewInputError("viewports must be desktop, mobile, or both")
        reveal_steps = arguments.get("reveal_steps", 1)
        if (
            isinstance(reveal_steps, bool)
            or not isinstance(reveal_steps, int)
            or not 0 <= reveal_steps <= 20
        ):
            raise PagePreviewInputError("reveal_steps must be an integer from 0 to 20")
        open_first_detail = arguments.get("open_first_detail", True)
        if not isinstance(open_first_detail, bool):
            raise PagePreviewInputError("open_first_detail must be boolean")
        quality_profile = arguments.get("quality_profile", "standard")
        if quality_profile not in {"standard", "high"}:
            raise PagePreviewInputError("quality_profile must be standard or high")
        return {
            "package_id": package_id,
            "module_id": module_id,
            "viewports": viewports,
            "reveal_steps": reveal_steps,
            "open_first_detail": open_first_detail,
            "quality_profile": quality_profile,
        }

    def _run_worker(
        self,
        request_path: Path,
        report_path: Path,
        work_dir: Path,
    ) -> None:
        node = os.getenv("MODEL_PREVIEW_NODE") or shutil.which("node")
        if not node or not Path(node).is_file():
            raise PagePreviewInputError("page preview requires a configured Node executable")
        worker = Path(__file__).resolve().parents[4] / "tools" / "preview_classroom_page.cjs"
        command = [
            str(node),
            str(worker),
            "--origin",
            self._validated_origin(),
            "--request",
            str(request_path),
            "--report",
            str(report_path),
            "--output",
            str(work_dir),
        ]
        browser = self._browser_path()
        if browser:
            command.extend(["--browser", browser])
        environment = {
            key: os.environ[key]
            for key in (
                "NODE_PATH",
                "PATH",
                "SYSTEMROOT",
                "HOME",
                "TMP",
                "TEMP",
            )
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
            raise PagePreviewInputError(
                f"page preview worker could not complete: {exc}"
            ) from exc
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "page preview failed")[:3500]
            for secret in (str(work_dir), str(node), browser, self._validated_origin()):
                if secret:
                    message = message.replace(secret, "<runtime-path>")
            raise PagePreviewInputError(f"learner page preview failed: {message}")

    @staticmethod
    def _validate(
        request: dict[str, Any],
        report_path: Path,
        work_dir: Path,
    ) -> tuple[dict[str, Any], list[Path]]:
        if not report_path.is_file() or report_path.stat().st_size == 0:
            raise PagePreviewInputError("page preview report is missing or empty")
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PagePreviewInputError(f"page preview report is invalid: {exc}") from exc
        if not report.get("passed"):
            raise PagePreviewInputError("page preview browser quality report did not pass")
        reports = report.get("viewports")
        expected_viewports = request["viewports"]
        if not isinstance(reports, list) or len(reports) != len(expected_viewports):
            raise PagePreviewInputError("page preview viewport report count is invalid")
        screenshot_paths: list[Path] = []
        image_evidence = []
        scale = 2 if request["quality_profile"] == "high" else 1
        for expected, viewport in zip(expected_viewports, reports, strict=True):
            if viewport.get("name") != expected["name"]:
                raise PagePreviewInputError("page preview viewport order is invalid")
            screenshot = work_dir / str(viewport.get("screenshot", ""))
            if screenshot.parent != work_dir or not screenshot.is_file():
                raise PagePreviewInputError("page preview screenshot is missing")
            if any(
                viewport.get(field)
                for field in (
                    "clipped_text",
                    "accessibility_issues",
                    "console_errors",
                    "failed_requests",
                )
            ):
                raise PagePreviewInputError(
                    f"{expected['name']} page preview contains quality failures"
                )
            if viewport.get("horizontal_overflow") not in (0, 1):
                raise PagePreviewInputError(
                    f"{expected['name']} page preview has horizontal overflow"
                )
            if viewport.get("unrendered_math") != 0:
                raise PagePreviewInputError(
                    f"{expected['name']} page preview has unrendered mathematics"
                )
            if not isinstance(viewport.get("baseline_steps"), int) or viewport[
                "baseline_steps"
            ] < 1:
                raise PagePreviewInputError(
                    f"{expected['name']} page preview has no visible lesson step"
                )
            if request["model_expected"] and not viewport.get("model_canvas_visible"):
                raise PagePreviewInputError(
                    f"{expected['name']} page preview did not render its teaching model"
                )
            with Image.open(screenshot) as image:
                expected_size = (
                    expected["width"] * scale,
                    expected["height"] * scale,
                )
                if image.size != expected_size:
                    raise PagePreviewInputError(
                        f"{screenshot.name} dimensions do not match {expected_size}"
                    )
                sample = image.convert("RGB")
                sample.thumbnail((128, 128))
                colors = sample.getcolors(maxcolors=128 * 128)
                unique = len(colors) if colors is not None else 128 * 128
                variance = sum(float(value) for value in ImageStat.Stat(sample).var)
            if unique < 20 or variance <= 1:
                raise PagePreviewInputError(
                    f"{screenshot.name} is blank or visually empty"
                )
            screenshot_paths.append(screenshot)
            image_evidence.append(
                {
                    "name": screenshot.name,
                    "unique_colors": unique,
                    "channel_variance": variance,
                    "bytes": screenshot.stat().st_size,
                }
            )
        return {**report, "passed": True, "images": image_evidence}, screenshot_paths

    def _validated_origin(self) -> str:
        origin = (self.public_origin or os.getenv("AI_CLASSROOM_PUBLIC_ORIGIN", "")).strip()
        parsed = urlsplit(origin)
        loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
        if parsed.scheme not in {"http", "https"} or (
            parsed.scheme != "https" and not loopback
        ):
            raise PagePreviewInputError(
                "AI_CLASSROOM_PUBLIC_ORIGIN must use HTTPS, except for loopback preview"
            )
        if (
            not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise PagePreviewInputError("AI_CLASSROOM_PUBLIC_ORIGIN must be a bare origin")
        return origin.rstrip("/")

    @classmethod
    def _collect_content_ids(cls, block: ContentBlock, target: set[str]) -> None:
        target.add(block.id)
        for branch in block.detail_branches:
            target.add(branch.id)
            for child in branch.blocks:
                cls._collect_content_ids(child, target)

    @staticmethod
    def _browser_path() -> str | None:
        candidates = [
            os.getenv("MODEL_PREVIEW_BROWSER"),
            shutil.which("google-chrome"),
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
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
    def _artifact(path: Path, media_type: str) -> ToolProducedArtifact:
        return ToolProducedArtifact(
            name=path.name,
            media_type=media_type,
            source_path=path.name,
        )
