from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.errors import api_error
from app.assets.repository import (
    AssetNotFoundError,
    AssetRepository,
    AssetRepositoryError,
)
from app.classroom.model_repository import (
    ModelNotFoundError,
    ModelRepositoryError,
    TeachingModelRepository,
)
from app.classroom.repository import (
    ClassroomNotFoundError,
    ClassroomRepository,
    ClassroomRepositoryError,
)
from app.classroom.runtime import ClassroomRuntimeService
from app.classroom.session_repository import (
    LearningSessionConflictError,
    LearningSessionNotFoundError,
    LearningSessionRepository,
    LearningSessionRepositoryError,
)
from app.classroom.sessions import (
    LearningSessionAccessError,
    LearningSessionService,
)


RuntimeFactory = Callable[[], ClassroomRuntimeService]
SessionServiceFactory = Callable[[], LearningSessionService]


class RuntimeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateLearningSessionRequest(RuntimeRequest):
    package_id: str = Field(min_length=1, max_length=120)
    module_id: str = Field(min_length=1, max_length=120)


class LearningSessionMutationRequest(RuntimeRequest):
    access_token: str = Field(min_length=20, max_length=200)
    expected_revision: int = Field(ge=1)


class LearningSessionInteractionRequest(LearningSessionMutationRequest):
    active_content_id: str = Field(min_length=1, max_length=120)


class LearningSessionReturnRequest(LearningSessionMutationRequest):
    idempotency_key: str = Field(min_length=1, max_length=200)


def default_runtime() -> ClassroomRuntimeService:
    root = Path(os.getenv("CLASSROOM_DATA_ROOT", Path.cwd() / "classroom_data"))
    seed = Path(__file__).resolve().parents[4] / "classroom_data" / "model_seed"
    return ClassroomRuntimeService(
        ClassroomRepository(root),
        model_repository=TeachingModelRepository(root, seed_root=seed),
        asset_repository=AssetRepository(root),
    )


def default_session_service() -> LearningSessionService:
    root = Path(os.getenv("CLASSROOM_DATA_ROOT", Path.cwd() / "classroom_data"))
    return LearningSessionService(
        LearningSessionRepository(root / "learning-sessions.sqlite3"),
        default_runtime(),
    )


def create_classroom_router(
    runtime_factory: RuntimeFactory = default_runtime,
    *,
    session_service_factory: SessionServiceFactory = default_session_service,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/classroom/v1",
        tags=["classroom-runtime"],
    )

    @router.get("/catalog", operation_id="getClassroomCatalog")
    def catalog() -> dict:
        return runtime_factory().catalog()

    @router.get("/models", operation_id="listRuntimeTeachingModels")
    def models() -> dict:
        return _map_errors(lambda: runtime_factory().models())

    @router.get(
        "/models/{model_id}/versions/{version}",
        operation_id="getRuntimeTeachingModel",
    )
    def model(model_id: str, version: str) -> dict:
        return _map_errors(lambda: runtime_factory().model(model_id, version))

    @router.get(
        "/models/{model_id}/versions/{version}/source.js",
        operation_id="getRuntimeTeachingModelSource",
        response_class=Response,
    )
    def model_source(model_id: str, version: str) -> Response:
        source = _map_errors(
            lambda: {"source": runtime_factory().model_source(model_id, version)}
        )["source"]
        return Response(
            content=source,
            media_type="application/javascript",
        )

    @router.get(
        "/assets/{asset_id}",
        operation_id="getClassroomAsset",
        response_class=FileResponse,
    )
    def asset(asset_id: str, request: Request):
        record, path = _map_errors(
            lambda: {"asset": runtime_factory().asset(asset_id)}
        )["asset"]
        etag = f'"{record.content_hash.removeprefix("sha256:")}"'
        headers = {
            "ETag": etag,
            "Cache-Control": "public, max-age=31536000, immutable",
            "X-Content-Type-Options": "nosniff",
        }
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers=headers)
        return FileResponse(
            path,
            media_type=record.media_type,
            headers=headers,
        )

    @router.get(
        "/packages/{package_id}",
        operation_id="getActiveClassroomPackage",
    )
    def active_package(package_id: str) -> dict:
        return _map_errors(
            lambda: runtime_factory().active_package(package_id)
        )

    @router.get(
        "/packages/{package_id}/modules/{module_id}",
        operation_id="getClassroomModule",
    )
    def module(package_id: str, module_id: str) -> dict:
        return _map_errors(
            lambda: runtime_factory().module(package_id, module_id)
        )

    @router.post(
        "/learning-sessions",
        status_code=201,
        operation_id="createLearningSession",
    )
    def create_learning_session(request: CreateLearningSessionRequest) -> dict:
        return _map_errors(
            lambda: session_service_factory().create(
                package_id=request.package_id,
                module_id=request.module_id,
            ).model_dump(mode="json", exclude_none=True)
        )

    @router.get(
        "/learning-sessions/{session_id}",
        operation_id="getLearningSession",
    )
    def get_learning_session(
        session_id: str,
        access_token: str = Query(min_length=20, max_length=200),
    ) -> dict:
        return _map_errors(
            lambda: session_service_factory().get_for_learner(
                session_id,
                access_token=access_token,
            ).model_dump(mode="json", exclude_none=True)
        )

    @router.post(
        "/learning-sessions/{session_id}/reveal",
        operation_id="revealLearningStep",
    )
    def reveal_learning_step(
        session_id: str,
        request: LearningSessionMutationRequest,
    ) -> dict:
        return _map_errors(
            lambda: session_service_factory().reveal(
                session_id,
                access_token=request.access_token,
                expected_revision=request.expected_revision,
            ).model_dump(mode="json", exclude_none=True)
        )

    @router.post(
        "/learning-sessions/{session_id}/interactions",
        operation_id="setLearningSessionFocus",
    )
    def set_learning_session_focus(
        session_id: str,
        request: LearningSessionInteractionRequest,
    ) -> dict:
        return _map_errors(
            lambda: session_service_factory().set_active_content(
                session_id,
                access_token=request.access_token,
                expected_revision=request.expected_revision,
                content_id=request.active_content_id,
            ).model_dump(mode="json", exclude_none=True)
        )

    @router.post(
        "/learning-sessions/{session_id}/return",
        operation_id="returnFromLearningExpansion",
    )
    def return_from_learning_expansion(
        session_id: str,
        request: LearningSessionReturnRequest,
    ) -> dict:
        return _map_errors(
            lambda: session_service_factory().return_for_learner(
                session_id,
                access_token=request.access_token,
                expected_revision=request.expected_revision,
                idempotency_key=request.idempotency_key,
            ).model_dump(mode="json", exclude_none=True)
        )

    @router.get(
        "/learning-sessions/{session_id}/events",
        operation_id="streamLearningSessionEvents",
        response_class=StreamingResponse,
    )
    def stream_learning_session_events(
        session_id: str,
        access_token: str = Query(min_length=20, max_length=200),
        after_revision: int = Query(default=0, ge=0),
    ) -> StreamingResponse:
        events = _map_errors(
            lambda: {
                "events": session_service_factory().events(
                    session_id,
                    access_token=access_token,
                    after_revision=after_revision,
                )
            }
        )["events"]

        def stream():
            for event in events:
                payload = json.dumps(
                    event.model_dump(mode="json", exclude_none=True),
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
                yield (
                    f"id: {event.revision}\n"
                    f"event: {event.kind}\n"
                    f"data: {payload}\n\n"
                )
            yield "retry: 1000\n\n"

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    return router


def _map_errors(operation: Callable[[], dict]) -> dict:
    try:
        return operation()
    except ClassroomNotFoundError as exc:
        raise api_error(404, "classroom_not_found", str(exc))
    except ClassroomRepositoryError as exc:
        raise api_error(400, "classroom_repository_error", str(exc))
    except AssetNotFoundError as exc:
        raise api_error(404, "classroom_asset_not_found", str(exc))
    except AssetRepositoryError as exc:
        raise api_error(500, "classroom_asset_repository_error", str(exc))
    except ModelNotFoundError as exc:
        raise api_error(404, "teaching_model_not_found", str(exc))
    except ModelRepositoryError as exc:
        raise api_error(400, "teaching_model_repository_error", str(exc))
    except LearningSessionAccessError as exc:
        raise api_error(403, "learning_session_access_denied", str(exc))
    except LearningSessionConflictError as exc:
        raise api_error(409, "learning_session_revision_conflict", str(exc))
    except LearningSessionNotFoundError as exc:
        raise api_error(404, "learning_session_not_found", str(exc))
    except LearningSessionRepositoryError as exc:
        raise api_error(400, "learning_session_error", str(exc))


router = create_classroom_router()
