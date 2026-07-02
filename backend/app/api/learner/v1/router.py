from __future__ import annotations

from fastapi import APIRouter

from app.api.learner.v1 import attempts, health, questions


router = APIRouter(prefix="/api/learner/v1")
router.include_router(health.router)
router.include_router(questions.router)
router.include_router(attempts.router)

