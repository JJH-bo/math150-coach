from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.tools.adapters.lesson_templates import (
    TemplateInputError,
    TemplateInstantiateAdapter,
    TemplateListAdapter,
)
from app.tools.contracts import ToolExecutionContext


def context(tmp_path: Path) -> ToolExecutionContext:
    return ToolExecutionContext(job_id="tj-000000000000000000000000", work_dir=tmp_path)


def test_template_list_ranks_by_teaching_intent_not_subject(tmp_path: Path) -> None:
    adapter = TemplateListAdapter()
    output = adapter.execute(
        {
            "learning_intent": "visual_mechanism",
            "output_mode": "browser",
            "interaction_required": True,
            "max_results": 3,
        },
        context(tmp_path),
    )

    assert adapter.definition.tool_id == "template.list"
    assert adapter.definition.quality_tier.value == "verified"
    assert output.result["recommendations"][0]["template_id"] == "visual_explainer"
    assert output.result["recommendations"][0]["score"] > output.result["recommendations"][1]["score"]
    assert output.result["selection_basis"] == [
        "learning_intent",
        "output_mode",
        "interaction_required",
    ]
    catalog = json.loads((tmp_path / "template-catalog.json").read_text("utf-8"))
    assert {item["template_id"] for item in catalog["templates"]} == {
        "concept_journey",
        "worked_examples",
        "visual_explainer",
        "seminar",
    }


def test_template_instantiate_creates_semantic_blueprint(tmp_path: Path) -> None:
    adapter = TemplateInstantiateAdapter()
    output = adapter.execute(
        {
            "template_id": "worked_examples",
            "title": "Solving first-order linear equations",
            "audience": "Learners beginning algebra who can perform arithmetic operations",
            "learning_objective": "Solve and check a first-order linear equation while explaining each inverse operation.",
            "output_mode": "presentation",
        },
        context(tmp_path),
    )

    assert adapter.definition.tool_id == "template.instantiate"
    assert adapter.definition.required_scope.value == "studio.author"
    blueprint = json.loads((tmp_path / "lesson-blueprint.json").read_text("utf-8"))
    assert blueprint["schema_version"] == "semantic_lesson_blueprint_v1"
    assert blueprint["semantic_template"] == "worked_examples"
    assert blueprint["slide_blueprints"][0]["kind"] == "opening"
    assert blueprint["slide_blueprints"][-1]["kind"] == "synthesis"
    assert any(item["kind"] == "example" for item in blueprint["slide_blueprints"])
    assert output.result["required_next_step"] == "author_and_validate_semantic_lesson_v1"


def test_templates_support_compact_chinese_context_and_output_compatibility(
    tmp_path: Path,
) -> None:
    recommendations = TemplateListAdapter().execute(
        {
            "learning_intent": "visual_mechanism",
            "output_mode": "document",
            "interaction_required": False,
            "max_results": 4,
        },
        context(tmp_path / "list"),
    ).result["recommendations"]
    blueprint = TemplateInstantiateAdapter().execute(
        {
            "template_id": "concept_journey",
            "title": "导数的局部变化率",
            "audience": "高中二年级理科学生",
            "learning_objective": "理解导数如何描述局部变化率，并能用一个具体函数解释几何意义。",
            "output_mode": "document",
        },
        context(tmp_path / "instantiate"),
    ).result["blueprint"]

    assert "visual_explainer" not in {
        item["template_id"] for item in recommendations
    }
    assert blueprint["audience"] == "高中二年级理科学生"


@pytest.mark.parametrize(
    "adapter,payload",
    [
        (TemplateListAdapter(), {"learning_intent": "subject_math"}),
        (
            TemplateInstantiateAdapter(),
            {
                "template_id": "unknown",
                "title": "x",
                "audience": "a" * 30,
                "learning_objective": "b" * 50,
                "output_mode": "browser",
            },
        ),
        (
            TemplateInstantiateAdapter(),
            {
                "template_id": "seminar",
                "title": "x",
                "audience": "short",
                "learning_objective": "b" * 50,
                "output_mode": "browser",
            },
        ),
    ],
)
def test_invalid_template_requests_fail(tmp_path: Path, adapter, payload) -> None:
    with pytest.raises(TemplateInputError):
        adapter.execute(payload, context(tmp_path))
