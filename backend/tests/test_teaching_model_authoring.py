from __future__ import annotations

import pytest

from app.classroom.idempotency import IdempotencyConflictError, IdempotencyLedger
from app.classroom.model_authoring import (
    ModelRegistrationError,
    TeachingModelAuthoringService,
)
from app.classroom.model_contracts import (
    PreviewJobRecord,
    TeachingModelManifest,
)
from app.classroom.model_repository import (
    ModelConflictError,
    TeachingModelRepository,
)
from app.classroom.model_validation import TeachingModelValidator
from test_teaching_model_contracts import manifest_payload, source


def service(tmp_path) -> TeachingModelAuthoringService:
    repository = TeachingModelRepository(tmp_path)
    return TeachingModelAuthoringService(
        repository,
        IdempotencyLedger(tmp_path / "operations"),
    )


def manifest() -> TeachingModelManifest:
    return TeachingModelManifest.model_validate(manifest_payload())


def successful_preview(
    draft,
    *,
    resources_after_dispose: int = 0,
    uncaught_errors: list[str] | None = None,
) -> PreviewJobRecord:
    return PreviewJobRecord(
        job_id="preview-1",
        draft_id=draft.draft_id,
        draft_revision=draft.revision,
        draft_content_hash=draft.content_hash,
        model_id=draft.manifest.model_id,
        scenario_id="approach-target",
        viewport={"width": 1280, "height": 800},
        status="succeeded",
        report={
            "uncaught_errors": uncaught_errors or [],
            "resources_after_dispose": resources_after_dispose,
            "snapshot": {"state": "approach"},
        },
    )


def test_validator_checks_lifecycle_and_forbidden_server_capabilities() -> None:
    validator = TeachingModelValidator()

    missing = validator.validate(manifest(), "export function createTeachingModel() {}")
    forbidden = validator.validate(manifest(), f"{source()}\nprocess.exit(1)")

    assert missing.passed is False
    assert {issue.code for issue in missing.issues} >= {
        "missing_lifecycle_method",
    }
    assert forbidden.passed is False
    assert forbidden.issues[0].code == "forbidden_model_source_capability"


def test_validator_checks_scenario_vocabulary() -> None:
    payload = manifest_payload()
    payload["scenarios"][0]["initial_state"] = "missing-state"
    payload["scenarios"][0]["commands"][1]["target"] = "missing-action"

    report = TeachingModelValidator().validate(
        TeachingModelManifest.model_validate(payload),
        source(),
    )

    assert {issue.code for issue in report.issues} == {
        "unknown_scenario_action",
        "unknown_scenario_state",
    }


def test_model_draft_mutations_are_idempotent_and_revision_checked(tmp_path) -> None:
    authoring = service(tmp_path)

    first = authoring.create_draft(
        "limit-draft",
        manifest(),
        source(),
        idempotency_key="create-1",
    )
    repeated = authoring.create_draft(
        "limit-draft",
        manifest(),
        source(),
        idempotency_key="create-1",
    )

    assert first == repeated
    with pytest.raises(IdempotencyConflictError):
        authoring.create_draft(
            "limit-draft",
            manifest(),
            f"{source()}\n// different",
            idempotency_key="create-1",
        )
    with pytest.raises(ModelConflictError):
        authoring.update_draft(
            "limit-draft",
            expected_revision=9,
            manifest=manifest(),
            source=source(),
            idempotency_key="update-1",
        )


def test_registration_requires_matching_successful_preview(tmp_path) -> None:
    authoring = service(tmp_path)
    authoring.create_draft(
        "limit-draft",
        manifest(),
        source(),
        idempotency_key="create-1",
    )

    with pytest.raises(ModelRegistrationError, match="successful preview"):
        authoring.register(
            "limit-draft",
            expected_revision=1,
            idempotency_key="register-1",
        )


@pytest.mark.parametrize(
    ("resources", "errors", "message"),
    [
        (1, [], "leaked tracked resources"),
        (0, ["boom"], "uncaught runtime errors"),
    ],
)
def test_registration_rejects_preview_runtime_failures(
    tmp_path,
    resources: int,
    errors: list[str],
    message: str,
) -> None:
    authoring = service(tmp_path)
    authoring.create_draft(
        "limit-draft",
        manifest(),
        source(),
        idempotency_key="create-1",
    )
    draft = authoring.repository.get_draft("limit-draft")
    authoring.repository.put_preview_job(
        successful_preview(
            draft,
            resources_after_dispose=resources,
            uncaught_errors=errors,
        )
    )

    with pytest.raises(ModelRegistrationError, match=message):
        authoring.register(
            "limit-draft",
            expected_revision=1,
            idempotency_key="register-1",
        )


def test_validated_previewed_model_registers_immutable_version(tmp_path) -> None:
    authoring = service(tmp_path)
    created = authoring.create_draft(
        "limit-draft",
        manifest(),
        source(),
        idempotency_key="create-1",
    )
    draft = authoring.repository.get_draft("limit-draft")
    authoring.repository.put_preview_job(successful_preview(draft))

    registered = authoring.register(
        "limit-draft",
        expected_revision=created["revision"],
        idempotency_key="register-1",
    )
    repeated = authoring.register(
        "limit-draft",
        expected_revision=created["revision"],
        idempotency_key="register-1",
    )

    assert registered == repeated
    assert registered["version"].startswith("m-")
    assert registered["preview_job_id"] == "preview-1"
