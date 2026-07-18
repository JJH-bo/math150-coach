from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.classroom.model_contracts import PreviewViewport, TeachingModelManifest
from app.classroom.models import ClassroomPackage


class StudioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateDraftRequest(StudioRequest):
    draft_id: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,119}$")
    package: ClassroomPackage


class UpdateDraftRequest(StudioRequest):
    expected_revision: int = Field(ge=1)
    package: ClassroomPackage


class PublishDraftRequest(StudioRequest):
    expected_revision: int = Field(ge=1)


class RollbackPackageRequest(StudioRequest):
    version: str = Field(pattern=r"^r-[a-f0-9]{16}$")


class CreateModelDraftRequest(StudioRequest):
    draft_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,79}$")
    manifest: TeachingModelManifest
    source: str = Field(min_length=1, max_length=1_000_000)


class UpdateModelDraftRequest(StudioRequest):
    expected_revision: int = Field(ge=1)
    manifest: TeachingModelManifest
    source: str = Field(min_length=1, max_length=1_000_000)


class RequestModelPreviewRequest(StudioRequest):
    scenario_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,79}$")
    viewport: PreviewViewport


class RegisterModelRequest(StudioRequest):
    expected_revision: int = Field(ge=1)
