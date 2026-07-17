from __future__ import annotations

import pytest

from app.classroom.authoring import (
    ClassroomAuthoringService,
    ClassroomValidationError,
)
from app.classroom.idempotency import IdempotencyConflictError, IdempotencyLedger
from app.classroom.models import ClassroomPackage
from app.classroom.repository import ClassroomRepository
from classroom_fixtures import classroom_package_payload


def service(tmp_path) -> ClassroomAuthoringService:
    repository = ClassroomRepository(tmp_path)
    ledger = IdempotencyLedger(tmp_path / "operations")
    return ClassroomAuthoringService(repository, ledger)


def test_repeated_create_with_same_key_returns_same_receipt(tmp_path) -> None:
    authoring = service(tmp_path)
    package = ClassroomPackage.model_validate(classroom_package_payload())

    first = authoring.create_draft("limits", package, idempotency_key="create-1")
    second = authoring.create_draft("limits", package, idempotency_key="create-1")

    assert first == second
    assert first["revision"] == 1


def test_reusing_key_with_different_request_is_rejected(tmp_path) -> None:
    authoring = service(tmp_path)
    package = ClassroomPackage.model_validate(classroom_package_payload())
    authoring.create_draft("limits", package, idempotency_key="create-1")
    changed = package.model_copy(update={"title": "不同请求"})

    with pytest.raises(IdempotencyConflictError):
        authoring.create_draft("limits", changed, idempotency_key="create-1")


def test_invalid_cross_object_package_cannot_publish(tmp_path) -> None:
    authoring = service(tmp_path)
    payload = classroom_package_payload()
    payload["courses"][0]["chapters"][0]["relations"] = [
        {
            "id": "broken-relation",
            "kind": "contrast",
            "source_module_id": "limit-core",
            "target_module_id": "missing",
        }
    ]
    package = ClassroomPackage.model_validate(payload)
    authoring.create_draft("limits", package, idempotency_key="create-1")

    with pytest.raises(ClassroomValidationError) as exc:
        authoring.publish("limits", 1, idempotency_key="publish-1")

    assert exc.value.report.issues[0].code == "unknown_relation_target"


def test_publish_and_rollback_return_explicit_receipts(tmp_path) -> None:
    authoring = service(tmp_path)
    package = ClassroomPackage.model_validate(classroom_package_payload())
    authoring.create_draft("limits", package, idempotency_key="create-1")
    published = authoring.publish("limits", 1, idempotency_key="publish-1")

    rolled_back = authoring.rollback(
        package.package_id,
        published["active_version"],
        idempotency_key="rollback-1",
    )

    assert published["action"] == "publish"
    assert rolled_back["action"] == "rollback"
    assert rolled_back["active_version"] == published["active_version"]
