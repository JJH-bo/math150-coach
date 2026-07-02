from __future__ import annotations

import re
from collections import defaultdict

from app.core.enums import ScoreDimension
from app.core.schemas import (
    Attempt,
    DimensionScore,
    KeyPoint,
    KnowledgeNode,
    Question,
    RubricItem,
    ScoreEvidence,
    ScorerResult,
)


class RubricScorer:
    scorer_name = "RubricScorer"

    def evaluate(self, question: Question, attempt: Attempt, node: KnowledgeNode) -> ScorerResult:
        del node
        items = self._collect_items(question)
        if not items:
            return ScorerResult(
                scorer_name=self.scorer_name,
                is_active=False,
                notes=["Inactive: question has no rubric, key points, or expected patterns."],
            )

        answer_text = self._normalize_text(attempt.user_answer)
        full_answer_text = self._answer_corpus(attempt)
        normalized_full_answer = self._normalize_text(full_answer_text)
        hit_weight_by_dimension: dict[ScoreDimension, float] = defaultdict(float)
        total_weight_by_dimension: dict[ScoreDimension, float] = defaultdict(float)
        matched_by_dimension: dict[ScoreDimension, list[str]] = defaultdict(list)
        partial_by_dimension: dict[ScoreDimension, list[str]] = defaultdict(list)
        required_missed_by_dimension: dict[ScoreDimension, list[str]] = defaultdict(list)
        optional_missed_by_dimension: dict[ScoreDimension, list[str]] = defaultdict(list)
        evidence_items: list[ScoreEvidence] = []

        for item in items:
            match = self._item_match(item, normalized_full_answer or answer_text, full_answer_text or attempt.user_answer)
            for dimension in item.target_dimensions:
                total_weight_by_dimension[dimension] += item.weight
                if match.score_ratio > 0:
                    hit_weight_by_dimension[dimension] += item.weight * match.score_ratio
                if match.is_full:
                    matched_by_dimension[dimension].append(item.id)
                elif match.is_partial:
                    partial_by_dimension[dimension].append(item.id)
                elif item.required:
                    required_missed_by_dimension[dimension].append(item.id)
                else:
                    optional_missed_by_dimension[dimension].append(item.id)
                evidence_items.append(
                    ScoreEvidence(
                        source=self.scorer_name,
                        dimension=dimension,
                        score=match.score,
                        confidence=0.85 if match.is_full else 0.62 if match.is_partial else 0.85,
                        evidence=self._item_evidence(item, match),
                        matched_items=[item.id] if match.is_full else [],
                        missed_items=[] if match.score_ratio > 0 else [item.id],
                        required_missed=[item.id] if (not match.is_full and not match.is_partial and item.required) else [],
                        optional_missed=[item.id] if (not match.is_full and not match.is_partial and not item.required) else [],
                    )
                )

        dimension_scores: dict[ScoreDimension, DimensionScore] = {}
        for dimension, total_weight in total_weight_by_dimension.items():
            if total_weight <= 0:
                continue
            score = 100 * hit_weight_by_dimension[dimension] / total_weight
            matched = matched_by_dimension[dimension]
            partial = partial_by_dimension[dimension]
            required_missed = required_missed_by_dimension[dimension]
            optional_missed = optional_missed_by_dimension[dimension]
            missed = required_missed + optional_missed
            evidence = (
                f"RubricScorer matched_items={matched}; partial_matched={partial}; missed_items={missed}; required_missed={required_missed}; "
                f"optional_missed={optional_missed}; score is weighted by rubric item weights. "
                "When required_keywords and expected_patterns both exist, all required keywords and all patterns must match."
            )
            dimension_scores[dimension] = DimensionScore(
                score=score,
                evidence=evidence,
                notes="Rubric-derived dimension score.",
            )

        return ScorerResult(
            scorer_name=self.scorer_name,
            is_active=bool(dimension_scores),
            dimension_scores=dimension_scores,
            evidence=evidence_items,
            confidence=0.85,
            notes=["Scored from question rubric/key points/patterns, not expected_scores."],
        )

    def _collect_items(self, question: Question) -> list[RubricItem]:
        items: list[RubricItem] = []
        if question.rubric:
            items.extend(question.rubric.items)
            items.extend(self._key_point_to_item(key_point) for key_point in question.rubric.key_points)
        items.extend(self._key_point_to_item(key_point) for key_point in question.expected_key_points)
        if question.expected_patterns:
            target_dimensions = question.tested_dimensions or [ScoreDimension.PROCESS]
            items.append(
                RubricItem(
                    id="question_expected_patterns",
                    description="Question-level expected patterns.",
                    target_dimensions=target_dimensions,
                    expected_patterns=question.expected_patterns,
                    weight=1,
                    evidence_on_hit="Matched question-level expected patterns.",
                    evidence_on_miss="Missed question-level expected patterns.",
                )
            )
        return items

    def _key_point_to_item(self, key_point: KeyPoint) -> RubricItem:
        keywords = key_point.required_keywords or [key_point.text]
        return RubricItem(
            id=key_point.id,
            description=key_point.text,
            target_dimensions=key_point.target_dimensions,
            required_keywords=keywords,
            weight=key_point.weight,
            required=key_point.required,
            evidence_on_hit=key_point.evidence_on_hit or f"Key point hit: {key_point.text}",
            evidence_on_miss=key_point.evidence_on_miss or f"Key point missed: {key_point.text}",
        )

    def _item_hit(self, item: RubricItem, normalized_answer: str, original_answer: str) -> bool:
        return self._item_match(item, normalized_answer, original_answer).is_full

    def _item_match(self, item: RubricItem, normalized_answer: str, original_answer: str) -> "_RubricItemMatch":
        keyword_results = [
            self._normalize_text(keyword) in normalized_answer for keyword in item.required_keywords
        ]
        pattern_results = [
            bool(re.search(pattern, original_answer, flags=re.IGNORECASE)) for pattern in item.expected_patterns
        ]
        checks = keyword_results + pattern_results
        if not checks:
            return _RubricItemMatch(score=0, score_ratio=0, is_full=False, is_partial=False)
        if all(checks):
            return _RubricItemMatch(score=100, score_ratio=1, is_full=True, is_partial=False)
        if not item.partial_credit:
            return _RubricItemMatch(score=0, score_ratio=0, is_full=False, is_partial=False)
        matched_count = sum(1 for check in checks if check)
        if matched_count == 0:
            return _RubricItemMatch(score=0, score_ratio=0, is_full=False, is_partial=False)
        raw_partial_score = max(35, item.partial_score * matched_count / len(checks))
        score = min(item.partial_score, raw_partial_score)
        return _RubricItemMatch(score=score, score_ratio=score / 100, is_full=False, is_partial=True)

    def _item_evidence(self, item: RubricItem, match: "_RubricItemMatch") -> str:
        if match.is_full:
            return item.evidence_on_hit
        if match.is_partial:
            return (
                f"Partial rubric evidence for {item.id}: learner supplied some required meaning, "
                f"but not the full expected evidence. {item.evidence_on_miss}"
            )
        return item.evidence_on_miss

    def _answer_corpus(self, attempt: Attempt) -> str:
        parts = [attempt.user_answer, *attempt.response_steps]
        if attempt.self_explanation:
            parts.append(attempt.self_explanation)
        return "\n".join(part for part in parts if part)

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", "", text.lower())


class _RubricItemMatch:
    def __init__(self, *, score: float, score_ratio: float, is_full: bool, is_partial: bool) -> None:
        self.score = score
        self.score_ratio = score_ratio
        self.is_full = is_full
        self.is_partial = is_partial
