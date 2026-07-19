from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.classroom.models import ContentBlock, utc_now


FORBIDDEN_SESSION_KEYS = {
    "ability_profile",
    "boss_challenge",
    "diagnosis",
    "mastery_state",
    "recommended_next_step",
    "review_schedule",
    "score",
}


class StrictSessionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExpansionRepresentation(str, Enum):
    ANIMATED_VISUAL = "animated_visual"
    ANNOTATED_DIAGRAM = "annotated_diagram"
    SMALLER_EXAMPLE = "smaller_example"
    COUNTEREXAMPLE = "counterexample"
    STEP_BY_STEP_DERIVATION = "step_by_step_derivation"
    CONCRETE_ANALOGY = "concrete_analogy"
    LOWER_ABSTRACTION = "lower_abstraction"


class BaselineStepSnapshot(StrictSessionModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")
    title: str = Field(min_length=1, max_length=240)
    blocks: list[ContentBlock] = Field(min_length=1)


class ModelCommand(StrictSessionModel):
    instance_id: str = Field(min_length=1, max_length=120)
    kind: Literal[
        "set_state",
        "perform_action",
        "update_parameters",
        "highlight_target",
        "clear_highlight",
        "reset",
    ]
    target: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class DetailedExpansion(StrictSessionModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")
    title: str = Field(min_length=1, max_length=240)
    parent_content_id: str = Field(min_length=1, max_length=120)
    parent_expansion_id: str | None = Field(default=None, max_length=120)
    learner_question: str = Field(min_length=1, max_length=4000)
    preserved_context: list[str] = Field(default_factory=list, max_length=20)
    focus_relation: str = Field(min_length=1, max_length=2000)
    representation: ExpansionRepresentation
    blocks: list[ContentBlock] = Field(min_length=1, max_length=40)
    model_commands: list[ModelCommand] = Field(default_factory=list, max_length=30)
    return_connection: str = Field(min_length=1, max_length=4000)

    @model_validator(mode="before")
    @classmethod
    def reject_learner_analysis(cls, value: Any) -> Any:
        _reject_forbidden_keys(value)
        return value


class ScenePatch(StrictSessionModel):
    expected_revision: int = Field(ge=1)
    pedagogical_intent: str = Field(min_length=1, max_length=2000)
    expansion: DetailedExpansion


class LearningSession(StrictSessionModel):
    schema_version: Literal["learning_session_v1"] = "learning_session_v1"
    session_id: str = Field(pattern=r"^ls-[a-f0-9]{20}$")
    package_id: str
    release_version: str
    module_id: str
    revision: int = Field(ge=1)
    baseline_steps: list[BaselineStepSnapshot] = Field(min_length=1)
    revealed_step_ids: list[str] = Field(min_length=1)
    active_content_id: str
    expansions: list[DetailedExpansion] = Field(default_factory=list)
    expansion_stack: list[str] = Field(default_factory=list)
    model_state: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)


class LearningSessionAccess(StrictSessionModel):
    session: LearningSession
    access_token: str


class StoredLearningSession(StrictSessionModel):
    session: LearningSession
    access_token_hash: str


class LearningSessionEvent(StrictSessionModel):
    event_id: int
    session_id: str
    revision: int
    kind: Literal[
        "session.created",
        "baseline.revealed",
        "scene.expanded",
        "scene.returned",
        "focus.changed",
    ]
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)


def _reject_forbidden_keys(value: Any, path: str = "expansion") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in FORBIDDEN_SESSION_KEYS:
                raise ValueError(
                    f"learning session cannot contain learner-analysis field "
                    f"{key!r} at {child_path}"
                )
            _reject_forbidden_keys(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_keys(child, f"{path}[{index}]")
