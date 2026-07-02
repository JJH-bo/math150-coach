from __future__ import annotations

import json
from typing import Any

from app.challenge.engine import ChallengeEngine
from app.challenge.models import GuideNodeKind, NetworkEdgeType
from app.challenge.repository import ChallengeRepository
from app.core.enums import ErrorType, PassState, RollbackLevel, ScoreDimension
from app.core.schemas import (
    CompositeScoreResult,
    DiagnosisResult,
    DimensionScore,
    ErrorItem,
    ErrorVector,
    Question,
    ScoreEvidence,
    ScorerResult,
    ScoreVector,
)
from app.logic_graph.evidence_engine import LogicEvidenceEngine
from app.logic_graph.models import AbilityEvidenceStatus, LogicEdgeType
from app.logic_graph.repository import LogicGraphRepository
from app.services.learning_orchestrator import LearningOrchestrator
from app.training.session_log import ensure_no_trusted_fields


def test_logic_graph_loads_hidden_abilities_without_creating_progress_nodes(tmp_path) -> None:
    logic_graph = LogicGraphRepository().load_graph("ode_network_mvp")
    challenge_payload = ChallengeEngine().start(
        "ode_network_mvp",
        session_id="logic-hidden",
        session_root=tmp_path,
    )

    assert len(logic_graph.abilities) >= 12
    assert {edge.edge_type for edge in logic_graph.edges} >= {
        LogicEdgeType.REQUIRES,
        LogicEdgeType.SUPPORTS,
        LogicEdgeType.COMMONLY_CONFUSED_WITH,
    }
    ability_ids = {ability.id for ability in logic_graph.abilities}
    progress_ids = set(challenge_payload["challenge"]["micro_nodes"]) | set(challenge_payload["challenge"]["macro_nodes"])
    assert ability_ids.isdisjoint(progress_ids)


def test_challenge_graph_exposes_non_trainable_guide_nodes_without_progress_state(tmp_path) -> None:
    graph = ChallengeRepository().load_graph("ode_network_mvp")
    payload = ChallengeEngine().start("ode_network_mvp", session_id="guide-nodes", session_root=tmp_path)

    guide_ids = {guide.id for guide in graph.guide_nodes}
    assert len(guide_ids) == 5
    assert {guide.kind for guide in graph.guide_nodes} >= {
        GuideNodeKind.FOUNDATION_ANCHOR,
        GuideNodeKind.BRIDGE,
        GuideNodeKind.BOSS_GATE,
        GuideNodeKind.WARNING_BEACON,
    }
    assert guide_ids.isdisjoint(payload["challenge"]["micro_nodes"])
    assert guide_ids.isdisjoint(payload["challenge"]["macro_nodes"])
    assert guide_ids.isdisjoint(payload["challenge"]["mastery"])
    public_guide_ids = {guide["id"] for guide in payload["challenge"]["network"]["guide_nodes"]}
    assert public_guide_ids == guide_ids


def test_guide_edges_express_navigation_without_unlocking_tasks() -> None:
    graph = ChallengeRepository().load_graph("ode_network_mvp")

    guide_edges = [edge for edge in graph.typed_edges if edge.source_id.startswith("ode.guide.")]
    assert {edge.edge_type for edge in guide_edges} >= {
        NetworkEdgeType.SUPPORT,
        NetworkEdgeType.BRIDGE,
        NetworkEdgeType.GATEWAY,
        NetworkEdgeType.REPAIR,
    }
    assert all(edge.source_id not in graph.contains for edge in guide_edges)


def test_logic_evidence_maps_transformation_root_to_hidden_ability() -> None:
    insight = LogicEvidenceEngine().analyze(
        transformation_question(),
        simple_attempt(),
        transformation_composite_result(),
        transformation_diagnosis_result(),
    )

    assert insight.active is True
    assert insight.primary_ability_id == "ode.logic.separable.side_move"
    assert insight.primary_target_node_id == "ode_separable.transformation"
    primary = [item for item in insight.ability_evidence if item.ability_id == insight.primary_ability_id][0]
    assert primary.status == AbilityEvidenceStatus.MISSING
    assert any("required_missed" in signal for signal in primary.signals)


def test_logic_evidence_keeps_final_answer_as_downstream_not_primary_when_transformation_root() -> None:
    insight = LogicEvidenceEngine().analyze(
        transformation_question(),
        simple_attempt(),
        transformation_composite_result(),
        transformation_diagnosis_result(),
    )

    assert insight.primary_ability_id != "ode.logic.separable.integral_constant"
    assert insight.primary_target_node_id == "ode_separable.transformation"
    assert any("root_cause:transformation_error" in item for item in insight.ability_chain_summary)


def test_logic_evidence_detects_response_contradiction_for_surface_keyword_answer() -> None:
    question = Question(
        id="logic-q-trigger",
        node_id="ode_separable.trigger",
        question_type="diagnostic",
        prompt="Classify the equation.",
        tested_dimensions=[ScoreDimension.TRIGGER],
        metadata={"challenge_chapter_id": "ode_network_mvp"},
    )
    composite = CompositeScoreResult(
        score_vector=ScoreVector(trigger=DimensionScore(score=72, evidence="surface trigger keyword appears")),
        scorer_results=[],
        merge_notes=[],
    )
    diagnosis = DiagnosisResult(
        score_vector=composite.score_vector,
        error_vector=ErrorVector(errors=[]),
        pass_state=PassState.FALSE_PASS,
        explanation="debug",
        learner_explanation="coach",
        next_action_hint="need evidence",
        root_cause=None,
    )

    insight = LogicEvidenceEngine().analyze(
        question,
        simple_attempt(answer="这是可分离，但我准备用积分因子来做。"),
        composite,
        diagnosis,
    )

    assert insight.primary_ability_id == "ode.logic.separable.trigger_split"
    primary = [item for item in insight.ability_evidence if item.ability_id == insight.primary_ability_id][0]
    assert primary.status == AbilityEvidenceStatus.CONTRADICTED
    assert any(signal.startswith("response_contradiction") for signal in primary.signals)
    assert insight.repair_cues


def test_challenge_submit_exposes_logic_insight_without_changing_movement_or_trusted_boundary(tmp_path) -> None:
    engine = ChallengeEngine()
    engine.start("ode_network_mvp", session_id="logic-submit", session_root=tmp_path)

    payload = engine.submit(
        session_id="logic-submit",
        answer="这是可分离变量方程，dy/dx=f(x)g(y)，其中 f(x)=x，g(y)=1+y^2。",
        steps=["识别 f(x)g(y)", "指出 f(x) 与 g(y)"],
        explanation="右端能拆成只含 x 的因子与只含 y 的因子。",
        session_root=tmp_path,
    )

    assert payload["challenge_attempt"]["pass_state"] == "pass"
    assert payload["challenge"]["current_task"]["task_id"] == "ode_separable.trigger"
    assert payload["logic_insight"]["active"] is True
    assert payload["logic_insight"]["primary_target_node_id"] == "ode_separable.concept"
    ensure_no_trusted_fields(payload)
    text = json.dumps(payload, ensure_ascii=False)
    assert "RubricScorer" not in text
    assert "MathValidatorScorer" not in text


def test_orchestrator_logic_insight_is_advisory_and_movement_stays_owned_by_engines() -> None:
    graph = ChallengeRepository().load_graph("ode_network_mvp")
    question_spec = ChallengeRepository().load_question_bank("ode_network_mvp").questions[3]
    engine = ChallengeEngine()
    question = engine._to_domain_question(graph, question_spec)
    node = engine._micro_node_adapter(graph, engine._micro(graph, "ode_separable.transformation"))
    orchestrated = LearningOrchestrator().process(
        question,
        simple_attempt(answer="I will integrate directly without separating the variables."),
        node,
    )

    assert orchestrated.logic_insight.active is True
    assert orchestrated.rollback_decision.rollback_nodes == orchestrated.diagnosis_result.rollback_nodes
    assert orchestrated.forward_decision.forward_nodes == orchestrated.diagnosis_result.forward_nodes


def transformation_question() -> Question:
    return Question(
        id="logic-q-transform",
        node_id="ode_separable",
        question_type="diagnostic",
        prompt="Solve a separable equation.",
        tested_dimensions=[
            ScoreDimension.TRIGGER,
            ScoreDimension.METHOD,
            ScoreDimension.TRANSFORMATION,
            ScoreDimension.CALCULATION,
            ScoreDimension.FINAL_ANSWER,
        ],
        metadata={"challenge_chapter_id": "ode_network_mvp"},
    )


def simple_attempt(answer: str = "I separated variables but wrote the wrong side move.") -> Any:
    from app.core.schemas import Attempt

    return Attempt(
        id="logic-a",
        question_id="logic-q-transform",
        user_answer=answer,
        response_steps=["separable", "wrong transformation"],
        self_explanation="I tried to separate variables.",
    )


def transformation_composite_result() -> CompositeScoreResult:
    score_vector = ScoreVector(
        trigger=DimensionScore(score=86, evidence="trigger identified"),
        method=DimensionScore(score=84, evidence="method selected"),
        transformation=DimensionScore(score=25, evidence="variables placed on wrong sides"),
        calculation=DimensionScore(score=20, evidence="calculation downstream of bad transformation"),
        final_answer=DimensionScore(score=0, evidence="final answer wrong downstream"),
    )
    return CompositeScoreResult(
        score_vector=score_vector,
        scorer_results=[
            ScorerResult(
                scorer_name="RubricScorer",
                is_active=True,
                dimension_scores={
                    ScoreDimension.TRANSFORMATION: score_vector.transformation,
                    ScoreDimension.CALCULATION: score_vector.calculation,
                    ScoreDimension.FINAL_ANSWER: score_vector.final_answer,
                },
                evidence=[
                    ScoreEvidence(
                        source="rubric",
                        dimension=ScoreDimension.TRANSFORMATION,
                        score=25,
                        confidence=0.8,
                        evidence="side move required item missed",
                        required_missed=["sep_macro_transform"],
                    )
                ],
                confidence=0.8,
            )
        ],
        merge_notes=["transformation: RubricScorer"],
    )


def transformation_diagnosis_result() -> DiagnosisResult:
    score_vector = transformation_composite_result().score_vector
    error = ErrorItem(
        error_type=ErrorType.TRANSFORMATION_ERROR,
        weight=0.9,
        related_dimensions=[ScoreDimension.TRANSFORMATION],
        evidence="Transformation failed before calculation.",
        suggested_rollback_level=RollbackLevel.R2_PREREQUISITE,
    )
    return DiagnosisResult(
        score_vector=score_vector,
        error_vector=ErrorVector(errors=[error]),
        pass_state=PassState.FAIL,
        explanation="debug",
        learner_explanation="coach explanation",
        next_action_hint="repair transformation",
        root_cause=ErrorType.TRANSFORMATION_ERROR,
        primary_errors=[ErrorType.TRANSFORMATION_ERROR],
    )
