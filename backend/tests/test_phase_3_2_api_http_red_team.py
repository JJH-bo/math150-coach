from __future__ import annotations

from copy import deepcopy

from fastapi.testclient import TestClient

from app.api.v1.nodes import get_node_or_404
from app.core.schemas import Attempt, Question
from app.main import app
from app.services.learning_orchestrator import LearningOrchestrator, MovementConsistencyError


client = TestClient(app)


def rubric_payload(
    *,
    user_answer: str = "This is separable; separate variables; integrate; ln|y|=x^2+C.",
    include_debug: bool = False,
    expected_answer: str | None = "ln|y|=x^2+C",
) -> dict:
    return {
        "node_id": "ode_separable",
        "question": {
            "id": "q_http_rubric",
            "node_id": "ode_separable",
            "question_type": "diagnostic",
            "prompt": "Solve dy/dx = 2xy.",
            "expected_answer": expected_answer,
            "tested_dimensions": ["trigger", "method", "transformation", "process", "calculation", "final_answer"],
            "solution_outline": "HTTP_SECRET_SOLUTION_OUTLINE_DO_NOT_LEAK",
            "rubric": {
                "items": [
                    {
                        "id": "trigger_separable",
                        "description": "HTTP_SECRET_RUBRIC_DESCRIPTION_DO_NOT_LEAK",
                        "target_dimensions": ["trigger"],
                        "required_keywords": ["separable"],
                        "weight": 1,
                        "required": True,
                        "evidence_on_hit": "Trigger hit.",
                        "evidence_on_miss": "Trigger missed.",
                    },
                    {
                        "id": "method_separate",
                        "description": "Method selection.",
                        "target_dimensions": ["method"],
                        "required_keywords": ["separate variables"],
                        "weight": 1,
                        "required": True,
                        "evidence_on_hit": "Method hit.",
                        "evidence_on_miss": "Method missed.",
                    },
                    {
                        "id": "transform_integrate",
                        "description": "Transformation and integration setup.",
                        "target_dimensions": ["transformation", "process"],
                        "required_keywords": ["integrate"],
                        "weight": 1,
                        "required": True,
                        "evidence_on_hit": "Transformation hit.",
                        "evidence_on_miss": "Transformation missed.",
                    },
                ]
            },
        },
        "attempt": {
            "id": "a_http_rubric",
            "question_id": "q_http_rubric",
            "user_answer": user_answer,
        },
        "options": {"include_debug": include_debug},
    }


def false_pass_payload() -> dict:
    payload = rubric_payload(user_answer="ln|y|=x^2+C.")
    payload["question"]["id"] = "q_http_false_pass"
    payload["attempt"]["id"] = "a_http_false_pass"
    payload["attempt"]["question_id"] = "q_http_false_pass"
    return payload


def rule_only_payload() -> dict:
    return {
        "node_id": "ode_separable",
        "question": {
            "id": "q_http_rule_only",
            "node_id": "ode_separable",
            "question_type": "diagnostic",
            "prompt": "Classify the equation.",
        },
        "attempt": {
            "id": "a_http_rule_only",
            "question_id": "q_http_rule_only",
            "user_answer": "This is separable.",
        },
    }


def no_signal_payload() -> dict:
    payload = rule_only_payload()
    payload["question"]["id"] = "q_http_no_signal"
    payload["attempt"]["id"] = "a_http_no_signal"
    payload["attempt"]["question_id"] = "q_http_no_signal"
    payload["attempt"]["user_answer"] = "I do not know."
    return payload


def model_inputs(payload: dict) -> tuple[Question, Attempt, object]:
    return Question(**deepcopy(payload["question"])), Attempt(**deepcopy(payload["attempt"])), get_node_or_404(payload["node_id"])


def test_http_health_returns_status_phase_capabilities_and_api_type() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["phase"] == "phase_3_1_internal_dev_api"
    assert "capabilities" in body
    assert body["api_type"] == "internal_dev"


def test_http_nodes_returns_catalog() -> None:
    response = client.get("/api/v1/nodes")

    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 16
    assert any(node["id"] == "ode_separable" for node in body["nodes"])


def test_http_node_detail_returns_single_node() -> None:
    response = client.get("/api/v1/nodes/ode_separable")

    assert response.status_code == 200
    assert response.json()["node"]["id"] == "ode_separable"


def test_http_invalid_node_keeps_api_error_envelope() -> None:
    response = client.get("/api/v1/nodes/not_a_node")

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "node_not_found"


def test_http_score_evaluate_returns_only_scoring_partition() -> None:
    response = client.post("/api/v1/score/evaluate", json=rubric_payload())

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"scoring"}
    assert "diagnosis" not in body
    assert "movement" not in body
    assert "action" not in body


def test_http_submit_attempt_returns_full_partitioned_loop() -> None:
    response = client.post("/api/v1/attempts/submit", json=rubric_payload())

    assert response.status_code == 200
    assert set(response.json()) == {"node", "scoring", "diagnosis", "movement", "action"}


def test_http_diagnosis_get_returns_partitioned_response() -> None:
    response = client.post("/api/v1/diagnosis/get", json=rubric_payload())

    assert response.status_code == 200
    assert {"scoring", "diagnosis", "movement", "action"} == set(response.json())


def test_http_next_action_does_not_contradict_movement() -> None:
    response = client.post("/api/v1/next-action/get", json=false_pass_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["forward_allowed"] is False
    assert body["forward_nodes"] == []
    assert body["next_action_hint"] == body["recommended_actions"][0]["reason"]


def test_http_false_pass_cannot_forward() -> None:
    response = client.post("/api/v1/attempts/submit", json=false_pass_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["diagnosis"]["pass_state"] == "false_pass"
    assert body["movement"]["forward_allowed"] is False
    assert body["movement"]["forward_nodes"] == []


def test_http_rule_only_returns_need_more_evidence_without_strong_forward() -> None:
    response = client.post("/api/v1/attempts/submit", json=rule_only_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["action"]["next_action_type"] == "need_more_evidence"
    assert body["movement"]["forward_allowed"] is False


def test_http_no_signal_returns_200_business_result_not_api_error() -> None:
    response = client.post("/api/v1/attempts/submit", json=no_signal_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["diagnosis"]["pass_state"] == "fail"
    assert body["action"]["next_action_type"] == "need_more_evidence"


def test_http_rejects_score_overrides() -> None:
    payload = rubric_payload()
    payload["attempt"]["metadata"] = {"score_overrides": {"trigger": 100}}

    response = client.post("/api/v1/attempts/submit", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "forbidden_public_api_field"


def test_http_rejects_evidence_overrides() -> None:
    payload = rubric_payload()
    payload["attempt"]["metadata"] = {"evidence_overrides": {"trigger": "manual"}}

    response = client.post("/api/v1/attempts/submit", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["field_path"] == "$.attempt.metadata.evidence_overrides"


def test_http_rejects_manual_override() -> None:
    payload = rubric_payload()
    payload["manual_override"] = True

    response = client.post("/api/v1/attempts/submit", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["field_path"] == "$.manual_override"


def test_http_rejects_scenario() -> None:
    payload = rubric_payload()
    payload["attempt"]["metadata"] = {"scenario": "answer_right_trigger_unclear"}

    response = client.post("/api/v1/attempts/submit", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["field_path"] == "$.attempt.metadata.scenario"


def test_http_rejects_nested_forbidden_field_recursively() -> None:
    payload = rubric_payload()
    payload["question"]["metadata"] = {"nested": [{"manual_override": True}]}

    response = client.post("/api/v1/attempts/submit", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"]["field_path"] == "$.question.metadata.nested[0].manual_override"


def test_http_question_node_mismatch_returns_422() -> None:
    payload = rubric_payload()
    payload["question"]["node_id"] = "ode_first_order_linear"

    response = client.post("/api/v1/attempts/submit", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "question_node_mismatch"


def test_http_attempt_question_mismatch_returns_422() -> None:
    payload = rubric_payload()
    payload["attempt"]["question_id"] = "wrong_question"

    response = client.post("/api/v1/attempts/submit", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "attempt_question_mismatch"


def test_http_default_response_has_no_debug_fields() -> None:
    response = client.post("/api/v1/attempts/submit", json=rubric_payload())
    body = response.json()
    serialized = response.text

    assert response.status_code == 200
    assert "debug" not in body
    assert "scorer_results" not in serialized
    assert "diagnosis_trace" not in serialized
    assert "raw_rollback_level" not in serialized
    assert "raw_forward_level" not in serialized
    assert "error_chain" not in serialized


def test_http_debug_true_returns_controlled_debug_fields() -> None:
    response = client.post("/api/v1/attempts/submit", json=rubric_payload(include_debug=True))

    assert response.status_code == 200
    debug = response.json()["debug"]
    assert "scorer_results" in debug
    assert "diagnosis_trace" in debug
    assert "raw_rollback_level" in debug
    assert "raw_forward_level" in debug
    assert "error_chain" in debug


def test_http_learner_safe_response_does_not_leak_answer_or_rubric() -> None:
    payload = rubric_payload(expected_answer="HTTP_SECRET_EXPECTED_ANSWER_DO_NOT_LEAK")
    payload["attempt"]["user_answer"] = "This is separable; separate variables; integrate."

    response = client.post("/api/v1/attempts/submit", json=payload)

    assert response.status_code == 200
    assert "HTTP_SECRET_EXPECTED_ANSWER_DO_NOT_LEAK" not in response.text
    assert "HTTP_SECRET_SOLUTION_OUTLINE_DO_NOT_LEAK" not in response.text
    assert "HTTP_SECRET_RUBRIC_DESCRIPTION_DO_NOT_LEAK" not in response.text


def test_http_empty_rollback_nodes_maps_to_rollback_required_false_without_raw_level() -> None:
    response = client.post("/api/v1/attempts/submit", json=no_signal_payload())

    assert response.status_code == 200
    movement = response.json()["movement"]
    assert movement == {
        "rollback_required": False,
        "rollback_nodes": [],
        "forward_allowed": False,
        "forward_nodes": [],
    }


def test_http_empty_forward_nodes_maps_to_forward_allowed_false_without_raw_level() -> None:
    response = client.post("/api/v1/attempts/submit", json=false_pass_payload())

    assert response.status_code == 200
    movement = response.json()["movement"]
    assert movement["forward_allowed"] is False
    assert movement["forward_nodes"] == []
    assert "forward_level" not in movement


def test_http_malformed_json_returns_422_without_stack_trace() -> None:
    response = client.post(
        "/api/v1/attempts/submit",
        content="{bad json",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422
    assert "Traceback" not in response.text


def test_http_missing_required_top_level_field_returns_request_schema_invalid() -> None:
    payload = rubric_payload()
    del payload["attempt"]

    response = client.post("/api/v1/attempts/submit", json=payload)

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "request_schema_invalid"


def test_http_openapi_registers_all_api_v1_endpoints() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = set(response.json()["paths"])
    assert {
        "/api/v1/health",
        "/api/v1/nodes",
        "/api/v1/nodes/{node_id}",
        "/api/v1/score/evaluate",
        "/api/v1/diagnosis/get",
        "/api/v1/next-action/get",
        "/api/v1/attempts/submit",
    } <= paths


def test_http_submit_attempt_matches_learning_orchestrator_outputs() -> None:
    payload = false_pass_payload()
    question, attempt, node = model_inputs(payload)
    orchestrated = LearningOrchestrator().process(question, attempt, node)

    response = client.post("/api/v1/attempts/submit", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["diagnosis"]["pass_state"] == orchestrated.diagnosis_result.pass_state.value
    assert body["diagnosis"]["root_cause"] == orchestrated.diagnosis_result.root_cause.value
    assert body["movement"]["rollback_nodes"] == orchestrated.rollback_decision.rollback_nodes
    assert body["movement"]["forward_nodes"] == orchestrated.forward_decision.forward_nodes


def test_http_movement_consistency_error_returns_500_without_stack_trace(monkeypatch) -> None:
    def fail(self, question, attempt, node):
        raise MovementConsistencyError("synthetic consistency failure")

    monkeypatch.setattr(LearningOrchestrator, "process", fail)

    response = client.post("/api/v1/attempts/submit", json=rubric_payload())

    assert response.status_code == 500
    assert response.json()["detail"]["error_code"] == "internal_engine_error"
    assert "Traceback" not in response.text
