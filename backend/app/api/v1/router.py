from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import diagnosis, health, next_action, nodes, score, submit_attempt


router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(nodes.router)
router.include_router(score.router)
router.include_router(diagnosis.router)
router.include_router(next_action.router)
router.include_router(submit_attempt.router)
