from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
import shutil
from pathlib import Path
from typing import Any

import kaleido
import plotly.graph_objects as go
from PIL import Image, ImageStat
from plotly.utils import PlotlyJSONEncoder

from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolProducedArtifact,
    ToolQualityTier,
    ToolScope,
)


TRACE_TYPES = (
    "line",
    "scatter",
    "bar",
    "area",
    "histogram",
    "heatmap",
    "contour",
    "surface",
)
ROOT_FIELDS = {
    "title",
    "x_label",
    "y_label",
    "z_label",
    "alt_text",
    "traces",
    "width",
    "height",
    "theme",
}
TRACE_FIELDS = {"type", "name", "x", "y", "z", "color", "opacity"}
COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
MAX_POINTS = 50_000


class PlotInputError(ValueError):
    pass


class PlotAdapter:
    definition = ToolDefinition(
        tool_id="visualization.plot",
        version="1.0.0",
        title="Verified interactive and static mathematical plots",
        description=(
            "Create validated line, scatter, bar, area, histogram, heatmap, "
            "contour, and surface visuals with accessible alt text, canonical "
            "Plotly JSON, self-contained HTML, PNG, SVG, and pixel-level QA."
        ),
        category="visualization",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.RENDER,
        execution_mode=ToolExecutionMode.ASYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=90,
        max_artifacts=12,
        max_artifact_bytes=64 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "x_label", "y_label", "alt_text", "traces"],
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 200},
                "x_label": {"type": "string", "minLength": 1, "maxLength": 160},
                "y_label": {"type": "string", "minLength": 1, "maxLength": 160},
                "z_label": {"type": "string", "maxLength": 160},
                "alt_text": {"type": "string", "minLength": 40, "maxLength": 2000},
                "width": {"type": "integer", "minimum": 600, "maximum": 2400},
                "height": {"type": "integer", "minimum": 400, "maximum": 1600},
                "theme": {"type": "string", "enum": ["light", "dark"]},
                "traces": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 32,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["type", "name"],
                        "properties": {
                            "type": {"type": "string", "enum": list(TRACE_TYPES)},
                            "name": {"type": "string", "minLength": 1, "maxLength": 160},
                            "x": {"type": "array", "maxItems": MAX_POINTS},
                            "y": {"type": "array", "maxItems": MAX_POINTS},
                            "z": {"type": "array", "maxItems": 1000},
                            "color": {"type": "string", "pattern": COLOR.pattern},
                            "opacity": {
                                "type": "number",
                                "minimum": 0.05,
                                "maximum": 1,
                            },
                        },
                    },
                },
            },
        },
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": [
                "title",
                "alt_text",
                "trace_count",
                "point_count",
                "width",
                "height",
                "theme",
                "figure_sha256",
                "validation",
            ],
            "properties": {
                "title": {"type": "string"},
                "alt_text": {"type": "string"},
                "trace_count": {"type": "integer"},
                "point_count": {"type": "integer"},
                "width": {"type": "integer"},
                "height": {"type": "integer"},
                "theme": {"type": "string"},
                "figure_sha256": {"type": "string"},
                "validation": {"type": "object"},
            },
        },
        output_media_types=[
            "application/json",
            "text/html",
            "image/png",
            "image/svg+xml",
            "text/plain",
        ],
        quality_gates=[
            "required_descriptive_alt_text",
            "finite_visible_marks",
            "static_browser_render",
            "pixel_variance_nonblank",
            "svg_structure",
            "bounded_readable_dimensions",
        ],
        upstream_project="https://plotly.com/python/ and https://github.com/plotly/Kaleido",
        license="MIT",
    )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        unknown = set(arguments) - ROOT_FIELDS
        if unknown:
            raise PlotInputError(f"unsupported plot fields: {sorted(unknown)}")
        title = self._text(arguments.get("title"), "title", 1, 200)
        x_label = self._text(arguments.get("x_label"), "x_label", 1, 160)
        y_label = self._text(arguments.get("y_label"), "y_label", 1, 160)
        z_label = self._text(arguments.get("z_label", "Value"), "z_label", 1, 160)
        alt_text = self._text(arguments.get("alt_text"), "alt_text", 40, 2000)
        width = self._integer(arguments.get("width", 1000), "width", 600, 2400)
        height = self._integer(arguments.get("height", 650), "height", 400, 1600)
        theme = arguments.get("theme", "light")
        if theme not in {"light", "dark"}:
            raise PlotInputError("theme must be light or dark")
        traces = arguments.get("traces")
        if not isinstance(traces, list) or not 1 <= len(traces) <= 32:
            raise PlotInputError("traces must contain 1 to 32 visible traces")

        figure = go.Figure()
        point_count = 0
        for index, trace in enumerate(traces):
            built, points = self._trace(trace, index)
            figure.add_trace(built)
            point_count += points
        if point_count < 1 or point_count > MAX_POINTS:
            raise PlotInputError(f"plot must contain 1 to {MAX_POINTS} visible points")
        figure.update_layout(
            title={"text": title, "x": 0.04, "xanchor": "left"},
            xaxis_title=x_label,
            yaxis_title=y_label,
            template="plotly_dark" if theme == "dark" else "plotly_white",
            width=width,
            height=height,
            margin={"l": 80, "r": 48, "t": 90, "b": 75},
            font={"family": "Arial, sans-serif", "size": 16},
            legend={"orientation": "h", "y": -0.18},
            hovermode="closest",
        )
        figure.update_layout(
            scene={
                "xaxis_title": x_label,
                "yaxis_title": y_label,
                "zaxis_title": z_label,
            }
        )
        work_dir = context.work_dir
        work_dir.mkdir(parents=True, exist_ok=True)
        figure_path = work_dir / "figure.json"
        html_path = work_dir / "figure.html"
        png_path = work_dir / "figure.png"
        svg_path = work_dir / "figure.svg"
        alt_path = work_dir / "alt.txt"
        validation_path = work_dir / "validation.json"

        figure_json = json.dumps(
            figure.to_plotly_json(),
            cls=PlotlyJSONEncoder,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ) + "\n"
        figure_path.write_text(figure_json, encoding="utf-8")
        fragment = figure.to_html(
            full_html=False,
            include_plotlyjs=True,
            div_id="studio-plot",
            config={"responsive": True, "displaylogo": False},
        )
        html_path.write_text(
            "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{html.escape(title)}</title></head><body>"
            f"<main role=\"img\" aria-label=\"{html.escape(alt_text, quote=True)}\">"
            f"{fragment}</main></body></html>\n",
            encoding="utf-8",
        )
        alt_path.write_text(alt_text + "\n", encoding="utf-8")
        self._render_static(figure, png_path, svg_path, width, height)
        validation = self._validate_artifacts(
            figure_path,
            html_path,
            png_path,
            svg_path,
            alt_path,
            width,
            height,
        )
        validation_path.write_text(
            json.dumps(validation, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        result = {
            "title": title,
            "alt_text": alt_text,
            "trace_count": len(traces),
            "point_count": point_count,
            "width": width,
            "height": height,
            "theme": theme,
            "figure_sha256": "sha256:" + hashlib.sha256(figure_json.encode("utf-8")).hexdigest(),
            "validation": validation,
        }
        artifacts = [
            self._artifact(figure_path, "application/json"),
            self._artifact(html_path, "text/html"),
            self._artifact(png_path, "image/png"),
            self._artifact(svg_path, "image/svg+xml"),
            self._artifact(alt_path, "text/plain"),
            self._artifact(validation_path, "application/json"),
        ]
        return ToolExecutionResult(
            result=result,
            artifacts=artifacts,
            metrics={
                "trace_count": len(traces),
                "point_count": point_count,
                "png_bytes": png_path.stat().st_size,
                "svg_bytes": svg_path.stat().st_size,
            },
        )

    def _trace(self, raw: Any, index: int) -> tuple[go.BaseTraceType, int]:
        if not isinstance(raw, dict):
            raise PlotInputError(f"trace {index} must be an object")
        unknown = set(raw) - TRACE_FIELDS
        if unknown:
            raise PlotInputError(f"trace {index} has unsupported fields: {sorted(unknown)}")
        trace_type = raw.get("type")
        if trace_type not in TRACE_TYPES:
            raise PlotInputError(f"trace {index} has unsupported type: {trace_type!r}")
        name = self._text(raw.get("name"), f"trace {index} name", 1, 160)
        color = raw.get("color")
        if color is not None and (not isinstance(color, str) or not COLOR.fullmatch(color)):
            raise PlotInputError(f"trace {index} color must be a six-digit hex color")
        opacity = raw.get("opacity", 1.0)
        if isinstance(opacity, bool) or not isinstance(opacity, (int, float)) or not 0.05 <= opacity <= 1:
            raise PlotInputError(f"trace {index} opacity must be between 0.05 and 1")
        opacity = float(opacity)
        if trace_type in {"line", "scatter", "bar", "area"}:
            x = self._numbers(raw.get("x"), f"trace {index} x", minimum=1)
            y = self._numbers(raw.get("y"), f"trace {index} y", minimum=1)
            if len(x) != len(y):
                raise PlotInputError(f"trace {index} x and y lengths must match")
            if trace_type == "line":
                return go.Scatter(x=x, y=y, name=name, mode="lines", opacity=opacity, line=self._color(color)), len(x)
            if trace_type == "scatter":
                return go.Scatter(x=x, y=y, name=name, mode="markers", opacity=opacity, marker=self._color(color)), len(x)
            if trace_type == "bar":
                return go.Bar(x=x, y=y, name=name, opacity=opacity, marker=self._color(color)), len(x)
            return go.Scatter(x=x, y=y, name=name, mode="lines", fill="tozeroy", opacity=opacity, line=self._color(color)), len(x)
        if trace_type == "histogram":
            x = self._numbers(raw.get("x"), f"trace {index} x", minimum=1)
            return go.Histogram(x=x, name=name, opacity=opacity, marker=self._color(color)), len(x)

        z = self._grid(raw.get("z"), f"trace {index} z")
        rows = len(z)
        columns = len(z[0])
        x = self._optional_axis(raw.get("x"), f"trace {index} x", columns)
        y = self._optional_axis(raw.get("y"), f"trace {index} y", rows)
        if trace_type == "heatmap":
            return go.Heatmap(z=z, x=x, y=y, name=name, opacity=opacity, colorscale="Viridis"), rows * columns
        if trace_type == "contour":
            return go.Contour(z=z, x=x, y=y, name=name, opacity=opacity, colorscale="Viridis"), rows * columns
        return go.Surface(z=z, x=x, y=y, name=name, opacity=opacity, colorscale="Viridis", showscale=True), rows * columns

    @staticmethod
    def _color(value: str | None) -> dict[str, str] | None:
        return {"color": value} if value is not None else None

    def _grid(self, raw: Any, name: str) -> list[list[float]]:
        if not isinstance(raw, list) or not raw or len(raw) > 1000:
            raise PlotInputError(f"{name} must be a non-empty bounded grid")
        if not all(isinstance(row, list) and row for row in raw):
            raise PlotInputError(f"{name} rows must be non-empty arrays")
        width = len(raw[0])
        if width > 1000 or any(len(row) != width for row in raw):
            raise PlotInputError(f"{name} must be rectangular and bounded")
        if len(raw) * width > MAX_POINTS:
            raise PlotInputError(f"{name} exceeds {MAX_POINTS} cells")
        return [
            [self._finite(value, name) for value in row]
            for row in raw
        ]

    def _optional_axis(self, raw: Any, name: str, expected: int) -> list[float] | None:
        if raw is None:
            return None
        values = self._numbers(raw, name, minimum=1)
        if len(values) != expected:
            raise PlotInputError(f"{name} length must be {expected}")
        return values

    def _numbers(self, raw: Any, name: str, *, minimum: int) -> list[float]:
        if not isinstance(raw, list) or not minimum <= len(raw) <= MAX_POINTS:
            raise PlotInputError(f"{name} must contain {minimum} to {MAX_POINTS} values")
        return [self._finite(value, name) for value in raw]

    @staticmethod
    def _finite(raw: Any, name: str) -> float:
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise PlotInputError(f"{name} values must be numbers")
        value = float(raw)
        if not math.isfinite(value):
            raise PlotInputError(f"{name} values must be finite")
        return value

    @staticmethod
    def _text(raw: Any, name: str, minimum: int, maximum: int) -> str:
        if not isinstance(raw, str) or not minimum <= len(raw.strip()) <= maximum:
            raise PlotInputError(f"{name} must contain {minimum} to {maximum} characters")
        return raw.strip()

    @staticmethod
    def _integer(raw: Any, name: str, minimum: int, maximum: int) -> int:
        if isinstance(raw, bool) or not isinstance(raw, int) or not minimum <= raw <= maximum:
            raise PlotInputError(f"{name} must be an integer from {minimum} to {maximum}")
        return raw

    def _render_static(
        self,
        figure: go.Figure,
        png_path: Path,
        svg_path: Path,
        width: int,
        height: int,
    ) -> None:
        browser = self._browser_path()
        options: dict[str, Any] = {"timeout": 90}
        if browser is not None:
            options["path"] = browser
        try:
            kaleido.write_fig_sync(
                figure,
                path=png_path,
                opts={"format": "png", "width": width, "height": height, "scale": 1},
                kopts=options,
            )
            kaleido.write_fig_sync(
                figure,
                path=svg_path,
                opts={"format": "svg", "width": width, "height": height, "scale": 1},
                kopts=options,
            )
        except Exception as exc:
            raise PlotInputError(
                "static browser rendering failed; configure MODEL_PREVIEW_BROWSER "
                f"to a working Chrome or Chromium executable: {exc}"
            ) from exc

    @staticmethod
    def _browser_path() -> str | None:
        configured = os.getenv("MODEL_PREVIEW_BROWSER")
        candidates = [
            configured,
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
    def _validate_artifacts(
        figure_path: Path,
        html_path: Path,
        png_path: Path,
        svg_path: Path,
        alt_path: Path,
        width: int,
        height: int,
    ) -> dict[str, Any]:
        for path in (figure_path, html_path, png_path, svg_path, alt_path):
            if not path.is_file() or path.stat().st_size == 0:
                raise PlotInputError(f"plot artifact is missing or empty: {path.name}")
        svg = svg_path.read_text(encoding="utf-8")
        if not svg.lstrip().startswith("<svg") or "</svg>" not in svg:
            raise PlotInputError("static SVG is structurally invalid")
        with Image.open(png_path) as image:
            if image.size != (width, height):
                raise PlotInputError(
                    f"PNG dimensions {image.size} do not match requested {(width, height)}"
                )
            sampled = image.convert("RGB")
            sampled.thumbnail((128, 128))
            colors = sampled.getcolors(maxcolors=128 * 128)
            unique_colors = len(colors) if colors is not None else 128 * 128
            variance = sum(float(value) for value in ImageStat.Stat(sampled).var)
        if unique_colors < 10 or variance <= 1:
            raise PlotInputError("plot is blank or contains no meaningful visual variation")
        return {
            "passed": True,
            "png_width": width,
            "png_height": height,
            "png_unique_colors": unique_colors,
            "png_channel_variance": variance,
            "png_bytes": png_path.stat().st_size,
            "svg_bytes": svg_path.stat().st_size,
            "html_bytes": html_path.stat().st_size,
            "figure_json_bytes": figure_path.stat().st_size,
            "alt_text_bytes": alt_path.stat().st_size,
        }

    @staticmethod
    def _artifact(path: Path, media_type: str) -> ToolProducedArtifact:
        return ToolProducedArtifact(
            name=path.name,
            media_type=media_type,
            source_path=path.name,
        )
