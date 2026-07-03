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
    ChapterControlledPublishRequest,
    ChapterDraftCandidateDryRunRequest,
    ChapterDraftHumanReviewRequest,
    ChapterDraftValidateRequest,
    ChapterIntelligentGenerateRequest,
    parse_request,
)
from app.api.v1.schemas import api_error
from app.challenge.atlas import ChallengeAtlasBuilder
from app.challenge.chapter_registry import ChapterRuntimeRegistry, ChapterRuntimeRegistryError
from app.challenge.engine import ChallengeEngine, ChallengeEngineError
from app.challenge.chapter_candidate_builder import build_chapter_candidate_dry_run
from app.challenge.chapter_draft_importer import record_chapter_human_review, validate_chapter_markdown
from app.challenge.chapter_intelligent_importer import build_intelligent_chapter_draft
from app.challenge.chapter_publish_executor import execute_chapter_controlled_publish
from app.challenge.chapter_publish_plan import build_chapter_publish_plan_dry_run
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


@router.get("/chapters/registry")
def challenge_chapter_registry() -> dict[str, Any]:
    return ChapterRuntimeRegistry().build()


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


@router.post("/authoring/chapter-draft/intelligent-generate")
async def intelligent_generate_chapter_draft(request: Request) -> dict[str, Any]:
    payload = await request.json()
    parsed = parse_request(ChapterIntelligentGenerateRequest, payload)
    assert isinstance(parsed, ChapterIntelligentGenerateRequest)
    return build_intelligent_chapter_draft(
        parsed.source_text,
        chapter_id=parsed.chapter_id,
        title=parsed.title,
        build_candidate=parsed.build_candidate,
    )


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


@router.post("/authoring/chapter-draft/candidate-dry-run")
async def chapter_draft_candidate_dry_run(request: Request) -> dict[str, Any]:
    return await _chapter_draft_candidate_dry_run_payload(request)


@router.post("/authoring/chapter-draft/candidate-build-dry-run")
async def chapter_draft_candidate_build_dry_run(request: Request) -> dict[str, Any]:
    return await _chapter_draft_candidate_dry_run_payload(request)


async def _chapter_draft_candidate_dry_run_payload(request: Request) -> dict[str, Any]:
    payload = await request.json()
    parsed = parse_request(ChapterDraftCandidateDryRunRequest, payload)
    assert isinstance(parsed, ChapterDraftCandidateDryRunRequest)
    try:
        return build_chapter_candidate_dry_run(
            parsed.markdown,
            reviewer=parsed.reviewer,
            decision=parsed.decision,
            checklist=parsed.checklist,
            notes=parsed.notes,
        )
    except ValueError as exc:
        raise api_error(400, "chapter_candidate_dry_run_invalid", str(exc))


@router.post("/authoring/chapter-draft/publish-plan-dry-run")
async def chapter_draft_publish_plan_dry_run(request: Request) -> dict[str, Any]:
    payload = await request.json()
    parsed = parse_request(ChapterDraftCandidateDryRunRequest, payload)
    assert isinstance(parsed, ChapterDraftCandidateDryRunRequest)
    try:
        return build_chapter_publish_plan_dry_run(
            parsed.markdown,
            reviewer=parsed.reviewer,
            decision=parsed.decision,
            checklist=parsed.checklist,
            notes=parsed.notes,
        )
    except ValueError as exc:
        raise api_error(400, "chapter_publish_plan_dry_run_invalid", str(exc))


@router.post("/authoring/chapter-draft/controlled-publish")
async def chapter_draft_controlled_publish(request: Request) -> dict[str, Any]:
    payload = await request.json()
    parsed = parse_request(ChapterControlledPublishRequest, payload)
    assert isinstance(parsed, ChapterControlledPublishRequest)
    if parsed.allow_write and not _controlled_publish_api_writes_enabled():
        raise api_error(
            403,
            "chapter_controlled_publish_write_disabled",
            "Controlled publish writes through the HTTP API are disabled by default.",
        )
    try:
        return execute_chapter_controlled_publish(
            parsed.markdown,
            reviewer=parsed.reviewer,
            decision=parsed.decision,
            checklist=parsed.checklist,
            notes=parsed.notes,
            target_root=_controlled_publish_target_root(),
            allow_write=parsed.allow_write,
            approval_phrase=parsed.approval_phrase,
            expected_publish_plan_hash=parsed.expected_publish_plan_hash,
        )
    except ValueError as exc:
        raise api_error(400, "chapter_controlled_publish_invalid", str(exc))


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
    except (ChallengeEngineError, ChapterRuntimeRegistryError, ChallengeProgressError, ChallengeRepositoryError, SessionLogError) as exc:
        raise api_error(400, "challenge_error", str(exc))


@router.get("/status/{session_id}")
def challenge_status(session_id: str) -> dict[str, Any]:
    try:
        safe_session_id = validate_session_id(session_id)
        return ChallengeEngine().status(session_id=safe_session_id, session_root=_session_root())
    except (ChallengeEngineError, ChapterRuntimeRegistryError, ChallengeProgressError, ChallengeRepositoryError, SessionLogError) as exc:
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
    except (ChallengeEngineError, ChapterRuntimeRegistryError, ChallengeProgressError, ChallengeRepositoryError, SessionLogError) as exc:
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
    except (ChallengeEngineError, ChapterRuntimeRegistryError, ChallengeProgressError, ChallengeRepositoryError, SessionLogError) as exc:
        raise api_error(400, "challenge_error", str(exc))


def _session_root() -> Path:
    configured = os.getenv("CHALLENGE_SESSION_ROOT")
    if configured:
        return Path(configured)
    return Path.cwd() / "training_sessions" / "challenge_api"


def _controlled_publish_api_writes_enabled() -> bool:
    return os.getenv("CHAPTER_CONTROLLED_PUBLISH_API_WRITES", "").strip().lower() in {"1", "true", "yes"}


def _controlled_publish_target_root() -> Path | None:
    configured = os.getenv("CHAPTER_CONTROLLED_PUBLISH_TARGET_ROOT")
    if configured:
        return Path(configured)
    return None
