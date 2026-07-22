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

    def workspace(
        self,
        *,
        public_origin: str,
        offset: int = 0,
        limit: int = 50,
    ) -> dict:
        origin = public_origin.rstrip("/")
        active_releases = self.repository.list_active_releases()
        active_by_package = {
            release.package_id: release
            for release in active_releases
        }
        active_packages = [
            {
                "package_id": release.package_id,
                "title": release.package.title,
                "active_version": release.version,
                "content_hash": release.content_hash,
                "learner_entry_url": (
                    f"{origin}/classroom/"
                    f"?package_id={release.package_id}"
                ),
                "courses": self._course_summaries(release.package.courses),
            }
            for release in active_releases
        ]
        draft_records = self.repository.list_drafts()
        draft_groups: dict[str, list] = {}
        for draft in draft_records:
            draft_groups.setdefault(draft.package.package_id, []).append(draft)
        recommended_drafts = {
            package_id: max(
                candidates,
                key=lambda item: (
                    item.updated_at or "",
                    item.revision,
                    item.draft_id,
                ),
            ).draft_id
            for package_id, candidates in draft_groups.items()
        }
        drafts = [
            {
                "draft_id": draft.draft_id,
                "revision": draft.revision,
                "content_hash": draft.content_hash,
                "updated_at": draft.updated_at,
                "package_id": draft.package.package_id,
                "title": draft.package.title,
                "courses": self._course_summaries(draft.package.courses),
                "matches_active_content": (
                    draft.package.package_id in active_by_package
                    and draft.content_hash
                    == active_by_package[draft.package.package_id].content_hash
                ),
                "recommended_for_update": (
                    recommended_drafts[draft.package.package_id]
                    == draft.draft_id
                ),
                "candidate_count": len(
                    draft_groups[draft.package.package_id]
                ),
                "selection_reason": (
                    "only_candidate"
                    if len(draft_groups[draft.package.package_id]) == 1
                    else (
                        "latest_updated_at"
                        if any(
                            candidate.updated_at is not None
                            for candidate in draft_groups[
                                draft.package.package_id
                            ]
                        )
                        else "legacy_highest_revision"
                    )
                ),
            }
            for draft in draft_records
        ]
        model_records = (
            self.model_repository.list_registered()
            if self.model_repository is not None
            else []
        )
        model_groups: dict[str, list] = {}
        for record in model_records:
            model_groups.setdefault(record.model_id, []).append(record)
        recommended_models = {
            model_id: max(
                versions,
                key=lambda item: (item.registered_at, item.version),
            ).version
            for model_id, versions in model_groups.items()
        }
        registered_models = [
                {
                    "model_id": record.model_id,
                    "version": record.version,
                    "content_hash": record.content_hash,
                    "registered_at": record.registered_at,
                    "recommended_for_use": (
                        recommended_models[record.model_id] == record.version
                    ),
                    "version_count": len(model_groups[record.model_id]),
                    "selection_reason": (
                        "only_version"
                        if len(model_groups[record.model_id]) == 1
                        else "latest_registered_at"
                    ),
                    "manifest": record.manifest.model_dump(
                        mode="json",
                        exclude_none=True,
                    ),
                }
                for record in model_records
        ]
        active_page, active_pagination = self._page(
            active_packages,
            offset=offset,
            limit=limit,
        )
        draft_page, draft_pagination = self._page(
            drafts,
            offset=offset,
            limit=limit,
        )
        model_page, model_pagination = self._page(
            registered_models,
            offset=offset,
            limit=limit,
        )
        return {
            "studio_version": "studio_v1",
            "public_origin": origin,
            "learner_entry_url": f"{origin}/classroom/",
            "active_packages": active_page,
            "drafts": draft_page,
            "registered_models": model_page,
            "pagination": {
                "offset": offset,
                "limit": limit,
                "active_packages": active_pagination,
                "drafts": draft_pagination,
                "registered_models": model_pagination,
            },
            "authoring_policy": {
                "routine_authoring_requires_confirmation": False,
                "publish_after_validation": True,
                "discover_identifiers_before_writes": True,
                "ask_user_for_internal_identifiers": False,
                "autonomous_from_uploaded_material": True,
                "complete_chapter_coverage_required": True,
                "interactive_models_require_semantic_preview": True,
                "learner_analysis_capabilities": [],
                "rollback_scope": (
                    "explicit_request_or_failed_just_published_release"
                ),
            },
        }

    @staticmethod
    def _page(
        items: list[dict],
        *,
        offset: int,
        limit: int,
    ) -> tuple[list[dict], dict]:
        page = items[offset : offset + limit]
        next_offset = offset + limit
        has_more = next_offset < len(items)
        return page, {
            "total": len(items),
            "returned": len(page),
            "has_more": has_more,
            "next_offset": next_offset if has_more else None,
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
