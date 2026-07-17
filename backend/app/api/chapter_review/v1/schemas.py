from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ReviewSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    review_key: str = Field(min_length=1, max_length=512)


class ApproveDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision: int = Field(ge=1)
    content_hash: str = Field(
        pattern=r"^sha256:[0-9a-f]{64}$",
    )


class RejectDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    revision: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=500)
