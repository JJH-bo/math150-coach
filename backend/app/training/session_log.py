from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")

TRUSTED_FIELD_DENYLIST = {
    "expected_answer",
    "answer_aliases",
    "rubric",
    "solution_outline",
    "validator_config",
    "trusted_scoring",
    "answer_key",
    "scorer_results",
    "diagnosis_trace",
    "debug_trace",
    "evidence_sources",
    "raw_rollback_level",
    "raw_forward_level",
    "score_overrides",
    "evidence_overrides",
    "manual_override",
    "scenario",
    "include_debug",
    "source_metadata",
    "validation_report",
    "review_checklist",
}


class SessionLogError(ValueError):
    """Raised when a local training session log would violate the safety boundary."""


def default_session_id() -> str:
    return datetime.now(UTC).strftime("session-%Y%m%dT%H%M%SZ")


def validate_session_id(session_id: str) -> str:
    if not SESSION_ID_PATTERN.fullmatch(session_id):
        raise SessionLogError("session_id must use only letters, digits, underscore, dot, or hyphen")
    return session_id


def resolve_session_root(session_root: str | Path | None = None) -> Path:
    if session_root is None:
        return (Path.cwd() / "training_sessions").resolve(strict=False)

    raw_path = Path(session_root)
    if ".." in raw_path.parts:
        raise SessionLogError("session_root must not contain parent-directory traversal")

    resolved = raw_path.resolve(strict=False)
    _reject_forbidden_workspace_location(resolved)
    return resolved


def append_attempt(record: dict[str, Any], session_id: str, session_root: str | Path | None = None) -> Path:
    safe_session_id = validate_session_id(session_id)
    ensure_no_trusted_fields(record)
    root = resolve_session_root(session_root)
    root.mkdir(parents=True, exist_ok=True)
    output_path = root / f"{safe_session_id}.jsonl"
    ensure_no_trusted_fields(record)
    with output_path.open("a", encoding="utf-8") as file:
        json.dump(record, file, ensure_ascii=False, sort_keys=True)
        file.write("\n")
    return output_path


def ensure_no_trusted_fields(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in TRUSTED_FIELD_DENYLIST:
                raise SessionLogError(f"trusted field is not allowed in local session log: {path}.{key}")
            ensure_no_trusted_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            ensure_no_trusted_fields(child, f"{path}[{index}]")


def _reject_forbidden_workspace_location(resolved: Path) -> None:
    repo_root = Path(__file__).resolve().parents[3]
    forbidden_roots = [
        repo_root / "backend" / "catalog_data",
        repo_root / "backend" / "catalog_authoring",
        repo_root / "docs",
        repo_root / "backend" / "tests",
        repo_root / "tests",
    ]
    for forbidden_root in forbidden_roots:
        try:
            resolved.relative_to(forbidden_root.resolve(strict=False))
        except ValueError:
            continue
        raise SessionLogError(f"session_root cannot point inside protected project area: {forbidden_root}")
