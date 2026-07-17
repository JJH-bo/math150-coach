from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from fastapi import APIRouter

from app.api.v1.schemas import api_error
from app.classroom.repository import (
    ClassroomNotFoundError,
    ClassroomRepository,
    ClassroomRepositoryError,
)
from app.classroom.runtime import ClassroomRuntimeService


RuntimeFactory = Callable[[], ClassroomRuntimeService]


def default_runtime() -> ClassroomRuntimeService:
    root = Path(os.getenv("CLASSROOM_DATA_ROOT", Path.cwd() / "classroom_data"))
    return ClassroomRuntimeService(ClassroomRepository(root))


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


router = create_classroom_router()
