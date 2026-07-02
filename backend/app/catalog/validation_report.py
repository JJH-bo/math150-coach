from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.catalog.repository import CatalogValidationError


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    error_code: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    field_path: str | None = None
    candidate_id: str | None = None
    batch_id: str | None = None


class CatalogValidationReport(BaseModel):
    """Authoring-side report wrapper around the fail-fast CatalogValidator."""

    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    batch_id: str | None = None
    passed: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    validator_version: str | None = "catalog_validator_phase_4_2"

    @classmethod
    def passed_report(
        cls,
        *,
        candidate_id: str,
        batch_id: str | None = None,
        validator_version: str | None = "catalog_validator_phase_4_2",
    ) -> "CatalogValidationReport":
        return cls(
            candidate_id=candidate_id,
            batch_id=batch_id,
            passed=True,
            issues=[],
            validator_version=validator_version,
        )

    @classmethod
    def failed_report(
        cls,
        *,
        candidate_id: str,
        error: CatalogValidationError,
        batch_id: str | None = None,
        field_path: str | None = None,
        validator_version: str | None = "catalog_validator_phase_4_2",
    ) -> "CatalogValidationReport":
        return cls(
            candidate_id=candidate_id,
            batch_id=batch_id,
            passed=False,
            issues=[
                ValidationIssue(
                    error_code=error.error_code,
                    message=str(error),
                    severity=ValidationSeverity.ERROR,
                    field_path=field_path,
                    candidate_id=candidate_id,
                    batch_id=batch_id,
                )
            ],
            validator_version=validator_version,
        )
