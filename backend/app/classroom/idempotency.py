from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.classroom.hashing import content_hash


class IdempotencyConflictError(ValueError):
    pass


class IdempotencyLedger:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def execute(
        self,
        scope: str,
        key: str,
        request_payload: Any,
        operation: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        request_hash = content_hash(request_payload)
        path = self._path(scope, key)
        if path.exists():
            stored = json.loads(path.read_text(encoding="utf-8"))
            if stored["request_hash"] != request_hash:
                raise IdempotencyConflictError(
                    f"idempotency key {key!r} was reused with a different request"
                )
            return dict(stored["response"])
        response = operation()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(f".{os.getpid()}.tmp")
        temporary.write_text(
            json.dumps(
                {"request_hash": request_hash, "response": response},
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return response

    def _path(self, scope: str, key: str) -> Path:
        digest = hashlib.sha256(f"{scope}:{key}".encode("utf-8")).hexdigest()
        return self.root / f"{digest}.json"
