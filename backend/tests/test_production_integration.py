from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


ROOT = Path(__file__).resolve().parents[2]


def _component_refs(value: object) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        ref = value.get("$ref")
        prefix = "#/components/schemas/"
        if isinstance(ref, str) and ref.startswith(prefix):
            refs.add(ref.removeprefix(prefix))
        for child in value.values():
            refs.update(_component_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.update(_component_refs(child))
    return refs


def _has_component_cycle(schemas: dict[str, object]) -> bool:
    graph = {
        name: _component_refs(schema)
        for name, schema in schemas.items()
    }
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> bool:
        if name in visiting:
            return True
        if name in visited:
            return False
        visiting.add(name)
        if any(visit(target) for target in graph.get(name, set())):
            return True
        visiting.remove(name)
        visited.add(name)
        return False

    return any(visit(name) for name in graph)


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
        "getStudioWorkspace",
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


def test_action_schema_uses_configured_public_https_origin(
    monkeypatch,
) -> None:
    monkeypatch.setenv(
        "AI_CLASSROOM_PUBLIC_ORIGIN",
        "https://math150.example/",
    )

    schema = (
        TestClient(
            create_app("mixed"),
            base_url="http://internal-service:8000",
        )
        .get("/api/studio/v1/action-schema.json")
        .json()
    )

    assert schema["servers"] == [{"url": "https://math150.example"}]


def test_action_schema_has_no_component_reference_cycles(
    monkeypatch,
) -> None:
    monkeypatch.setenv("STUDIO_API_KEY", "do-not-expose-this-secret")
    schema = (
        TestClient(create_app("mixed"))
        .get("/api/studio/v1/action-schema.json")
        .json()
    )

    component_schemas = schema["components"]["schemas"]
    assert not _has_component_cycle(component_schemas)
    assert {
        "ActionNestedContentBlock",
        "ActionNestedDetailBranch",
        "ActionLeafContentBlock",
    } <= component_schemas.keys()


def test_action_schema_object_responses_have_property_skeletons(
    monkeypatch,
) -> None:
    monkeypatch.setenv("STUDIO_API_KEY", "do-not-expose-this-secret")
    schema = (
        TestClient(create_app("mixed"))
        .get("/api/studio/v1/action-schema.json")
        .json()
    )

    object_responses = [
        media["schema"]
        for path_item in schema["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict)
        for response in operation.get("responses", {}).values()
        for media in response.get("content", {}).values()
        if media.get("schema", {}).get("type") == "object"
    ]

    assert object_responses
    assert all("properties" in response for response in object_responses)


def test_workspace_action_response_is_fully_described(monkeypatch) -> None:
    monkeypatch.setenv("STUDIO_API_KEY", "do-not-expose-this-secret")
    schema = (
        TestClient(create_app("mixed"))
        .get("/api/studio/v1/action-schema.json")
        .json()
    )

    response_schema = schema["paths"]["/api/studio/v1/workspace"]["get"][
        "responses"
    ]["200"]["content"]["application/json"]["schema"]

    assert response_schema == {
        "$ref": "#/components/schemas/StudioWorkspaceResponse"
    }
    workspace = schema["components"]["schemas"]["StudioWorkspaceResponse"]
    assert {
        "public_origin",
        "learner_entry_url",
        "active_packages",
        "drafts",
        "registered_models",
        "pagination",
        "authoring_policy",
    } <= workspace["properties"].keys()


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


def test_railway_config_uses_docker_healthcheck_and_safe_restart_policy() -> None:
    config = json.loads((ROOT / "railway.json").read_text(encoding="utf-8"))

    assert config["$schema"] == "https://railway.com/railway.schema.json"
    assert config["build"] == {
        "builder": "DOCKERFILE",
        "dockerfilePath": "Dockerfile",
    }
    assert config["deploy"] == {
        "healthcheckPath": "/health",
        "healthcheckTimeout": 300,
        "restartPolicyType": "ON_FAILURE",
        "restartPolicyMaxRetries": 10,
    }
    assert not (ROOT / "render.yaml").exists()


def test_railway_runbook_keeps_volume_and_secret_out_of_source() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Railway" in readme
    assert "mount" in readme
    assert "`/var/data`" in readme
    assert "`STUDIO_API_KEY`" in readme
    assert "`AI_CLASSROOM_PUBLIC_ORIGIN`" in readme
    assert "Generate Domain" in readme
    assert "render.yaml" not in readme


def test_docker_image_bootstraps_before_starting_the_server() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "python:3.12-slim" in dockerfile
    assert "chromium" in dockerfile
    assert "npm ci --omit=dev" in dockerfile
    assert "tools/bootstrap_ai_classroom.py" in dockerfile
    assert 'CLASSROOM_DATA_ROOT' in dockerfile
    assert 'exec uvicorn app.main:app' in dockerfile
