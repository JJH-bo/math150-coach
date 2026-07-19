from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse

from app.api.studio.v1.auth import require_studio_key
from app.api.studio.v1.schemas import (
    CreateDraftRequest,
    CreateModelDraftRequest,
    PublishDraftRequest,
    RegisterModelRequest,
    RequestModelPreviewRequest,
    RollbackPackageRequest,
    StudioWorkspaceResponse,
    UpdateDraftRequest,
    UpdateModelDraftRequest,
)
from app.api.errors import api_error
from app.classroom.authoring import (
    ClassroomAuthoringService,
    ClassroomValidationError,
)
from app.classroom.idempotency import IdempotencyConflictError, IdempotencyLedger
from app.classroom.model_authoring import (
    ModelRegistrationError,
    ModelValidationError,
    TeachingModelAuthoringService,
)
from app.classroom.model_repository import (
    ModelConflictError,
    ModelNotFoundError,
    ModelRepositoryError,
    TeachingModelRepository,
)
from app.classroom.preview import TeachingModelPreviewService
from app.classroom.models import ContentBlockKind
from app.classroom.repository import (
    ClassroomConflictError,
    ClassroomNotFoundError,
    ClassroomRepository,
    ClassroomRepositoryError,
)
from app.classroom.validation import ClassroomPackageValidator


ServiceFactory = Callable[[], ClassroomAuthoringService]
ModelServiceFactory = Callable[[], TeachingModelAuthoringService]
PreviewServiceFactory = Callable[[], TeachingModelPreviewService]


def _data_roots() -> tuple[Path, Path]:
    root = Path(os.getenv("CLASSROOM_DATA_ROOT", Path.cwd() / "classroom_data"))
    seed = Path(__file__).resolve().parents[4] / "classroom_data" / "model_seed"
    return root, seed


def default_model_repository() -> TeachingModelRepository:
    root, seed = _data_roots()
    return TeachingModelRepository(root, seed_root=seed)


def default_service() -> ClassroomAuthoringService:
    root, _ = _data_roots()
    models = default_model_repository()
    return ClassroomAuthoringService(
        ClassroomRepository(root),
        IdempotencyLedger(root / "operations"),
        ClassroomPackageValidator(model_resolver=models.get_registered),
        model_repository=models,
    )


def default_model_service() -> TeachingModelAuthoringService:
    root, _ = _data_roots()
    return TeachingModelAuthoringService(
        default_model_repository(),
        IdempotencyLedger(root / "model-operations"),
    )


def default_preview_service() -> TeachingModelPreviewService:
    return TeachingModelPreviewService(default_model_repository())


def create_studio_router(
    service_factory: ServiceFactory = default_service,
    *,
    model_service_factory: ModelServiceFactory = default_model_service,
    preview_service_factory: PreviewServiceFactory = default_preview_service,
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
            "teaching_model_workshop": {
                "contract_version": "teaching_model_v1",
                "supports_source_authoring": True,
                "requires_matching_preview_before_registration": True,
                "preview_jobs_are_durable": True,
            },
        }

    @router.get(
        "/workspace",
        operation_id="getStudioWorkspace",
        response_model=StudioWorkspaceResponse,
    )
    def workspace(request: Request) -> StudioWorkspaceResponse:
        public_origin = os.getenv(
            "AI_CLASSROOM_PUBLIC_ORIGIN",
            str(request.base_url),
        ).rstrip("/")
        return _map_errors(
            lambda: service_factory().workspace(public_origin=public_origin)
        )

    @router.get("/models", operation_id="listTeachingModels")
    def list_models() -> dict:
        return {"models": model_service_factory().list_registered()}

    @router.post(
        "/model-drafts",
        status_code=201,
        operation_id="createTeachingModelDraft",
    )
    def create_model_draft(
        request: CreateModelDraftRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: model_service_factory().create_draft(
                request.draft_id,
                request.manifest,
                request.source,
                idempotency_key=idempotency_key,
            )
        )

    @router.get(
        "/model-drafts/{draft_id}",
        operation_id="getTeachingModelDraft",
    )
    def get_model_draft(draft_id: str) -> dict:
        return _map_errors(lambda: model_service_factory().get_draft(draft_id))

    @router.put(
        "/model-drafts/{draft_id}",
        operation_id="updateTeachingModelDraft",
    )
    def update_model_draft(
        draft_id: str,
        request: UpdateModelDraftRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: model_service_factory().update_draft(
                draft_id,
                expected_revision=request.expected_revision,
                manifest=request.manifest,
                source=request.source,
                idempotency_key=idempotency_key,
            )
        )

    @router.post(
        "/model-drafts/{draft_id}/validate",
        operation_id="validateTeachingModelDraft",
    )
    def validate_model_draft(draft_id: str) -> dict:
        return _map_errors(lambda: model_service_factory().validate(draft_id))

    @router.post(
        "/model-drafts/{draft_id}/previews",
        status_code=202,
        operation_id="requestTeachingModelPreview",
    )
    def request_model_preview(
        draft_id: str,
        request: RequestModelPreviewRequest,
        background_tasks: BackgroundTasks,
    ) -> dict:
        service = preview_service_factory()
        job = _map_errors(
            lambda: service.request_preview(
                draft_id,
                scenario_id=request.scenario_id,
                viewport=request.viewport,
            ).model_dump(mode="json", exclude_none=True)
        )
        background_tasks.add_task(service.run_preview, job["job_id"])
        return job

    @router.get(
        "/previews/{job_id}",
        operation_id="getTeachingModelPreview",
    )
    def get_model_preview(job_id: str) -> dict:
        return _map_errors(
            lambda: preview_service_factory().get_preview(job_id).model_dump(
                mode="json",
                exclude_none=True,
            )
        )

    @router.get(
        "/previews/{job_id}/artifacts/{name}",
        operation_id="getTeachingModelPreviewArtifact",
    )
    def get_model_preview_artifact(job_id: str, name: str) -> FileResponse:
        try:
            service = preview_service_factory()
            path = service.artifact(job_id, name)
            job = service.get_preview(job_id)
            media_type = next(
                (
                    artifact.media_type
                    for artifact in job.artifacts
                    if artifact.name == name
                ),
                "application/octet-stream",
            )
            return FileResponse(path, media_type=media_type, filename=name)
        except (FileNotFoundError, ModelNotFoundError) as exc:
            raise api_error(404, "model_preview_artifact_not_found", str(exc))

    @router.post(
        "/model-drafts/{draft_id}/register",
        status_code=201,
        operation_id="registerTeachingModel",
    )
    def register_model(
        draft_id: str,
        request: RegisterModelRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: model_service_factory().register(
                draft_id,
                expected_revision=request.expected_revision,
                idempotency_key=idempotency_key,
            )
        )

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
    except ModelValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "teaching_model_validation_failed",
                "message": str(exc),
                "validation": exc.report.model_dump(mode="json"),
            },
        )
    except ModelRegistrationError as exc:
        raise api_error(409, "teaching_model_registration_blocked", str(exc))
    except ModelConflictError as exc:
        raise api_error(409, "teaching_model_revision_conflict", str(exc))
    except ModelNotFoundError as exc:
        raise api_error(404, "teaching_model_not_found", str(exc))
    except ModelRepositoryError as exc:
        raise api_error(400, "teaching_model_repository_error", str(exc))
    except ClassroomConflictError as exc:
        raise api_error(409, "classroom_revision_conflict", str(exc))
    except ClassroomNotFoundError as exc:
        raise api_error(404, "classroom_not_found", str(exc))
    except ClassroomRepositoryError as exc:
        raise api_error(400, "classroom_repository_error", str(exc))
    except ValueError as exc:
        raise api_error(422, "studio_request_invalid", str(exc))


router = create_studio_router()
