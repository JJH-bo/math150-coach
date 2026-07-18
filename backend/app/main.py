from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.classroom.v1.router import router as classroom_v1_router
from app.api.challenge.v1.router import router as challenge_v1_router
from app.api.learner.v1.router import router as learner_v1_router
from app.api.studio.v1.router import router as studio_v1_router
from app.api.v1.router import router as api_v1_router
from app.config import AppProfile, resolve_app_profile


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
CLASSROOM_FRONTEND_DIR = FRONTEND_DIR / "classroom"
MODEL_RUNTIME_DIR = FRONTEND_DIR / "model-runtime"


def create_app(profile: AppProfile | str | None = None) -> FastAPI:
    resolved_profile = resolve_app_profile(profile)
    application = FastAPI(
        title="Math150 AI Classroom",
        version="0.2.0",
        description="AI Classroom Studio and runtime alongside isolated legacy APIs.",
    )
    application.state.app_profile = resolved_profile.value

    if resolved_profile in {AppProfile.INTERNAL, AppProfile.MIXED}:
        application.include_router(api_v1_router)
        application.include_router(studio_v1_router)
    if resolved_profile in {AppProfile.LEARNER, AppProfile.MIXED}:
        application.include_router(learner_v1_router)
        application.include_router(classroom_v1_router)
        if MODEL_RUNTIME_DIR.exists():
            application.mount(
                "/classroom-runtime",
                StaticFiles(directory=MODEL_RUNTIME_DIR),
                name="classroom-model-runtime",
            )
        if CLASSROOM_FRONTEND_DIR.exists():
            application.mount(
                "/classroom",
                StaticFiles(directory=CLASSROOM_FRONTEND_DIR, html=True),
                name="classroom",
            )
    if resolved_profile == AppProfile.MIXED:
        application.include_router(challenge_v1_router)
        if FRONTEND_DIR.exists():
            application.mount("/trainer", StaticFiles(directory=FRONTEND_DIR, html=True), name="trainer")

    @application.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "phase": "phase_4_1_profile_gating",
            "app_profile": resolved_profile.value,
        }

    return application


app = create_app()
