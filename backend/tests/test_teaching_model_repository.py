from __future__ import annotations

import json

import pytest

from app.classroom.model_contracts import (
    PreviewJobRecord,
    TeachingModelManifest,
    model_version,
)
from app.classroom.model_repository import (
    ModelConflictError,
    ModelNotFoundError,
    TeachingModelRepository,
)
from test_teaching_model_contracts import manifest_payload, source


def manifest() -> TeachingModelManifest:
    return TeachingModelManifest.model_validate(manifest_payload())


def preview_job(content_hash: str, *, status: str = "succeeded") -> PreviewJobRecord:
    return PreviewJobRecord(
        job_id="preview-1",
        draft_id="limit-draft",
        draft_revision=1,
        draft_content_hash=content_hash,
        model_id="limit-neighborhood-2d",
        scenario_id="approach-target",
        viewport={"width": 1280, "height": 800},
        status=status,
        report={"uncaught_errors": [], "resources_after_dispose": 0},
    )


def test_draft_create_and_revision_checked_update_are_atomic(tmp_path) -> None:
    repository = TeachingModelRepository(tmp_path)
    created = repository.create_draft("limit-draft", manifest(), source())
    changed_source = f"{source()}\n// revision two"

    updated = repository.update_draft(
        "limit-draft",
        expected_revision=1,
        manifest=manifest(),
        source=changed_source,
    )

    assert created.revision == 1
    assert updated.revision == 2
    assert repository.get_draft("limit-draft").source == changed_source
    persisted = json.loads(
        (tmp_path / "model-drafts" / "limit-draft.json").read_text(encoding="utf-8")
    )
    assert persisted["revision"] == 2

    with pytest.raises(ModelConflictError, match="expected revision 1"):
        repository.update_draft(
            "limit-draft",
            expected_revision=1,
            manifest=manifest(),
            source=source(),
        )


def test_repository_rejects_unsafe_ids_and_missing_records(tmp_path) -> None:
    repository = TeachingModelRepository(tmp_path)

    with pytest.raises(ValueError, match="safe"):
        repository.create_draft("../escape", manifest(), source())
    with pytest.raises(ModelNotFoundError):
        repository.get_draft("missing")


def test_registration_is_immutable_and_repeatable_for_same_content(tmp_path) -> None:
    repository = TeachingModelRepository(tmp_path)
    draft = repository.create_draft("limit-draft", manifest(), source())
    expected_version = model_version(draft.manifest, draft.source)

    registered = repository.register(
        draft,
        validation={"passed": True, "issues": []},
        preview_job_id="preview-1",
    )
    repeated = repository.register(
        draft,
        validation={"passed": True, "issues": []},
        preview_job_id="preview-1",
    )

    assert registered.version == expected_version
    assert repeated == registered
    assert repository.get_registered(draft.manifest.model_id, expected_version) == registered
    assert repository.list_registered()[0].version == expected_version


def test_checked_in_seed_is_read_as_an_immutable_registered_version(tmp_path) -> None:
    seed_root = tmp_path / "seed"
    model_root = seed_root / "limit-neighborhood-2d"
    model_root.mkdir(parents=True)
    (model_root / "manifest.json").write_text(
        json.dumps(manifest_payload(), ensure_ascii=False),
        encoding="utf-8",
    )
    (model_root / "source.js").write_text(source(), encoding="utf-8")
    repository = TeachingModelRepository(tmp_path / "local", seed_root=seed_root)
    expected_version = model_version(manifest(), source())

    record = repository.get_registered("limit-neighborhood-2d", expected_version)

    assert record.version == expected_version
    assert record.preview_job_id == "checked-in-seed"
    assert repository.list_registered()[0].model_id == "limit-neighborhood-2d"


def test_preview_jobs_are_durable_and_match_the_exact_draft_hash(tmp_path) -> None:
    repository = TeachingModelRepository(tmp_path)
    draft = repository.create_draft("limit-draft", manifest(), source())
    job = preview_job(draft.content_hash)

    repository.put_preview_job(job)

    assert repository.get_preview_job(job.job_id) == job
    assert repository.find_successful_preview(draft.content_hash) == job
    assert repository.find_successful_preview("sha256:different") is None
    assert repository.artifact_path(job.job_id, "screenshot.png").parent.name == job.job_id

    with pytest.raises(ValueError, match="safe"):
        repository.artifact_path(job.job_id, "../secret")
