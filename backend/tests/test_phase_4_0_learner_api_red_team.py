from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.v1.nodes import get_node_or_404
from app.catalog.learner_projector import LearnerAttemptAssembler, LearnerResponseProjector
from app.catalog.yaml_repository import get_catalog_repository
from app.main import app
from app.services.learning_orchestrator import LearningOrchestrator


client = TestClient(app)


GOOD_ANSWER = "This is separable; separate variables; dy/y = 2x dx; integrate; ln|y|=x^2+C."


def learner_payload(**overrides) -> dict:
    payload = {
        "question_id": "ode-sep-001",
        "user_answer": GOOD_ANSWER,
        "response_steps": ["separable", "dy/y = 2x dx", "ln|y|=x^2+C"],
        "self_explanation": "I separated variables and integrated both sides.",
    }
    payload.update(overrides)
    return payload


def test_learner_health_returns_public_status_without_internal_capabilities() -> None:
    response = client.get("/api/learner/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["api_type"] == "learner_public"
    assert "internal_dev" not in response.text


def test_learner_get_published_question_returns_public_view() -> None:
    response = client.get("/api/learner/v1/questions/ode-sep-001")

    assert response.status_code == 200
    question = response.json()["question"]
    assert question["question_id"] == "ode-sep-001"
    assert question["node_id"] == "ode_separable"
    assert "prompt_markdown" in question


def test_learner_get_draft_question_returns_404() -> None:
    response = client.get("/api/learner/v1/questions/ode-sep-draft-001")

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "question_not_found"


def test_learner_get_retired_question_returns_404() -> None:
    response = client.get("/api/learner/v1/questions/ode-sep-retired-001")

    assert response.status_code == 404


def test_learner_get_internal_question_returns_404() -> None:
    response = client.get("/api/learner/v1/questions/ode-sep-internal-001")

    assert response.status_code == 404


def test_learner_get_unknown_question_returns_404() -> None:
    response = client.get("/api/learner/v1/questions/unknown-001")

    assert response.status_code == 404


def test_learner_get_illegal_question_id_returns_404_without_catalog_detail() -> None:
    response = client.get("/api/learner/v1/questions/bad%25idxx")

    assert response.status_code == 404
    assert "catalog" not in response.text.lower()


def test_learner_get_question_does_not_leak_expected_answer() -> None:
    response = client.get("/api/learner/v1/questions/ode-sep-001")

    assert response.status_code == 200
    assert "expected_answer" not in response.text
    assert "ln|y|=x^2+C" not in response.text


def test_learner_get_question_does_not_leak_rubric() -> None:
    response = client.get("/api/learner/v1/questions/ode-sep-001")

    assert response.status_code == 200
    assert "rubric" not in response.text
    assert "trigger_separable" not in response.text


def test_learner_get_question_does_not_leak_solution_outline() -> None:
    response = client.get("/api/learner/v1/questions/ode-sep-001")

    assert response.status_code == 200
    assert "solution_outline" not in response.text
    assert "Separate dy/y" not in response.text


def test_learner_list_node_questions_only_returns_visible_published_questions() -> None:
    response = client.get("/api/learner/v1/nodes/ode_separable/questions")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert [question["question_id"] for question in body["questions"]] == ["ode-sep-001"]
    assert "draft" not in response.text
    assert "retired" not in response.text
    assert "internal" not in response.text


def test_learner_list_unknown_node_returns_404() -> None:
    response = client.get("/api/learner/v1/nodes/not_a_node/questions")

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "node_not_found"


def test_learner_submit_accepts_question_id_and_answer_only() -> None:
    response = client.post(
        "/api/learner/v1/attempts/submit",
        json={"question_id": "ode-sep-001", "user_answer": GOOD_ANSWER},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"scoring", "diagnosis", "movement", "action"}


def test_learner_submit_accepts_optional_steps_and_self_explanation() -> None:
    response = client.post("/api/learner/v1/attempts/submit", json=learner_payload())

    assert response.status_code == 200


def test_learner_submit_rejects_question_object() -> None:
    payload = learner_payload(question={"id": "ode-sep-001", "expected_answer": "spoof"})

    response = client.post("/api/learner/v1/attempts/submit", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["field_path"] == "$.question.expected_answer"


def test_learner_submit_rejects_free_metadata() -> None:
    payload = learner_payload(metadata={"anything": "not allowed"})

    response = client.post("/api/learner/v1/attempts/submit", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "learner_request_schema_invalid"


def test_learner_submit_rejects_expected_answer_injection() -> None:
    assert_forbidden_field({"expected_answer": "spoof"}, "$.expected_answer")


def test_learner_submit_rejects_rubric_injection() -> None:
    assert_forbidden_field({"rubric": {"items": []}}, "$.rubric")


def test_learner_submit_rejects_solution_outline_injection() -> None:
    assert_forbidden_field({"solution_outline": "spoof"}, "$.solution_outline")


def test_learner_submit_rejects_answer_alias_injection() -> None:
    assert_forbidden_field({"answer_aliases": ["spoof"]}, "$.answer_aliases")


def test_learner_submit_rejects_validator_config_injection() -> None:
    assert_forbidden_field({"validator_config": {"requires_constant": False}}, "$.validator_config")


def test_learner_submit_rejects_score_overrides() -> None:
    assert_forbidden_field({"score_overrides": {"trigger": 100}}, "$.score_overrides")


def test_learner_submit_rejects_evidence_overrides() -> None:
    assert_forbidden_field({"evidence_overrides": {"trigger": "spoof"}}, "$.evidence_overrides")


def test_learner_submit_rejects_manual_override() -> None:
    assert_forbidden_field({"manual_override": True}, "$.manual_override")


def test_learner_submit_rejects_scenario() -> None:
    assert_forbidden_field({"scenario": "process_right_calculation_wrong"}, "$.scenario")


def test_learner_submit_rejects_include_debug() -> None:
    assert_forbidden_field({"include_debug": True}, "$.include_debug")


def test_learner_submit_rejects_debug() -> None:
    assert_forbidden_field({"debug": True}, "$.debug")


def test_learner_submit_rejects_nested_sensitive_field_in_steps() -> None:
    payload = learner_payload(response_steps=["step 1", {"nested": [{"score_overrides": {"trigger": 100}}]}])

    response = client.post("/api/learner/v1/attempts/submit", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["field_path"] == "$.response_steps[1].nested[0].score_overrides"


def test_learner_submit_unknown_question_returns_404() -> None:
    response = client.post("/api/learner/v1/attempts/submit", json=learner_payload(question_id="unknown-001"))

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "question_not_found"


def test_learner_submit_illegal_question_id_returns_stable_error() -> None:
    response = client.post("/api/learner/v1/attempts/submit", json=learner_payload(question_id="../secret"))

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "learner_request_schema_invalid"


def test_learner_submit_malformed_request_returns_stable_error() -> None:
    payload = learner_payload()
    del payload["user_answer"]

    response = client.post("/api/learner/v1/attempts/submit", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "learner_request_schema_invalid"


def test_learner_submit_malformed_json_returns_422_without_stack_trace() -> None:
    response = client.post(
        "/api/learner/v1/attempts/submit",
        content="{bad json",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422
    assert "Traceback" not in response.text


def test_learner_submit_response_has_no_debug_trace() -> None:
    response = client.post("/api/learner/v1/attempts/submit", json=learner_payload())

    assert response.status_code == 200
    assert "debug" not in response.json()
    assert "scorer_results" not in response.text
    assert "diagnosis_trace" not in response.text
    assert "evidence_sources" not in response.text
    assert "error_chain" not in response.text


def test_learner_submit_response_has_no_raw_movement_levels() -> None:
    response = client.post("/api/learner/v1/attempts/submit", json=learner_payload())

    assert response.status_code == 200
    assert "raw_rollback_level" not in response.text
    assert "raw_forward_level" not in response.text
    assert "rollback_level" not in response.text
    assert "forward_level" not in response.text


def test_learner_submit_response_does_not_leak_answer_rubric_or_solution() -> None:
    response = client.post("/api/learner/v1/attempts/submit", json=learner_payload())

    assert response.status_code == 200
    assert "ln|y|=x^2+C" not in response.text
    assert "answer_aliases" not in response.text
    assert "rubric" not in response.text
    assert "solution_outline" not in response.text
    assert "validator_config" not in response.text
    assert "scoring_notes_internal" not in response.text


def test_learner_submit_response_uses_movement_without_raw_debug() -> None:
    response = client.post("/api/learner/v1/attempts/submit", json=learner_payload(user_answer="I do not know."))

    assert response.status_code == 200
    movement = response.json()["movement"]
    assert set(movement) == {"rollback_required", "rollback_nodes", "forward_allowed", "forward_nodes"}


def test_learner_submit_matches_internal_orchestrator_at_safe_projection_layer() -> None:
    record = get_catalog_repository().get_published("ode-sep-001")
    assert record is not None
    node = get_node_or_404(record.manifest.node_id)
    question = record.to_domain_question(node)
    attempt = LearnerAttemptAssembler().to_attempt(
        question_id="ode-sep-001",
        user_answer=GOOD_ANSWER,
        response_steps=["separable", "dy/y = 2x dx", "ln|y|=x^2+C"],
        self_explanation="I separated variables and integrated both sides.",
    )
    orchestrated = LearningOrchestrator().process(question, attempt, node)
    expected = LearnerResponseProjector().from_orchestrated(orchestrated)

    response = client.post("/api/learner/v1/attempts/submit", json=learner_payload())

    assert response.status_code == 200
    assert response.json() == expected


def test_existing_api_v1_health_contract_remains_internal_dev() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["api_type"] == "internal_dev"
    assert response.json()["phase"] == "phase_3_1_internal_dev_api"


def test_openapi_contains_both_frozen_internal_and_new_learner_routes() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = set(response.json()["paths"])
    assert "/api/v1/attempts/submit" in paths
    assert "/api/learner/v1/attempts/submit" in paths
    assert "/api/learner/v1/questions/{question_id}" in paths


def assert_forbidden_field(extra: dict, expected_path: str) -> None:
    payload = learner_payload(**extra)
    response = client.post("/api/learner/v1/attempts/submit", json=payload)

    assert response.status_code == 400
    body = response.json()["detail"]
    assert body["error_code"] == "forbidden_learner_api_field"
    assert body["field_path"] == expected_path

