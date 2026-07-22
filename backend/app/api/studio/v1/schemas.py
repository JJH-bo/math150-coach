from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.classroom.model_contracts import PreviewViewport, TeachingModelManifest
from app.classroom.models import ClassroomPackage
from app.classroom.session_models import DetailedExpansion
from app.tools.contracts import ToolDefinition


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


class PatchLearningSessionRequest(StudioRequest):
    expected_revision: int = Field(ge=1)
    pedagogical_intent: str = Field(min_length=1, max_length=2000)
    expansion: DetailedExpansion


class ReturnLearningSessionRequest(StudioRequest):
    expected_revision: int = Field(ge=1)


class CreateToolJobRequest(StudioRequest):
    tool_id: str = Field(pattern=r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)+$")
    tool_version: str | None = Field(
        default=None,
        pattern=r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$",
    )
    arguments: dict[str, Any]


class StudioToolListResponse(StudioRequest):
    tools: list[ToolDefinition]
    total: int = Field(ge=0)


class ChapterAuthoringCapabilities(StudioRequest):
    requires_source_sections: Literal[True]
    requires_knowledge_ledger: Literal[True]
    requires_exact_coverage: Literal[True]
    requires_chapter_overview: Literal[True]
    core_modules_are_indispensable_questions: Literal[True]
    requires_problem_progression: Literal[True]
    requires_beginner_bridges: Literal[True]
    requires_detailed_expansion_per_module: Literal[True]
    rejects_shallow_expansions: Literal[True]


class AutonomousAuthoringCapabilities(StudioRequest):
    starts_from_uploaded_material: Literal[True]
    asks_for_routine_confirmation: Literal[False]
    asks_learner_for_internal_identifiers: Literal[False]
    repairs_validation_and_preview_failures: Literal[True]


class LiveLearningSessionCapabilities(StudioRequest):
    baseline_reveal_is_published_content: Literal[True]
    supports_exact_target_expansion: Literal[True]
    supports_nested_expansion: Literal[True]
    requires_internal_identifiers_from_learner: Literal[False]


class TeachingModelWorkshopCapabilities(StudioRequest):
    contract_version: Literal["teaching_model_v1"]
    supports_source_authoring: Literal[True]
    requires_matching_preview_before_registration: Literal[True]
    preview_jobs_are_durable: Literal[True]
    requires_semantic_visual_evidence: Literal[True]
    requires_interaction_change_evidence: Literal[True]
    rejects_blank_or_noop_models: Literal[True]


class StudioCapabilitiesResponse(StudioRequest):
    studio_version: Literal["studio_v1"]
    schema_version: Literal["classroom_package_v1"]
    quality_contract_version: Literal["learning_quality_v1"]
    module_structure: Literal["free_composition"]
    content_block_kinds: list[str]
    mutable_operations_require_idempotency_key: Literal[True]
    learner_analysis_capabilities: list[str] = Field(max_length=0)
    chapter_authoring: ChapterAuthoringCapabilities
    autonomous_authoring: AutonomousAuthoringCapabilities
    live_learning_sessions: LiveLearningSessionCapabilities
    teaching_model_workshop: TeachingModelWorkshopCapabilities


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
    learner_entry_url: str
    courses: list[WorkspaceCourseSummary]


class WorkspaceClassroomDraft(StudioRequest):
    draft_id: str
    revision: int = Field(ge=1)
    content_hash: str
    updated_at: str | None = None
    package_id: str
    title: str
    courses: list[WorkspaceCourseSummary]
    matches_active_content: bool
    recommended_for_update: bool
    candidate_count: int = Field(ge=1)
    selection_reason: Literal[
        "only_candidate",
        "latest_updated_at",
        "legacy_highest_revision",
    ]


class WorkspaceRegisteredModel(StudioRequest):
    model_id: str
    version: str
    content_hash: str
    registered_at: str
    recommended_for_use: bool
    version_count: int = Field(ge=1)
    selection_reason: Literal["only_version", "latest_registered_at"]
    manifest: TeachingModelManifest


class WorkspaceAuthoringPolicy(StudioRequest):
    routine_authoring_requires_confirmation: Literal[False]
    publish_after_validation: Literal[True]
    discover_identifiers_before_writes: Literal[True]
    ask_user_for_internal_identifiers: Literal[False]
    autonomous_from_uploaded_material: Literal[True]
    complete_chapter_coverage_required: Literal[True]
    interactive_models_require_semantic_preview: Literal[True]
    learner_analysis_capabilities: list[str] = Field(max_length=0)
    rollback_scope: Literal[
        "explicit_request_or_failed_just_published_release"
    ]


class WorkspacePageSummary(StudioRequest):
    total: int = Field(ge=0)
    returned: int = Field(ge=0)
    has_more: bool
    next_offset: int | None = Field(default=None, ge=0)


class WorkspacePagination(StudioRequest):
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    active_packages: WorkspacePageSummary
    drafts: WorkspacePageSummary
    registered_models: WorkspacePageSummary


class StudioWorkspaceResponse(StudioRequest):
    studio_version: Literal["studio_v1"]
    public_origin: str
    learner_entry_url: str
    active_packages: list[WorkspaceActivePackage]
    drafts: list[WorkspaceClassroomDraft]
    registered_models: list[WorkspaceRegisteredModel]
    pagination: WorkspacePagination
    authoring_policy: WorkspaceAuthoringPolicy
