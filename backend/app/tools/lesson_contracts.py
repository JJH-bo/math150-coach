from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


INTERNAL_COPY = re.compile(
    r"(?:STUDIO_API_KEY|OPENAI_API_KEY|Idempotency-Key|\bdraft_id\b|"
    r"\bjob_id\b|\bsystem prompt\b|\binternal id\b|"
    r"[A-Za-z]:\\|/(?:var|etc|home)/)",
    re.IGNORECASE,
)
WHITESPACE = re.compile(r"[ \t\r\f\v]+")


class LessonTemplate(str, Enum):
    CONCEPT_JOURNEY = "concept_journey"
    WORKED_EXAMPLES = "worked_examples"
    VISUAL_EXPLAINER = "visual_explainer"
    SEMINAR = "seminar"


class LessonNarrativeArc(str, Enum):
    LEARNING_PROGRESSION = "learning_progression"
    QUESTION_ANALYSIS_ANSWER = "question_analysis_answer"
    CLAIM_EVIDENCE_CONSEQUENCE = "claim_evidence_consequence"


class LessonSlideKind(str, Enum):
    OPENING = "opening"
    CONCEPT = "concept"
    STEPS = "steps"
    EXAMPLE = "example"
    COMPARISON = "comparison"
    VISUAL = "visual"
    SYNTHESIS = "synthesis"


def normalize_text(value: str) -> str:
    lines = [WHITESPACE.sub(" ", line).strip() for line in value.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def reject_internal_copy(value: str, field_name: str) -> str:
    if INTERNAL_COPY.search(value):
        raise ValueError(f"{field_name} contains internal operations, secrets, or paths")
    return value


class StrictLessonModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LessonSlide(StrictLessonModel):
    slide_id: str = Field(pattern=r"^[a-z][a-z0-9-]{0,79}$")
    kind: LessonSlideKind
    title: str = Field(min_length=1, max_length=90)
    narrative_job: str = Field(min_length=20, max_length=240)
    primary_claim: str = Field(min_length=20, max_length=240)
    body: list[str] = Field(default_factory=list, max_length=4)
    bullets: list[str] = Field(default_factory=list, max_length=6)
    formula: str | None = Field(default=None, max_length=500)
    speaker_notes: str | None = Field(default=None, max_length=3000)

    @field_validator(
        "title",
        "narrative_job",
        "primary_claim",
        "formula",
        "speaker_notes",
        mode="before",
    )
    @classmethod
    def normalize_scalar_text(cls, value, info):
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = normalize_text(value)
        return reject_internal_copy(normalized, info.field_name)

    @field_validator("body", "bullets", mode="before")
    @classmethod
    def normalize_text_lists(cls, value, info):
        if not isinstance(value, list):
            return value
        maximum = 320 if info.field_name == "body" else 180
        output = []
        for item in value:
            if not isinstance(item, str):
                output.append(item)
                continue
            normalized = reject_internal_copy(normalize_text(item), info.field_name)
            if not normalized or len(normalized) > maximum:
                raise ValueError(
                    f"{info.field_name} items must contain 1 to {maximum} characters"
                )
            output.append(normalized)
        return output

    @model_validator(mode="after")
    def require_teachable_content_and_density(self):
        if not self.body and not self.bullets and not self.formula:
            raise ValueError("each slide requires body, bullets, or a formula")
        visible = (
            len(self.title)
            + len(self.primary_claim)
            + sum(len(item) for item in self.body)
            + sum(len(item) for item in self.bullets)
            + len(self.formula or "")
        )
        if visible > 1200:
            raise ValueError("slide visible copy exceeds the 1200-character density budget")
        return self


class SemanticLesson(StrictLessonModel):
    schema_version: Literal["semantic_lesson_v1"]
    title: str = Field(min_length=1, max_length=80)
    subtitle: str | None = Field(default=None, max_length=160)
    audience: str = Field(min_length=20, max_length=300)
    learning_objective: str = Field(min_length=40, max_length=600)
    central_takeaway: str = Field(min_length=40, max_length=600)
    opening_question: str = Field(min_length=20, max_length=300)
    closing_resolution: str = Field(min_length=40, max_length=600)
    narrative_arc: LessonNarrativeArc
    template: LessonTemplate
    slides: list[LessonSlide] = Field(min_length=3, max_length=30)

    @field_validator(
        "title",
        "subtitle",
        "audience",
        "learning_objective",
        "central_takeaway",
        "opening_question",
        "closing_resolution",
        mode="before",
    )
    @classmethod
    def normalize_root_text(cls, value, info):
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = normalize_text(value)
        return reject_internal_copy(normalized, info.field_name)

    @model_validator(mode="after")
    def validate_narrative_sequence(self):
        if self.slides[0].kind is not LessonSlideKind.OPENING:
            raise ValueError("the first slide must be an opening")
        if self.slides[-1].kind is not LessonSlideKind.SYNTHESIS:
            raise ValueError("the final slide must be a synthesis")
        if any(
            slide.kind is LessonSlideKind.OPENING for slide in self.slides[1:]
        ):
            raise ValueError("opening slides may appear only at the beginning")
        if any(
            slide.kind is LessonSlideKind.SYNTHESIS for slide in self.slides[:-1]
        ):
            raise ValueError("synthesis slides may appear only at the end")
        slide_ids = [slide.slide_id for slide in self.slides]
        if len(slide_ids) != len(set(slide_ids)):
            raise ValueError("slide IDs must be unique")
        claims = [slide.primary_claim.casefold() for slide in self.slides]
        if len(claims) != len(set(claims)):
            raise ValueError("primary claims must be unique")
        return self
