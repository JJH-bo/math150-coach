from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ContentBlockKind(str, Enum):
    PROSE = "prose"
    HEADING = "heading"
    CALLOUT = "callout"
    MATH = "math"
    FORMULA_EXPLANATION = "formula_explanation"
    DERIVATION = "derivation"
    COMPARISON = "comparison"
    WORKED_EXAMPLE = "worked_example"
    CODE_EXPLANATION = "code_explanation"
    TABLE = "table"
    MATRIX = "matrix"
    IMAGE = "image"
    MODEL_REFERENCE = "model_reference"
    GROUP = "group"


class SourceAnchor(StrictModel):
    asset_id: str
    filename: str | None = None
    page: str | None = None
    section: str | None = None
    source_span: str | None = None
    note: str | None = None


class DetailBranch(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    blocks: list["ContentBlock"] = Field(min_length=1)


class ContentBlock(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    kind: ContentBlockKind
    data: dict[str, Any]
    source_anchor: SourceAnchor | None = None
    detail_branches: list[DetailBranch] = Field(default_factory=list)


class LearningSegment(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    title: str | None = Field(default=None, max_length=240)
    blocks: list[ContentBlock] = Field(min_length=1)


class CoreModule(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    summary: str | None = None
    blocks: list[ContentBlock] = Field(default_factory=list)
    segments: list[LearningSegment] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_content(self) -> "CoreModule":
        if not self.blocks and not self.segments:
            raise ValueError("core module requires at least one block or segment")
        return self


class ModuleRelationKind(str, Enum):
    PREREQUISITE_CONTEXT = "prerequisite_context"
    CONCEPTUAL_DEPENDENCY = "conceptual_dependency"
    CONTRAST = "contrast"
    ANALOGY = "analogy"
    DERIVATION = "derivation"
    APPLICATION = "application"
    SHARED_MODEL = "shared_model"
    CHAPTER_SYNTHESIS = "chapter_synthesis"


class ModuleRelation(StrictModel):
    id: str
    kind: ModuleRelationKind
    source_module_id: str
    target_module_id: str
    label: str | None = None


class Chapter(StrictModel):
    id: str
    title: str
    modules: list[CoreModule] = Field(min_length=1)
    relations: list[ModuleRelation] = Field(default_factory=list)


class Course(StrictModel):
    id: str
    title: str
    chapters: list[Chapter] = Field(min_length=1)


class ModelInstanceReference(StrictModel):
    instance_id: str
    model_id: str
    model_version: str
    preset: str | None = None
    initial_state: dict[str, Any] = Field(default_factory=dict)


class AssetReference(StrictModel):
    asset_id: str
    media_type: str
    uri: str
    content_hash: str | None = None


class ClassroomPackage(StrictModel):
    schema_version: Literal["classroom_package_v1"]
    package_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,79}$")
    title: str = Field(min_length=1, max_length=240)
    courses: list[Course] = Field(min_length=1)
    model_instances: list[ModelInstanceReference] = Field(default_factory=list)
    assets: list[AssetReference] = Field(default_factory=list)


class DraftRecord(StrictModel):
    draft_id: str
    revision: int = Field(ge=1)
    content_hash: str
    package: ClassroomPackage


class ReleaseRecord(StrictModel):
    package_id: str
    version: str
    content_hash: str
    package: ClassroomPackage


class ActivationReceipt(StrictModel):
    action: Literal["publish", "rollback"]
    package_id: str
    active_version: str
    previous_version: str | None = None
    content_hash: str
    activated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
