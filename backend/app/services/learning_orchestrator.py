from __future__ import annotations

from dataclasses import dataclass

from app.core.schemas import (
    Attempt,
    CompositeScoreResult,
    DiagnosisResult,
    ForwardDecision,
    KnowledgeNode,
    Question,
    RollbackDecision,
)
from app.logic_graph.evidence_engine import LogicEvidenceEngine
from app.logic_graph.models import LogicDiagnosisInsight
from app.services.composite_scoring_engine import CompositeScoringEngine
from app.services.diagnosis_engine import DiagnosisEngine
from app.services.forward_engine import ForwardEngine
from app.services.rollback_engine import RollbackEngine


class MovementConsistencyError(RuntimeError):
    """Raised when explicit movement decisions diverge from DiagnosisResult compatibility fields."""


@dataclass(frozen=True)
class OrchestratedAttemptResult:
    node: KnowledgeNode
    question: Question
    attempt: Attempt
    score_result: CompositeScoreResult
    diagnosis_result: DiagnosisResult
    rollback_decision: RollbackDecision
    forward_decision: ForwardDecision
    next_action_hint: str
    logic_insight: LogicDiagnosisInsight
    rollback_consistent: bool
    forward_consistent: bool


class LearningOrchestrator:
    """Fixed training-loop orchestrator.

    This service exposes existing engines in a stable order. It does not add
    scoring, diagnosis, rollback, forward, or action policy logic.
    """

    def __init__(
        self,
        scoring_engine: CompositeScoringEngine | None = None,
        diagnosis_engine: DiagnosisEngine | None = None,
        rollback_engine: RollbackEngine | None = None,
        forward_engine: ForwardEngine | None = None,
        logic_evidence_engine: LogicEvidenceEngine | None = None,
    ) -> None:
        self.scoring_engine = scoring_engine or CompositeScoringEngine()
        self.diagnosis_engine = diagnosis_engine or DiagnosisEngine()
        self.rollback_engine = rollback_engine or RollbackEngine()
        self.forward_engine = forward_engine or ForwardEngine()
        self.logic_evidence_engine = logic_evidence_engine or LogicEvidenceEngine()

    def process(
        self,
        question: Question,
        attempt: Attempt,
        node: KnowledgeNode,
    ) -> OrchestratedAttemptResult:
        score_result = self.scoring_engine.evaluate_detailed(question, attempt, node)
        diagnosis_result = self.diagnosis_engine.diagnose_detailed(score_result, question, attempt, node)
        rollback_decision = self.rollback_engine.decide_rollback(diagnosis_result.error_vector, node)
        forward_decision = self.forward_engine.decide_forward(
            diagnosis_result.score_vector,
            diagnosis_result.error_vector,
            node,
        )

        rollback_consistent = (
            diagnosis_result.rollback_level == rollback_decision.level
            and diagnosis_result.rollback_nodes == rollback_decision.rollback_nodes
        )
        forward_consistent = (
            diagnosis_result.forward_level == forward_decision.level
            and diagnosis_result.forward_nodes == forward_decision.forward_nodes
        )
        if not rollback_consistent or not forward_consistent:
            raise MovementConsistencyError("Explicit movement decisions differ from DiagnosisResult compatibility fields.")

        logic_insight = self.logic_evidence_engine.analyze(
            question,
            attempt,
            score_result,
            diagnosis_result,
        )

        return OrchestratedAttemptResult(
            node=node,
            question=question,
            attempt=attempt,
            score_result=score_result,
            diagnosis_result=diagnosis_result,
            rollback_decision=rollback_decision,
            forward_decision=forward_decision,
            next_action_hint=self._extract_next_action_hint(diagnosis_result, rollback_decision, forward_decision),
            logic_insight=logic_insight,
            rollback_consistent=rollback_consistent,
            forward_consistent=forward_consistent,
        )

    def _extract_next_action_hint(
        self,
        diagnosis_result: DiagnosisResult,
        rollback_decision: RollbackDecision,
        forward_decision: ForwardDecision,
    ) -> str:
        del rollback_decision, forward_decision
        if diagnosis_result.recommended_actions:
            return diagnosis_result.recommended_actions[0].reason
        return diagnosis_result.next_action_hint
