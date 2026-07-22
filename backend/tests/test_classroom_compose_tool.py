from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.classroom.validation import ClassroomPackageValidator
from app.tools.adapters.classroom_compose import (
    ClassroomComposeAdapter,
    ClassroomComposeInputError,
)
from app.tools.contracts import ToolExecutionContext
from classroom_fixtures import classroom_package_payload


def execute(tmp_path: Path, arguments: dict):
    return ClassroomComposeAdapter(ClassroomPackageValidator()).execute(
        arguments,
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def test_compose_definition_is_verified_complete_and_non_mutating() -> None:
    definition = ClassroomComposeAdapter(ClassroomPackageValidator()).definition

    assert definition.tool_id == "classroom.compose"
    assert definition.version == "1.0.0"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.author"
    assert definition.input_schema["required"] == ["package"]
    assert "script" not in definition.input_schema["properties"]
    assert "semantic_publish_validation" in definition.quality_gates


def test_compose_validates_a_complete_publish_ready_package(tmp_path: Path) -> None:
    output = execute(tmp_path, {"package": classroom_package_payload()})

    assert output.result["package_id"] == "calculus-foundations"
    assert output.result["schema_version"] == "classroom_package_v1"
    assert output.result["publish_ready"] is True
    assert output.result["applied"] is False
    assert output.result["counts"] == {
        "courses": 1,
        "chapters": 1,
        "modules": 1,
        "segments": 3,
        "blocks": 5,
        "detail_branches": 1,
        "knowledge_points": 3,
        "assets": 0,
        "model_instances": 0,
        "bindings": 0,
    }
    assert output.result["validation"] == {"passed": True, "issues": []}


def test_compose_returns_repairable_semantic_report_without_publishing(
    tmp_path: Path,
) -> None:
    package = classroom_package_payload()
    package["courses"][0]["chapters"][0]["coverage_audit"][
        "unresolved_items"
    ] = ["kp-limit-definition"]

    output = execute(tmp_path, {"package": package})

    assert output.result["publish_ready"] is False
    assert output.result["applied"] is False
    assert any(
        issue["severity"] == "error"
        for issue in output.result["validation"]["issues"]
    )
    assert output.warnings == [
        "Composed package is structurally valid but not publish-ready; repair every validation error."
    ]


@pytest.mark.parametrize(
    "arguments, message",
    [
        ({"package": {"schema_version": "classroom_package_v1"}}, "structurally invalid"),
        (
            {"package": classroom_package_payload(), "script": "read('/etc/passwd')"},
            "unsupported",
        ),
    ],
)
def test_compose_rejects_incomplete_or_executable_inputs(
    tmp_path: Path, arguments: dict, message: str
) -> None:
    with pytest.raises(ClassroomComposeInputError, match=message):
        execute(tmp_path, arguments)


def test_compose_artifacts_are_canonical_and_deterministic(tmp_path: Path) -> None:
    output = execute(tmp_path, {"package": classroom_package_payload()})

    assert [artifact.name for artifact in output.artifacts] == [
        "composed-package.json",
        "composition-report.json",
    ]
    package = json.loads(
        (tmp_path / "composed-package.json").read_text(encoding="utf-8")
    )
    report = json.loads(
        (tmp_path / "composition-report.json").read_text(encoding="utf-8")
    )
    assert package["package_id"] == output.result["package_id"]
    assert report["package_content_hash"] == output.result["package_content_hash"]
    assert report["next_action"].startswith("Call createClassroomDraft")
