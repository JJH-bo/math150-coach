from __future__ import annotations

import hashlib
import html
import json
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


ROOT_FIELDS = {
    "title",
    "alt_text",
    "direction",
    "theme",
    "width",
    "height",
    "nodes",
    "edges",
}
NODE_FIELDS = {"id", "label", "shape"}
EDGE_FIELDS = {"source", "target", "label"}
NODE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,47}$")
SHAPES = ("rectangle", "rounded", "stadium", "circle", "diamond")
DIRECTIONS = ("TB", "TD", "BT", "RL", "LR")


class DiagramInputError(ValueError):
    pass


class DiagramAdapter:
    definition = ToolDefinition(
        tool_id="visualization.diagram",
        version="1.0.0",
        title="Verified structured concept and process diagrams",
        description=(
            "Render bounded node-edge diagrams through Mermaid 11 and real Chromium. "
            "The GPT supplies structured nodes and edges rather than executable Mermaid "
            "source. Outputs include canonical JSON/source, accessible self-contained "
            "SVG/HTML, PNG, alt text, and clipping/pixel/browser QA."
        ),
        category="visualization",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.RENDER,
        execution_mode=ToolExecutionMode.ASYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=90,
        max_artifacts=10,
        max_artifact_bytes=64 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "alt_text", "nodes", "edges"],
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 200},
                "alt_text": {"type": "string", "minLength": 40, "maxLength": 2000},
                "direction": {"type": "string", "enum": list(DIRECTIONS)},
                "theme": {"type": "string", "enum": ["light", "dark"]},
                "width": {"type": "integer", "minimum": 600, "maximum": 2400},
                "height": {"type": "integer", "minimum": 400, "maximum": 1600},
                "nodes": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 80,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id", "label"],
                        "properties": {
                            "id": {"type": "string", "pattern": NODE_ID.pattern},
                            "label": {"type": "string", "minLength": 1, "maxLength": 180},
                            "shape": {"type": "string", "enum": list(SHAPES)},
                        },
                    },
                },
                "edges": {
                    "type": "array",
                    "minItems": 0,
                    "maxItems": 160,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["source", "target"],
                        "properties": {
                            "source": {"type": "string", "pattern": NODE_ID.pattern},
                            "target": {"type": "string", "pattern": NODE_ID.pattern},
                            "label": {"type": "string", "maxLength": 160},
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
                "node_count",
                "edge_count",
                "width",
                "height",
                "theme",
                "diagram_sha256",
                "validation",
            ],
            "properties": {
                "title": {"type": "string"},
                "alt_text": {"type": "string"},
                "node_count": {"type": "integer"},
                "edge_count": {"type": "integer"},
                "width": {"type": "integer"},
                "height": {"type": "integer"},
                "theme": {"type": "string"},
                "diagram_sha256": {"type": "string"},
                "validation": {"type": "object"},
            },
        },
        output_media_types=[
            "application/json",
            "text/vnd.mermaid",
            "image/svg+xml",
            "text/html",
            "image/png",
            "text/plain",
        ],
        quality_gates=[
            "required_descriptive_alt_text",
            "structured_non_executable_input",
            "strict_mermaid_security",
            "real_browser_render",
            "zero_console_or_request_errors",
            "svg_structure_and_visible_nodes",
            "no_clipping",
            "pixel_variance_nonblank",
        ],
        upstream_project="https://mermaid.js.org/",
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
        spec_path = work_dir / "diagram.json"
        source_path = work_dir / "diagram.mmd"
        svg_path = work_dir / "diagram.svg"
        html_path = work_dir / "diagram.html"
        png_path = work_dir / "diagram.png"
        alt_path = work_dir / "alt.txt"
        validation_path = work_dir / "validation.json"

        canonical = json.dumps(
            specification,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ) + "\n"
        spec_path.write_text(canonical, encoding="utf-8")
        source = self._mermaid_source(specification)
        source_path.write_text(source, encoding="utf-8")
        alt_path.write_text(specification["alt_text"] + "\n", encoding="utf-8")
        self._run_worker(spec_path, source_path, svg_path, png_path, validation_path)
        svg = self._validated_svg(svg_path, specification)
        html_path.write_text(
            self._self_contained_html(specification, svg),
            encoding="utf-8",
        )
        validation = self._validate_artifacts(
            specification,
            spec_path,
            source_path,
            svg_path,
            html_path,
            png_path,
            alt_path,
            validation_path,
        )
        validation_path.write_text(
            json.dumps(validation, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        result = {
            "title": specification["title"],
            "alt_text": specification["alt_text"],
            "node_count": len(specification["nodes"]),
            "edge_count": len(specification["edges"]),
            "width": specification["width"],
            "height": specification["height"],
            "theme": specification["theme"],
            "diagram_sha256": "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "validation": validation,
        }
        paths_and_types = [
            (spec_path, "application/json"),
            (source_path, "text/vnd.mermaid"),
            (svg_path, "image/svg+xml"),
            (html_path, "text/html"),
            (png_path, "image/png"),
            (alt_path, "text/plain"),
            (validation_path, "application/json"),
        ]
        return ToolExecutionResult(
            result=result,
            artifacts=[self._artifact(path, media) for path, media in paths_and_types],
            metrics={
                "node_count": len(specification["nodes"]),
                "edge_count": len(specification["edges"]),
                "png_bytes": png_path.stat().st_size,
                "svg_bytes": svg_path.stat().st_size,
            },
        )

    def _normalize(self, arguments: Any) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise DiagramInputError("diagram arguments must be an object")
        unknown = set(arguments) - ROOT_FIELDS
        if unknown:
            raise DiagramInputError(f"unsupported diagram fields: {sorted(unknown)}")
        title = self._text(arguments.get("title"), "title", 1, 200)
        alt_text = self._text(arguments.get("alt_text"), "alt_text", 40, 2000)
        direction = arguments.get("direction", "TB")
        theme = arguments.get("theme", "light")
        if direction not in DIRECTIONS:
            raise DiagramInputError(f"direction must be one of {DIRECTIONS}")
        if theme not in {"light", "dark"}:
            raise DiagramInputError("theme must be light or dark")
        width = self._integer(arguments.get("width", 1000), "width", 600, 2400)
        height = self._integer(arguments.get("height", 650), "height", 400, 1600)
        raw_nodes = arguments.get("nodes")
        raw_edges = arguments.get("edges")
        if not isinstance(raw_nodes, list) or not 1 <= len(raw_nodes) <= 80:
            raise DiagramInputError("nodes must contain 1 to 80 items")
        if not isinstance(raw_edges, list) or len(raw_edges) > 160:
            raise DiagramInputError("edges must contain 0 to 160 items")
        nodes = [self._node(item, index) for index, item in enumerate(raw_nodes)]
        node_ids = [node["id"] for node in nodes]
        if len(set(node_ids)) != len(node_ids):
            raise DiagramInputError("node IDs must be unique")
        known_ids = set(node_ids)
        edges = [self._edge(item, index, known_ids) for index, item in enumerate(raw_edges)]
        return {
            "title": title,
            "alt_text": alt_text,
            "direction": direction,
            "theme": theme,
            "width": width,
            "height": height,
            "nodes": nodes,
            "edges": edges,
        }

    def _node(self, raw: Any, index: int) -> dict[str, str]:
        if not isinstance(raw, dict):
            raise DiagramInputError(f"node {index} must be an object")
        unknown = set(raw) - NODE_FIELDS
        if unknown:
            raise DiagramInputError(f"node {index} has unsupported fields: {sorted(unknown)}")
        node_id = raw.get("id")
        if not isinstance(node_id, str) or not NODE_ID.fullmatch(node_id):
            raise DiagramInputError(f"node {index} id is invalid")
        label = self._safe_label(raw.get("label"), f"node {index} label", 1, 180)
        shape = raw.get("shape", "rectangle")
        if shape not in SHAPES:
            raise DiagramInputError(f"node {index} shape must be one of {SHAPES}")
        return {"id": node_id, "label": label, "shape": shape}

    def _edge(self, raw: Any, index: int, known_ids: set[str]) -> dict[str, str]:
        if not isinstance(raw, dict):
            raise DiagramInputError(f"edge {index} must be an object")
        unknown = set(raw) - EDGE_FIELDS
        if unknown:
            raise DiagramInputError(f"edge {index} has unsupported fields: {sorted(unknown)}")
        source = raw.get("source")
        target = raw.get("target")
        if source not in known_ids or target not in known_ids:
            raise DiagramInputError(f"edge {index} references an unknown node")
        label = self._safe_label(raw.get("label", ""), f"edge {index} label", 0, 160)
        return {"source": source, "target": target, "label": label}

    @staticmethod
    def _mermaid_source(specification: dict[str, Any]) -> str:
        wrappers = {
            "rectangle": ('["', '"]'),
            "rounded": ('("', '")'),
            "stadium": ('(["', '"])'),
            "circle": ('(("', '"))'),
            "diamond": ('{"', '"}'),
        }
        lines = [f"flowchart {specification['direction']}"]
        for node in specification["nodes"]:
            opening, closing = wrappers[node["shape"]]
            label = DiagramAdapter._wrapped_mermaid_label(node["label"])
            lines.append(f"    {node['id']}{opening}{label}{closing}")
        for edge in specification["edges"]:
            if edge["label"]:
                label = html.escape(edge["label"], quote=True).replace("|", "&#124;")
                lines.append(f"    {edge['source']} -->|{label}| {edge['target']}")
            else:
                lines.append(f"    {edge['source']} --> {edge['target']}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _wrapped_mermaid_label(label: str) -> str:
        words = label.split()
        if len(label) <= 18 or len(words) < 2:
            return html.escape(label, quote=True)
        split = min(
            range(1, len(words)),
            key=lambda index: abs(
                len(" ".join(words[:index])) - len(" ".join(words[index:]))
            ),
        )
        first = html.escape(" ".join(words[:split]), quote=True)
        second = html.escape(" ".join(words[split:]), quote=True)
        return f"{first}<br/>{second}"

    def _run_worker(
        self,
        spec_path: Path,
        source_path: Path,
        svg_path: Path,
        png_path: Path,
        report_path: Path,
    ) -> None:
        node = os.getenv("MODEL_PREVIEW_NODE") or shutil.which("node")
        if not node or not Path(node).is_file():
            raise DiagramInputError("diagram renderer requires a configured Node executable")
        worker = Path(__file__).resolve().parents[4] / "tools" / "render_mermaid_diagram.cjs"
        command = [
            str(node),
            str(worker),
            "--spec",
            str(spec_path),
            "--source",
            str(source_path),
            "--svg",
            str(svg_path),
            "--png",
            str(png_path),
            "--report",
            str(report_path),
        ]
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
                timeout=90,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DiagramInputError(f"diagram render worker could not complete: {exc}") from exc
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "diagram worker failed")[:3500]
            for secret in (str(spec_path.parent), str(node), browser):
                if secret:
                    message = message.replace(secret, "<runtime-path>")
            raise DiagramInputError(f"diagram browser rendering failed: {message}")

    @staticmethod
    def _validated_svg(svg_path: Path, specification: dict[str, Any]) -> str:
        try:
            svg = svg_path.read_text(encoding="utf-8")
            root = ElementTree.fromstring(svg)
        except (OSError, ElementTree.ParseError) as exc:
            raise DiagramInputError(f"diagram SVG is missing or invalid: {exc}") from exc
        if not root.tag.endswith("svg"):
            raise DiagramInputError("diagram SVG root is not an svg element")
        visible_text = " ".join(" ".join(root.itertext()).split())
        if not all(node["label"] in visible_text for node in specification["nodes"]):
            raise DiagramInputError("diagram SVG is missing one or more node labels")
        return svg

    @staticmethod
    def _self_contained_html(specification: dict[str, Any], svg: str) -> str:
        background = "#0B1119" if specification["theme"] == "dark" else "#F7F9FC"
        title = html.escape(specification["title"])
        alt = html.escape(specification["alt_text"], quote=True)
        return (
            "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{title}</title><style>html,body{{margin:0;background:{background};}}"
            "main{min-height:100vh;display:grid;place-items:center;padding:24px;box-sizing:border-box;}"
            "svg{max-width:100%;height:auto;}</style></head><body>"
            f"<main role=\"img\" aria-label=\"{alt}\">{svg}</main></body></html>\n"
        )

    @staticmethod
    def _validate_artifacts(
        specification: dict[str, Any],
        spec_path: Path,
        source_path: Path,
        svg_path: Path,
        html_path: Path,
        png_path: Path,
        alt_path: Path,
        report_path: Path,
    ) -> dict[str, Any]:
        paths = (spec_path, source_path, svg_path, html_path, png_path, alt_path, report_path)
        for path in paths:
            if not path.is_file() or path.stat().st_size == 0:
                raise DiagramInputError(f"diagram artifact is missing or empty: {path.name}")
        try:
            browser_report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DiagramInputError(f"diagram browser report is invalid: {exc}") from exc
        if not browser_report.get("passed"):
            raise DiagramInputError("diagram browser quality report did not pass")
        with Image.open(png_path) as image:
            expected = (specification["width"], specification["height"])
            if image.size != expected:
                raise DiagramInputError(
                    f"diagram PNG dimensions {image.size} do not match requested {expected}"
                )
            sampled = image.convert("RGB")
            sampled.thumbnail((128, 128))
            colors = sampled.getcolors(maxcolors=128 * 128)
            unique_colors = len(colors) if colors is not None else 128 * 128
            variance = sum(float(value) for value in ImageStat.Stat(sampled).var)
        if unique_colors < 10 or variance <= 1:
            raise DiagramInputError("diagram is blank or has no meaningful visual variation")
        return {
            **browser_report,
            "passed": True,
            "png_unique_colors": unique_colors,
            "png_channel_variance": variance,
            "png_bytes": png_path.stat().st_size,
            "svg_bytes": svg_path.stat().st_size,
            "html_bytes": html_path.stat().st_size,
            "specification_bytes": spec_path.stat().st_size,
            "source_bytes": source_path.stat().st_size,
            "alt_text_bytes": alt_path.stat().st_size,
        }

    @staticmethod
    def _safe_label(raw: Any, name: str, minimum: int, maximum: int) -> str:
        value = DiagramAdapter._text(raw, name, minimum, maximum)
        if any(character in value for character in ("<", ">", "`", "\x00")):
            raise DiagramInputError(f"{name} contains unsafe markup characters")
        return value

    @staticmethod
    def _text(raw: Any, name: str, minimum: int, maximum: int) -> str:
        if not isinstance(raw, str) or not minimum <= len(raw.strip()) <= maximum:
            raise DiagramInputError(f"{name} must contain {minimum} to {maximum} characters")
        return raw.strip()

    @staticmethod
    def _integer(raw: Any, name: str, minimum: int, maximum: int) -> int:
        if isinstance(raw, bool) or not isinstance(raw, int) or not minimum <= raw <= maximum:
            raise DiagramInputError(f"{name} must be an integer from {minimum} to {maximum}")
        return raw

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
