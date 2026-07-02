from __future__ import annotations

import re

from app.core.enums import ScoreDimension
from app.core.schemas import Attempt, DimensionScore, KnowledgeNode, Question, ScoreEvidence, ScorerResult


class MathValidatorScorer:
    scorer_name = "MathValidatorScorer"

    def evaluate(self, question: Question, attempt: Attempt, node: KnowledgeNode) -> ScorerResult:
        del node
        dimension_scores: dict[ScoreDimension, DimensionScore] = {}
        evidence_items: list[ScoreEvidence] = []
        answer = attempt.user_answer
        normalized_answer = self._normalize_expr(answer)

        expected_candidates = self._expected_candidates(question)
        if expected_candidates and any(candidate in normalized_answer for candidate in expected_candidates):
            evidence = "MathValidatorScorer matched normalized expected answer string or alias."
            dimension_scores[ScoreDimension.FINAL_ANSWER] = DimensionScore(score=95, evidence=evidence)
            dimension_scores[ScoreDimension.CALCULATION] = DimensionScore(
                score=85,
                evidence="MathValidatorScorer found final answer match; calculation receives supportive evidence only.",
            )
            evidence_items.extend(
                [
                    ScoreEvidence(
                        source=self.scorer_name,
                        dimension=ScoreDimension.FINAL_ANSWER,
                        score=95,
                        confidence=0.9,
                        evidence=evidence,
                        matched_items=["expected_answer"],
                    ),
                    ScoreEvidence(
                        source=self.scorer_name,
                        dimension=ScoreDimension.CALCULATION,
                        score=85,
                        confidence=0.75,
                        evidence="Final answer match supports calculation but does not grade reasoning.",
                        matched_items=["expected_answer"],
                    ),
                ]
            )

        missing_constant = self._requires_constant(question) and not self._has_constant(answer)
        if missing_constant:
            evidence = "MathValidatorScorer detected likely missing arbitrary constant C in a general-solution question."
            dimension_scores[ScoreDimension.FINAL_ANSWER] = DimensionScore(score=35, evidence=evidence)
            dimension_scores[ScoreDimension.CALCULATION] = DimensionScore(
                score=60,
                evidence="MathValidatorScorer found the solution path plausible but incomplete because C is missing.",
            )
            evidence_items.append(
                ScoreEvidence(
                    source=self.scorer_name,
                    dimension=ScoreDimension.FINAL_ANSWER,
                    score=35,
                    confidence=0.85,
                    evidence=evidence,
                    missed_items=["constant_C"],
                )
            )
            evidence_items.append(
                ScoreEvidence(
                    source=self.scorer_name,
                    dimension=ScoreDimension.CALCULATION,
                    score=60,
                    confidence=0.75,
                    evidence="Missing C limits calculation completeness.",
                    missed_items=["constant_C"],
                )
            )

        missing_initial_value = (
            self._requires_initial_value(question)
            and self._has_constant(answer)
            and not self._has_resolved_initial_constant(answer)
            and not self._has_expected_special_solution(question, normalized_answer)
        )
        if missing_initial_value:
            evidence = "MathValidatorScorer detected an initial-value question that stopped at a general solution."
            dimension_scores[ScoreDimension.FINAL_ANSWER] = DimensionScore(score=40, evidence=evidence)
            evidence_items.append(
                ScoreEvidence(
                    source=self.scorer_name,
                    dimension=ScoreDimension.FINAL_ANSWER,
                    score=40,
                    confidence=0.85,
                    evidence=evidence,
                    missed_items=["initial_value_resolution"],
                )
            )

        return ScorerResult(
            scorer_name=self.scorer_name,
            is_active=bool(dimension_scores),
            dimension_scores=dimension_scores,
            evidence=evidence_items,
            confidence=0.9 if dimension_scores else 0,
            notes=["Phase 1 lightweight string validator; no symbolic ODE verification."],
        )

    def _expected_candidates(self, question: Question) -> list[str]:
        candidates: list[str] = []
        if question.expected_answer:
            candidates.append(self._normalize_expr(question.expected_answer))
        for alias in question.metadata.get("expected_answer_aliases", []):
            candidates.append(self._normalize_expr(alias))
        return [candidate for candidate in candidates if candidate]

    def _requires_constant(self, question: Question) -> bool:
        if question.metadata.get("requires_constant"):
            return True
        prompt = question.prompt.lower()
        return "通解" in prompt or "general solution" in prompt

    def _requires_initial_value(self, question: Question) -> bool:
        if question.metadata.get("requires_initial_condition"):
            return True
        return bool(re.search(r"y\s*\([^)]*\)\s*=", question.prompt)) or "初值" in question.prompt.lower()

    def _has_constant(self, answer: str) -> bool:
        return bool(
            re.search(
                r"(?i)(\bc\b|c_?\d+\b|c\s*=|任意常数|常数项|arbitrary\s+constant)",
                answer,
            )
        )

    def _has_resolved_initial_constant(self, answer: str) -> bool:
        return bool(re.search(r"(?i)c_?\d*\s*=\s*[-+]?\d+(?:\.\d+)?", answer))

    def _has_expected_special_solution(self, question: Question, normalized_answer: str) -> bool:
        expected_candidates = self._expected_candidates(question)
        return bool(expected_candidates) and any(candidate in normalized_answer for candidate in expected_candidates)

    def _normalize_expr(self, value: str) -> str:
        normalized = value.lower()
        normalized = normalized.replace(" ", "")
        normalized = normalized.replace("\\", "")
        normalized = normalized.replace("{", "").replace("}", "")
        normalized = normalized.replace("c_1", "c").replace("c1", "c")
        normalized = normalized.replace("·", "")
        normalized = normalized.replace("*", "")
        return normalized
