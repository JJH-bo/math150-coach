from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from app.core.enums import ScoreDimension
from app.core.schemas import (
    Attempt,
    CompositeScoreResult,
    DimensionScore,
    KnowledgeNode,
    Question,
    ScoreVector,
    ScorerResult,
)
from app.services.manual_override_scorer import ManualOverrideScorer
from app.services.math_validator_scorer import MathValidatorScorer
from app.services.rubric_scorer import RubricScorer
from app.services.rule_scorer import RuleScorer


class DetailedScorer(Protocol):
    scorer_name: str

    def evaluate(self, question: Question, attempt: Attempt, node: KnowledgeNode) -> ScorerResult:
        ...


class LLMScorerStub:
    scorer_name = "LLMScorerStub"

    def evaluate(self, question: Question, attempt: Attempt, node: KnowledgeNode) -> ScorerResult:
        del question, attempt, node
        return ScorerResult(
            scorer_name=self.scorer_name,
            is_active=False,
            notes=["Inactive Phase 1 stub. Future input: question, attempt, node, rubric, and known solution hints."],
        )


class CompositeScoringEngine:
    def __init__(self, scorers: list[DetailedScorer] | None = None) -> None:
        self.scorers = scorers or [
            ManualOverrideScorer(),
            RubricScorer(),
            MathValidatorScorer(),
            RuleScorer(),
            LLMScorerStub(),
        ]

    def evaluate(self, question: Question, attempt: Attempt, node: KnowledgeNode) -> ScoreVector:
        return self.evaluate_detailed(question, attempt, node).score_vector

    def evaluate_detailed(self, question: Question, attempt: Attempt, node: KnowledgeNode) -> CompositeScoreResult:
        scorer_results = [scorer.evaluate(question, attempt, node) for scorer in self.scorers]
        dimension_scores: dict[ScoreDimension, DimensionScore | None] = {
            dimension: None for dimension in ScoreDimension
        }
        merge_notes: list[str] = []

        active_scorers = [result.scorer_name for result in scorer_results if result.is_active]
        merge_notes.append(f"Active scorers: {active_scorers or ['none']}.")

        contributions: dict[ScoreDimension, list[tuple[ScorerResult, DimensionScore]]] = defaultdict(list)
        for result in scorer_results:
            if not result.is_active:
                continue
            for dimension, score in result.dimension_scores.items():
                if score.score is None:
                    continue
                contributions[dimension].append((result, score))

        for dimension, dimension_contributions in contributions.items():
            manual = [
                score
                for result, score in dimension_contributions
                if result.scorer_name == "ManualOverrideScorer"
            ]
            if manual:
                selected = manual[-1]
                dimension_scores[dimension] = DimensionScore(
                    score=selected.score,
                    evidence=f"{selected.evidence} [merged from ManualOverrideScorer]",
                    notes="Manual override has highest priority for this dimension.",
                )
                merge_notes.append(f"{dimension.value}: manual override selected.")
                continue

            weighted_total = 0.0
            confidence_total = 0.0
            evidence_parts: list[str] = []
            source_names: list[str] = []
            for result, score in dimension_contributions:
                confidence = max(result.confidence, 0.01)
                weighted_total += (score.score or 0) * confidence
                confidence_total += confidence
                source_names.append(result.scorer_name)
                if score.evidence:
                    evidence_parts.append(f"{result.scorer_name}: {score.evidence}")

            if confidence_total == 0:
                continue
            merged_score = weighted_total / confidence_total
            dimension_scores[dimension] = DimensionScore(
                score=merged_score,
                evidence=" | ".join(evidence_parts) or f"Merged score from {source_names}.",
                notes=f"Merged by confidence from {source_names}.",
            )
            merge_notes.append(f"{dimension.value}: confidence merge from {source_names}.")

        return CompositeScoreResult(
            score_vector=ScoreVector(
                concept=dimension_scores[ScoreDimension.CONCEPT],
                trigger=dimension_scores[ScoreDimension.TRIGGER],
                method=dimension_scores[ScoreDimension.METHOD],
                transformation=dimension_scores[ScoreDimension.TRANSFORMATION],
                process=dimension_scores[ScoreDimension.PROCESS],
                calculation=dimension_scores[ScoreDimension.CALCULATION],
                final_answer=dimension_scores[ScoreDimension.FINAL_ANSWER],
                expression=dimension_scores[ScoreDimension.EXPRESSION],
                migration=dimension_scores[ScoreDimension.MIGRATION],
            ),
            scorer_results=scorer_results,
            merge_notes=merge_notes,
        )
