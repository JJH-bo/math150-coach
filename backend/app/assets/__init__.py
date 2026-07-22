"""Persistent verified assets for published classrooms."""

from app.assets.models import AssetRecord
from app.assets.repository import AssetRepository

__all__ = ["AssetRecord", "AssetRepository"]
