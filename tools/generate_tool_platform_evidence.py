from __future__ import annotations

import argparse
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
            submitted = request_json(
                f"{origin}/api/studio/v1/tool-jobs",
                studio_key=studio_key,
                method="POST",
                idempotency_key="evidence-factor-polynomial-v1",
                payload={
                    "tool_id": "math.symbolic",
                    "arguments": {
                        "operation": "factor",
                        "expression": "x**2 - 1",
                        "symbols": {"x": {"real": True}},
                    },
                },
            )
            job = submitted
            deadline = time.monotonic() + 20
            while job["state"] not in TERMINAL_STATES:
                if time.monotonic() >= deadline:
                    raise RuntimeError("symbolic evidence job did not reach a terminal state")
                time.sleep(0.05)
                job = request_json(
                    f"{origin}/api/studio/v1/tool-jobs/{submitted['job_id']}",
                    studio_key=studio_key,
                )
            if job["state"] != "succeeded":
                raise RuntimeError(f"symbolic evidence job failed: {job.get('error')}")
            for artifact in job["artifacts"]:
                request = Request(
                    f"{origin}{artifact['download_path']}",
                    headers={"Authorization": f"Bearer {studio_key}"},
                )
                with urlopen(request, timeout=10) as response:
                    content = response.read()
                if len(content) != artifact["size_bytes"]:
                    raise RuntimeError(f"artifact size mismatch: {artifact['name']}")

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
            serialized = json.dumps([registry, job, evidence]).lower()
            if studio_key.lower() in serialized or temporary.lower() in serialized:
                raise RuntimeError("evidence contains a secret or temporary path")
            write_json(output_root / "tool-registry.json", registry)
            write_json(output_root / "symbolic-job.json", job)
            write_json(output_root / "openapi-operation-ids.json", evidence)
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
