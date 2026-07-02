from __future__ import annotations

import importlib.util
from pathlib import Path

from app.core.enums import ErrorType, ForwardLevel, NodeType, PassState, QuestionType, RollbackLevel, ScoreDimension
from app.core.schemas import Attempt, ErrorItem, ErrorVector, KnowledgeNode, Question
from app.services.composite_scoring_engine import CompositeScoringEngine
from app.services.diagnosis_engine import DiagnosisEngine
from app.services.forward_engine import ForwardEngine
from app.services.rollback_engine import RollbackEngine


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def movement_node(
    *,
    node_id: str = "ode_movement_node",
    node_type: str = "method",
    prerequisites: list[str] | None = None,
    successors: list[str] | None = None,
    common_errors: list[str] | None = None,
) -> KnowledgeNode:
    return KnowledgeNode(
        id=node_id,
        name="Phase 2.2 movement node",
        type=node_type,
        status="available",
        prerequisites=prerequisites or ["pre_concept", "pre_method", "pre_transform"],
        successors=successors or ["next_direct", "next_synthesis", "next_challenge"],
        core_dimensions=["concept", "trigger", "method", "transformation", "process", "calculation", "final_answer", "expression"],
        common_errors=common_errors
        or [
            "concept_gap",
            "trigger_failure",
            "method_error",
            "transformation_error",
            "process_gap",
            "calculation_error",
            "condition_miss",
            "expression_weakness",
        ],
        description="Movement integration red-team node.",
        trigger_patterns=["movement"],
        scoring_weights={
            "concept": 0.10,
            "trigger": 0.16,
            "method": 0.16,
            "transformation": 0.16,
            "process": 0.14,
            "calculation": 0.14,
            "final_answer": 0.10,
            "expression": 0.04,
        },
        rollback_policy={
            "concept_gap": {"level": "r2_prerequisite", "target_nodes": ["pre_concept"]},
            "trigger_failure": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "method_error": {"level": "r2_prerequisite", "target_nodes": ["pre_method"]},
            "transformation_error": {"level": "r2_prerequisite", "target_nodes": ["pre_transform"]},
            "process_gap": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "calculation_error": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "condition_miss": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "expression_weakness": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "knowledge_confusion": {"level": "r4_chapter_framework", "target_nodes": ["pre_concept", "pre_method"]},
            "synthesis_failure": {"level": "r4_chapter_framework", "target_nodes": ["pre_method", "pre_transform"]},
        },
        pass_criteria={
            "min_overall": 80,
            "min_required_dimensions": {"trigger": 70, "method": 70, "transformation": 70, "process": 65},
            "max_primary_errors": 0,
        },
        variant_policy={"template_families": ["movement"], "parameter_focus": ["movement"], "validation_required": True},
    )


def manual_result(scores: dict[str, float], node: KnowledgeNode | None = None, question: Question | None = None):
    node = node or movement_node()
    question = question or Question(
        id=f"q_{node.id}",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Movement integration diagnostic question.",
        tested_dimensions=node.core_dimensions,
    )
    attempt = Attempt(
        id=f"a_{question.id}",
        question_id=question.id,
        user_answer="manual movement answer",
        metadata={
            "score_overrides": scores,
            "evidence_overrides": {dimension: f"movement evidence for {dimension}" for dimension in scores},
        },
    )
    composite = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    return DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)


def scored_result(question: Question, answer: str, node: KnowledgeNode | None = None):
    node = node or movement_node(node_id=question.node_id)
    attempt = Attempt(id=f"a_{question.id}", question_id=question.id, user_answer=answer)
    composite = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    return DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)


def assert_engine_owned_movement(result, node: KnowledgeNode) -> None:
    rollback = RollbackEngine().decide_rollback(result.error_vector, node)
    forward = ForwardEngine().decide_forward(result.score_vector, result.error_vector, node)

    assert result.rollback_nodes == rollback.rollback_nodes
    assert result.rollback_level == rollback.level
    assert result.forward_nodes == forward.forward_nodes
    assert result.forward_level == forward.level


def assert_not_all_prerequisites(result, node: KnowledgeNode) -> None:
    assert set(result.rollback_nodes) != set(node.prerequisites)


def test_false_pass_blocks_p2_p3_and_prefers_review_action() -> None:
    node = movement_node()
    result = manual_result({"trigger": 20, "method": 25, "process": 30, "calculation": 80, "final_answer": 95}, node)

    assert result.pass_state == PassState.FALSE_PASS
    assert result.forward_level == ForwardLevel.P0_NONE
    assert result.forward_nodes == []
    assert result.recommended_actions[0].action_type in {"trigger_drill", "method_comparison"}
    assert_engine_owned_movement(result, node)


def test_rule_only_cannot_strong_forward_and_needs_more_evidence() -> None:
    node = movement_node()
    question = Question(id="q_rule_only_move", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="Classify the equation.")
    result = scored_result(question, "This is separable.", node)

    assert result.diagnosis_trace.rule_only is True
    assert result.forward_level in {ForwardLevel.P0_NONE, ForwardLevel.P1_PARTIAL}
    assert result.forward_level not in {ForwardLevel.P2_NORMAL, ForwardLevel.P3_STRONG}
    assert result.recommended_actions[0].action_type == "need_more_evidence"
    assert_engine_owned_movement(result, node)


def test_no_signal_fails_without_full_prerequisite_rollback() -> None:
    node = movement_node()
    question = Question(id="q_no_signal_move", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="Classify the equation.")
    result = scored_result(question, "I am not sure.", node)

    assert result.pass_state == PassState.FAIL
    assert result.root_cause is None
    assert result.recommended_actions[0].action_type == "need_more_evidence"
    assert result.forward_level == ForwardLevel.P0_NONE
    assert_not_all_prerequisites(result, node)


def test_calculation_error_stays_on_current_node_not_concept_or_method_prereq() -> None:
    node = movement_node()
    result = manual_result({"trigger": 92, "method": 91, "transformation": 90, "process": 86, "calculation": 20, "final_answer": 0}, node)

    assert result.root_cause == ErrorType.CALCULATION_ERROR
    assert result.rollback_level == RollbackLevel.R1_INTERNAL
    assert result.rollback_nodes == [node.id]
    assert "pre_concept" not in result.rollback_nodes
    assert "pre_method" not in result.rollback_nodes
    assert result.recommended_actions[0].action_type == "calculation_repair"


def test_trigger_failure_rolls_back_precisely_and_blocks_strong_forward() -> None:
    node = movement_node()
    result = manual_result({"trigger": 10, "method": 20, "transformation": 25, "process": 30, "calculation": 50, "final_answer": 0}, node)

    assert result.root_cause == ErrorType.TRIGGER_FAILURE
    assert result.rollback_nodes == [node.id]
    assert result.forward_level == ForwardLevel.P0_NONE
    assert_not_all_prerequisites(result, node)


def test_method_error_uses_one_direct_prerequisite_not_all_prerequisites() -> None:
    node = movement_node()
    result = manual_result({"trigger": 82, "method": 20, "process": 25, "calculation": 30, "final_answer": 0}, node)

    assert result.root_cause == ErrorType.METHOD_ERROR
    assert result.rollback_level == RollbackLevel.R2_PREREQUISITE
    assert result.rollback_nodes == ["pre_method"]
    assert_not_all_prerequisites(result, node)


def test_transformation_error_targets_transformation_prerequisite() -> None:
    node = movement_node()
    result = manual_result({"trigger": 84, "method": 82, "transformation": 15, "process": 35, "calculation": 45, "final_answer": 0}, node)

    assert result.root_cause == ErrorType.TRANSFORMATION_ERROR
    assert result.rollback_level == RollbackLevel.R2_PREREQUISITE
    assert result.rollback_nodes == ["pre_transform"]
    assert result.recommended_actions[0].action_type == "transformation_drill"


def test_condition_miss_stays_r1_and_never_r4() -> None:
    node = movement_node()
    question = Question(
        id="q_condition_move",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Solve y'=y with y(0)=2.",
        expected_answer="y=2e^x",
        tested_dimensions=node.core_dimensions,
        metadata={"requires_initial_condition": True},
    )
    result = scored_result(question, "y=C e^x", node)

    assert result.root_cause == ErrorType.CONDITION_MISS
    assert result.rollback_level == RollbackLevel.R1_INTERNAL
    assert result.rollback_nodes == [node.id]
    assert result.recommended_actions[0].action_type == "condition_check"


def test_expression_weakness_partial_pass_only_allows_p1() -> None:
    node = movement_node()
    result = manual_result(
        {"concept": 88, "trigger": 95, "method": 95, "transformation": 94, "process": 92, "calculation": 94, "final_answer": 93, "expression": 35},
        node,
    )

    assert result.root_cause == ErrorType.EXPRESSION_WEAKNESS
    assert result.pass_state == PassState.PARTIAL_PASS
    assert result.forward_level == ForwardLevel.P1_PARTIAL
    assert result.forward_nodes == []


def test_knowledge_confusion_r4_goes_through_rollback_engine_safety() -> None:
    node = movement_node(prerequisites=["pre_concept", "pre_method"], common_errors=["knowledge_confusion", "trigger_failure", "method_error"])
    result = manual_result({"concept": 20, "trigger": 20, "method": 20}, node)
    rollback = RollbackEngine().decide_rollback(result.error_vector, node)

    assert result.root_cause == ErrorType.KNOWLEDGE_CONFUSION
    assert rollback.level == RollbackLevel.R4_CHAPTER_FRAMEWORK
    assert rollback.is_chapter_framework_rollback is True
    assert rollback.blocked_reason == "allowed_chapter_framework_rollback"
    assert result.rollback_nodes == rollback.rollback_nodes


def test_synthesis_failure_can_recommend_framework_but_rollback_engine_owns_nodes() -> None:
    node = movement_node(node_type=NodeType.APPLICATION.value, common_errors=["synthesis_failure", "method_error", "trigger_failure"])
    result = manual_result({"trigger": 15, "method": 20, "process": 20, "final_answer": 0}, node)

    assert result.root_cause == ErrorType.SYNTHESIS_FAILURE
    assert result.recommended_actions[0].action_type == "chapter_framework_review"
    assert result.rollback_level == RollbackEngine().decide_rollback(result.error_vector, node).level
    assert result.rollback_nodes == RollbackEngine().decide_rollback(result.error_vector, node).rollback_nodes


def test_pass_allows_strong_forward_without_rollback_and_action_matches_progress() -> None:
    node = movement_node()
    result = manual_result({"trigger": 96, "method": 96, "transformation": 95, "process": 95, "calculation": 96, "final_answer": 96}, node)

    assert result.pass_state == PassState.PASS
    assert result.forward_level == ForwardLevel.P3_STRONG
    assert result.forward_nodes == node.successors[:2]
    assert result.rollback_nodes == []
    assert result.recommended_actions[0].action_type == "variant_training"
    assert result.recommended_actions[0].action_type != "need_more_evidence"


def test_primary_errors_block_forward_even_with_some_high_scores() -> None:
    node = movement_node()
    result = manual_result({"trigger": 20, "method": 20, "transformation": 85, "process": 80, "calculation": 80, "final_answer": 80}, node)

    assert result.primary_errors
    assert result.forward_level == ForwardLevel.P0_NONE
    assert result.forward_nodes == []


def test_result_movement_fields_are_owned_by_rollback_and_forward_engines() -> None:
    node = movement_node()
    result = manual_result({"trigger": 82, "method": 20, "process": 30, "final_answer": 0}, node)

    assert_engine_owned_movement(result, node)


def test_next_action_does_not_contradict_blocked_forward() -> None:
    node = movement_node()
    result = manual_result({"trigger": 10, "method": 25, "final_answer": 95}, node)

    assert result.forward_nodes == []
    assert result.forward_level == ForwardLevel.P0_NONE
    assert result.next_action_hint == result.recommended_actions[0].reason
    assert all(successor not in result.next_action_hint for successor in node.successors)


def test_derived_final_answer_error_does_not_expand_transformation_rollback() -> None:
    node = movement_node()
    result = manual_result({"trigger": 86, "method": 84, "transformation": 15, "process": 35, "calculation": 45, "final_answer": 0}, node)

    assert result.root_cause == ErrorType.TRANSFORMATION_ERROR
    assert any(item.role == "derived_result" and ScoreDimension.FINAL_ANSWER in item.related_dimensions for item in result.error_chain)
    assert result.rollback_nodes == ["pre_transform"]
    assert_not_all_prerequisites(result, node)


def test_derived_or_secondary_errors_do_not_override_calculation_root_movement() -> None:
    node = movement_node()
    result = manual_result({"concept": 90, "trigger": 90, "method": 90, "transformation": 88, "process": 86, "calculation": 15, "final_answer": 0}, node)

    assert result.root_cause == ErrorType.CALCULATION_ERROR
    assert result.rollback_nodes == [node.id]
    assert "pre_concept" not in result.rollback_nodes
    assert "pre_method" not in result.rollback_nodes


def test_illegal_r4_from_normal_error_is_downgraded_by_rollback_engine() -> None:
    node = movement_node()
    error_vector = ErrorVector(
        errors=[
            ErrorItem(
                error_type=ErrorType.TRIGGER_FAILURE,
                weight=0.9,
                related_dimensions=["trigger"],
                evidence="Bad policy attempted to force R4 for a normal trigger error.",
                suggested_rollback_level="r4_chapter_framework",
            )
        ]
    )
    decision = RollbackEngine().decide_rollback(error_vector, node)

    assert decision.level == RollbackLevel.R2_PREREQUISITE
    assert decision.is_chapter_framework_rollback is False
    assert decision.blocked_reason == "illegal_r4_downgraded_to_targeted_rollback"
    assert_not_all_prerequisites(type("Result", (), {"rollback_nodes": decision.rollback_nodes})(), node)


def test_phase_2_2_movement_eval_is_wired_into_golden_runner() -> None:
    spec = importlib.util.spec_from_file_location("run_evals", PROJECT_ROOT / "evals" / "run_evals.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    movement_cases = module.load_movement_cases()
    assert 10 <= len(movement_cases) <= 12
    assert module.main() == 0
