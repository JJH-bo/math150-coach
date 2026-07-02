from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(tags=["learner-health"])


@router.get("/health")
def learner_health() -> dict[str, object]:
    return {
        "status": "ok",
        "phase": "phase_4_0_lite_learner_api",
        "api_type": "learner_public",
        "capabilities": [
            "published_question_catalog",
            "learner_safe_attempt_submit",
            "server_side_trusted_question_hydration",
        ],
    }

