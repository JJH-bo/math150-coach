# Phase 0.5 Review Dump

This file contains the complete contents requested for human review.

## backend/app/core/schemas.py

```python
from __future__ import annotations

from typing import Any, Mapping, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.enums import (
    ErrorType,
    ForwardLevel,
    NodeStatus,
    NodeType,
    PassState,
    QuestionType,
    RollbackLevel,
    ScoreDimension,
)


class DimensionScore(BaseModel):
    score: Optional[float] = Field(default=None, ge=0, le=100)
    evidence: Optional[str] = None
    notes: Optional[str] = None


class ScoreVector(BaseModel):
    concept: Optional[DimensionScore] = None
    trigger: Optional[DimensionScore] = None
    method: Optional[DimensionScore] = None
    transformation: Optional[DimensionScore] = None
    process: Optional[DimensionScore] = None
    calculation: Optional[DimensionScore] = None
    final_answer: Optional[DimensionScore] = None
    expression: Optional[DimensionScore] = None
    migration: Optional[DimensionScore] = None

    def as_dimension_map(self) -> dict[ScoreDimension, Optional[DimensionScore]]:
        return {
            ScoreDimension.CONCEPT: self.concept,
            ScoreDimension.TRIGGER: self.trigger,
            ScoreDimension.METHOD: self.method,
            ScoreDimension.TRANSFORMATION: self.transformation,
            ScoreDimension.PROCESS: self.process,
            ScoreDimension.CALCULATION: self.calculation,
            ScoreDimension.FINAL_ANSWER: self.final_answer,
            ScoreDimension.EXPRESSION: self.expression,
            ScoreDimension.MIGRATION: self.migration,
        }

    def get_dimension(self, dimension: ScoreDimension | str) -> Optional[DimensionScore]:
        dim = ScoreDimension(dimension)
        return self.as_dimension_map()[dim]

    def overall_score(self, weights: Optional[Mapping[ScoreDimension | str, float]] = None) -> Optional[float]:
        """Average available dimensions. This helper must not decide pass state alone."""

        normalized_weights: dict[str, float] = {}
        if weights:
            normalized_weights = {str(key.value if isinstance(key, ScoreDimension) else key): value for key, value in weights.items()}

        weighted_total = 0.0
        weight_total = 0.0
        for dimension, dimension_score in self.as_dimension_map().items():
            if dimension_score is None or dimension_score.score is None:
                continue
            weight = normalized_weights.get(dimension.value, 1.0)
            if weight <= 0:
                continue
            weighted_total += dimension_score.score * weight
            weight_total += weight

        if weight_total == 0:
            return None
        return weighted_total / weight_total


class ErrorItem(BaseModel):
    error_type: ErrorType
    weight: float = Field(ge=0, le=1)
    related_dimensions: list[ScoreDimension] = Field(default_factory=list)
    evidence: str = ""
    is_primary: bool = False
    suggested_rollback_level: RollbackLevel = RollbackLevel.R1_INTERNAL

    @field_validator("related_dimensions")
    @classmethod
    def related_dimensions_must_not_be_empty(
        cls,
        value: list[ScoreDimension],
    ) -> list[ScoreDimension]:
        if not value:
            raise ValueError("Each error item must include at least one related dimension.")
        return value

    @field_validator("evidence")
    @classmethod
    def evidence_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Each error item must include evidence.")
        return value

    @model_validator(mode="after")
    def classify_primary_from_weight(self) -> "ErrorItem":
        self.is_primary = self.weight >= 0.7
        return self


class ErrorVector(BaseModel):
    errors: list[ErrorItem] = Field(default_factory=list)

    def primary_errors(self) -> list[ErrorItem]:
        return [error for error in self.errors if error.is_primary]

    def secondary_errors(self) -> list[ErrorItem]:
        return [error for error in self.errors if 0.4 <= error.weight < 0.7]

    def has_error_type(self, error_type: ErrorType | str) -> bool:
        expected = ErrorType(error_type)
        return any(error.error_type == expected for error in self.errors)

    def sorted_by_weight(self) -> list[ErrorItem]:
        return sorted(self.errors, key=lambda error: error.weight, reverse=True)


class RollbackPolicyEntry(BaseModel):
    level: RollbackLevel
    target_nodes: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class PassCriteria(BaseModel):
    min_overall: float = 80
    min_required_dimensions: dict[ScoreDimension, float] = Field(default_factory=dict)
    max_primary_errors: int = 0
    allow_false_pass: bool = False


class VariantPolicy(BaseModel):
    template_families: list[str] = Field(default_factory=list)
    parameter_focus: list[str] = Field(default_factory=list)
    validation_required: bool = True


class KnowledgeNode(BaseModel):
    id: str
    name: str
    type: NodeType
    status: NodeStatus
    prerequisites: list[str] = Field(default_factory=list)
    successors: list[str] = Field(default_factory=list)
    core_dimensions: list[ScoreDimension] = Field(default_factory=list)
    common_errors: list[ErrorType] = Field(default_factory=list)
    description: str
    trigger_patterns: list[str] = Field(default_factory=list)
    scoring_weights: dict[ScoreDimension, float] = Field(default_factory=dict)
    rollback_policy: dict[str, RollbackPolicyEntry] = Field(default_factory=dict)
    pass_criteria: PassCriteria = Field(default_factory=PassCriteria)
    variant_policy: VariantPolicy = Field(default_factory=VariantPolicy)


class Question(BaseModel):
    id: str
    node_id: str
    question_type: QuestionType
    prompt: str
    expected_answer: Optional[str] = None
    tested_dimensions: list[ScoreDimension] = Field(default_factory=list)
    solution_outline: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Attempt(BaseModel):
    id: str
    question_id: str
    user_answer: str
    response_steps: list[str] = Field(default_factory=list)
    self_explanation: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReviewTask(BaseModel):
    node_id: str
    reason: str
    focus_dimensions: list[ScoreDimension] = Field(default_factory=list)
    error_types: list[ErrorType] = Field(default_factory=list)
    due_after_attempts: int = 1
    priority: int = Field(default=2, ge=1, le=5)


class DiagnosisResult(BaseModel):
    score_vector: ScoreVector
    error_vector: ErrorVector
    pass_state: PassState
    rollback_nodes: list[str] = Field(default_factory=list)
    forward_nodes: list[str] = Field(default_factory=list)
    rollback_level: RollbackLevel = RollbackLevel.R1_INTERNAL
    forward_level: ForwardLevel = ForwardLevel.P0_NONE
    explanation: str
    next_action_hint: str


class NodeAction(BaseModel):
    rollback_nodes: list[str] = Field(default_factory=list)
    forward_nodes: list[str] = Field(default_factory=list)
    review_tasks: list[ReviewTask] = Field(default_factory=list)
    node_status_updates: dict[str, NodeStatus] = Field(default_factory=dict)
    mastery_updates: dict[str, Any] = Field(default_factory=dict)
    explanation: str
```

## backend/app/services/scoring_engine.py

```python
from __future__ import annotations

from app.core.enums import ScoreDimension
from app.core.schemas import Attempt, DimensionScore, KnowledgeNode, Question, ScoreVector


class ScoringEngine:
    """Rule-shaped scoring facade.

    Phase 0 intentionally avoids real LLM grading. The engine returns structured
    score evidence and supports deterministic overrides for tests and evals.
    """

    def evaluate(self, question: Question, attempt: Attempt, node: KnowledgeNode) -> ScoreVector:
        tested_dimensions = question.tested_dimensions or node.core_dimensions
        scores: dict[ScoreDimension, DimensionScore | None] = {
            dimension: None for dimension in ScoreDimension
        }

        for dimension in tested_dimensions:
            scores[dimension] = DimensionScore(
                score=70,
                evidence=f"Default Phase 0 evidence for {dimension.value}.",
                notes="Replace with rule, human, or LLM grader evidence in later phases.",
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
```

## backend/app/services/diagnosis_engine.py

```python
from __future__ import annotations

from app.core.config import DEFAULT_ENGINE_CONFIG, EngineConfig
from app.core.enums import ErrorType, ForwardLevel, PassState, RollbackLevel, ScoreDimension
from app.core.schemas import (
    Attempt,
    DiagnosisResult,
    ErrorItem,
    ErrorVector,
    KnowledgeNode,
    Question,
    ScoreVector,
)


class DiagnosisEngine:
    def __init__(self, config: EngineConfig = DEFAULT_ENGINE_CONFIG) -> None:
        self.config = config

    def diagnose(
        self,
        score_vector: ScoreVector,
        question: Question,
        attempt: Attempt,
        node: KnowledgeNode,
    ) -> ErrorVector:
        del question, attempt
        errors: list[ErrorItem] = []

        for dimension, error_type in self.config.dimension_error_map.items():
            dimension_score = score_vector.get_dimension(dimension)
            if dimension_score is None or dimension_score.score is None:
                continue
            if dimension_score.score >= 70:
                continue
            errors.append(
                self._build_error(
                    error_type=error_type,
                    dimension=dimension,
                    score=dimension_score.score,
                    evidence=dimension_score.evidence or f"Low {dimension.value} score.",
                )
            )

        errors = self._merge_duplicate_errors(errors)
        errors = self._promote_false_pass_errors(score_vector, errors)
        errors = self._align_with_node_policy(errors, node)
        return ErrorVector(errors=sorted(errors, key=lambda error: error.weight, reverse=True))

    def classify_pass_state(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
        node: KnowledgeNode,
    ) -> PassState:
        if self._has_false_pass_signal(score_vector):
            return PassState.FALSE_PASS

        primary_errors = error_vector.primary_errors()
        if len(primary_errors) > node.pass_criteria.max_primary_errors:
            return PassState.FAIL

        overall = score_vector.overall_score(node.scoring_weights)
        if overall is None:
            return PassState.FAIL

        required_dimensions_met = self._required_dimensions_met(score_vector, node)
        if overall >= node.pass_criteria.min_overall and required_dimensions_met:
            return PassState.PASS

        if overall >= 70 and not primary_errors:
            return PassState.PARTIAL_PASS

        return PassState.FAIL

    def build_result(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
        node: KnowledgeNode,
        rollback_nodes: list[str],
        forward_nodes: list[str],
        rollback_level: RollbackLevel,
        forward_level: ForwardLevel,
    ) -> DiagnosisResult:
        pass_state = self.classify_pass_state(score_vector, error_vector, node)
        explanation = self.explain(score_vector, error_vector, pass_state, rollback_nodes, forward_nodes)
        next_action_hint = self.next_action_hint(pass_state, rollback_nodes, forward_nodes)
        return DiagnosisResult(
            score_vector=score_vector,
            error_vector=error_vector,
            pass_state=pass_state,
            rollback_nodes=rollback_nodes,
            forward_nodes=forward_nodes,
            rollback_level=rollback_level,
            forward_level=forward_level,
            explanation=explanation,
            next_action_hint=next_action_hint,
        )

    def explain(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
        pass_state: PassState,
        rollback_nodes: list[str],
        forward_nodes: list[str],
    ) -> str:
        overall = score_vector.overall_score()
        overall_text = f"{overall:.1f}" if overall is not None else "none"
        primary = [error.error_type.value for error in error_vector.primary_errors()]
        return (
            f"overall_score={overall_text}; "
            f"pass_state={pass_state.value}; "
            f"primary_errors={primary}; "
            f"rollback_nodes={rollback_nodes}; "
            f"forward_nodes={forward_nodes}."
        )

    def next_action_hint(
        self,
        pass_state: PassState,
        rollback_nodes: list[str],
        forward_nodes: list[str],
    ) -> str:
        if pass_state in {PassState.FAIL, PassState.FALSE_PASS} and rollback_nodes:
            return f"Review targeted rollback nodes first: {', '.join(rollback_nodes)}."
        if pass_state == PassState.PARTIAL_PASS:
            return "Do a short review task before normal progression."
        if forward_nodes:
            return f"Proceed to next node candidate: {forward_nodes[0]}."
        return "Stay on the current node and collect more evidence."

    def _build_error(
        self,
        error_type: ErrorType,
        dimension: ScoreDimension,
        score: float,
        evidence: str,
    ) -> ErrorItem:
        weight = self._weight_from_score(score)
        related_dimensions = [dimension]
        if error_type == ErrorType.CALCULATION_ERROR:
            related_dimensions.append(ScoreDimension.FINAL_ANSWER)
        return ErrorItem(
            error_type=error_type,
            weight=weight,
            related_dimensions=related_dimensions,
            evidence=evidence,
            is_primary=weight >= self.config.primary_error_threshold,
            suggested_rollback_level=self.config.default_rollback_level_by_error[error_type],
        )

    def _weight_from_score(self, score: float) -> float:
        if score < 30:
            return 0.9
        if score < 50:
            return 0.75
        if score < 70:
            return 0.5
        return 0.0

    def _merge_duplicate_errors(self, errors: list[ErrorItem]) -> list[ErrorItem]:
        merged: dict[ErrorType, ErrorItem] = {}
        for error in errors:
            existing = merged.get(error.error_type)
            if existing is None or error.weight > existing.weight:
                merged[error.error_type] = error
            elif existing:
                existing.related_dimensions = list({*existing.related_dimensions, *error.related_dimensions})
        return list(merged.values())

    def _promote_false_pass_errors(self, score_vector: ScoreVector, errors: list[ErrorItem]) -> list[ErrorItem]:
        if not self._has_false_pass_signal(score_vector):
            return errors

        existing_types = {error.error_type for error in errors}
        for dimension, error_type in (
            (ScoreDimension.TRIGGER, ErrorType.TRIGGER_FAILURE),
            (ScoreDimension.METHOD, ErrorType.METHOD_ERROR),
        ):
            dimension_score = score_vector.get_dimension(dimension)
            if (
                dimension_score is not None
                and dimension_score.score is not None
                and dimension_score.score < self.config.false_pass_dimension_max
                and error_type not in existing_types
            ):
                errors.append(
                    ErrorItem(
                        error_type=error_type,
                        weight=0.8 if dimension == ScoreDimension.TRIGGER else 0.7,
                        related_dimensions=[dimension],
                        evidence=dimension_score.evidence or "False-pass signal: final answer is high but reasoning evidence is weak.",
                        is_primary=True,
                        suggested_rollback_level=self.config.default_rollback_level_by_error[error_type],
                    )
                )
        return errors

    def _align_with_node_policy(self, errors: list[ErrorItem], node: KnowledgeNode) -> list[ErrorItem]:
        for error in errors:
            policy = node.rollback_policy.get(error.error_type.value)
            if policy:
                error.suggested_rollback_level = policy.level
        return errors

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
```

## backend/app/services/rollback_engine.py

```python
from __future__ import annotations

from app.core.config import DEFAULT_ENGINE_CONFIG, EngineConfig
from app.core.enums import ErrorType, RollbackLevel
from app.core.schemas import ErrorItem, ErrorVector, KnowledgeNode


class RollbackEngine:
    R4_ALLOWED_SINGLE_ERROR_TYPES = {
        ErrorType.KNOWLEDGE_CONFUSION,
        ErrorType.SYNTHESIS_FAILURE,
    }

    def __init__(self, config: EngineConfig = DEFAULT_ENGINE_CONFIG) -> None:
        self.config = config

    def select_rollback_nodes(self, error_vector: ErrorVector, node: KnowledgeNode) -> list[str]:
        candidate_errors = error_vector.primary_errors() or error_vector.secondary_errors()
        if not candidate_errors:
            return []

        selected: list[str] = []
        for error in sorted(candidate_errors, key=lambda item: item.weight, reverse=True):
            selected.extend(self._targets_for_error(error, node))
            selected = self._dedupe(selected)
            if len(selected) >= self.config.max_rollback_nodes:
                break

        selected = selected[: self.config.max_rollback_nodes]
        return self._avoid_all_prerequisites_for_local_errors(selected, candidate_errors, node)

    def determine_rollback_level(self, error_vector: ErrorVector) -> RollbackLevel:
        candidate_errors = error_vector.primary_errors() or error_vector.secondary_errors()
        if not candidate_errors:
            return RollbackLevel.R1_INTERNAL
        top_error = sorted(candidate_errors, key=lambda item: item.weight, reverse=True)[0]
        return self._effective_rollback_level(top_error)

    def _targets_for_error(self, error: ErrorItem, node: KnowledgeNode) -> list[str]:
        if error.error_type == ErrorType.CALCULATION_ERROR:
            return [node.id]

        effective_level = self._effective_rollback_level(error)
        policy = node.rollback_policy.get(error.error_type.value)
        if policy and policy.target_nodes:
            targets = [self._resolve_target(target, node) for target in policy.target_nodes if self._resolve_target(target, node)]
            if effective_level != RollbackLevel.R4_CHAPTER_FRAMEWORK and self._is_all_prerequisites(targets, node):
                return targets[:1] or [node.id]
            return targets

        if effective_level == RollbackLevel.R1_INTERNAL:
            return [node.id]

        if node.prerequisites:
            if effective_level == RollbackLevel.R4_CHAPTER_FRAMEWORK:
                return node.prerequisites[: self.config.max_rollback_nodes]
            return [node.prerequisites[0]]

        return [node.id]

    def _effective_rollback_level(self, error: ErrorItem) -> RollbackLevel:
        if (
            error.suggested_rollback_level == RollbackLevel.R4_CHAPTER_FRAMEWORK
            and error.error_type not in self.R4_ALLOWED_SINGLE_ERROR_TYPES
        ):
            return RollbackLevel.R2_PREREQUISITE
        return error.suggested_rollback_level

    def _resolve_target(self, target: str, node: KnowledgeNode) -> str:
        if target == "__self__":
            return node.id
        if target == "__first_prerequisite__":
            return node.prerequisites[0] if node.prerequisites else node.id
        return target

    def _avoid_all_prerequisites_for_local_errors(
        self,
        selected: list[str],
        errors: list[ErrorItem],
        node: KnowledgeNode,
    ) -> list[str]:
        local_error_types = {
            ErrorType.CALCULATION_ERROR,
            ErrorType.EXPRESSION_WEAKNESS,
            ErrorType.PROCESS_GAP,
        }
        if any(error.error_type in local_error_types for error in errors):
            if self._is_all_prerequisites(selected, node):
                return [node.id]
        if self._is_all_prerequisites(selected, node):
            top_level = self._effective_rollback_level(sorted(errors, key=lambda item: item.weight, reverse=True)[0])
            if top_level != RollbackLevel.R4_CHAPTER_FRAMEWORK:
                return selected[:1]
        return selected

    def _is_all_prerequisites(self, selected: list[str], node: KnowledgeNode) -> bool:
        return bool(node.prerequisites) and set(selected) == set(node.prerequisites) and len(selected) == len(node.prerequisites)

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                deduped.append(value)
        return deduped
```

## backend/app/services/forward_engine.py

```python
from __future__ import annotations

from app.core.config import DEFAULT_ENGINE_CONFIG, EngineConfig
from app.core.enums import ForwardLevel, ScoreDimension
from app.core.schemas import ErrorVector, KnowledgeNode, ScoreVector


class ForwardEngine:
    def __init__(self, config: EngineConfig = DEFAULT_ENGINE_CONFIG) -> None:
        self.config = config

    def determine_forward_level(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
        node: KnowledgeNode,
    ) -> ForwardLevel:
        if error_vector.primary_errors():
            return ForwardLevel.P0_NONE

        if self._has_false_pass_signal(score_vector):
            return ForwardLevel.P0_NONE

        if not self._required_dimensions_met(score_vector, node):
            return ForwardLevel.P1_PARTIAL if score_vector.overall_score(node.scoring_weights) and score_vector.overall_score(node.scoring_weights) >= 70 else ForwardLevel.P0_NONE

        overall = score_vector.overall_score(node.scoring_weights)
        if overall is None:
            return ForwardLevel.P0_NONE

        if not self._has_sufficient_non_answer_evidence(score_vector):
            return ForwardLevel.P1_PARTIAL if overall >= 70 else ForwardLevel.P0_NONE

        if overall >= 92 and not error_vector.secondary_errors() and self._strong_forward_ready(score_vector):
            return ForwardLevel.P3_STRONG
        if overall >= node.pass_criteria.min_overall:
            return ForwardLevel.P2_NORMAL
        if overall >= 70:
            return ForwardLevel.P1_PARTIAL
        return ForwardLevel.P0_NONE

    def select_forward_nodes(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
        node: KnowledgeNode,
    ) -> list[str]:
        level = self.determine_forward_level(score_vector, error_vector, node)
        if level == ForwardLevel.P0_NONE:
            return []
        if level == ForwardLevel.P1_PARTIAL:
            return node.successors[:1]
        if level == ForwardLevel.P2_NORMAL:
            return node.successors[:1]
        return node.successors[:2]

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
```

## backend/app/seed/ode_nodes.yaml

```yaml
nodes:
  - id: ode_basic_concept
    name: 微分方程基本概念
    type: concept
    status: available
    prerequisites: []
    successors: [ode_order, ode_general_special_solution]
    core_dimensions: [concept, expression]
    common_errors: [concept_gap, expression_weakness]
    description: 理解微分方程、未知函数、导数、阶、解、通解和特解的基本语言。
    trigger_patterns:
      - 出现未知函数及其导数关系
      - 要求判断是否为微分方程或说明解的含义
    scoring_weights:
      concept: 0.55
      expression: 0.25
      final_answer: 0.20
    rollback_policy:
      concept_gap:
        level: r1_internal
        target_nodes: [__self__]
        notes: 回到定义和对象识别。
      expression_weakness:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练基本表述和符号规范。
    pass_criteria:
      min_overall: 75
      min_required_dimensions:
        concept: 75
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [definition_judgement, solution_check]
      parameter_focus: [unknown_function, derivative_order]
      validation_required: true

  - id: ode_order
    name: 解的阶与方程阶
    type: concept
    status: locked
    prerequisites: [ode_basic_concept]
    successors: [ode_general_special_solution]
    core_dimensions: [concept, trigger, expression]
    common_errors: [concept_gap, condition_miss, expression_weakness]
    description: 判断微分方程阶数，区分方程阶、导数阶和解中任意常数个数。
    trigger_patterns:
      - 要求判断微分方程阶数
      - 出现最高阶导数或任意常数个数
    scoring_weights:
      concept: 0.45
      trigger: 0.25
      expression: 0.15
      final_answer: 0.15
    rollback_policy:
      concept_gap:
        level: r2_prerequisite
        target_nodes: [ode_basic_concept]
        notes: 回到微分方程对象和解的定义。
      condition_miss:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练最高阶导数识别。
    pass_criteria:
      min_overall: 75
      min_required_dimensions:
        concept: 75
        trigger: 70
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [order_identification, solution_constant_count]
      parameter_focus: [highest_derivative, implicit_form]
      validation_required: true

  - id: ode_general_special_solution
    name: 通解与特解
    type: concept
    status: locked
    prerequisites: [ode_basic_concept, ode_order]
    successors: [ode_separable, ode_first_order_linear]
    core_dimensions: [concept, process, expression, final_answer]
    common_errors: [concept_gap, condition_miss, expression_weakness]
    description: 区分通解、特解、初值条件和任意常数。
    trigger_patterns:
      - 出现初值条件
      - 要求说明通解或特解
      - 需要代入条件确定常数
    scoring_weights:
      concept: 0.40
      process: 0.25
      expression: 0.15
      final_answer: 0.20
    rollback_policy:
      concept_gap:
        level: r2_prerequisite
        target_nodes: [ode_basic_concept, ode_order]
        notes: 回到解的定义和阶数关系。
      condition_miss:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练初值条件代入。
    pass_criteria:
      min_overall: 78
      min_required_dimensions:
        concept: 75
        expression: 70
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [initial_value, constant_determination]
      parameter_focus: [initial_condition, arbitrary_constant]
      validation_required: true

  - id: ode_separable
    name: 可分离变量方程
    type: method
    status: locked
    prerequisites: [ode_basic_concept, ode_general_special_solution]
    successors: [ode_homogeneous_first_order, ode_first_order_linear]
    core_dimensions: [trigger, method, transformation, calculation, final_answer]
    common_errors: [trigger_failure, method_error, transformation_error, calculation_error, condition_miss]
    description: 识别并求解可写成 g(y)dy = f(x)dx 的一阶方程。
    trigger_patterns:
      - dy/dx 可整理为 f(x)g(y)
      - x 与 y 可分离到等式两侧
    scoring_weights:
      trigger: 0.20
      method: 0.20
      transformation: 0.20
      calculation: 0.20
      final_answer: 0.20
    rollback_policy:
      trigger_failure:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练可分离形式识别。
      transformation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练变量分离和等价变形。
      calculation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 只做局部积分与代数计算修复。
      concept_gap:
        level: r2_prerequisite
        target_nodes: [ode_general_special_solution]
        notes: 回到通解和特解概念。
    pass_criteria:
      min_overall: 80
      min_required_dimensions:
        trigger: 75
        method: 75
        transformation: 75
        calculation: 70
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [direct_separable, separable_with_initial_value]
      parameter_focus: [separable_factors, integration_constant]
      validation_required: true

  - id: ode_homogeneous_first_order
    name: 一阶齐次方程
    type: method
    status: locked
    prerequisites: [ode_separable]
    successors: [ode_first_order_linear, ode_bernoulli]
    core_dimensions: [trigger, method, transformation, calculation]
    common_errors: [trigger_failure, method_error, transformation_error, calculation_error, knowledge_confusion]
    description: 识别 y/x 或 x/y 结构，通过 y = vx 或 x = vy 转化为可分离方程。
    trigger_patterns:
      - dy/dx = F(y/x)
      - M(x,y), N(x,y) 为同次齐次函数
    scoring_weights:
      trigger: 0.25
      method: 0.20
      transformation: 0.30
      calculation: 0.15
      final_answer: 0.10
    rollback_policy:
      trigger_failure:
        level: r2_prerequisite
        target_nodes: [ode_separable]
        notes: 先确认转化后要回到可分离。
      transformation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练 y = vx 的导数转化。
      knowledge_confusion:
        level: r4_chapter_framework
        target_nodes: [ode_separable, ode_first_order_linear]
        notes: 对比一阶齐次与一阶线性。
      calculation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 局部计算训练。
    pass_criteria:
      min_overall: 80
      min_required_dimensions:
        trigger: 75
        transformation: 75
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [y_over_x_substitution, homogeneous_mn_form]
      parameter_focus: [homogeneous_degree, substitution_choice]
      validation_required: true

  - id: ode_first_order_linear
    name: 一阶线性微分方程
    type: method
    status: locked
    prerequisites: [ode_general_special_solution, ode_separable]
    successors: [ode_integrating_factor, ode_bernoulli]
    core_dimensions: [trigger, method, transformation, calculation, final_answer]
    common_errors: [trigger_failure, method_error, formula_memory_error, transformation_error, calculation_error]
    description: 识别 y' + P(x)y = Q(x) 标准形并使用通解公式或积分因子。
    trigger_patterns:
      - y' + P(x)y = Q(x)
      - 未知函数及其一阶导数线性出现
    scoring_weights:
      trigger: 0.20
      method: 0.20
      transformation: 0.20
      calculation: 0.20
      final_answer: 0.20
    rollback_policy:
      trigger_failure:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练标准形识别。
      formula_memory_error:
        level: r2_prerequisite
        target_nodes: [ode_integrating_factor]
        notes: 回到积分因子公式。
      calculation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 局部积分计算训练。
      method_error:
        level: r2_prerequisite
        target_nodes: [ode_separable]
        notes: 对比可分离与一阶线性。
    pass_criteria:
      min_overall: 80
      min_required_dimensions:
        trigger: 75
        method: 75
        calculation: 70
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [standard_linear, linear_with_initial_value]
      parameter_focus: [p_of_x, q_of_x, integrating_factor]
      validation_required: true

  - id: ode_integrating_factor
    name: 积分因子
    type: transformation
    status: locked
    prerequisites: [ode_first_order_linear]
    successors: [ode_bernoulli]
    core_dimensions: [concept, transformation, calculation, expression]
    common_errors: [formula_memory_error, transformation_error, calculation_error, expression_weakness]
    description: 理解并计算一阶线性方程中的积分因子。
    trigger_patterns:
      - 出现 y' + P(x)y = Q(x)
      - 需要乘以 e 的积分形式使左侧成为乘积导数
    scoring_weights:
      concept: 0.20
      transformation: 0.35
      calculation: 0.25
      expression: 0.10
      final_answer: 0.10
    rollback_policy:
      formula_memory_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 复习 mu(x)=e^{int P(x)dx}。
      transformation_error:
        level: r2_prerequisite
        target_nodes: [ode_first_order_linear]
        notes: 回到标准形整理。
      calculation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 局部积分计算。
    pass_criteria:
      min_overall: 78
      min_required_dimensions:
        transformation: 75
        calculation: 70
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [integrating_factor_compute, product_derivative]
      parameter_focus: [p_of_x_integral, constant_handling]
      validation_required: true

  - id: ode_bernoulli
    name: 伯努利方程
    type: method
    status: locked
    prerequisites: [ode_first_order_linear, ode_integrating_factor]
    successors: [ode_reducible_order]
    core_dimensions: [trigger, method, transformation, calculation]
    common_errors: [trigger_failure, method_error, transformation_error, formula_memory_error, calculation_error]
    description: 识别 y' + P(x)y = Q(x)y^n，通过变量替换转化为一阶线性方程。
    trigger_patterns:
      - y' + P(x)y = Q(x)y^n
      - n 不是 0 或 1
    scoring_weights:
      trigger: 0.25
      method: 0.20
      transformation: 0.30
      calculation: 0.15
      final_answer: 0.10
    rollback_policy:
      trigger_failure:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练 Bernoulli 形态识别。
      transformation_error:
        level: r2_prerequisite
        target_nodes: [ode_first_order_linear]
        notes: 回到替换后的一阶线性方程。
      formula_memory_error:
        level: r2_prerequisite
        target_nodes: [ode_integrating_factor]
        notes: 修复一阶线性求解公式。
      calculation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 局部计算训练。
    pass_criteria:
      min_overall: 80
      min_required_dimensions:
        trigger: 75
        transformation: 75
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [bernoulli_standard, bernoulli_transform]
      parameter_focus: [power_n, substitution_z]
      validation_required: true

  - id: ode_reducible_order
    name: 可降阶方程
    type: method
    status: locked
    prerequisites: [ode_order, ode_general_special_solution]
    successors: [ode_y_missing_x, ode_second_order_constant_hom]
    core_dimensions: [trigger, method, transformation, process]
    common_errors: [trigger_failure, method_error, transformation_error, process_gap]
    description: 识别可通过变量替换或缺失变量降低阶数的高阶方程。
    trigger_patterns:
      - 高阶方程中缺少 x 或 y
      - 可令 p = y' 或 p(y) 降阶
    scoring_weights:
      trigger: 0.25
      method: 0.25
      transformation: 0.30
      process: 0.20
    rollback_policy:
      trigger_failure:
        level: r4_chapter_framework
        target_nodes: [ode_order]
        notes: 回到阶数和缺失变量识别。
      transformation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练降阶替换。
      process_gap:
        level: r1_internal
        target_nodes: [__self__]
        notes: 重构降阶过程。
    pass_criteria:
      min_overall: 78
      min_required_dimensions:
        trigger: 70
        transformation: 75
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [missing_variable, order_reduction]
      parameter_focus: [missing_x_or_y, substitution_p]
      validation_required: true

  - id: ode_y_missing_x
    name: 不显含 x 型可降阶
    type: transformation
    status: locked
    prerequisites: [ode_reducible_order]
    successors: [ode_second_order_constant_hom]
    core_dimensions: [trigger, transformation, process, calculation]
    common_errors: [trigger_failure, transformation_error, process_gap, calculation_error]
    description: 对不显含 x 的二阶方程使用 p(y)=y' 和 y''=p dp/dy 进行降阶。
    trigger_patterns:
      - 方程不显含 x
      - 需要使用 y'' = p dp/dy
    scoring_weights:
      trigger: 0.20
      transformation: 0.35
      process: 0.25
      calculation: 0.20
    rollback_policy:
      trigger_failure:
        level: r2_prerequisite
        target_nodes: [ode_reducible_order]
        notes: 回到可降阶分类。
      transformation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练 p(y) 替换。
      calculation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 局部微分计算。
    pass_criteria:
      min_overall: 78
      min_required_dimensions:
        transformation: 75
        process: 70
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [missing_x_reduction]
      parameter_focus: [p_of_y, second_derivative_transform]
      validation_required: true

  - id: ode_second_order_constant_hom
    name: 二阶常系数齐次线性方程
    type: method
    status: locked
    prerequisites: [ode_order, ode_general_special_solution]
    successors: [ode_characteristic_equation, ode_second_order_constant_nonhom]
    core_dimensions: [trigger, method, calculation, final_answer]
    common_errors: [trigger_failure, method_error, formula_memory_error, calculation_error]
    description: 识别 ay''+by'+cy=0 并通过特征方程求通解。
    trigger_patterns:
      - 二阶线性齐次
      - 系数为常数
      - 右端为 0
    scoring_weights:
      trigger: 0.25
      method: 0.25
      calculation: 0.20
      final_answer: 0.20
      expression: 0.10
    rollback_policy:
      trigger_failure:
        level: r4_chapter_framework
        target_nodes: [ode_order, ode_general_special_solution]
        notes: 回到阶数和线性齐次识别。
      formula_memory_error:
        level: r2_prerequisite
        target_nodes: [ode_characteristic_equation]
        notes: 回到根型与通解形式。
      calculation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 局部特征根计算。
    pass_criteria:
      min_overall: 80
      min_required_dimensions:
        trigger: 75
        method: 75
        final_answer: 75
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [constant_hom_roots]
      parameter_focus: [distinct_roots, repeated_roots, complex_roots]
      validation_required: true

  - id: ode_characteristic_equation
    name: 特征方程
    type: transformation
    status: locked
    prerequisites: [ode_second_order_constant_hom]
    successors: [ode_second_order_constant_nonhom]
    core_dimensions: [method, transformation, calculation, final_answer]
    common_errors: [formula_memory_error, calculation_error, expression_weakness]
    description: 从常系数线性方程建立特征方程，并根据根型写出解结构。
    trigger_patterns:
      - 常系数线性微分方程
      - 需要求特征根
      - 根型决定通解结构
    scoring_weights:
      method: 0.20
      transformation: 0.25
      calculation: 0.25
      final_answer: 0.20
      expression: 0.10
    rollback_policy:
      formula_memory_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 复习根型与解形式。
      calculation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 局部代数计算。
      expression_weakness:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练通解表达。
    pass_criteria:
      min_overall: 80
      min_required_dimensions:
        transformation: 75
        calculation: 75
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [characteristic_roots]
      parameter_focus: [root_type, solution_basis]
      validation_required: true

  - id: ode_second_order_constant_nonhom
    name: 二阶常系数非齐次线性方程
    type: method
    status: locked
    prerequisites: [ode_second_order_constant_hom, ode_characteristic_equation]
    successors: [ode_particular_solution_form, ode_euler]
    core_dimensions: [trigger, method, process, final_answer]
    common_errors: [trigger_failure, method_error, synthesis_failure, formula_memory_error, calculation_error]
    description: 将解分解为齐次通解和非齐次特解，选择待定系数或其他方法。
    trigger_patterns:
      - 二阶常系数线性方程
      - 右端非零
      - 需要 yc + yp
    scoring_weights:
      trigger: 0.20
      method: 0.25
      process: 0.25
      calculation: 0.15
      final_answer: 0.15
    rollback_policy:
      trigger_failure:
        level: r2_prerequisite
        target_nodes: [ode_second_order_constant_hom]
        notes: 对比齐次与非齐次。
      synthesis_failure:
        level: r4_chapter_framework
        target_nodes: [ode_second_order_constant_hom, ode_particular_solution_form]
        notes: 拆解 yc 与 yp。
      formula_memory_error:
        level: r2_prerequisite
        target_nodes: [ode_characteristic_equation]
        notes: 修复齐次解部分。
      calculation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 局部计算训练。
    pass_criteria:
      min_overall: 80
      min_required_dimensions:
        trigger: 75
        method: 75
        process: 75
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [nonhom_constant_coeff]
      parameter_focus: [forcing_term, yc_plus_yp]
      validation_required: true

  - id: ode_particular_solution_form
    name: 非齐次特解形式设定
    type: transformation
    status: locked
    prerequisites: [ode_second_order_constant_nonhom]
    successors: [ode_euler, ode_application_modeling]
    core_dimensions: [trigger, method, transformation, migration]
    common_errors: [trigger_failure, method_error, transformation_error, migration_failure]
    description: 根据右端函数形式和共振情况设定非齐次特解形式。
    trigger_patterns:
      - 右端为指数、多项式、三角函数或其组合
      - 需要判断是否与齐次解重复
    scoring_weights:
      trigger: 0.25
      method: 0.25
      transformation: 0.30
      migration: 0.20
    rollback_policy:
      trigger_failure:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练右端函数类型识别。
      transformation_error:
        level: r2_prerequisite
        target_nodes: [ode_characteristic_equation]
        notes: 回到根型和共振判断。
      migration_failure:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练变式右端。
    pass_criteria:
      min_overall: 80
      min_required_dimensions:
        trigger: 75
        transformation: 75
        migration: 65
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [undetermined_coefficients_form]
      parameter_focus: [forcing_family, resonance_multiplier]
      validation_required: true

  - id: ode_euler
    name: 欧拉方程
    type: method
    status: locked
    prerequisites: [ode_second_order_constant_hom, ode_characteristic_equation]
    successors: [ode_application_modeling]
    core_dimensions: [trigger, method, transformation, calculation]
    common_errors: [trigger_failure, method_error, transformation_error, formula_memory_error, calculation_error]
    description: 识别 Cauchy-Euler 方程并通过 x=e^t 或 y=x^r 求解。
    trigger_patterns:
      - x^2 y'' + a x y' + b y 形式
      - 幂次系数与导数阶数匹配
    scoring_weights:
      trigger: 0.25
      method: 0.25
      transformation: 0.25
      calculation: 0.15
      final_answer: 0.10
    rollback_policy:
      trigger_failure:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练欧拉方程结构识别。
      transformation_error:
        level: r2_prerequisite
        target_nodes: [ode_characteristic_equation]
        notes: 回到幂函数设解和特征方程。
      calculation_error:
        level: r1_internal
        target_nodes: [__self__]
        notes: 局部代数计算。
    pass_criteria:
      min_overall: 78
      min_required_dimensions:
        trigger: 75
        transformation: 70
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [euler_homogeneous]
      parameter_focus: [power_coefficients, root_type]
      validation_required: true

  - id: ode_application_modeling
    name: 微分方程应用建模
    type: application
    status: locked
    prerequisites: [ode_general_special_solution, ode_first_order_linear, ode_second_order_constant_nonhom]
    successors: []
    core_dimensions: [concept, trigger, method, process, expression, migration]
    common_errors: [condition_miss, synthesis_failure, method_error, expression_weakness, migration_failure]
    description: 将变化率、增长衰减、运动或物理背景转化为微分方程并求解解释。
    trigger_patterns:
      - 出现变化率与状态量关系
      - 需要从文字条件建立微分方程
      - 需要解释模型结果
    scoring_weights:
      concept: 0.15
      trigger: 0.20
      method: 0.20
      process: 0.20
      expression: 0.15
      migration: 0.10
    rollback_policy:
      condition_miss:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练文字条件提取。
      synthesis_failure:
        level: r4_chapter_framework
        target_nodes: [ode_general_special_solution, ode_first_order_linear]
        notes: 回到建模拆解路径。
      method_error:
        level: r2_prerequisite
        target_nodes: [ode_first_order_linear]
        notes: 常见建模落到一阶线性。
      expression_weakness:
        level: r1_internal
        target_nodes: [__self__]
        notes: 训练模型解释表达。
    pass_criteria:
      min_overall: 80
      min_required_dimensions:
        trigger: 75
        method: 75
        process: 75
      max_primary_errors: 0
      allow_false_pass: false
    variant_policy:
      template_families: [growth_decay, rate_modeling, motion_modeling]
      parameter_focus: [initial_condition, rate_relation, interpretation]
      validation_required: true
```

## evals/golden_cases/ode_scoring_cases.yaml

```yaml
cases:
  - id: ode_separable_complete_correct
    category: complete_correct
    title: 完全正确
    question:
      id: q_ode_sep_001
      node_id: ode_separable
      question_type: diagnostic
      prompt: 求解 dy/dx = 2xy，并写出通解。
    user_answer: 先分离变量 dy/y = 2x dx，积分得 ln|y| = x^2 + C，因此 y = Ce^{x^2}。
    expected_scores:
      concept: 90
      trigger: 92
      method: 95
      transformation: 95
      process: 92
      calculation: 95
      final_answer: 95
      expression: 90
      migration: null
    expected_errors: []
    expected_pass_state: pass
    expected_rollback_behavior:
      rollback_level: null
      forward_level: p2_normal
      target_nodes: []
      should_not_return_all_prerequisites: true
      explanation: 无主错因，可正常推进到后继节点。

  - id: ode_separable_process_right_calculation_wrong
    category: process_right_calculation_wrong
    title: 过程对但计算错
    question:
      id: q_ode_sep_002
      node_id: ode_separable
      question_type: diagnostic
      prompt: 求解 dy/dx = 2xy，并写出通解。
    user_answer: 分离变量 dy/y = 2x dx，积分后误写为 ln|y| = 2x^2 + C，所以 y = Ce^{2x^2}。
    expected_scores:
      concept: 85
      trigger: 88
      method: 90
      transformation: 88
      process: 82
      calculation: 20
      final_answer: 0
      expression: 75
      migration: null
    expected_errors:
      - error_type: calculation_error
        weight: 0.85
        related_dimensions: [calculation, final_answer]
        is_primary: true
        suggested_rollback_level: r1_internal
        evidence: 方法和变量分离正确，但积分系数计算错误。
    expected_pass_state: fail
    expected_rollback_behavior:
      rollback_level: r1_internal
      forward_level: p0_none
      target_nodes: [ode_separable]
      should_not_return_all_prerequisites: true
      explanation: 方法和转化证据较好，只做局部计算回溯。

  - id: ode_linear_answer_right_trigger_unclear
    category: answer_right_trigger_unclear
    title: 答案对但题眼不清
    question:
      id: q_ode_linear_001
      node_id: ode_first_order_linear
      question_type: diagnostic
      prompt: 求解 y' + y = e^x。
    user_answer: 写出正确答案 y = 1/2 e^x + Ce^{-x}，但无法说明为什么用一阶线性方程方法。
    expected_scores:
      concept: 60
      trigger: 25
      method: 35
      transformation: 55
      process: 60
      calculation: 85
      final_answer: 95
      expression: 80
      migration: null
    expected_errors:
      - error_type: trigger_failure
        weight: 0.80
        related_dimensions: [trigger]
        is_primary: true
        suggested_rollback_level: r1_internal
        evidence: 不能说明一阶线性标准形题眼。
      - error_type: method_error
        weight: 0.70
        related_dimensions: [method]
        is_primary: true
        suggested_rollback_level: r1_internal
        evidence: 方法选择缺少可解释证据。
    expected_pass_state: false_pass
    expected_rollback_behavior:
      rollback_level: r1_internal
      forward_level: p0_none
      target_nodes: [ode_first_order_linear]
      should_not_strong_forward: true
      explanation: final_answer 高但 trigger/method 低，属于假性通过。

  - id: ode_homogeneous_trigger_failure
    category: trigger_failure
    title: 题眼识别失败
    question:
      id: q_ode_hom_001
      node_id: ode_homogeneous_first_order
      question_type: diagnostic
      prompt: 求解 dy/dx = (x + y) / x。
    user_answer: 尝试直接积分 dy = (1 + y/x) dx，没有识别 y/x 结构。
    expected_scores:
      concept: 55
      trigger: 10
      method: 25
      transformation: 20
      process: 35
      calculation: 50
      final_answer: 0
      expression: 55
      migration: null
    expected_errors:
      - error_type: trigger_failure
        weight: 0.90
        related_dimensions: [trigger, method]
        is_primary: true
        suggested_rollback_level: r2_prerequisite
        evidence: 未识别 F(y/x) 的一阶齐次题眼。
      - error_type: transformation_error
        weight: 0.70
        related_dimensions: [transformation]
        is_primary: true
        suggested_rollback_level: r1_internal
        evidence: 没有使用 y = vx 转化。
    expected_pass_state: fail
    expected_rollback_behavior:
      rollback_level: r2_prerequisite
      forward_level: p0_none
      target_nodes: [ode_separable]
      should_not_return_all_prerequisites: true
      explanation: 优先回到一阶齐次转化后连接的可分离方法。

  - id: ode_bernoulli_transformation_failure
    category: transformation_failure
    title: 条件转化失败
    question:
      id: q_ode_bern_001
      node_id: ode_bernoulli
      question_type: diagnostic
      prompt: 求解 y' + y = xy^2。
    user_answer: 识别为伯努利方程，但令 z = y^2 后直接代入，导致转化错误。
    expected_scores:
      concept: 70
      trigger: 82
      method: 75
      transformation: 15
      process: 35
      calculation: 45
      final_answer: 0
      expression: 60
      migration: null
    expected_errors:
      - error_type: transformation_error
        weight: 0.92
        related_dimensions: [transformation, process]
        is_primary: true
        suggested_rollback_level: r2_prerequisite
        evidence: 伯努利替换方向错误，未转化为一阶线性方程。
      - error_type: calculation_error
        weight: 0.45
        related_dimensions: [calculation]
        is_primary: false
        suggested_rollback_level: r1_internal
        evidence: 后续计算受错误转化影响。
    expected_pass_state: fail
    expected_rollback_behavior:
      rollback_level: r2_prerequisite
      forward_level: p0_none
      target_nodes: [ode_first_order_linear]
      should_not_return_all_prerequisites: true
      explanation: 主错因是替换转化失败，应回到一阶线性转化连接。

  - id: ode_separable_method_error
    category: method_error
    title: 方法选择错误
    question:
      id: q_ode_sep_003
      node_id: ode_separable
      question_type: diagnostic
      prompt: 求解 dy/dx = x(1+y^2)。
    user_answer: 误认为是一阶线性方程，尝试写成 y' + P(x)y = Q(x)。
    expected_scores:
      concept: 65
      trigger: 45
      method: 20
      transformation: 30
      process: 30
      calculation: 60
      final_answer: 0
      expression: 60
      migration: null
    expected_errors:
      - error_type: method_error
        weight: 0.90
        related_dimensions: [method]
        is_primary: true
        suggested_rollback_level: r2_prerequisite
        evidence: 可分离方程误选为一阶线性方法。
      - error_type: trigger_failure
        weight: 0.55
        related_dimensions: [trigger]
        is_primary: false
        suggested_rollback_level: r1_internal
        evidence: 未抓住变量可分离题眼。
    expected_pass_state: fail
    expected_rollback_behavior:
      rollback_level: r2_prerequisite
      forward_level: p0_none
      target_nodes: [ode_general_special_solution]
      should_not_return_all_prerequisites: true
      explanation: 主错因是方法选择，应回到直接方法比较与前置概念。

  - id: ode_basic_expression_weak_but_meaning_right
    category: expression_weakness
    title: 概念表达不严谨但大意正确
    question:
      id: q_ode_basic_001
      node_id: ode_basic_concept
      question_type: diagnostic
      prompt: 说明什么是微分方程的通解。
    user_answer: 大概就是很多答案放一起，里面有 C，但没有说明任意常数个数和满足方程。
    expected_scores:
      concept: 72
      trigger: null
      method: null
      transformation: null
      process: 65
      calculation: null
      final_answer: 70
      expression: 35
      migration: null
    expected_errors:
      - error_type: expression_weakness
        weight: 0.75
        related_dimensions: [expression]
        is_primary: true
        suggested_rollback_level: r1_internal
        evidence: 大意接近但缺少严谨定义和条件。
    expected_pass_state: partial_pass
    expected_rollback_behavior:
      rollback_level: r1_internal
      forward_level: p1_partial
      target_nodes: [ode_basic_concept]
      should_not_return_all_prerequisites: true
      explanation: 概念大意可保留，但表达需本节点修复。

  - id: ode_linear_formula_memory_error
    category: formula_memory_error
    title: 公式记忆错误
    question:
      id: q_ode_linear_002
      node_id: ode_integrating_factor
      question_type: diagnostic
      prompt: 对 y' + 2xy = x 求积分因子。
    user_answer: 写成 mu(x)=e^{2x}，没有对 2x 积分为 x^2。
    expected_scores:
      concept: 65
      trigger: 75
      method: 70
      transformation: 55
      process: 60
      calculation: 30
      final_answer: 0
      expression: 70
      migration: null
    expected_errors:
      - error_type: formula_memory_error
        weight: 0.85
        related_dimensions: [method, transformation]
        is_primary: true
        suggested_rollback_level: r1_internal
        evidence: 积分因子公式记忆不完整。
      - error_type: calculation_error
        weight: 0.55
        related_dimensions: [calculation]
        is_primary: false
        suggested_rollback_level: r1_internal
        evidence: 对 P(x) 的积分错误。
    expected_pass_state: fail
    expected_rollback_behavior:
      rollback_level: r1_internal
      forward_level: p0_none
      target_nodes: [ode_integrating_factor]
      should_not_return_all_prerequisites: true
      explanation: 先修复积分因子公式和局部积分。

  - id: ode_ivp_condition_miss
    category: condition_miss
    title: 审题遗漏
    question:
      id: q_ode_ivp_001
      node_id: ode_general_special_solution
      question_type: diagnostic
      prompt: 求解 y' = 2x, y(0)=3。
    user_answer: 积分得 y=x^2+C，但未代入 y(0)=3。
    expected_scores:
      concept: 78
      trigger: 75
      method: 82
      transformation: 80
      process: 68
      calculation: 85
      final_answer: 40
      expression: 70
      migration: null
    expected_errors:
      - error_type: condition_miss
        weight: 0.82
        related_dimensions: [process, final_answer]
        is_primary: true
        suggested_rollback_level: r1_internal
        evidence: 漏用初值条件，停在通解。
    expected_pass_state: fail
    expected_rollback_behavior:
      rollback_level: r1_internal
      forward_level: p0_none
      target_nodes: [ode_general_special_solution]
      should_not_return_all_prerequisites: true
      explanation: 方法正确但漏条件，回到本节点初值条件训练。

  - id: ode_homogeneous_linear_confusion
    category: knowledge_confusion
    title: 知识点混淆
    question:
      id: q_ode_confusion_001
      node_id: ode_homogeneous_first_order
      question_type: diagnostic
      prompt: 判断 dy/dx = y/x 应使用哪类方法。
    user_answer: 说这是二阶常系数齐次线性方程，要写特征方程。
    expected_scores:
      concept: 35
      trigger: 20
      method: 10
      transformation: 20
      process: 25
      calculation: null
      final_answer: 0
      expression: 55
      migration: null
    expected_errors:
      - error_type: knowledge_confusion
        weight: 0.95
        related_dimensions: [concept, trigger, method]
        is_primary: true
        suggested_rollback_level: r4_chapter_framework
        evidence: 混淆一阶齐次方程和二阶常系数齐次线性方程。
    expected_pass_state: fail
    expected_rollback_behavior:
      rollback_level: r4_chapter_framework
      forward_level: p0_none
      target_nodes: [ode_separable, ode_first_order_linear]
      should_not_return_all_prerequisites: false
      explanation: 属于知识框架混淆，可做章节内类型对比回溯。

  - id: ode_particular_variant_migration_failure
    category: migration_failure
    title: 变式迁移失败
    question:
      id: q_ode_variant_001
      node_id: ode_particular_solution_form
      question_type: variant
      prompt: 已会处理 e^x 右端，现在判断右端 x e^x 时特解形式如何调整。
    user_answer: 仍写 Ae^x，没有考虑多项式因子和待定系数形式变化。
    expected_scores:
      concept: 75
      trigger: 70
      method: 70
      transformation: 50
      process: 55
      calculation: null
      final_answer: 30
      expression: 65
      migration: 20
    expected_errors:
      - error_type: migration_failure
        weight: 0.90
        related_dimensions: [migration, transformation]
        is_primary: true
        suggested_rollback_level: r1_internal
        evidence: 标准题会做，但右端变式后不能调整特解形式。
    expected_pass_state: fail
    expected_rollback_behavior:
      rollback_level: r1_internal
      forward_level: p0_none
      target_nodes: [ode_particular_solution_form]
      should_not_return_all_prerequisites: true
      explanation: 进入本节点变式梯度训练。

  - id: ode_application_synthesis_failure
    category: synthesis_failure
    title: 综合拆解失败
    question:
      id: q_ode_app_001
      node_id: ode_application_modeling
      question_type: diagnostic
      prompt: 根据变化率与当前量成正比且有初值的文字条件建立并求解模型。
    user_answer: 只写出一个零散公式，没有建立方程、代入初值或解释结果。
    expected_scores:
      concept: 40
      trigger: 25
      method: 20
      transformation: 25
      process: 15
      calculation: 45
      final_answer: 0
      expression: 40
      migration: 20
    expected_errors:
      - error_type: synthesis_failure
        weight: 0.95
        related_dimensions: [trigger, method, process]
        is_primary: true
        suggested_rollback_level: r4_chapter_framework
        evidence: 无法把文字题拆成建模、求解、代入和解释。
      - error_type: condition_miss
        weight: 0.60
        related_dimensions: [process]
        is_primary: false
        suggested_rollback_level: r1_internal
        evidence: 初值条件没有进入求解链。
    expected_pass_state: fail
    expected_rollback_behavior:
      rollback_level: r4_chapter_framework
      forward_level: p0_none
      target_nodes: [ode_general_special_solution, ode_first_order_linear]
      should_not_return_all_prerequisites: false
      explanation: 综合拆解失败允许章节框架级回溯。

  - id: ode_linear_correct_answer_unexplainable_method
    category: correct_answer_unexplainable_method
    title: 看似答案正确但方法不可解释
    question:
      id: q_ode_linear_003
      node_id: ode_first_order_linear
      question_type: diagnostic
      prompt: 求解 y' - y = 0。
    user_answer: 答案 y=Ce^x 正确，但说不出这是分离变量还是一阶线性，也无法解释步骤。
    expected_scores:
      concept: 55
      trigger: 30
      method: 25
      transformation: 50
      process: 45
      calculation: 80
      final_answer: 95
      expression: 75
      migration: null
    expected_errors:
      - error_type: trigger_failure
        weight: 0.80
        related_dimensions: [trigger]
        is_primary: true
        suggested_rollback_level: r1_internal
        evidence: 答案正确但无法解释题型识别。
      - error_type: method_error
        weight: 0.82
        related_dimensions: [method]
        is_primary: true
        suggested_rollback_level: r1_internal
        evidence: 方法路径不可解释。
    expected_pass_state: false_pass
    expected_rollback_behavior:
      rollback_level: r1_internal
      forward_level: p0_none
      target_nodes: [ode_first_order_linear]
      should_not_strong_forward: true
      explanation: 正确答案不能掩盖方法不可解释。

  - id: ode_method_right_initial_condition_miss
    category: method_right_initial_condition_miss
    title: 方法对但漏初值条件
    question:
      id: q_ode_linear_ivp_001
      node_id: ode_first_order_linear
      question_type: diagnostic
      prompt: 求解 y' + y = 0, y(0)=2。
    user_answer: 正确得到通解 y=Ce^{-x}，但没有求出 C=2。
    expected_scores:
      concept: 80
      trigger: 85
      method: 88
      transformation: 82
      process: 65
      calculation: 85
      final_answer: 45
      expression: 70
      migration: null
    expected_errors:
      - error_type: condition_miss
        weight: 0.85
        related_dimensions: [process, final_answer]
        is_primary: true
        suggested_rollback_level: r1_internal
        evidence: 求出通解后漏代初值条件。
    expected_pass_state: fail
    expected_rollback_behavior:
      rollback_level: r1_internal
      forward_level: p0_none
      target_nodes: [ode_first_order_linear]
      should_not_return_all_prerequisites: true
      explanation: 方法链正确，回到本节点条件处理。

  - id: ode_nonhom_particular_solution_form_wrong
    category: particular_solution_form_error
    title: 非齐次特解形式设错
    question:
      id: q_ode_nonhom_001
      node_id: ode_particular_solution_form
      question_type: diagnostic
      prompt: 对 y'' - y = e^x，判断待定特解形式。
    user_answer: 直接设 yp=Ae^x，没有发现 e^x 已是齐次解的一部分。
    expected_scores:
      concept: 70
      trigger: 65
      method: 60
      transformation: 20
      process: 40
      calculation: null
      final_answer: 0
      expression: 65
      migration: 45
    expected_errors:
      - error_type: transformation_error
        weight: 0.90
        related_dimensions: [transformation, method]
        is_primary: true
        suggested_rollback_level: r2_prerequisite
        evidence: 未处理共振，特解形式少乘 x。
      - error_type: formula_memory_error
        weight: 0.65
        related_dimensions: [method]
        is_primary: false
        suggested_rollback_level: r2_prerequisite
        evidence: 非齐次特解设定规则记忆不稳。
    expected_pass_state: fail
    expected_rollback_behavior:
      rollback_level: r2_prerequisite
      forward_level: p0_none
      target_nodes: [ode_characteristic_equation]
      should_not_return_all_prerequisites: true
      explanation: 回到特征根与共振判断后再练特解形式。
```
