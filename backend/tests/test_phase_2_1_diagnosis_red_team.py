from __future__ import annotations

import importlib.util
from pathlib import Path

from app.core.enums import ErrorType, ForwardLevel, NodeType, PassState, QuestionType, ScoreDimension
from app.core.schemas import Attempt, KnowledgeNode, Question, RubricItem, ScoringRubric
from app.services.composite_scoring_engine import CompositeScoringEngine
from app.services.diagnosis_engine import DiagnosisEngine


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def red_node(
    *,
    node_id: str = "ode_phase21_node",
    node_type: str = "method",
    common_errors: list[str] | None = None,
) -> KnowledgeNode:
    return KnowledgeNode(
        id=node_id,
        name="Phase 2.1 red node",
        type=node_type,
        status="available",
        prerequisites=["pre_trigger", "pre_method", "pre_transform"],
        successors=["next_direct", "next_synthesis"],
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
        description="Red-team node for diagnosis hardening.",
        trigger_patterns=["red-team"],
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
            "concept_gap": {"level": "r2_prerequisite", "target_nodes": ["pre_trigger"]},
            "trigger_failure": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "method_error": {"level": "r2_prerequisite", "target_nodes": ["pre_method"]},
            "transformation_error": {"level": "r2_prerequisite", "target_nodes": ["pre_transform"]},
            "calculation_error": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "condition_miss": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "expression_weakness": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "knowledge_confusion": {"level": "r4_chapter_framework", "target_nodes": ["pre_trigger", "pre_method"]},
            "synthesis_failure": {"level": "r4_chapter_framework", "target_nodes": ["pre_method", "pre_transform"]},
        },
        pass_criteria={
            "min_overall": 80,
            "min_required_dimensions": {"trigger": 70, "method": 70, "transformation": 70, "process": 65},
            "max_primary_errors": 0,
        },
        variant_policy={"template_families": ["red"], "parameter_focus": ["red"], "validation_required": True},
    )


def manual_result(scores: dict[str, float], node: KnowledgeNode | None = None, question: Question | None = None):
    node = node or red_node()
    question = question or Question(
        id="q_manual",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Manual diagnosis red-team question.",
        tested_dimensions=node.core_dimensions,
    )
    attempt = Attempt(
        id="a_manual",
        question_id=question.id,
        user_answer="manual diagnostic answer",
        metadata={
            "score_overrides": scores,
            "evidence_overrides": {dimension: f"manual evidence for {dimension}" for dimension in scores},
        },
    )
    composite = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    return DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)


def scored_result(question: Question, answer: str, node: KnowledgeNode | None = None):
    node = node or red_node(node_id=question.node_id)
    attempt = Attempt(id=f"a_{question.id}", question_id=question.id, user_answer=answer)
    composite = CompositeScoringEngine().evaluate_detailed(question, attempt, node)
    return DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)


def rubric_question(items: list[RubricItem], *, expected_answer: str | None = None, metadata: dict | None = None) -> Question:
    return Question(
        id="q_rubric_red",
        node_id="ode_phase21_node",
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Rubric red-team question.",
        expected_answer=expected_answer,
        tested_dimensions=["trigger", "method", "transformation", "process", "calculation", "final_answer", "expression", "concept"],
        rubric=ScoringRubric(items=items),
        metadata=metadata or {},
    )


def test_mixed_low_scores_prefer_trigger_root() -> None:
    result = manual_result({"trigger": 10, "method": 15, "transformation": 25, "calculation": 20, "final_answer": 0})

    assert result.root_cause == ErrorType.TRIGGER_FAILURE
    assert ErrorType.METHOD_ERROR in result.derived_errors
    assert ErrorType.TRANSFORMATION_ERROR in result.derived_errors


def test_method_error_derives_calculation_low() -> None:
    result = manual_result({"trigger": 75, "method": 15, "process": 30, "calculation": 20, "final_answer": 0})

    assert result.root_cause == ErrorType.METHOD_ERROR
    assert ErrorType.CALCULATION_ERROR in result.derived_errors


def test_transformation_error_makes_final_answer_downstream() -> None:
    result = manual_result({"trigger": 82, "method": 78, "transformation": 10, "process": 35, "final_answer": 0})

    assert result.root_cause == ErrorType.TRANSFORMATION_ERROR
    assert any(item.role == "derived_result" and ScoreDimension.FINAL_ANSWER in item.related_dimensions for item in result.error_chain)


def test_calculation_root_requires_prior_chain_ok() -> None:
    result = manual_result({"trigger": 90, "method": 90, "transformation": 88, "process": 85, "calculation": 20, "final_answer": 0})

    assert result.root_cause == ErrorType.CALCULATION_ERROR
    assert result.recommended_actions[0].action_type == "calculation_repair"


def test_initial_value_missing_is_condition_miss() -> None:
    question = Question(
        id="q_ivp_red",
        node_id="ode_phase21_node",
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Solve y'=y, y(0)=2.",
        expected_answer="y=2e^x",
        metadata={"requires_initial_condition": True},
    )
    result = scored_result(question, "y=C e^x")

    assert result.root_cause == ErrorType.CONDITION_MISS
    assert result.recommended_actions[0].action_type == "condition_check"


def test_y0_discussion_without_initial_requirement_does_not_trigger_condition_miss() -> None:
    question = Question(
        id="q_y0_discussion",
        node_id="ode_phase21_node",
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Discuss notation y(0) in examples, but only find the general solution.",
        expected_answer="y=Ce^x",
    )
    result = scored_result(question, "y=C e^x")

    assert result.root_cause != ErrorType.CONDITION_MISS
    assert not result.error_vector.has_error_type(ErrorType.CONDITION_MISS)


def test_missing_c_and_required_initial_condition_prioritizes_condition_miss() -> None:
    question = rubric_question(
        [
            RubricItem(
                id="initial_condition_required",
                description="Initial condition required.",
                target_dimensions=["process"],
                required_keywords=["use y(0)=2"],
                evidence_on_hit="Initial condition hit.",
                evidence_on_miss="Initial condition missed.",
            )
        ],
        expected_answer="y=2e^x",
        metadata={"requires_constant": True},
    )
    result = scored_result(question, "y=e^x")

    assert result.root_cause == ErrorType.CONDITION_MISS
    assert ErrorType.CALCULATION_ERROR in result.derived_errors


def test_required_miss_beats_high_final_answer() -> None:
    question = rubric_question(
        [
            RubricItem(
                id="trigger_required_linear_form",
                description="Trigger required.",
                target_dimensions=["trigger"],
                required_keywords=["linear standard form"],
                evidence_on_hit="Trigger hit.",
                evidence_on_miss="Trigger missed.",
            )
        ],
        expected_answer="y=1/2e^x+Ce^-x",
    )
    result = scored_result(question, "y=1/2e^x+Ce^-x")

    assert result.root_cause == ErrorType.TRIGGER_FAILURE
    assert result.pass_state == PassState.FALSE_PASS


def test_method_hit_but_transformation_required_missed_prefers_transformation() -> None:
    question = rubric_question(
        [
            RubricItem(
                id="method_bernoulli_hit",
                description="Method hit.",
                target_dimensions=["method"],
                required_keywords=["bernoulli"],
                evidence_on_hit="Method hit.",
                evidence_on_miss="Method missed.",
            ),
            RubricItem(
                id="transformation_required_inverse_power",
                description="Transformation required.",
                target_dimensions=["transformation"],
                required_keywords=["z=y^-1"],
                evidence_on_hit="Transformation hit.",
                evidence_on_miss="Transformation missed.",
            ),
        ]
    )
    result = scored_result(question, "bernoulli")

    assert result.root_cause == ErrorType.TRANSFORMATION_ERROR


def test_multiple_optional_misses_do_not_create_root() -> None:
    question = rubric_question(
        [
            RubricItem(
                id="method_required",
                description="Required method.",
                target_dimensions=["method"],
                required_keywords=["separable"],
                required=True,
                weight=1,
                evidence_on_hit="Required hit.",
                evidence_on_miss="Required missed.",
            ),
            RubricItem(
                id="optional_domain",
                description="Optional domain.",
                target_dimensions=["method"],
                required_keywords=["domain"],
                required=False,
                weight=0.1,
                evidence_on_hit="Optional hit.",
                evidence_on_miss="Optional missed.",
            ),
            RubricItem(
                id="optional_zero",
                description="Optional zero solution.",
                target_dimensions=["method"],
                required_keywords=["zero solution"],
                required=False,
                weight=0.1,
                evidence_on_hit="Optional hit.",
                evidence_on_miss="Optional missed.",
            ),
        ]
    )
    result = scored_result(question, "separable")

    assert result.root_cause is None
    assert not result.error_vector.primary_errors()


def test_rule_signal_does_not_override_core_required_miss() -> None:
    question = rubric_question(
        [
            RubricItem(
                id="trigger_required_reason",
                description="Trigger required.",
                target_dimensions=["trigger"],
                required_keywords=["variables can be separated"],
                evidence_on_hit="Trigger hit.",
                evidence_on_miss="Trigger missed.",
            )
        ]
    )
    result = scored_result(question, "This is separable.")

    assert result.root_cause == ErrorType.TRIGGER_FAILURE
    assert "RuleScorer" in result.diagnosis_trace.active_scorers


def test_keyword_copy_with_correct_answer_is_false_pass() -> None:
    question = rubric_question(
        [
            RubricItem(
                id="trigger_required_not_copy",
                description="Trigger required.",
                target_dimensions=["trigger"],
                required_keywords=["unknown function and derivative appear linearly"],
                evidence_on_hit="Trigger hit.",
                evidence_on_miss="Trigger missed.",
            )
        ],
        expected_answer="y=1/2e^x+Ce^-x",
    )
    result = scored_result(question, "first-order linear, y=1/2e^x+Ce^-x")

    assert result.root_cause == ErrorType.TRIGGER_FAILURE
    assert result.pass_state == PassState.FALSE_PASS


def test_complete_looking_process_with_bad_equivalence_is_transformation_error() -> None:
    result = manual_result({"trigger": 85, "method": 85, "transformation": 20, "process": 75, "calculation": 70, "final_answer": 30})

    assert result.root_cause == ErrorType.TRANSFORMATION_ERROR


def test_wrong_method_name_but_strong_solution_chain_needs_more_evidence() -> None:
    result = manual_result({"method": 20, "transformation": 90, "process": 88, "calculation": 90, "final_answer": 90})

    assert result.root_cause is None
    assert result.confidence <= 0.3
    assert result.recommended_actions[0].action_type == "need_more_evidence"


def test_expression_weakness_with_traceable_solution_is_partial_pass() -> None:
    result = manual_result(
        {"concept": 80, "trigger": 85, "method": 85, "transformation": 85, "process": 80, "calculation": 82, "final_answer": 82, "expression": 35}
    )

    assert result.root_cause == ErrorType.EXPRESSION_WEAKNESS
    assert result.pass_state == PassState.PARTIAL_PASS


def test_expression_weakness_does_not_hide_concept_gap() -> None:
    result = manual_result({"concept": 20, "expression": 25})

    assert result.root_cause == ErrorType.CONCEPT_GAP
    assert result.root_cause != ErrorType.EXPRESSION_WEAKNESS


def test_knowledge_confusion_beats_local_trigger_failure_when_node_context_supports_it() -> None:
    node = red_node(common_errors=["knowledge_confusion", "trigger_failure"], node_type=NodeType.SYNTHESIS.value)
    result = manual_result({"concept": 20, "trigger": 20, "method": 20}, node=node)

    assert result.root_cause == ErrorType.KNOWLEDGE_CONFUSION
    assert result.recommended_actions[0].action_type == "chapter_framework_review"


def test_synthesis_context_beats_method_error() -> None:
    node = red_node(common_errors=["synthesis_failure", "method_error"], node_type=NodeType.APPLICATION.value)
    result = manual_result({"trigger": 20, "method": 20, "process": 20, "final_answer": 0}, node=node)

    assert result.root_cause == ErrorType.SYNTHESIS_FAILURE
    assert "拆题路径" in result.learner_explanation


def test_no_scoring_evidence_needs_more_evidence() -> None:
    node = red_node()
    question = Question(id="q_no_evidence", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="No scoring signal.")
    result = scored_result(question, "plain text", node)

    assert result.root_cause is None
    assert result.recommended_actions[0].action_type == "need_more_evidence"


def test_learner_explanation_is_chinese_coach_text_not_debug() -> None:
    result = manual_result({"trigger": 10, "method": 20, "final_answer": 0})
    text = result.learner_explanation

    assert "根因判断" in text
    assert "为什么不是另一个常见错因" in text
    assert "是否允许推进" in text
    assert "下一步训练动作" in text
    assert "root_cause=" not in text
    assert "policy_hits=" not in text
    assert "The root issue" not in text


def test_phase_2_1_golden_eval_counts() -> None:
    spec = importlib.util.spec_from_file_location("run_evals", PROJECT_ROOT / "evals" / "run_evals.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    diagnosis_cases = module.load_diagnosis_cases()
    new_cases = [case for case in diagnosis_cases if str(case["id"]).startswith("diag21_")]
    assert len(module.load_golden_cases()) == 30
    assert len(diagnosis_cases) == 25
    assert sum(1 for case in new_cases if case["scoring_path"] == "manual_override") <= 5
    assert sum(1 for case in new_cases if case["scoring_path"] != "manual_override") >= 10
    assert module.main() == 0
