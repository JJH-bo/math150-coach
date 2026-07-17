from __future__ import annotations

import json

import pytest

from app.classroom.models import ClassroomPackage
from app.classroom.repository import (
    ClassroomConflictError,
    ClassroomPathError,
    ClassroomRepository,
)
from classroom_fixtures import classroom_package_payload


def package() -> ClassroomPackage:
    return ClassroomPackage.model_validate(classroom_package_payload())


def test_create_and_update_draft_use_revisions_and_atomic_json(tmp_path) -> None:
    repository = ClassroomRepository(tmp_path)
    created = repository.create_draft("limits-draft", package())
    payload = created.package.model_copy(update={"title": "更新后的课堂"})

    updated = repository.update_draft("limits-draft", 1, payload)

    assert created.revision == 1
    assert updated.revision == 2
    assert repository.get_draft("limits-draft").package.title == "更新后的课堂"
    stored = json.loads((tmp_path / "drafts" / "limits-draft.json").read_text("utf-8"))
    assert stored["revision"] == 2
    assert not list((tmp_path / "drafts").glob("*.tmp"))


def test_stale_draft_revision_is_rejected(tmp_path) -> None:
    repository = ClassroomRepository(tmp_path)
    repository.create_draft("limits-draft", package())

    with pytest.raises(ClassroomConflictError, match="expected revision 2"):
        repository.update_draft("limits-draft", 2, package())


def test_publish_creates_immutable_release_and_active_pointer(tmp_path) -> None:
    repository = ClassroomRepository(tmp_path)
    repository.create_draft("limits-draft", package())

    receipt = repository.publish("limits-draft", 1)
    active = repository.get_active_release("calculus-foundations")

    assert receipt.action == "publish"
    assert receipt.active_version.startswith("r-")
    assert active.version == receipt.active_version
    assert active.package.package_id == "calculus-foundations"


def test_rollback_repoints_active_release_without_mutating_release(tmp_path) -> None:
    repository = ClassroomRepository(tmp_path)
    repository.create_draft("limits-draft", package())
    first = repository.publish("limits-draft", 1)
    changed = package().model_copy(update={"title": "第二版"})
    repository.update_draft("limits-draft", 1, changed)
    second = repository.publish("limits-draft", 2)

    receipt = repository.rollback("calculus-foundations", first.active_version)

    assert receipt.previous_version == second.active_version
    assert repository.get_active_release("calculus-foundations").version == first.active_version
    assert (
        tmp_path
        / "packages"
        / "calculus-foundations"
        / "releases"
        / f"{second.active_version}.json"
    ).exists()


def test_path_traversal_identifiers_are_rejected(tmp_path) -> None:
    repository = ClassroomRepository(tmp_path)

    with pytest.raises(ClassroomPathError):
        repository.create_draft("../outside", package())
