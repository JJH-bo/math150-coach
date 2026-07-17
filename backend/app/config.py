from __future__ import annotations

import os
from enum import Enum
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class AppProfile(str, Enum):
    LEARNER = "learner"
    INTERNAL = "internal"
    MIXED = "mixed"


class AppProfileConfigError(ValueError):
    """Raised when APP_PROFILE is not one of the supported deployment profiles."""


def resolve_app_profile(profile: AppProfile | str | None = None) -> AppProfile:
    """Resolve an app profile.

    Explicit arguments are used for tests and app factories. The environment is
    read only when no explicit profile is supplied.
    """

    raw_profile = profile if profile is not None else os.getenv("APP_PROFILE", AppProfile.MIXED.value)
    if isinstance(raw_profile, AppProfile):
        return raw_profile
    normalized = str(raw_profile).strip().lower()
    try:
        return AppProfile(normalized)
    except ValueError as exc:
        supported = ", ".join(item.value for item in AppProfile)
        raise AppProfileConfigError(f"Invalid APP_PROFILE: {raw_profile}. Expected one of: {supported}.") from exc


def chapter_draft_root() -> Path:
    configured = os.getenv("CHAPTER_DRAFT_ROOT", "").strip()
    return (
        Path(configured).expanduser().resolve()
        if configured
        else (PROJECT_ROOT / "runtime" / "chapter_drafts").resolve()
    )


def public_base_url() -> str:
    return os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")


def chapter_publish_target_root() -> Path:
    configured = os.getenv("CHAPTER_PUBLISH_TARGET_ROOT", "").strip()
    return (
        Path(configured).expanduser().resolve()
        if configured
        else PROJECT_ROOT.resolve()
    )

