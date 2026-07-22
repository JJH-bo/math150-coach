from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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


class SourceSection(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    asset_id: str = Field(min_length=1, max_length=120)
    filename: str | None = Field(default=None, max_length=240)
    order: int = Field(ge=1)
    page: str | None = Field(default=None, max_length=120)
    heading: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1, max_length=100_000)
    content_hash: str = Field(min_length=1, max_length=200)


class SourceQuote(StrictModel):
    source_section_id: str = Field(min_length=1, max_length=120)
    quote: str = Field(min_length=1, max_length=4000)


class KnowledgePointKind(str, Enum):
    CONCEPT = "concept"
    DEFINITION = "definition"
    THEOREM = "theorem"
    MECHANISM = "mechanism"
    METHOD = "method"
    FORMULA = "formula"
    CONDITION = "condition"
    EXAMPLE = "example"
    BOUNDARY = "boundary"
    WARNING = "warning"
    APPLICATION = "application"


class KnowledgePointImportance(str, Enum):
    CORE = "core"
    SUPPORTING = "supporting"


class KnowledgePoint(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    statement: str = Field(min_length=1, max_length=4000)
    kind: KnowledgePointKind
    importance: KnowledgePointImportance
    source_section_ids: list[str] = Field(min_length=1)
    source_quotes: list[SourceQuote] = Field(min_length=1)


class KnowledgeCoverage(StrictModel):
    knowledge_point_id: str = Field(min_length=1, max_length=120)
    module_id: str = Field(min_length=1, max_length=120)
    baseline_content_ids: list[str] = Field(min_length=1)
    detail_content_ids: list[str] = Field(default_factory=list)
    model_instance_ids: list[str] = Field(default_factory=list)


class CoverageAudit(StrictModel):
    source_section_ids: list[str] = Field(min_length=1)
    knowledge_point_ids: list[str] = Field(min_length=1)
    unresolved_items: list[str] = Field(default_factory=list)
    auditor_summary: str = Field(min_length=1, max_length=4000)


class ExpansionRepresentation(str, Enum):
    ANIMATED_VISUAL = "animated_visual"
    ANNOTATED_DIAGRAM = "annotated_diagram"
    SMALLER_EXAMPLE = "smaller_example"
    COUNTEREXAMPLE = "counterexample"
    STEP_BY_STEP_DERIVATION = "step_by_step_derivation"
    CONCRETE_ANALOGY = "concrete_analogy"
    LOWER_ABSTRACTION = "lower_abstraction"


class DetailBranch(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    trigger_question: str = Field(min_length=8, max_length=2000)
    learning_obstacle: str = Field(min_length=12, max_length=3000)
    representation: ExpansionRepresentation
    focus_relation: str = Field(min_length=12, max_length=3000)
    bridge_steps: list[str] = Field(min_length=2, max_length=12)
    blocks: list["ContentBlock"] = Field(min_length=2)
    return_connection: str = Field(min_length=12, max_length=3000)


class ContentBlock(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    kind: ContentBlockKind
    data: dict[str, Any]
    knowledge_point_ids: list[str] = Field(default_factory=list)
    source_anchor: SourceAnchor | None = None
    detail_branches: list[DetailBranch] = Field(default_factory=list)


class LearningSegment(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    title: str | None = Field(default=None, max_length=240)
    question_answered: str = Field(min_length=8, max_length=1000)
    bridge_from_previous: str = Field(min_length=12, max_length=3000)
    mechanism: str = Field(min_length=12, max_length=5000)
    entry_assumptions: list[str] = Field(min_length=1, max_length=20)
    exit_understanding: str = Field(min_length=8, max_length=2000)
    knowledge_point_ids: list[str] = Field(min_length=1)
    blocks: list[ContentBlock] = Field(min_length=1)


class NoviceBridge(StrictModel):
    known_before: list[str] = Field(min_length=1, max_length=20)
    missing_bridge: str = Field(min_length=12, max_length=3000)
    concrete_anchor: str = Field(min_length=8, max_length=3000)
    bridge_strategy: str = Field(min_length=12, max_length=3000)


class CoreModule(StrictModel):
    id: str = Field(min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=240)
    summary: str | None = None
    core_question: str = Field(min_length=8, max_length=1000)
    chapter_role: str = Field(min_length=12, max_length=3000)
    why_indispensable: str = Field(min_length=12, max_length=3000)
    depends_on_module_ids: list[str] = Field(default_factory=list)
    novice_bridge: NoviceBridge
    knowledge_point_ids: list[str] = Field(min_length=1)
    blocks: list[ContentBlock] = Field(default_factory=list)
    segments: list[LearningSegment] = Field(min_length=1)

    @model_validator(mode="after")
    def require_content(self) -> "CoreModule":
        if not self.segments:
            raise ValueError("core module requires at least one learning segment")
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
    source_sections: list[SourceSection] = Field(default_factory=list)
    knowledge_points: list[KnowledgePoint] = Field(default_factory=list)
    coverage_map: list[KnowledgeCoverage] = Field(default_factory=list)
    coverage_audit: CoverageAudit | None = None
    overview: "ChapterOverview | None" = None


class ChapterOverview(StrictModel):
    essential_question: str = Field(min_length=8, max_length=1000)
    learning_route_summary: str = Field(min_length=12, max_length=4000)
    module_order: list[str] = Field(min_length=1)


class Course(StrictModel):
    id: str
    title: str
    chapters: list[Chapter] = Field(min_length=1)


class ModelInstanceReference(StrictModel):
    instance_id: str
    model_id: str
    model_version: str
    initial_state: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    viewport_mode: str = "inline"
    quality_profile: str = "balanced"
    allowed_interactions: list[str] = Field(default_factory=list)
    fallback_description: str = Field(min_length=1, max_length=2000)


class BindingTriggerKind(str, Enum):
    BLOCK_ENTER = "block_enter"
    BLOCK_LEAVE = "block_leave"
    BLOCK_ACTIVATE = "block_activate"
    DETAIL_BRANCH_OPEN = "detail_branch_open"
    DETAIL_BRANCH_CLOSE = "detail_branch_close"
    EXPLICIT_CONTROL = "explicit_control"
    PARAMETER_CHANGE = "parameter_change"


class BindingTrigger(StrictModel):
    kind: BindingTriggerKind
    detail_branch_id: str | None = None
    control_id: str | None = None


class BindingEffectKind(str, Enum):
    SET_STATE = "set_state"
    PERFORM_ACTION = "perform_action"
    UPDATE_PARAMETERS = "update_parameters"
    PLAY = "play"
    PAUSE = "pause"
    RESET = "reset"
    STEP = "step"
    HIGHLIGHT_TARGET = "highlight_target"
    CLEAR_HIGHLIGHT = "clear_highlight"
    SAVE_SNAPSHOT = "save_snapshot"
    RESTORE_SNAPSHOT = "restore_snapshot"


class BindingEffect(StrictModel):
    kind: BindingEffectKind
    target: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ContentModelBinding(StrictModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{0,119}$")
    content_id: str
    instance_id: str
    trigger: BindingTrigger
    effect: BindingEffect
    restore_previous: bool = False
    return_effect: BindingEffect | None = None


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
    model_bindings: list[ContentModelBinding] = Field(default_factory=list)
    assets: list[AssetReference] = Field(default_factory=list)


class DraftRecord(StrictModel):
    draft_id: str
    revision: int = Field(ge=1)
    content_hash: str
    package: ClassroomPackage
    updated_at: str | None = None


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
        default_factory=utc_now
    )
