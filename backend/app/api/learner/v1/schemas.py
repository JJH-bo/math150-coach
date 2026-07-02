from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.api.v1.schemas import api_error
from app.catalog.models import validate_question_id


SENSITIVE_LEARNER_FIELDS = {
    "expected_answer",
    "rubric",
    "solution_outline",
    "answer_key",
    "answer_aliases",
    "validator_config",
    "scoring_notes_internal",
    "golden_case_refs",
    "authoring_metadata",
    "score_overrides",
    "evidence_overrides",
    "manual_override",
    "scenario",
    "include_debug",
    "debug",
    "scorer_results",
    "diagnosis_trace",
    "evidence_sources",
    "raw_rollback_level",
    "raw_forward_level",
}


class LearnerAttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    user_answer: str = Field(min_length=1)
    response_steps: list[str] = Field(default_factory=list)
    self_explanation: str | None = None

    @field_validator("question_id")
    @classmethod
    def validate_request_question_id(cls, value: str) -> str:
        return validate_question_id(value)


def find_sensitive_learner_field(value: Any, path: str = "$") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in SENSITIVE_LEARNER_FIELDS:
                return child_path
            nested = find_sensitive_learner_field(child, child_path)
            if nested:
                return nested
    elif isinstance(value, list):
        for index, child in enumerate(value):
            nested = find_sensitive_learner_field(child, f"{path}[{index}]")
            if nested:
                return nested
    return None


def parse_learner_attempt_payload(payload: dict[str, Any]) -> LearnerAttemptRequest:
    forbidden_path = find_sensitive_learner_field(payload)
    if forbidden_path:
        raise api_error(
            status_code=400,
            error_code="forbidden_learner_api_field",
            message="Learner requests must not include trusted scoring, debug, scenario, or override fields.",
            field_path=forbidden_path,
        )
    try:
        return LearnerAttemptRequest.model_validate(payload)
    except ValidationError as exc:
        first_error = exc.errors()[0] if exc.errors() else {}
        loc = first_error.get("loc", ())
        field_path = ".".join(str(item) for item in loc) if loc else None
        message = str(first_error.get("msg", "Invalid learner request schema."))
        raise api_error(422, "learner_request_schema_invalid", message, field_path)

