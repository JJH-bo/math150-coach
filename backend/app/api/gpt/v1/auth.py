from __future__ import annotations

import hmac
import os

from fastapi import HTTPException, Request


def require_gpt_authoring_key(request: Request) -> None:
    configured = os.getenv("GPT_AUTHORING_KEY", "").strip()
    if not configured:
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "authoring_not_configured",
                "message": "GPT authoring is disabled until a key is configured.",
            },
        )
    supplied = request.headers.get("Authorization", "")
    expected = f"Bearer {configured}"
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "authoring_auth_invalid",
                "message": "A valid GPT authoring key is required.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
