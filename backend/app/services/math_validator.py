from __future__ import annotations

from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    is_valid: bool
    reasons: list[str] = Field(default_factory=list)


class MathValidator:
    """Validation interface for generated question candidates.

    Phase 0 performs only structural checks. Later phases should add symbolic
    verification, numeric sampling, answer checks, and duplicate detection.
    """

    def validate_candidate(self, question_payload: dict) -> ValidationResult:
        required_fields = {"prompt", "expected_answer", "node_id"}
        missing = sorted(required_fields - set(question_payload))
        if missing:
            return ValidationResult(is_valid=False, reasons=[f"Missing required fields: {missing}"])
        return ValidationResult(is_valid=True, reasons=["Structural validation passed."])
