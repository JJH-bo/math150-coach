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


ROOT_FIELDS = {"title", "alt_text", "width", "height", "theme", "camera", "objects"}
CAMERA_FIELDS = {"azimuth", "elevation", "distance", "target"}
COMMON_FIELDS = {"id", "type", "label", "color"}
TYPE_FIELDS = {
    "surface": {"opacity", "x", "y", "z"},
    "vector": {"origin", "direction"},
    "point": {"position", "size"},
}
IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,47}$")
COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


class Scene3dInputError(ValueError):
    pass


class Scene3dAdapter:
    definition = ToolDefinition(
        tool_id="visualization.scene3d",
        version="1.0.0",
        title="Verified interactive Three.js mathematical scenes",
        description=(
            "Render bounded mathematical surfaces, vectors, and points with pinned "
            "Three.js, WebGL, lighting, axes, camera controls, self-contained HTML, "
            "poster and interaction screenshots, and real-browser state-change QA. "
            "The input is structured scene data and never arbitrary JavaScript."
        ),
        category="visualization",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.RENDER,
        execution_mode=ToolExecutionMode.ASYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=120,
        max_artifacts=10,
        max_artifact_bytes=128 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "alt_text", "camera", "objects"],
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 200},
                "alt_text": {"type": "string", "minLength": 40, "maxLength": 2000},
                "width": {"type": "integer", "minimum": 800, "maximum": 2400},
                "height": {"type": "integer", "minimum": 550, "maximum": 1600},
                "theme": {"type": "string", "enum": ["light", "dark"]},
                "camera": {"type": "object"},
                "objects": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 40,
                    "items": {"type": "object"},
                },
            },
        },
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "alt_text", "object_count", "width", "height", "scene_sha256", "validation"],
            "properties": {
                "title": {"type": "string"},
                "alt_text": {"type": "string"},
                "object_count": {"type": "integer"},
                "width": {"type": "integer"},
                "height": {"type": "integer"},
                "scene_sha256": {"type": "string"},
                "validation": {"type": "object"},
            },
        },
        output_media_types=["application/json", "text/html", "image/png", "text/plain"],
        quality_gates=[
            "required_descriptive_alt_text",
            "structured_non_executable_scene",
            "finite_bounded_meshes",
            "self_contained_pinned_threejs",
            "real_webgl_browser_render",
            "camera_interaction_exercised",
            "interaction_changes_scene_state",
            "visible_rendered_objects",
            "zero_console_or_request_errors",
            "pixel_variance_nonblank",
        ],
        upstream_project="https://threejs.org/",
        license="MIT",
    )

    def execute(self, arguments: dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        specification = self._normalize(arguments)
        work_dir = context.work_dir
        work_dir.mkdir(parents=True, exist_ok=True)
        spec_path = work_dir / "scene.json"
        html_path = work_dir / "scene.html"
        poster_path = work_dir / "poster.png"
        interaction_path = work_dir / "interaction.png"
        alt_path = work_dir / "alt.txt"
        report_path = work_dir / "validation.json"
        canonical = json.dumps(specification, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        spec_path.write_text(canonical, encoding="utf-8")
        html_path.write_text(self._html(specification), encoding="utf-8")
        alt_path.write_text(specification["alt_text"] + "\n", encoding="utf-8")
        self._run_worker(spec_path, html_path, poster_path, interaction_path, report_path, work_dir)
        validation = self._validate(
            specification,
            spec_path,
            html_path,
            poster_path,
            interaction_path,
            alt_path,
            report_path,
        )
        report_path.write_text(
            json.dumps(validation, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        result = {
            "title": specification["title"],
            "alt_text": specification["alt_text"],
            "object_count": len(specification["objects"]),
            "width": specification["width"],
            "height": specification["height"],
            "scene_sha256": "sha256:" + hashlib.sha256(canonical.encode()).hexdigest(),
            "validation": validation,
        }
        paths_and_media = [
            (spec_path, "application/json"),
            (html_path, "text/html"),
            (poster_path, "image/png"),
            (interaction_path, "image/png"),
            (alt_path, "text/plain"),
            (report_path, "application/json"),
        ]
        return ToolExecutionResult(
            result=result,
            artifacts=[self._artifact(path, media) for path, media in paths_and_media],
            metrics={
                "object_count": len(specification["objects"]),
                "triangle_count": validation["triangle_count"],
                "poster_bytes": poster_path.stat().st_size,
            },
        )

    def _normalize(self, arguments: Any) -> dict[str, Any]:
        if not isinstance(arguments, dict):
            raise Scene3dInputError("scene arguments must be an object")
        unknown = set(arguments) - ROOT_FIELDS
        if unknown:
            raise Scene3dInputError(f"unsupported scene fields: {sorted(unknown)}")
        title = self._text(arguments.get("title"), "title", 1, 200)
        alt_text = self._text(arguments.get("alt_text"), "alt_text", 40, 2000)
        width = self._integer(arguments.get("width", 1000), "width", 800, 2400)
        height = self._integer(arguments.get("height", 650), "height", 550, 1600)
        theme = arguments.get("theme", "light")
        if theme not in {"light", "dark"}:
            raise Scene3dInputError("theme must be light or dark")
        camera = self._camera(arguments.get("camera"))
        raw_objects = arguments.get("objects")
        if not isinstance(raw_objects, list) or not 1 <= len(raw_objects) <= 40:
            raise Scene3dInputError("objects must contain 1 to 40 items")
        objects = [self._object(raw, index) for index, raw in enumerate(raw_objects)]
        identifiers = [item["id"] for item in objects]
        if len(set(identifiers)) != len(identifiers):
            raise Scene3dInputError("object IDs must be unique")
        return {
            "title": title,
            "alt_text": alt_text,
            "width": width,
            "height": height,
            "theme": theme,
            "camera": camera,
            "objects": objects,
        }

    def _camera(self, raw: Any) -> dict[str, Any]:
        if not isinstance(raw, dict) or set(raw) != CAMERA_FIELDS:
            raise Scene3dInputError(f"camera must contain exactly {sorted(CAMERA_FIELDS)}")
        azimuth = self._finite(raw["azimuth"], "camera azimuth")
        elevation = self._finite(raw["elevation"], "camera elevation")
        distance = self._finite(raw["distance"], "camera distance")
        if not -360 <= azimuth <= 360 or not -80 <= elevation <= 80 or not 1 <= distance <= 100:
            raise Scene3dInputError("camera azimuth, elevation, or distance is out of range")
        return {
            "azimuth": azimuth,
            "elevation": elevation,
            "distance": distance,
            "target": self._vector3(raw["target"], "camera target"),
        }

    def _object(self, raw: Any, index: int) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise Scene3dInputError(f"object {index} must be an object")
        object_type = raw.get("type")
        if object_type not in TYPE_FIELDS:
            raise Scene3dInputError(f"object {index} has unsupported type {object_type!r}")
        expected = COMMON_FIELDS | TYPE_FIELDS[object_type]
        if set(raw) != expected:
            raise Scene3dInputError(f"object {index} must contain exactly {sorted(expected)}")
        identifier = raw["id"]
        if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
            raise Scene3dInputError(f"object {index} id is invalid")
        color = raw["color"]
        if not isinstance(color, str) or not COLOR.fullmatch(color):
            raise Scene3dInputError(f"object {index} color must be a six-digit hex color")
        result: dict[str, Any] = {
            "id": identifier,
            "type": object_type,
            "label": self._safe_text(raw["label"], f"object {index} label", 1, 120),
            "color": color.upper(),
        }
        if object_type == "surface":
            x = self._number_list(raw["x"], f"object {index} x", 2, 80)
            y = self._number_list(raw["y"], f"object {index} y", 2, 80)
            z = raw["z"]
            if not isinstance(z, list) or len(z) != len(y) or any(not isinstance(row, list) or len(row) != len(x) for row in z):
                raise Scene3dInputError(f"object {index} z must be a rectangular y-by-x grid")
            result.update(
                {
                    "opacity": self._bounded(raw["opacity"], f"object {index} opacity", 0.1, 1),
                    "x": x,
                    "y": y,
                    "z": [[self._finite(value, f"object {index} z") for value in row] for row in z],
                }
            )
        elif object_type == "vector":
            origin = self._vector3(raw["origin"], f"object {index} origin")
            direction = self._vector3(raw["direction"], f"object {index} direction")
            if math.sqrt(sum(value * value for value in direction)) <= 1e-9:
                raise Scene3dInputError(f"object {index} direction must be nonzero")
            result.update({"origin": origin, "direction": direction})
        else:
            result.update(
                {
                    "position": self._vector3(raw["position"], f"object {index} position"),
                    "size": self._bounded(raw["size"], f"object {index} size", 0.02, 2),
                }
            )
        return result

    def _html(self, specification: dict[str, Any]) -> str:
        root = Path(__file__).resolve().parents[4]
        three_path = root / "node_modules" / "three" / "build" / "three.module.min.js"
        three_core_path = root / "node_modules" / "three" / "build" / "three.core.min.js"
        runtime_path = root / "tools" / "scene3d_runtime.js"
        if not three_path.is_file() or not three_core_path.is_file():
            raise Scene3dInputError("pinned Three.js browser module is unavailable")
        three_source = json.dumps(three_path.read_text(encoding="utf-8"))
        three_core_source = json.dumps(three_core_path.read_text(encoding="utf-8"))
        runtime = runtime_path.read_text(encoding="utf-8")
        payload = json.dumps(specification, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c")
        dark = specification["theme"] == "dark"
        background = "#0B1119" if dark else "#F5F8FC"
        panel = "#101923" if dark else "#FFFFFF"
        foreground = "#F4F7FB" if dark else "#132033"
        muted = "#9FB0C3" if dark else "#53657A"
        border = "#273545" if dark else "#D7E0EA"
        return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(specification["title"])}</title><style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:{background};color:{foreground};font-family:Inter,Arial,sans-serif}}body{{display:grid;grid-template-rows:auto 1fr;gap:16px;padding:26px 30px;box-sizing:border-box}}header{{display:grid;gap:5px}}.kicker{{color:#33C3FF;font-size:12px;font-weight:800;letter-spacing:.14em}}h1{{margin:0;font-size:28px;line-height:1.12;letter-spacing:-.025em}}
.workspace{{min-height:0;display:grid;grid-template-columns:minmax(0,1fr) 225px;gap:18px}}#scene-mount,.panel{{border:1px solid {border};border-radius:18px;background:{panel};overflow:hidden}}#scene-mount canvas{{display:block;width:100%;height:100%}}.panel{{padding:18px;display:grid;align-content:start;gap:18px}}.panel h2{{margin:0;font-size:15px}}label{{display:grid;gap:8px;font-size:13px;color:{muted}}}.row{{display:flex;justify-content:space-between;gap:8px}}output{{color:#33C3FF;font-weight:800}}input{{width:100%;accent-color:#33C3FF}}ul{{list-style:none;margin:0;padding:0;display:grid;gap:9px;font-size:13px;color:{muted}}}li{{display:flex;align-items:center;gap:8px}}li span{{width:10px;height:10px;border-radius:50%}}
</style></head><body><header><div class="kicker">INTERACTIVE 3D SCENE</div><h1>{html.escape(specification["title"])}</h1></header><main class="workspace" role="img" aria-label="{html.escape(specification["alt_text"], quote=True)}"><section id="scene-mount"></section><aside class="panel"><h2>Orbit camera</h2><label><span class="row"><span>Azimuth</span><output id="camera-azimuth-value"></output></span><input id="camera-azimuth" type="range" min="-180" max="180" step="1" value="{specification["camera"]["azimuth"]}" aria-label="Camera azimuth"></label><label><span class="row"><span>Elevation</span><output id="camera-elevation-value"></output></span><input id="camera-elevation" type="range" min="-70" max="70" step="1" value="{specification["camera"]["elevation"]}" aria-label="Camera elevation"></label><h2>Scene objects</h2><ul id="scene-legend"></ul></aside></main><script id="scene-spec" type="application/json">{payload}</script><script type="module">const coreSource={three_core_source};const moduleSource={three_source};const coreUrl=URL.createObjectURL(new Blob([coreSource],{{type:"text/javascript"}}));const moduleUrl=URL.createObjectURL(new Blob([moduleSource.replaceAll("./three.core.min.js",coreUrl)],{{type:"text/javascript"}}));const THREE=await import(moduleUrl);URL.revokeObjectURL(moduleUrl);URL.revokeObjectURL(coreUrl);{runtime}</script></body></html>'''

    def _run_worker(self, spec_path: Path, html_path: Path, poster_path: Path, interaction_path: Path, report_path: Path, work_dir: Path) -> None:
        node = os.getenv("MODEL_PREVIEW_NODE") or shutil.which("node")
        if not node or not Path(node).is_file():
            raise Scene3dInputError("3D renderer requires a configured Node executable")
        worker = Path(__file__).resolve().parents[4] / "tools" / "render_scene3d.cjs"
        command = [str(node), str(worker), "--spec", str(spec_path), "--html", str(html_path), "--poster", str(poster_path), "--interaction", str(interaction_path), "--report", str(report_path)]
        browser = self._browser_path()
        if browser:
            command.extend(["--browser", browser])
        environment = {key: os.environ[key] for key in ("NODE_PATH", "PATH", "SYSTEMROOT", "HOME", "TMP", "TEMP") if os.environ.get(key)}
        try:
            completed = subprocess.run(command, cwd=worker.parent.parent, env=environment, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise Scene3dInputError(f"3D render worker could not complete: {exc}") from exc
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "3D worker failed")[:3500]
            for secret in (str(work_dir), str(node), browser):
                if secret:
                    message = message.replace(secret, "<runtime-path>")
            raise Scene3dInputError(f"3D browser rendering failed: {message}")

    @staticmethod
    def _validate(specification: dict[str, Any], spec_path: Path, html_path: Path, poster_path: Path, interaction_path: Path, alt_path: Path, report_path: Path) -> dict[str, Any]:
        for path in (spec_path, html_path, poster_path, interaction_path, alt_path, report_path):
            if not path.is_file() or path.stat().st_size == 0:
                raise Scene3dInputError(f"3D artifact is missing or empty: {path.name}")
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise Scene3dInputError(f"3D report is invalid: {exc}") from exc
        if not report.get("passed"):
            raise Scene3dInputError("3D browser quality report did not pass")
        images = []
        for path in (poster_path, interaction_path):
            with Image.open(path) as image:
                expected = (specification["width"], specification["height"])
                if image.size != expected:
                    raise Scene3dInputError(f"{path.name} dimensions do not match {expected}")
                sample = image.convert("RGB")
                sample.thumbnail((128, 128))
                colors = sample.getcolors(maxcolors=128 * 128)
                unique = len(colors) if colors is not None else 128 * 128
                variance = sum(float(value) for value in ImageStat.Stat(sample).var)
            if unique < 20 or variance <= 1:
                raise Scene3dInputError(f"{path.name} is blank or visually empty")
            images.append({"name": path.name, "unique_colors": unique, "channel_variance": variance, "bytes": path.stat().st_size})
        if poster_path.read_bytes() == interaction_path.read_bytes():
            raise Scene3dInputError("camera interaction did not change the rendered image")
        return {
            **report,
            "passed": True,
            "poster_unique_colors": images[0]["unique_colors"],
            "poster_channel_variance": images[0]["channel_variance"],
            "images": images,
            "html_bytes": html_path.stat().st_size,
            "specification_bytes": spec_path.stat().st_size,
        }

    def _number_list(self, raw: Any, name: str, minimum: int, maximum: int) -> list[float]:
        if not isinstance(raw, list) or not minimum <= len(raw) <= maximum:
            raise Scene3dInputError(f"{name} must contain {minimum} to {maximum} values")
        return [self._finite(value, name) for value in raw]

    def _vector3(self, raw: Any, name: str) -> list[float]:
        if not isinstance(raw, list) or len(raw) != 3:
            raise Scene3dInputError(f"{name} must contain exactly three values")
        return [self._finite(value, name) for value in raw]

    def _bounded(self, raw: Any, name: str, minimum: float, maximum: float) -> float:
        value = self._finite(raw, name)
        if not minimum <= value <= maximum:
            raise Scene3dInputError(f"{name} must be from {minimum} to {maximum}")
        return value

    @staticmethod
    def _finite(raw: Any, name: str) -> float:
        if isinstance(raw, bool) or not isinstance(raw, (int, float)) or not math.isfinite(float(raw)):
            raise Scene3dInputError(f"{name} must be finite")
        value = float(raw)
        if abs(value) > 1_000_000:
            raise Scene3dInputError(f"{name} exceeds the bounded numeric range")
        return value

    @staticmethod
    def _safe_text(raw: Any, name: str, minimum: int, maximum: int) -> str:
        value = Scene3dAdapter._text(raw, name, minimum, maximum)
        if any(character in value for character in ("<", ">", "`", "\x00")):
            raise Scene3dInputError(f"{name} contains unsafe markup")
        return value

    @staticmethod
    def _text(raw: Any, name: str, minimum: int, maximum: int) -> str:
        if not isinstance(raw, str) or not minimum <= len(raw.strip()) <= maximum:
            raise Scene3dInputError(f"{name} must contain {minimum} to {maximum} characters")
        return raw.strip()

    @staticmethod
    def _integer(raw: Any, name: str, minimum: int, maximum: int) -> int:
        if isinstance(raw, bool) or not isinstance(raw, int) or not minimum <= raw <= maximum:
            raise Scene3dInputError(f"{name} must be an integer from {minimum} to {maximum}")
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
