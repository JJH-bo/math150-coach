from __future__ import annotations

import base64
import io
from pathlib import Path

import pytest
from PIL import Image

from app.assets.repository import AssetRepository
from app.tools.adapters.asset_images import (
    AssetIngestAdapter,
    AssetToolInputError,
    AssetTransformAdapter,
)
from app.tools.contracts import (
    ToolExecutionContext,
    ToolJob,
    ToolJobState,
    ToolProducedArtifact,
    ToolScope,
)
from app.tools.repository import ToolJobRepository


SOURCE_JOB_ID = "tj-111111111111111111111111"


def png_bytes(*, size: tuple[int, int] = (240, 160)) -> bytes:
    image = Image.new("RGB", size, (240, 248, 252))
    for x in range(size[0] // 4, size[0] * 3 // 4):
        for y in range(size[1] // 4, size[1] * 3 // 4):
            image.putpixel((x, y), (20, 120, 210))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def context(path: Path, *, job_id: str = "tj-222222222222222222222222") -> ToolExecutionContext:
    return ToolExecutionContext(job_id=job_id, work_dir=path)


def succeeded_source_job(repository: ToolJobRepository, data: bytes) -> ToolJob:
    job = ToolJob(
        job_id=SOURCE_JOB_ID,
        tool_id="visualization.plot",
        tool_version="1.0.0",
        required_scope=ToolScope.RENDER,
        state=ToolJobState.QUEUED,
        argument_hash="sha256:" + "0" * 64,
        arguments={},
        created_at="2026-07-22T00:00:00Z",
    )
    repository.create(job)
    source = repository.work_dir(job.job_id) / "figure.png"
    source.write_bytes(data)
    artifact = repository.promote_artifact(
        job.job_id,
        produced=ToolProducedArtifact(
            name="figure.png",
            media_type="image/png",
            source_path="figure.png",
        ),
        max_artifact_bytes=8 * 1024 * 1024,
    )
    return repository.update(
        job.model_copy(
            update={
                "state": ToolJobState.SUCCEEDED,
                "started_at": "2026-07-22T00:00:01Z",
                "finished_at": "2026-07-22T00:00:02Z",
                "result": {"passed": True},
                "artifacts": [artifact],
            }
        )
    )


def test_ingest_upload_and_prior_job_artifact_produce_same_asset(tmp_path) -> None:
    assets = AssetRepository(tmp_path)
    jobs = ToolJobRepository(tmp_path)
    source = png_bytes()
    succeeded_source_job(jobs, source)
    adapter = AssetIngestAdapter(assets, jobs)

    upload = adapter.execute(
        {
            "filename": "curve.png",
            "declared_media_type": "image/png",
            "content_base64": base64.b64encode(source).decode("ascii"),
            "output_format": "png",
            "alt_text": "A blue rectangle centered on a pale background.",
        },
        context(tmp_path / "upload"),
    )
    chained = adapter.execute(
        {
            "filename": "curve.png",
            "source_job_id": SOURCE_JOB_ID,
            "source_artifact_name": "figure.png",
            "output_format": "png",
            "alt_text": "A blue rectangle centered on a pale background.",
        },
        context(tmp_path / "chained", job_id="tj-333333333333333333333333"),
    )

    assert upload.result["asset"]["asset_id"] == chained.result["asset"]["asset_id"]
    assert upload.result["duplicate"] is False
    assert chained.result["duplicate"] is True
    assert upload.result["validation"]["second_decode_verified"] is True
    assert upload.result["validation"]["metadata_removed"] is True
    assert upload.result["asset"]["uri"].startswith("/api/classroom/v1/assets/a-")
    assert {artifact.name for artifact in upload.artifacts} == {
        "asset.png",
        "validation-report.json",
    }


def test_ingest_definition_has_strict_sources_and_author_scope(tmp_path) -> None:
    definition = AssetIngestAdapter(
        AssetRepository(tmp_path), ToolJobRepository(tmp_path)
    ).definition

    assert definition.tool_id == "asset.ingest"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope == ToolScope.AUTHOR
    assert definition.input_schema["additionalProperties"] is False
    assert len(definition.input_schema["oneOf"]) == 2
    assert "image/svg+xml" not in definition.output_media_types


@pytest.mark.parametrize(
    "payload,error",
    [
        (
            {
                "filename": "x.png",
                "declared_media_type": "image/png",
                "content_base64": "not-base64!",
                "output_format": "png",
                "alt_text": "A meaningful image description.",
            },
            "base64",
        ),
        (
            {
                "filename": "x.png",
                "declared_media_type": "image/png",
                "content_base64": base64.b64encode(png_bytes()).decode("ascii"),
                "source_job_id": SOURCE_JOB_ID,
                "source_artifact_name": "figure.png",
                "output_format": "png",
                "alt_text": "A meaningful image description.",
            },
            "exactly one source",
        ),
        (
            {
                "filename": "x.png",
                "source_job_id": SOURCE_JOB_ID,
                "source_artifact_name": "figure.png",
                "output_format": "png",
                "alt_text": "short",
            },
            "alt_text",
        ),
    ],
)
def test_ingest_rejects_invalid_source_contract(tmp_path, payload, error: str) -> None:
    adapter = AssetIngestAdapter(
        AssetRepository(tmp_path), ToolJobRepository(tmp_path)
    )

    with pytest.raises(AssetToolInputError, match=error):
        adapter.execute(payload, context(tmp_path / "work"))


def test_ingest_rejects_unfinished_or_tampered_source_job(tmp_path) -> None:
    assets = AssetRepository(tmp_path)
    jobs = ToolJobRepository(tmp_path)
    source_job = succeeded_source_job(jobs, png_bytes())
    adapter = AssetIngestAdapter(assets, jobs)
    payload = {
        "filename": "plot.png",
        "source_job_id": SOURCE_JOB_ID,
        "source_artifact_name": "figure.png",
        "output_format": "png",
        "alt_text": "A meaningful plot description for learners.",
    }
    jobs.update(source_job.model_copy(update={"state": ToolJobState.RUNNING}))

    with pytest.raises(AssetToolInputError, match="succeeded"):
        adapter.execute(payload, context(tmp_path / "unfinished"))

    jobs.update(source_job)
    jobs.artifact_path(SOURCE_JOB_ID, "figure.png").write_bytes(b"tampered")
    with pytest.raises(AssetToolInputError, match="hash"):
        adapter.execute(payload, context(tmp_path / "tampered"))


def test_transform_creates_bounded_content_addressed_variant(tmp_path) -> None:
    assets = AssetRepository(tmp_path)
    jobs = ToolJobRepository(tmp_path)
    ingest = AssetIngestAdapter(assets, jobs).execute(
        {
            "filename": "source.png",
            "declared_media_type": "image/png",
            "content_base64": base64.b64encode(png_bytes(size=(800, 520))).decode(
                "ascii"
            ),
            "output_format": "png",
            "alt_text": "A centered blue rectangle used as a resize source.",
        },
        context(tmp_path / "ingest"),
    )
    adapter = AssetTransformAdapter(assets)

    output = adapter.execute(
        {
            "asset_id": ingest.result["asset"]["asset_id"],
            "width": 320,
            "height": 180,
            "mode": "cover",
            "output_format": "webp",
            "quality": 88,
            "allow_upscale": False,
            "background": "#ffffff",
        },
        context(tmp_path / "transform", job_id="tj-444444444444444444444444"),
    )

    assert output.result["asset"]["media_type"] == "image/webp"
    assert output.result["asset"]["width"] == 320
    assert output.result["asset"]["height"] == 180
    assert output.result["source_asset_id"] == ingest.result["asset"]["asset_id"]
    assert output.result["asset"]["asset_id"] != output.result["source_asset_id"]
    assert output.result["validation"]["resampling"] == "lanczos"
    assert adapter.definition.required_scope == ToolScope.RENDER


def test_transform_rejects_unknown_asset_and_unsafe_fields(tmp_path) -> None:
    adapter = AssetTransformAdapter(AssetRepository(tmp_path))

    with pytest.raises(AssetToolInputError, match="not found"):
        adapter.execute(
            {
                "asset_id": "a-" + "1" * 64,
                "width": 320,
                "height": 180,
                "mode": "contain",
                "output_format": "png",
                "quality": 90,
                "allow_upscale": False,
                "background": "#ffffff",
            },
            context(tmp_path / "missing"),
        )
    with pytest.raises(AssetToolInputError, match="unsupported"):
        adapter.execute(
            {
                "asset_id": "a-" + "1" * 64,
                "width": 320,
                "height": 180,
                "mode": "contain",
                "output_format": "png",
                "quality": 90,
                "allow_upscale": False,
                "background": "#ffffff",
                "host_path": "C:/secrets/image.png",
            },
            context(tmp_path / "unsafe"),
        )
