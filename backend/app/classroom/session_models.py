from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.classroom.models import (
    ContentBlock,
    ContentBlockKind,
    ExpansionRepresentation,
    utc_now,
)


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


class BaselineStepSnapshot(StrictSessionModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")
    title: str = Field(min_length=1, max_length=240)
    question_answered: str | None = Field(default=None, max_length=1000)
    bridge_from_previous: str | None = Field(default=None, max_length=3000)
    mechanism: str | None = Field(default=None, max_length=5000)
    entry_assumptions: list[str] = Field(default_factory=list, max_length=20)
    exit_understanding: str | None = Field(default=None, max_length=2000)
    knowledge_point_ids: list[str] = Field(default_factory=list)
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
    learning_obstacle: str = Field(min_length=12, max_length=3000)
    previous_explanation_limit: str = Field(min_length=12, max_length=3000)
    focus_relation: str = Field(min_length=1, max_length=2000)
    representation: ExpansionRepresentation
    bridge_steps: list[str] = Field(min_length=2, max_length=12)
    understanding_target: str = Field(min_length=12, max_length=3000)
    blocks: list[ContentBlock] = Field(min_length=1, max_length=40)
    model_commands: list[ModelCommand] = Field(default_factory=list, max_length=30)
    return_connection: str = Field(min_length=1, max_length=4000)

    @model_validator(mode="before")
    @classmethod
    def reject_learner_analysis(cls, value: Any) -> Any:
        _reject_forbidden_keys(value)
        return value

    @model_validator(mode="after")
    def require_substantive_re_design(self) -> "DetailedExpansion":
        if len(self.blocks) >= 2:
            return self
        block = self.blocks[0]
        steps = block.data.get("steps")
        if (
            block.kind
            in {
                ContentBlockKind.DERIVATION,
                ContentBlockKind.WORKED_EXAMPLE,
            }
            and isinstance(steps, list)
            and len(steps) >= 3
        ):
            return self
        raise ValueError(
            "detailed expansion must be a substantive re-design with either "
            "multiple complementary blocks or a complete multi-step example"
        )


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
