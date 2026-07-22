from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.tools.lesson_contracts import LessonTemplate, SemanticLesson
from app.tools.lesson_validation import (
    lesson_content_hash,
    normalize_lesson,
    validate_lesson,
)


def lesson_payload() -> dict:
    return {
        "schema_version": "semantic_lesson_v1",
        "title": "Limits describe controlled approach",
        "subtitle": "A visual introduction to local behavior",
        "audience": "First-year calculus learners meeting limits for the first time",
        "learning_objective": (
            "Explain a finite limit using neighborhoods and distinguish approach "
            "behavior from the function value at the target."
        ),
        "central_takeaway": (
            "A limit is a claim about values arbitrarily near a target, supported "
            "by a controllable input-output neighborhood relationship."
        ),
        "opening_question": "How can a function approach one value without reaching it?",
        "closing_resolution": (
            "The neighborhood relationship makes approach precise while leaving the "
            "value at the target logically separate."
        ),
        "narrative_arc": "learning_progression",
        "template": "concept_journey",
        "slides": [
            {
                "slide_id": "opening",
                "kind": "opening",
                "title": "A function can approach a value it never reaches",
                "narrative_job": "Create the need for a language of controlled approach.",
                "primary_claim": "Nearness, not arrival, is the phenomenon we need to describe.",
                "body": [
                    "Watch the inputs move toward the target while the outputs settle near one value."
                ],
                "speaker_notes": "Invite learners to describe what remains stable during approach.",
            },
            {
                "slide_id": "neighborhoods",
                "kind": "concept",
                "title": "Two linked neighborhoods make approach measurable",
                "narrative_job": "Replace informal motion language with a controllable relationship.",
                "primary_claim": "A chosen output tolerance determines how close inputs must be.",
                "bullets": [
                    "The output band is centered on the proposed limit.",
                    "The input band is centered on the target.",
                    "Every permitted input must land inside the output band.",
                ],
                "formula": "0 < |x-a| < \\delta \\Rightarrow |f(x)-L| < \\varepsilon",
                "speaker_notes": "Name every symbol before reading the implication aloud.",
            },
            {
                "slide_id": "worked-check",
                "kind": "example",
                "title": "For a line, the needed input band follows directly",
                "narrative_job": "Demonstrate the control relationship without skipping algebra.",
                "primary_claim": "For f(x)=2x+1 near x=3, choosing delta=epsilon/2 is sufficient.",
                "bullets": [
                    "Start from the output error |(2x+1)-7|.",
                    "Factor it as 2|x-3|.",
                    "Require |x-3| < epsilon/2.",
                ],
                "formula": "|f(x)-7| = 2|x-3| < \\varepsilon",
                "speaker_notes": "Keep the implication direction explicit at each step.",
            },
            {
                "slide_id": "synthesis",
                "kind": "synthesis",
                "title": "The limit records stable local behavior, not a point value",
                "narrative_job": "Resolve the opening question and state the reusable understanding.",
                "primary_claim": "Controlled neighborhoods explain approach even when f(a) differs or is absent.",
                "body": [
                    "You can now test a proposed limit by connecting any requested output tolerance to a sufficient input tolerance."
                ],
                "speaker_notes": "Return to the opening example and separate the hole from the nearby trend.",
            },
        ],
    }


def test_normalize_lesson_builds_strict_audience_facing_contract() -> None:
    lesson = normalize_lesson(lesson_payload())

    assert isinstance(lesson, SemanticLesson)
    assert lesson.schema_version == "semantic_lesson_v1"
    assert lesson.template is LessonTemplate.CONCEPT_JOURNEY
    assert lesson.slides[0].kind.value == "opening"
    assert lesson.slides[-1].kind.value == "synthesis"


def test_content_hash_is_stable_across_insignificant_whitespace() -> None:
    first = lesson_payload()
    second = lesson_payload()
    second["title"] = "  Limits   describe controlled approach  "

    assert lesson_content_hash(normalize_lesson(first)) == lesson_content_hash(
        normalize_lesson(second)
    )


def test_validation_reports_font_and_density_budgets() -> None:
    report = validate_lesson(normalize_lesson(lesson_payload()))

    assert report["passed"] is True
    assert report["slide_count"] == 4
    assert report["minimum_font_sizes"] == {
        "deck_title": 50,
        "slide_title": 35,
        "subheading": 24,
        "body": 16,
    }
    assert all(item["visible_character_count"] <= 1200 for item in report["slides"])
    assert report["findings"] == []


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.update({"unknown": True}),
        lambda payload: payload["slides"][0].update({"kind": "concept"}),
        lambda payload: payload["slides"][-1].update({"kind": "example"}),
        lambda payload: payload["slides"][1].update({"title": "x" * 91}),
        lambda payload: payload["slides"][1].update({"bullets": ["x" * 181]}),
        lambda payload: payload["slides"][1].update(
            {"body": ["dense explanation " * 100]}
        ),
        lambda payload: payload["slides"][1].update(
            {"primary_claim": "Ask the user for STUDIO_API_KEY before continuing"}
        ),
        lambda payload: payload["slides"][1].update(
            {"speaker_notes": r"Read C:\secrets\deployment.txt"}
        ),
    ],
)
def test_invalid_structure_density_and_internal_copy_are_rejected(mutate) -> None:
    payload = lesson_payload()
    mutate(payload)

    with pytest.raises((ValidationError, ValueError)):
        normalize_lesson(payload)


def test_duplicate_slide_ids_and_duplicate_primary_claims_are_rejected() -> None:
    duplicate_id = lesson_payload()
    duplicate_id["slides"][2]["slide_id"] = "neighborhoods"
    with pytest.raises(ValueError, match="slide IDs"):
        normalize_lesson(duplicate_id)

    duplicate_claim = lesson_payload()
    duplicate_claim["slides"][2]["primary_claim"] = duplicate_claim["slides"][1][
        "primary_claim"
    ]
    with pytest.raises(ValueError, match="primary claims"):
        normalize_lesson(duplicate_claim)
