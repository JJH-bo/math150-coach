from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.catalog.authoring_models import SourceMetadata


class ImportDraftEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: str
    path: str
    expected_question_id: str | None = None
    source_metadata_override: dict[str, Any] | None = None
    review_checklist_path: str | None = None
    ai_assisted: bool | None = None


class ImportManifest(BaseModel):
    """Authoring-only batch manifest. It is not the formal catalog manifest."""

    model_config = ConfigDict(extra="forbid")

    import_batch_id: str
    batch_name: str | None = None
    source_summary: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    default_source_metadata: SourceMetadata | None = None
    drafts: list[ImportDraftEntry] = Field(default_factory=list)
    output_report_dir: str | None = None
    strict_mode: bool = True

    @model_validator(mode="after")
    def validate_unique_draft_ids(self) -> "ImportManifest":
        seen: set[str] = set()
        duplicates: set[str] = set()
        for draft in self.drafts:
            if draft.draft_id in seen:
                duplicates.add(draft.draft_id)
            seen.add(draft.draft_id)
        if duplicates:
            raise ValueError(f"duplicate draft_id values: {sorted(duplicates)}")
        return self


def merge_source_metadata(
    default_source_metadata: SourceMetadata | None,
    override: dict[str, Any] | None,
) -> SourceMetadata | None:
    if default_source_metadata is None and not override:
        return None
    merged = default_source_metadata.model_dump(mode="json") if default_source_metadata else {}
    merged.update(override or {})
    return SourceMetadata.model_validate(merged)
