from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.classroom.v1.router import router as classroom_v1_router
from app.api.studio.v1.router import router as studio_v1_router
from app.config import AppProfile, resolve_app_profile


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
CLASSROOM_FRONTEND_DIR = FRONTEND_DIR / "classroom"
MODEL_RUNTIME_DIR = FRONTEND_DIR / "model-runtime"


def create_app(profile: AppProfile | str | None = None) -> FastAPI:
    resolved_profile = resolve_app_profile(profile)
    application = FastAPI(
        title="Math150 AI Classroom",
        version="1.0.0",
        description="GPT authoring Studio and read-only AI Classroom runtime.",
    )
    application.state.app_profile = resolved_profile.value

    if resolved_profile in {AppProfile.INTERNAL, AppProfile.MIXED}:
        application.include_router(studio_v1_router)
        action_contract = FastAPI(
            title="Math150 AI Classroom Studio Action",
            version=application.version,
            description=(
                "Authenticated authoring operations for publishing structured "
                "AI Classroom content and teaching models."
            ),
            docs_url=None,
            redoc_url=None,
        )
        action_contract.include_router(studio_v1_router)

        @application.get(
            "/api/studio/v1/action-schema.json",
            include_in_schema=False,
        )
        def studio_action_schema(request: Request) -> JSONResponse:
            schema = deepcopy(action_contract.openapi())
            schema["servers"] = [{"url": str(request.base_url).rstrip("/")}]
            return JSONResponse(
                schema,
                headers={"Cache-Control": "public, max-age=300"},
            )
    if resolved_profile in {AppProfile.LEARNER, AppProfile.MIXED}:
        application.include_router(classroom_v1_router)

        @application.get("/", include_in_schema=False)
        def classroom_entry() -> RedirectResponse:
            return RedirectResponse("/classroom/", status_code=307)

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

    @application.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "product": "ai_classroom",
            "app_profile": resolved_profile.value,
        }

    @application.get(
        "/privacy",
        include_in_schema=False,
        response_class=HTMLResponse,
    )
    def privacy() -> HTMLResponse:
        return HTMLResponse(
            """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Classroom Privacy</title>
  <style>
    body { max-width: 760px; margin: 0 auto; padding: 48px 24px;
           font: 16px/1.65 system-ui, sans-serif; color: #172033; }
    h1, h2 { line-height: 1.2; }
  </style>
</head>
<body>
  <h1>AI Classroom Privacy</h1>
  <p>Last updated: July 18, 2026.</p>
  <h2>What the Action stores</h2>
  <p>When you direct a Custom GPT to create or publish classroom material, the
  Action stores that submitted course structure, teaching content, model
  source, versions, and preview artifacts on the classroom service.</p>
  <h2>How the data is used</h2>
  <p>The stored data is used only to validate, preview, publish, and display
  the requested AI Classroom material. The service does not score learners,
  diagnose mistakes, infer mastery, schedule review, or build advertising
  profiles.</p>
  <h2>Access and retention</h2>
  <p>Authoring operations require a private bearer credential. Published
  classroom material is readable by the learner-facing site. Authoring data
  remains on the service until the service owner replaces or removes it.</p>
  <h2>Third parties</h2>
  <p>The classroom hosting provider processes service traffic and persistent
  storage. The Action does not sell classroom or learner data.</p>
</body>
</html>"""
        )

    return application


app = create_app()
