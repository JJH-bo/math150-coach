from __future__ import annotations

from app.core.enums import ErrorType, PassState, QuestionType, RollbackLevel
from app.core.schemas import Attempt, KnowledgeNode, Question
from app.services.diagnosis_engine import DiagnosisEngine
from app.services.scoring_engine import ScoringEngine


def linear_node() -> KnowledgeNode:
    return KnowledgeNode(
        id="ode_first_order_linear",
        name="一阶线性微分方程",
        type="method",
        status="available",
        prerequisites=["ode_general_special_solution", "ode_separable"],
        successors=["ode_integrating_factor"],
        core_dimensions=["trigger", "method", "transformation", "process", "calculation", "final_answer"],
        common_errors=["trigger_failure", "method_error", "calculation_error"],
        description="Sample first-order linear node.",
        trigger_patterns=["y' + P(x)y = Q(x)"],
        scoring_weights={
            "trigger": 0.2,
            "method": 0.2,
            "transformation": 0.2,
            "process": 0.15,
            "calculation": 0.15,
            "final_answer": 0.1,
        },
        rollback_policy={
            "trigger_failure": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "method_error": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "calculation_error": {"level": "r1_internal", "target_nodes": ["__self__"]},
        },
        pass_criteria={
            "min_overall": 80,
            "min_required_dimensions": {"trigger": 75, "method": 75, "calculation": 70},
            "max_primary_errors": 0,
            "allow_false_pass": False,
        },
        variant_policy={
            "template_families": ["standard_linear"],
            "parameter_focus": ["p_of_x", "q_of_x"],
            "validation_required": True,
        },
    )


def test_process_right_calculation_wrong_fails_without_broad_concept_rollback() -> None:
    node = linear_node()
    question = Question(
        id="q1",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Solve y' + y = e^x.",
        tested_dimensions=node.core_dimensions,
    )
    attempt = Attempt(
        id="a1",
        question_id="q1",
        user_answer="Method right, calculation wrong.",
        metadata={"scenario": "process_right_calculation_wrong"},
    )

    score_vector = ScoringEngine().evaluate(question, attempt, node)
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)
    pass_state = DiagnosisEngine().classify_pass_state(score_vector, error_vector, node)

    assert error_vector.has_error_type(ErrorType.CALCULATION_ERROR)
    calculation_error = error_vector.primary_errors()[0]
    assert calculation_error.suggested_rollback_level == RollbackLevel.R1_INTERNAL
    assert pass_state == PassState.FAIL


def test_answer_right_but_trigger_unclear_is_false_pass_not_full_pass() -> None:
    node = linear_node()
    question = Question(
        id="q2",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Solve y' + y = e^x.",
        tested_dimensions=node.core_dimensions,
    )
    attempt = Attempt(
        id="a2",
        question_id="q2",
        user_answer="Correct answer without method explanation.",
        metadata={"scenario": "answer_right_trigger_unclear"},
    )

    score_vector = ScoringEngine().evaluate(question, attempt, node)
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)
    pass_state = DiagnosisEngine().classify_pass_state(score_vector, error_vector, node)

    assert score_vector.final_answer.score >= 90
    assert error_vector.has_error_type(ErrorType.TRIGGER_FAILURE)
    assert error_vector.has_error_type(ErrorType.METHOD_ERROR)
    assert pass_state == PassState.FALSE_PASS
