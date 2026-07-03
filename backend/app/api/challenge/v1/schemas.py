from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.api.v1.schemas import api_error
from app.training.session_log import validate_session_id


class ChallengeStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter_id: str = "ode_network_mvp"
    session_id: str

    @field_validator("session_id")
    @classmethod
    def validate_start_session_id(cls, value: str) -> str:
        return validate_session_id(value)


class ChallengeSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    answer: str = Field(min_length=1)
    steps: list[str] = Field(default_factory=list)
    explanation: str | None = None

    @field_validator("session_id")
    @classmethod
    def validate_submit_session_id(cls, value: str) -> str:
        return validate_session_id(value)


class ChallengeResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    node_id: str | None = None
    reset_all: bool = True

    @field_validator("session_id")
    @classmethod
    def validate_reset_session_id(cls, value: str) -> str:
        return validate_session_id(value)


class ChapterDraftValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown: str = Field(min_length=1)


class ChapterDraftHumanReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown: str = Field(min_length=1)
    reviewer: str = Field(min_length=1, max_length=80)
    decision: Literal["request_changes", "approve_for_candidate"]
    checklist: dict[str, bool] = Field(default_factory=dict)
    notes: str | None = None


class ChapterDraftCandidateDryRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    markdown: str = Field(min_length=1)
    reviewer: str = Field(min_length=1, max_length=80)
    decision: Literal["request_changes", "approve_for_candidate"]
    checklist: dict[str, bool] = Field(default_factory=dict)
    notes: str | None = None


class ChapterControlledPublishRequest(ChapterDraftCandidateDryRunRequest):
    allow_write: bool = False
    approval_phrase: str | None = None
    expected_publish_plan_hash: str | None = None


def parse_request(model: type[BaseModel], payload: dict[str, Any]) -> BaseModel:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        first_error = exc.errors()[0] if exc.errors() else {}
        loc = first_error.get("loc", ())
        field_path = ".".join(str(item) for item in loc) if loc else None
        message = str(first_error.get("msg", "Invalid challenge request schema."))
        raise api_error(422, "challenge_request_schema_invalid", message, field_path)
