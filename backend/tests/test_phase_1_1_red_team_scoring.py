from __future__ import annotations

import importlib.util
from pathlib import Path

from app.core.enums import ForwardLevel, PassState, QuestionType, ScoreDimension
from app.core.schemas import Attempt, KnowledgeNode, Question, RubricItem, ScoringRubric
from app.services.composite_scoring_engine import CompositeScoringEngine
from app.services.diagnosis_engine import DiagnosisEngine
from app.services.forward_engine import ForwardEngine
from app.services.math_validator_scorer import MathValidatorScorer
from app.services.rubric_scorer import RubricScorer


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def red_node() -> KnowledgeNode:
    return KnowledgeNode(
        id="ode_red_team",
        name="Red team node",
        type="method",
        status="available",
        prerequisites=["pre_a", "pre_b"],
        successors=["next_a", "next_b"],
        core_dimensions=["trigger", "method", "transformation", "process", "calculation", "final_answer", "expression"],
        common_errors=["trigger_failure", "method_error", "transformation_error", "process_gap", "calculation_error"],
        description="Node for red-team scoring tests.",
        trigger_patterns=["red"],
        scoring_weights={
            "trigger": 0.2,
            "method": 0.2,
            "transformation": 0.2,
            "process": 0.2,
            "calculation": 0.1,
            "final_answer": 0.1,
        },
        rollback_policy={
            "trigger_failure": {"level": "r1_internal", "target_nodes": ["__self__"]},
            "method_error": {"level": "r2_prerequisite", "target_nodes": ["pre_a"]},
            "calculation_error": {"level": "r1_internal", "target_nodes": ["__self__"]},
        },
        pass_criteria={
            "min_overall": 80,
            "min_required_dimensions": {"trigger": 75, "method": 75, "transformation": 75, "process": 70},
            "max_primary_errors": 0,
        },
        variant_policy={"template_families": ["red"], "parameter_focus": ["red"], "validation_required": True},
    )


def question_with_items(items: list[RubricItem], expected_answer: str | None = None) -> Question:
    return Question(
        id="q_red",
        node_id="ode_red_team",
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Red team scoring question.",
        expected_answer=expected_answer,
        tested_dimensions=["trigger", "method", "transformation", "process", "calculation", "final_answer", "expression"],
        rubric=ScoringRubric(items=items),
    )


def classify(score_vector, question, attempt, node) -> PassState:
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)
    return DiagnosisEngine().classify_pass_state(score_vector, error_vector, node)


def forward_level(score_vector, question, attempt, node) -> ForwardLevel:
    error_vector = DiagnosisEngine().diagnose(score_vector, question, attempt, node)
    return ForwardEngine().determine_forward_level(score_vector, error_vector, node)


def test_keyword_with_wrong_meaning_cannot_pass_or_advance() -> None:
    node = red_node()
    question = Question(id="q", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="Classify method.")
    attempt = Attempt(id="a", question_id="q", user_answer="This is separable, but I use first-order linear integrating factor.")

    score_vector = CompositeScoringEngine().evaluate(question, attempt, node)

    assert score_vector.trigger.score == 65
    assert classify(score_vector, question, attempt, node) != PassState.PASS
    assert forward_level(score_vector, question, attempt, node) not in {ForwardLevel.P2_NORMAL, ForwardLevel.P3_STRONG}


def test_copying_prompt_keyword_does_not_create_high_score() -> None:
    node = red_node()
    question = Question(id="q", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="This is first-order linear. Explain.")
    attempt = Attempt(id="a", question_id="q", user_answer="first-order linear")

    score_vector = CompositeScoringEngine().evaluate(question, attempt, node)

    assert score_vector.trigger.score == 65
    assert score_vector.method.score == 65
    assert classify(score_vector, question, attempt, node) != PassState.PASS


def test_required_missing_pulls_dimension_down_but_optional_missing_is_soft() -> None:
    node = red_node()
    required_question = question_with_items(
        [
            RubricItem(
                id="required_method",
                description="Required method.",
                target_dimensions=["method"],
                required_keywords=["separable"],
                required=True,
                weight=1,
                evidence_on_hit="Required hit.",
                evidence_on_miss="Required missed.",
            )
        ]
    )
    optional_question = question_with_items(
        [
            RubricItem(
                id="required_method",
                description="Required method.",
                target_dimensions=["method"],
                required_keywords=["separable"],
                required=True,
                weight=1,
                evidence_on_hit="Required hit.",
                evidence_on_miss="Required missed.",
            ),
            RubricItem(
                id="optional_note",
                description="Optional note.",
                target_dimensions=["method"],
                required_keywords=["shortcut"],
                required=False,
                weight=0.1,
                evidence_on_hit="Optional hit.",
                evidence_on_miss="Optional missed.",
            ),
        ]
    )
    attempt = Attempt(id="a", question_id="q", user_answer="separable")

    required_score = RubricScorer().evaluate(required_question, attempt, node).dimension_scores[ScoreDimension.METHOD]
    optional_score = RubricScorer().evaluate(optional_question, attempt, node).dimension_scores[ScoreDimension.METHOD]

    assert required_score.score == 100
    assert optional_score.score > 90
    assert "optional_missed=['optional_note']" in optional_score.evidence


def test_required_missing_evidence_is_explicit() -> None:
    node = red_node()
    question = question_with_items(
        [
            RubricItem(
                id="required_trigger",
                description="Required trigger.",
                target_dimensions=["trigger"],
                required_keywords=["standard form"],
                required=True,
                evidence_on_hit="Hit.",
                evidence_on_miss="Miss.",
            )
        ]
    )
    score = RubricScorer().evaluate(question, Attempt(id="a", question_id="q", user_answer="no match"), node).dimension_scores[
        ScoreDimension.TRIGGER
    ]

    assert score.score == 0
    assert "required_missed=['required_trigger']" in score.evidence


def test_weighted_mixed_rubric_items_score_reasonably() -> None:
    node = red_node()
    question = question_with_items(
        [
            RubricItem(
                id="heavy_hit",
                description="Heavy hit.",
                target_dimensions=["process"],
                required_keywords=["main step"],
                weight=3,
                evidence_on_hit="Hit.",
                evidence_on_miss="Miss.",
            ),
            RubricItem(
                id="light_miss",
                description="Light miss.",
                target_dimensions=["process"],
                required_keywords=["small detail"],
                weight=1,
                evidence_on_hit="Hit.",
                evidence_on_miss="Miss.",
            ),
        ]
    )

    score = RubricScorer().evaluate(question, Attempt(id="a", question_id="q", user_answer="main step"), node).dimension_scores[
        ScoreDimension.PROCESS
    ]

    assert score.score == 75
    assert "matched_items=['heavy_hit']" in score.evidence
    assert "required_missed=['light_miss']" in score.evidence


def test_keywords_and_patterns_are_all_required_when_both_exist() -> None:
    node = red_node()
    question = question_with_items(
        [
            RubricItem(
                id="keyword_and_pattern",
                description="Both keyword and pattern required.",
                target_dimensions=["transformation"],
                required_keywords=["substitution"],
                expected_patterns=[r"y\s*=\s*vx"],
                evidence_on_hit="Both hit.",
                evidence_on_miss="Keyword or pattern missed.",
            )
        ]
    )

    missing_keyword = RubricScorer().evaluate(question, Attempt(id="a1", question_id="q", user_answer="y = vx"), node)
    missing_pattern = RubricScorer().evaluate(question, Attempt(id="a2", question_id="q", user_answer="substitution only"), node)
    both = RubricScorer().evaluate(question, Attempt(id="a3", question_id="q", user_answer="substitution y = vx"), node)

    assert missing_keyword.dimension_scores[ScoreDimension.TRANSFORMATION].score == 0
    assert missing_pattern.dimension_scores[ScoreDimension.TRANSFORMATION].score == 0
    assert both.dimension_scores[ScoreDimension.TRANSFORMATION].score == 100


def test_constant_forms_are_not_marked_missing() -> None:
    node = red_node()
    question = Question(
        id="q",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Find the general solution.",
        expected_answer="y=Ce^x",
        metadata={"requires_constant": True},
    )
    validator = MathValidatorScorer()

    for answer in ["y=c e^x", "y=C1 e^x", "y=C_1 e^x", "y=e^x + 任意常数", "y=e^x + 常数项"]:
        result = validator.evaluate(question, Attempt(id=answer, question_id="q", user_answer=answer), node)
        assert result.dimension_scores.get(ScoreDimension.FINAL_ANSWER) is None or result.dimension_scores[
            ScoreDimension.FINAL_ANSWER
        ].score != 35


def test_missing_constant_is_penalized() -> None:
    node = red_node()
    question = Question(
        id="q",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Find the general solution.",
        expected_answer="y=Ce^x",
        metadata={"requires_constant": True},
    )
    result = MathValidatorScorer().evaluate(question, Attempt(id="a", question_id="q", user_answer="y=e^x"), node)

    assert result.dimension_scores[ScoreDimension.FINAL_ANSWER].score == 35


def test_initial_value_with_resolved_constant_not_penalized() -> None:
    node = red_node()
    question = Question(
        id="q",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Solve y'=y, y(0)=2.",
        expected_answer="y=2e^x",
        metadata={"requires_initial_condition": True},
    )

    result = MathValidatorScorer().evaluate(
        question,
        Attempt(id="a", question_id="q", user_answer="general y=C e^x, C=2, final y=2e^x"),
        node,
    )

    assert result.dimension_scores[ScoreDimension.FINAL_ANSWER].score == 95


def test_initial_value_stopped_at_general_solution_is_penalized() -> None:
    node = red_node()
    question = Question(
        id="q",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Solve y'=y, y(0)=2.",
        expected_answer="y=2e^x",
        metadata={"requires_initial_condition": True},
    )
    result = MathValidatorScorer().evaluate(question, Attempt(id="a", question_id="q", user_answer="y=C e^x"), node)

    assert result.dimension_scores[ScoreDimension.FINAL_ANSWER].score == 40


def test_initial_value_special_solution_is_accepted() -> None:
    node = red_node()
    question = Question(
        id="q",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Solve y'=y, y(0)=2.",
        expected_answer="y=2e^x",
        metadata={"requires_initial_condition": True},
    )
    result = MathValidatorScorer().evaluate(question, Attempt(id="a", question_id="q", user_answer="y=2e^x"), node)

    assert result.dimension_scores[ScoreDimension.FINAL_ANSWER].score == 95


def test_final_answer_correct_but_blank_process_is_false_pass() -> None:
    node = red_node()
    question = question_with_items(
        [
            RubricItem(
                id="trigger_required",
                description="Trigger required.",
                target_dimensions=["trigger"],
                required_keywords=["trigger"],
                evidence_on_hit="Hit.",
                evidence_on_miss="Miss.",
            ),
            RubricItem(
                id="method_required",
                description="Method required.",
                target_dimensions=["method"],
                required_keywords=["method"],
                evidence_on_hit="Hit.",
                evidence_on_miss="Miss.",
            ),
            RubricItem(
                id="process_required",
                description="Process required.",
                target_dimensions=["process"],
                required_keywords=["because"],
                evidence_on_hit="Hit.",
                evidence_on_miss="Miss.",
            ),
        ],
        expected_answer="y=Ce^x",
    )
    attempt = Attempt(id="a", question_id="q", user_answer="y=C e^x")
    score_vector = CompositeScoringEngine().evaluate(question, attempt, node)

    assert score_vector.final_answer.score >= 90
    assert classify(score_vector, question, attempt, node) == PassState.FALSE_PASS


def test_expected_answer_alias_accepts_equivalent_simple_form() -> None:
    node = red_node()
    question = Question(
        id="q",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Solve.",
        expected_answer="y=Ce^x^2",
        metadata={"expected_answer_aliases": ["y=Cexp(x^2)"]},
    )
    result = MathValidatorScorer().evaluate(question, Attempt(id="a", question_id="q", user_answer="y=C exp(x^2)"), node)

    assert result.dimension_scores[ScoreDimension.FINAL_ANSWER].score == 95


def test_rule_only_case_has_no_p2_or_p3() -> None:
    node = red_node()
    question = Question(id="q", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="Identify method.")
    attempt = Attempt(id="a", question_id="q", user_answer="Use integrating factor for first-order linear.")
    score_vector = CompositeScoringEngine().evaluate(question, attempt, node)

    assert classify(score_vector, question, attempt, node) != PassState.PASS
    assert forward_level(score_vector, question, attempt, node) not in {ForwardLevel.P2_NORMAL, ForwardLevel.P3_STRONG}


def test_composite_audit_helpers_report_active_sources_and_merge_explanation() -> None:
    node = red_node()
    question = question_with_items(
        [
            RubricItem(
                id="method_hit",
                description="Method hit.",
                target_dimensions=["method"],
                required_keywords=["separable"],
                evidence_on_hit="Hit.",
                evidence_on_miss="Miss.",
            )
        ]
    )
    result = CompositeScoringEngine().evaluate_detailed(question, Attempt(id="a", question_id="q", user_answer="separable"), node)

    assert "RubricScorer" in result.get_active_scorer_names()
    assert ScoreDimension.METHOD in result.get_dimension_sources()
    assert "method:" in result.explain_merge_for_dimension("method")


def test_scenario_still_ignored_after_red_team_changes() -> None:
    node = red_node()
    question = Question(id="q", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="No signal.")
    result = CompositeScoringEngine().evaluate_detailed(
        question,
        Attempt(id="a", question_id="q", user_answer="plain", metadata={"scenario": "answer_right_trigger_unclear"}),
        node,
    )

    assert result.score_vector.overall_score() is None
    assert "LegacyScenarioScorer" not in result.get_active_scorer_names()


def test_no_signal_all_dimensions_none() -> None:
    node = red_node()
    question = Question(id="q", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="No signal.")
    score_vector = CompositeScoringEngine().evaluate(question, Attempt(id="a", question_id="q", user_answer="plain"), node)

    assert all(score is None for score in score_vector.as_dimension_map().values())


def test_rule_signal_does_not_fill_process_or_final_answer() -> None:
    node = red_node()
    question = Question(id="q", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="Rule signal only.")
    score_vector = CompositeScoringEngine().evaluate(
        question,
        Attempt(id="a", question_id="q", user_answer="This is separable with integrating factor."),
        node,
    )

    assert score_vector.trigger is not None
    assert score_vector.process is None
    assert score_vector.final_answer is None


def test_rule_only_eval_case_explicitly_stays_below_normal_forward() -> None:
    node = red_node()
    question = Question(id="q", node_id=node.id, question_type=QuestionType.DIAGNOSTIC, prompt="Rule-only audit.")
    attempt = Attempt(id="a", question_id="q", user_answer="first-order linear integrating factor")
    detailed = CompositeScoringEngine().evaluate_detailed(question, attempt, node)

    assert detailed.get_active_scorer_names() == ["RuleScorer"]
    assert forward_level(detailed.score_vector, question, attempt, node) == ForwardLevel.P0_NONE


def test_golden_eval_still_passes_30_cases_after_red_team_changes() -> None:
    spec = importlib.util.spec_from_file_location("run_evals", PROJECT_ROOT / "evals" / "run_evals.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert len(module.load_golden_cases()) == 30
    assert module.main() == 0
