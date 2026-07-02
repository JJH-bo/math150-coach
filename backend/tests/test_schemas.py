from __future__ import annotations

from app.core.enums import (
    ErrorType,
    ForwardLevel,
    NodeStatus,
    NodeType,
    PassState,
    QuestionType,
    RollbackLevel,
    ScoreDimension,
)
from app.core.schemas import (
    DiagnosisResult,
    DimensionScore,
    ErrorItem,
    ErrorVector,
    NodeAction,
    ReviewTask,
    ScoreVector,
)
from app.main import app


def test_enums_import_with_stable_values() -> None:
    assert NodeType.CONCEPT.value == "concept"
    assert NodeStatus.AVAILABLE.value == "available"
    assert QuestionType.DIAGNOSTIC.value == "diagnostic"
    assert ScoreDimension.FINAL_ANSWER.value == "final_answer"
    assert ErrorType.CALCULATION_ERROR.value == "calculation_error"
    assert PassState.FALSE_PASS.value == "false_pass"
    assert RollbackLevel.R1_INTERNAL.value == "r1_internal"
    assert ForwardLevel.P0_NONE.value == "p0_none"


def test_main_app_imports() -> None:
    assert app.title == "Math150 Coach Engine"


def test_score_vector_supports_notes_missing_dimensions_and_overall_score() -> None:
    score_vector = ScoreVector(
        concept=DimensionScore(score=80, evidence="Definition is correct.", notes="Good."),
        trigger=None,
        method=DimensionScore(score=90, evidence="Method is suitable."),
        final_answer=DimensionScore(score=0, evidence="Calculation led to wrong answer."),
    )

    assert score_vector.trigger is None
    assert score_vector.concept.evidence == "Definition is correct."
    assert score_vector.overall_score() == (80 + 90 + 0) / 3


def test_error_vector_supports_multiple_weighted_errors() -> None:
    error_vector = ErrorVector(
        errors=[
            ErrorItem(
                error_type=ErrorType.TRIGGER_FAILURE,
                weight=0.8,
                related_dimensions=[ScoreDimension.TRIGGER],
                evidence="Cannot name the trigger.",
                is_primary=True,
                suggested_rollback_level=RollbackLevel.R1_INTERNAL,
            ),
            ErrorItem(
                error_type=ErrorType.METHOD_ERROR,
                weight=0.5,
                related_dimensions=[ScoreDimension.METHOD],
                evidence="Method is weak.",
                is_primary=False,
                suggested_rollback_level=RollbackLevel.R2_PREREQUISITE,
            ),
        ]
    )

    assert len(error_vector.errors) == 2
    assert error_vector.primary_errors()[0].error_type == ErrorType.TRIGGER_FAILURE
    assert error_vector.secondary_errors()[0].error_type == ErrorType.METHOD_ERROR


def test_diagnosis_result_and_node_action_have_full_explanation_chain() -> None:
    score_vector = ScoreVector(
        trigger=DimensionScore(score=25, evidence="Trigger unclear."),
        method=DimensionScore(score=35, evidence="Method not justified."),
        final_answer=DimensionScore(score=95, evidence="Answer is correct."),
    )
    error_vector = ErrorVector(
        errors=[
            ErrorItem(
                error_type=ErrorType.TRIGGER_FAILURE,
                weight=0.8,
                related_dimensions=[ScoreDimension.TRIGGER],
                evidence="Correct answer without trigger evidence.",
                is_primary=True,
                suggested_rollback_level=RollbackLevel.R1_INTERNAL,
            )
        ]
    )

    result = DiagnosisResult(
        score_vector=score_vector,
        error_vector=error_vector,
        pass_state=PassState.FALSE_PASS,
        rollback_nodes=["ode_first_order_linear"],
        forward_nodes=[],
        rollback_level=RollbackLevel.R1_INTERNAL,
        forward_level=ForwardLevel.P0_NONE,
        explanation="Final answer is correct but trigger and method evidence are weak.",
        next_action_hint="Review trigger patterns before moving forward.",
    )

    action = NodeAction(
        rollback_nodes=result.rollback_nodes,
        forward_nodes=result.forward_nodes,
        review_tasks=[
            ReviewTask(
                node_id="ode_first_order_linear",
                reason="False pass on trigger recognition.",
                focus_dimensions=[ScoreDimension.TRIGGER],
                error_types=[ErrorType.TRIGGER_FAILURE],
            )
        ],
        node_status_updates={"ode_first_order_linear": NodeStatus.REVIEW},
        mastery_updates={"ode_first_order_linear": {"delta": -0.1}},
        explanation=result.explanation,
    )

    assert result.pass_state == PassState.FALSE_PASS
    assert result.rollback_level == RollbackLevel.R1_INTERNAL
    assert action.review_tasks[0].node_id == "ode_first_order_linear"
    assert action.mastery_updates["ode_first_order_linear"]["delta"] == -0.1
