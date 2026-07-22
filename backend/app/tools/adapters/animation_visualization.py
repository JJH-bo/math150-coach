from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

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


ROOT_FIELDS = {
    "title",
    "alt_text",
    "width",
    "height",
    "fps",
    "background",
    "output_format",
    "objects",
    "timeline",
}
OBJECT_FIELDS = {
    "axes": {
        "id",
        "type",
        "x_range",
        "y_range",
        "x_length",
        "y_length",
        "position",
        "color",
    },
    "polyline": {"id", "type", "axes_id", "points", "color", "stroke_width"},
    "dot": {"id", "type", "position", "radius", "color"},
    "line": {"id", "type", "start", "end", "color", "stroke_width"},
    "arrow": {"id", "type", "start", "end", "color", "stroke_width"},
    "circle": {"id", "type", "position", "radius", "color", "fill_opacity"},
    "rectangle": {
        "id",
        "type",
        "position",
        "width",
        "height",
        "color",
        "fill_opacity",
    },
    "text": {"id", "type", "text", "position", "font_size", "color"},
}
ACTION_FIELDS = {
    "create": {"action", "object_id", "duration", "caption"},
    "write": {"action", "object_id", "duration", "caption"},
    "fade_in": {"action", "object_id", "duration", "caption"},
    "fade_out": {"action", "object_id", "duration", "caption"},
    "move_to": {"action", "object_id", "to", "duration", "caption"},
    "set_color": {"action", "object_id", "color", "duration", "caption"},
    "indicate": {"action", "object_id", "duration", "caption"},
    "transform": {
        "action",
        "object_id",
        "target_id",
        "duration",
        "caption",
    },
    "wait": {"action", "duration", "caption"},
}
IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,47}$")
COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
SIGNATURES = {
    "mp4": lambda data: b"ftyp" in data[:32],
    "webm": lambda data: data.startswith(bytes.fromhex("1a45dfa3")),
    "gif": lambda data: data.startswith((b"GIF87a", b"GIF89a")),
}


class AnimationInputError(ValueError):
    pass


class AnimationAdapter:
    definition = ToolDefinition(
        tool_id="visualization.animation",
        version="1.0.0",
        title="Verified structured mathematical animation",
        description=(
            "Render a bounded declarative scene and pedagogical timeline with Manim "
            "Community. Supports axes, sampled curves, points, lines, vectors, shapes, "
            "and Unicode mathematical labels plus create, write, transform, movement, "
            "highlight, color, fade, and wait actions. Emits MP4/WebM/GIF, poster, "
            "frame sheet, timed captions, alt text, and decoded-video quality evidence. "
            "The input never accepts Python, Manim source, shell commands, or paths."
        ),
        category="visualization",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.RENDER,
        execution_mode=ToolExecutionMode.ASYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=600,
        max_artifacts=7,
        max_artifact_bytes=512 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "alt_text", "objects", "timeline", "output_format"],
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 200},
                "alt_text": {"type": "string", "minLength": 40, "maxLength": 2000},
                "width": {"type": "integer", "minimum": 480, "maximum": 1920},
                "height": {"type": "integer", "minimum": 270, "maximum": 1080},
                "fps": {"type": "integer", "minimum": 12, "maximum": 60},
                "background": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
                "output_format": {"type": "string", "enum": ["mp4", "webm", "gif"]},
                "objects": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 40,
                    "items": {"type": "object"},
                },
                "timeline": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 60,
                    "items": {"type": "object"},
                },
            },
        },
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": [
                "title",
                "alt_text",
                "output_format",
                "object_count",
                "action_count",
                "duration_seconds",
                "scene_sha256",
                "validation",
            ],
            "properties": {
                "title": {"type": "string"},
                "alt_text": {"type": "string"},
                "output_format": {"type": "string"},
                "object_count": {"type": "integer"},
                "action_count": {"type": "integer"},
                "duration_seconds": {"type": "number"},
                "scene_sha256": {"type": "string"},
                "validation": {"type": "object"},
            },
        },
        output_media_types=[
            "application/json",
            "video/mp4",
            "video/webm",
            "image/gif",
            "image/png",
            "text/vtt",
            "text/plain",
        ],
        quality_gates=[
            "structured_non_executable_scene",
            "bounded_objects_and_timeline",
            "required_descriptive_alt_text",
            "timed_action_captions",
            "manim_community_0_20_1",
            "decoded_media_dimensions_and_fps",
            "representative_frame_sheet",
            "distinct_scene_states",
            "pixel_variance_nonblank",
            "artifact_signature_verified",
        ],
        upstream_project="Manim Community 0.20.1",
        license="MIT",
    )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        specification = self._normalize(arguments)
        work_dir = context.work_dir
        work_dir.mkdir(parents=True, exist_ok=True)
        spec_path = work_dir / "animation.json"
        report_path = work_dir / "validation.json"
        captions_path = work_dir / "captions.vtt"
        alt_path = work_dir / "alt.txt"
        canonical = json.dumps(specification, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        spec_path.write_text(canonical, encoding="utf-8")
        captions_path.write_text(self._captions(specification), encoding="utf-8")
        alt_path.write_text(specification["alt_text"] + "\n", encoding="utf-8")
        self._run_worker(spec_path, report_path, work_dir)
        video_path = work_dir / f"animation.{specification['output_format']}"
        poster_path = work_dir / "poster.png"
        sheet_path = work_dir / "frame-sheet.png"
        validation = self._validate(
            specification,
            video_path,
            poster_path,
            sheet_path,
            report_path,
            work_dir,
        )
        report_path.write_text(
            json.dumps(validation, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        media_type = {
            "mp4": "video/mp4",
            "webm": "video/webm",
            "gif": "image/gif",
        }[specification["output_format"]]
        paths = [
            (spec_path, "application/json"),
            (video_path, media_type),
            (poster_path, "image/png"),
            (sheet_path, "image/png"),
            (captions_path, "text/vtt"),
            (alt_path, "text/plain"),
            (report_path, "application/json"),
        ]
        duration = specification["timeline"][-1]["end_seconds"]
        return ToolExecutionResult(
            result={
                "title": specification["title"],
                "alt_text": specification["alt_text"],
                "output_format": specification["output_format"],
                "object_count": len(specification["objects"]),
                "action_count": len(specification["timeline"]),
                "duration_seconds": duration,
                "scene_sha256": "sha256:" + hashlib.sha256(canonical.encode()).hexdigest(),
                "validation": validation,
            },
            artifacts=[self._artifact(path, media) for path, media in paths],
            metrics={
                "object_count": len(specification["objects"]),
                "action_count": len(specification["timeline"]),
                "frame_count": validation["frame_count"],
                "duration_seconds": validation["duration_seconds"],
                "video_bytes": video_path.stat().st_size,
            },
        )

    def _normalize(self, arguments: Any) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise AnimationInputError("animation arguments must be an object")
        unknown = set(arguments) - ROOT_FIELDS
        if unknown:
            raise AnimationInputError(f"unsupported animation fields: {sorted(unknown)}")
        title = self._text(arguments.get("title"), "title", 1, 200)
        alt_text = self._safe_text(arguments.get("alt_text"), "alt_text", 40, 2000)
        width = self._integer(arguments.get("width", 1280), "width", 480, 1920)
        height = self._integer(arguments.get("height", 720), "height", 270, 1080)
        if not 1.5 <= width / height <= 2.0:
            raise AnimationInputError("animation aspect ratio must be from 1.5 to 2.0")
        fps = self._integer(arguments.get("fps", 30), "fps", 12, 60)
        background = self._color(arguments.get("background", "#0B1119"), "background")
        output_format = arguments.get("output_format")
        if output_format not in SIGNATURES:
            raise AnimationInputError("output_format must be mp4, webm, or gif")
        raw_objects = arguments.get("objects")
        if not isinstance(raw_objects, list) or not 1 <= len(raw_objects) <= 40:
            raise AnimationInputError("objects must contain 1 to 40 items")
        objects = []
        known: dict[str, dict[str, Any]] = {}
        for index, raw in enumerate(raw_objects):
            value = self._object(raw, index, known)
            if value["id"] in known:
                raise AnimationInputError("animation object IDs must be unique")
            known[value["id"]] = value
            objects.append(value)
        raw_timeline = arguments.get("timeline")
        if not isinstance(raw_timeline, list) or not 2 <= len(raw_timeline) <= 60:
            raise AnimationInputError("timeline must contain 2 to 60 actions")
        timeline = []
        visible: set[str] = set()
        elapsed = 0.0
        for index, raw in enumerate(raw_timeline):
            action = self._action(raw, index, known, visible)
            action["start_seconds"] = round(elapsed, 6)
            elapsed += action["duration"]
            action["end_seconds"] = round(elapsed, 6)
            timeline.append(action)
        if not 0.5 <= elapsed <= 30:
            raise AnimationInputError("animation duration must be from 0.5 to 30 seconds")
        if not visible:
            raise AnimationInputError("animation must finish with at least one visible object")
        return {
            "title": title,
            "alt_text": alt_text,
            "width": width,
            "height": height,
            "fps": fps,
            "background": background,
            "output_format": output_format,
            "objects": objects,
            "timeline": timeline,
        }

    def _object(
        self,
        raw: Any,
        index: int,
        known: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise AnimationInputError(f"object {index} must be an object")
        kind = raw.get("type")
        expected = OBJECT_FIELDS.get(kind)
        if expected is None or set(raw) != expected:
            raise AnimationInputError(f"object {index} fields are invalid for type {kind!r}")
        object_id = raw.get("id")
        if not isinstance(object_id, str) or IDENTIFIER.fullmatch(object_id) is None:
            raise AnimationInputError(f"object {index} id is invalid")
        value = dict(raw)
        value["color"] = self._color(raw["color"], f"object {index} color")
        if kind == "axes":
            value["x_range"] = self._axis_range(raw["x_range"], f"object {index} x_range")
            value["y_range"] = self._axis_range(raw["y_range"], f"object {index} y_range")
            value["x_length"] = self._bounded(raw["x_length"], f"object {index} x_length", 1, 12)
            value["y_length"] = self._bounded(raw["y_length"], f"object {index} y_length", 1, 7)
            value["position"] = self._position(raw["position"], f"object {index} position")
        elif kind == "polyline":
            axes_id = raw["axes_id"]
            if axes_id not in known or known[axes_id]["type"] != "axes":
                raise AnimationInputError(f"object {index} axes_id must reference an earlier axes object")
            if not isinstance(raw["points"], list) or not 2 <= len(raw["points"]) <= 500:
                raise AnimationInputError(f"object {index} points must contain 2 to 500 coordinates")
            value["points"] = [
                self._finite_pair(point, f"object {index} point") for point in raw["points"]
            ]
            value["stroke_width"] = self._bounded(
                raw["stroke_width"], f"object {index} stroke_width", 1, 20
            )
        elif kind in {"line", "arrow"}:
            value["start"] = self._position(raw["start"], f"object {index} start")
            value["end"] = self._position(raw["end"], f"object {index} end")
            value["stroke_width"] = self._bounded(
                raw["stroke_width"], f"object {index} stroke_width", 1, 20
            )
        elif kind in {"dot", "circle"}:
            value["position"] = self._position(raw["position"], f"object {index} position")
            value["radius"] = self._bounded(raw["radius"], f"object {index} radius", 0.03, 3)
            if kind == "circle":
                value["fill_opacity"] = self._bounded(
                    raw["fill_opacity"], f"object {index} fill_opacity", 0, 1
                )
        elif kind == "rectangle":
            value["position"] = self._position(raw["position"], f"object {index} position")
            value["width"] = self._bounded(raw["width"], f"object {index} width", 0.1, 12)
            value["height"] = self._bounded(raw["height"], f"object {index} height", 0.1, 7)
            value["fill_opacity"] = self._bounded(
                raw["fill_opacity"], f"object {index} fill_opacity", 0, 1
            )
        elif kind == "text":
            value["text"] = self._safe_text(raw["text"], f"object {index} text", 1, 200)
            value["position"] = self._position(raw["position"], f"object {index} position")
            value["font_size"] = self._integer(
                raw["font_size"], f"object {index} font_size", 12, 96
            )
        return value

    def _action(
        self,
        raw: Any,
        index: int,
        known: dict[str, dict[str, Any]],
        visible: set[str],
    ) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise AnimationInputError(f"timeline action {index} must be an object")
        kind = raw.get("action")
        expected = ACTION_FIELDS.get(kind)
        if expected is None or set(raw) != expected:
            raise AnimationInputError(f"timeline action {index} fields are invalid")
        value = dict(raw)
        value["duration"] = self._bounded(
            raw["duration"], f"timeline action {index} duration", 0.05, 10
        )
        value["caption"] = self._safe_text(
            raw["caption"], f"timeline action {index} caption", 12, 1000
        )
        if kind == "wait":
            return value
        object_id = raw["object_id"]
        if object_id not in known:
            raise AnimationInputError(f"timeline action {index} references an unknown object")
        if kind in {"create", "write", "fade_in"}:
            if object_id in visible:
                raise AnimationInputError(f"timeline action {index} shows an already visible object")
            visible.add(object_id)
        else:
            if object_id not in visible:
                raise AnimationInputError(f"timeline action {index} requires a visible object")
            if kind == "fade_out":
                visible.remove(object_id)
        if kind == "move_to":
            value["to"] = self._position(raw["to"], f"timeline action {index} to")
        elif kind == "set_color":
            value["color"] = self._color(raw["color"], f"timeline action {index} color")
        elif kind == "indicate":
            value["color"] = "#F6C85F"
        elif kind == "transform":
            target_id = raw["target_id"]
            if target_id not in known or target_id == object_id:
                raise AnimationInputError(f"timeline action {index} transform target is invalid")
        return value

    def _run_worker(self, spec_path: Path, report_path: Path, work_dir: Path) -> None:
        python = os.getenv("MANIM_PYTHON") or os.getenv("PYTHON_EXECUTABLE") or sys.executable
        if not Path(python).is_file():
            raise AnimationInputError("animation renderer requires MANIM_PYTHON")
        worker = Path(__file__).resolve().parents[4] / "tools" / "render_structured_animation.py"
        environment = {
            key: os.environ[key]
            for key in (
                "PATH",
                "SYSTEMROOT",
                "HOME",
                "USERPROFILE",
                "APPDATA",
                "LOCALAPPDATA",
                "TMP",
                "TEMP",
            )
            if os.environ.get(key)
        }
        try:
            completed = subprocess.run(
                [
                    str(python),
                    str(worker),
                    "--spec",
                    str(spec_path),
                    "--output",
                    str(work_dir),
                    "--report",
                    str(report_path),
                ],
                cwd=worker.parent.parent,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise AnimationInputError(f"animation worker could not complete: {exc}") from exc
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "animation worker failed")[:3500]
            for secret in (str(work_dir), str(python)):
                message = message.replace(secret, "<runtime-path>")
            raise AnimationInputError(f"Manim animation rendering failed: {message}")

    @staticmethod
    def _validate(
        specification: dict[str, Any],
        video_path: Path,
        poster_path: Path,
        sheet_path: Path,
        report_path: Path,
        work_dir: Path,
    ) -> dict[str, Any]:
        for path in (video_path, poster_path, sheet_path, report_path):
            if not path.is_file() or path.stat().st_size == 0:
                raise AnimationInputError(f"animation artifact is missing or empty: {path.name}")
        data = video_path.read_bytes()
        if not SIGNATURES[specification["output_format"]](data):
            raise AnimationInputError("animation media signature does not match its format")
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AnimationInputError(f"animation validation report is invalid: {exc}") from exc
        if not report.get("passed") or report.get("manim_version") != "0.20.1":
            raise AnimationInputError("animation quality report did not pass Manim 0.20.1 gates")
        if report.get("width") != specification["width"] or report.get("height") != specification["height"]:
            raise AnimationInputError("animation decoded dimensions do not match the request")
        image_evidence = []
        for path in (poster_path, sheet_path):
            with Image.open(path) as image:
                sample = image.convert("RGB")
                sample.thumbnail((160, 90))
                colors = sample.getcolors(maxcolors=160 * 90)
                unique = len(colors) if colors is not None else 160 * 90
                variance = sum(float(value) for value in ImageStat.Stat(sample).var)
            if unique < 20 or variance <= 1:
                raise AnimationInputError(f"{path.name} is blank or visually empty")
            image_evidence.append(
                {
                    "name": path.name,
                    "unique_colors": unique,
                    "channel_variance": variance,
                    "bytes": path.stat().st_size,
                }
            )
        serialized = json.dumps(report).lower()
        if str(work_dir).lower() in serialized or "studio_api_key" in serialized:
            raise AnimationInputError("animation report contains a runtime path or secret")
        return {**report, "passed": True, "images": image_evidence}

    @staticmethod
    def _captions(specification: dict[str, Any]) -> str:
        lines = ["WEBVTT", ""]
        for index, action in enumerate(specification["timeline"], start=1):
            lines.extend(
                [
                    str(index),
                    (
                        f"{AnimationAdapter._timestamp(action['start_seconds'])} --> "
                        f"{AnimationAdapter._timestamp(action['end_seconds'])}"
                    ),
                    action["caption"],
                    "",
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def _timestamp(seconds: float) -> str:
        milliseconds = int(round(seconds * 1000))
        hours, milliseconds = divmod(milliseconds, 3_600_000)
        minutes, milliseconds = divmod(milliseconds, 60_000)
        whole_seconds, milliseconds = divmod(milliseconds, 1000)
        return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}.{milliseconds:03d}"

    @staticmethod
    def _axis_range(raw: Any, name: str) -> list[float]:
        if not isinstance(raw, list) or len(raw) != 3:
            raise AnimationInputError(f"{name} must contain minimum, maximum, and step")
        minimum, maximum, step = [AnimationAdapter._finite(value, name) for value in raw]
        if minimum >= maximum or step <= 0 or (maximum - minimum) / step > 100:
            raise AnimationInputError(f"{name} is invalid or too dense")
        return [minimum, maximum, step]

    @staticmethod
    def _position(raw: Any, name: str) -> list[float]:
        x, y = AnimationAdapter._finite_pair(raw, name)
        if not -7 <= x <= 7 or not -4 <= y <= 4:
            raise AnimationInputError(f"{name} must stay inside the animation frame")
        return [x, y]

    @staticmethod
    def _finite_pair(raw: Any, name: str) -> list[float]:
        if not isinstance(raw, list) or len(raw) != 2:
            raise AnimationInputError(f"{name} must contain exactly two numbers")
        return [AnimationAdapter._finite(value, name) for value in raw]

    @staticmethod
    def _finite(raw: Any, name: str) -> float:
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)):
            raise AnimationInputError(f"{name} must contain finite numbers")
        value = float(raw)
        if abs(value) > 1_000_000:
            raise AnimationInputError(f"{name} exceeds the bounded numeric range")
        return value

    @staticmethod
    def _bounded(raw: Any, name: str, minimum: float, maximum: float) -> float:
        value = AnimationAdapter._finite(raw, name)
        if not minimum <= value <= maximum:
            raise AnimationInputError(f"{name} must be from {minimum} to {maximum}")
        return value

    @staticmethod
    def _integer(raw: Any, name: str, minimum: int, maximum: int) -> int:
        if isinstance(raw, bool) or not isinstance(raw, int) or not minimum <= raw <= maximum:
            raise AnimationInputError(f"{name} must be an integer from {minimum} to {maximum}")
        return raw

    @staticmethod
    def _color(raw: Any, name: str) -> str:
        if not isinstance(raw, str) or COLOR.fullmatch(raw) is None:
            raise AnimationInputError(f"{name} must be a hexadecimal color")
        return raw.upper()

    @staticmethod
    def _safe_text(raw: Any, name: str, minimum: int, maximum: int) -> str:
        value = AnimationAdapter._text(raw, name, minimum, maximum)
        if any(character in value for character in ("<", ">", "`", "\x00")):
            raise AnimationInputError(f"{name} contains unsafe markup")
        return value

    @staticmethod
    def _text(raw: Any, name: str, minimum: int, maximum: int) -> str:
        if not isinstance(raw, str) or not minimum <= len(raw.strip()) <= maximum:
            raise AnimationInputError(f"{name} must contain {minimum} to {maximum} characters")
        return raw.strip()

    @staticmethod
    def _artifact(path: Path, media_type: str) -> ToolProducedArtifact:
        return ToolProducedArtifact(
            name=path.name,
            media_type=media_type,
            source_path=path.name,
        )
