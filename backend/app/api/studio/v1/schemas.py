from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

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
