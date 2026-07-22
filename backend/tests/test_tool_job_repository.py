from __future__ import annotations

from pathlib import Path

import pytest

from app.tools.contracts import (
    ToolJob,
    ToolJobState,
    ToolProducedArtifact,
    ToolScope,
)
from app.tools.repository import (
    ToolArtifactConflictError,
    ToolArtifactLimitError,
    ToolJobNotFoundError,
    ToolJobRepository,
    ToolPathError,
)


def job(job_id: str = "tj-0123456789abcdef01234567") -> ToolJob:
    return ToolJob(
        job_id=job_id,
        tool_id="math.symbolic",
        tool_version="1.0.0",
        required_scope=ToolScope.COMPUTE,
        state=ToolJobState.QUEUED,
        argument_hash=f"sha256:{'a' * 64}",
        arguments={"expression": "x + x"},
        created_at="2026-07-22T00:00:00Z",
    )


def test_repository_creates_and_reads_atomic_job_record(tmp_path: Path) -> None:
    repository = ToolJobRepository(tmp_path)

    created = repository.create(job())
    loaded = repository.get(created.job_id)

    assert loaded == created
    assert (tmp_path / "tool-jobs" / created.job_id / "job.json").is_file()
    assert not list(tmp_path.rglob("*.tmp"))


def test_repository_updates_state_without_changing_job_identity(tmp_path: Path) -> None:
    repository = ToolJobRepository(tmp_path)
    created = repository.create(job())

    updated = repository.update(
        created.model_copy(
            update={
                "state": ToolJobState.RUNNING,
                "started_at": "2026-07-22T00:00:01Z",
            }
        )
    )

    assert updated.state == ToolJobState.RUNNING
    assert repository.get(created.job_id).tool_id == "math.symbolic"


def test_repository_marks_cancellation_request_durably(tmp_path: Path) -> None:
    repository = ToolJobRepository(tmp_path)
    repository.create(job())

    cancelled = repository.request_cancel("tj-0123456789abcdef01234567")

    assert cancelled.cancellation_requested is True
    assert repository.get(cancelled.job_id).cancellation_requested is True


def test_repository_reports_unknown_job(tmp_path: Path) -> None:
    repository = ToolJobRepository(tmp_path)

    with pytest.raises(ToolJobNotFoundError, match="tj-ffffffffffffffffffffffff"):
        repository.get("tj-ffffffffffffffffffffffff")


def test_repository_promotes_hash_addressed_artifact(tmp_path: Path) -> None:
    repository = ToolJobRepository(tmp_path)
    repository.create(job())
    source = repository.work_dir("tj-0123456789abcdef01234567") / "result.txt"
    source.write_bytes(b"2*x\n")

    artifact = repository.promote_artifact(
        "tj-0123456789abcdef01234567",
        ToolProducedArtifact(
            name="result.txt",
            media_type="text/plain; charset=utf-8",
            source_path="result.txt",
        ),
        max_artifact_bytes=100,
    )

    assert artifact.size_bytes == 4
    assert artifact.sha256.startswith("sha256:")
    assert artifact.download_path.endswith("/artifacts/result.txt")
    assert repository.artifact_path(
        artifact.download_path.split("/")[-3], artifact.name
    ).read_bytes() == b"2*x\n"


def test_repository_rejects_source_path_escape(tmp_path: Path) -> None:
    repository = ToolJobRepository(tmp_path)
    repository.create(job())
    (tmp_path / "escape.txt").write_text("secret", encoding="utf-8")

    with pytest.raises(ToolPathError, match="work directory"):
        repository.promote_artifact(
            "tj-0123456789abcdef01234567",
            ToolProducedArtifact(
                name="escape.txt",
                media_type="text/plain",
                source_path="../../../escape.txt",
            ),
            max_artifact_bytes=100,
        )


def test_repository_rejects_artifact_over_limit(tmp_path: Path) -> None:
    repository = ToolJobRepository(tmp_path)
    repository.create(job())
    source = repository.work_dir("tj-0123456789abcdef01234567") / "large.bin"
    source.write_bytes(b"x" * 11)

    with pytest.raises(ToolArtifactLimitError, match="11"):
        repository.promote_artifact(
            "tj-0123456789abcdef01234567",
            ToolProducedArtifact(
                name="large.bin",
                media_type="application/octet-stream",
                source_path="large.bin",
            ),
            max_artifact_bytes=10,
        )


def test_repository_rejects_replacing_immutable_artifact(tmp_path: Path) -> None:
    repository = ToolJobRepository(tmp_path)
    repository.create(job())
    source = repository.work_dir("tj-0123456789abcdef01234567") / "result.txt"
    source.write_text("first", encoding="utf-8")
    produced = ToolProducedArtifact(
        name="result.txt",
        media_type="text/plain",
        source_path="result.txt",
    )
    repository.promote_artifact(
        "tj-0123456789abcdef01234567",
        produced,
        max_artifact_bytes=100,
    )
    source.write_text("second", encoding="utf-8")

    with pytest.raises(ToolArtifactConflictError, match="result.txt"):
        repository.promote_artifact(
            "tj-0123456789abcdef01234567",
            produced,
            max_artifact_bytes=100,
        )
