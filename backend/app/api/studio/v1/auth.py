from __future__ import annotations

import os
import secrets

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.v1.schemas import api_error


bearer = HTTPBearer(auto_error=False)


def require_studio_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> None:
    configured = os.getenv("STUDIO_API_KEY", "")
    if not configured:
        raise api_error(
            503,
            "studio_api_key_not_configured",
            "STUDIO_API_KEY is not configured.",
        )
    provided = credentials.credentials if credentials else ""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise api_error(
            401,
            "studio_auth_required",
            "Studio bearer authentication is required.",
        )
    if not secrets.compare_digest(provided, configured):
        raise api_error(
            401,
            "studio_auth_invalid",
            "Studio bearer authentication failed.",
        )
