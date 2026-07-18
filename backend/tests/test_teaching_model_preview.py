from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from app.classroom.model_contracts import TeachingModelManifest
from app.classroom.model_repository import TeachingModelRepository
from app.classroom.preview import TeachingModelPreviewService
from test_teaching_model_contracts import manifest_payload, source


PNG = b"\x89PNG\r\n\x1a\nfake"


def draft(repository: TeachingModelRepository):
    return repository.create_draft(
        "limit-draft",
        TeachingModelManifest.model_validate(manifest_payload()),
        source(),
    )


def fake_runner(request_path: Path, artifact_dir: Path) -> dict:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    (artifact_dir / "screenshot.png").write_bytes(PNG)
    return {
        "uncaught_errors": [],
        "resources_before_dispose": {"frames": 0, "listeners": 0},
        "resources_after_dispose": 0,
        "snapshot": {"state": "approach"},
        "viewport": request["viewport"],
    }


def test_preview_job_is_durable_and_produces_artifacts(tmp_path) -> None:
    repository = TeachingModelRepository(tmp_path)
    record = draft(repository)
    service = TeachingModelPreviewService(repository, runner=fake_runner)

    queued = service.request_preview(
        record.draft_id,
        scenario_id="approach-target",
        viewport={"width": 1280, "height": 800},
    )
    succeeded = service.run_preview(queued.job_id)

    assert queued.status == "queued"
    assert succeeded.status == "succeeded"
    assert succeeded.draft_content_hash == record.content_hash
    assert {artifact.name for artifact in succeeded.artifacts} >= {
        "request.json",
        "preview.html",
        "report.json",
        "screenshot.png",
    }
    assert service.artifact(queued.job_id, "screenshot.png").read_bytes() == PNG
    assert repository.find_successful_preview(record.content_hash) == succeeded


def test_preview_failure_is_structured_and_retryable(tmp_path) -> None:
    repository = TeachingModelRepository(tmp_path)
    record = draft(repository)

    def failing_runner(request_path: Path, artifact_dir: Path) -> dict:
        raise FileNotFoundError("browser executable missing")

    service = TeachingModelPreviewService(repository, runner=failing_runner)
    job = service.request_preview(
        record.draft_id,
        scenario_id="approach-target",
        viewport={"width": 390, "height": 844},
    )

    failed = service.run_preview(job.job_id)

    assert failed.status == "failed"
    assert failed.error.code == "preview_environment_unavailable"
    assert failed.error.retryable is True


def test_preview_rejects_unknown_scenario(tmp_path) -> None:
    repository = TeachingModelRepository(tmp_path)
    record = draft(repository)
    service = TeachingModelPreviewService(repository, runner=fake_runner)

    with pytest.raises(ValueError, match="scenario"):
        service.request_preview(
            record.draft_id,
            scenario_id="missing",
            viewport={"width": 1280, "height": 800},
        )


@pytest.mark.skipif(
    not all(
        os.getenv(name)
        for name in ("MODEL_PREVIEW_NODE", "NODE_PATH", "MODEL_PREVIEW_BROWSER")
    ),
    reason="real preview environment is not configured",
)
def test_real_browser_preview_has_png_and_clean_disposal(tmp_path) -> None:
    seed_root = Path(__file__).resolve().parents[1] / "classroom_data" / "model_seed"
    manifest = TeachingModelManifest.model_validate(
        json.loads(
            (seed_root / "limit-neighborhood-2d" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
    )
    source_text = (
        seed_root / "limit-neighborhood-2d" / "source.js"
    ).read_text(encoding="utf-8")
    repository = TeachingModelRepository(tmp_path)
    record = repository.create_draft("limit-real", manifest, source_text)
    service = TeachingModelPreviewService(repository)
    job = service.request_preview(
        record.draft_id,
        scenario_id="approach-target",
        viewport={"width": 1280, "height": 800},
    )

    result = service.run_preview(job.job_id)

    assert result.status == "succeeded", result.error
    assert service.artifact(job.job_id, "screenshot.png").read_bytes().startswith(
        b"\x89PNG"
    )
    assert result.report["viewport"]["width"] == 1280
    assert result.report["resources_after_dispose"] == 0
