from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.studio.v1.router import create_studio_router
from app.classroom.authoring import ClassroomAuthoringService
from app.classroom.idempotency import IdempotencyLedger
from app.classroom.model_authoring import TeachingModelAuthoringService
from app.classroom.model_contracts import PreviewJobRecord, TeachingModelManifest
from app.classroom.model_repository import TeachingModelRepository
from app.classroom.preview import TeachingModelPreviewService
from app.classroom.repository import ClassroomRepository
from test_teaching_model_contracts import manifest_payload, source


AUTH = {"Authorization": "Bearer model-secret"}


def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("STUDIO_API_KEY", "model-secret")
    classroom = ClassroomAuthoringService(
        ClassroomRepository(tmp_path / "classrooms"),
        IdempotencyLedger(tmp_path / "classroom-operations"),
    )
    repository = TeachingModelRepository(tmp_path / "models")
    models = TeachingModelAuthoringService(
        repository,
        IdempotencyLedger(tmp_path / "model-operations"),
    )

    def runner(request_path, artifact_dir):
        request = json.loads(request_path.read_text(encoding="utf-8"))
        (artifact_dir / "screenshot.png").write_bytes(b"\x89PNG\r\n\x1a\napi")
        return {
            "uncaught_errors": [],
            "resources_after_dispose": 0,
            "snapshot": {"state": "approach"},
            "viewport": request["viewport"],
            "visible_element_count": 3,
            "painted_bounds": {
                "x": 20,
                "y": 40,
                "width": 600,
                "height": 300,
                "area": 180_000,
            },
            "semantic_visual_signal": {
                "has_meaningful_content": True,
                "visible_text_characters": 24,
                "svg_graphic_count": 0,
                "canvas_distinct_colors": 4,
            },
            "interaction_exercised": True,
            "interaction_changed": True,
        }

    previews = TeachingModelPreviewService(repository, runner=runner)
    app = FastAPI()
    app.include_router(
        create_studio_router(
            lambda: classroom,
            model_service_factory=lambda: models,
            preview_service_factory=lambda: previews,
        )
    )
    return TestClient(app)


def test_model_draft_validate_preview_register_action_flow(tmp_path, monkeypatch) -> None:
    api = client(tmp_path, monkeypatch)
    created = api.post(
        "/api/studio/v1/model-drafts",
        headers={**AUTH, "Idempotency-Key": "create-model-1"},
        json={
            "draft_id": "limit-draft",
            "manifest": manifest_payload(),
            "source": source(),
        },
    )
    validated = api.post(
        "/api/studio/v1/model-drafts/limit-draft/validate",
        headers=AUTH,
    )
    previewed = api.post(
        "/api/studio/v1/model-drafts/limit-draft/previews",
        headers=AUTH,
        json={
            "scenario_id": "approach-target",
            "viewport": {"width": 1280, "height": 800},
        },
    )
    job_id = previewed.json()["job_id"]
    job = api.get(f"/api/studio/v1/previews/{job_id}", headers=AUTH)
    artifact = api.get(
        f"/api/studio/v1/previews/{job_id}/artifacts/screenshot.png",
        headers=AUTH,
    )
    registered = api.post(
        "/api/studio/v1/model-drafts/limit-draft/register",
        headers={**AUTH, "Idempotency-Key": "register-model-1"},
        json={"expected_revision": 1},
    )

    assert created.status_code == 201
    assert validated.json()["passed"] is True
    assert previewed.status_code == 202
    assert job.json()["status"] == "succeeded"
    assert artifact.headers["content-type"] == "image/png"
    assert registered.status_code == 201
    assert registered.json()["version"].startswith("m-")


def test_model_routes_require_studio_auth_and_stable_operation_ids(
    tmp_path,
    monkeypatch,
) -> None:
    api = client(tmp_path, monkeypatch)

    assert api.get("/api/studio/v1/models").status_code == 401
    schema = api.get("/openapi.json").json()
    operations = {
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    }
    assert {
        "listTeachingModels",
        "createTeachingModelDraft",
        "getTeachingModelDraft",
        "updateTeachingModelDraft",
        "validateTeachingModelDraft",
        "requestTeachingModelPreview",
        "getTeachingModelPreview",
        "getTeachingModelPreviewArtifact",
        "registerTeachingModel",
    } <= operations
