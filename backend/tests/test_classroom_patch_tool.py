from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.classroom.models import ClassroomPackage
from app.classroom.repository import ClassroomRepository
from app.classroom.validation import ClassroomPackageValidator
from app.tools.adapters.classroom_patch import (
    ClassroomPatchAdapter,
    ClassroomPatchInputError,
)
from app.tools.contracts import ToolExecutionContext
from classroom_fixtures import classroom_package_payload


def repository_with_draft(tmp_path: Path) -> tuple[ClassroomRepository, int]:
    repository = ClassroomRepository(tmp_path)
    package = ClassroomPackage.model_validate(classroom_package_payload())
    draft = repository.create_draft("editable-classroom", package)
    return repository, draft.revision


def replacement_block() -> dict:
    return {
        "id": "limit-intro",
        "kind": "prose",
        "knowledge_point_ids": ["kp-limit-neighborhood"],
        "data": {
            "markdown": "A limit follows nearby values rather than one isolated point."
        },
        "detail_branches": [],
    }


def inserted_block() -> dict:
    return {
        "id": "limit-neighborhood-check",
        "kind": "worked_example",
        "knowledge_point_ids": ["kp-limit-neighborhood"],
        "data": {
            "prompt": "Compare values on both sides of the target.",
            "steps": ["Use x=0.9.", "Use x=1.1.", "Compare the outputs."],
        },
        "detail_branches": [],
    }


def execute(tmp_path: Path, payload: dict):
    repository, _ = repository_with_draft(tmp_path / "data")
    adapter = ClassroomPatchAdapter(repository, ClassroomPackageValidator())
    return adapter.execute(
        payload,
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path / "work",
        ),
    )


def test_definition_is_verified_typed_non_mutating_classroom_editor(tmp_path: Path) -> None:
    repository, _ = repository_with_draft(tmp_path)
    definition = ClassroomPatchAdapter(
        repository, ClassroomPackageValidator()
    ).definition

    assert definition.tool_id == "classroom.patch"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.author"
    assert "operations" in definition.input_schema["required"]
    assert "json_pointer" not in definition.input_schema["properties"]
    assert "script" not in definition.input_schema["properties"]


def test_patch_replaces_and_inserts_blocks_without_mutating_draft(tmp_path: Path) -> None:
    repository, revision = repository_with_draft(tmp_path / "data")
    adapter = ClassroomPatchAdapter(repository, ClassroomPackageValidator())
    output = adapter.execute(
        {
            "draft_id": "editable-classroom",
            "expected_revision": revision,
            "operations": [
                {
                    "op": "replace_block",
                    "block_id": "limit-intro",
                    "block": replacement_block(),
                },
                {
                    "op": "insert_block",
                    "container_id": "limit-neighborhood-segment",
                    "index": 1,
                    "block": inserted_block(),
                },
            ],
        },
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path / "work",
        ),
    )

    assert output.result["operation_count"] == 2
    assert output.result["source_revision"] == revision
    assert output.result["source_content_hash"] != output.result["candidate_content_hash"]
    assert output.result["applied"] is False
    assert [artifact.name for artifact in output.artifacts] == [
        "patched-package.json",
        "patch-report.json",
    ]
    patched = json.loads(
        (tmp_path / "work" / "patched-package.json").read_text(encoding="utf-8")
    )
    blocks = patched["courses"][0]["chapters"][0]["modules"][0]["segments"][0][
        "blocks"
    ]
    assert [block["id"] for block in blocks[:2]] == [
        "limit-intro",
        "limit-neighborhood-check",
    ]
    assert blocks[0]["data"]["markdown"].startswith("A limit follows")
    unchanged = repository.get_draft("editable-classroom")
    assert unchanged.revision == revision
    original = unchanged.package.courses[0].chapters[0].modules[0].segments[0].blocks[0]
    assert original.data["markdown"] != blocks[0]["data"]["markdown"]


@pytest.mark.parametrize(
    "mutate, message",
    [
        (lambda payload: payload.update({"expected_revision": 99}), "revision"),
        (
            lambda payload: payload["operations"][0].update(
                {
                    "block_id": "missing-block",
                    "block": {**replacement_block(), "id": "missing-block"},
                }
            ),
            "not found",
        ),
        (
            lambda payload: payload["operations"][0].update(
                {"block": {**replacement_block(), "id": "changed-id"}}
            ),
            "preserve",
        ),
        (
            lambda payload: payload["operations"][0].update(
                {"script": "fetch('/secrets')"}
            ),
            "fields",
        ),
    ],
)
def test_patch_rejects_stale_unknown_or_unsafe_operations(
    tmp_path: Path, mutate, message: str
) -> None:
    repository, revision = repository_with_draft(tmp_path)
    adapter = ClassroomPatchAdapter(repository, ClassroomPackageValidator())
    payload = {
        "draft_id": "editable-classroom",
        "expected_revision": revision,
        "operations": [
            {
                "op": "replace_block",
                "block_id": "limit-intro",
                "block": replacement_block(),
            }
        ],
    }
    mutate(payload)

    with pytest.raises(ClassroomPatchInputError, match=message):
        adapter.execute(
            payload,
            ToolExecutionContext(
                job_id="tj-000000000000000000000000",
                work_dir=tmp_path / "work",
            ),
        )


def test_patch_rejects_structurally_invalid_candidate(tmp_path: Path) -> None:
    repository, revision = repository_with_draft(tmp_path)
    adapter = ClassroomPatchAdapter(repository, ClassroomPackageValidator())

    with pytest.raises(ClassroomPatchInputError, match="structurally invalid"):
        adapter.execute(
            {
                "draft_id": "editable-classroom",
                "expected_revision": revision,
                "operations": [
                    {
                        "op": "replace_module",
                        "module_id": "limit-core",
                        "module": {
                            **classroom_package_payload()["courses"][0]["chapters"][0][
                                "modules"
                            ][0],
                            "segments": [],
                        },
                    }
                ],
            },
            ToolExecutionContext(
                job_id="tj-000000000000000000000000",
                work_dir=tmp_path / "work",
            ),
        )
