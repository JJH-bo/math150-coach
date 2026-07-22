from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictAssetModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AssetRecord(StrictAssetModel):
    asset_id: str = Field(pattern=r"^a-[a-f0-9]{64}$")
    content_hash: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    metadata_hash: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    media_type: Literal["image/png", "image/jpeg", "image/webp"]
    extension: Literal["png", "jpg", "webp"]
    width: int = Field(ge=1, le=6000)
    height: int = Field(ge=1, le=6000)
    size_bytes: int = Field(ge=1, le=8 * 1024 * 1024)
    display_filename: str = Field(min_length=1, max_length=120)
    uri: str = Field(pattern=r"^/api/classroom/v1/assets/a-[a-f0-9]{64}$")
    created_at: str = Field(min_length=20, max_length=40)
