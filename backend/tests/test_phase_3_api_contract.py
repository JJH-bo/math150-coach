from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

from fastapi import HTTPException

from app.api.v1.diagnosis import get_diagnosis
from app.api.v1.health import health
from app.api.v1.next_action import get_next_action
from app.api.v1.nodes import get_node, list_nodes
from app.api.v1.score import evaluate_score
from app.api.v1.submit_attempt import submit_attempt
from app.main import app
from app.services.diagnosis_engine import DiagnosisEngine
from app.services.forward_engine import ForwardEngine
from app.services.learning_orchestrator import LearningOrchestrator
from app.services.rollback_engine import RollbackEngine


class RouteResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload, ensure_ascii=False)

    def json(self) -> Any:
        return self._payload


def call_route(route_fn, *args, **kwargs) -> RouteResponse:
    try:
        return RouteResponse(200, route_fn(*args, **kwargs))
    except HTTPException as exc:
        return RouteResponse(exc.status_code, {"detail": exc.detail})


def rubric_payload(
    *,
    node_id: str = "ode_separable",
    user_answer: str = "This is separable; separate variables; integrate; ln|y|=x^2+C.",
    expected_answer: str | None = "ln|y|=x^2+C",
    include_debug: bool = False,
) -> dict:
    return {
        "node_id": node_id,
        "question": {
            "id": "q_api_rubric",
            "node_id": node_id,
            "question_type": "diagnostic",
            "prompt": "Solve dy/dx = 2xy.",
            "expected_answer": expected_answer,
            "tested_dimensions": ["trigger", "method", "transformation", "process", "calculation", "final_answer"],
            "solution_outline": "SECRET_SOLUTION_OUTLINE_DO_NOT_LEAK",
            "rubric": {
                "items": [
                    {
                        "id": "trigger_separable",
                        "description": "SECRET_RUBRIC_TRIGGER_DO_NOT_LEAK",
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
            "id": "a_api_rubric",
            "question_id": "q_api_rubric",
            "user_answer": user_answer,
        },
        "options": {"include_debug": include_debug},
    }


def false_pass_payload() -> dict:
    payload = rubric_payload(user_answer="ln|y|=x^2+C.")
    payload["question"]["id"] = "q_api_false_pass"
    payload["attempt"]["question_id"] = "q_api_false_pass"
    payload["attempt"]["id"] = "a_api_false_pass"
    return payload


def rule_only_payload() -> dict:
    return {
        "node_id": "ode_separable",
        "question": {
            "id": "q_api_rule_only",
            "node_id": "ode_separable",
            "question_type": "diagnostic",
            "prompt": "Classify the equation.",
        },
        "attempt": {
            "id": "a_api_rule_only",
            "question_id": "q_api_rule_only",
            "user_answer": "This is separable.",
        },
        "options": {"include_debug": False},
    }


def no_signal_payload() -> dict:
    payload = rule_only_payload()
    payload["question"]["id"] = "q_api_no_signal"
    payload["attempt"]["id"] = "a_api_no_signal"
    payload["attempt"]["question_id"] = "q_api_no_signal"
    payload["attempt"]["user_answer"] = "I do not know."
    return payload


def post_json(path: str, payload: dict):
    routes = {
        "/api/v1/score/evaluate": evaluate_score,
        "/api/v1/diagnosis/get": get_diagnosis,
        "/api/v1/next-action/get": get_next_action,
        "/api/v1/attempts/submit": submit_attempt,
    }
    return call_route(routes[path], deepcopy(payload))


def test_health_endpoint() -> None:
    response = call_route(health)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["phase"] == "phase_3_1_internal_dev_api"
    assert "scoring" in body["capabilities"]


def test_api_v1_routes_are_registered_on_app() -> None:
    route_paths = set(app.openapi()["paths"])

    assert "/api/v1/health" in route_paths
    assert "/api/v1/nodes" in route_paths
    assert "/api/v1/nodes/{node_id}" in route_paths
    assert "/api/v1/score/evaluate" in route_paths
    assert "/api/v1/attempts/submit" in route_paths


def test_node_list_endpoint() -> None:
    response = call_route(list_nodes)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] >= 16
    assert any(node["id"] == "ode_separable" for node in body["nodes"])


def test_node_detail_endpoint() -> None:
    response = call_route(get_node, "ode_separable")

    assert response.status_code == 200
    assert response.json()["node"]["id"] == "ode_separable"


def test_invalid_node_returns_404_api_error() -> None:
    response = call_route(get_node, "not_a_node")

    assert response.status_code == 404
    assert response.json()["detail"]["error_code"] == "node_not_found"


def test_score_endpoint_returns_only_scoring() -> None:
    response = post_json("/api/v1/score/evaluate", rubric_payload())

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"scoring"}
    assert "score_vector" in body["scoring"]


def test_score_endpoint_does_not_return_diagnosis_or_movement() -> None:
    body = post_json("/api/v1/score/evaluate", rubric_payload()).json()

    assert "diagnosis" not in body
    assert "movement" not in body
    assert "action" not in body
    assert "root_cause" not in str(body)


def test_score_endpoint_does_not_call_diagnosis_or_movement(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("score endpoint must not call diagnosis or movement engines")

    monkeypatch.setattr(DiagnosisEngine, "diagnose_detailed", fail)
    monkeypatch.setattr(RollbackEngine, "decide_rollback", fail)
    monkeypatch.setattr(ForwardEngine, "decide_forward", fail)

    response = post_json("/api/v1/score/evaluate", rubric_payload())

    assert response.status_code == 200


def test_diagnosis_endpoint_returns_partitioned_response() -> None:
    response = post_json("/api/v1/diagnosis/get", rubric_payload())

    assert response.status_code == 200
    body = response.json()
    assert {"scoring", "diagnosis", "movement", "action"} <= set(body)
    assert body["diagnosis"]["pass_state"] in {"pass", "partial_pass", "fail", "false_pass"}


def test_diagnosis_endpoint_movement_matches_engine_outputs() -> None:
    payload = false_pass_payload()
    response = post_json("/api/v1/diagnosis/get", payload)
    orchestrated = LearningOrchestrator().process(
        question_payload_to_model(payload["question"]),
        attempt_payload_to_model(payload["attempt"]),
        node_from_api(payload["node_id"]),
    )

    assert response.status_code == 200
    movement = response.json()["movement"]
    assert movement["rollback_nodes"] == orchestrated.rollback_decision.rollback_nodes
    assert movement["forward_nodes"] == orchestrated.forward_decision.forward_nodes


def test_submit_attempt_returns_full_loop() -> None:
    response = post_json("/api/v1/attempts/submit", rubric_payload())

    assert response.status_code == 200
    body = response.json()
    assert {"node", "scoring", "diagnosis", "movement", "action"} <= set(body)
    assert body["node"]["id"] == "ode_separable"


def test_next_action_does_not_contradict_rollback_or_forward() -> None:
    response = post_json("/api/v1/next-action/get", false_pass_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["forward_allowed"] is False
    assert body["forward_nodes"] == []
    assert body["recommended_actions"]
    assert body["next_action_hint"] == body["recommended_actions"][0]["reason"]


def test_false_pass_cannot_strong_forward_through_api() -> None:
    response = post_json("/api/v1/attempts/submit", false_pass_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["diagnosis"]["pass_state"] == "false_pass"
    assert body["movement"]["forward_allowed"] is False
    assert body["movement"]["forward_nodes"] == []


def test_rule_only_cannot_strong_forward_through_api() -> None:
    response = post_json("/api/v1/attempts/submit", rule_only_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["diagnosis"]["root_cause"] is None
    assert body["action"]["next_action_type"] == "need_more_evidence"
    assert body["movement"]["forward_allowed"] is False


def test_no_signal_returns_business_result_not_api_error() -> None:
    response = post_json("/api/v1/attempts/submit", no_signal_payload())

    assert response.status_code == 200
    body = response.json()
    assert body["diagnosis"]["pass_state"] == "fail"
    assert body["action"]["next_action_type"] == "need_more_evidence"


def test_score_overrides_rejected_by_public_api() -> None:
    payload = rubric_payload()
    payload["attempt"]["metadata"] = {"score_overrides": {"trigger": 100}}

    response = post_json("/api/v1/score/evaluate", payload)

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "forbidden_public_api_field"


def test_evidence_overrides_rejected_by_public_api() -> None:
    payload = rubric_payload()
    payload["attempt"]["metadata"] = {"evidence_overrides": {"trigger": "manual"}}

    response = post_json("/api/v1/attempts/submit", payload)

    assert response.status_code == 400
    assert response.json()["detail"]["field_path"] == "$.attempt.metadata.evidence_overrides"


def test_manual_override_rejected_by_public_api() -> None:
    payload = rubric_payload()
    payload["manual_override"] = True

    response = post_json("/api/v1/attempts/submit", payload)

    assert response.status_code == 400
    assert response.json()["detail"]["field_path"] == "$.manual_override"


def test_scenario_rejected_by_public_api() -> None:
    payload = rubric_payload()
    payload["attempt"]["metadata"] = {"scenario": "process_right_calculation_wrong"}

    response = post_json("/api/v1/attempts/submit", payload)

    assert response.status_code == 400
    assert response.json()["detail"]["field_path"] == "$.attempt.metadata.scenario"


def test_nested_override_field_rejected_recursively() -> None:
    payload = rubric_payload()
    payload["question"]["metadata"] = {"safe": [{"score_overrides": {"method": 100}}]}

    response = post_json("/api/v1/attempts/submit", payload)

    assert response.status_code == 400
    assert response.json()["detail"]["field_path"] == "$.question.metadata.safe[0].score_overrides"


def test_learner_response_does_not_expose_debug_trace_by_default() -> None:
    body = post_json("/api/v1/attempts/submit", rubric_payload()).json()

    assert "debug" not in body
    assert "scorer_results" not in str(body)
    assert "diagnosis_trace" not in str(body)


def test_debug_true_returns_debug_fields() -> None:
    body = post_json("/api/v1/attempts/submit", rubric_payload(include_debug=True)).json()

    assert "debug" in body
    assert "scorer_results" in body["debug"]
    assert "merge_notes" in body["debug"]
    assert "raw_rollback_level" in body["debug"]
    assert "raw_forward_level" in body["debug"]


def test_learner_safe_response_does_not_leak_answer_or_rubric_payload() -> None:
    payload = rubric_payload(expected_answer="SECRET_EXPECTED_ANSWER_DO_NOT_LEAK")
    payload["attempt"]["user_answer"] = "This is separable; separate variables; integrate."

    response_text = post_json("/api/v1/attempts/submit", payload).text

    assert "SECRET_EXPECTED_ANSWER_DO_NOT_LEAK" not in response_text
    assert "SECRET_SOLUTION_OUTLINE_DO_NOT_LEAK" not in response_text
    assert "SECRET_RUBRIC_TRIGGER_DO_NOT_LEAK" not in response_text


def test_rollback_nodes_empty_maps_to_rollback_required_false() -> None:
    body = post_json("/api/v1/attempts/submit", no_signal_payload()).json()

    assert body["movement"]["rollback_nodes"] == []
    assert body["movement"]["rollback_required"] is False
    assert "rollback_level" not in body["movement"]


def test_forward_nodes_empty_maps_to_forward_allowed_false() -> None:
    body = post_json("/api/v1/attempts/submit", false_pass_payload()).json()

    assert body["movement"]["forward_nodes"] == []
    assert body["movement"]["forward_allowed"] is False
    assert "forward_level" not in body["movement"]


def test_question_node_id_mismatch_returns_422() -> None:
    payload = rubric_payload()
    payload["question"]["node_id"] = "ode_first_order_linear"

    response = post_json("/api/v1/attempts/submit", payload)

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "question_node_mismatch"


def test_attempt_question_id_mismatch_returns_422() -> None:
    payload = rubric_payload()
    payload["attempt"]["question_id"] = "wrong_question"

    response = post_json("/api/v1/attempts/submit", payload)

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "attempt_question_mismatch"


def test_submit_attempt_matches_direct_orchestrator_outputs() -> None:
    payload = false_pass_payload()
    body = post_json("/api/v1/attempts/submit", payload).json()
    orchestrated = LearningOrchestrator().process(
        question_payload_to_model(payload["question"]),
        attempt_payload_to_model(payload["attempt"]),
        node_from_api(payload["node_id"]),
    )

    assert body["diagnosis"]["pass_state"] == orchestrated.diagnosis_result.pass_state.value
    assert body["diagnosis"]["root_cause"] == orchestrated.diagnosis_result.root_cause.value
    assert body["diagnosis"]["downstream_result_errors"] == [
        error.value for error in orchestrated.diagnosis_result.downstream_result_errors
    ]
    assert body["diagnosis"]["weak_signal_errors"] == [
        error.value for error in orchestrated.diagnosis_result.weak_signal_errors
    ]
    assert body["diagnosis"]["evidence_gap_errors"] == [
        error.value for error in orchestrated.diagnosis_result.evidence_gap_errors
    ]
    assert body["movement"]["rollback_nodes"] == orchestrated.rollback_decision.rollback_nodes
    assert body["movement"]["forward_nodes"] == orchestrated.forward_decision.forward_nodes


def test_orchestrator_explicit_movement_matches_diagnosis_compat_fields() -> None:
    payload = false_pass_payload()
    orchestrated = LearningOrchestrator().process(
        question_payload_to_model(payload["question"]),
        attempt_payload_to_model(payload["attempt"]),
        node_from_api(payload["node_id"]),
    )

    assert orchestrated.rollback_consistent is True
    assert orchestrated.forward_consistent is True
    assert orchestrated.rollback_decision.rollback_nodes == orchestrated.diagnosis_result.rollback_nodes
    assert orchestrated.forward_decision.forward_nodes == orchestrated.diagnosis_result.forward_nodes


def question_payload_to_model(payload: dict):
    from app.core.schemas import Question

    return Question(**deepcopy(payload))


def attempt_payload_to_model(payload: dict):
    from app.core.schemas import Attempt

    return Attempt(**deepcopy(payload))


def node_from_api(node_id: str):
    from app.api.v1.nodes import get_node_or_404

    return get_node_or_404(node_id)
