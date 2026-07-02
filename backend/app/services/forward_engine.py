from __future__ import annotations

from app.core.config import DEFAULT_ENGINE_CONFIG, EngineConfig
from app.core.enums import ErrorType, ForwardLevel, ScoreDimension
from app.core.schemas import ErrorVector, ForwardDecision, KnowledgeNode, ScoreVector


class ForwardEngine:
    def __init__(self, config: EngineConfig = DEFAULT_ENGINE_CONFIG) -> None:
        self.config = config

    def determine_forward_level(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
        node: KnowledgeNode,
    ) -> ForwardLevel:
        return self.decide_forward(score_vector, error_vector, node).level

    def decide_forward(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
        node: KnowledgeNode,
    ) -> ForwardDecision:
        if self._has_false_pass_signal(score_vector):
            return ForwardDecision(
                level=ForwardLevel.P0_NONE,
                forward_nodes=[],
                blocked_nodes=node.successors,
                reason="False-pass signal: final answer is high but trigger or method evidence is weak.",
                allowed_training_modes=["current_node_trigger_drill", "direct_review"],
            )

        primary_errors = error_vector.primary_errors()
        if primary_errors and not self._only_soft_primary_errors(primary_errors):
            return ForwardDecision(
                level=ForwardLevel.P0_NONE,
                forward_nodes=[],
                blocked_nodes=node.successors,
                reason="Primary errors block forward movement.",
                allowed_training_modes=["current_node_review"],
            )
        if primary_errors and self._only_soft_primary_errors(primary_errors):
            return self._p1_decision(node, "Soft primary errors allow only local review and variants, not successor unlock.")

        if not self._required_dimensions_met(score_vector, node):
            overall_for_gate = score_vector.overall_score(node.scoring_weights)
            if overall_for_gate and overall_for_gate >= 70:
                return self._p1_decision(node, "Required dimensions are not all met; allow local variant/review only.")
            return ForwardDecision(
                level=ForwardLevel.P0_NONE,
                forward_nodes=[],
                blocked_nodes=node.successors,
                reason="Required dimensions are below progression threshold.",
                allowed_training_modes=["current_node_review"],
            )

        overall = score_vector.overall_score(node.scoring_weights)
        if overall is None:
            return ForwardDecision(
                level=ForwardLevel.P0_NONE,
                forward_nodes=[],
                blocked_nodes=node.successors,
                reason="No available scored dimensions for forward decision.",
                allowed_training_modes=["current_node_review"],
            )

        if not self._has_sufficient_non_answer_evidence(score_vector):
            if overall >= 70:
                return self._p1_decision(node, "Overall score is acceptable but non-answer evidence is insufficient.")
            return ForwardDecision(
                level=ForwardLevel.P0_NONE,
                forward_nodes=[],
                blocked_nodes=node.successors,
                reason="Non-answer evidence is insufficient and overall score is low.",
                allowed_training_modes=["current_node_review"],
            )

        if overall >= 92 and not error_vector.secondary_errors() and self._strong_forward_ready(score_vector):
            return ForwardDecision(
                level=ForwardLevel.P3_STRONG,
                forward_nodes=node.successors[:2],
                blocked_nodes=node.successors[2:],
                reason="Core dimensions are strong and no primary or secondary errors block progression.",
                allowed_training_modes=["direct_successor", "challenge_variant", "migration_preview"],
            )
        if overall >= node.pass_criteria.min_overall:
            return ForwardDecision(
                level=ForwardLevel.P2_NORMAL,
                forward_nodes=node.successors[:1],
                blocked_nodes=node.successors[1:],
                reason="Required dimensions meet thresholds; unlock one direct successor.",
                allowed_training_modes=["direct_successor", "current_node_variant"],
            )
        if overall >= 70:
            return self._p1_decision(node, "Partial evidence supports review and same-node variants, not successor unlock.")
        return ForwardDecision(
            level=ForwardLevel.P0_NONE,
            forward_nodes=[],
            blocked_nodes=node.successors,
            reason="Overall evidence is below forward threshold.",
            allowed_training_modes=["current_node_review"],
        )

    def select_forward_nodes(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
        node: KnowledgeNode,
    ) -> list[str]:
        return self.decide_forward(score_vector, error_vector, node).forward_nodes

    def _has_false_pass_signal(self, score_vector: ScoreVector) -> bool:
        final_answer = score_vector.get_dimension(ScoreDimension.FINAL_ANSWER)
        if final_answer is None or final_answer.score is None:
            return False
        if final_answer.score < self.config.false_pass_final_answer_min:
            return False
        for dimension in (ScoreDimension.TRIGGER, ScoreDimension.METHOD):
            dimension_score = score_vector.get_dimension(dimension)
            if (
                dimension_score is not None
                and dimension_score.score is not None
                and dimension_score.score < self.config.false_pass_dimension_max
            ):
                return True
        return False

    def _required_dimensions_met(self, score_vector: ScoreVector, node: KnowledgeNode) -> bool:
        for dimension, minimum in node.pass_criteria.min_required_dimensions.items():
            dimension_score = score_vector.get_dimension(dimension)
            if dimension_score is None or dimension_score.score is None:
                return False
            if dimension_score.score < minimum:
                return False
        return True

    def _p1_decision(self, node: KnowledgeNode, reason: str) -> ForwardDecision:
        return ForwardDecision(
            level=ForwardLevel.P1_PARTIAL,
            forward_nodes=[],
            blocked_nodes=node.successors,
            reason=reason,
            allowed_training_modes=["current_node_variant", "direct_review"],
        )

    def _only_soft_primary_errors(self, primary_errors: list) -> bool:
        soft_error_types = {ErrorType.EXPRESSION_WEAKNESS}
        return bool(primary_errors) and all(error.error_type in soft_error_types for error in primary_errors)

    def _has_sufficient_non_answer_evidence(self, score_vector: ScoreVector) -> bool:
        non_answer_scores = []
        for dimension in ScoreDimension:
            if dimension == ScoreDimension.FINAL_ANSWER:
                continue
            dimension_score = score_vector.get_dimension(dimension)
            if dimension_score is not None and dimension_score.score is not None:
                non_answer_scores.append(dimension_score.score)
        return len(non_answer_scores) >= 2 and all(score >= 70 for score in non_answer_scores[:2])

    def _strong_forward_ready(self, score_vector: ScoreVector) -> bool:
        for dimension in (
            ScoreDimension.TRIGGER,
            ScoreDimension.METHOD,
            ScoreDimension.TRANSFORMATION,
            ScoreDimension.CALCULATION,
        ):
            dimension_score = score_vector.get_dimension(dimension)
            if dimension_score is None or dimension_score.score is None or dimension_score.score < 90:
                return False
        return True
