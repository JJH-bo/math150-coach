from __future__ import annotations

from app.core.enums import ScoreDimension
from app.core.schemas import Attempt, DimensionScore, KnowledgeNode, Question, ScoreVector


class LegacyScenarioScorer:
    """Deterministic Phase 0 adapter for old tests only.

    This class is not part of the default CompositeScoringEngine path. It may
    read scenario flags and provide default scores for compatibility with older
    tests, but it must not be used as a real scorer.
    """

    def evaluate(self, question: Question, attempt: Attempt, node: KnowledgeNode) -> ScoreVector:
        tested_dimensions = question.tested_dimensions or node.core_dimensions
        scores: dict[ScoreDimension, DimensionScore | None] = {
            dimension: None for dimension in ScoreDimension
        }

        for dimension in tested_dimensions:
            scores[dimension] = DimensionScore(
                score=70,
                evidence=f"Legacy deterministic default evidence for {dimension.value}.",
                notes="LegacyScenarioScorer is for old tests only.",
            )

        self._apply_answer_signal(question, attempt, scores)
        self._apply_scenario_flags(attempt, scores)
        self._apply_score_overrides(attempt, scores)

        return ScoreVector(
            concept=scores[ScoreDimension.CONCEPT],
            trigger=scores[ScoreDimension.TRIGGER],
            method=scores[ScoreDimension.METHOD],
            transformation=scores[ScoreDimension.TRANSFORMATION],
            process=scores[ScoreDimension.PROCESS],
            calculation=scores[ScoreDimension.CALCULATION],
            final_answer=scores[ScoreDimension.FINAL_ANSWER],
            expression=scores[ScoreDimension.EXPRESSION],
            migration=scores[ScoreDimension.MIGRATION],
        )

    def _apply_answer_signal(
        self,
        question: Question,
        attempt: Attempt,
        scores: dict[ScoreDimension, DimensionScore | None],
    ) -> None:
        if not question.expected_answer:
            return
        normalized_expected = "".join(question.expected_answer.split())
        normalized_answer = "".join(attempt.user_answer.split())
        if normalized_expected and normalized_expected in normalized_answer:
            scores[ScoreDimension.FINAL_ANSWER] = DimensionScore(
                score=95,
                evidence="User answer contains the expected final answer.",
                notes="Final answer is only one scoring dimension.",
            )

    def _apply_scenario_flags(
        self,
        attempt: Attempt,
        scores: dict[ScoreDimension, DimensionScore | None],
    ) -> None:
        scenario = attempt.metadata.get("scenario")
        if scenario == "process_right_calculation_wrong":
            scores.update(
                {
                    ScoreDimension.CONCEPT: DimensionScore(score=85, evidence="Concept is used correctly."),
                    ScoreDimension.TRIGGER: DimensionScore(score=88, evidence="Correctly identifies the separable structure."),
                    ScoreDimension.METHOD: DimensionScore(score=90, evidence="Chooses the correct solving method."),
                    ScoreDimension.TRANSFORMATION: DimensionScore(score=88, evidence="Variables are separated correctly."),
                    ScoreDimension.PROCESS: DimensionScore(score=82, evidence="Solution process is coherent."),
                    ScoreDimension.CALCULATION: DimensionScore(score=20, evidence="Integral or simplification is wrong."),
                    ScoreDimension.FINAL_ANSWER: DimensionScore(score=0, evidence="Final result is wrong due to calculation."),
                    ScoreDimension.EXPRESSION: DimensionScore(score=75, evidence="Expression is mostly readable."),
                }
            )
        if scenario == "answer_right_trigger_unclear":
            scores.update(
                {
                    ScoreDimension.CONCEPT: DimensionScore(score=60, evidence="Concept evidence is thin."),
                    ScoreDimension.TRIGGER: DimensionScore(score=25, evidence="Cannot explain the problem trigger."),
                    ScoreDimension.METHOD: DimensionScore(score=35, evidence="Cannot justify the selected method."),
                    ScoreDimension.TRANSFORMATION: DimensionScore(score=55, evidence="Transformation evidence is incomplete."),
                    ScoreDimension.PROCESS: DimensionScore(score=60, evidence="Process is plausible but under-explained."),
                    ScoreDimension.CALCULATION: DimensionScore(score=85, evidence="Computation is mostly correct."),
                    ScoreDimension.FINAL_ANSWER: DimensionScore(score=95, evidence="Final answer is correct."),
                    ScoreDimension.EXPRESSION: DimensionScore(score=80, evidence="Final expression is acceptable."),
                }
            )
        if scenario == "trigger_failure":
            scores.update(
                {
                    ScoreDimension.CONCEPT: DimensionScore(score=55, evidence="Concept is unstable."),
                    ScoreDimension.TRIGGER: DimensionScore(score=10, evidence="Misses the key recognition pattern."),
                    ScoreDimension.METHOD: DimensionScore(score=25, evidence="Method does not fit the problem."),
                    ScoreDimension.TRANSFORMATION: DimensionScore(score=20, evidence="Cannot reach the required form."),
                    ScoreDimension.PROCESS: DimensionScore(score=35, evidence="Process breaks after method selection."),
                    ScoreDimension.CALCULATION: DimensionScore(score=50, evidence="Some local calculation is possible."),
                    ScoreDimension.FINAL_ANSWER: DimensionScore(score=0, evidence="No valid final answer."),
                    ScoreDimension.EXPRESSION: DimensionScore(score=55, evidence="Expression is incomplete."),
                }
            )
        if scenario == "transformation_failure":
            scores.update(
                {
                    ScoreDimension.CONCEPT: DimensionScore(score=70, evidence="Basic concept is present."),
                    ScoreDimension.TRIGGER: DimensionScore(score=82, evidence="Recognizes the equation family."),
                    ScoreDimension.METHOD: DimensionScore(score=75, evidence="Selects a plausible method."),
                    ScoreDimension.TRANSFORMATION: DimensionScore(score=15, evidence="Uses the wrong substitution or equivalent form."),
                    ScoreDimension.PROCESS: DimensionScore(score=35, evidence="Process fails after the transformation."),
                    ScoreDimension.CALCULATION: DimensionScore(score=45, evidence="Calculation is affected by the wrong form."),
                    ScoreDimension.FINAL_ANSWER: DimensionScore(score=0, evidence="Final answer is invalid."),
                    ScoreDimension.EXPRESSION: DimensionScore(score=60, evidence="Expression is partially clear."),
                }
            )

    def _apply_score_overrides(
        self,
        attempt: Attempt,
        scores: dict[ScoreDimension, DimensionScore | None],
    ) -> None:
        overrides = attempt.metadata.get("score_overrides", {})
        evidence_overrides = attempt.metadata.get("evidence_overrides", {})
        for raw_dimension, raw_score in overrides.items():
            dimension = ScoreDimension(raw_dimension)
            scores[dimension] = DimensionScore(
                score=raw_score,
                evidence=evidence_overrides.get(dimension.value, "Score supplied by deterministic override."),
                notes="Override is intended for tests, evals, or imported grader output.",
            )
