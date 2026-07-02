from __future__ import annotations

from typing import Any

from app.challenge.engine import ChallengeEngine
from app.challenge.models import ChallengeEvaluation
from app.challenge.repository import ChallengeRepository
from app.core.enums import ErrorType, NodeStatus, NodeType, PassState, QuestionType, ScoreDimension
from app.core.schemas import (
    Attempt,
    CompositeScoreResult,
    DimensionScore,
    KnowledgeNode,
    PassCriteria,
    Question,
    ScorerResult,
    ScoreVector,
)
from app.logic_graph.models import LogicAbilityKind, LogicAbilitySpec, LogicEdgeSpec, LogicEdgeType, LogicGraph
from app.logic_graph.quality_validator import KnowledgeGraphQualityValidator
from app.logic_graph.repository import LogicGraphRepository
from app.services.diagnosis_engine import DiagnosisEngine


def test_quality_validator_accepts_current_network_without_blocking_errors() -> None:
    challenge_graph = ChallengeRepository().load_graph("ode_network_mvp")
    logic_graph = LogicGraphRepository().load_graph("ode_network_mvp")

    report = KnowledgeGraphQualityValidator().validate(challenge_graph, logic_graph)

    assert report.passed is True
    assert report.error_count == 0
    assert {issue.code for issue in report.issues}.isdisjoint(
        {
            "micro_missing_hidden_ability",
            "error_missing_hidden_ability_mapping",
            "boss_missing_micro_coverage",
            "hidden_ability_missing_evidence_source",
            "hidden_ability_missing_why_exists",
        }
    )


def test_quality_validator_rejects_trainable_micro_without_hidden_ability() -> None:
    challenge_graph = ChallengeRepository().load_graph("ode_network_mvp")
    logic_graph = LogicGraphRepository().load_graph("ode_network_mvp")
    node_map = dict(logic_graph.node_ability_map)
    node_map.pop("ode_separable.trigger")
    weakened_graph = logic_graph.model_copy(update={"node_ability_map": node_map})

    report = KnowledgeGraphQualityValidator().validate(challenge_graph, weakened_graph)

    assert report.passed is False
    assert any(
        issue.code == "micro_missing_hidden_ability" and issue.node_id == "ode_separable.trigger"
        for issue in report.issues
    )


def test_quality_validator_rejects_core_error_without_repair_ability_mapping() -> None:
    challenge_graph = ChallengeRepository().load_graph("ode_network_mvp")
    logic_graph = LogicGraphRepository().load_graph("ode_network_mvp")
    error_map = dict(logic_graph.error_ability_map)
    error_map.pop(ErrorType.PROCESS_GAP)
    weakened_graph = logic_graph.model_copy(update={"error_ability_map": error_map})

    report = KnowledgeGraphQualityValidator().validate(challenge_graph, weakened_graph)

    assert report.passed is False
    assert any(
        issue.code == "error_missing_hidden_ability_mapping"
        and "process_gap" in issue.message
        for issue in report.issues
    )


def test_quality_validator_detects_ultimate_graph_quality_failures() -> None:
    challenge_graph = ChallengeRepository().load_graph("ode_network_mvp")
    logic_graph = LogicGraphRepository().load_graph("ode_network_mvp")
    bad_edges = [
        *logic_graph.edges,
        LogicEdgeSpec(
            id="bad.self.loop",
            edge_type=LogicEdgeType.REQUIRES,
            source_id="ode.logic.separable.trigger_split",
            target_id="ode.logic.separable.trigger_split",
            label="bad self loop",
        ),
        LogicEdgeSpec(
            id="bad.cycle",
            edge_type=LogicEdgeType.REQUIRES,
            source_id="ode.logic.separable.method_reason",
            target_id="ode.logic.separable.trigger_split",
            label="bad reverse dependency",
        ),
    ]
    weakened_graph = logic_graph.model_copy(update={"edges": bad_edges})

    report = KnowledgeGraphQualityValidator().validate(challenge_graph, weakened_graph)

    assert report.passed is False
    assert {issue.code for issue in report.issues} >= {
        "logic_edge_self_loop",
        "logic_dependency_cycle",
    }


def test_quality_validator_detects_visible_node_explosion_and_repair_target_gap() -> None:
    challenge_graph = ChallengeRepository().load_graph("ode_network_mvp")
    logic_graph = LogicGraphRepository().load_graph("ode_network_mvp")
    bloated_contains = dict(challenge_graph.contains)
    bloated_contains["ode_separable"] = [f"fake.visible.{index}" for index in range(13)]
    bloated_challenge = challenge_graph.model_copy(update={"contains": bloated_contains})
    macro_target_ability = logic_graph.ability_by_id("ode.logic.separable.product_structure")
    assert macro_target_ability is not None
    updated_abilities = [
        ability.model_copy(update={"repair_target_node_id": "ode_separable"})
        if ability.id == macro_target_ability.id else ability
        for ability in logic_graph.abilities
    ]
    weakened_logic = logic_graph.model_copy(
        update={
            "abilities": updated_abilities,
            "error_ability_map": {ErrorType.CONCEPT_GAP: [macro_target_ability.id]},
        }
    )

    report = KnowledgeGraphQualityValidator().validate(bloated_challenge, weakened_logic)

    assert report.passed is False
    assert {issue.code for issue in report.issues} >= {
        "macro_visible_micro_node_explosion",
        "root_cause_has_no_micro_repair_target",
    }


def test_diagnosis_uses_hidden_logic_contradiction_as_root_cause_evidence() -> None:
    node = diagnostic_node(
        "ode_separable.trigger",
        [ScoreDimension.TRIGGER],
        common_errors=[ErrorType.TRIGGER_FAILURE],
    )
    question = Question(
        id="ultimate-trigger",
        node_id="ode_separable.trigger",
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Classify the equation.",
        tested_dimensions=[ScoreDimension.TRIGGER],
        metadata={"challenge_chapter_id": "ode_network_mvp"},
    )
    attempt = Attempt(
        id="ultimate-trigger-a",
        question_id=question.id,
        user_answer="This is separable, but I will use y=vx substitution.",
    )
    composite = CompositeScoreResult(
        score_vector=ScoreVector(trigger=DimensionScore(score=82, evidence="Surface trigger looked plausible.")),
        scorer_results=[
            ScorerResult(
                scorer_name="RubricScorer",
                is_active=True,
                dimension_scores={
                    ScoreDimension.TRIGGER: DimensionScore(score=82, evidence="Surface trigger looked plausible.")
                },
                confidence=0.8,
            )
        ],
        merge_notes=["trigger: RubricScorer"],
    )

    result = DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)

    assert result.root_cause == ErrorType.TRIGGER_FAILURE
    assert result.pass_state == PassState.FAIL
    assert result.diagnosis_trace is not None
    assert any("contradiction:trigger_pattern" in item for item in result.diagnosis_trace.logic_contradictions)
    assert any("Hidden logic graph contradiction" in error.evidence for error in result.error_vector.errors)


def test_surface_keyword_only_stays_low_confidence_and_needs_more_evidence() -> None:
    graph = LogicGraph(
        chapter_id="tmp_logic",
        title="Temporary logic graph",
        abilities=[
            LogicAbilitySpec(
                id="logic.tmp.trigger",
                title="Temporary trigger",
                kind=LogicAbilityKind.TRIGGER_PATTERN,
                owner_node_id="tmp.node",
                dimensions=[ScoreDimension.TRIGGER],
                weak_cues=["separable"],
                repair_target_node_id="tmp.node",
            )
        ],
        node_ability_map={"tmp.node": ["logic.tmp.trigger"]},
        error_ability_map={},
    )
    node = diagnostic_node("tmp.node", [ScoreDimension.TRIGGER])
    question = Question(
        id="tmp-q",
        node_id="tmp.node",
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Classify.",
        tested_dimensions=[ScoreDimension.TRIGGER],
        metadata={"challenge_chapter_id": "tmp_logic"},
    )
    attempt = Attempt(id="tmp-a", question_id=question.id, user_answer="separable")
    composite = CompositeScoreResult(
        score_vector=ScoreVector(),
        scorer_results=[ScorerResult(scorer_name="RubricScorer", is_active=True, confidence=0.4)],
        merge_notes=[],
    )

    result = DiagnosisEngine(logic_graph_repository=StaticLogicRepo(graph)).diagnose_detailed(
        composite,
        question,
        attempt,
        node,
    )

    assert result.root_cause is None
    assert result.confidence <= 0.3
    assert result.recommended_actions[0].action_type == "need_more_evidence"
    assert result.diagnosis_trace is not None
    assert result.diagnosis_trace.surface_keyword_only is True


def test_partial_concept_understanding_is_not_treated_as_plain_fail() -> None:
    node = diagnostic_node("concept.partial", [ScoreDimension.CONCEPT])
    question = Question(
        id="concept-q",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="Explain the concept.",
        tested_dimensions=[ScoreDimension.CONCEPT],
    )
    attempt = Attempt(id="concept-a", question_id=question.id, user_answer="I know the idea but not exact wording.")
    composite = CompositeScoreResult(
        score_vector=ScoreVector(concept=DimensionScore(score=58, evidence="Partially correct concept wording.")),
        scorer_results=[
            ScorerResult(
                scorer_name="RubricScorer",
                is_active=True,
                dimension_scores={
                    ScoreDimension.CONCEPT: DimensionScore(score=58, evidence="Partially correct concept wording.")
                },
                confidence=0.8,
            )
        ],
        merge_notes=["concept: RubricScorer"],
    )

    result = DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)

    assert result.root_cause == ErrorType.CONCEPT_GAP
    assert result.pass_state == PassState.PARTIAL_PASS
    assert result.ability_state == "understands_but_imprecise"


def test_macro_failure_prefers_hidden_ability_repair_target_over_generic_error_mapping() -> None:
    graph = ChallengeRepository().load_graph("ode_network_mvp")
    evaluation = ChallengeEvaluation(
        pass_state=PassState.FAIL,
        root_cause=ErrorType.METHOD_ERROR,
        repair_target_node_id="ode_separable.transformation",
        coach_payload={},
    )

    target = ChallengeEngine()._target_micro_for_evaluation(graph, "ode_separable", evaluation)

    assert target == "ode_separable.transformation"


def diagnostic_node(
    node_id: str,
    dimensions: list[ScoreDimension],
    *,
    common_errors: list[ErrorType] | None = None,
) -> KnowledgeNode:
    return KnowledgeNode(
        id=node_id,
        name="Diagnostic node",
        type=NodeType.METHOD,
        status=NodeStatus.AVAILABLE,
        core_dimensions=dimensions,
        common_errors=common_errors or [ErrorType.CONCEPT_GAP, ErrorType.TRIGGER_FAILURE, ErrorType.METHOD_ERROR],
        description="diagnostic node",
        scoring_weights={dimension: 1 / len(dimensions) for dimension in dimensions},
        pass_criteria=PassCriteria(
            min_overall=70,
            min_required_dimensions={dimension: 70 for dimension in dimensions},
            max_primary_errors=0,
        ),
    )


class StaticLogicRepo:
    def __init__(self, graph: LogicGraph) -> None:
        self.graph = graph

    def try_load_graph(self, chapter_id: str | None) -> LogicGraph | None:
        del chapter_id
        return self.graph

    def load_graph(self, chapter_id: str) -> LogicGraph:
        del chapter_id
        return self.graph
