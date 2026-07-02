from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.core.enums import ErrorType, ScoreDimension
from app.core.schemas import (
    Attempt,
    CompositeScoreResult,
    DiagnosisResult,
    DimensionScore,
    ErrorItem,
    ErrorVector,
    ForwardDecision,
    KnowledgeNode,
    Question,
    RecommendedAction,
    RollbackDecision,
)


FORBIDDEN_PUBLIC_FIELDS = {
    "score_overrides",
    "evidence_overrides",
    "manual_override",
    "scenario",
}


class ApiError(BaseModel):
    error_code: str
    message: str
    field_path: str | None = None
    request_id: str | None = None


class ApiOptions(BaseModel):
    include_debug: bool = False


class AttemptEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    question: Question
    attempt: Attempt
    options: ApiOptions = Field(default_factory=ApiOptions)

    @model_validator(mode="after")
    def validate_references(self) -> "AttemptEvaluationRequest":
        if self.question.node_id != self.node_id:
            raise ValueError("question.node_id must match node_id")
        if self.attempt.question_id != self.question.id:
            raise ValueError("attempt.question_id must match question.id")
        return self


def api_error(status_code: int, error_code: str, message: str, field_path: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ApiError(error_code=error_code, message=message, field_path=field_path).model_dump(exclude_none=True),
    )


def find_forbidden_public_field(value: Any, path: str = "$") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_PUBLIC_FIELDS:
                return child_path
            nested = find_forbidden_public_field(child, child_path)
            if nested:
                return nested
    elif isinstance(value, list):
        for index, child in enumerate(value):
            nested = find_forbidden_public_field(child, f"{path}[{index}]")
            if nested:
                return nested
    return None


def parse_attempt_request_payload(payload: dict[str, Any]) -> AttemptEvaluationRequest:
    forbidden_path = find_forbidden_public_field(payload)
    if forbidden_path:
        raise api_error(
            status_code=400,
            error_code="forbidden_public_api_field",
            message="Public API requests must not include override or scenario fields.",
            field_path=forbidden_path,
        )
    try:
        return AttemptEvaluationRequest.model_validate(payload)
    except ValidationError as exc:
        first_error = exc.errors()[0] if exc.errors() else {}
        loc = first_error.get("loc", ())
        field_path = ".".join(str(item) for item in loc) if loc else None
        message = str(first_error.get("msg", "Invalid request schema."))
        if "question.node_id must match node_id" in message:
            raise api_error(422, "question_node_mismatch", message, field_path)
        if "attempt.question_id must match question.id" in message:
            raise api_error(422, "attempt_question_mismatch", message, field_path)
        raise api_error(422, "request_schema_invalid", message, field_path)


def model_to_json(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if isinstance(value, list):
        return [model_to_json(item) for item in value]
    if isinstance(value, dict):
        return {str(key): model_to_json(item) for key, item in value.items()}
    return value


def score_vector_summary(score_result: CompositeScoreResult | DiagnosisResult) -> dict[str, Any]:
    score_vector = score_result.score_vector
    summary: dict[str, Any] = {}
    for dimension, dimension_score in score_vector.as_dimension_map().items():
        summary[dimension.value] = dimension_score_summary(dimension_score)
    return summary


def dimension_score_summary(dimension_score: DimensionScore | None) -> dict[str, Any] | None:
    if dimension_score is None or dimension_score.score is None:
        return None
    payload: dict[str, Any] = {"score": dimension_score.score}
    if dimension_score.notes:
        payload["notes"] = dimension_score.notes
    return payload


def active_scorers(score_result: CompositeScoreResult) -> list[str]:
    return score_result.get_active_scorer_names()


def dimension_sources(score_result: CompositeScoreResult) -> dict[str, list[str]]:
    return {dimension.value: sources for dimension, sources in score_result.get_dimension_sources().items()}


def sanitized_error_item(error: ErrorItem) -> dict[str, Any]:
    return {
        "error_type": error.error_type.value,
        "weight": error.weight,
        "related_dimensions": [dimension.value for dimension in error.related_dimensions],
        "is_primary": error.is_primary,
        "suggested_rollback_level": error.suggested_rollback_level.value,
    }


def sanitized_error_vector(error_vector: ErrorVector) -> list[dict[str, Any]]:
    return [sanitized_error_item(error) for error in error_vector.errors]


def action_payloads(actions: list[RecommendedAction]) -> list[dict[str, Any]]:
    return [action.model_dump(mode="json", exclude_none=True) for action in actions]


def error_type_values(errors: list[ErrorType]) -> list[str]:
    return [error.value for error in errors]


def build_score_response(score_result: CompositeScoreResult, include_debug: bool = False) -> dict[str, Any]:
    response: dict[str, Any] = {
        "scoring": {
            "score_vector": score_vector_summary(score_result),
            "active_scorers": active_scorers(score_result),
            "dimension_sources": dimension_sources(score_result),
        }
    }
    if include_debug:
        response["debug"] = {
            "scorer_results": model_to_json(score_result.scorer_results),
            "merge_notes": list(score_result.merge_notes),
        }
    return response


def build_diagnosis_section(diagnosis_result: DiagnosisResult) -> dict[str, Any]:
    return {
        "pass_state": diagnosis_result.pass_state.value,
        "error_vector": sanitized_error_vector(diagnosis_result.error_vector),
        "root_cause": diagnosis_result.root_cause.value if diagnosis_result.root_cause else None,
        "primary_errors": error_type_values(diagnosis_result.primary_errors),
        "secondary_errors": error_type_values(diagnosis_result.secondary_errors),
        "derived_errors": error_type_values(diagnosis_result.derived_errors),
        "downstream_result_errors": error_type_values(diagnosis_result.downstream_result_errors),
        "weak_signal_errors": error_type_values(diagnosis_result.weak_signal_errors),
        "evidence_gap_errors": error_type_values(diagnosis_result.evidence_gap_errors),
        "confidence": diagnosis_result.confidence,
        "learner_explanation": diagnosis_result.learner_explanation,
        "recommended_actions": action_payloads(diagnosis_result.recommended_actions),
    }


def build_movement_section(
    rollback_decision: RollbackDecision,
    forward_decision: ForwardDecision,
) -> dict[str, Any]:
    return {
        "rollback_required": bool(rollback_decision.rollback_nodes),
        "rollback_nodes": list(rollback_decision.rollback_nodes),
        "forward_allowed": bool(forward_decision.forward_nodes),
        "forward_nodes": list(forward_decision.forward_nodes),
    }


def build_action_section(next_action_hint: str, diagnosis_result: DiagnosisResult) -> dict[str, Any]:
    return {
        "next_action_hint": next_action_hint,
        "next_action_type": diagnosis_result.recommended_actions[0].action_type if diagnosis_result.recommended_actions else None,
    }


def build_debug_section(
    score_result: CompositeScoreResult,
    diagnosis_result: DiagnosisResult,
    rollback_decision: RollbackDecision,
    forward_decision: ForwardDecision,
    *,
    rollback_consistent: bool,
    forward_consistent: bool,
) -> dict[str, Any]:
    trace = diagnosis_result.diagnosis_trace
    return {
        "scorer_results": model_to_json(score_result.scorer_results),
        "merge_notes": list(score_result.merge_notes),
        "evidence_sources": model_to_json(diagnosis_result.evidence_sources),
        "diagnosis_trace": model_to_json(trace) if trace else None,
        "policy_hits": list(trace.policy_hits) if trace else [],
        "debug_explanation": diagnosis_result.explanation,
        "error_chain": model_to_json(diagnosis_result.error_chain),
        "raw_rollback_level": rollback_decision.level.value,
        "raw_forward_level": forward_decision.level.value,
        "rollback_decision": model_to_json(rollback_decision),
        "forward_decision": model_to_json(forward_decision),
        "movement_consistency": {
            "rollback_matches_diagnosis_result": rollback_consistent,
            "forward_matches_diagnosis_result": forward_consistent,
        },
    }


def build_attempt_response(orchestrated: Any, include_debug: bool = False, include_node: bool = False) -> dict[str, Any]:
    response: dict[str, Any] = {
        "scoring": build_score_response(orchestrated.score_result, include_debug=False)["scoring"],
        "diagnosis": build_diagnosis_section(orchestrated.diagnosis_result),
        "movement": build_movement_section(orchestrated.rollback_decision, orchestrated.forward_decision),
        "action": build_action_section(orchestrated.next_action_hint, orchestrated.diagnosis_result),
    }
    if include_node:
        response["node"] = model_to_json(orchestrated.node)
    if include_debug:
        response["debug"] = build_debug_section(
            orchestrated.score_result,
            orchestrated.diagnosis_result,
            orchestrated.rollback_decision,
            orchestrated.forward_decision,
            rollback_consistent=orchestrated.rollback_consistent,
            forward_consistent=orchestrated.forward_consistent,
        )
    return response


def build_next_action_response(orchestrated: Any, include_debug: bool = False) -> dict[str, Any]:
    response = {
        "pass_state": orchestrated.diagnosis_result.pass_state.value,
        "root_cause": orchestrated.diagnosis_result.root_cause.value if orchestrated.diagnosis_result.root_cause else None,
        "recommended_actions": action_payloads(orchestrated.diagnosis_result.recommended_actions),
        "next_action_hint": orchestrated.next_action_hint,
        "rollback_required": bool(orchestrated.rollback_decision.rollback_nodes),
        "rollback_nodes": list(orchestrated.rollback_decision.rollback_nodes),
        "forward_allowed": bool(orchestrated.forward_decision.forward_nodes),
        "forward_nodes": list(orchestrated.forward_decision.forward_nodes),
    }
    if include_debug:
        response["debug"] = build_debug_section(
            orchestrated.score_result,
            orchestrated.diagnosis_result,
            orchestrated.rollback_decision,
            orchestrated.forward_decision,
            rollback_consistent=orchestrated.rollback_consistent,
            forward_consistent=orchestrated.forward_consistent,
        )
    return response
