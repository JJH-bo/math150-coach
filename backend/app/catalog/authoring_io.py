from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.catalog.authoring_models import AuthoringDraft, HumanReviewChecklist
from app.catalog.import_manifest import ImportManifest


class AuthoringPathError(ValueError):
    """Raised when an authoring path is missing or escapes its allowed root."""


class AuthoringParseError(ValueError):
    """Raised when YAML cannot be parsed."""


def resolve_inside(
    path: str | Path,
    root: str | Path,
    *,
    label: str = "path",
    must_exist: bool = True,
) -> Path:
    root_path = Path(root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root_path / candidate
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root_path)
    except ValueError as exc:
        raise AuthoringPathError(f"{label} escapes authoring root: {path}") from exc
    if must_exist and not resolved.exists():
        raise AuthoringPathError(f"{label} not found: {path}")
    return resolved


def safe_load_yaml(path: str | Path) -> Any:
    try:
        with Path(path).open("r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}
    except yaml.YAMLError as exc:
        raise AuthoringParseError(f"invalid YAML: {path}") from exc
    except OSError as exc:
        raise AuthoringPathError(str(exc)) from exc


def load_authoring_draft(path: str | Path, authoring_root: str | Path) -> AuthoringDraft:
    resolved = resolve_inside(path, authoring_root, label="draft path")
    data = safe_load_yaml(resolved)
    return AuthoringDraft.model_validate(data)


def load_import_manifest(path: str | Path, authoring_root: str | Path) -> ImportManifest:
    resolved = resolve_inside(path, authoring_root, label="import manifest path")
    data = safe_load_yaml(resolved)
    return ImportManifest.model_validate(data)


def load_review_checklist(path: str | Path, authoring_root: str | Path) -> HumanReviewChecklist:
    resolved = resolve_inside(path, authoring_root, label="review checklist path")
    data = safe_load_yaml(resolved)
    return HumanReviewChecklist.model_validate(data)


def write_json_report(payload: dict[str, Any], output_path: str | Path, allowed_root: str | Path) -> Path:
    resolved = resolve_inside(output_path, allowed_root, label="output path", must_exist=False)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, sort_keys=True, indent=2)
        file.write("\n")
    return resolved


def write_yaml_preview(payload: dict[str, Any], output_path: str | Path, allowed_root: str | Path) -> Path:
    resolved = resolve_inside(output_path, allowed_root, label="preview path", must_exist=False)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    with resolved.open("w", encoding="utf-8") as file:
        yaml.safe_dump(payload, file, allow_unicode=True, sort_keys=False)
    return resolved


def validation_error_message(exc: ValidationError) -> str:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(part) for part in first_error.get("loc", []))
    message = first_error.get("msg", str(exc))
    return f"{location}: {message}" if location else str(message)
