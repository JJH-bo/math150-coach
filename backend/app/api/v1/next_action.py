from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from app.api.v1.nodes import get_node_or_404
from app.api.v1.schemas import api_error, build_next_action_response, parse_attempt_request_payload
from app.services.learning_orchestrator import LearningOrchestrator, MovementConsistencyError


router = APIRouter(prefix="/next-action", tags=["next-action"])


@router.post("/get")
def get_next_action(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    request = parse_attempt_request_payload(payload)
    node = get_node_or_404(request.node_id)
    try:
        orchestrated = LearningOrchestrator().process(request.question, request.attempt, node)
    except HTTPException:
        raise
    except MovementConsistencyError as exc:
        raise api_error(500, "internal_engine_error", str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive API boundary
        raise api_error(500, "internal_engine_error", str(exc)) from exc
    return build_next_action_response(orchestrated, include_debug=request.options.include_debug)
