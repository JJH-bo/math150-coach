from __future__ import annotations

import hashlib
import json
from typing import Any

from app.catalog.models import CatalogQuestionRecord


def canonical_runtime_record_payload(record: CatalogQuestionRecord) -> dict[str, Any]:
    """Return the deterministic runtime artifact payload used for authoring hashes."""

    payload = record.model_dump(mode="json")
    payload["manifest"].pop("content_hash", None)
    payload["trusted_scoring"].pop("authoring_metadata", None)
    return payload


def compute_runtime_content_hash(record: CatalogQuestionRecord) -> str:
    payload = canonical_runtime_record_payload(record)
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
