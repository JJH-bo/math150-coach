from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException

from app.api.studio.v1.auth import require_studio_key
from app.api.studio.v1.schemas import (
    CreateDraftRequest,
    PublishDraftRequest,
    RollbackPackageRequest,
    UpdateDraftRequest,
)
from app.api.v1.schemas import api_error
from app.classroom.authoring import (
    ClassroomAuthoringService,
    ClassroomValidationError,
)
from app.classroom.idempotency import IdempotencyConflictError, IdempotencyLedger
from app.classroom.models import ContentBlockKind
from app.classroom.repository import (
    ClassroomConflictError,
    ClassroomNotFoundError,
    ClassroomRepository,
    ClassroomRepositoryError,
)


ServiceFactory = Callable[[], ClassroomAuthoringService]


def default_service() -> ClassroomAuthoringService:
    root = Path(os.getenv("CLASSROOM_DATA_ROOT", Path.cwd() / "classroom_data"))
    return ClassroomAuthoringService(
        ClassroomRepository(root),
        IdempotencyLedger(root / "operations"),
    )


def create_studio_router(
    service_factory: ServiceFactory = default_service,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/studio/v1",
        tags=["classroom-studio"],
        dependencies=[Depends(require_studio_key)],
    )

    @router.get("/capabilities", operation_id="getStudioCapabilities")
    def capabilities() -> dict:
        return {
            "studio_version": "studio_v1",
            "schema_version": "classroom_package_v1",
            "module_structure": "free_composition",
            "content_block_kinds": [kind.value for kind in ContentBlockKind],
            "mutable_operations_require_idempotency_key": True,
            "learner_analysis_capabilities": [],
        }

    @router.post("/drafts", status_code=201, operation_id="createClassroomDraft")
    def create_draft(
        request: CreateDraftRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: service_factory().create_draft(
                request.draft_id,
                request.package,
                idempotency_key=idempotency_key,
            )
        )

    @router.get("/drafts/{draft_id}", operation_id="getClassroomDraft")
    def get_draft(draft_id: str) -> dict:
        return _map_errors(lambda: service_factory().get_draft(draft_id))

    @router.put("/drafts/{draft_id}", operation_id="updateClassroomDraft")
    def update_draft(
        draft_id: str,
        request: UpdateDraftRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: service_factory().update_draft(
                draft_id,
                request.expected_revision,
                request.package,
                idempotency_key=idempotency_key,
            )
        )

    @router.post(
        "/drafts/{draft_id}/validate",
        operation_id="validateClassroomDraft",
    )
    def validate_draft(draft_id: str) -> dict:
        return _map_errors(lambda: service_factory().validate(draft_id))

    @router.post(
        "/drafts/{draft_id}/publish",
        operation_id="publishClassroomDraft",
    )
    def publish_draft(
        draft_id: str,
        request: PublishDraftRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: service_factory().publish(
                draft_id,
                request.expected_revision,
                idempotency_key=idempotency_key,
            )
        )

    @router.post(
        "/packages/{package_id}/rollback",
        operation_id="rollbackClassroomPackage",
    )
    def rollback_package(
        package_id: str,
        request: RollbackPackageRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: service_factory().rollback(
                package_id,
                request.version,
                idempotency_key=idempotency_key,
            )
        )

    return router


def _map_errors(operation: Callable[[], dict]) -> dict:
    try:
        return operation()
    except ClassroomValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "classroom_validation_failed",
                "message": "Classroom package validation failed.",
                "validation": exc.report.model_dump(mode="json"),
            },
        )
    except IdempotencyConflictError as exc:
        raise api_error(409, "idempotency_key_conflict", str(exc))
    except ClassroomConflictError as exc:
        raise api_error(409, "classroom_revision_conflict", str(exc))
    except ClassroomNotFoundError as exc:
        raise api_error(404, "classroom_not_found", str(exc))
    except ClassroomRepositoryError as exc:
        raise api_error(400, "classroom_repository_error", str(exc))


router = create_studio_router()
