from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.classroom.hashing import content_hash
from app.classroom.models import ClassroomPackage
from classroom_fixtures import classroom_package_payload


def test_package_accepts_free_module_blocks_and_optional_segments() -> None:
    package = ClassroomPackage.model_validate(classroom_package_payload())

    module = package.courses[0].chapters[0].modules[0]
    assert module.id == "limit-core"
    assert len(module.blocks) == 2
    assert len(module.segments) == 1
    assert module.blocks[0].detail_branches[0].blocks[0].kind == "prose"


def test_module_can_use_only_continuous_blocks_without_segments() -> None:
    payload = classroom_package_payload()
    payload["courses"][0]["chapters"][0]["modules"][0]["segments"] = []

    module = ClassroomPackage.model_validate(payload).courses[0].chapters[0].modules[0]

    assert module.blocks
    assert module.segments == []


def test_module_can_use_only_segments_without_top_level_blocks() -> None:
    payload = classroom_package_payload()
    payload["courses"][0]["chapters"][0]["modules"][0]["blocks"] = []

    module = ClassroomPackage.model_validate(payload).courses[0].chapters[0].modules[0]

    assert module.blocks == []
    assert module.segments


def test_empty_module_is_rejected() -> None:
    payload = classroom_package_payload()
    module = payload["courses"][0]["chapters"][0]["modules"][0]
    module["blocks"] = []
    module["segments"] = []

    with pytest.raises(ValidationError, match="at least one block or segment"):
        ClassroomPackage.model_validate(payload)


def test_unknown_content_block_fields_are_rejected() -> None:
    payload = classroom_package_payload()
    payload["courses"][0]["chapters"][0]["modules"][0]["blocks"][0]["score"] = 1

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ClassroomPackage.model_validate(payload)


def test_content_hash_is_stable_across_mapping_order() -> None:
    payload = classroom_package_payload()
    reordered = {key: payload[key] for key in reversed(payload)}

    assert content_hash(payload) == content_hash(reordered)
    assert content_hash(payload).startswith("sha256:")
