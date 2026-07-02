from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from app.api.v1.nodes import get_node_or_404
from app.api.v1.schemas import api_error, build_score_response, parse_attempt_request_payload
from app.services.composite_scoring_engine import CompositeScoringEngine


router = APIRouter(prefix="/score", tags=["score"])


@router.post("/evaluate")
def evaluate_score(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    request = parse_attempt_request_payload(payload)
    node = get_node_or_404(request.node_id)
    try:
        score_result = CompositeScoringEngine().evaluate_detailed(request.question, request.attempt, node)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive API boundary
        raise api_error(500, "internal_engine_error", str(exc)) from exc
    return build_score_response(score_result, include_debug=request.options.include_debug)
