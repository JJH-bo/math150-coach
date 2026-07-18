from __future__ import annotations

from app.classroom.idempotency import IdempotencyLedger
from app.classroom.model_contracts import TeachingModelManifest
from app.classroom.model_repository import (
    ModelConflictError,
    TeachingModelRepository,
)
from app.classroom.model_validation import (
    ModelValidationReport,
    TeachingModelValidator,
)


class ModelValidationError(ValueError):
    def __init__(self, report: ModelValidationReport) -> None:
        super().__init__("teaching model validation failed")
        self.report = report


class ModelRegistrationError(ValueError):
    pass


class TeachingModelAuthoringService:
    def __init__(
        self,
        repository: TeachingModelRepository,
        ledger: IdempotencyLedger,
        validator: TeachingModelValidator | None = None,
    ) -> None:
        self.repository = repository
        self.ledger = ledger
        self.validator = validator or TeachingModelValidator()

    def create_draft(
        self,
        draft_id: str,
        manifest: TeachingModelManifest,
        source: str,
        *,
        idempotency_key: str,
    ) -> dict:
        request = {
            "manifest": manifest.model_dump(mode="json", exclude_none=True),
            "source": source,
        }
        return self.ledger.execute(
            f"create-model-draft:{draft_id}",
            idempotency_key,
            request,
            lambda: self.repository.create_draft(
                draft_id,
                manifest,
                source,
            ).model_dump(mode="json", exclude_none=True),
        )

    def get_draft(self, draft_id: str) -> dict:
        return self.repository.get_draft(draft_id).model_dump(
            mode="json",
            exclude_none=True,
        )

    def update_draft(
        self,
        draft_id: str,
        *,
        expected_revision: int,
        manifest: TeachingModelManifest,
        source: str,
        idempotency_key: str,
    ) -> dict:
        request = {
            "expected_revision": expected_revision,
            "manifest": manifest.model_dump(mode="json", exclude_none=True),
            "source": source,
        }
        return self.ledger.execute(
            f"update-model-draft:{draft_id}",
            idempotency_key,
            request,
            lambda: self.repository.update_draft(
                draft_id,
                expected_revision=expected_revision,
                manifest=manifest,
                source=source,
            ).model_dump(mode="json", exclude_none=True),
        )

    def validate(self, draft_id: str) -> dict:
        draft = self.repository.get_draft(draft_id)
        return self.validator.validate(draft.manifest, draft.source).model_dump(
            mode="json"
        )

    def register(
        self,
        draft_id: str,
        *,
        expected_revision: int,
        idempotency_key: str,
    ) -> dict:
        draft = self.repository.get_draft(draft_id)
        if draft.revision != expected_revision:
            raise ModelConflictError(
                f"model draft {draft_id!r} expected revision {expected_revision}, "
                f"but current revision is {draft.revision}"
            )
        report = self.validator.validate(draft.manifest, draft.source)
        if not report.passed:
            raise ModelValidationError(report)
        preview = self.repository.find_successful_preview(draft.content_hash)
        if preview is None:
            raise ModelRegistrationError(
                "registration requires a successful preview for the current draft"
            )
        preview_report = preview.report or {}
        if preview_report.get("resources_after_dispose") != 0:
            raise ModelRegistrationError(
                "preview leaked tracked resources after model disposal"
            )
        if preview_report.get("uncaught_errors"):
            raise ModelRegistrationError("preview reported uncaught runtime errors")

        request = {
            "expected_revision": expected_revision,
            "content_hash": draft.content_hash,
            "preview_job_id": preview.job_id,
        }
        return self.ledger.execute(
            f"register-model:{draft_id}",
            idempotency_key,
            request,
            lambda: self.repository.register(
                draft,
                validation=report.model_dump(mode="json"),
                preview_job_id=preview.job_id,
            ).model_dump(mode="json", exclude_none=True),
        )

    def list_registered(self) -> list[dict]:
        return [
            record.model_dump(mode="json", exclude_none=True)
            for record in self.repository.list_registered()
        ]
