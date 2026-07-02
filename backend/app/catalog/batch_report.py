from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.catalog.validation_report import CatalogValidationReport, ValidationIssue


class BatchDraftResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_id: str
    question_id: str | None = None
    status: str
    validation_report: CatalogValidationReport | None = None
    human_review_status: str
    content_hash: str | None = None
    publish_candidate_preview_path: str | None = None


class BatchReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    import_batch_id: str
    total: int
    passed: int
    failed: int
    candidates_built: int = 0
    dry_run_only: Literal[True] = True
    issues: list[ValidationIssue] = Field(default_factory=list)
    per_draft_results: list[BatchDraftResult] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    tool_version: str = "phase_4_4_dry_run"
