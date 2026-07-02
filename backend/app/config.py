from __future__ import annotations

import os
from enum import Enum


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

