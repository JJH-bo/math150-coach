from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.studio.v1.router import create_studio_router
from app.classroom.idempotency import IdempotencyLedger
from app.tools.adapters.symbolic_math import SymbolicMathAdapter
from app.tools.execution import ToolExecutionService
from app.tools.registry import ToolRegistry
from app.tools.repository import ToolJobRepository


def tool_service(tmp_path) -> ToolExecutionService:
    return ToolExecutionService(
        ToolRegistry([SymbolicMathAdapter()]),
        ToolJobRepository(tmp_path),
        IdempotencyLedger(tmp_path / "tool-idempotency"),
    )


def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("STUDIO_API_KEY", "studio-test-key")
    service = tool_service(tmp_path)
    app = FastAPI()
    app.include_router(
        create_studio_router(tool_service_factory=lambda: service)
    )
    return TestClient(app)


def auth_headers(*, operation: str | None = None) -> dict[str, str]:
    headers = {"Authorization": "Bearer studio-test-key"}
    if operation is not None:
        headers["Idempotency-Key"] = operation
    return headers


def test_tools_require_studio_bearer_authentication(tmp_path, monkeypatch) -> None:
    studio = client(tmp_path, monkeypatch)

    assert studio.get("/api/studio/v1/tools").status_code == 401
    assert studio.post(
        "/api/studio/v1/tool-jobs",
        headers={"Idempotency-Key": "missing-auth"},
        json={"tool_id": "math.symbolic", "arguments": {}},
    ).status_code == 401


def test_tool_discovery_is_searchable_and_does_not_expose_secrets(
    tmp_path, monkeypatch
) -> None:
    studio = client(tmp_path, monkeypatch)

    response = studio.get(
        "/api/studio/v1/tools?query=symbolic&quality_tier=verified",
        headers=auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    definition = payload["tools"][0]
    assert definition["tool_id"] == "math.symbolic"
    assert definition["required_scope"] == "studio.compute"
    assert definition["quality_tier"] == "verified"
    assert "input_schema" in definition
    serialized = response.text.lower()
    assert "studio-test-key" not in serialized
    assert "api_key" not in serialized


def test_get_tool_returns_requested_verified_definition(tmp_path, monkeypatch) -> None:
    response = client(tmp_path, monkeypatch).get(
        "/api/studio/v1/tools/math.symbolic?version=1.0.0",
        headers=auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["version"] == "1.0.0"


def test_submit_poll_and_download_symbolic_artifacts(tmp_path, monkeypatch) -> None:
    studio = client(tmp_path, monkeypatch)
    request = {
        "tool_id": "math.symbolic",
        "arguments": {
            "operation": "factor",
            "expression": "x**2 - 1",
            "symbols": {"x": {"real": True}},
        },
    }

    submitted = studio.post(
        "/api/studio/v1/tool-jobs",
        headers=auth_headers(operation="factor-once"),
        json=request,
    )

    assert submitted.status_code == 202
    job_id = submitted.json()["job_id"]
    polled = studio.get(
        f"/api/studio/v1/tool-jobs/{job_id}",
        headers=auth_headers(),
    )
    assert polled.status_code == 200
    job = polled.json()
    assert job["state"] == "succeeded"
    assert job["result"]["exact"] == "(x - 1)*(x + 1)"
    assert {item["name"] for item in job["artifacts"]} == {
        "symbolic-result.json",
        "symbolic-result.tex",
    }

    artifact = studio.get(
        f"/api/studio/v1/tool-jobs/{job_id}/artifacts/symbolic-result.tex",
        headers=auth_headers(),
    )
    assert artifact.status_code == 200
    assert artifact.headers["content-type"].startswith("text/x-tex")
    assert artifact.text == "\\left(x - 1\\right) \\left(x + 1\\right)\n"


def test_submission_is_idempotent_and_rejects_changed_payload(
    tmp_path, monkeypatch
) -> None:
    studio = client(tmp_path, monkeypatch)
    first_request = {
        "tool_id": "math.symbolic",
        "arguments": {
            "operation": "simplify",
            "expression": "x + x",
            "symbols": {"x": {"real": True}},
        },
    }
    headers = auth_headers(operation="same-tool-operation")

    first = studio.post("/api/studio/v1/tool-jobs", headers=headers, json=first_request)
    replay = studio.post("/api/studio/v1/tool-jobs", headers=headers, json=first_request)
    changed = studio.post(
        "/api/studio/v1/tool-jobs",
        headers=headers,
        json={
            **first_request,
            "arguments": {**first_request["arguments"], "expression": "x + 1"},
        },
    )

    assert replay.status_code == 202
    assert replay.json()["job_id"] == first.json()["job_id"]
    assert changed.status_code == 409
    assert changed.json()["detail"]["error_code"] == "idempotency_key_conflict"


def test_cancel_is_terminal_safe_and_missing_artifact_is_404(
    tmp_path, monkeypatch
) -> None:
    studio = client(tmp_path, monkeypatch)
    submitted = studio.post(
        "/api/studio/v1/tool-jobs",
        headers=auth_headers(operation="cancel-terminal-job"),
        json={
            "tool_id": "math.symbolic",
            "arguments": {
                "operation": "simplify",
                "expression": "x + x",
                "symbols": {"x": {"real": True}},
            },
        },
    )
    job_id = submitted.json()["job_id"]

    cancelled = studio.post(
        f"/api/studio/v1/tool-jobs/{job_id}/cancel",
        headers=auth_headers(operation="cancel-once"),
    )
    missing = studio.get(
        f"/api/studio/v1/tool-jobs/{job_id}/artifacts/missing.svg",
        headers=auth_headers(),
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["state"] in {"succeeded", "cancelled"}
    assert missing.status_code == 404
    assert missing.json()["detail"]["error_code"] == "tool_job_not_found"


def test_openapi_exposes_stable_custom_gpt_tool_operation_ids(
    tmp_path, monkeypatch
) -> None:
    schema = client(tmp_path, monkeypatch).get("/openapi.json").json()
    operations = {
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    }

    assert {
        "listStudioTools",
        "getStudioTool",
        "submitStudioToolJob",
        "getStudioToolJob",
        "cancelStudioToolJob",
        "getStudioToolArtifact",
    } <= operations
