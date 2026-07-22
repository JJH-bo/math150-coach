from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
TERMINAL_STATES = {"succeeded", "failed", "cancelled"}


def request_json(
    url: str,
    *,
    studio_key: str | None = None,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    headers = {"Accept": "application/json"}
    if studio_key is not None:
        headers["Authorization"] = f"Bearer {studio_key}"
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    body = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, headers=headers, method=method)
    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def request_bytes(url: str, *, studio_key: str) -> bytes:
    request = Request(
        url,
        headers={"Authorization": f"Bearer {studio_key}"},
    )
    with urlopen(request, timeout=20) as response:
        return response.read()


def submit_and_wait(
    origin: str,
    studio_key: str,
    *,
    idempotency_key: str,
    tool_id: str,
    arguments: dict[str, Any],
    timeout_seconds: float = 30,
) -> dict[str, Any]:
    submitted = request_json(
        f"{origin}/api/studio/v1/tool-jobs",
        studio_key=studio_key,
        method="POST",
        idempotency_key=idempotency_key,
        payload={"tool_id": tool_id, "arguments": arguments},
    )
    job = submitted
    deadline = time.monotonic() + timeout_seconds
    while job["state"] not in TERMINAL_STATES:
        if time.monotonic() >= deadline:
            raise RuntimeError(f"{tool_id} evidence job did not reach a terminal state")
        time.sleep(0.05)
        job = request_json(
            f"{origin}/api/studio/v1/tool-jobs/{submitted['job_id']}",
            studio_key=studio_key,
        )
    if job["state"] != "succeeded":
        raise RuntimeError(f"{tool_id} evidence job failed: {job.get('error')}")
    return job


def download_artifacts(
    origin: str,
    studio_key: str,
    job: dict[str, Any],
) -> dict[str, bytes]:
    downloaded: dict[str, bytes] = {}
    for artifact in job["artifacts"]:
        content = request_bytes(
            f"{origin}{artifact['download_path']}",
            studio_key=studio_key,
        )
        if len(content) != artifact["size_bytes"]:
            raise RuntimeError(f"artifact size mismatch: {artifact['name']}")
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        if digest != artifact["sha256"]:
            raise RuntimeError(f"artifact hash mismatch: {artifact['name']}")
        downloaded[artifact["name"]] = content
    return downloaded


def configured_browser() -> str | None:
    candidates = [
        os.getenv("MODEL_PREVIEW_BROWSER"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/usr/bin/chromium",
        "/usr/bin/google-chrome",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate))
    return None


def wait_until_ready(origin: str, process: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + 20
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"temporary server exited with code {process.returncode}")
        try:
            health = request_json(f"{origin}/health")
            if health.get("status") == "ok":
                return
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
        time.sleep(0.1)
    raise RuntimeError(f"temporary server did not become ready: {last_error}")


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def lesson_payload() -> dict[str, Any]:
    return {
        "schema_version": "semantic_lesson_v1",
        "title": "Limits describe controlled approach",
        "subtitle": "A visual introduction to local behavior",
        "audience": "First-year calculus learners meeting limits for the first time",
        "learning_objective": (
            "Explain a finite limit using neighborhoods and distinguish approach "
            "behavior from the function value at the target."
        ),
        "central_takeaway": (
            "A limit is a claim about values arbitrarily near a target, supported "
            "by a controllable input-output neighborhood relationship."
        ),
        "opening_question": "How can a function approach one value without reaching it?",
        "closing_resolution": (
            "The neighborhood relationship makes approach precise while leaving the "
            "value at the target logically separate."
        ),
        "narrative_arc": "learning_progression",
        "template": "concept_journey",
        "slides": [
            {
                "slide_id": "opening",
                "kind": "opening",
                "title": "A function can approach a value it never reaches",
                "narrative_job": "Create the need for a language of controlled approach.",
                "primary_claim": "Nearness, not arrival, is the phenomenon we need to describe.",
                "body": [
                    "Watch the inputs move toward the target while the outputs settle near one value."
                ],
                "speaker_notes": "Invite learners to describe what remains stable during approach.",
            },
            {
                "slide_id": "neighborhoods",
                "kind": "concept",
                "title": "Two linked neighborhoods make approach measurable",
                "narrative_job": "Replace informal motion language with a controllable relationship.",
                "primary_claim": "A chosen output tolerance determines how close inputs must be.",
                "bullets": [
                    "The output band is centered on the proposed limit.",
                    "The input band is centered on the target.",
                    "Every permitted input must land inside the output band.",
                ],
                "formula": "0 < |x-a| < \\delta \\Rightarrow |f(x)-L| < \\varepsilon",
                "speaker_notes": "Name every symbol before reading the implication aloud.",
            },
            {
                "slide_id": "worked-check",
                "kind": "example",
                "title": "For a line, the needed input band follows directly",
                "narrative_job": "Demonstrate the control relationship without skipping algebra.",
                "primary_claim": "For f(x)=2x+1 near x=3, choosing delta=epsilon/2 is sufficient.",
                "bullets": [
                    "Start from the output error |(2x+1)-7|.",
                    "Factor it as 2|x-3|.",
                    "Require |x-3| < epsilon/2.",
                ],
                "formula": "|f(x)-7| = 2|x-3| < \\varepsilon",
                "speaker_notes": "Keep the implication direction explicit at each step.",
            },
            {
                "slide_id": "synthesis",
                "kind": "synthesis",
                "title": "The limit records stable local behavior, not a point value",
                "narrative_job": "Resolve the opening question and state the reusable understanding.",
                "primary_claim": "Controlled neighborhoods explain approach even when f(a) differs or is absent.",
                "body": [
                    "You can now test a proposed limit by connecting any requested output tolerance to a sufficient input tolerance."
                ],
                "speaker_notes": "Return to the opening example and separate the hole from the nearby trend.",
            },
        ],
    }


def geometry_payload() -> dict[str, Any]:
    binding_x = {"parameter": "t", "scale": 2, "offset": 0}
    binding_y = {"parameter": "t", "scale": 3, "offset": 0}
    return {
        "title": "Scaling a vector preserves its direction",
        "alt_text": (
            "An interactive coordinate plane showing a reference ray with slope three "
            "halves and a vector whose endpoint is controlled by scale factor t, so its "
            "length changes while every endpoint remains on the same ray."
        ),
        "viewport": {"x_min": -1, "x_max": 5, "y_min": -1, "y_max": 7},
        "width": 1000,
        "height": 650,
        "theme": "dark",
        "parameters": [
            {
                "id": "t",
                "label": "Scale factor t",
                "minimum": 0.5,
                "maximum": 2.0,
                "step": 0.1,
                "value": 1.0,
            }
        ],
        "objects": [
            {
                "id": "reference-ray",
                "type": "polyline",
                "label": "y = 1.5x",
                "color": "#33C3FF",
                "points": [
                    {"x": 0, "y": 0},
                    {"x": 1, "y": 1.5},
                    {"x": 2, "y": 3},
                    {"x": 3, "y": 4.5},
                    {"x": 4, "y": 6},
                ],
            },
            {
                "id": "origin",
                "type": "point",
                "label": "O",
                "color": "#F6C85F",
                "x": 0,
                "y": 0,
            },
            {
                "id": "moving",
                "type": "point",
                "label": "Q(t)",
                "color": "#FF6B8A",
                "x": binding_x,
                "y": binding_y,
            },
            {
                "id": "scaled",
                "type": "vector",
                "label": "scaled vector",
                "color": "#FF6B8A",
                "x": 0,
                "y": 0,
                "dx": binding_x,
                "dy": binding_y,
            },
        ],
    }


def scene3d_payload() -> dict[str, Any]:
    axis = [value / 2 for value in range(-4, 5)]
    return {
        "title": "A saddle bends in opposite directions",
        "alt_text": (
            "An interactive three-dimensional scene of the saddle surface z equals x "
            "squared minus y squared, with colored axes and camera orbit controls that "
            "reveal upward curvature along x and downward curvature along y."
        ),
        "width": 1000,
        "height": 650,
        "theme": "dark",
        "camera": {
            "azimuth": 42,
            "elevation": 28,
            "distance": 16,
            "target": [0, 0, 0],
        },
        "objects": [
            {
                "id": "saddle",
                "type": "surface",
                "label": "z = x² - y²",
                "color": "#33C3FF",
                "opacity": 1.0,
                "x": axis,
                "y": axis,
                "z": [[x * x - y * y for x in axis] for y in axis],
            },
            {
                "id": "normal",
                "type": "vector",
                "label": "normal at the origin",
                "color": "#FF6B8A",
                "origin": [0, 0, 0],
                "direction": [0, 0, 2.5],
            },
            {
                "id": "origin",
                "type": "point",
                "label": "origin",
                "color": "#F6C85F",
                "position": [0, 0, 0],
                "size": 0.16,
            },
        ],
    }


def generate(output_root: Path) -> None:
    studio_key = "temporary-evidence-key-never-serialized"
    port = free_port()
    origin = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="math150-tool-evidence-") as temporary:
        environment = os.environ.copy()
        environment.update(
            {
                "APP_PROFILE": "mixed",
                "CLASSROOM_DATA_ROOT": str(Path(temporary) / "data"),
                "STUDIO_API_KEY": studio_key,
                "AI_CLASSROOM_PUBLIC_ORIGIN": origin,
                "PYTHONPATH": str(ROOT / "backend"),
            }
        )
        browser = configured_browser()
        if browser is not None:
            environment["MODEL_PREVIEW_BROWSER"] = browser
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                "backend",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--log-level",
                "warning",
            ],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait_until_ready(origin, process)
            registry = request_json(
                f"{origin}/api/studio/v1/tools?quality_tier=verified",
                studio_key=studio_key,
            )
            jobs = {}
            jobs["symbolic"] = submit_and_wait(
                origin,
                studio_key,
                idempotency_key="evidence-factor-polynomial-v1",
                tool_id="math.symbolic",
                arguments={
                    "operation": "factor",
                    "expression": "x**2 - 1",
                    "symbols": {"x": {"real": True}},
                },
            )
            jobs["numeric"] = submit_and_wait(
                origin,
                studio_key,
                idempotency_key="evidence-integrate-sine-v1",
                tool_id="math.numeric",
                arguments={
                    "operation": "quadrature",
                    "expression": "sin(x)",
                    "variable": "x",
                    "interval": [0, "pi"],
                    "tolerance": 1e-10,
                },
            )
            jobs["verification"] = submit_and_wait(
                origin,
                studio_key,
                idempotency_key="evidence-trig-identity-v1",
                tool_id="math.verify",
                arguments={
                    "left_expression": "sin(x)**2 + cos(x)**2",
                    "right_expression": "1",
                    "symbols": {"x": {"real": True}},
                    "domains": {"x": [-6.283185307179586, 6.283185307179586]},
                },
            )
            jobs["graph"] = submit_and_wait(
                origin,
                studio_key,
                idempotency_key="evidence-learning-path-v1",
                tool_id="math.graph",
                arguments={
                    "operation": "shortest_path",
                    "directed": True,
                    "weighted": True,
                    "source": "definition",
                    "target": "application",
                    "nodes": [
                        {"id": "definition", "label": "Definition"},
                        {"id": "mechanism", "label": "Mechanism"},
                        {"id": "example", "label": "Worked example"},
                        {"id": "application", "label": "Application"},
                    ],
                    "edges": [
                        {"source": "definition", "target": "mechanism", "weight": 1},
                        {"source": "mechanism", "target": "example", "weight": 1},
                        {"source": "example", "target": "application", "weight": 1},
                        {"source": "definition", "target": "application", "weight": 8},
                    ],
                },
            )
            jobs["plot"] = submit_and_wait(
                origin,
                studio_key,
                idempotency_key="evidence-quadratic-plot-v1",
                tool_id="visualization.plot",
                timeout_seconds=60,
                arguments={
                    "title": "Quadratic growth",
                    "x_label": "Input x",
                    "y_label": "Output x squared",
                    "alt_text": (
                        "A line plot of x squared from negative three to three, "
                        "symmetric around the origin with its minimum at zero."
                    ),
                    "traces": [
                        {
                            "type": "line",
                            "name": "x squared",
                            "x": [-3, -2, -1, 0, 1, 2, 3],
                            "y": [9, 4, 1, 0, 1, 4, 9],
                            "color": "#33C3FF",
                        }
                    ],
                    "width": 800,
                    "height": 520,
                    "theme": "dark",
                },
            )
            jobs["diagram"] = submit_and_wait(
                origin,
                studio_key,
                idempotency_key="evidence-limit-concept-diagram-v1",
                tool_id="visualization.diagram",
                timeout_seconds=60,
                arguments={
                    "title": "From informal approach to a precise limit",
                    "alt_text": (
                        "A left-to-right concept flow from observing nearby values, "
                        "through choosing an output tolerance and a matching input "
                        "tolerance, to a verified finite-limit statement."
                    ),
                    "direction": "LR",
                    "theme": "dark",
                    "width": 1000,
                    "height": 620,
                    "nodes": [
                        {"id": "observe", "label": "Observe nearby values", "shape": "rounded"},
                        {"id": "epsilon", "label": "Choose output tolerance ε"},
                        {"id": "delta", "label": "Find input tolerance δ"},
                        {"id": "verify", "label": "Verify the limit claim", "shape": "stadium"},
                    ],
                    "edges": [
                        {"source": "observe", "target": "epsilon", "label": "focus output"},
                        {"source": "epsilon", "target": "delta", "label": "control input"},
                        {"source": "delta", "target": "verify", "label": "check all points"},
                    ],
                },
            )
            jobs["geometry2d"] = submit_and_wait(
                origin,
                studio_key,
                idempotency_key="evidence-vector-scaling-geometry-v1",
                tool_id="visualization.geometry2d",
                timeout_seconds=60,
                arguments=geometry_payload(),
            )
            jobs["scene3d"] = submit_and_wait(
                origin,
                studio_key,
                idempotency_key="evidence-saddle-scene3d-v1",
                tool_id="visualization.scene3d",
                timeout_seconds=90,
                arguments=scene3d_payload(),
            )
            for format_name, tool_id in (
                ("reveal", "export.reveal"),
                ("pptx", "export.pptx"),
                ("pdf", "export.pdf"),
                ("html", "export.html"),
                ("package", "export.package"),
            ):
                jobs[format_name] = submit_and_wait(
                    origin,
                    studio_key,
                    idempotency_key=f"evidence-semantic-lesson-{format_name}-v1",
                    tool_id=tool_id,
                    arguments=lesson_payload(),
                    timeout_seconds=120,
                )
            artifacts = {
                name: download_artifacts(origin, studio_key, job)
                for name, job in jobs.items()
            }

            export_names = ("reveal", "pptx", "pdf", "html", "package")
            content_hashes = {
                name: jobs[name]["result"]["content_hash"] for name in export_names
            }
            if len(set(content_hashes.values())) != 1:
                raise RuntimeError(f"cross-format lesson hash mismatch: {content_hashes}")

            action_schema = request_json(
                f"{origin}/api/studio/v1/action-schema.json"
            )
            operation_ids = sorted(
                operation["operationId"]
                for path in action_schema["paths"].values()
                for operation in path.values()
                if isinstance(operation, dict) and "operationId" in operation
            )
            evidence = {
                "tool_protocol_version": "studio_tools_v1",
                "operation_ids": operation_ids,
                "tool_operation_ids": [
                    "cancelStudioToolJob",
                    "getStudioTool",
                    "getStudioToolArtifact",
                    "getStudioToolJob",
                    "listStudioTools",
                    "submitStudioToolJob",
                ],
                "lesson_export_content_hash": next(iter(content_hashes.values())),
                "verified_lesson_exports": list(export_names),
            }
            serialized = json.dumps([registry, jobs, evidence]).lower()
            if studio_key.lower() in serialized or temporary.lower() in serialized:
                raise RuntimeError("evidence contains a secret or temporary path")
            forbidden_bytes = (
                studio_key.lower().encode("utf-8"),
                temporary.lower().encode("utf-8"),
            )
            for format_artifacts in artifacts.values():
                for artifact_name, content in format_artifacts.items():
                    lowered = content.lower()
                    if any(forbidden in lowered for forbidden in forbidden_bytes):
                        raise RuntimeError(
                            f"artifact contains a secret or temporary path: {artifact_name}"
                        )
            write_json(output_root / "tool-registry.json", registry)
            for name, job in jobs.items():
                write_json(output_root / f"{name}-job.json", job)
            write_json(output_root / "openapi-operation-ids.json", evidence)
            write_bytes(output_root / "plot.png", artifacts["plot"]["figure.png"])
            write_bytes(output_root / "plot.svg", artifacts["plot"]["figure.svg"])
            write_bytes(
                output_root / "plot-validation.json",
                artifacts["plot"]["validation.json"],
            )
            for artifact_name, content in artifacts["diagram"].items():
                write_bytes(output_root / "diagram" / artifact_name, content)
            for artifact_name, content in artifacts["geometry2d"].items():
                write_bytes(output_root / "geometry2d" / artifact_name, content)
            for artifact_name, content in artifacts["scene3d"].items():
                write_bytes(output_root / "scene3d" / artifact_name, content)
            for format_name in export_names:
                for artifact_name, content in artifacts[format_name].items():
                    write_bytes(
                        output_root / "lesson-exports" / format_name / artifact_name,
                        content,
                    )
            write_json(
                output_root / "lesson-exports" / "cross-format-report.json",
                {
                    "passed": True,
                    "content_hash": next(iter(content_hashes.values())),
                    "formats": list(export_names),
                },
            )
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT / "docs" / "preview-artifacts" / "tool-platform-core",
    )
    arguments = parser.parse_args()
    generate(arguments.output_root.resolve())


if __name__ == "__main__":
    main()
