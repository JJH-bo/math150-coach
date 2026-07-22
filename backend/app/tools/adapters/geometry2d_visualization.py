from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
import shutil
import subprocess
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


ROOT_FIELDS = {"title", "alt_text", "viewport", "width", "height", "theme", "parameters", "objects"}
PARAMETER_FIELDS = {"id", "label", "minimum", "maximum", "step", "value"}
COMMON_OBJECT_FIELDS = {"id", "type", "label", "color"}
TYPE_FIELDS = {
    "point": {"x", "y"},
    "segment": {"x1", "y1", "x2", "y2"},
    "vector": {"x", "y", "dx", "dy"},
    "circle": {"cx", "cy", "r"},
    "polyline": {"points"},
    "polygon": {"points"},
}
IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,47}$")
COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class Geometry2dInputError(ValueError):
    pass


class Geometry2dAdapter:
    definition = ToolDefinition(
        tool_id="visualization.geometry2d",
        version="1.0.0",
        title="Verified interactive two-dimensional mathematical geometry",
        description=(
            "Create accessible coordinate scenes from bounded points, segments, vectors, "
            "circles, polylines, polygons, and slider parameters. Numeric properties may "
            "use safe affine parameter bindings; arbitrary code is not accepted. Real "
            "Chromium exercises every declared control and records before/after evidence."
        ),
        category="visualization",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.RENDER,
        execution_mode=ToolExecutionMode.ASYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=90,
        max_artifacts=20,
        max_artifact_bytes=96 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "alt_text", "viewport", "objects"],
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 200},
                "alt_text": {"type": "string", "minLength": 40, "maxLength": 2000},
                "viewport": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["x_min", "x_max", "y_min", "y_max"],
                    "properties": {
                        name: {"type": "number", "minimum": -1_000_000, "maximum": 1_000_000}
                        for name in ("x_min", "x_max", "y_min", "y_max")
                    },
                },
                "width": {"type": "integer", "minimum": 700, "maximum": 2400},
                "height": {"type": "integer", "minimum": 500, "maximum": 1600},
                "theme": {"type": "string", "enum": ["light", "dark"]},
                "parameters": {
                    "type": "array",
                    "maxItems": 8,
                    "items": {"type": "object"},
                },
                "objects": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 100,
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
                "object_count",
                "parameter_count",
                "width",
                "height",
                "geometry_sha256",
                "validation",
            ],
            "properties": {
                "title": {"type": "string"},
                "alt_text": {"type": "string"},
                "object_count": {"type": "integer"},
                "parameter_count": {"type": "integer"},
                "width": {"type": "integer"},
                "height": {"type": "integer"},
                "geometry_sha256": {"type": "string"},
                "validation": {"type": "object"},
            },
        },
        output_media_types=["application/json", "image/svg+xml", "text/html", "image/png", "text/plain"],
        quality_gates=[
            "required_descriptive_alt_text",
            "structured_non_executable_scene",
            "finite_bounded_geometry",
            "self_contained_browser_runtime",
            "real_browser_render",
            "declared_interaction_exercised",
            "interaction_changes_scene_state",
            "zero_console_or_request_errors",
            "no_clipping",
            "pixel_variance_nonblank",
        ],
        upstream_project="https://developer.mozilla.org/en-US/docs/Web/SVG",
        license="Project-owned runtime; web standards",
    )

    def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        specification = self._normalize(arguments)
        work_dir = context.work_dir
        work_dir.mkdir(parents=True, exist_ok=True)
        spec_path = work_dir / "geometry.json"
        svg_path = work_dir / "geometry.svg"
        html_path = work_dir / "geometry.html"
        png_path = work_dir / "geometry.png"
        alt_path = work_dir / "alt.txt"
        report_path = work_dir / "validation.json"
        interaction_paths = [
            work_dir / f"interaction-{index:03d}.png"
            for index in range(1, len(specification["parameters"]) + 1)
        ]
        canonical = json.dumps(specification, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        spec_path.write_text(canonical, encoding="utf-8")
        html_path.write_text(self._html(specification), encoding="utf-8")
        alt_path.write_text(specification["alt_text"] + "\n", encoding="utf-8")
        self._run_worker(spec_path, html_path, svg_path, png_path, report_path, work_dir)
        validation = self._validate(
            specification,
            spec_path,
            svg_path,
            html_path,
            png_path,
            alt_path,
            report_path,
            interaction_paths,
        )
        report_path.write_text(
            json.dumps(validation, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        result = {
            "title": specification["title"],
            "alt_text": specification["alt_text"],
            "object_count": len(specification["objects"]),
            "parameter_count": len(specification["parameters"]),
            "width": specification["width"],
            "height": specification["height"],
            "geometry_sha256": "sha256:" + hashlib.sha256(canonical.encode()).hexdigest(),
            "validation": validation,
        }
        paths = [spec_path, svg_path, html_path, png_path, *interaction_paths, alt_path, report_path]
        media = {".json": "application/json", ".svg": "image/svg+xml", ".html": "text/html", ".png": "image/png", ".txt": "text/plain"}
        return ToolExecutionResult(
            result=result,
            artifacts=[self._artifact(path, media[path.suffix]) for path in paths],
            metrics={
                "object_count": len(specification["objects"]),
                "parameter_count": len(specification["parameters"]),
                "png_bytes": png_path.stat().st_size,
                "svg_bytes": svg_path.stat().st_size,
            },
        )

    def _normalize(self, arguments: Any) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise Geometry2dInputError("geometry arguments must be an object")
        unknown = set(arguments) - ROOT_FIELDS
        if unknown:
            raise Geometry2dInputError(f"unsupported geometry fields: {sorted(unknown)}")
        title = self._text(arguments.get("title"), "title", 1, 200)
        alt_text = self._text(arguments.get("alt_text"), "alt_text", 40, 2000)
        viewport = self._viewport(arguments.get("viewport"))
        width = self._integer(arguments.get("width", 1000), "width", 700, 2400)
        height = self._integer(arguments.get("height", 650), "height", 500, 1600)
        theme = arguments.get("theme", "light")
        if theme not in {"light", "dark"}:
            raise Geometry2dInputError("theme must be light or dark")
        raw_parameters = arguments.get("parameters", [])
        if not isinstance(raw_parameters, list) or len(raw_parameters) > 8:
            raise Geometry2dInputError("parameters must contain at most 8 items")
        parameters = [self._parameter(raw, index) for index, raw in enumerate(raw_parameters)]
        parameter_ids = [item["id"] for item in parameters]
        if len(set(parameter_ids)) != len(parameter_ids):
            raise Geometry2dInputError("parameter IDs must be unique")
        parameter_map = {item["id"]: item for item in parameters}
        raw_objects = arguments.get("objects")
        if not isinstance(raw_objects, list) or not 1 <= len(raw_objects) <= 100:
            raise Geometry2dInputError("objects must contain 1 to 100 items")
        objects = [self._object(raw, index, parameter_map) for index, raw in enumerate(raw_objects)]
        object_ids = [item["id"] for item in objects]
        if len(set(object_ids)) != len(object_ids):
            raise Geometry2dInputError("object IDs must be unique")
        return {
            "title": title,
            "alt_text": alt_text,
            "viewport": viewport,
            "width": width,
            "height": height,
            "theme": theme,
            "parameters": parameters,
            "objects": objects,
        }

    def _viewport(self, raw: Any) -> dict[str, float]:
        fields = {"x_min", "x_max", "y_min", "y_max"}
        if not isinstance(raw, dict) or set(raw) != fields:
            raise Geometry2dInputError("viewport must contain x_min, x_max, y_min, and y_max")
        result = {name: self._finite(raw[name], f"viewport {name}") for name in fields}
        if result["x_max"] <= result["x_min"] or result["y_max"] <= result["y_min"]:
            raise Geometry2dInputError("viewport maxima must be greater than minima")
        if result["x_max"] - result["x_min"] > 1_000_000 or result["y_max"] - result["y_min"] > 1_000_000:
            raise Geometry2dInputError("viewport span is too large")
        return {name: result[name] for name in ("x_min", "x_max", "y_min", "y_max")}

    def _parameter(self, raw: Any, index: int) -> dict[str, Any]:
        if not isinstance(raw, dict) or set(raw) != PARAMETER_FIELDS:
            raise Geometry2dInputError(f"parameter {index} must contain exactly {sorted(PARAMETER_FIELDS)}")
        identifier = raw["id"]
        if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
            raise Geometry2dInputError(f"parameter {index} id is invalid")
        minimum = self._finite(raw["minimum"], f"parameter {index} minimum")
        maximum = self._finite(raw["maximum"], f"parameter {index} maximum")
        step = self._finite(raw["step"], f"parameter {index} step")
        value = self._finite(raw["value"], f"parameter {index} value")
        if maximum <= minimum or step <= 0 or step > maximum - minimum or not minimum <= value <= maximum:
            raise Geometry2dInputError(f"parameter {index} range, step, and value are inconsistent")
        return {
            "id": identifier,
            "label": self._safe_text(raw["label"], f"parameter {index} label", 1, 120),
            "minimum": minimum,
            "maximum": maximum,
            "step": step,
            "value": value,
        }

    def _object(self, raw: Any, index: int, parameters: dict[str, dict[str, Any]]) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise Geometry2dInputError(f"object {index} must be an object")
        object_type = raw.get("type")
        if object_type not in TYPE_FIELDS:
            raise Geometry2dInputError(f"object {index} has unsupported type {object_type!r}")
        expected = COMMON_OBJECT_FIELDS | TYPE_FIELDS[object_type]
        if set(raw) != expected:
            raise Geometry2dInputError(f"object {index} must contain exactly {sorted(expected)}")
        identifier = raw["id"]
        if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
            raise Geometry2dInputError(f"object {index} id is invalid")
        color = raw["color"]
        if not isinstance(color, str) or not COLOR.fullmatch(color):
            raise Geometry2dInputError(f"object {index} color must be a six-digit hex color")
        result: dict[str, Any] = {
            "id": identifier,
            "type": object_type,
            "label": self._safe_text(raw["label"], f"object {index} label", 1, 120),
            "color": color.upper(),
        }
        if object_type in {"polyline", "polygon"}:
            points = raw["points"]
            minimum = 2 if object_type == "polyline" else 3
            if not isinstance(points, list) or not minimum <= len(points) <= 2000:
                raise Geometry2dInputError(f"object {index} points must contain {minimum} to 2000 items")
            normalized = []
            for point_index, point in enumerate(points):
                if not isinstance(point, dict) or set(point) != {"x", "y"}:
                    raise Geometry2dInputError(f"object {index} point {point_index} is invalid")
                normalized.append(
                    {
                        "x": self._scalar(point["x"], f"object {index} point {point_index} x", parameters),
                        "y": self._scalar(point["y"], f"object {index} point {point_index} y", parameters),
                    }
                )
            result["points"] = normalized
        else:
            for name in TYPE_FIELDS[object_type]:
                result[name] = self._scalar(raw[name], f"object {index} {name}", parameters)
        if object_type == "circle":
            radii = self._scalar_extremes(result["r"], parameters)
            if min(radii) <= 0:
                raise Geometry2dInputError(f"object {index} radius must stay positive")
        return result

    def _scalar(self, raw: Any, name: str, parameters: dict[str, dict[str, Any]]) -> float | dict[str, Any]:
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            return self._finite(raw, name)
        fields = {"parameter", "scale", "offset"}
        if not isinstance(raw, dict) or set(raw) != fields or raw["parameter"] not in parameters:
            raise Geometry2dInputError(f"{name} must be finite or a valid affine parameter binding")
        result = {
            "parameter": raw["parameter"],
            "scale": self._finite(raw["scale"], f"{name} scale"),
            "offset": self._finite(raw["offset"], f"{name} offset"),
        }
        if max(abs(value) for value in self._scalar_extremes(result, parameters)) > 10_000_000:
            raise Geometry2dInputError(f"{name} exceeds the bounded coordinate range")
        return result

    @staticmethod
    def _scalar_extremes(value: float | dict[str, Any], parameters: dict[str, dict[str, Any]]) -> tuple[float, float]:
        if isinstance(value, float):
            return value, value
        parameter = parameters[value["parameter"]]
        return tuple(value["offset"] + value["scale"] * item for item in (parameter["minimum"], parameter["maximum"]))

    def _html(self, specification: dict[str, Any]) -> str:
        runtime_path = Path(__file__).resolve().parents[4] / "tools" / "geometry2d_runtime.js"
        runtime = runtime_path.read_text(encoding="utf-8")
        payload = json.dumps(specification, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c")
        dark = specification["theme"] == "dark"
        background = "#0B1119" if dark else "#F5F8FC"
        panel = "#101923" if dark else "#FFFFFF"
        foreground = "#F4F7FB" if dark else "#132033"
        muted = "#9FB0C3" if dark else "#53657A"
        border = "#273545" if dark else "#D7E0EA"
        return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(specification["title"])}</title><style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:{background};color:{foreground};font-family:Inter,Arial,sans-serif}}
body{{display:grid;grid-template-rows:auto 1fr;gap:18px;padding:28px 30px;box-sizing:border-box}}
header{{display:grid;gap:6px}}.kicker{{color:#33C3FF;font-size:12px;font-weight:800;letter-spacing:.14em}}h1{{margin:0;font-size:28px;line-height:1.12;letter-spacing:-.025em}}
.workspace{{min-height:0;display:grid;grid-template-columns:minmax(0,1fr) 220px;gap:18px}}.canvas-card,.controls{{border:1px solid {border};border-radius:18px;background:{panel}}}
.canvas-card{{min-width:0;min-height:0;padding:12px;display:grid}}#geometry-canvas{{width:100%;height:100%}}.grid line{{stroke:{border};stroke-width:1}}.grid text{{fill:{muted};font-size:13px}}.axis{{stroke:{muted};stroke-width:2}}
.controls{{padding:18px;display:grid;align-content:start;gap:16px}}.controls h2{{margin:0;font-size:15px}}.control{{display:grid;gap:9px}}.control-heading{{display:flex;justify-content:space-between;gap:10px;font-size:13px;color:{muted}}}output{{color:#33C3FF;font-weight:800}}input[type="range"]{{width:100%;accent-color:#33C3FF}}
</style></head><body><header><div class="kicker">INTERACTIVE GEOMETRY</div><h1>{html.escape(specification["title"])}</h1></header>
<main class="workspace" role="img" aria-label="{html.escape(specification["alt_text"], quote=True)}"><section class="canvas-card"><svg id="geometry-canvas" viewBox="0 0 900 430" role="img" aria-label="{html.escape(specification["alt_text"], quote=True)}"></svg></section><aside class="controls"><h2>Explore parameters</h2><div id="geometry-controls"></div></aside></main>
<script id="geometry-spec" type="application/json">{payload}</script><script>{runtime}</script></body></html>
'''

    def _run_worker(self, spec_path: Path, html_path: Path, svg_path: Path, png_path: Path, report_path: Path, work_dir: Path) -> None:
        node = os.getenv("MODEL_PREVIEW_NODE") or shutil.which("node")
        if not node or not Path(node).is_file():
            raise Geometry2dInputError("geometry renderer requires a configured Node executable")
        worker = Path(__file__).resolve().parents[4] / "tools" / "render_geometry2d.cjs"
        command = [str(node), str(worker), "--spec", str(spec_path), "--html", str(html_path), "--svg", str(svg_path), "--png", str(png_path), "--report", str(report_path), "--output", str(work_dir)]
        browser = self._browser_path()
        if browser:
            command.extend(["--browser", browser])
        environment = {key: os.environ[key] for key in ("NODE_PATH", "PATH", "SYSTEMROOT", "HOME", "TMP", "TEMP") if os.environ.get(key)}
        try:
            completed = subprocess.run(command, cwd=worker.parent.parent, env=environment, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise Geometry2dInputError(f"geometry render worker could not complete: {exc}") from exc
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "geometry worker failed")[:3500]
            for secret in (str(work_dir), str(node), browser):
                if secret:
                    message = message.replace(secret, "<runtime-path>")
            raise Geometry2dInputError(f"geometry browser rendering failed: {message}")

    @staticmethod
    def _validate(specification: dict[str, Any], spec_path: Path, svg_path: Path, html_path: Path, png_path: Path, alt_path: Path, report_path: Path, interaction_paths: list[Path]) -> dict[str, Any]:
        paths = [spec_path, svg_path, html_path, png_path, alt_path, report_path, *interaction_paths]
        for path in paths:
            if not path.is_file() or path.stat().st_size == 0:
                raise Geometry2dInputError(f"geometry artifact is missing or empty: {path.name}")
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            root = ElementTree.fromstring(svg_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, ElementTree.ParseError) as exc:
            raise Geometry2dInputError(f"geometry report or SVG is invalid: {exc}") from exc
        if not root.tag.endswith("svg") or not report.get("passed"):
            raise Geometry2dInputError("geometry browser quality report did not pass")
        image_reports = []
        for path in [png_path, *interaction_paths]:
            with Image.open(path) as image:
                expected = (specification["width"], specification["height"])
                if image.size != expected:
                    raise Geometry2dInputError(f"{path.name} dimensions do not match {expected}")
                sample = image.convert("RGB")
                sample.thumbnail((128, 128))
                colors = sample.getcolors(maxcolors=128 * 128)
                unique = len(colors) if colors is not None else 128 * 128
                variance = sum(float(value) for value in ImageStat.Stat(sample).var)
            if unique < 10 or variance <= 1:
                raise Geometry2dInputError(f"{path.name} is blank or visually empty")
            image_reports.append({"name": path.name, "unique_colors": unique, "channel_variance": variance, "bytes": path.stat().st_size})
        return {
            **report,
            "passed": True,
            "png_unique_colors": image_reports[0]["unique_colors"],
            "png_channel_variance": image_reports[0]["channel_variance"],
            "images": image_reports,
            "svg_bytes": svg_path.stat().st_size,
            "html_bytes": html_path.stat().st_size,
            "specification_bytes": spec_path.stat().st_size,
        }

    @staticmethod
    def _finite(raw: Any, name: str) -> float:
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)):
            raise Geometry2dInputError(f"{name} must be a finite number")
        value = float(raw)
        if abs(value) > 10_000_000:
            raise Geometry2dInputError(f"{name} exceeds the bounded numeric range")
        return value

    @staticmethod
    def _safe_text(raw: Any, name: str, minimum: int, maximum: int) -> str:
        value = Geometry2dAdapter._text(raw, name, minimum, maximum)
        if any(character in value for character in ("<", ">", "`", "\x00")):
            raise Geometry2dInputError(f"{name} contains unsafe markup")
        return value

    @staticmethod
    def _text(raw: Any, name: str, minimum: int, maximum: int) -> str:
        if not isinstance(raw, str) or not minimum <= len(raw.strip()) <= maximum:
            raise Geometry2dInputError(f"{name} must contain {minimum} to {maximum} characters")
        return raw.strip()

    @staticmethod
    def _integer(raw: Any, name: str, minimum: int, maximum: int) -> int:
        if isinstance(raw, bool) or not isinstance(raw, int) or not minimum <= raw <= maximum:
            raise Geometry2dInputError(f"{name} must be an integer from {minimum} to {maximum}")
        return raw

    @staticmethod
    def _browser_path() -> str | None:
        candidates = [os.getenv("MODEL_PREVIEW_BROWSER"), shutil.which("google-chrome"), shutil.which("chromium"), shutil.which("chromium-browser"), shutil.which("msedge"), r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", "/usr/bin/chromium", "/usr/bin/google-chrome"]
        for candidate in candidates:
            if candidate and Path(candidate).is_file():
                return str(Path(candidate))
        return None

    @staticmethod
    def _artifact(path: Path, media_type: str) -> ToolProducedArtifact:
        return ToolProducedArtifact(name=path.name, media_type=media_type, source_path=path.name)
