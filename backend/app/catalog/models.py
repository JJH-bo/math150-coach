from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.enums import QuestionType, ScoreDimension
from app.core.schemas import KnowledgeNode, Question, ScoringRubric


QUESTION_ID_PATTERN = re.compile(r"^[a-z0-9._-]{8,120}$")


def validate_question_id(value: str) -> str:
    """Validate immutable catalog question ids without exposing path details."""

    if not value.isascii() or not QUESTION_ID_PATTERN.fullmatch(value):
        raise ValueError("question_id must be 8-120 chars of lowercase ASCII letters, digits, dot, underscore, or hyphen.")
    return value


CatalogStatus = Literal["draft", "published", "retired"]
CatalogAudience = Literal["learner", "internal"]
RESERVED_VALIDATOR_CONFIG_KEYS = {
    "catalog_question_id",
    "question_id",
    "node_id",
    "question_version",
    "rubric_version",
    "answer_key_version",
    "expected_answer_aliases",
    "expected_answer",
    "answer_aliases",
    "rubric",
    "solution_outline",
    "score_overrides",
    "evidence_overrides",
    "manual_override",
    "scenario",
    "include_debug",
    "debug",
    "scorer_results",
    "diagnosis_trace",
    "evidence_sources",
    "raw_rollback_level",
    "raw_forward_level",
}


class CatalogManifestEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    logical_question_id: str
    question_family_id: str | None = None
    node_id: str
    status: CatalogStatus
    audience: CatalogAudience
    question_version: str
    rubric_version: str
    answer_key_version: str
    catalog_schema_version: str
    supersedes: str | None = None
    tags: list[str] = Field(default_factory=list)
    content_hash: str | None = None

    @field_validator("question_id", "logical_question_id", "question_family_id", "supersedes")
    @classmethod
    def validate_catalog_ids(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_question_id(value)


class PublicQuestionView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str
    node_id: str
    title: str
    stem: str
    prompt_markdown: str
    answer_format: str
    response_step_mode: str
    difficulty: str
    display_assets: list[dict[str, Any]] = Field(default_factory=list)
    hints_public: list[str] = Field(default_factory=list)

    @field_validator("question_id")
    @classmethod
    def validate_public_question_id(cls, value: str) -> str:
        return validate_question_id(value)


class TrustedQuestionSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_answer: str | None = None
    answer_aliases: list[str] = Field(default_factory=list)
    rubric: ScoringRubric | None = None
    solution_outline: str | None = None
    validator_config: dict[str, Any] = Field(default_factory=dict)
    scoring_notes_internal: str | None = None
    golden_case_refs: list[str] = Field(default_factory=list)
    authoring_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("validator_config")
    @classmethod
    def validator_config_must_not_override_reserved_metadata(cls, value: dict[str, Any]) -> dict[str, Any]:
        reserved_keys = sorted(set(value) & RESERVED_VALIDATOR_CONFIG_KEYS)
        if reserved_keys:
            raise ValueError(f"validator_config contains reserved metadata keys: {reserved_keys}")
        return value


class CatalogQuestionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    manifest: CatalogManifestEntry
    presentation: PublicQuestionView
    trusted_scoring: TrustedQuestionSpec

    @model_validator(mode="after")
    def validate_layer_consistency(self) -> "CatalogQuestionRecord":
        if self.presentation.question_id != self.manifest.question_id:
            raise ValueError("presentation.question_id must match manifest.question_id")
        if self.presentation.node_id != self.manifest.node_id:
            raise ValueError("presentation.node_id must match manifest.node_id")
        return self

    def is_learner_visible(self) -> bool:
        return self.manifest.status == "published" and self.manifest.audience == "learner"

    def to_public_question_view(self) -> PublicQuestionView:
        return self.presentation

    def to_domain_question(self, node: KnowledgeNode | None = None) -> Question:
        trusted = self.trusted_scoring
        metadata = {
            "catalog_question_id": self.manifest.question_id,
            "question_version": self.manifest.question_version,
            "rubric_version": self.manifest.rubric_version,
            "answer_key_version": self.manifest.answer_key_version,
            "expected_answer_aliases": list(trusted.answer_aliases),
            **trusted.validator_config,
        }
        tested_dimensions = self._tested_dimensions(node)
        return Question(
            id=self.manifest.question_id,
            node_id=self.manifest.node_id,
            question_type=QuestionType.DIAGNOSTIC,
            prompt=self.presentation.prompt_markdown,
            expected_answer=trusted.expected_answer,
            tested_dimensions=tested_dimensions,
            solution_outline=trusted.solution_outline,
            rubric=trusted.rubric,
            metadata=metadata,
        )

    def _tested_dimensions(self, node: KnowledgeNode | None) -> list[ScoreDimension]:
        dimensions: list[ScoreDimension] = []
        if self.trusted_scoring.rubric:
            for item in self.trusted_scoring.rubric.items:
                dimensions.extend(item.target_dimensions)
            for key_point in self.trusted_scoring.rubric.key_points:
                dimensions.extend(key_point.target_dimensions)
        if self.trusted_scoring.expected_answer:
            dimensions.extend([ScoreDimension.CALCULATION, ScoreDimension.FINAL_ANSWER])
        if not dimensions and node:
            dimensions.extend(node.core_dimensions)

        seen: set[ScoreDimension] = set()
        unique_dimensions: list[ScoreDimension] = []
        for dimension in dimensions:
            if dimension not in seen:
                seen.add(dimension)
                unique_dimensions.append(dimension)
        return unique_dimensions
