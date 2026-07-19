from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

try:
    from tools.bootstrap_ai_classroom import bootstrap
except ModuleNotFoundError:
    from bootstrap_ai_classroom import bootstrap


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def generate(output_root: Path) -> dict:
    root = Path(__file__).resolve().parents[1]
    output_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ai-classroom-runtime-") as temporary:
        data_root = Path(temporary)
        bootstrap(
            data_root,
            seed_package_path=root
            / "backend"
            / "classroom_data"
            / "seed"
            / "calculus-foundations.json",
            model_seed_root=root / "backend" / "classroom_data" / "model_seed",
        )
        port = free_port()
        environment = os.environ.copy()
        environment.update(
            {
                "APP_PROFILE": "mixed",
                "CLASSROOM_DATA_ROOT": str(data_root),
                "PYTHONPATH": str(root / "backend"),
                "STUDIO_API_KEY": "browser-evidence-placeholder-secret",
            }
        )
        server = subprocess.Popen(
            [
                os.environ.get("PYTHON_EXECUTABLE", "python"),
                "-m",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                "backend",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=root,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        try:
            health = f"http://127.0.0.1:{port}/health"
            for _ in range(80):
                try:
                    with urllib.request.urlopen(health, timeout=0.5):
                        break
                except Exception:
                    if server.poll() is not None:
                        raise RuntimeError(server.stderr.read())
                    time.sleep(0.1)
            else:
                raise RuntimeError("classroom server did not become ready")
            node = os.environ.get("MODEL_PREVIEW_NODE", "node")
            completed = subprocess.run(
                [
                    node,
                    str(root / "tools" / "capture_cosmic_classroom.cjs"),
                    f"http://127.0.0.1:{port}",
                    str(output_root),
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=60,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr or completed.stdout)
            return json.loads(completed.stdout)
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-root",
        type=Path,
        default=root / "docs" / "preview-artifacts" / "project-c",
    )
    args = parser.parse_args()
    print(json.dumps(generate(args.output_root), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
