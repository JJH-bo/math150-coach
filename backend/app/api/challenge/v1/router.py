from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from pydantic import ValidationError

from app.api.challenge.v1.schemas import (
    ChallengeResetRequest,
    ChallengeStartRequest,
    ChallengeSubmitRequest,
    ChapterDraftHumanReviewRequest,
    ChapterDraftValidateRequest,
    parse_request,
)
from app.api.v1.schemas import api_error
from app.challenge.atlas import ChallengeAtlasBuilder
from app.challenge.engine import ChallengeEngine, ChallengeEngineError
from app.challenge.chapter_draft_importer import record_chapter_human_review, validate_chapter_markdown
from app.challenge.progress_store import ChallengeProgressError
from app.challenge.repository import ChallengeRepository, ChallengeRepositoryError
from app.logic_graph.quality_validator import KnowledgeGraphQualityValidator
from app.logic_graph.repository import LogicGraphRepository, LogicGraphRepositoryError
from app.training.session_log import SessionLogError, validate_session_id


router = APIRouter(prefix="/api/challenge/v1", tags=["challenge"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "api_type": "local_challenge"}


@router.get("/atlas")
def challenge_atlas() -> dict[str, Any]:
    try:
        return ChallengeAtlasBuilder().build()
    except ChallengeRepositoryError as exc:
        raise api_error(400, "challenge_error", str(exc))


@router.get("/quality/{chapter_id}")
def challenge_quality(chapter_id: str) -> dict[str, Any]:
    try:
        graph = ChallengeRepository().load_graph(chapter_id)
        logic_graph = LogicGraphRepository().try_load_graph(chapter_id)
        report = KnowledgeGraphQualityValidator().validate(graph, logic_graph)
        return {
            "mode": "runtime_graph_quality",
            "publish_state": "read_only",
            "chapter_id": graph.chapter_id,
            "report": _quality_report_payload(report),
        }
    except ChallengeRepositoryError as exc:
        raise api_error(400, "challenge_error", str(exc))
    except (LogicGraphRepositoryError, ValidationError):
        raise api_error(400, "challenge_error", "Runtime graph quality report is unavailable.")


def _quality_report_payload(report: Any) -> dict[str, Any]:
    return {
        "passed": report.passed,
        "issue_count": report.issue_count,
        "error_count": report.error_count,
        "warning_count": report.warning_count,
        "info_count": report.info_count,
        "issues": [
            {
                "severity": issue.severity.value,
                "code": issue.code,
            }
            for issue in report.issues
        ],
    }


@router.post("/authoring/chapter-draft/validate")
async def validate_chapter_draft(request: Request) -> dict[str, Any]:
    payload = await request.json()
    parsed = parse_request(ChapterDraftValidateRequest, payload)
    assert isinstance(parsed, ChapterDraftValidateRequest)
    return validate_chapter_markdown(parsed.markdown)


@router.post("/authoring/chapter-draft/human-review")
async def record_chapter_draft_human_review(request: Request) -> dict[str, Any]:
    payload = await request.json()
    parsed = parse_request(ChapterDraftHumanReviewRequest, payload)
    assert isinstance(parsed, ChapterDraftHumanReviewRequest)
    try:
        return record_chapter_human_review(
            parsed.markdown,
            reviewer=parsed.reviewer,
            decision=parsed.decision,
            checklist=parsed.checklist,
            notes=parsed.notes,
        )
    except ValueError as exc:
        raise api_error(400, "chapter_human_review_invalid", str(exc))


@router.post("/start")
async def start_challenge(request: Request) -> dict[str, Any]:
    payload = await request.json()
    parsed = parse_request(ChallengeStartRequest, payload)
    assert isinstance(parsed, ChallengeStartRequest)
    try:
        return ChallengeEngine().start(
            parsed.chapter_id,
            session_id=parsed.session_id,
            session_root=_session_root(),
        )
    except (ChallengeEngineError, ChallengeProgressError, ChallengeRepositoryError, SessionLogError) as exc:
        raise api_error(400, "challenge_error", str(exc))


@router.get("/status/{session_id}")
def challenge_status(session_id: str) -> dict[str, Any]:
    try:
        safe_session_id = validate_session_id(session_id)
        return ChallengeEngine().status(session_id=safe_session_id, session_root=_session_root())
    except (ChallengeEngineError, ChallengeProgressError, ChallengeRepositoryError, SessionLogError) as exc:
        raise api_error(400, "challenge_error", str(exc))


@router.post("/submit")
async def submit_challenge(request: Request) -> dict[str, Any]:
    payload = await request.json()
    parsed = parse_request(ChallengeSubmitRequest, payload)
    assert isinstance(parsed, ChallengeSubmitRequest)
    try:
        return ChallengeEngine().submit(
            session_id=parsed.session_id,
            answer=parsed.answer,
            steps=parsed.steps,
            explanation=parsed.explanation,
            session_root=_session_root(),
        )
    except (ChallengeEngineError, ChallengeProgressError, ChallengeRepositoryError, SessionLogError) as exc:
        raise api_error(400, "challenge_error", str(exc))


@router.post("/reset")
async def reset_challenge(request: Request) -> dict[str, Any]:
    payload = await request.json()
    parsed = parse_request(ChallengeResetRequest, payload)
    assert isinstance(parsed, ChallengeResetRequest)
    try:
        return ChallengeEngine().reset(
            session_id=parsed.session_id,
            node_id=parsed.node_id,
            reset_all=parsed.reset_all,
            session_root=_session_root(),
        )
    except (ChallengeEngineError, ChallengeProgressError, ChallengeRepositoryError, SessionLogError) as exc:
        raise api_error(400, "challenge_error", str(exc))


def _session_root() -> Path:
    configured = os.getenv("CHALLENGE_SESSION_ROOT")
    if configured:
        return Path(configured)
    return Path.cwd() / "training_sessions" / "challenge_api"
