from __future__ import annotations

from collections import defaultdict

from app.core.enums import ScoreDimension
from app.core.schemas import Attempt, DimensionScore, KnowledgeNode, Question, ScoreEvidence, ScorerResult


class RuleScorer:
    scorer_name = "RuleScorer"
    max_confidence = 0.55

    KEYWORD_RULES = (
        ("积分因子", [ScoreDimension.TRIGGER, ScoreDimension.METHOD], "Mentions integrating factor."),
        ("integrating factor", [ScoreDimension.TRIGGER, ScoreDimension.METHOD], "Mentions integrating factor."),
        ("一阶线性", [ScoreDimension.TRIGGER, ScoreDimension.METHOD], "Mentions first-order linear equation."),
        ("first-order linear", [ScoreDimension.TRIGGER, ScoreDimension.METHOD], "Mentions first-order linear equation."),
        ("可分离", [ScoreDimension.TRIGGER, ScoreDimension.METHOD], "Mentions separable equation."),
        ("分离变量", [ScoreDimension.TRIGGER, ScoreDimension.METHOD], "Mentions separation of variables."),
        ("separable", [ScoreDimension.TRIGGER, ScoreDimension.METHOD], "Mentions separable equation."),
        ("y=vx", [ScoreDimension.TRIGGER, ScoreDimension.TRANSFORMATION], "Mentions y=vx substitution."),
        ("y = vx", [ScoreDimension.TRIGGER, ScoreDimension.TRANSFORMATION], "Mentions y=vx substitution."),
        ("p=y'", [ScoreDimension.TRIGGER, ScoreDimension.TRANSFORMATION], "Mentions p=y' reduction."),
        ("p = y'", [ScoreDimension.TRIGGER, ScoreDimension.TRANSFORMATION], "Mentions p=y' reduction."),
        ("共振", [ScoreDimension.TRIGGER, ScoreDimension.TRANSFORMATION], "Mentions resonance."),
        ("resonance", [ScoreDimension.TRIGGER, ScoreDimension.TRANSFORMATION], "Mentions resonance."),
    )

    def evaluate(self, question: Question, attempt: Attempt, node: KnowledgeNode) -> ScorerResult:
        allowed_dimensions = set(question.tested_dimensions or node.core_dimensions or list(ScoreDimension))
        answer = "\n".join(
            part
            for part in [attempt.user_answer, *attempt.response_steps, attempt.self_explanation or ""]
            if part
        ).lower()
        hits_by_dimension: dict[ScoreDimension, list[str]] = defaultdict(list)
        evidence_items: list[ScoreEvidence] = []

        for keyword, dimensions, evidence in self.KEYWORD_RULES:
            if keyword.lower() not in answer:
                continue
            for dimension in dimensions:
                if dimension not in allowed_dimensions:
                    continue
                hits_by_dimension[dimension].append(keyword)
                evidence_items.append(
                    ScoreEvidence(
                        source=self.scorer_name,
                        dimension=dimension,
                        score=65,
                        confidence=self.max_confidence,
                        evidence=evidence,
                        matched_items=[keyword],
                    )
                )

        dimension_scores = {
            dimension: DimensionScore(
                score=65,
                evidence=f"RuleScorer weak signal from keywords={keywords}; cannot independently prove mastery.",
                notes="Weak keyword/structure signal only.",
            )
            for dimension, keywords in hits_by_dimension.items()
        }

        return ScorerResult(
            scorer_name=self.scorer_name,
            is_active=bool(dimension_scores),
            dimension_scores=dimension_scores,
            evidence=evidence_items,
            confidence=self.max_confidence if dimension_scores else 0,
            notes=[
                "RuleScorer is capped at confidence 0.55 and cannot independently cause full pass.",
                "RuleScorer only contributes to dimensions explicitly tested by the question or node.",
            ],
        )
