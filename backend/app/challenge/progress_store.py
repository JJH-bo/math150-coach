from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from app.challenge.models import ChallengeProgress
from app.training.session_log import (
    SessionLogError,
    ensure_no_trusted_fields,
    resolve_session_root,
    validate_session_id,
)


class ChallengeProgressError(ValueError):
    """Raised when local challenge progress cannot be read or written safely."""


class ChallengeProgressStore:
    def progress_path(self, session_id: str, session_root: str | Path | None = None) -> Path:
        safe_session_id = validate_session_id(session_id)
        root = resolve_session_root(session_root)
        return root / f"{safe_session_id}.challenge_progress.json"

    def exists(self, session_id: str, session_root: str | Path | None = None) -> bool:
        return self.progress_path(session_id, session_root).exists()

    def load(self, session_id: str, session_root: str | Path | None = None) -> ChallengeProgress:
        path = self.progress_path(session_id, session_root)
        if not path.exists():
            raise ChallengeProgressError(f"challenge progress not found for session_id: {session_id}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return ChallengeProgress.model_validate(data)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            raise ChallengeProgressError(f"invalid challenge progress file: {path}") from exc

    def save(self, progress: ChallengeProgress, session_root: str | Path | None = None) -> Path:
        path = self.progress_path(progress.session_id, session_root)
        payload = progress.model_dump(mode="json", exclude_none=True)
        ensure_no_trusted_fields(payload)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        except (OSError, SessionLogError) as exc:
            raise ChallengeProgressError(str(exc)) from exc
        return path

