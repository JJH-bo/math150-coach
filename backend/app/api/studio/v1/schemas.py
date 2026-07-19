from __future__ import annotations

from typing import Literal

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


class WorkspaceModuleSummary(StudioRequest):
    id: str
    title: str
    summary: str | None = None


class WorkspaceChapterSummary(StudioRequest):
    id: str
    title: str
    modules: list[WorkspaceModuleSummary]


class WorkspaceCourseSummary(StudioRequest):
    id: str
    title: str
    chapters: list[WorkspaceChapterSummary]


class WorkspaceActivePackage(StudioRequest):
    package_id: str
    title: str
    active_version: str
    content_hash: str
    courses: list[WorkspaceCourseSummary]


class WorkspaceClassroomDraft(StudioRequest):
    draft_id: str
    revision: int = Field(ge=1)
    content_hash: str
    package_id: str
    title: str
    courses: list[WorkspaceCourseSummary]


class WorkspaceRegisteredModel(StudioRequest):
    model_id: str
    version: str
    content_hash: str
    manifest: TeachingModelManifest


class WorkspaceAuthoringPolicy(StudioRequest):
    routine_authoring_requires_confirmation: Literal[False]
    publish_after_validation: Literal[True]
    discover_identifiers_before_writes: Literal[True]
    ask_user_for_internal_identifiers: Literal[False]
    learner_analysis_capabilities: list[str] = Field(max_length=0)
    rollback_scope: Literal[
        "explicit_request_or_failed_just_published_release"
    ]


class StudioWorkspaceResponse(StudioRequest):
    studio_version: Literal["studio_v1"]
    public_origin: str
    learner_entry_url: str
    active_packages: list[WorkspaceActivePackage]
    drafts: list[WorkspaceClassroomDraft]
    registered_models: list[WorkspaceRegisteredModel]
    authoring_policy: WorkspaceAuthoringPolicy
