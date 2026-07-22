from __future__ import annotations

from typing import Any

from app.classroom.hashing import content_hash
from app.tools.lesson_contracts import SemanticLesson


MINIMUM_FONT_SIZES = {
    "deck_title": 50,
    "slide_title": 35,
    "subheading": 24,
    "body": 16,
}


def normalize_lesson(arguments: dict[str, Any]) -> SemanticLesson:
    return SemanticLesson.model_validate(arguments)


def lesson_content_hash(lesson: SemanticLesson) -> str:
    return content_hash(lesson.model_dump(mode="json", exclude_none=True))


def validate_lesson(lesson: SemanticLesson) -> dict[str, Any]:
    slide_reports = []
    for slide in lesson.slides:
        visible_character_count = (
            len(slide.title)
            + len(slide.primary_claim)
            + sum(len(item) for item in slide.body)
            + sum(len(item) for item in slide.bullets)
            + len(slide.formula or "")
        )
        slide_reports.append(
            {
                "slide_id": slide.slide_id,
                "kind": slide.kind.value,
                "visible_character_count": visible_character_count,
                "body_item_count": len(slide.body),
                "bullet_count": len(slide.bullets),
                "has_formula": slide.formula is not None,
                "has_speaker_notes": slide.speaker_notes is not None,
            }
        )
    return {
        "passed": True,
        "schema_version": lesson.schema_version,
        "content_hash": lesson_content_hash(lesson),
        "slide_count": len(lesson.slides),
        "template": lesson.template.value,
        "narrative_arc": lesson.narrative_arc.value,
        "minimum_font_sizes": MINIMUM_FONT_SIZES,
        "slides": slide_reports,
        "findings": [],
    }
