from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.studio.v1.router import create_studio_router
from app.classroom.authoring import ClassroomAuthoringService
from app.classroom.idempotency import IdempotencyLedger
from app.classroom.model_repository import TeachingModelRepository
from app.classroom.repository import ClassroomRepository
from classroom_fixtures import classroom_package_payload


def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("STUDIO_API_KEY", "studio-test-key")
    model_seed = Path(__file__).resolve().parents[1] / "classroom_data" / "model_seed"
    service = ClassroomAuthoringService(
        ClassroomRepository(tmp_path),
        IdempotencyLedger(tmp_path / "operations"),
        model_repository=TeachingModelRepository(
            tmp_path,
            seed_root=model_seed,
        ),
    )
    app = FastAPI()
    app.include_router(create_studio_router(lambda: service))
    return TestClient(app)


def headers(key: str = "studio-test-key", operation: str = "operation-1") -> dict:
    return {
        "Authorization": f"Bearer {key}",
        "Idempotency-Key": operation,
    }


def test_studio_rejects_missing_and_invalid_bearer_key(tmp_path, monkeypatch) -> None:
    studio = client(tmp_path, monkeypatch)

    assert studio.get("/api/studio/v1/capabilities").status_code == 401
    assert studio.get(
        "/api/studio/v1/capabilities",
        headers={"Authorization": "Bearer wrong"},
    ).status_code == 401


def test_capabilities_describe_free_modules_and_no_analysis_systems(
    tmp_path, monkeypatch
) -> None:
    response = client(tmp_path, monkeypatch).get(
        "/api/studio/v1/capabilities",
        headers=headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "classroom_package_v1"
    assert payload["module_structure"] == "free_composition"
    assert "formula_explanation" in payload["content_block_kinds"]
    assert payload["learner_analysis_capabilities"] == []


def test_workspace_discovers_existing_authoring_targets(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv(
        "AI_CLASSROOM_PUBLIC_ORIGIN",
        "https://classroom.example/",
    )
    studio = client(tmp_path, monkeypatch)
    studio.post(
        "/api/studio/v1/drafts",
        headers=headers(operation="create-workspace-draft"),
        json={"draft_id": "limits", "package": classroom_package_payload()},
    )
    studio.post(
        "/api/studio/v1/drafts/limits/publish",
        headers=headers(operation="publish-workspace-draft"),
        json={"expected_revision": 1},
    )

    response = studio.get(
        "/api/studio/v1/workspace",
        headers={"Authorization": "Bearer studio-test-key"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["public_origin"] == "https://classroom.example"
    assert payload["learner_entry_url"] == "https://classroom.example/classroom/"
    assert payload["active_packages"][0]["package_id"] == "calculus-foundations"
    assert payload["active_packages"][0]["courses"][0]["chapters"][0][
        "modules"
    ][0]["id"] == "limit-core"
    assert payload["drafts"][0]["draft_id"] == "limits"
    assert payload["drafts"][0]["revision"] == 1
    assert payload["registered_models"]
    assert payload["authoring_policy"] == {
        "routine_authoring_requires_confirmation": False,
        "publish_after_validation": True,
        "discover_identifiers_before_writes": True,
        "ask_user_for_internal_identifiers": False,
        "learner_analysis_capabilities": [],
        "rollback_scope": "explicit_request_or_failed_just_published_release",
    }


def test_create_validate_publish_and_rollback_workflow(tmp_path, monkeypatch) -> None:
    studio = client(tmp_path, monkeypatch)
    created = studio.post(
        "/api/studio/v1/drafts",
        headers=headers(operation="create"),
        json={"draft_id": "limits", "package": classroom_package_payload()},
    )
    validated = studio.post(
        "/api/studio/v1/drafts/limits/validate",
        headers={"Authorization": "Bearer studio-test-key"},
    )
    published = studio.post(
        "/api/studio/v1/drafts/limits/publish",
        headers=headers(operation="publish"),
        json={"expected_revision": 1},
    )
    version = published.json()["active_version"]
    rolled_back = studio.post(
        "/api/studio/v1/packages/calculus-foundations/rollback",
        headers=headers(operation="rollback"),
        json={"version": version},
    )

    assert created.status_code == 201
    assert validated.json()["passed"] is True
    assert published.status_code == 200
    assert rolled_back.json()["active_version"] == version


def test_update_requires_correct_revision_and_idempotency_key(
    tmp_path, monkeypatch
) -> None:
    studio = client(tmp_path, monkeypatch)
    studio.post(
        "/api/studio/v1/drafts",
        headers=headers(operation="create"),
        json={"draft_id": "limits", "package": classroom_package_payload()},
    )
    payload = classroom_package_payload()
    payload["title"] = "更新后的课堂"

    stale = studio.put(
        "/api/studio/v1/drafts/limits",
        headers=headers(operation="update"),
        json={"expected_revision": 2, "package": payload},
    )

    assert stale.status_code == 409
    assert stale.json()["detail"]["error_code"] == "classroom_revision_conflict"


def test_openapi_has_stable_action_operation_ids(tmp_path, monkeypatch) -> None:
    schema = client(tmp_path, monkeypatch).get("/openapi.json").json()
    operations = {
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    }

    assert {
        "getStudioCapabilities",
        "getStudioWorkspace",
        "createClassroomDraft",
        "getClassroomDraft",
        "updateClassroomDraft",
        "validateClassroomDraft",
        "publishClassroomDraft",
        "rollbackClassroomPackage",
    } <= operations
