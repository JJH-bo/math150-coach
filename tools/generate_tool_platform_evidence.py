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
            artifacts = {
                name: download_artifacts(origin, studio_key, job)
                for name, job in jobs.items()
            }

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
            }
            serialized = json.dumps([registry, jobs, evidence]).lower()
            if studio_key.lower() in serialized or temporary.lower() in serialized:
                raise RuntimeError("evidence contains a secret or temporary path")
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
