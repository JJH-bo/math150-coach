from __future__ import annotations

from pathlib import Path

import yaml

from app.core.enums import ErrorType, ForwardLevel, QuestionType
from app.core.schemas import Attempt, ErrorItem, ErrorVector, KnowledgeNode, Question
from app.services.diagnosis_engine import DiagnosisEngine
from app.services.forward_engine import ForwardEngine
from app.services.rollback_engine import RollbackEngine
from app.services.scoring_engine import ScoringEngine


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ODE_NODES_PATH = PROJECT_ROOT / "backend" / "app" / "seed" / "ode_nodes.yaml"
GOLDEN_CASES_PATH = PROJECT_ROOT / "evals" / "golden_cases" / "ode_scoring_cases.yaml"


REQUIRED_NODE_FIELDS = {
    "id",
    "name",
    "type",
    "status",
    "prerequisites",
    "successors",
    "core_dimensions",
    "common_errors",
    "description",
    "trigger_patterns",
    "scoring_weights",
    "rollback_policy",
    "pass_criteria",
    "variant_policy",
}

REQUIRED_GOLDEN_CASE_FIELDS = {
    "question",
    "user_answer",
    "expected_scores",
    "expected_errors",
    "expected_pass_state",
    "expected_rollback_behavior",
}


def load_ode_nodes() -> list[KnowledgeNode]:
    with ODE_NODES_PATH.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return [KnowledgeNode(**node) for node in data["nodes"]]


def test_ode_nodes_yaml_has_at_least_10_valid_nodes_with_required_policy_fields() -> None:
    with ODE_NODES_PATH.open("r", encoding="utf-8") as file:
        raw_nodes = yaml.safe_load(file)["nodes"]

    assert len(raw_nodes) >= 10
    assert len(raw_nodes) >= 16

    for raw_node in raw_nodes:
        assert REQUIRED_NODE_FIELDS <= set(raw_node)
        assert raw_node["trigger_patterns"]
        assert raw_node["scoring_weights"]
        assert raw_node["rollback_policy"]
        assert raw_node["pass_criteria"]
        assert raw_node["variant_policy"]

    parsed_nodes = [KnowledgeNode(**node) for node in raw_nodes]
    assert len(parsed_nodes) >= 16


def test_ode_golden_cases_are_not_empty_placeholders() -> None:
    with GOLDEN_CASES_PATH.open("r", encoding="utf-8") as file:
        cases = yaml.safe_load(file)["cases"]

    assert len(cases) >= 5
    expected_ids = {
        "ode_separable_complete_correct",
        "ode_separable_process_right_calculation_wrong",
        "ode_linear_answer_right_trigger_unclear",
        "ode_homogeneous_trigger_failure",
        "ode_bernoulli_transformation_failure",
    }
    assert expected_ids <= {case["id"] for case in cases}

    for case in cases:
        assert REQUIRED_GOLDEN_CASE_FIELDS <= set(case)
        assert case["question"]["prompt"]
        assert case["user_answer"]
        assert case["expected_scores"]
        assert "explanation" in case["expected_rollback_behavior"]


def test_ordinary_calculation_error_does_not_return_all_prerequisites() -> None:
    node = KnowledgeNode(
        id="ode_test_node",
        name="Test node",
        type="method",
        status="available",
        prerequisites=["pre_a", "pre_b", "pre_c"],
        successors=["next_a"],
        core_dimensions=["calculation", "final_answer"],
        common_errors=["calculation_error"],
        description="Node with several prerequisites.",
        trigger_patterns=["test"],
        scoring_weights={"calculation": 0.5, "final_answer": 0.5},
        rollback_policy={
            "calculation_error": {
                "level": "r1_internal",
                "target_nodes": ["__self__"],
                "notes": "Local calculation only.",
            }
        },
        pass_criteria={
            "min_overall": 80,
            "min_required_dimensions": {"calculation": 70},
            "max_primary_errors": 0,
            "allow_false_pass": False,
        },
        variant_policy={"template_families": ["test"], "parameter_focus": ["test"], "validation_required": True},
    )
    error_vector = ErrorVector(
        errors=[
            ErrorItem(
                error_type=ErrorType.CALCULATION_ERROR,
                weight=0.85,
                related_dimensions=["calculation", "final_answer"],
                evidence="Wrong integral after correct setup.",
                is_primary=True,
                suggested_rollback_level="r1_internal",
            )
        ]
    )

    rollback_nodes = RollbackEngine().select_rollback_nodes(error_vector, node)

    assert rollback_nodes == ["ode_test_node"]
    assert set(rollback_nodes) != set(node.prerequisites)
    assert len(rollback_nodes) < len(node.prerequisites)


def test_process_right_calculation_wrong_only_rolls_back_calculation_related_node() -> None:
    node = next(node for node in load_ode_nodes() if node.id == "ode_separable")
    question = Question(
        id="q_calc",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Solve dy/dx=2xy.",
        tested_dimensions=node.core_dimensions,
    )
    attempt = Attempt(
        id="a_calc",
        question_id="q_calc",
        user_answer="Correct setup but wrong integral.",
        metadata={"scenario": "process_right_calculation_wrong"},
    )

    score_vector = ScoringEngine().evaluate(question, attempt, node)
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)
    rollback_nodes = RollbackEngine().select_rollback_nodes(error_vector, node)
    forward_level = ForwardEngine().determine_forward_level(score_vector, error_vector, node)

    assert score_vector.method.score >= 85
    assert score_vector.transformation.score >= 80
    assert score_vector.final_answer.score == 0
    assert rollback_nodes == ["ode_separable"]
    assert set(rollback_nodes) != set(node.prerequisites)
    assert forward_level == ForwardLevel.P0_NONE


def test_answer_right_trigger_unclear_cannot_strong_forward() -> None:
    node = next(node for node in load_ode_nodes() if node.id == "ode_first_order_linear")
    question = Question(
        id="q_false_pass",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Solve y' + y = e^x.",
        tested_dimensions=node.core_dimensions,
    )
    attempt = Attempt(
        id="a_false_pass",
        question_id="q_false_pass",
        user_answer="Correct final answer but no trigger explanation.",
        metadata={"scenario": "answer_right_trigger_unclear"},
    )

    score_vector = ScoringEngine().evaluate(question, attempt, node)
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)
    forward_level = ForwardEngine().determine_forward_level(score_vector, error_vector, node)
    forward_nodes = ForwardEngine().select_forward_nodes(score_vector, error_vector, node)
    pass_state = DiagnosisEngine().classify_pass_state(score_vector, error_vector, node)

    assert pass_state.value in {"false_pass", "partial_pass"}
    assert forward_level != ForwardLevel.P3_STRONG
    assert forward_nodes == []
