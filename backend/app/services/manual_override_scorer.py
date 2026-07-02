from __future__ import annotations

from app.core.enums import ScoreDimension
from app.core.schemas import (
    Attempt,
    DimensionScore,
    KnowledgeNode,
    Question,
    ScoreEvidence,
    ScorerResult,
)


class ManualOverrideScorer:
    scorer_name = "ManualOverrideScorer"

    def evaluate(self, question: Question, attempt: Attempt, node: KnowledgeNode) -> ScorerResult:
        del question, node
        overrides = attempt.metadata.get("score_overrides")
        if not overrides:
            return ScorerResult(
                scorer_name=self.scorer_name,
                is_active=False,
                notes=["Inactive: no attempt.metadata.score_overrides supplied."],
            )

        evidence_overrides = attempt.metadata.get("evidence_overrides", {})
        dimension_scores: dict[ScoreDimension, DimensionScore] = {}
        evidence_items: list[ScoreEvidence] = []
        for raw_dimension, raw_score in overrides.items():
            if raw_score is None:
                continue
            dimension = ScoreDimension(raw_dimension)
            evidence = evidence_overrides.get(
                dimension.value,
                f"imported/manual override score for {dimension.value}.",
            )
            if "manual override" not in evidence.lower() and "imported" not in evidence.lower():
                evidence = f"imported/manual override: {evidence}"
            dimension_scores[dimension] = DimensionScore(
                score=raw_score,
                evidence=evidence,
                notes="ManualOverrideScorer only imports explicit scores; it is not a real grader.",
            )
            evidence_items.append(
                ScoreEvidence(
                    source=self.scorer_name,
                    dimension=dimension,
                    score=raw_score,
                    confidence=1.0,
                    evidence=evidence,
                    matched_items=[f"score_overrides.{dimension.value}"],
                )
            )

        return ScorerResult(
            scorer_name=self.scorer_name,
            is_active=bool(dimension_scores),
            dimension_scores=dimension_scores,
            evidence=evidence_items,
            confidence=1.0,
            notes=["Imported manual/test/eval scores from attempt.metadata.score_overrides."],
        )
