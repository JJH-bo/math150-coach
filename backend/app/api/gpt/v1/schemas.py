from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class GptDraftCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chapter_id: str = Field(
        pattern=r"^[a-z0-9][a-z0-9_-]{1,79}$",
    )
    title: str = Field(min_length=1, max_length=160)
    source_markdown: str = Field(min_length=1, max_length=750_000)
    client_request_id: str = Field(
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$",
    )
    contract_version: Literal["chapter-galaxy-v1"]


class GptDraftUpdateRequest(GptDraftCreateRequest):
    expected_revision: int = Field(ge=1)
