from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.challenge.gpt_authoring_contract import CONTRACT_VERSION
from app.challenge.gpt_authoring_service import DraftSubmission, GptAuthoringService
from app.challenge.gpt_draft_store import (
    ChapterDraftStore,
    IdempotencyConflict,
    RevisionConflict,
)
from test_chapter_galaxy_builder import _chapter_markdown


def _valid_authoring_markdown() -> str:
    markdown = re.sub(
        r"(?m)^title:.*$",
        "title: Demo",
        _chapter_markdown(),
        count=1,
    )
    return (
        markdown
        + """

## ErrorRepairMap
| root_cause | repair_target_node_id |
| --- | --- |
| concept_gap | demo.system_01.concept |
"""
    )


def _create_valid_revision(
    store: ChapterDraftStore,
    *,
    request_id: str = "request-001",
    markdown: str | None = None,
) -> dict:
    return store.create_revision(
        chapter_id="demo",
        title="Demo",
        source_markdown=markdown or _chapter_markdown(),
        client_request_id=request_id,
        contract_version=CONTRACT_VERSION,
        validation_report={"report": {"error_count": 0, "issues": []}},
        galaxy_asset={"chapterId": "demo", "metrics": {"systemCount": 2}},
    )


def test_idempotent_submission_returns_same_draft(tmp_path: Path) -> None:
    store = ChapterDraftStore(tmp_path)

    first = _create_valid_revision(store)
    second = _create_valid_revision(store)

    assert second["draft_id"] == first["draft_id"]
    assert second["revision"] == 1
    assert second["source_markdown"] == _chapter_markdown()


def test_idempotency_key_cannot_change_content(tmp_path: Path) -> None:
    store = ChapterDraftStore(tmp_path)
    _create_valid_revision(store)

    with pytest.raises(IdempotencyConflict):
        _create_valid_revision(
            store,
            markdown=_chapter_markdown() + "\nchanged",
        )


def test_revision_compare_and_swap_prevents_overwrite(tmp_path: Path) -> None:
    store = ChapterDraftStore(tmp_path)
    created = _create_valid_revision(store)

    with pytest.raises(RevisionConflict):
        store.revise(
            created["draft_id"],
            expected_revision=0,
            source_markdown=_chapter_markdown(),
            validation_report={"report": {"error_count": 0, "issues": []}},
            galaxy_asset={"chapterId": "demo"},
        )


def test_revision_files_are_immutable_and_loadable(tmp_path: Path) -> None:
    store = ChapterDraftStore(tmp_path)
    created = _create_valid_revision(store)
    changed = _chapter_markdown().replace("title: ", "title: Updated ", 1)

    revised = store.revise(
        created["draft_id"],
        expected_revision=1,
        source_markdown=changed,
        validation_report={"report": {"error_count": 0, "issues": []}},
        galaxy_asset={"chapterId": "demo", "title": "Updated Demo"},
    )

    assert revised["revision"] == 2
    assert store.load(created["draft_id"], 1)["source_markdown"] == _chapter_markdown()
    assert store.load(created["draft_id"], 2)["source_markdown"] == changed


def test_authoring_service_builds_preview_ready_draft(tmp_path: Path) -> None:
    service = GptAuthoringService(
        ChapterDraftStore(tmp_path),
        public_base_url="https://math.example",
    )

    payload = service.create(
        DraftSubmission(
            chapter_id="demo",
            title="Demo",
            source_markdown=_valid_authoring_markdown(),
            client_request_id="request-001",
            contract_version=CONTRACT_VERSION,
        )
    )

    assert payload["status"] == "preview_ready"
    assert payload["metrics"] == {
        "systemCount": 2,
        "planetCount": 6,
        "bossCount": 1,
    }
    assert payload["preview_url"].startswith(
        "https://math.example/trainer/chapter-review/?draft="
    )


def test_authoring_service_retains_invalid_draft_diagnostics(tmp_path: Path) -> None:
    service = GptAuthoringService(ChapterDraftStore(tmp_path))

    payload = service.create(
        DraftSubmission(
            chapter_id="demo",
            title="Demo",
            source_markdown="# Demo\nchapter_id: demo\ntitle: Demo",
            client_request_id="request-invalid",
            contract_version=CONTRACT_VERSION,
        )
    )

    assert payload["status"] == "invalid"
    assert payload["metrics"] == {}
    assert payload["issues"]
