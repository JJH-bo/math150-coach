from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictToolModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ToolScope(str, Enum):
    READ = "studio.read"
    COMPUTE = "studio.compute"
    RENDER = "studio.render"
    AUTHOR = "studio.author"
    PUBLISH = "studio.publish"
    ROLLBACK = "studio.rollback"
    ADMIN_TOOLS = "studio.admin_tools"


class ToolQualityTier(str, Enum):
    VERIFIED = "verified"
    PREVIEWED = "previewed"
    EXPERIMENTAL = "experimental"


class ToolExecutionMode(str, Enum):
    SYNC = "sync"
    ASYNC = "async"


class ToolJobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ToolDefinition(StrictToolModel):
    tool_id: str = Field(pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
    version: str = Field(pattern=r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=2000)
    category: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,79}$")
    quality_tier: ToolQualityTier
    required_scope: ToolScope
    execution_mode: ToolExecutionMode
    deterministic: bool
    cacheable: bool
    timeout_seconds: int = Field(ge=1, le=3600)
    max_artifacts: int = Field(ge=1, le=128)
    max_artifact_bytes: int = Field(ge=1, le=1_073_741_824)
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    output_media_types: list[str] = Field(min_length=1, max_length=32)
    quality_gates: list[str] = Field(min_length=1, max_length=32)
    upstream_project: str = Field(min_length=1, max_length=500)
    license: str = Field(min_length=1, max_length=100)

    @field_validator("input_schema", "output_schema")
    @classmethod
    def require_object_schema(cls, value: dict[str, Any]) -> dict[str, Any]:
        if value.get("type") != "object":
            raise ValueError("tool schemas must declare type=object")
        return value

    @field_validator("output_media_types", "quality_gates")
    @classmethod
    def require_unique_nonblank_values(cls, value: list[str]) -> list[str]:
        if any(not item.strip() for item in value):
            raise ValueError("tool metadata values cannot be blank")
        if len(set(value)) != len(value):
            raise ValueError("tool metadata values must be unique")
        return value


class ToolArtifact(StrictToolModel):
    name: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")
    media_type: str = Field(min_length=1, max_length=160)
    size_bytes: int = Field(ge=0)
    sha256: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    download_path: str = Field(min_length=1, max_length=500)


class ToolProducedArtifact(StrictToolModel):
    name: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")
    media_type: str = Field(min_length=1, max_length=160)
    source_path: str = Field(min_length=1, max_length=500)


class ToolError(StrictToolModel):
    code: str = Field(pattern=r"^[a-z][a-z0-9_]{1,119}$")
    message: str = Field(min_length=1, max_length=4000)
    path: str | None = Field(default=None, max_length=500)
    retryable: bool = False
    repair_hint: str | None = Field(default=None, max_length=2000)


class ToolExecutionResult(StrictToolModel):
    result: dict[str, Any]
    warnings: list[str] = Field(default_factory=list, max_length=100)
    artifacts: list[ToolProducedArtifact] = Field(default_factory=list, max_length=128)
    metrics: dict[str, int | float | str | bool | None] = Field(default_factory=dict)


class ToolJob(StrictToolModel):
    job_id: str = Field(pattern=r"^tj-[a-f0-9]{24}$")
    tool_id: str
    tool_version: str
    required_scope: ToolScope
    state: ToolJobState
    argument_hash: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    arguments: dict[str, Any]
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    cancellation_requested: bool = False
    result: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    error: ToolError | None = None
    artifacts: list[ToolArtifact] = Field(default_factory=list)
    metrics: dict[str, int | float | str | bool | None] = Field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolExecutionContext:
    job_id: str
    work_dir: Path
    is_cancellation_requested: Callable[[], bool] = lambda: False


class ToolAdapter(Protocol):
    definition: ToolDefinition

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult: ...
