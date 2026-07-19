from __future__ import annotations

from app.classroom.idempotency import IdempotencyLedger
from app.classroom.model_repository import TeachingModelRepository
from app.classroom.models import ClassroomPackage, Course
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
        model_repository: TeachingModelRepository | None = None,
    ) -> None:
        self.repository = repository
        self.ledger = ledger
        self.validator = validator or ClassroomPackageValidator()
        self.model_repository = model_repository

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

    def workspace(self, *, public_origin: str) -> dict:
        origin = public_origin.rstrip("/")
        active_packages = [
            {
                "package_id": release.package_id,
                "title": release.package.title,
                "active_version": release.version,
                "content_hash": release.content_hash,
                "courses": self._course_summaries(release.package.courses),
            }
            for release in self.repository.list_active_releases()
        ]
        drafts = [
            {
                "draft_id": draft.draft_id,
                "revision": draft.revision,
                "content_hash": draft.content_hash,
                "package_id": draft.package.package_id,
                "title": draft.package.title,
                "courses": self._course_summaries(draft.package.courses),
            }
            for draft in self.repository.list_drafts()
        ]
        registered_models = (
            [
                {
                    "model_id": record.model_id,
                    "version": record.version,
                    "content_hash": record.content_hash,
                    "manifest": record.manifest.model_dump(
                        mode="json",
                        exclude_none=True,
                    ),
                }
                for record in self.model_repository.list_registered()
            ]
            if self.model_repository is not None
            else []
        )
        return {
            "studio_version": "studio_v1",
            "public_origin": origin,
            "learner_entry_url": f"{origin}/classroom/",
            "active_packages": active_packages,
            "drafts": drafts,
            "registered_models": registered_models,
            "authoring_policy": {
                "routine_authoring_requires_confirmation": False,
                "publish_after_validation": True,
                "discover_identifiers_before_writes": True,
                "ask_user_for_internal_identifiers": False,
                "learner_analysis_capabilities": [],
                "rollback_scope": (
                    "explicit_request_or_failed_just_published_release"
                ),
            },
        }

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

    @staticmethod
    def _course_summaries(courses: list[Course]) -> list[dict]:
        return [
            {
                "id": course.id,
                "title": course.title,
                "chapters": [
                    {
                        "id": chapter.id,
                        "title": chapter.title,
                        "modules": [
                            {
                                "id": module.id,
                                "title": module.title,
                                **(
                                    {"summary": module.summary}
                                    if module.summary is not None
                                    else {}
                                ),
                            }
                            for module in chapter.modules
                        ],
                    }
                    for chapter in course.chapters
                ],
            }
            for course in courses
        ]
