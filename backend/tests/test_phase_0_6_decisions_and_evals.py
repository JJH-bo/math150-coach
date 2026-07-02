from __future__ import annotations

from pathlib import Path

import yaml

from app.core.enums import ErrorType, ForwardLevel, PassState, RollbackLevel
from app.core.schemas import (
    DiagnosisResult,
    DimensionScore,
    ErrorItem,
    ErrorVector,
    KnowledgeNode,
    ScoreVector,
)
from app.services.forward_engine import ForwardEngine
from app.services.rollback_engine import RollbackEngine


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ODE_NODES_PATH = PROJECT_ROOT / "backend" / "app" / "seed" / "ode_nodes.yaml"


def decision_node() -> KnowledgeNode:
    return KnowledgeNode(
        id="ode_decision_guard",
        name="Decision guard",
        type="method",
        status="available",
        prerequisites=["pre_a", "pre_b"],
        successors=["next_a", "next_b", "next_c"],
        core_dimensions=["trigger", "method", "transformation", "calculation", "final_answer"],
        common_errors=["trigger_failure", "calculation_error", "synthesis_failure"],
        description="Node for decision tests.",
        trigger_patterns=["guard"],
        scoring_weights={
            "trigger": 0.22,
            "method": 0.22,
            "transformation": 0.22,
            "calculation": 0.22,
            "final_answer": 0.12,
        },
        rollback_policy={
            "trigger_failure": {"level": "r2_prerequisite", "target_nodes": ["pre_a"]},
            "calculation_error": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "synthesis_failure": {"level": "r4_chapter_framework", "target_nodes": ["pre_a", "pre_b"]},
        },
        pass_criteria={
            "min_overall": 80,
            "min_required_dimensions": {
                "trigger": 75,
                "method": 75,
                "transformation": 75,
                "calculation": 70,
            },
            "max_primary_errors": 0,
        },
        variant_policy={"template_families": ["guard"], "parameter_focus": ["guard"], "validation_required": True},
    )


def test_ode_yaml_has_no_r4_for_ordinary_error_types() -> None:
    allowed_r4 = {"knowledge_confusion", "synthesis_failure"}
    with ODE_NODES_PATH.open("r", encoding="utf-8") as file:
        nodes = yaml.safe_load(file)["nodes"]

    violations: list[str] = []
    for node in nodes:
        for error_type, policy in node.get("rollback_policy", {}).items():
            if policy.get("level") == RollbackLevel.R4_CHAPTER_FRAMEWORK.value and error_type not in allowed_r4:
                violations.append(f"{node['id']}:{error_type}")

    assert violations == []


def test_forward_decision_p1_p2_p3_have_distinct_behavior() -> None:
    node = decision_node()
    engine = ForwardEngine()
    no_errors = ErrorVector(errors=[])

    p1_scores = ScoreVector(
        trigger=DimensionScore(score=72, evidence="Near threshold."),
        method=DimensionScore(score=72, evidence="Near threshold."),
        transformation=DimensionScore(score=78, evidence="Adequate."),
        calculation=DimensionScore(score=78, evidence="Adequate."),
        final_answer=DimensionScore(score=90, evidence="Correct."),
    )
    p2_scores = ScoreVector(
        trigger=DimensionScore(score=82, evidence="Good."),
        method=DimensionScore(score=82, evidence="Good."),
        transformation=DimensionScore(score=82, evidence="Good."),
        calculation=DimensionScore(score=82, evidence="Good."),
        final_answer=DimensionScore(score=82, evidence="Good."),
    )
    p3_scores = ScoreVector(
        trigger=DimensionScore(score=95, evidence="Strong."),
        method=DimensionScore(score=95, evidence="Strong."),
        transformation=DimensionScore(score=95, evidence="Strong."),
        calculation=DimensionScore(score=95, evidence="Strong."),
        final_answer=DimensionScore(score=95, evidence="Strong."),
    )

    p1 = engine.decide_forward(p1_scores, no_errors, node)
    p2 = engine.decide_forward(p2_scores, no_errors, node)
    p3 = engine.decide_forward(p3_scores, no_errors, node)

    assert p1.level == ForwardLevel.P1_PARTIAL
    assert p1.forward_nodes == []
    assert p1.blocked_nodes == node.successors
    assert p1.allowed_training_modes == ["current_node_variant", "direct_review"]

    assert p2.level == ForwardLevel.P2_NORMAL
    assert p2.forward_nodes == ["next_a"]
    assert p2.blocked_nodes == ["next_b", "next_c"]

    assert p3.level == ForwardLevel.P3_STRONG
    assert p3.forward_nodes == ["next_a", "next_b"]
    assert p3.blocked_nodes == ["next_c"]


def test_forward_decision_false_pass_is_p0_with_no_forward_nodes() -> None:
    node = decision_node()
    false_pass_scores = ScoreVector(
        trigger=DimensionScore(score=25, evidence="Cannot identify trigger."),
        method=DimensionScore(score=35, evidence="Cannot explain method."),
        transformation=DimensionScore(score=75, evidence="Some transformation."),
        calculation=DimensionScore(score=90, evidence="Good calculation."),
        final_answer=DimensionScore(score=95, evidence="Correct final answer."),
    )

    decision = ForwardEngine().decide_forward(false_pass_scores, ErrorVector(errors=[]), node)

    assert decision.level == ForwardLevel.P0_NONE
    assert decision.forward_nodes == []
    assert decision.blocked_nodes == node.successors
    assert "False-pass" in decision.reason


def test_rollback_decision_for_calculation_error_explains_targeted_local_rollback() -> None:
    node = decision_node()
    error_vector = ErrorVector(
        errors=[
            ErrorItem(
                error_type=ErrorType.CALCULATION_ERROR,
                weight=0.85,
                related_dimensions=["calculation", "final_answer"],
                evidence="Computation failed after correct method.",
                suggested_rollback_level=RollbackLevel.R1_INTERNAL,
            )
        ]
    )

    decision = RollbackEngine().decide_rollback(error_vector, node)

    assert decision.level == RollbackLevel.R1_INTERNAL
    assert decision.rollback_nodes == [node.id]
    assert decision.is_chapter_framework_rollback is False
    assert "did not return all prerequisites" in decision.explanation


def test_rollback_decision_for_trigger_error_uses_targeted_prerequisite_not_all() -> None:
    node = decision_node()
    error_vector = ErrorVector(
        errors=[
            ErrorItem(
                error_type=ErrorType.TRIGGER_FAILURE,
                weight=0.9,
                related_dimensions=["trigger"],
                evidence="Missed the type trigger.",
                suggested_rollback_level=RollbackLevel.R2_PREREQUISITE,
            )
        ]
    )

    decision = RollbackEngine().decide_rollback(error_vector, node)

    assert decision.level == RollbackLevel.R2_PREREQUISITE
    assert decision.rollback_nodes == ["pre_a"]
    assert set(decision.rollback_nodes) != set(node.prerequisites)
    assert decision.blocked_reason == "targeted_rollback_prevents_full_prerequisite_reset"


def test_rollback_decision_allows_r4_only_for_framework_errors() -> None:
    node = decision_node()
    legal_r4 = ErrorVector(
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
    illegal_r4 = ErrorVector(
        errors=[
            ErrorItem(
                error_type=ErrorType.TRIGGER_FAILURE,
                weight=0.95,
                related_dimensions=["trigger"],
                evidence="Single trigger miss should not trigger R4.",
                suggested_rollback_level=RollbackLevel.R4_CHAPTER_FRAMEWORK,
            )
        ]
    )

    legal_decision = RollbackEngine().decide_rollback(legal_r4, node)
    illegal_decision = RollbackEngine().decide_rollback(illegal_r4, node)

    assert legal_decision.level == RollbackLevel.R4_CHAPTER_FRAMEWORK
    assert set(legal_decision.rollback_nodes) == set(node.prerequisites)
    assert legal_decision.is_chapter_framework_rollback is True

    assert illegal_decision.level != RollbackLevel.R4_CHAPTER_FRAMEWORK
    assert set(illegal_decision.rollback_nodes) != set(node.prerequisites)
    assert illegal_decision.blocked_reason == "illegal_r4_downgraded_to_targeted_rollback"


def test_diagnosis_result_has_learner_explanation_field() -> None:
    result = DiagnosisResult(
        score_vector=ScoreVector(final_answer=DimensionScore(score=95, evidence="Correct.")),
        error_vector=ErrorVector(errors=[]),
        pass_state=PassState.PASS,
        rollback_nodes=[],
        forward_nodes=["next_a"],
        rollback_level=RollbackLevel.R1_INTERNAL,
        forward_level=ForwardLevel.P2_NORMAL,
        explanation="debug explanation",
        learner_explanation="You can move to the next node.",
        next_action_hint="Continue.",
    )

    assert result.learner_explanation == "You can move to the next node."
