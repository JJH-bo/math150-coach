from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.classroom.v1.router import create_classroom_router
from app.classroom.models import ClassroomPackage
from app.classroom.repository import ClassroomRepository
from app.classroom.runtime import ClassroomRuntimeService
from classroom_fixtures import classroom_package_payload


def client(tmp_path) -> TestClient:
    repository = ClassroomRepository(tmp_path)
    package = ClassroomPackage.model_validate(classroom_package_payload())
    repository.create_draft("limits", package)
    repository.publish("limits", 1)
    app = FastAPI()
    app.include_router(
        create_classroom_router(lambda: ClassroomRuntimeService(repository))
    )
    return TestClient(app)


def test_catalog_lists_only_active_packages(tmp_path) -> None:
    response = client(tmp_path).get("/api/classroom/v1/catalog")

    assert response.status_code == 200
    assert response.json()["packages"][0]["package_id"] == "calculus-foundations"


def test_active_package_returns_release_context_and_content(tmp_path) -> None:
    response = client(tmp_path).get(
        "/api/classroom/v1/packages/calculus-foundations"
    )

    assert response.status_code == 200
    assert response.json()["version"].startswith("r-")
    assert response.json()["package"]["courses"][0]["chapters"][0]["id"] == "limits"


def test_module_projection_keeps_complete_module_content(tmp_path) -> None:
    response = client(tmp_path).get(
        "/api/classroom/v1/packages/calculus-foundations/modules/limit-core"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["module"]["id"] == "limit-core"
    assert len(payload["module"]["blocks"]) == 2
    assert payload["module"]["segments"][0]["id"] == "limit-example-segment"


def test_runtime_payload_has_no_learner_analysis_fields(tmp_path) -> None:
    response = client(tmp_path).get(
        "/api/classroom/v1/packages/calculus-foundations"
    )
    serialized = response.text

    for forbidden in (
        "mastery",
        "diagnosis",
        "score",
        "review_schedule",
        "recommended_next_step",
        "boss_challenge",
    ):
        assert forbidden not in serialized
