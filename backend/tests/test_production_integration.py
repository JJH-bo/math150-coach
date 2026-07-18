from __future__ import annotations

from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from app.main import create_app


ROOT = Path(__file__).resolve().parents[2]


def test_action_schema_is_available_only_when_studio_is_mounted(
    monkeypatch,
) -> None:
    monkeypatch.setenv("STUDIO_API_KEY", "do-not-expose-this-secret")

    for profile in ("internal", "mixed"):
        response = TestClient(create_app(profile)).get(
            "/api/studio/v1/action-schema.json"
        )
        assert response.status_code == 200

    assert (
        TestClient(create_app("learner"))
        .get("/api/studio/v1/action-schema.json")
        .status_code
        == 404
    )


def test_action_schema_contains_only_authenticated_studio_operations(
    monkeypatch,
) -> None:
    secret = "do-not-expose-this-secret"
    monkeypatch.setenv("STUDIO_API_KEY", secret)
    response = TestClient(
        create_app("mixed"),
        base_url="https://classroom.example",
    ).get("/api/studio/v1/action-schema.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["servers"] == [{"url": "https://classroom.example"}]
    assert schema["paths"]
    assert all(path.startswith("/api/studio/v1/") for path in schema["paths"])
    assert "/api/studio/v1/action-schema.json" not in schema["paths"]
    assert not any(
        path.startswith("/api/classroom/v1/") for path in schema["paths"]
    )
    assert schema["components"]["securitySchemes"]["HTTPBearer"] == {
        "type": "http",
        "scheme": "bearer",
    }
    assert secret not in response.text

    operation_ids = [
        operation["operationId"]
        for path_item in schema["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    ]
    assert len(operation_ids) == len(set(operation_ids))
    assert {
        "getStudioCapabilities",
        "createClassroomDraft",
        "validateClassroomDraft",
        "publishClassroomDraft",
        "createTeachingModelDraft",
        "requestTeachingModelPreview",
        "registerTeachingModel",
    } <= set(operation_ids)
    assert all(
        operation.get("security") == [{"HTTPBearer": []}]
        for path_item in schema["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    )


def test_privacy_page_is_public_in_every_profile() -> None:
    for profile in ("learner", "internal", "mixed"):
        response = TestClient(create_app(profile)).get("/privacy")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "AI Classroom Privacy" in response.text
        assert "diagnose" in response.text
        assert "STUDIO_API_KEY" not in response.text


def test_action_schema_and_privacy_are_not_added_to_general_openapi() -> None:
    schema = TestClient(create_app("mixed")).get("/openapi.json").json()
    assert "/api/studio/v1/action-schema.json" not in schema["paths"]
    assert "/privacy" not in schema["paths"]


def test_render_blueprint_uses_mixed_profile_and_persistent_data_root() -> None:
    blueprint = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    service = blueprint["services"][0]
    env = {item["key"]: item for item in service["envVars"]}

    assert service["type"] == "web"
    assert service["runtime"] == "docker"
    assert service["healthCheckPath"] == "/health"
    assert service["numInstances"] == 1
    assert service["disk"]["mountPath"] == "/var/data"
    assert service["disk"]["sizeGB"] >= 1
    assert env["APP_PROFILE"]["value"] == "mixed"
    assert env["CLASSROOM_DATA_ROOT"]["value"] == "/var/data"
    assert env["STUDIO_API_KEY"]["generateValue"] is True
    assert "value" not in env["STUDIO_API_KEY"]
    assert env["MODEL_PREVIEW_BROWSER"]["value"] == "/usr/bin/chromium"
    assert env["NODE_PATH"]["value"] == "/app/node_modules"


def test_docker_image_bootstraps_before_starting_the_server() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "python:3.12-slim" in dockerfile
    assert "chromium" in dockerfile
    assert "npm ci --omit=dev" in dockerfile
    assert "tools/bootstrap_ai_classroom.py" in dockerfile
    assert 'CLASSROOM_DATA_ROOT' in dockerfile
    assert 'exec uvicorn app.main:app' in dockerfile
