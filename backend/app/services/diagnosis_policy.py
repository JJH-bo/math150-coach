from __future__ import annotations

from dataclasses import dataclass, field

from app.core.config import DEFAULT_ENGINE_CONFIG
from app.core.enums import ErrorType, QuestionType, ScoreDimension
from app.core.schemas import DiagnosisTrace, ErrorItem, KnowledgeNode, Question, ScoreVector


@dataclass(frozen=True)
class ErrorAttributionRule:
    id: str
    produces_error_type: ErrorType
    root_when_tags: tuple[str, ...] = ()
    derived_errors: tuple[ErrorType, ...] = ()
    suppresses: tuple[ErrorType, ...] = ()
    action_type: str = "current_node_review"
    explanation_template: str = ""


@dataclass(frozen=True)
class DiagnosisPolicy:
    primary_weight_threshold: float = 0.7
    secondary_weight_threshold: float = 0.4
    rule_only_confidence_cap: float = 0.3
    no_evidence_confidence: float = 0.2
    dimension_error_map: dict[ScoreDimension, ErrorType] = field(
        default_factory=lambda: dict(DEFAULT_ENGINE_CONFIG.dimension_error_map)
    )
    action_by_error: dict[ErrorType, str] = field(
        default_factory=lambda: {
            ErrorType.CONCEPT_GAP: "current_node_review",
            ErrorType.TRIGGER_FAILURE: "trigger_drill",
            ErrorType.METHOD_ERROR: "method_comparison",
            ErrorType.TRANSFORMATION_ERROR: "transformation_drill",
            ErrorType.PROCESS_GAP: "current_node_review",
            ErrorType.CALCULATION_ERROR: "calculation_repair",
            ErrorType.CONDITION_MISS: "condition_check",
            ErrorType.FORMULA_MEMORY_ERROR: "current_node_review",
            ErrorType.KNOWLEDGE_CONFUSION: "chapter_framework_review",
            ErrorType.EXPRESSION_WEAKNESS: "expression_rewrite",
            ErrorType.MIGRATION_FAILURE: "variant_training",
            ErrorType.SYNTHESIS_FAILURE: "chapter_framework_review",
        }
    )
    derived_by_root: dict[ErrorType, tuple[ErrorType, ...]] = field(
        default_factory=lambda: {
            ErrorType.TRIGGER_FAILURE: (
                ErrorType.METHOD_ERROR,
                ErrorType.TRANSFORMATION_ERROR,
                ErrorType.PROCESS_GAP,
            ),
            ErrorType.METHOD_ERROR: (
                ErrorType.TRANSFORMATION_ERROR,
                ErrorType.PROCESS_GAP,
                ErrorType.CALCULATION_ERROR,
            ),
            ErrorType.TRANSFORMATION_ERROR: (
                ErrorType.PROCESS_GAP,
                ErrorType.CALCULATION_ERROR,
            ),
            ErrorType.CALCULATION_ERROR: (),
            ErrorType.CONDITION_MISS: (ErrorType.CALCULATION_ERROR,),
            ErrorType.EXPRESSION_WEAKNESS: (),
            ErrorType.KNOWLEDGE_CONFUSION: (
                ErrorType.CONCEPT_GAP,
                ErrorType.TRIGGER_FAILURE,
                ErrorType.METHOD_ERROR,
                ErrorType.TRANSFORMATION_ERROR,
            ),
            ErrorType.SYNTHESIS_FAILURE: (
                ErrorType.TRIGGER_FAILURE,
                ErrorType.METHOD_ERROR,
                ErrorType.PROCESS_GAP,
            ),
        }
    )
    root_priority: tuple[ErrorType, ...] = (
        ErrorType.CONDITION_MISS,
        ErrorType.KNOWLEDGE_CONFUSION,
        ErrorType.SYNTHESIS_FAILURE,
        ErrorType.TRIGGER_FAILURE,
        ErrorType.METHOD_ERROR,
        ErrorType.TRANSFORMATION_ERROR,
        ErrorType.CALCULATION_ERROR,
        ErrorType.EXPRESSION_WEAKNESS,
        ErrorType.FORMULA_MEMORY_ERROR,
        ErrorType.CONCEPT_GAP,
        ErrorType.MIGRATION_FAILURE,
        ErrorType.PROCESS_GAP,
    )
    rules: tuple[ErrorAttributionRule, ...] = field(
        default_factory=lambda: (
            ErrorAttributionRule(
                id="trigger_failure_derives_reasoning_errors",
                produces_error_type=ErrorType.TRIGGER_FAILURE,
                root_when_tags=("low_trigger", "required_missed"),
                derived_errors=(ErrorType.METHOD_ERROR, ErrorType.TRANSFORMATION_ERROR, ErrorType.PROCESS_GAP),
                action_type="trigger_drill",
                explanation_template="Trigger failure can cause method, transformation, and process errors.",
            ),
            ErrorAttributionRule(
                id="method_error_derives_process_and_answer_errors",
                produces_error_type=ErrorType.METHOD_ERROR,
                root_when_tags=("low_method",),
                derived_errors=(ErrorType.PROCESS_GAP, ErrorType.CALCULATION_ERROR),
                action_type="method_comparison",
                explanation_template="A wrong method can make later process and answer evidence unreliable.",
            ),
            ErrorAttributionRule(
                id="transformation_error_derives_process_and_answer_errors",
                produces_error_type=ErrorType.TRANSFORMATION_ERROR,
                root_when_tags=("low_transformation", "required_missed"),
                derived_errors=(ErrorType.PROCESS_GAP, ErrorType.CALCULATION_ERROR),
                action_type="transformation_drill",
                explanation_template="A wrong transformation can make later steps wrong even when the trigger is recognized.",
            ),
            ErrorAttributionRule(
                id="calculation_error_derives_final_answer_error",
                produces_error_type=ErrorType.CALCULATION_ERROR,
                root_when_tags=("low_calculation", "constant_C"),
                action_type="calculation_repair",
                explanation_template="Calculation errors can make the final answer wrong without invalidating the method.",
            ),
            ErrorAttributionRule(
                id="condition_miss_not_calculation_error",
                produces_error_type=ErrorType.CONDITION_MISS,
                root_when_tags=("initial_value_resolution",),
                suppresses=(ErrorType.CALCULATION_ERROR,),
                action_type="condition_check",
                explanation_template="Missing an initial condition makes the answer incomplete but is not a pure calculation error.",
            ),
            ErrorAttributionRule(
                id="expression_weakness_not_concept_gap",
                produces_error_type=ErrorType.EXPRESSION_WEAKNESS,
                root_when_tags=("low_expression", "concept_ok"),
                suppresses=(ErrorType.CONCEPT_GAP,),
                action_type="expression_rewrite",
                explanation_template="Weak expression should not become concept gap when the concept evidence is adequate.",
            ),
            ErrorAttributionRule(
                id="rule_only_needs_more_evidence",
                produces_error_type=ErrorType.TRIGGER_FAILURE,
                root_when_tags=("rule_only",),
                action_type="need_more_evidence",
                explanation_template="Rule-only evidence is too weak for a strong root-cause diagnosis.",
            ),
        )
    )

    def select_root_cause(
        self,
        errors: list[ErrorItem],
        score_vector: ScoreVector,
        trace: DiagnosisTrace,
        question: Question,
        node: KnowledgeNode,
    ) -> tuple[ErrorType | None, str]:
        if trace.rule_only:
            return None, "policy_rule_only_needs_more_evidence"
        if trace.surface_keyword_only:
            return None, "policy_surface_keyword_only_needs_more_evidence"
        if not errors:
            return None, "policy_no_error_evidence"
        if trace.optional_only and all(error.weight < self.primary_weight_threshold for error in errors):
            return None, "policy_optional_only_weak_evidence"
        if all(error.weight < self.secondary_weight_threshold for error in errors):
            return None, "policy_only_weak_evidence"

        error_types = {error.error_type for error in errors}
        if ErrorType.CONDITION_MISS in error_types and self._condition_miss_strong_evidence(trace, question):
            return ErrorType.CONDITION_MISS, "policy_condition_miss_strong_evidence"

        if ErrorType.KNOWLEDGE_CONFUSION in error_types and (
            ErrorType.KNOWLEDGE_CONFUSION in node.common_errors or self._has_logic_contradiction_for(trace, "misconception_guard")
        ):
            return ErrorType.KNOWLEDGE_CONFUSION, "policy_supported_knowledge_confusion"

        if ErrorType.SYNTHESIS_FAILURE in error_types and self._synthesis_context(question, node):
            return ErrorType.SYNTHESIS_FAILURE, "policy_synthesis_context"

        if ErrorType.EXPRESSION_WEAKNESS in error_types and self._concept_is_not_low(score_vector):
            if self._only_error_family(errors, {ErrorType.EXPRESSION_WEAKNESS}):
                return ErrorType.EXPRESSION_WEAKNESS, "policy_expression_weakness_with_concept_ok"

        for error_type in self.root_priority:
            if error_type not in error_types:
                continue
            if self._root_supported(error_type, score_vector, trace, question, node):
                return error_type, f"policy_root_priority_{error_type.value}"

        top_error = sorted(errors, key=lambda error: error.weight, reverse=True)[0]
        if top_error.weight < self.primary_weight_threshold:
            return None, "policy_no_primary_strength_root"
        if not self._root_supported(top_error.error_type, score_vector, trace, question, node):
            return None, f"policy_no_supported_root_{top_error.error_type.value}"
        return top_error.error_type, "policy_fallback_top_weight"

    def role_for_error(self, error_type: ErrorType, root_cause: ErrorType | None) -> str:
        if root_cause is None:
            return "secondary"
        if error_type == root_cause:
            return "root"
        if error_type in self.derived_by_root.get(root_cause, ()):
            return "derived"
        return "secondary"

    def adjusted_weight(self, error: ErrorItem, role: str, root_cause: ErrorType | None) -> float:
        if role == "root":
            return max(error.weight, 0.9)
        if role == "derived":
            return min(error.weight, 0.6)
        if root_cause == ErrorType.EXPRESSION_WEAKNESS and error.error_type == ErrorType.CONCEPT_GAP:
            return min(error.weight, 0.35)
        return min(error.weight, 0.65)

    def confidence(
        self,
        root_cause: ErrorType | None,
        trace: DiagnosisTrace,
        evidence_count: int,
    ) -> float:
        if trace.rule_only or trace.surface_keyword_only:
            return self.rule_only_confidence_cap
        if root_cause is None:
            return self.no_evidence_confidence
        if trace.logic_contradictions:
            return min(0.88, 0.72 + 0.03 * min(len(trace.logic_contradictions), 4))
        if evidence_count >= 4 and any(name in trace.active_scorers for name in ("RubricScorer", "MathValidatorScorer")):
            return 0.86
        if evidence_count >= 2:
            return 0.72
        return 0.55

    def action_type_for(self, root_cause: ErrorType | None, trace: DiagnosisTrace) -> str:
        if trace.rule_only or trace.surface_keyword_only or root_cause is None:
            return "need_more_evidence"
        return self.action_by_error.get(root_cause, "current_node_review")

    def final_answer_is_downstream(self, root_cause: ErrorType | None) -> bool:
        return root_cause in {
            ErrorType.CALCULATION_ERROR,
            ErrorType.METHOD_ERROR,
            ErrorType.TRANSFORMATION_ERROR,
            ErrorType.CONDITION_MISS,
            ErrorType.TRIGGER_FAILURE,
        }

    def _root_supported(
        self,
        error_type: ErrorType,
        score_vector: ScoreVector,
        trace: DiagnosisTrace,
        question: Question,
        node: KnowledgeNode,
    ) -> bool:
        if error_type == ErrorType.TRIGGER_FAILURE:
            return (
                self._score_below(score_vector, ScoreDimension.TRIGGER, 60)
                or self._has_required_miss_for(trace, "trigger")
                or self._has_logic_contradiction_for(trace, "trigger_pattern")
            )
        if error_type == ErrorType.METHOD_ERROR:
            if self._has_required_miss_for(trace, "method"):
                return True
            if self._has_logic_contradiction_for(trace, "method_step"):
                return True
            if self._score_below(score_vector, ScoreDimension.METHOD, 60):
                return not self._downstream_solution_chain_strong(score_vector)
            return False
        if error_type == ErrorType.TRANSFORMATION_ERROR:
            return (
                self._score_below(score_vector, ScoreDimension.TRANSFORMATION, 60)
                or self._has_required_miss_for(trace, "transformation")
                or self._has_logic_contradiction_for(trace, "transformation_rule")
            )
        if error_type == ErrorType.CALCULATION_ERROR:
            if self._score_below(score_vector, ScoreDimension.TRIGGER, 60):
                return False
            if self._score_below(score_vector, ScoreDimension.METHOD, 60):
                return False
            if self._score_below(score_vector, ScoreDimension.TRANSFORMATION, 60):
                return False
            return self._score_below(score_vector, ScoreDimension.CALCULATION, 70) or "constant_C" in trace.validator_flags
        if error_type == ErrorType.CONDITION_MISS:
            return self._condition_miss_strong_evidence(trace, question)
        if error_type == ErrorType.EXPRESSION_WEAKNESS:
            return self._score_below(score_vector, ScoreDimension.EXPRESSION, 70) and self._concept_is_not_low(score_vector)
        if error_type == ErrorType.SYNTHESIS_FAILURE:
            return self._synthesis_context(question, node)
        if error_type == ErrorType.KNOWLEDGE_CONFUSION:
            return ErrorType.KNOWLEDGE_CONFUSION in node.common_errors or self._has_logic_contradiction_for(trace, "misconception_guard")
        return True

    def _downstream_solution_chain_strong(self, score_vector: ScoreVector) -> bool:
        strong_dimensions = (
            ScoreDimension.TRANSFORMATION,
            ScoreDimension.PROCESS,
            ScoreDimension.CALCULATION,
            ScoreDimension.FINAL_ANSWER,
        )
        available_scores = []
        for dimension in strong_dimensions:
            dimension_score = score_vector.get_dimension(dimension)
            if dimension_score is not None and dimension_score.score is not None:
                available_scores.append(dimension_score.score)
        return len(available_scores) >= 3 and all(score >= 80 for score in available_scores)

    def _score_below(self, score_vector: ScoreVector, dimension: ScoreDimension, threshold: float) -> bool:
        dimension_score = score_vector.get_dimension(dimension)
        return dimension_score is not None and dimension_score.score is not None and dimension_score.score < threshold

    def _concept_is_not_low(self, score_vector: ScoreVector) -> bool:
        concept = score_vector.get_dimension(ScoreDimension.CONCEPT)
        return concept is None or concept.score is None or concept.score >= 60

    def _has_required_miss_for(self, trace: DiagnosisTrace, dimension_name: str) -> bool:
        needle = dimension_name.lower()
        return any(needle in item.lower() for item in trace.required_missed)

    def _has_logic_contradiction_for(self, trace: DiagnosisTrace, ability_kind: str) -> bool:
        needle = f":{ability_kind}:"
        return any(needle in item for item in trace.logic_contradictions)

    def _condition_miss_strong_evidence(self, trace: DiagnosisTrace, question: Question) -> bool:
        if "initial_value_resolution" in trace.validator_flags:
            return True
        if any(
            token in item.lower()
            for item in trace.required_missed
            for token in ("initial_condition", "initial", "ivp", "condition_check", "constant_resolution")
        ):
            return True
        return bool(
            question.metadata.get("requires_initial_condition")
            or question.metadata.get("requires_condition_check")
        ) and any(
            token in trace.validator_flags or any(token in item.lower() for item in trace.required_missed)
            for token in ("initial_value_resolution", "condition_check", "initial")
        )

    def _only_error_family(self, errors: list[ErrorItem], allowed: set[ErrorType]) -> bool:
        return bool(errors) and all(error.error_type in allowed for error in errors)

    def _synthesis_context(self, question: Question, node: KnowledgeNode) -> bool:
        return (
            node.type.value in {"application", "synthesis"}
            or question.question_type == QuestionType.EXAM
            or ErrorType.SYNTHESIS_FAILURE in node.common_errors
        )
