from __future__ import annotations

import importlib.util
from pathlib import Path

from app.core.enums import ForwardLevel, PassState, QuestionType, ScoreDimension
from app.core.schemas import Attempt, KnowledgeNode, Question, RubricItem, ScoringRubric
from app.services.composite_scoring_engine import CompositeScoringEngine
from app.services.diagnosis_engine import DiagnosisEngine
from app.services.forward_engine import ForwardEngine
from app.services.manual_override_scorer import ManualOverrideScorer
from app.services.math_validator_scorer import MathValidatorScorer
from app.services.rubric_scorer import RubricScorer
from app.services.rule_scorer import RuleScorer


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def scoring_node() -> KnowledgeNode:
    return KnowledgeNode(
        id="ode_phase1_node",
        name="Phase 1 node",
        type="method",
        status="available",
        prerequisites=["pre_a", "pre_b"],
        successors=["next_a", "next_b"],
        core_dimensions=["trigger", "method", "transformation", "calculation", "final_answer", "expression"],
        common_errors=["trigger_failure", "method_error", "transformation_error", "calculation_error", "expression_weakness"],
        description="Node for Phase 1 scoring tests.",
        trigger_patterns=["phase1"],
        scoring_weights={"trigger": 0.2, "method": 0.2, "transformation": 0.2, "calculation": 0.2, "final_answer": 0.2},
        rollback_policy={
            "trigger_failure": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "method_error": {"level": "r2_prerequisite", "target_nodes": ["pre_a"]},
            "calculation_error": {"level": "r1_internal", "target_nodes": ["__self__"]},
        },
        pass_criteria={
            "min_overall": 80,
            "min_required_dimensions": {"trigger": 75, "method": 75, "transformation": 75, "calculation": 70},
            "max_primary_errors": 0,
        },
        variant_policy={"template_families": ["phase1"], "parameter_focus": ["phase1"], "validation_required": True},
    )


def rubric_question(items: list[RubricItem], expected_answer: str | None = None) -> Question:
    return Question(
        id="q_phase1",
        node_id="ode_phase1_node",
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Phase 1 rubric question.",
        expected_answer=expected_answer,
        tested_dimensions=["concept", "trigger", "method", "transformation", "process", "expression"],
        rubric=ScoringRubric(items=items),
    )


def test_manual_override_scorer_only_active_with_score_overrides() -> None:
    node = scoring_node()
    question = Question(id="q", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="No override.")
    inactive = ManualOverrideScorer().evaluate(question, Attempt(id="a1", question_id="q", user_answer=""), node)
    active = ManualOverrideScorer().evaluate(
        question,
        Attempt(id="a2", question_id="q", user_answer="", metadata={"score_overrides": {"method": 88}}),
        node,
    )

    assert inactive.is_active is False
    assert active.is_active is True
    assert active.dimension_scores[ScoreDimension.METHOD].score == 88
    assert "manual override" in active.dimension_scores[ScoreDimension.METHOD].evidence.lower()


def test_composite_ignores_scenario_and_does_not_default_to_70() -> None:
    node = scoring_node()
    question = Question(
        id="q",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="No rubric, no validator, no rule signal.",
        tested_dimensions=["method", "final_answer"],
    )
    attempt = Attempt(
        id="a",
        question_id="q",
        user_answer="plain answer without scorer signals",
        metadata={"scenario": "process_right_calculation_wrong"},
    )

    result = CompositeScoringEngine().evaluate_detailed(question, attempt, node)

    assert result.score_vector.method is None
    assert result.score_vector.final_answer is None
    assert all(not scorer.is_active for scorer in result.scorer_results)


def test_rubric_scorer_scores_multiple_dimensions_and_records_matches() -> None:
    node = scoring_node()
    question = rubric_question(
        [
            RubricItem(
                id="concept_hit",
                description="Concept hit.",
                target_dimensions=["concept"],
                required_keywords=["definition"],
                evidence_on_hit="Concept keyword hit.",
                evidence_on_miss="Concept keyword missed.",
            ),
            RubricItem(
                id="trigger_miss",
                description="Trigger miss.",
                target_dimensions=["trigger"],
                required_keywords=["standard form"],
                evidence_on_hit="Trigger hit.",
                evidence_on_miss="Trigger missed.",
            ),
            RubricItem(
                id="method_hit",
                description="Method hit.",
                target_dimensions=["method"],
                required_keywords=["integrating factor"],
                evidence_on_hit="Method hit.",
                evidence_on_miss="Method missed.",
            ),
        ]
    )
    attempt = Attempt(id="a", question_id=question.id, user_answer="definition uses integrating factor")

    result = RubricScorer().evaluate(question, attempt, node)

    assert result.is_active is True
    assert result.dimension_scores[ScoreDimension.CONCEPT].score == 100
    assert result.dimension_scores[ScoreDimension.TRIGGER].score == 0
    assert result.dimension_scores[ScoreDimension.METHOD].score == 100
    trigger_evidence = result.dimension_scores[ScoreDimension.TRIGGER].evidence
    assert "matched_items" in trigger_evidence
    assert "missed_items" in trigger_evidence


def test_rubric_scorer_does_not_read_expected_scores_metadata() -> None:
    node = scoring_node()
    question = rubric_question(
        [
            RubricItem(
                id="concept_required",
                description="Concept required.",
                target_dimensions=["concept"],
                required_keywords=["definition"],
                evidence_on_hit="Hit.",
                evidence_on_miss="Miss.",
            )
        ]
    )
    attempt = Attempt(
        id="a",
        question_id=question.id,
        user_answer="no matching word",
        metadata={"expected_scores": {"concept": 100}},
    )

    result = RubricScorer().evaluate(question, attempt, node)

    assert result.dimension_scores[ScoreDimension.CONCEPT].score == 0


def test_rule_scorer_is_weak_and_cannot_trigger_p2_or_p3() -> None:
    node = scoring_node()
    question = Question(id="q", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="Identify method.")
    attempt = Attempt(id="a", question_id="q", user_answer="Use first-order linear.")

    score_vector = CompositeScoringEngine().evaluate(question, attempt, node)
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)
    pass_state = DiagnosisEngine().classify_pass_state(score_vector, error_vector, node)
    forward_level = ForwardEngine().determine_forward_level(score_vector, error_vector, node)
    rule_result = RuleScorer().evaluate(question, attempt, node)

    assert rule_result.confidence <= 0.55
    assert score_vector.trigger.score == 65
    assert pass_state != PassState.PASS
    assert forward_level not in {ForwardLevel.P2_NORMAL, ForwardLevel.P3_STRONG}


def test_math_validator_simple_match_missing_c_and_missing_initial_value() -> None:
    node = scoring_node()
    validator = MathValidatorScorer()
    exact = validator.evaluate(
        Question(id="q1", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="Solve.", expected_answer="y=Ce^x"),
        Attempt(id="a1", question_id="q1", user_answer="y = C e^x"),
        node,
    )
    missing_c = validator.evaluate(
        Question(
            id="q2",
            node_id=node.id,
            question_type=QuestionType.DIAGNOSTIC,
            prompt="Find the general solution.",
            expected_answer="y=Ce^x",
            metadata={"requires_constant": True},
        ),
        Attempt(id="a2", question_id="q2", user_answer="y=e^x"),
        node,
    )
    missing_iv = validator.evaluate(
        Question(
            id="q3",
            node_id=node.id,
            question_type=QuestionType.DIAGNOSTIC,
            prompt="Solve y'=y, y(0)=2.",
            expected_answer="y=2e^x",
            metadata={"requires_initial_condition": True},
        ),
        Attempt(id="a3", question_id="q3", user_answer="y=C e^x"),
        node,
    )

    assert exact.dimension_scores[ScoreDimension.FINAL_ANSWER].score == 95
    assert missing_c.dimension_scores[ScoreDimension.FINAL_ANSWER].score == 35
    assert missing_c.dimension_scores[ScoreDimension.CALCULATION].score == 60
    assert missing_iv.dimension_scores[ScoreDimension.FINAL_ANSWER].score == 40


def test_composite_merges_same_dimension_by_confidence() -> None:
    node = scoring_node()
    question = rubric_question(
        [
            RubricItem(
                id="trigger_miss",
                description="Trigger reason missing.",
                target_dimensions=["trigger"],
                required_keywords=["reason"],
                evidence_on_hit="Reason hit.",
                evidence_on_miss="Reason missed.",
            ),
            RubricItem(
                id="method_hit",
                description="Method hit.",
                target_dimensions=["method"],
                required_keywords=["separable"],
                evidence_on_hit="Method hit.",
                evidence_on_miss="Method miss.",
            ),
        ]
    )
    attempt = Attempt(id="a", question_id=question.id, user_answer="separable")

    result = CompositeScoringEngine().evaluate_detailed(question, attempt, node)

    assert 20 <= result.score_vector.trigger.score <= 35
    assert 80 <= result.score_vector.method.score <= 95
    assert any("RuleScorer" in note for note in result.merge_notes)


def test_final_answer_high_but_trigger_method_low_still_false_pass() -> None:
    node = scoring_node()
    question = rubric_question(
        [
            RubricItem(
                id="trigger_missing",
                description="Trigger required.",
                target_dimensions=["trigger"],
                required_keywords=["trigger condition"],
                evidence_on_hit="Trigger hit.",
                evidence_on_miss="Trigger missed.",
            ),
            RubricItem(
                id="method_missing",
                description="Method required.",
                target_dimensions=["method"],
                required_keywords=["method reason"],
                evidence_on_hit="Method hit.",
                evidence_on_miss="Method missed.",
            ),
        ],
        expected_answer="y=Ce^x",
    )
    attempt = Attempt(id="a", question_id=question.id, user_answer="y = C e^x")

    score_vector = CompositeScoringEngine().evaluate(question, attempt, node)
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)

    assert score_vector.final_answer.score >= 90
    assert score_vector.trigger.score == 0
    assert score_vector.method.score == 0
    assert DiagnosisEngine().classify_pass_state(score_vector, error_vector, node) == PassState.FALSE_PASS


def test_process_right_but_final_answer_wrong_cannot_full_pass() -> None:
    node = scoring_node()
    question = rubric_question(
        [
            RubricItem(
                id="trigger_hit",
                description="Trigger hit.",
                target_dimensions=["trigger"],
                required_keywords=["separable"],
                evidence_on_hit="Trigger hit.",
                evidence_on_miss="Trigger missed.",
            ),
            RubricItem(
                id="method_hit",
                description="Method hit.",
                target_dimensions=["method", "transformation"],
                required_keywords=["separate", "integrate"],
                evidence_on_hit="Method hit.",
                evidence_on_miss="Method missed.",
            ),
        ],
        expected_answer="y=Ce^x",
    )
    question.metadata["requires_constant"] = True
    attempt = Attempt(id="a", question_id=question.id, user_answer="separable separate integrate y=e^x")

    score_vector = CompositeScoringEngine().evaluate(question, attempt, node)
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)

    assert score_vector.method.score >= 80
    assert score_vector.final_answer.score < 50
    assert DiagnosisEngine().classify_pass_state(score_vector, error_vector, node) != PassState.PASS


def test_every_non_empty_composite_score_has_evidence() -> None:
    node = scoring_node()
    question = rubric_question(
        [
            RubricItem(
                id="method_hit",
                description="Method hit.",
                target_dimensions=["method"],
                required_keywords=["separable"],
                evidence_on_hit="Method hit.",
                evidence_on_miss="Method missed.",
            )
        ]
    )
    result = CompositeScoringEngine().evaluate_detailed(
        question,
        Attempt(id="a", question_id=question.id, user_answer="separable"),
        node,
    )

    for dimension_score in result.score_vector.as_dimension_map().values():
        if dimension_score is not None:
            assert dimension_score.evidence


def test_golden_eval_30_cases_execute_successfully() -> None:
    spec = importlib.util.spec_from_file_location("run_evals", PROJECT_ROOT / "evals" / "run_evals.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    cases = module.load_golden_cases()
    assert len(cases) == 30
    assert module.main() == 0
