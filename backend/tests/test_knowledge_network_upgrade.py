from __future__ import annotations

from typing import Any

from app.challenge.engine import ChallengeEngine
from app.challenge.models import ChallengeEvaluation, NetworkEdgeType
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
from app.services.diagnosis_engine import DiagnosisEngine
from app.training.session_log import ensure_no_trusted_fields


def test_challenge_graph_exposes_atom_compare_and_typed_edges() -> None:
    graph = ChallengeRepository().load_graph("ode_network_mvp")

    assert len(graph.atom_nodes) >= len(graph.micro_nodes)
    assert len(graph.compare_nodes) == 3
    assert {edge.edge_type for edge in graph.typed_edges} >= {
        NetworkEdgeType.PREREQUISITE,
        NetworkEdgeType.CONFUSION,
        NetworkEdgeType.SYNTHESIS,
    }
    assert graph.macro_challenges[0].id == "ode_separable.macro_challenge"


def test_atom_nodes_are_hidden_prerequisites_not_progress_nodes(tmp_path) -> None:
    payload = ChallengeEngine(processor=QueueProcessor([])).start(
        "ode_network_mvp",
        session_id="atom-hidden",
        session_root=tmp_path,
    )

    challenge = payload["challenge"]
    atom_ids = {atom["id"] for atom in challenge["network"]["atom_nodes"]}
    assert atom_ids
    assert not atom_ids.intersection(challenge["micro_nodes"])
    assert not atom_ids.intersection(challenge["macro_nodes"])
    assert not atom_ids.intersection(challenge["mastery"])
    assert len(challenge["mastery"]) == 21


def test_logic_overlay_exposes_ultimate_logic_layer_without_progress_nodes(tmp_path) -> None:
    payload = ChallengeEngine(processor=QueueProcessor([])).start(
        "ode_network_mvp",
        session_id="logic-overlay",
        session_root=tmp_path,
    )

    challenge = payload["challenge"]
    overlay = challenge["logic_overlay"]
    logic_nodes = overlay["logic_nodes"]
    logic_edges = overlay["logic_edges"]
    logic_ids = {node["id"] for node in logic_nodes}
    logic_kinds = {node["node_kind"] for node in logic_nodes}
    edge_types = {edge["edge_type"] for edge in logic_edges}

    assert overlay["active"] is True
    assert {"hidden_ability", "compare_guard", "transfer_node", "synthesis_node", "boss_criterion"}.issubset(logic_kinds)
    assert {"derives_to", "transforms_to", "repairs", "transfers_to", "boss_checks"}.issubset(edge_types)
    assert not logic_ids.intersection(challenge["micro_nodes"])
    assert not logic_ids.intersection(challenge["macro_nodes"])
    assert not logic_ids.intersection(challenge["macro_challenges"])
    assert not logic_ids.intersection(challenge["mastery"])
    assert challenge["current_task"]["task_id"] not in logic_ids
    ensure_no_trusted_fields(payload)


def test_logic_overlay_keeps_remediates_compatible_as_repairs(tmp_path) -> None:
    payload = ChallengeEngine(processor=QueueProcessor([])).start(
        "ode_network_mvp",
        session_id="logic-repairs",
        session_root=tmp_path,
    )

    edge_types = {edge["edge_type"] for edge in payload["challenge"]["logic_overlay"]["logic_edges"]}

    assert "repairs" in edge_types
    assert "remediates" not in edge_types


def test_status_payload_contains_public_network_without_trusted_fields(tmp_path) -> None:
    payload = ChallengeEngine(processor=QueueProcessor([])).start(
        "ode_network_mvp",
        session_id="network-public",
        session_root=tmp_path,
    )

    network = payload["challenge"]["network"]
    assert network["node_model"]["atom_node"].startswith("隐藏原子前置能力")
    assert network["macro_challenges"][0]["node_kind"] == "boss_challenge"
    assert network["compare_nodes"][0]["id"].startswith("ode.compare.")
    ensure_no_trusted_fields(payload)


def test_current_micro_node_exposes_atom_hints_without_repair_focus_initially(tmp_path) -> None:
    payload = ChallengeEngine(processor=QueueProcessor([])).start(
        "ode_network_mvp",
        session_id="atom-initial",
        session_root=tmp_path,
    )

    hints = payload["challenge"]["active_atom_hints"]
    assert [hint["micro_node_id"] for hint in hints] == ["ode_separable.concept"]
    assert hints[0]["repair_focus"] is False


def test_micro_fail_stays_on_micro_and_marks_atom_repair_focus(tmp_path) -> None:
    engine = ChallengeEngine(processor=QueueProcessor([(PassState.FAIL, ErrorType.CONCEPT_GAP)]))
    engine.start("ode_network_mvp", session_id="atom-repair", session_root=tmp_path)

    payload = engine.submit(session_id="atom-repair", answer="wrong", session_root=tmp_path)

    assert payload["challenge"]["current_task"]["task_id"] == "ode_separable.concept"
    hints = payload["challenge"]["active_atom_hints"]
    assert hints[0]["id"] == "ode.atom.separable_product_form"
    assert hints[0]["repair_focus"] is True
    assert hints[0]["title"] in payload["next_step_plan"]


def test_compare_nodes_are_public_map_metadata_not_trainable_tasks(tmp_path) -> None:
    payload = ChallengeEngine(processor=QueueProcessor([])).start(
        "ode_network_mvp",
        session_id="compare-public",
        session_root=tmp_path,
    )

    compare_ids = {node["id"] for node in payload["challenge"]["network"]["compare_nodes"]}
    assert "ode.compare.separable_vs_linear" in compare_ids
    assert not compare_ids.intersection(payload["challenge"]["micro_nodes"])
    assert not compare_ids.intersection(payload["challenge"]["macro_challenges"])


def test_ability_state_distinguishes_imprecise_concept_from_plain_wrong() -> None:
    result = diagnose_with_scores(
        ScoreVector(
            concept=DimensionScore(score=55, evidence="partial concept evidence"),
            expression=DimensionScore(score=85, evidence="readable expression"),
        ),
        [ScoreDimension.CONCEPT],
    )

    assert result.root_cause == ErrorType.CONCEPT_GAP
    assert result.ability_state == "understands_but_imprecise"
    assert result.ability_state_label
    assert result.ability_state_explanation


def test_ability_state_marks_answer_without_evidence_false_pass() -> None:
    result = diagnose_with_scores(
        ScoreVector(
            final_answer=DimensionScore(score=100, evidence="expected answer appears"),
            trigger=DimensionScore(score=20, evidence="no trigger reason"),
            method=DimensionScore(score=25, evidence="no method reason"),
        ),
        [ScoreDimension.FINAL_ANSWER, ScoreDimension.TRIGGER, ScoreDimension.METHOD],
    )

    assert result.pass_state == PassState.FALSE_PASS
    assert result.ability_state == "answer_without_evidence"
    assert result.ability_state_explanation


def diagnose_with_scores(score_vector: ScoreVector, dimensions: list[ScoreDimension]):
    node = KnowledgeNode(
        id="ability-node",
        name="能力节点",
        type=NodeType.CONCEPT,
        status=NodeStatus.AVAILABLE,
        description="ability node",
        core_dimensions=dimensions,
        common_errors=[ErrorType.CONCEPT_GAP, ErrorType.TRIGGER_FAILURE, ErrorType.METHOD_ERROR],
        scoring_weights={dimension: 1 / len(dimensions) for dimension in dimensions},
        pass_criteria=PassCriteria(
            min_overall=70,
            min_required_dimensions={dimension: 70 for dimension in dimensions},
        ),
    )
    question = Question(
        id="ability-question",
        node_id=node.id,
        question_type=QuestionType.DIAGNOSTIC,
        prompt="diagnose ability",
        tested_dimensions=dimensions,
    )
    attempt = Attempt(id="ability-attempt", question_id=question.id, user_answer="answer")
    dimension_scores = {
        dimension: score_vector.get_dimension(dimension)
        for dimension in dimensions
        if score_vector.get_dimension(dimension) is not None
    }
    composite = CompositeScoreResult(
        score_vector=score_vector,
        scorer_results=[
            ScorerResult(
                scorer_name="RubricScorer",
                is_active=True,
                dimension_scores=dimension_scores,
                confidence=0.8,
            )
        ],
        merge_notes=[f"{dimension.value}: RubricScorer" for dimension in dimensions],
    )
    return DiagnosisEngine().diagnose_detailed(composite, question, attempt, node)


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
                    "concept": {"score": 25} if root_cause == ErrorType.CONCEPT_GAP else None,
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
