from __future__ import annotations

import base64
import hashlib
import hmac
import os
import time

from fastapi import HTTPException, Request, Response

from app.config import public_base_url


REVIEW_COOKIE_NAME = "chapter_review_session"
DEFAULT_REVIEW_SESSION_TTL_SECONDS = 8 * 60 * 60


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


def establish_review_session(
    supplied_key: str,
    response: Response,
) -> None:
    configured = _review_key()
    authoring_key = os.getenv("GPT_AUTHORING_KEY", "").strip()
    if not configured or configured == authoring_key:
        raise HTTPException(
            status_code=503,
            detail={
                "error_code": "review_not_configured",
                "message": "A distinct human review key is required.",
            },
        )
    if not hmac.compare_digest(supplied_key, configured):
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "review_auth_invalid",
                "message": "The human review key is invalid.",
            },
        )
    response.set_cookie(
        REVIEW_COOKIE_NAME,
        issue_review_session(),
        max_age=_review_ttl_seconds(),
        httponly=True,
        secure=public_base_url().startswith("https://"),
        samesite="strict",
        path="/",
    )


def issue_review_session(now: int | None = None) -> str:
    issued_at = int(time.time() if now is None else now)
    payload = f"chapter-review:{issued_at}"
    signature = hmac.new(
        _review_key().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    encoded = base64.urlsafe_b64encode(
        f"{payload}:{signature}".encode("utf-8")
    ).decode("ascii")
    return encoded.rstrip("=")


def require_review_session(
    request: Request,
    *,
    now: int | None = None,
) -> None:
    token = request.cookies.get(REVIEW_COOKIE_NAME, "")
    current_time = int(time.time() if now is None else now)
    if not _valid_review_token(token, current_time):
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "review_auth_required",
                "message": "A valid human review session is required.",
            },
        )


def _valid_review_token(token: str, now: int) -> bool:
    if not token or not _review_key():
        return False
    try:
        padding = "=" * (-len(token) % 4)
        decoded = base64.urlsafe_b64decode(
            token + padding
        ).decode("utf-8")
        prefix, issued_text, supplied_signature = decoded.split(":", 2)
        issued_at = int(issued_text)
    except (ValueError, UnicodeDecodeError):
        return False
    if prefix != "chapter-review":
        return False
    age = now - issued_at
    if age < 0 or age > _review_ttl_seconds():
        return False
    payload = f"{prefix}:{issued_at}"
    expected = hmac.new(
        _review_key().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(supplied_signature, expected)


def _review_key() -> str:
    return os.getenv("CHAPTER_REVIEW_KEY", "").strip()


def _review_ttl_seconds() -> int:
    raw = os.getenv(
        "CHAPTER_REVIEW_SESSION_TTL_SECONDS",
        str(DEFAULT_REVIEW_SESSION_TTL_SECONDS),
    )
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_REVIEW_SESSION_TTL_SECONDS
    return min(max(value, 300), 24 * 60 * 60)
