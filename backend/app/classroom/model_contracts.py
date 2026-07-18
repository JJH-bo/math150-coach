from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.classroom.hashing import content_hash


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ModelParameterType(str, Enum):
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"
    CHOICE = "choice"


class ModelParameterSpec(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,79}$")
    type: ModelParameterType
    default: Any
    minimum: float | None = None
    maximum: float | None = None
    choices: list[str] = Field(default_factory=list)
    description: str | None = None

    @model_validator(mode="after")
    def validate_default(self) -> "ModelParameterSpec":
        value = self.default
        if self.type == ModelParameterType.NUMBER:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("number default must be numeric")
        elif self.type == ModelParameterType.INTEGER:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("integer default must be an integer")
        elif self.type == ModelParameterType.BOOLEAN:
            if not isinstance(value, bool):
                raise ValueError("boolean default must be boolean")
        elif self.type == ModelParameterType.STRING:
            if not isinstance(value, str):
                raise ValueError("string default must be text")
        elif self.type == ModelParameterType.CHOICE:
            if not self.choices:
                raise ValueError("choice parameter requires choices")
            if value not in self.choices:
                raise ValueError("choice default must be declared")

        if self.minimum is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < self.minimum
        ):
            raise ValueError("default must be at least minimum")
        if self.maximum is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value > self.maximum
        ):
            raise ValueError("default must be at most maximum")
        if (
            self.minimum is not None
            and self.maximum is not None
            and self.minimum > self.maximum
        ):
            raise ValueError("minimum must not exceed maximum")
        return self


class ModelStateSpec(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,79}$")
    title: str = Field(min_length=1, max_length=160)
    description: str | None = None


class ModelActionPayloadField(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,79}$")
    type: ModelParameterType
    required: bool = True


class ModelActionSpec(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,79}$")
    title: str = Field(min_length=1, max_length=160)
    payload_fields: list[ModelActionPayloadField] = Field(default_factory=list)
    description: str | None = None


class ModelScenarioCommandKind(str, Enum):
    SET_STATE = "set_state"
    PERFORM_ACTION = "perform_action"
    UPDATE_PARAMETERS = "update_parameters"
    PAUSE = "pause"
    RESUME = "resume"
    RESET = "reset"


class ModelScenarioCommand(StrictModel):
    kind: ModelScenarioCommandKind
    target: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ModelScenario(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,79}$")
    title: str = Field(min_length=1, max_length=160)
    initial_state: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    commands: list[ModelScenarioCommand] = Field(default_factory=list)


class TeachingModelManifest(StrictModel):
    contract_version: Literal["teaching_model_v1"]
    model_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,79}$")
    title: str = Field(min_length=1, max_length=200)
    purpose: str = Field(min_length=1, max_length=1000)
    domains: list[str] = Field(min_length=1)
    parameters: list[ModelParameterSpec] = Field(default_factory=list)
    states: list[ModelStateSpec] = Field(min_length=1)
    actions: list[ModelActionSpec] = Field(default_factory=list)
    targets: list[str] = Field(default_factory=list)
    interactions: list[str] = Field(default_factory=list)
    viewport_modes: list[str] = Field(min_length=1)
    quality_profiles: list[str] = Field(min_length=1)
    scenarios: list[ModelScenario] = Field(min_length=1)
    fallback_description: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def validate_unique_vocabulary(self) -> "TeachingModelManifest":
        for label, values in (
            ("parameter", self.parameters),
            ("state", self.states),
            ("action", self.actions),
            ("scenario", self.scenarios),
        ):
            ids = [value.id for value in values]
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate {label} id")
        for label, values in (
            ("target", self.targets),
            ("interaction", self.interactions),
            ("viewport mode", self.viewport_modes),
            ("quality profile", self.quality_profiles),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"duplicate {label}")
        return self


def model_content_hash(manifest: TeachingModelManifest, source: str) -> str:
    return content_hash(
        {
            "manifest": manifest.model_dump(mode="json", exclude_none=True),
            "source": source.replace("\r\n", "\n"),
        }
    )


def model_version(manifest: TeachingModelManifest, source: str) -> str:
    return f"m-{model_content_hash(manifest, source).split(':', 1)[1][:16]}"


class ModelDraftRecord(StrictModel):
    draft_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,79}$")
    revision: int = Field(ge=1)
    content_hash: str
    manifest: TeachingModelManifest
    source: str = Field(min_length=1, max_length=1_000_000)
    updated_at: str = Field(default_factory=utc_now)


class RegisteredModelRecord(StrictModel):
    model_id: str
    version: str
    content_hash: str
    manifest: TeachingModelManifest
    source: str
    validation: dict[str, Any] = Field(default_factory=dict)
    preview_job_id: str
    registered_at: str = Field(default_factory=utc_now)


class PreviewViewport(StrictModel):
    width: int = Field(ge=320, le=3840)
    height: int = Field(ge=320, le=2160)
    device_scale_factor: float = Field(default=1, ge=0.5, le=3)


class PreviewArtifact(StrictModel):
    name: str
    media_type: str
    size: int = Field(ge=0)
    content_hash: str


class PreviewError(StrictModel):
    code: str
    message: str
    retryable: bool = False


class PreviewJobRecord(StrictModel):
    job_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,79}$")
    draft_id: str
    draft_revision: int = Field(ge=1)
    draft_content_hash: str
    model_id: str
    scenario_id: str
    viewport: PreviewViewport
    status: Literal["queued", "running", "succeeded", "failed"]
    artifacts: list[PreviewArtifact] = Field(default_factory=list)
    report: dict[str, Any] | None = None
    error: PreviewError | None = None
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)
