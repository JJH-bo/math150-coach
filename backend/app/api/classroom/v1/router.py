from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter, Response

from app.api.v1.schemas import api_error
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


RuntimeFactory = Callable[[], ClassroomRuntimeService]


def default_runtime() -> ClassroomRuntimeService:
    root = Path(os.getenv("CLASSROOM_DATA_ROOT", Path.cwd() / "classroom_data"))
    seed = Path(__file__).resolve().parents[4] / "classroom_data" / "model_seed"
    return ClassroomRuntimeService(
        ClassroomRepository(root),
        model_repository=TeachingModelRepository(root, seed_root=seed),
    )


def create_classroom_router(
    runtime_factory: RuntimeFactory = default_runtime,
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

    return router


def _map_errors(operation: Callable[[], dict]) -> dict:
    try:
        return operation()
    except ClassroomNotFoundError as exc:
        raise api_error(404, "classroom_not_found", str(exc))
    except ClassroomRepositoryError as exc:
        raise api_error(400, "classroom_repository_error", str(exc))
    except ModelNotFoundError as exc:
        raise api_error(404, "teaching_model_not_found", str(exc))
    except ModelRepositoryError as exc:
        raise api_error(400, "teaching_model_repository_error", str(exc))


router = create_classroom_router()
