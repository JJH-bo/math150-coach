from __future__ import annotations

from pathlib import Path


def test_runtime_dependencies_do_not_use_the_httpx_typo() -> None:
    requirements = {
        line.strip()
        for line in Path("requirements.txt").read_text(
            encoding="utf-8"
        ).splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert "httpx" in requirements
    assert "httpx2" not in requirements


def test_container_runs_the_mixed_fastapi_app_with_a_healthcheck() -> None:
    dockerfile = Path("Dockerfile").read_text(encoding="utf-8")

    assert "uvicorn app.main:app" in dockerfile
    assert "--app-dir backend" in dockerfile
    assert 'APP_PROFILE="mixed"' in dockerfile
    assert "/health" in dockerfile
    assert "USER app" in dockerfile
