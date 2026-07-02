from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.catalog.models import CatalogQuestionRecord
from app.catalog.validation_report import CatalogValidationReport


class AuthoringStatus(StrEnum):
    IMPORTED = "imported"
    DRAFT = "draft"
    VALIDATION_FAILED = "validation_failed"
    VALIDATED = "validated"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    RETIRED = "retired"


class SourceType(StrEnum):
    TEXTBOOK = "textbook"
    LECTURE_NOTES = "lecture_notes"
    PAST_EXAM = "past_exam"
    GENERATED_VARIANT = "generated_variant"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class SourceMetadata(BaseModel):
    """Internal authoring provenance, never part of learner-facing catalog views."""

    model_config = ConfigDict(extra="forbid")

    source_type: SourceType = SourceType.UNKNOWN
    source_name: str
    source_section: str | None = None
    page_range: str | None = None
    problem_number: str | None = None
    original_problem_ref: str | None = None
    author_notes: str | None = None
    copyright_note: str | None = None
    imported_by: str | None = None
    imported_at: datetime | None = None
    source_fingerprint: str | None = None


class HumanReviewChecklist(BaseModel):
    """Human gate required before an authoring draft can become a publish candidate."""

    model_config = ConfigDict(extra="forbid")

    math_i_scope_confirmed: bool = False
    module_topic_type_confirmed: bool = False
    node_id_confirmed: bool = False
    public_prompt_clear: bool = False
    expected_answer_checked: bool = False
    aliases_checked: bool = False
    solution_outline_checked: bool = False
    rubric_checked: bool = False
    target_dimensions_checked: bool = False
    validator_config_checked: bool = False
    no_public_leak_confirmed: bool = False
    question_id_version_checked: bool = False
    publish_approved: bool = False
    reviewer: str | None = None
    reviewed_at: datetime | None = None
    notes: str | None = None

    def is_publish_ready(self) -> bool:
        return all(getattr(self, field_name) for field_name in self.required_publish_fields())

    @classmethod
    def required_publish_fields(cls) -> tuple[str, ...]:
        return (
            "math_i_scope_confirmed",
            "module_topic_type_confirmed",
            "node_id_confirmed",
            "public_prompt_clear",
            "expected_answer_checked",
            "aliases_checked",
            "solution_outline_checked",
            "rubric_checked",
            "target_dimensions_checked",
            "validator_config_checked",
            "no_public_leak_confirmed",
            "question_id_version_checked",
            "publish_approved",
        )


class AuthoringDraft(BaseModel):
    """Authoring-only wrapper around a runtime catalog candidate."""

    model_config = ConfigDict(extra="forbid")

    draft_id: str
    import_batch_id: str | None = None
    status: AuthoringStatus = AuthoringStatus.DRAFT
    candidate_record: CatalogQuestionRecord
    source_metadata: SourceMetadata | None = None
    validation_report: CatalogValidationReport | None = None
    review_checklist: HumanReviewChecklist | None = None
    ai_assisted: bool = False
    rejection_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def has_passed_validation(self) -> bool:
        return bool(self.validation_report and self.validation_report.passed)
