from __future__ import annotations

from app.core.enums import QuestionType, ScoreDimension
from app.core.schemas import Attempt, KnowledgeNode, Question
from app.services.scoring_engine import ScoringEngine


def sample_node() -> KnowledgeNode:
    return KnowledgeNode(
        id="ode_separable",
        name="可分离变量方程",
        type="method",
        status="available",
        prerequisites=["ode_basic_concept", "ode_general_special_solution"],
        successors=["ode_first_order_linear"],
        core_dimensions=[
            "trigger",
            "method",
            "transformation",
            "process",
            "calculation",
            "final_answer",
        ],
        common_errors=["calculation_error", "trigger_failure", "method_error"],
        description="Sample node.",
        trigger_patterns=["dy/dx can be separated."],
        scoring_weights={
            "trigger": 0.2,
            "method": 0.2,
            "transformation": 0.2,
            "process": 0.15,
            "calculation": 0.15,
            "final_answer": 0.1,
        },
        rollback_policy={
            "calculation_error": {
                "level": "r1_internal",
                "target_nodes": ["__self__"],
                "notes": "Local calculation repair.",
            }
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
            "allow_false_pass": False,
        },
        variant_policy={
            "template_families": ["direct_separable"],
            "parameter_focus": ["separable_factors"],
            "validation_required": True,
        },
    )


def test_scoring_engine_process_right_calculation_wrong_shape() -> None:
    engine = ScoringEngine()
    node = sample_node()
    question = Question(
        id="q1",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Solve dy/dx=2xy.",
        tested_dimensions=node.core_dimensions,
    )
    attempt = Attempt(
        id="a1",
        question_id="q1",
        user_answer="Right method, wrong integral.",
        metadata={"scenario": "process_right_calculation_wrong"},
    )

    score_vector = engine.evaluate(question, attempt, node)

    assert score_vector.method.score >= 85
    assert score_vector.transformation.score >= 80
    assert score_vector.calculation.score < 30
    assert score_vector.final_answer.score == 0
    assert score_vector.migration is None


def test_scoring_engine_answer_right_trigger_unclear_shape() -> None:
    engine = ScoringEngine()
    node = sample_node()
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
        user_answer="Correct final answer but no explanation.",
        metadata={"scenario": "answer_right_trigger_unclear"},
    )

    score_vector = engine.evaluate(question, attempt, node)

    assert score_vector.final_answer.score >= 90
    assert score_vector.trigger.score < 60
    assert score_vector.method.score < 60
