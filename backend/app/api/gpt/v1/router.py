from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ValidationError
import yaml

from app.api.gpt.v1.auth import require_gpt_authoring_key
from app.api.gpt.v1.schemas import (
    GptDraftCreateRequest,
    GptDraftUpdateRequest,
)
from app.challenge.gpt_authoring_contract import chapter_authoring_contract
from app.challenge.gpt_authoring_service import (
    DraftSubmission,
    GptAuthoringService,
)
from app.challenge.gpt_draft_store import (
    ChapterDraftStore,
    DraftNotFound,
    IdempotencyConflict,
    RevisionConflict,
)
from app.config import chapter_draft_root, public_base_url


router = APIRouter(prefix="/api/gpt/v1", tags=["gpt-authoring"])
ACTION_SCHEMA_PATH = (
    Path(__file__).resolve().parents[5]
    / "docs"
    / "custom-gpt"
    / "chapter-authoring-actions.openapi.yaml"
)


def _service() -> GptAuthoringService:
    return GptAuthoringService(
        ChapterDraftStore(chapter_draft_root()),
        public_base_url=public_base_url(),
    )


def _parse(
    model: type[BaseModel],
    payload: dict[str, Any],
) -> BaseModel:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        first = exc.errors()[0] if exc.errors() else {}
        raise HTTPException(
            status_code=422,
            detail={
                "error_code": "authoring_request_schema_invalid",
                "message": str(first.get("msg", "Invalid authoring request.")),
                "field": ".".join(str(item) for item in first.get("loc", ())),
            },
        ) from exc


def _domain_error(exc: Exception) -> HTTPException:
    if isinstance(exc, DraftNotFound):
        return HTTPException(
            status_code=404,
            detail={
                "error_code": "draft_not_found",
                "message": "The requested chapter draft was not found.",
            },
        )
    if isinstance(exc, IdempotencyConflict):
        return HTTPException(
            status_code=409,
            detail={
                "error_code": "idempotency_conflict",
                "message": "The request ID was already used with different content.",
            },
        )
    if isinstance(exc, RevisionConflict):
        return HTTPException(
            status_code=409,
            detail={
                "error_code": "revision_conflict",
                "message": "The draft has a newer revision.",
            },
        )
    return HTTPException(
        status_code=400,
        detail={
            "error_code": "chapter_draft_invalid",
            "message": str(exc),
        },
    )


@router.get(
    "/action-schema",
    include_in_schema=False,
    response_class=Response,
)
def get_action_schema(request: Request) -> Response:
    schema = yaml.safe_load(
        ACTION_SCHEMA_PATH.read_text(encoding="utf-8")
    )
    base_url = public_base_url() or str(request.base_url).rstrip("/")
    schema["servers"] = [{"url": base_url}]
    return Response(
        content=yaml.safe_dump(
            schema,
            allow_unicode=True,
            sort_keys=False,
        ),
        media_type="application/yaml",
    )


@router.get("/contract", operation_id="getProjectContract")
def get_project_contract(request: Request) -> dict[str, Any]:
    require_gpt_authoring_key(request)
    return chapter_authoring_contract()


@router.post(
    "/drafts",
    status_code=201,
    operation_id="createChapterDraft",
)
async def create_chapter_draft(request: Request) -> dict[str, Any]:
    require_gpt_authoring_key(request)
    parsed = _parse(
        GptDraftCreateRequest,
        await request.json(),
    )
    assert isinstance(parsed, GptDraftCreateRequest)
    try:
        return _service().create(
            DraftSubmission(**parsed.model_dump())
        )
    except (ValueError, DraftNotFound) as exc:
        raise _domain_error(exc)


@router.put(
    "/drafts/{draft_id}",
    operation_id="updateChapterDraft",
)
async def update_chapter_draft(
    draft_id: str,
    request: Request,
) -> dict[str, Any]:
    require_gpt_authoring_key(request)
    parsed = _parse(
        GptDraftUpdateRequest,
        await request.json(),
    )
    assert isinstance(parsed, GptDraftUpdateRequest)
    values = parsed.model_dump()
    expected_revision = int(values.pop("expected_revision"))
    try:
        return _service().revise(
            draft_id,
            expected_revision=expected_revision,
            submission=DraftSubmission(**values),
        )
    except (ValueError, DraftNotFound) as exc:
        raise _domain_error(exc)


@router.get(
    "/drafts/{draft_id}",
    operation_id="getChapterDraft",
)
def get_chapter_draft(
    draft_id: str,
    request: Request,
) -> dict[str, Any]:
    require_gpt_authoring_key(request)
    try:
        return _service().get(draft_id)
    except DraftNotFound as exc:
        raise _domain_error(exc)


@router.post(
    "/drafts/{draft_id}/validate",
    operation_id="validateChapterDraft",
)
def validate_chapter_draft(
    draft_id: str,
    request: Request,
) -> dict[str, Any]:
    require_gpt_authoring_key(request)
    try:
        return _service().validate(draft_id)
    except DraftNotFound as exc:
        raise _domain_error(exc)
