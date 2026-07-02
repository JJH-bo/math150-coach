from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from app.api.learner.v1.questions import question_not_found
from app.api.learner.v1.schemas import parse_learner_attempt_payload
from app.api.v1.nodes import get_node_or_404
from app.api.v1.schemas import api_error
from app.catalog.learner_projector import LearnerAttemptAssembler, LearnerResponseProjector
from app.catalog.yaml_repository import get_catalog_repository
from app.services.learning_orchestrator import LearningOrchestrator, MovementConsistencyError


router = APIRouter(prefix="/attempts", tags=["learner-attempts"])


@router.post("/submit")
def submit_learner_attempt(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    request = parse_learner_attempt_payload(payload)
    record = get_catalog_repository().get_published(request.question_id)
    if record is None:
        raise question_not_found()

    node = get_node_or_404(record.manifest.node_id)
    question = record.to_domain_question(node)
    attempt = LearnerAttemptAssembler().to_attempt(
        question_id=request.question_id,
        user_answer=request.user_answer,
        response_steps=request.response_steps,
        self_explanation=request.self_explanation,
    )
    try:
        orchestrated = LearningOrchestrator().process(question, attempt, node)
    except HTTPException:
        raise
    except MovementConsistencyError as exc:
        raise api_error(500, "internal_engine_error", str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive API boundary
        raise api_error(500, "internal_engine_error", str(exc)) from exc
    return LearnerResponseProjector().from_orchestrated(orchestrated)

