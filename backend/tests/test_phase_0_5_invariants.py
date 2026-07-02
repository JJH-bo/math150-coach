from __future__ import annotations

from pathlib import Path

import yaml

from app.core.enums import ErrorType, ForwardLevel, PassState, QuestionType, RollbackLevel
from app.core.schemas import (
    Attempt,
    DimensionScore,
    ErrorItem,
    ErrorVector,
    KnowledgeNode,
    Question,
    ScoreVector,
)
from app.services.diagnosis_engine import DiagnosisEngine
from app.services.forward_engine import ForwardEngine
from app.services.rollback_engine import RollbackEngine
from app.services.scoring_engine import ScoringEngine


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ODE_NODES_PATH = PROJECT_ROOT / "backend" / "app" / "seed" / "ode_nodes.yaml"


def load_node(node_id: str) -> KnowledgeNode:
    with ODE_NODES_PATH.open("r", encoding="utf-8") as file:
        nodes = yaml.safe_load(file)["nodes"]
    return next(KnowledgeNode(**node) for node in nodes if node["id"] == node_id)


def make_question(node: KnowledgeNode, scenario: str = "diagnostic") -> Question:
    return Question(
        id=f"q_{node.id}_{scenario}",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Phase 0.5 invariant test question.",
        tested_dimensions=node.core_dimensions,
    )


def test_score_vector_invariants_and_overall_ignores_none() -> None:
    score_vector = ScoreVector(
        concept=DimensionScore(score=80, evidence="Concept evidence.", notes="Concept note."),
        trigger=None,
        method=DimensionScore(score=100, evidence="Method evidence.", notes="Method note."),
        final_answer=DimensionScore(score=20, evidence="Answer evidence.", notes="Answer note."),
    )

    assert score_vector.trigger is None
    assert score_vector.concept.score == 80
    assert score_vector.concept.evidence == "Concept evidence."
    assert score_vector.concept.notes == "Concept note."
    assert score_vector.overall_score() == (80 + 100 + 20) / 3


def test_overall_score_alone_cannot_create_pass_or_strong_forward() -> None:
    node = load_node("ode_first_order_linear")
    score_vector = ScoreVector(final_answer=DimensionScore(score=100, evidence="Correct final answer only."))
    error_vector = ErrorVector(errors=[])

    pass_state = DiagnosisEngine().classify_pass_state(score_vector, error_vector, node)
    forward_level = ForwardEngine().determine_forward_level(score_vector, error_vector, node)

    assert score_vector.overall_score() == 100
    assert pass_state != PassState.PASS
    assert forward_level not in {ForwardLevel.P2_NORMAL, ForwardLevel.P3_STRONG}


def test_error_vector_weight_thresholds_are_automatic_and_multi_label() -> None:
    primary = ErrorItem(
        error_type=ErrorType.TRIGGER_FAILURE,
        weight=0.7,
        related_dimensions=["trigger"],
        evidence="Trigger evidence.",
        suggested_rollback_level=RollbackLevel.R1_INTERNAL,
    )
    secondary = ErrorItem(
        error_type=ErrorType.METHOD_ERROR,
        weight=0.4,
        related_dimensions=["method"],
        evidence="Method evidence.",
        suggested_rollback_level=RollbackLevel.R2_PREREQUISITE,
    )
    weak = ErrorItem(
        error_type=ErrorType.EXPRESSION_WEAKNESS,
        weight=0.2,
        related_dimensions=["expression"],
        evidence="Expression evidence.",
        suggested_rollback_level=RollbackLevel.R1_INTERNAL,
    )
    error_vector = ErrorVector(errors=[primary, secondary, weak])

    assert len(error_vector.errors) == 3
    assert primary.is_primary is True
    assert secondary.is_primary is False
    assert error_vector.primary_errors() == [primary]
    assert error_vector.secondary_errors() == [secondary]
    for error in error_vector.errors:
        assert error.related_dimensions
        assert error.evidence
        assert error.suggested_rollback_level


def test_process_right_calculation_wrong_has_precise_local_rollback() -> None:
    node = load_node("ode_separable")
    question = make_question(node, "calculation_wrong")
    attempt = Attempt(
        id="a_calc_wrong",
        question_id=question.id,
        user_answer="Correct separation and method, wrong integral.",
        metadata={"scenario": "process_right_calculation_wrong"},
    )

    score_vector = ScoringEngine().evaluate(question, attempt, node)
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)
    pass_state = DiagnosisEngine().classify_pass_state(score_vector, error_vector, node)
    rollback_nodes = RollbackEngine().select_rollback_nodes(error_vector, node)
    forward_level = ForwardEngine().determine_forward_level(score_vector, error_vector, node)

    assert score_vector.method.score >= 85
    assert score_vector.transformation.score >= 80
    assert score_vector.calculation.score < 30
    assert score_vector.final_answer.score <= 5
    assert pass_state != PassState.PASS
    assert rollback_nodes == [node.id]
    assert set(rollback_nodes) != set(node.prerequisites)
    assert forward_level != ForwardLevel.P3_STRONG


def test_answer_right_trigger_unclear_is_false_pass_and_unlocks_no_migration_node() -> None:
    node = KnowledgeNode(
        id="ode_false_pass_guard",
        name="False pass guard",
        type="method",
        status="available",
        prerequisites=["ode_general_special_solution", "ode_separable"],
        successors=["ode_application_modeling"],
        core_dimensions=["trigger", "method", "transformation", "calculation", "final_answer"],
        common_errors=["trigger_failure", "method_error"],
        description="Custom node for false pass guard.",
        trigger_patterns=["standard form"],
        scoring_weights={"trigger": 0.25, "method": 0.25, "transformation": 0.2, "calculation": 0.15, "final_answer": 0.15},
        rollback_policy={
            "trigger_failure": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "method_error": {"level": "r1_internal", "target_nodes": ["__self__"]},
        },
        pass_criteria={
            "min_overall": 80,
            "min_required_dimensions": {"trigger": 75, "method": 75},
            "max_primary_errors": 0,
            "allow_false_pass": False,
        },
        variant_policy={"template_families": ["guard"], "parameter_focus": ["guard"], "validation_required": True},
    )
    question = make_question(node, "false_pass")
    attempt = Attempt(
        id="a_false_pass_guard",
        question_id=question.id,
        user_answer="Correct answer but no method explanation.",
        metadata={"scenario": "answer_right_trigger_unclear"},
    )

    score_vector = ScoringEngine().evaluate(question, attempt, node)
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)
    pass_state = DiagnosisEngine().classify_pass_state(score_vector, error_vector, node)
    forward_level = ForwardEngine().determine_forward_level(score_vector, error_vector, node)
    forward_nodes = ForwardEngine().select_forward_nodes(score_vector, error_vector, node)

    assert score_vector.final_answer.score >= 90
    assert score_vector.trigger.score < 60
    assert score_vector.method.score < 60
    assert pass_state in {PassState.FALSE_PASS, PassState.PARTIAL_PASS}
    assert forward_level != ForwardLevel.P3_STRONG
    assert "ode_application_modeling" not in forward_nodes
    assert forward_nodes == []


def test_trigger_failure_is_primary_and_not_misread_as_calculation_only() -> None:
    node = load_node("ode_homogeneous_first_order")
    question = make_question(node, "trigger_failure")
    attempt = Attempt(
        id="a_trigger_failure",
        question_id=question.id,
        user_answer="Wrong direct integration route.",
        metadata={"scenario": "trigger_failure"},
    )

    score_vector = ScoringEngine().evaluate(question, attempt, node)
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)
    rollback_nodes = RollbackEngine().select_rollback_nodes(error_vector, node)

    trigger_errors = [error for error in error_vector.errors if error.error_type == ErrorType.TRIGGER_FAILURE]
    assert trigger_errors and trigger_errors[0].is_primary
    assert not (len(error_vector.errors) == 1 and error_vector.errors[0].error_type == ErrorType.CALCULATION_ERROR)
    assert rollback_nodes
    assert rollback_nodes[0] in {"ode_homogeneous_first_order", "ode_separable", "ode_first_order_linear"}
    assert set(rollback_nodes) != set(node.prerequisites)


def test_transformation_failure_targets_transformation_or_method_prerequisite_not_all_basics() -> None:
    node = load_node("ode_bernoulli")
    question = make_question(node, "transformation_failure")
    attempt = Attempt(
        id="a_transformation_failure",
        question_id=question.id,
        user_answer="Recognizes Bernoulli but uses wrong substitution.",
        metadata={"scenario": "transformation_failure"},
    )

    score_vector = ScoringEngine().evaluate(question, attempt, node)
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)
    rollback_nodes = RollbackEngine().select_rollback_nodes(error_vector, node)

    transformation_errors = [error for error in error_vector.errors if error.error_type == ErrorType.TRANSFORMATION_ERROR]
    assert transformation_errors and transformation_errors[0].is_primary
    assert rollback_nodes[0] in {"ode_bernoulli", "ode_first_order_linear"}
    assert set(rollback_nodes) != set(node.prerequisites)
    assert "ode_basic_concept" not in rollback_nodes


def test_rollback_safety_all_prerequisites_requires_allowed_r4_reason() -> None:
    node = KnowledgeNode(
        id="ode_r4_guard",
        name="R4 guard",
        type="synthesis",
        status="available",
        prerequisites=["pre_type_a", "pre_type_b"],
        successors=[],
        core_dimensions=["trigger", "method", "process"],
        common_errors=["synthesis_failure", "trigger_failure"],
        description="Custom R4 guard node.",
        trigger_patterns=["compound task"],
        scoring_weights={"trigger": 0.3, "method": 0.3, "process": 0.4},
        rollback_policy={},
        pass_criteria={"min_overall": 80, "min_required_dimensions": {"trigger": 75}, "max_primary_errors": 0},
        variant_policy={"template_families": ["guard"], "parameter_focus": ["guard"], "validation_required": True},
    )
    allowed_r4 = ErrorVector(
        errors=[
            ErrorItem(
                error_type=ErrorType.SYNTHESIS_FAILURE,
                weight=0.95,
                related_dimensions=["trigger", "method", "process"],
                evidence="Cannot decompose the chapter-level task.",
                suggested_rollback_level=RollbackLevel.R4_CHAPTER_FRAMEWORK,
            )
        ]
    )
    ordinary_r4_request = ErrorVector(
        errors=[
            ErrorItem(
                error_type=ErrorType.TRIGGER_FAILURE,
                weight=0.95,
                related_dimensions=["trigger"],
                evidence="Single-question trigger miss should not become R4.",
                suggested_rollback_level=RollbackLevel.R4_CHAPTER_FRAMEWORK,
            )
        ]
    )

    rollback_engine = RollbackEngine()
    allowed_nodes = rollback_engine.select_rollback_nodes(allowed_r4, node)
    ordinary_nodes = rollback_engine.select_rollback_nodes(ordinary_r4_request, node)

    assert set(allowed_nodes) == set(node.prerequisites)
    assert rollback_engine.determine_rollback_level(allowed_r4) == RollbackLevel.R4_CHAPTER_FRAMEWORK
    assert set(ordinary_nodes) != set(node.prerequisites)
    assert rollback_engine.determine_rollback_level(ordinary_r4_request) != RollbackLevel.R4_CHAPTER_FRAMEWORK


def test_forward_safety_final_answer_alone_and_p3_high_standard() -> None:
    node = KnowledgeNode(
        id="ode_forward_guard",
        name="Forward guard",
        type="method",
        status="available",
        prerequisites=[],
        successors=["next_regular", "next_challenge"],
        core_dimensions=["trigger", "method", "transformation", "calculation", "final_answer"],
        common_errors=[],
        description="Custom forward guard node.",
        trigger_patterns=["guard"],
        scoring_weights={"trigger": 0.22, "method": 0.22, "transformation": 0.22, "calculation": 0.22, "final_answer": 0.12},
        rollback_policy={},
        pass_criteria={
            "min_overall": 80,
            "min_required_dimensions": {"trigger": 75, "method": 75, "transformation": 75, "calculation": 70},
            "max_primary_errors": 0,
        },
        variant_policy={"template_families": ["guard"], "parameter_focus": ["guard"], "validation_required": True},
    )

    final_only = ScoreVector(final_answer=DimensionScore(score=100, evidence="Answer only."))
    almost_strong = ScoreVector(
        trigger=DimensionScore(score=95, evidence="Strong trigger."),
        method=DimensionScore(score=95, evidence="Strong method."),
        transformation=DimensionScore(score=89, evidence="Not high enough for P3."),
        calculation=DimensionScore(score=95, evidence="Strong calculation."),
        final_answer=DimensionScore(score=100, evidence="Correct."),
    )
    strong = ScoreVector(
        trigger=DimensionScore(score=95, evidence="Strong trigger."),
        method=DimensionScore(score=95, evidence="Strong method."),
        transformation=DimensionScore(score=95, evidence="Strong transformation."),
        calculation=DimensionScore(score=95, evidence="Strong calculation."),
        final_answer=DimensionScore(score=100, evidence="Correct."),
    )
    error_vector = ErrorVector(errors=[])
    forward_engine = ForwardEngine()

    assert forward_engine.determine_forward_level(final_only, error_vector, node) not in {
        ForwardLevel.P2_NORMAL,
        ForwardLevel.P3_STRONG,
    }
    assert forward_engine.determine_forward_level(almost_strong, error_vector, node) == ForwardLevel.P2_NORMAL
    assert forward_engine.determine_forward_level(strong, error_vector, node) == ForwardLevel.P3_STRONG
