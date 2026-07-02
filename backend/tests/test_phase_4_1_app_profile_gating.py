from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import AppProfile, AppProfileConfigError, resolve_app_profile
from app.main import app, create_app


GOOD_ANSWER = "This is separable; separate variables; dy/y = 2x dx; integrate; ln|y|=x^2+C."


def public_payload() -> dict:
    return {
        "question_id": "ode-sep-001",
        "user_answer": GOOD_ANSWER,
        "response_steps": ["separable", "dy/y = 2x dx", "ln|y|=x^2+C"],
        "self_explanation": "I separated variables and integrated both sides.",
    }


def internal_payload() -> dict:
    return {
        "node_id": "ode_separable",
        "question": {
            "id": "q_profile_internal",
            "node_id": "ode_separable",
            "question_type": "diagnostic",
            "prompt": "Solve dy/dx = 2xy.",
            "expected_answer": "ln|y|=x^2+C",
            "tested_dimensions": ["trigger", "method", "transformation", "process", "calculation", "final_answer"],
            "rubric": {
                "items": [
                    {
                        "id": "trigger_separable",
                        "description": "Recognize separable form.",
                        "target_dimensions": ["trigger"],
                        "required_keywords": ["separable"],
                        "weight": 1,
                        "required": True,
                        "evidence_on_hit": "Trigger hit.",
                        "evidence_on_miss": "Trigger missed.",
                    }
                ]
            },
        },
        "attempt": {
            "id": "a_profile_internal",
            "question_id": "q_profile_internal",
            "user_answer": GOOD_ANSWER,
        },
    }


def paths_for(profile: str) -> set[str]:
    response = TestClient(create_app(profile=profile)).get("/openapi.json")
    assert response.status_code == 200
    return set(response.json()["paths"])


def test_create_app_mixed_registers_internal_and_learner_routes() -> None:
    paths = paths_for("mixed")

    assert "/api/v1/health" in paths
    assert "/api/v1/attempts/submit" in paths
    assert "/api/learner/v1/health" in paths
    assert "/api/learner/v1/attempts/submit" in paths


def test_create_app_learner_registers_only_learner_routes() -> None:
    paths = paths_for("learner")

    assert "/api/learner/v1/health" in paths
    assert "/api/learner/v1/questions/{question_id}" in paths
    assert "/api/learner/v1/attempts/submit" in paths
    assert not any(path.startswith("/api/v1/") for path in paths)


def test_create_app_internal_registers_only_internal_routes() -> None:
    paths = paths_for("internal")

    assert "/api/v1/health" in paths
    assert "/api/v1/attempts/submit" in paths
    assert not any(path.startswith("/api/learner/v1/") for path in paths)


def test_learner_openapi_omits_api_v1_health() -> None:
    assert "/api/v1/health" not in paths_for("learner")


def test_learner_openapi_omits_api_v1_attempt_submit() -> None:
    assert "/api/v1/attempts/submit" not in paths_for("learner")


def test_learner_profile_api_v1_health_returns_404() -> None:
    response = TestClient(create_app("learner")).get("/api/v1/health")

    assert response.status_code == 404


def test_learner_profile_api_v1_submit_returns_404() -> None:
    response = TestClient(create_app("learner")).post("/api/v1/attempts/submit", json=internal_payload())

    assert response.status_code == 404


def test_learner_profile_learner_health_returns_200() -> None:
    response = TestClient(create_app("learner")).get("/api/learner/v1/health")

    assert response.status_code == 200
    assert response.json()["api_type"] == "learner_public"


def test_learner_profile_learner_submit_still_works() -> None:
    response = TestClient(create_app("learner")).post("/api/learner/v1/attempts/submit", json=public_payload())

    assert response.status_code == 200
    assert set(response.json()) == {"scoring", "diagnosis", "movement", "action"}


def test_learner_profile_response_still_hides_trusted_and_debug_fields() -> None:
    response = TestClient(create_app("learner")).post("/api/learner/v1/attempts/submit", json=public_payload())

    assert response.status_code == 200
    serialized = response.text
    assert "expected_answer" not in serialized
    assert "rubric" not in serialized
    assert "solution_outline" not in serialized
    assert "debug" not in response.json()
    assert "diagnosis_trace" not in serialized
    assert "raw_rollback_level" not in serialized
    assert "raw_forward_level" not in serialized


def test_internal_openapi_omits_learner_health() -> None:
    assert "/api/learner/v1/health" not in paths_for("internal")


def test_internal_openapi_omits_learner_question_detail() -> None:
    assert "/api/learner/v1/questions/{question_id}" not in paths_for("internal")


def test_internal_profile_learner_health_returns_404() -> None:
    response = TestClient(create_app("internal")).get("/api/learner/v1/health")

    assert response.status_code == 404


def test_internal_profile_api_v1_health_returns_200() -> None:
    response = TestClient(create_app("internal")).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["api_type"] == "internal_dev"


def test_internal_profile_api_v1_submit_still_works() -> None:
    response = TestClient(create_app("internal")).post("/api/v1/attempts/submit", json=internal_payload())

    assert response.status_code == 200
    assert {"node", "scoring", "diagnosis", "movement", "action"} == set(response.json())


def test_mixed_profile_keeps_current_two_surfaces() -> None:
    client = TestClient(create_app("mixed"))

    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/learner/v1/health").status_code == 200


def test_unset_app_profile_defaults_to_mixed(monkeypatch) -> None:
    monkeypatch.delenv("APP_PROFILE", raising=False)

    assert resolve_app_profile() == AppProfile.MIXED
    assert create_app().state.app_profile == "mixed"


def test_explicit_profile_takes_precedence_over_env(monkeypatch) -> None:
    monkeypatch.setenv("APP_PROFILE", "learner")

    assert create_app(profile="internal").state.app_profile == "internal"


def test_app_profile_env_is_case_and_whitespace_tolerant(monkeypatch) -> None:
    monkeypatch.setenv("APP_PROFILE", "  LEARNER ")

    assert create_app().state.app_profile == "learner"


def test_invalid_explicit_profile_fails_fast() -> None:
    with pytest.raises(AppProfileConfigError, match="Invalid APP_PROFILE"):
        create_app(profile="public")


def test_invalid_env_profile_fails_fast(monkeypatch) -> None:
    monkeypatch.setenv("APP_PROFILE", "public")

    with pytest.raises(AppProfileConfigError, match="Invalid APP_PROFILE"):
        create_app()


def test_from_app_main_import_app_remains_available_as_default_mixed_surface() -> None:
    client = TestClient(app)

    assert getattr(app.state, "app_profile") == "mixed"
    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/learner/v1/health").status_code == 200


def test_root_health_in_learner_profile_is_minimal_and_route_agnostic() -> None:
    response = TestClient(create_app("learner")).get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "ok",
        "phase": "phase_4_1_profile_gating",
        "app_profile": "learner",
    }
    assert "/api/v1" not in response.text
    assert "internal_dev" not in response.text
    assert "capabilities" not in response.text


def test_root_health_in_internal_profile_is_minimal_and_route_agnostic() -> None:
    response = TestClient(create_app("internal")).get("/health")

    assert response.status_code == 200
    assert "/api/learner" not in response.text
    assert "capabilities" not in response.text


def test_openapi_and_http_404_are_consistent_for_profile_hidden_routes() -> None:
    learner_client = TestClient(create_app("learner"))
    learner_paths = set(learner_client.get("/openapi.json").json()["paths"])
    assert "/api/v1/health" not in learner_paths
    assert learner_client.get("/api/v1/health").status_code == 404

    internal_client = TestClient(create_app("internal"))
    internal_paths = set(internal_client.get("/openapi.json").json()["paths"])
    assert "/api/learner/v1/health" not in internal_paths
    assert internal_client.get("/api/learner/v1/health").status_code == 404

