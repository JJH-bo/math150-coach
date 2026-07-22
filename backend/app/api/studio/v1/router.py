from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
)
from fastapi.responses import FileResponse

from app.api.studio.v1.auth import require_studio_key
from app.api.studio.v1.schemas import (
    CreateDraftRequest,
    CreateModelDraftRequest,
    CreateToolJobRequest,
    PublishDraftRequest,
    PatchLearningSessionRequest,
    RegisterModelRequest,
    RequestModelPreviewRequest,
    ReturnLearningSessionRequest,
    RollbackPackageRequest,
    StudioCapabilitiesResponse,
    StudioToolListResponse,
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
from app.classroom.runtime import ClassroomRuntimeService
from app.classroom.session_models import ScenePatch
from app.classroom.session_repository import (
    LearningSessionConflictError,
    LearningSessionNotFoundError,
    LearningSessionRepository,
    LearningSessionRepositoryError,
)
from app.classroom.sessions import LearningSessionService
from app.classroom.repository import (
    ClassroomConflictError,
    ClassroomNotFoundError,
    ClassroomRepository,
    ClassroomRepositoryError,
)
from app.classroom.validation import ClassroomPackageValidator
from app.tools.adapters.symbolic_math import SymbolicMathAdapter
from app.tools.adapters.numeric_math import NumericMathAdapter
from app.tools.adapters.math_verify import MathVerifyAdapter
from app.tools.adapters.graph_math import GraphMathAdapter
from app.tools.adapters.plot_visualization import PlotAdapter
from app.tools.adapters.diagram_visualization import DiagramAdapter
from app.tools.adapters.geometry2d_visualization import Geometry2dAdapter
from app.tools.adapters.reveal_export import RevealExportAdapter
from app.tools.adapters.pptx_export import PptxExportAdapter
from app.tools.adapters.pdf_export import PdfExportAdapter
from app.tools.adapters.html_export import HtmlExportAdapter
from app.tools.adapters.package_export import PackageExportAdapter
from app.tools.contracts import (
    ToolDefinition,
    ToolJob,
    ToolQualityTier,
    ToolScope,
)
from app.tools.execution import (
    ToolArgumentValidationError,
    ToolExecutionService,
    ToolScopeDeniedError,
)
from app.tools.registry import ToolNotFoundError, ToolRegistry
from app.tools.repository import (
    ToolJobNotFoundError,
    ToolJobRepository,
    ToolJobRepositoryError,
)


ServiceFactory = Callable[[], ClassroomAuthoringService]
ModelServiceFactory = Callable[[], TeachingModelAuthoringService]
PreviewServiceFactory = Callable[[], TeachingModelPreviewService]
SessionServiceFactory = Callable[[], LearningSessionService]
ToolServiceFactory = Callable[[], ToolExecutionService]


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


def default_session_service() -> LearningSessionService:
    root, _ = _data_roots()
    runtime = ClassroomRuntimeService(
        ClassroomRepository(root),
        model_repository=default_model_repository(),
    )
    return LearningSessionService(
        LearningSessionRepository(root / "learning-sessions.sqlite3"),
        runtime,
    )


def default_tool_service() -> ToolExecutionService:
    root, _ = _data_roots()
    return ToolExecutionService(
        ToolRegistry(
            [
                SymbolicMathAdapter(),
                NumericMathAdapter(),
                MathVerifyAdapter(),
                GraphMathAdapter(),
                PlotAdapter(),
                DiagramAdapter(),
                Geometry2dAdapter(),
                RevealExportAdapter(),
                PptxExportAdapter(),
                PdfExportAdapter(),
                HtmlExportAdapter(),
                PackageExportAdapter(),
            ]
        ),
        ToolJobRepository(root),
        IdempotencyLedger(root / "tool-idempotency"),
    )


def create_studio_router(
    service_factory: ServiceFactory = default_service,
    *,
    model_service_factory: ModelServiceFactory = default_model_service,
    preview_service_factory: PreviewServiceFactory = default_preview_service,
    session_service_factory: SessionServiceFactory = default_session_service,
    tool_service_factory: ToolServiceFactory = default_tool_service,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/studio/v1",
        tags=["classroom-studio"],
        dependencies=[Depends(require_studio_key)],
    )

    @router.get(
        "/tools",
        operation_id="listStudioTools",
        response_model=StudioToolListResponse,
    )
    def list_tools(
        query: str | None = Query(default=None, min_length=1, max_length=160),
        category: str | None = Query(default=None, min_length=2, max_length=80),
        quality_tier: ToolQualityTier | None = Query(default=None),
    ) -> StudioToolListResponse:
        tools = tool_service_factory().registry.list(
            query=query,
            category=category,
            quality_tier=quality_tier,
        )
        return StudioToolListResponse(tools=tools, total=len(tools))

    @router.get(
        "/tools/{tool_id}",
        operation_id="getStudioTool",
        response_model=ToolDefinition,
    )
    def get_tool(
        tool_id: str,
        version: str | None = Query(default=None),
    ) -> ToolDefinition:
        return _map_errors(
            lambda: tool_service_factory().registry.get(
                tool_id,
                version,
            ).definition
        )

    @router.post(
        "/tool-jobs",
        status_code=202,
        operation_id="submitStudioToolJob",
        response_model=ToolJob,
    )
    def submit_tool_job(
        request: CreateToolJobRequest,
        background_tasks: BackgroundTasks,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> ToolJob:
        service = tool_service_factory()
        job = _map_errors(
            lambda: service.submit(
                tool_id=request.tool_id,
                tool_version=request.tool_version,
                arguments=request.arguments,
                idempotency_key=idempotency_key,
                granted_scopes=set(ToolScope),
            )
        )
        if job.state.value == "queued":
            background_tasks.add_task(service.run, job.job_id)
        return job

    @router.get(
        "/tool-jobs/{job_id}",
        operation_id="getStudioToolJob",
        response_model=ToolJob,
    )
    def get_tool_job(job_id: str) -> ToolJob:
        return _map_errors(lambda: tool_service_factory().get(job_id))

    @router.post(
        "/tool-jobs/{job_id}/cancel",
        operation_id="cancelStudioToolJob",
        response_model=ToolJob,
    )
    def cancel_tool_job(job_id: str) -> ToolJob:
        return _map_errors(lambda: tool_service_factory().cancel(job_id))

    @router.get(
        "/tool-jobs/{job_id}/artifacts/{artifact_name}",
        operation_id="getStudioToolArtifact",
        response_class=FileResponse,
    )
    def get_tool_artifact(job_id: str, artifact_name: str) -> FileResponse:
        service = tool_service_factory()
        job = _map_errors(lambda: service.get(job_id))
        metadata = next(
            (item for item in job.artifacts if item.name == artifact_name),
            None,
        )
        if metadata is None:
            raise api_error(
                404,
                "tool_job_not_found",
                f"artifact {artifact_name} for tool job {job_id} was not found",
            )
        path = _map_errors(lambda: service.artifact(job_id, artifact_name))
        return FileResponse(
            path,
            media_type=metadata.media_type,
            filename=metadata.name,
        )

    @router.get(
        "/capabilities",
        operation_id="getStudioCapabilities",
        response_model=StudioCapabilitiesResponse,
    )
    def capabilities() -> StudioCapabilitiesResponse:
        return {
            "studio_version": "studio_v1",
            "schema_version": "classroom_package_v1",
            "quality_contract_version": "learning_quality_v1",
            "module_structure": "free_composition",
            "content_block_kinds": [kind.value for kind in ContentBlockKind],
            "mutable_operations_require_idempotency_key": True,
            "learner_analysis_capabilities": [],
            "chapter_authoring": {
                "requires_source_sections": True,
                "requires_knowledge_ledger": True,
                "requires_exact_coverage": True,
                "requires_chapter_overview": True,
                "core_modules_are_indispensable_questions": True,
                "requires_problem_progression": True,
                "requires_beginner_bridges": True,
                "requires_detailed_expansion_per_module": True,
                "rejects_shallow_expansions": True,
            },
            "autonomous_authoring": {
                "starts_from_uploaded_material": True,
                "asks_for_routine_confirmation": False,
                "asks_learner_for_internal_identifiers": False,
                "repairs_validation_and_preview_failures": True,
            },
            "live_learning_sessions": {
                "baseline_reveal_is_published_content": True,
                "supports_exact_target_expansion": True,
                "supports_nested_expansion": True,
                "requires_internal_identifiers_from_learner": False,
            },
            "teaching_model_workshop": {
                "contract_version": "teaching_model_v1",
                "supports_source_authoring": True,
                "requires_matching_preview_before_registration": True,
                "preview_jobs_are_durable": True,
                "requires_semantic_visual_evidence": True,
                "requires_interaction_change_evidence": True,
                "rejects_blank_or_noop_models": True,
            },
            "tool_protocol_version": "studio_tools_v1",
            "granted_tool_scopes": [scope.value for scope in ToolScope],
            "tool_execution": {
                "discovery_first": True,
                "default_quality_tier": "verified",
                "durable_jobs": True,
                "supports_cancellation": True,
                "supports_artifact_download": True,
                "experimental_outputs_publish_eligible": False,
            },
        }

    @router.get(
        "/workspace",
        operation_id="getStudioWorkspace",
        response_model=StudioWorkspaceResponse,
    )
    def workspace(
        request: Request,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=100),
    ) -> StudioWorkspaceResponse:
        public_origin = os.getenv(
            "AI_CLASSROOM_PUBLIC_ORIGIN",
            str(request.base_url),
        ).rstrip("/")
        return _map_errors(
            lambda: service_factory().workspace(
                public_origin=public_origin,
                offset=offset,
                limit=limit,
            )
        )

    @router.get(
        "/learning-sessions",
        operation_id="listLearningSessions",
    )
    def list_learning_sessions(
        limit: int = Query(default=20, ge=1, le=100),
    ) -> dict:
        return _map_errors(
            lambda: session_service_factory().list_for_studio(limit=limit)
        )

    @router.get(
        "/learning-sessions/{session_id}",
        operation_id="getStudioLearningSession",
    )
    def get_learning_session(session_id: str) -> dict:
        return _map_errors(
            lambda: session_service_factory().get_for_studio(
                session_id
            ).model_dump(mode="json", exclude_none=True)
        )

    @router.patch(
        "/learning-sessions/{session_id}/scene",
        operation_id="patchLearningSessionScene",
    )
    def patch_learning_session(
        session_id: str,
        request: PatchLearningSessionRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: session_service_factory().patch(
                session_id,
                ScenePatch.model_validate(request.model_dump(mode="json")),
                idempotency_key=idempotency_key,
            ).model_dump(mode="json", exclude_none=True)
        )

    @router.post(
        "/learning-sessions/{session_id}/return",
        operation_id="returnLearningSessionExpansion",
    )
    def return_learning_session_expansion(
        session_id: str,
        request: ReturnLearningSessionRequest,
        idempotency_key: str = Header(alias="Idempotency-Key", min_length=1),
    ) -> dict:
        return _map_errors(
            lambda: session_service_factory().return_to_parent(
                session_id,
                expected_revision=request.expected_revision,
                idempotency_key=idempotency_key,
            ).model_dump(mode="json", exclude_none=True)
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


def _map_errors(operation: Callable[[], Any]) -> Any:
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
    except ToolNotFoundError as exc:
        raise api_error(404, "studio_tool_not_found", str(exc))
    except ToolScopeDeniedError as exc:
        raise api_error(403, "studio_tool_scope_denied", str(exc))
    except ToolArgumentValidationError as exc:
        raise api_error(422, "studio_tool_arguments_invalid", str(exc))
    except ToolJobNotFoundError as exc:
        raise api_error(404, "tool_job_not_found", str(exc))
    except ToolJobRepositoryError as exc:
        raise api_error(400, "tool_job_repository_error", str(exc))
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
    except LearningSessionConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "learning_session_revision_conflict",
                "message": str(exc),
                "current_revision": exc.current_revision,
                "retryable": True,
                "next_action": "getStudioLearningSession",
            },
        )
    except LearningSessionNotFoundError as exc:
        raise api_error(404, "learning_session_not_found", str(exc))
    except LearningSessionRepositoryError as exc:
        raise api_error(400, "learning_session_error", str(exc))
    except ValueError as exc:
        raise api_error(422, "studio_request_invalid", str(exc))


router = create_studio_router()
