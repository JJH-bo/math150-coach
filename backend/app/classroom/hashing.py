from __future__ import annotations

import hashlib
import json
from typing import Any

from pydantic import BaseModel


def canonical_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return canonical_value(value.model_dump(mode="json", exclude_none=True))
    if isinstance(value, dict):
        return {str(key): canonical_value(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [canonical_value(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        canonical_value(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def content_hash(value: Any) -> str:
    encoded = canonical_json(value).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"
