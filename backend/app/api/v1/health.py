from __future__ import annotations

from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "phase": "phase_3_1_internal_dev_api",
        "capabilities": [
            "scoring",
            "diagnosis",
            "rollback_forward_movement",
            "deterministic_next_action",
            "ode_sample_nodes",
        ],
        "api_type": "internal_dev",
    }
