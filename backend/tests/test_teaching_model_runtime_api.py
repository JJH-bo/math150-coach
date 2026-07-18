from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.classroom.v1.router import create_classroom_router
from app.classroom.model_contracts import TeachingModelManifest
from app.classroom.model_repository import TeachingModelRepository
from app.classroom.models import ClassroomPackage
from app.classroom.repository import ClassroomRepository
from app.classroom.runtime import ClassroomRuntimeService
from classroom_fixtures import classroom_package_payload
from test_teaching_model_contracts import manifest_payload, source


def client(tmp_path) -> tuple[TestClient, str]:
    models = TeachingModelRepository(tmp_path / "models")
    manifest = TeachingModelManifest.model_validate(manifest_payload())
    draft = models.create_draft("limit-model", manifest, source())
    registered = models.register(
        draft,
        validation={"passed": True, "issues": []},
        preview_job_id="preview-1",
    )
    payload = classroom_package_payload()
    payload["model_instances"] = [
        {
            "instance_id": "limit-view",
            "model_id": registered.model_id,
            "model_version": registered.version,
            "initial_state": "overview",
            "parameters": {"delta": 0.5, "theme": "cyan"},
            "viewport_mode": "inline",
            "quality_profile": "balanced",
            "allowed_interactions": ["parameter_change"],
            "fallback_description": "极限邻域静态图。",
        }
    ]
    payload["model_bindings"] = [
        {
            "id": "formula-enters",
            "content_id": "limit-formula",
            "instance_id": "limit-view",
            "trigger": {"kind": "block_enter"},
            "effect": {"kind": "set_state", "target": "approach"},
            "restore_previous": True,
        }
    ]
    classrooms = ClassroomRepository(tmp_path / "classrooms")
    package = ClassroomPackage.model_validate(payload)
    classrooms.create_draft("limits", package)
    classrooms.publish("limits", 1)
    app = FastAPI()
    app.include_router(
        create_classroom_router(
            lambda: ClassroomRuntimeService(classrooms, model_repository=models)
        )
    )
    return TestClient(app), registered.version


def test_runtime_serves_exact_registered_manifest_and_source(tmp_path) -> None:
    api, version = client(tmp_path)

    metadata = api.get(
        f"/api/classroom/v1/models/limit-neighborhood-2d/versions/{version}"
    )
    source_response = api.get(
        f"/api/classroom/v1/models/limit-neighborhood-2d/versions/{version}/source.js"
    )

    assert metadata.status_code == 200
    assert metadata.json()["manifest"]["model_id"] == "limit-neighborhood-2d"
    assert source_response.status_code == 200
    assert source_response.headers["content-type"].startswith("application/javascript")
    assert "createTeachingModel" in source_response.text


def test_module_projection_includes_only_its_instances_and_bindings(tmp_path) -> None:
    api, _ = client(tmp_path)

    response = api.get(
        "/api/classroom/v1/packages/calculus-foundations/modules/limit-core"
    )

    assert response.status_code == 200
    assert response.json()["model_instances"][0]["instance_id"] == "limit-view"
    assert response.json()["model_bindings"][0]["content_id"] == "limit-formula"
