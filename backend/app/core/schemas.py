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


class ScoreEvidence(BaseModel):
    source: str
    dimension: ScoreDimension
    score: Optional[float] = Field(default=None, ge=0, le=100)
    confidence: float = Field(default=0, ge=0, le=1)
    evidence: str
    matched_items: list[str] = Field(default_factory=list)
    missed_items: list[str] = Field(default_factory=list)
    required_missed: list[str] = Field(default_factory=list)
    optional_missed: list[str] = Field(default_factory=list)


class RubricItem(BaseModel):
    id: str
    description: str
    target_dimensions: list[ScoreDimension]
    required_keywords: list[str] = Field(default_factory=list)
    expected_patterns: list[str] = Field(default_factory=list)
    weight: float = Field(default=1, ge=0)
    required: bool = True
    partial_credit: bool = False
    partial_score: float = Field(default=60, ge=0, le=100)
    evidence_on_hit: str
    evidence_on_miss: str


class KeyPoint(BaseModel):
    id: str
    text: str
    target_dimensions: list[ScoreDimension]
    required: bool = True
    weight: float = Field(default=1, ge=0)
    required_keywords: list[str] = Field(default_factory=list)
    evidence_on_hit: Optional[str] = None
    evidence_on_miss: Optional[str] = None


class DimensionMergePolicy(BaseModel):
    strategy: str = "weighted_by_confidence"
    manual_override_first: bool = True
    missing_if_no_signal: bool = True


class ScoringRubric(BaseModel):
    items: list[RubricItem] = Field(default_factory=list)
    key_points: list[KeyPoint] = Field(default_factory=list)
    dimension_weights: dict[ScoreDimension, float] = Field(default_factory=dict)
    merge_policy: DimensionMergePolicy = Field(default_factory=DimensionMergePolicy)


class ScorerResult(BaseModel):
    scorer_name: str
    is_active: bool = False
    dimension_scores: dict[ScoreDimension, DimensionScore] = Field(default_factory=dict)
    evidence: list[ScoreEvidence] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)
    notes: list[str] = Field(default_factory=list)


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
            if normalized_weights and dimension.value not in normalized_weights:
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


class ErrorEvidence(BaseModel):
    source_type: str
    source_name: str
    dimension: Optional[ScoreDimension] = None
    error_type: Optional[ErrorType] = None
    rubric_item_id: Optional[str] = None
    evidence: str
    strength: float = Field(default=0, ge=0, le=1)
    confidence: float = Field(default=0, ge=0, le=1)
    tags: list[str] = Field(default_factory=list)


class ErrorChainItem(BaseModel):
    error_type: ErrorType
    role: str
    weight: float = Field(ge=0, le=1)
    related_dimensions: list[ScoreDimension] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    derived_from: Optional[ErrorType] = None
    reason: str
    suggested_rollback_level: RollbackLevel = RollbackLevel.R1_INTERNAL


class RootCauseAnalysis(BaseModel):
    root_cause: Optional[ErrorType] = None
    primary_errors: list[ErrorType] = Field(default_factory=list)
    secondary_errors: list[ErrorType] = Field(default_factory=list)
    derived_errors: list[ErrorType] = Field(default_factory=list)
    error_chain: list[ErrorChainItem] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)


class DiagnosisTrace(BaseModel):
    active_scorers: list[str] = Field(default_factory=list)
    dimension_sources: dict[ScoreDimension, list[str]] = Field(default_factory=dict)
    evidence_bundle: dict[str, list[str]] = Field(default_factory=dict)
    required_missed: list[str] = Field(default_factory=list)
    optional_missed: list[str] = Field(default_factory=list)
    validator_flags: list[str] = Field(default_factory=list)
    response_evidence: list[str] = Field(default_factory=list)
    logic_ability_signals: list[str] = Field(default_factory=list)
    logic_contradictions: list[str] = Field(default_factory=list)
    logic_weak_signals: list[str] = Field(default_factory=list)
    graph_edge_semantics: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    surface_keyword_only: bool = False
    optional_only: bool = False
    rule_only: bool = False
    policy_hits: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class RecommendedAction(BaseModel):
    action_type: str
    target_node_ids: list[str] = Field(default_factory=list)
    training_mode: Optional[str] = None
    priority: int = Field(default=3, ge=1, le=5)
    reason: str


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
    rubric: Optional[ScoringRubric] = None
    expected_key_points: list[KeyPoint] = Field(default_factory=list)
    expected_patterns: list[str] = Field(default_factory=list)
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
    learner_explanation: str = ""
    next_action_hint: str
    root_cause: Optional[ErrorType] = None
    primary_errors: list[ErrorType] = Field(default_factory=list)
    secondary_errors: list[ErrorType] = Field(default_factory=list)
    derived_errors: list[ErrorType] = Field(default_factory=list)
    downstream_result_errors: list[ErrorType] = Field(default_factory=list)
    weak_signal_errors: list[ErrorType] = Field(default_factory=list)
    evidence_gap_errors: list[ErrorType] = Field(default_factory=list)
    error_chain: list[ErrorChainItem] = Field(default_factory=list)
    confidence: float = Field(default=0, ge=0, le=1)
    evidence_sources: list[ErrorEvidence] = Field(default_factory=list)
    recommended_actions: list[RecommendedAction] = Field(default_factory=list)
    diagnosis_trace: Optional[DiagnosisTrace] = None
    ability_state: Optional[str] = None
    ability_state_label: str = ""
    ability_state_explanation: str = ""


class ForwardDecision(BaseModel):
    level: ForwardLevel
    forward_nodes: list[str] = Field(default_factory=list)
    blocked_nodes: list[str] = Field(default_factory=list)
    reason: str
    allowed_training_modes: list[str] = Field(default_factory=list)


class RollbackDecision(BaseModel):
    level: RollbackLevel
    rollback_nodes: list[str] = Field(default_factory=list)
    blocked_reason: str = ""
    is_chapter_framework_rollback: bool = False
    explanation: str


class CompositeScoreResult(BaseModel):
    score_vector: ScoreVector
    scorer_results: list[ScorerResult] = Field(default_factory=list)
    merge_notes: list[str] = Field(default_factory=list)

    def get_active_scorer_names(self) -> list[str]:
        return [result.scorer_name for result in self.scorer_results if result.is_active]

    def get_dimension_sources(self) -> dict[ScoreDimension, list[str]]:
        sources: dict[ScoreDimension, list[str]] = {}
        for result in self.scorer_results:
            if not result.is_active:
                continue
            for dimension in result.dimension_scores:
                sources.setdefault(dimension, []).append(result.scorer_name)
        return sources

    def explain_merge_for_dimension(self, dimension: ScoreDimension | str) -> str:
        dim = ScoreDimension(dimension)
        relevant_notes = [note for note in self.merge_notes if note.startswith(f"{dim.value}:")]
        if relevant_notes:
            return " ".join(relevant_notes)
        return f"{dim.value}: no scorer contributed a score."


class NodeAction(BaseModel):
    rollback_nodes: list[str] = Field(default_factory=list)
    forward_nodes: list[str] = Field(default_factory=list)
    review_tasks: list[ReviewTask] = Field(default_factory=list)
    node_status_updates: dict[str, NodeStatus] = Field(default_factory=dict)
    mastery_updates: dict[str, Any] = Field(default_factory=dict)
    explanation: str
