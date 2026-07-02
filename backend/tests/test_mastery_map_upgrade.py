from __future__ import annotations

from typing import Any

from app.challenge.engine import ChallengeEngine
from app.challenge.models import ChallengeEvaluation
from app.challenge.repository import ChallengeRepository
from app.core.enums import ErrorType, PassState, ScoreDimension
from app.core.schemas import Attempt
from app.services.rubric_scorer import RubricScorer
from app.services.rule_scorer import RuleScorer


def test_challenge_status_exposes_mastery_for_macro_and_micro_nodes(tmp_path) -> None:
    payload = ChallengeEngine(processor=QueueProcessor([])).start(
        "ode_network_mvp",
        session_id="mastery-start",
        session_root=tmp_path,
    )

    mastery = payload["challenge"]["mastery"]
    assert len(mastery) == 21
    assert mastery["ode_separable"]["visual_state"] == "locked"
    assert mastery["ode_separable.concept"]["visual_state"] == "active"
    assert mastery["ode_separable.concept"]["mastery_score"] == 0


def test_micro_pass_updates_mastery_without_creating_stable_mastery_too_early(tmp_path) -> None:
    engine = ChallengeEngine(processor=QueueProcessor([(PassState.PASS, None)]))
    engine.start("ode_network_mvp", session_id="micro-mastery-pass", session_root=tmp_path)

    payload = engine.submit(session_id="micro-mastery-pass", answer="pass", session_root=tmp_path)

    concept_mastery = payload["challenge"]["mastery"]["ode_separable.concept"]
    assert concept_mastery["mastery_score"] >= 72
    assert concept_mastery["confidence"] > 0
    assert concept_mastery["stability"] > 0
    assert concept_mastery["visual_state"] == "lit_unstable"
    assert payload["challenge"]["mastery"]["ode_separable.trigger"]["visual_state"] == "active"


def test_micro_fail_records_weak_dimension_and_stays_repair_active(tmp_path) -> None:
    engine = ChallengeEngine(processor=QueueProcessor([(PassState.FAIL, ErrorType.TRIGGER_FAILURE)]))
    engine.start("ode_network_mvp", session_id="micro-mastery-fail", session_root=tmp_path)

    payload = engine.submit(session_id="micro-mastery-fail", answer="wrong", session_root=tmp_path)

    concept_mastery = payload["challenge"]["mastery"]["ode_separable.concept"]
    assert concept_mastery["visual_state"] == "repair"
    assert concept_mastery["recent_root_causes"] == ["trigger_failure"]
    assert "trigger" in concept_mastery["weak_dimensions"]
    assert payload["challenge"]["current_task"]["task_id"] == "ode_separable.concept"


def test_macro_fail_penalizes_one_root_cause_target_micro_node(tmp_path) -> None:
    outcomes = [(PassState.PASS, None)] * 6 + [(PassState.FAIL, ErrorType.CALCULATION_ERROR)]
    engine = ChallengeEngine(processor=QueueProcessor(outcomes))
    engine.start("ode_network_mvp", session_id="macro-mastery-fail", session_root=tmp_path)

    for _ in outcomes:
        payload = engine.submit(session_id="macro-mastery-fail", answer="attempt", session_root=tmp_path)

    assert payload["challenge"]["current_task"]["task_id"] == "ode_separable.calculation"
    calculation = payload["challenge"]["mastery"]["ode_separable.calculation"]
    concept = payload["challenge"]["mastery"]["ode_separable.concept"]
    assert calculation["visual_state"] == "repair"
    assert "calculation_error" in calculation["recent_root_causes"]
    assert "calculation" in calculation["weak_dimensions"]
    assert concept["visual_state"] == "lit_unstable"


def test_rubric_partial_credit_marks_incomplete_concept_as_partial_evidence() -> None:
    engine = ChallengeEngine()
    graph = ChallengeRepository().load_graph("ode_network_mvp")
    question_spec = ChallengeRepository().load_question_bank("ode_network_mvp").questions[0]
    question = engine._to_domain_question(graph, question_spec)
    node = engine._micro_node_adapter(graph, engine._micro(graph, "ode_separable.concept"))
    attempt = Attempt(
        id="partial",
        question_id=question.id,
        user_answer="这是可分离，因为右端可以拆成一个只含 x 的部分和一个只含 y 的部分。",
    )

    result = RubricScorer().evaluate(question, attempt, node)

    score = result.dimension_scores[ScoreDimension.CONCEPT]
    assert 0 < score.score < 70
    assert "partial_matched=['sep_concept_structure']" in score.evidence
    assert "required_missed=[]" in score.evidence


def test_rubric_reads_steps_and_self_explanation_for_concept_evidence() -> None:
    engine = ChallengeEngine()
    graph = ChallengeRepository().load_graph("ode_network_mvp")
    question_spec = ChallengeRepository().load_question_bank("ode_network_mvp").questions[0]
    question = engine._to_domain_question(graph, question_spec)
    node = engine._micro_node_adapter(graph, engine._micro(graph, "ode_separable.concept"))
    attempt = Attempt(
        id="steps",
        question_id=question.id,
        user_answer="属于这种类型。",
        response_steps=["dy/dx=f(x)g(y)", "f(x)=x", "g(y)=1+y^2"],
        self_explanation="所以它是可分离变量方程。",
    )

    result = RubricScorer().evaluate(question, attempt, node)

    assert result.dimension_scores[ScoreDimension.CONCEPT].score == 100


def test_rule_scorer_does_not_leak_method_signal_into_concept_only_question() -> None:
    engine = ChallengeEngine()
    graph = ChallengeRepository().load_graph("ode_network_mvp")
    question_spec = ChallengeRepository().load_question_bank("ode_network_mvp").questions[0]
    question = engine._to_domain_question(graph, question_spec)
    node = engine._micro_node_adapter(graph, engine._micro(graph, "ode_separable.concept"))
    attempt = Attempt(
        id="rule-scope",
        question_id=question.id,
        user_answer="属于可分离变量方程，可以分离变量。",
    )

    result = RuleScorer().evaluate(question, attempt, node)

    assert result.is_active is False
    assert ScoreDimension.TRIGGER not in result.dimension_scores
    assert ScoreDimension.METHOD not in result.dimension_scores


class QueueProcessor:
    def __init__(self, outcomes: list[tuple[PassState, ErrorType | None]]) -> None:
        self.outcomes = list(outcomes)

    def __call__(self, question: Any, attempt: Any, node: Any) -> ChallengeEvaluation:
        del attempt, node
        if not self.outcomes:
            raise AssertionError("QueueProcessor has no remaining outcomes")
        pass_state, root_cause = self.outcomes.pop(0)
        return ChallengeEvaluation(
            pass_state=pass_state,
            root_cause=root_cause,
            coach_payload={
                "question_id": question.id,
                "pass_state": pass_state.value,
                "score_vector_summary": {
                    "trigger": {"score": 25} if root_cause == ErrorType.TRIGGER_FAILURE else None,
                    "calculation": {"score": 20} if root_cause == ErrorType.CALCULATION_ERROR else None,
                },
                "learner_explanation": "fake challenge evaluation",
                "recommended_actions": [],
                "rollback_required": False,
                "rollback_nodes": [],
                "forward_allowed": False,
                "forward_nodes": [],
                "next_action_hint": "fake next action",
                "response_evidence_present": {
                    "has_response_steps": False,
                    "response_step_count": 0,
                    "has_self_explanation": False,
                },
                "session_log_written": False,
                "session_id": None,
            },
        )
