from __future__ import annotations

import hmac
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response

from app.api.chapter_review.v1.schemas import (
    ApproveDraftRequest,
    RejectDraftRequest,
    ReviewSessionRequest,
)
from app.api.gpt.v1.auth import (
    establish_review_session,
    require_review_session,
)
from app.challenge.chapter_draft_importer import HUMAN_REVIEW_CHECKS
from app.challenge.chapter_publish_executor import (
    APPROVAL_PHRASE,
    execute_chapter_controlled_publish,
)
from app.challenge.chapter_publish_plan import (
    build_chapter_publish_plan_dry_run,
)
from app.challenge.gpt_authoring_service import GptAuthoringService
from app.challenge.gpt_draft_store import (
    ChapterDraftStore,
    DraftNotFound,
    RevisionConflict,
)
from app.config import (
    chapter_draft_root,
    chapter_publish_target_root,
    public_base_url,
)


router = APIRouter(
    prefix="/api/chapter-review",
    tags=["chapter-review"],
)


def _store() -> ChapterDraftStore:
    return ChapterDraftStore(chapter_draft_root())


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={
            "error_code": "draft_not_found",
            "message": "The requested chapter draft was not found.",
        },
    )


def _revision_mismatch() -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={
            "error_code": "approval_revision_mismatch",
            "message": "The displayed revision no longer matches the draft.",
        },
    )


@router.post("/session", status_code=204)
def create_review_session(
    payload: ReviewSessionRequest,
    response: Response,
) -> Response:
    establish_review_session(payload.review_key, response)
    response.status_code = 204
    return response


@router.get("/{draft_id}/metadata")
def get_review_metadata(
    draft_id: str,
    request: Request,
) -> dict[str, Any]:
    require_review_session(request)
    try:
        return GptAuthoringService(
            _store(),
            public_base_url=public_base_url(),
        ).get(draft_id)
    except DraftNotFound as exc:
        raise _not_found() from exc


@router.post("/{draft_id}/approve")
def approve_draft(
    draft_id: str,
    payload: ApproveDraftRequest,
    request: Request,
) -> dict[str, Any]:
    require_review_session(request)
    store = _store()
    try:
        current = store.load(draft_id)
        selected = store.load(draft_id, payload.revision)
    except DraftNotFound as exc:
        raise _not_found() from exc

    if (
        int(current["revision"]) != payload.revision
        or not hmac.compare_digest(
            str(selected["content_hash"]),
            payload.content_hash,
        )
    ):
        raise _revision_mismatch()
    if current.get("status") != "preview_ready":
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "preview_not_ready",
                "message": "Only a validated preview can be published.",
            },
        )

    checklist = {
        code: True
        for code, _description in HUMAN_REVIEW_CHECKS
    }
    notes = (
        f"Approved draft {draft_id} revision {payload.revision}"
    )
    plan = build_chapter_publish_plan_dry_run(
        selected["source_markdown"],
        reviewer="chapter-review-ui",
        decision="approve_for_candidate",
        checklist=checklist,
        notes=notes,
    )
    if plan.get("publish_plan_grade") != "ready":
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "publish_plan_not_ready",
                "message": "The approved draft did not pass publish planning.",
                "blocking_reasons": plan.get("blocking_reasons", []),
            },
        )

    result = execute_chapter_controlled_publish(
        selected["source_markdown"],
        reviewer="chapter-review-ui",
        decision="approve_for_candidate",
        checklist=checklist,
        notes=notes,
        target_root=chapter_publish_target_root(),
        allow_write=True,
        approval_phrase=APPROVAL_PHRASE,
        expected_publish_plan_hash=plan["publish_plan_hash"],
    )
    if result.get("status") != "published":
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "publish_failed",
                "message": "Controlled publish did not complete.",
                "blocking_reasons": result.get("blocking_reasons", []),
            },
        )

    store.mark_published(
        draft_id,
        revision=payload.revision,
        content_hash=payload.content_hash,
        publish_result=result,
    )
    base = public_base_url()
    result["formal_url"] = (
        f"{base}/trainer/space/galaxy-lab/"
        f"?chapter={selected['chapter_id']}"
    )
    return result


@router.post("/{draft_id}/reject")
def reject_draft(
    draft_id: str,
    payload: RejectDraftRequest,
    request: Request,
) -> dict[str, Any]:
    require_review_session(request)
    try:
        record = _store().mark_rejected(
            draft_id,
            revision=payload.revision,
            reason=payload.reason,
        )
    except DraftNotFound as exc:
        raise _not_found() from exc
    except RevisionConflict as exc:
        raise _revision_mismatch() from exc
    return {
        "draft_id": record["draft_id"],
        "chapter_id": record["chapter_id"],
        "revision": record["revision"],
        "status": record["status"],
        "reason": record["rejection_reason"],
    }
