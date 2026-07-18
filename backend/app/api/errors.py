from __future__ import annotations

from fastapi import HTTPException


def api_error(
    status_code: int,
    error_code: str,
    message: str,
    field_path: str | None = None,
) -> HTTPException:
    detail: dict[str, str] = {
        "error_code": error_code,
        "message": message,
    }
    if field_path is not None:
        detail["field_path"] = field_path
    return HTTPException(status_code=status_code, detail=detail)
