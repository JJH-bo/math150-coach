from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.classroom.v1.router import create_classroom_router
from app.api.studio.v1.router import create_studio_router
from app.classroom.authoring import ClassroomAuthoringService
from app.classroom.idempotency import IdempotencyLedger
from app.classroom.models import ClassroomPackage
from app.classroom.repository import ClassroomRepository
from app.classroom.runtime import ClassroomRuntimeService
from app.classroom.session_repository import LearningSessionRepository
from app.classroom.sessions import LearningSessionService
from classroom_fixtures import classroom_package_payload


def app_client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("STUDIO_API_KEY", "studio-test-key")
    classroom_repository = ClassroomRepository(tmp_path)
    package = ClassroomPackage.model_validate(classroom_package_payload())
    classroom_repository.create_draft("limits", package)
    classroom_repository.publish("limits", 1)
    runtime = ClassroomRuntimeService(classroom_repository)
    sessions = LearningSessionService(
        LearningSessionRepository(tmp_path / "learning-sessions.sqlite3"),
        runtime,
    )
    authoring = ClassroomAuthoringService(
        classroom_repository,
        IdempotencyLedger(tmp_path / "operations"),
    )
    app = FastAPI()
    app.include_router(
        create_classroom_router(
            lambda: runtime,
            session_service_factory=lambda: sessions,
        )
    )
    app.include_router(
        create_studio_router(
            lambda: authoring,
            session_service_factory=lambda: sessions,
        )
    )
    return TestClient(app)


def studio_headers(*, operation: str | None = None) -> dict[str, str]:
    result = {"Authorization": "Bearer studio-test-key"}
    if operation:
        result["Idempotency-Key"] = operation
    return result


def detailed_expansion_payload() -> dict:
    return {
        "expected_revision": 2,
        "pedagogical_intent": "把直接代入与邻域行为放到同一个对比图中。",
        "expansion": {
            "id": "why-not-substitute-live",
            "title": "为什么不能只看点值",
            "parent_content_id": "limit-formula",
            "learner_question": "这里没懂，为什么不直接代入？",
            "preserved_context": ["极限描述趋近过程"],
            "focus_relation": "点值与邻域趋势是两个不同对象",
            "representation": "counterexample",
            "blocks": [
                {
                    "id": "punctured-function-counterexample",
                    "kind": "worked_example",
                    "data": {
                        "prompt": "比较缺口处点值与周围函数值。",
                        "steps": [
                            "先遮住 x=1 这个点",
                            "观察两侧都靠近 2",
                            "再单独改变 x=1 的点值",
                            "周围趋近趋势没有改变",
                        ],
                    },
                }
            ],
            "return_connection": "因此极限公式描述邻域趋势，而不是该点赋值。",
        },
    }


def create_session(client: TestClient) -> tuple[str, str]:
    response = client.post(
        "/api/classroom/v1/learning-sessions",
        json={
            "package_id": "calculus-foundations",
            "module_id": "limit-core",
        },
    )
    assert response.status_code == 201
    payload = response.json()
    return payload["session"]["session_id"], payload["access_token"]


def test_learner_creates_restores_and_reveals_fixed_baseline(
    tmp_path, monkeypatch
) -> None:
    client = app_client(tmp_path, monkeypatch)
    session_id, access_token = create_session(client)

    restored = client.get(
        f"/api/classroom/v1/learning-sessions/{session_id}",
        params={"access_token": access_token},
    )
    revealed = client.post(
        f"/api/classroom/v1/learning-sessions/{session_id}/reveal",
        json={"access_token": access_token, "expected_revision": 1},
    )

    assert restored.status_code == 200
    assert restored.json()["revealed_step_ids"] == ["limit-intro"]
    assert revealed.status_code == 200
    assert revealed.json()["revealed_step_ids"] == [
        "limit-intro",
        "limit-formula",
    ]
    assert revealed.json()["expansions"] == []


def test_learner_updates_exact_active_content_and_replays_events(
    tmp_path, monkeypatch
) -> None:
    client = app_client(tmp_path, monkeypatch)
    session_id, access_token = create_session(client)

    focused = client.post(
        f"/api/classroom/v1/learning-sessions/{session_id}/interactions",
        json={
            "access_token": access_token,
            "expected_revision": 1,
            "active_content_id": "limit-intro",
        },
    )
    events = client.get(
        f"/api/classroom/v1/learning-sessions/{session_id}/events",
        params={"access_token": access_token, "after_revision": 0},
    )

    assert focused.status_code == 200
    assert events.status_code == 200
    assert events.headers["content-type"].startswith("text/event-stream")
    assert "event: session.created" in events.text


def test_studio_discovers_active_session_and_inserts_exact_expansion(
    tmp_path, monkeypatch
) -> None:
    client = app_client(tmp_path, monkeypatch)
    session_id, access_token = create_session(client)
    client.post(
        f"/api/classroom/v1/learning-sessions/{session_id}/reveal",
        json={"access_token": access_token, "expected_revision": 1},
    )

    discovered = client.get(
        "/api/studio/v1/learning-sessions",
        headers=studio_headers(),
    )
    patched = client.patch(
        f"/api/studio/v1/learning-sessions/{session_id}/scene",
        headers=studio_headers(operation="expand-limit-formula"),
        json=detailed_expansion_payload(),
    )

    assert discovered.status_code == 200
    sessions = discovered.json()["sessions"]
    assert sessions[0]["recommended_for_update"] is True
    assert sessions[0]["active_content_id"] == "limit-formula"
    assert patched.status_code == 200
    assert patched.json()["expansions"][0]["parent_content_id"] == "limit-formula"
    assert patched.json()["active_content_id"] == (
        "punctured-function-counterexample"
    )


def test_studio_patch_requires_auth_revision_and_idempotency(
    tmp_path, monkeypatch
) -> None:
    client = app_client(tmp_path, monkeypatch)
    session_id, access_token = create_session(client)
    client.post(
        f"/api/classroom/v1/learning-sessions/{session_id}/reveal",
        json={"access_token": access_token, "expected_revision": 1},
    )

    missing_auth = client.patch(
        f"/api/studio/v1/learning-sessions/{session_id}/scene",
        headers={"Idempotency-Key": "missing-auth"},
        json=detailed_expansion_payload(),
    )
    stale = detailed_expansion_payload()
    stale["expected_revision"] = 1
    conflict = client.patch(
        f"/api/studio/v1/learning-sessions/{session_id}/scene",
        headers=studio_headers(operation="stale-patch"),
        json=stale,
    )

    assert missing_auth.status_code == 401
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["error_code"] == (
        "learning_session_revision_conflict"
    )
    assert conflict.json()["detail"]["current_revision"] == 2


def test_openapi_exposes_learning_session_action_operations(
    tmp_path, monkeypatch
) -> None:
    schema = app_client(tmp_path, monkeypatch).get("/openapi.json").json()
    operation_ids = {
        operation["operationId"]
        for path in schema["paths"].values()
        for operation in path.values()
        if isinstance(operation, dict) and "operationId" in operation
    }

    assert {
        "listLearningSessions",
        "getStudioLearningSession",
        "patchLearningSessionScene",
        "returnLearningSessionExpansion",
    } <= operation_ids
