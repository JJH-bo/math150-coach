from __future__ import annotations

from app.classroom.idempotency import IdempotencyLedger
from app.classroom.models import ClassroomPackage
from app.classroom.repository import ClassroomRepository
from app.classroom.validation import (
    ClassroomPackageValidator,
    ClassroomValidationReport,
)


class ClassroomValidationError(ValueError):
    def __init__(self, report: ClassroomValidationReport) -> None:
        super().__init__("classroom package validation failed")
        self.report = report


class ClassroomAuthoringService:
    def __init__(
        self,
        repository: ClassroomRepository,
        ledger: IdempotencyLedger,
        validator: ClassroomPackageValidator | None = None,
    ) -> None:
        self.repository = repository
        self.ledger = ledger
        self.validator = validator or ClassroomPackageValidator()

    def create_draft(
        self,
        draft_id: str,
        package: ClassroomPackage,
        *,
        idempotency_key: str,
    ) -> dict:
        return self.ledger.execute(
            f"create-draft:{draft_id}",
            idempotency_key,
            package,
            lambda: self.repository.create_draft(draft_id, package).model_dump(
                mode="json", exclude_none=True
            ),
        )

    def get_draft(self, draft_id: str) -> dict:
        return self.repository.get_draft(draft_id).model_dump(
            mode="json", exclude_none=True
        )

    def update_draft(
        self,
        draft_id: str,
        expected_revision: int,
        package: ClassroomPackage,
        *,
        idempotency_key: str,
    ) -> dict:
        request = {
            "expected_revision": expected_revision,
            "package": package.model_dump(mode="json", exclude_none=True),
        }
        return self.ledger.execute(
            f"update-draft:{draft_id}",
            idempotency_key,
            request,
            lambda: self.repository.update_draft(
                draft_id, expected_revision, package
            ).model_dump(mode="json", exclude_none=True),
        )

    def validate(self, draft_id: str) -> dict:
        record = self.repository.get_draft(draft_id)
        return self.validator.validate(record.package).model_dump(mode="json")

    def publish(
        self,
        draft_id: str,
        expected_revision: int,
        *,
        idempotency_key: str,
    ) -> dict:
        record = self.repository.get_draft(draft_id)
        report = self.validator.validate(record.package)
        if not report.passed:
            raise ClassroomValidationError(report)
        return self.ledger.execute(
            f"publish:{draft_id}",
            idempotency_key,
            {"expected_revision": expected_revision, "hash": record.content_hash},
            lambda: self.repository.publish(
                draft_id, expected_revision
            ).model_dump(mode="json", exclude_none=True),
        )

    def rollback(
        self,
        package_id: str,
        version: str,
        *,
        idempotency_key: str,
    ) -> dict:
        return self.ledger.execute(
            f"rollback:{package_id}",
            idempotency_key,
            {"version": version},
            lambda: self.repository.rollback(package_id, version).model_dump(
                mode="json", exclude_none=True
            ),
        )
