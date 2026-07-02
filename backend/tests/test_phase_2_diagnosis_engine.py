from __future__ import annotations

import importlib.util
from pathlib import Path

from app.core.enums import ErrorType, ForwardLevel, NodeType, PassState, QuestionType, ScoreDimension
from app.core.schemas import Attempt, KnowledgeNode, Question, RubricItem, ScoringRubric
from app.services.composite_scoring_engine import CompositeScoringEngine
from app.services.diagnosis_engine import DiagnosisEngine


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def phase2_node(
    common_errors: list[str] | None = None,
    node_type: str = "method",
) -> KnowledgeNode:
    return KnowledgeNode(
        id="ode_phase2_node",
        name="Phase 2 node",
        type=node_type,
        status="available",
        prerequisites=["pre_trigger", "pre_method", "pre_transform"],
        successors=["next_direct", "next_synthesis"],
        core_dimensions=["concept", "trigger", "method", "transformation", "process", "calculation", "final_answer", "expression"],
        common_errors=common_errors
        or [
            "trigger_failure",
            "method_error",
            "transformation_error",
            "process_gap",
            "calculation_error",
            "condition_miss",
            "expression_weakness",
        ],
        description="Phase 2 diagnosis node.",
        trigger_patterns=["phase2"],
        scoring_weights={
            "concept": 0.1,
            "trigger": 0.16,
            "method": 0.16,
            "transformation": 0.16,
            "process": 0.14,
            "calculation": 0.14,
            "final_answer": 0.1,
            "expression": 0.04,
        },
        rollback_policy={
            "trigger_failure": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "method_error": {"level": "r2_prerequisite", "target_nodes": ["pre_method"]},
            "transformation_error": {"level": "r2_prerequisite", "target_nodes": ["pre_transform"]},
            "calculation_error": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "condition_miss": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "expression_weakness": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "knowledge_confusion": {"level": "r4_chapter_framework", "target_nodes": ["pre_trigger", "pre_method", "pre_transform"]},
            "synthesis_failure": {"level": "r4_chapter_framework", "target_nodes": ["pre_trigger", "pre_method", "pre_transform"]},
        },
        pass_criteria={
            "min_overall": 80,
            "min_required_dimensions": {"trigger": 70, "method": 70, "transformation": 70, "process": 65},
            "max_primary_errors": 0,
        },
        variant_policy={"template_families": ["phase2"], "parameter_focus": ["phase2"], "validation_required": True},
    )


def manual_question(node: KnowledgeNode, question_type: str = "diagnostic") -> Question:
    return Question(
        id="q_phase2",
        node_id=node.id,
        question_type=QuestionType(question_type),
        prompt="Phase 2 diagnostic question.",
        tested_dimensions=node.core_dimensions,
    )


def detailed_from_scores(
    scores: dict[str, float],
    node: KnowledgeNode | None = None,
    question: Question | None = None,
):
    node = node or phase2_node()
    question = question or manual_question(node)
    attempt = Attempt(
        id="a_phase2",
        question_id=question.id,
        user_answer="manual diagnostic answer",
        metadata={
            "score_overrides": scores,
            "evidence_overrides": {dimension: f"manual evidence for {dimension}" for dimension in scores},
        },
    )
    composite = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    return DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)


def rubric_detail(items: list[RubricItem], answer: str, expected_answer: str | None = None, node: KnowledgeNode | None = None):
    node = node or phase2_node()
    question = Question(
        id="q_rubric",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Rubric diagnosis question.",
        expected_answer=expected_answer,
        tested_dimensions=node.core_dimensions,
        rubric=ScoringRubric(items=items),
    )
    attempt = Attempt(id="a_rubric", question_id=question.id, user_answer=answer)
    composite = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    return DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)


def test_process_right_calculation_wrong_has_calculation_root_and_final_answer_derived() -> None:
    result = detailed_from_scores(
        {
            "trigger": 88,
            "method": 90,
            "transformation": 88,
            "process": 82,
            "calculation": 20,
            "final_answer": 0,
        }
    )

    assert result.root_cause == ErrorType.CALCULATION_ERROR
    assert ErrorType.CALCULATION_ERROR in result.downstream_result_errors
    assert any(item.role == "downstream_result" and ScoreDimension.FINAL_ANSWER in item.related_dimensions for item in result.error_chain)
    assert any(item.role == "derived_result" and ScoreDimension.FINAL_ANSWER in item.related_dimensions for item in result.error_chain)
    assert result.recommended_actions[0].action_type == "calculation_repair"


def test_answer_right_trigger_unclear_is_false_pass_with_coach_explanation() -> None:
    result = detailed_from_scores(
        {
            "trigger": 20,
            "method": 35,
            "process": 50,
            "calculation": 85,
            "final_answer": 95,
        }
    )

    assert result.pass_state == PassState.FALSE_PASS
    assert result.root_cause == ErrorType.TRIGGER_FAILURE
    assert "答案不能证明掌握" in result.learner_explanation


def test_final_answer_high_but_blank_process_cannot_pass() -> None:
    result = detailed_from_scores({"final_answer": 95})

    assert result.pass_state != PassState.PASS
    assert result.pass_state == PassState.FALSE_PASS


def test_trigger_failure_is_root_and_later_errors_are_derived() -> None:
    result = detailed_from_scores({"trigger": 10, "method": 25, "transformation": 30, "process": 35, "final_answer": 0})

    assert result.root_cause == ErrorType.TRIGGER_FAILURE
    assert ErrorType.METHOD_ERROR in result.derived_errors
    assert ErrorType.TRANSFORMATION_ERROR in result.derived_errors


def test_method_error_is_not_misdiagnosed_as_calculation_error() -> None:
    result = detailed_from_scores({"trigger": 65, "method": 15, "process": 30, "calculation": 35, "final_answer": 0})

    assert result.root_cause == ErrorType.METHOD_ERROR
    assert result.root_cause != ErrorType.CALCULATION_ERROR
    assert result.recommended_actions[0].action_type == "method_comparison"


def test_bernoulli_wrong_substitution_is_transformation_root() -> None:
    result = detailed_from_scores({"trigger": 82, "method": 76, "transformation": 15, "process": 35, "final_answer": 0})

    assert result.root_cause == ErrorType.TRANSFORMATION_ERROR
    assert result.recommended_actions[0].action_type == "transformation_drill"


def test_reducible_order_incomplete_explanation_is_transformation_or_process_issue() -> None:
    result = detailed_from_scores({"trigger": 78, "method": 75, "transformation": 45, "process": 35, "final_answer": 20})

    assert result.root_cause in {ErrorType.TRANSFORMATION_ERROR, ErrorType.PROCESS_GAP}


def test_missing_c_is_not_method_error() -> None:
    node = phase2_node()
    question = Question(
        id="q_missing_c",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Find the general solution.",
        expected_answer="y=Ce^x",
        metadata={"requires_constant": True},
    )
    attempt = Attempt(id="a_missing_c", question_id=question.id, user_answer="y=e^x")
    composite = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    result = DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)

    assert result.root_cause != ErrorType.METHOD_ERROR
    assert result.root_cause == ErrorType.CALCULATION_ERROR
    assert result.recommended_actions[0].action_type == "calculation_repair"


def test_missing_initial_value_is_condition_miss() -> None:
    node = phase2_node()
    question = Question(
        id="q_ivp",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Solve y'=y, y(0)=2.",
        expected_answer="y=2e^x",
        metadata={"requires_initial_condition": True},
    )
    attempt = Attempt(id="a_ivp", question_id=question.id, user_answer="y=C e^x")
    composite = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    result = DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)

    assert result.root_cause == ErrorType.CONDITION_MISS
    assert result.recommended_actions[0].action_type == "condition_check"


def test_expression_weakness_allows_partial_pass_when_concept_is_ok() -> None:
    result = detailed_from_scores(
        {
            "concept": 80,
            "trigger": 85,
            "method": 85,
            "transformation": 85,
            "process": 80,
            "calculation": 82,
            "final_answer": 82,
            "expression": 35,
        }
    )

    assert result.root_cause == ErrorType.EXPRESSION_WEAKNESS
    assert result.pass_state == PassState.PARTIAL_PASS
    assert result.recommended_actions[0].action_type == "expression_rewrite"


def test_knowledge_confusion_can_suggest_framework_review_without_directly_selecting_nodes() -> None:
    node = phase2_node(common_errors=["knowledge_confusion"], node_type=NodeType.SYNTHESIS.value)
    result = detailed_from_scores({"concept": 20, "trigger": 25, "method": 25, "transformation": 40}, node=node)

    assert result.root_cause == ErrorType.KNOWLEDGE_CONFUSION
    assert result.recommended_actions[0].action_type == "chapter_framework_review"
    assert result.rollback_nodes


def test_synthesis_failure_mentions_decomposition_path() -> None:
    node = phase2_node(common_errors=["synthesis_failure"], node_type=NodeType.APPLICATION.value)
    result = detailed_from_scores({"trigger": 20, "method": 25, "process": 20, "final_answer": 0}, node=node)

    assert result.root_cause == ErrorType.SYNTHESIS_FAILURE
    assert "拆题路径" in result.learner_explanation


def test_rule_only_is_low_confidence_and_needs_more_evidence() -> None:
    node = phase2_node()
    question = Question(id="q_rule", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="Identify method.")
    attempt = Attempt(id="a_rule", question_id=question.id, user_answer="Use first-order linear integrating factor.")
    composite = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    result = DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)

    assert result.diagnosis_trace.rule_only is True
    assert result.root_cause is None
    assert result.confidence <= 0.3
    assert result.recommended_actions[0].action_type == "need_more_evidence"
    assert result.weak_signal_errors or any(item.role == "weak_signal" for item in result.error_chain)


def test_ultimate_evidence_bundle_keeps_secondary_error_when_root_is_not_supported() -> None:
    result = detailed_from_scores(
        {
            "method": 55,
            "transformation": 88,
            "process": 86,
            "calculation": 87,
            "final_answer": 86,
        }
    )

    assert result.root_cause is None
    assert ErrorType.METHOD_ERROR in result.secondary_errors
    assert any(item.role == "secondary" and item.error_type == ErrorType.METHOD_ERROR for item in result.error_chain)
    assert result.diagnosis_trace is not None
    assert "score_vector" in result.diagnosis_trace.evidence_bundle


def test_required_missed_can_create_primary_root_cause() -> None:
    result = rubric_detail(
        [
            RubricItem(
                id="trigger_required_reason",
                description="Trigger reason.",
                target_dimensions=["trigger"],
                required_keywords=["standard form"],
                required=True,
                evidence_on_hit="Trigger hit.",
                evidence_on_miss="Trigger missed.",
            )
        ],
        answer="no reason",
    )

    assert result.root_cause == ErrorType.TRIGGER_FAILURE
    assert result.diagnosis_trace is not None
    assert "rubric_required_missed" in result.diagnosis_trace.evidence_bundle
    assert "trigger:trigger_required_reason" in result.diagnosis_trace.required_missed


def test_optional_missed_does_not_create_primary_root_cause() -> None:
    result = rubric_detail(
        [
            RubricItem(
                id="method_required",
                description="Required method.",
                target_dimensions=["method"],
                required_keywords=["separable"],
                required=True,
                weight=1,
                evidence_on_hit="Method hit.",
                evidence_on_miss="Method missed.",
            ),
            RubricItem(
                id="method_optional_shortcut",
                description="Optional shortcut.",
                target_dimensions=["method"],
                required_keywords=["shortcut"],
                required=False,
                weight=0.1,
                evidence_on_hit="Shortcut hit.",
                evidence_on_miss="Shortcut missed.",
            ),
        ],
        answer="separable",
    )

    assert result.root_cause is None
    assert not result.error_vector.primary_errors()
    assert "method:method_optional_shortcut" in result.diagnosis_trace.optional_missed


def test_missing_scoring_evidence_recommends_more_evidence() -> None:
    node = phase2_node()
    question = Question(id="q_none", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="No scorer signal.")
    attempt = Attempt(id="a_none", question_id=question.id, user_answer="plain")
    composite = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    result = DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)

    assert result.root_cause is None
    assert result.recommended_actions[0].action_type == "need_more_evidence"


def test_error_chain_has_root_primary_and_derived_layers() -> None:
    result = detailed_from_scores({"trigger": 10, "method": 20, "transformation": 20, "process": 25, "final_answer": 0})
    roles = {item.role for item in result.error_chain}

    assert "root" in roles
    assert "derived" in roles
    assert result.primary_errors == [ErrorType.TRIGGER_FAILURE]


def test_learner_explanation_is_not_debug_string() -> None:
    result = detailed_from_scores({"trigger": 10, "method": 20, "final_answer": 0})

    assert "root_cause=" not in result.learner_explanation
    assert "policy_hits=" not in result.learner_explanation
    assert "下一步训练动作" in result.learner_explanation


def test_diagnosis_result_uses_rollback_and_forward_engines_for_compat_fields() -> None:
    result = detailed_from_scores({"trigger": 85, "method": 88, "transformation": 85, "process": 80, "calculation": 20, "final_answer": 0})

    assert result.rollback_nodes == ["ode_phase2_node"]
    assert result.forward_level == ForwardLevel.P0_NONE
    assert result.forward_nodes == []


def test_phase_2_golden_evals_execute_scoring_and_diagnosis_cases() -> None:
    spec = importlib.util.spec_from_file_location("run_evals", PROJECT_ROOT / "evals" / "run_evals.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert len(module.load_golden_cases()) == 30
    assert len(module.load_diagnosis_cases()) == 25
    assert module.main() == 0
