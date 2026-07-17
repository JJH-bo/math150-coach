from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.challenge.gpt_draft_store import ChapterDraftStore
from app.main import create_app
from test_chapter_publish_executor import MARKDOWN


def _configure(monkeypatch, tmp_path: Path) -> ChapterDraftStore:
    draft_root = tmp_path / "drafts"
    monkeypatch.setenv("GPT_AUTHORING_KEY", "authoring-secret")
    monkeypatch.setenv("CHAPTER_REVIEW_KEY", "review-secret")
    monkeypatch.setenv("CHAPTER_DRAFT_ROOT", str(draft_root))
    monkeypatch.setenv(
        "CHAPTER_PUBLISH_TARGET_ROOT",
        str(tmp_path / "published"),
    )
    monkeypatch.setenv("CHAPTER_REVIEW_SESSION_TTL_SECONDS", "28800")
    return ChapterDraftStore(draft_root)


def _preview_ready_draft(store: ChapterDraftStore) -> dict:
    return store.create_revision(
        chapter_id="controlled_demo",
        title="Controlled Demo",
        source_markdown=MARKDOWN,
        client_request_id="request-review-001",
        contract_version="chapter-galaxy-v1",
        validation_report={"report": {"error_count": 0, "errors": [], "warnings": []}},
        galaxy_asset={
            "chapterId": "controlled_demo",
            "title": "Controlled Demo",
            "systems": [],
            "boss": {"id": "controlled_demo.boss"},
            "metrics": {
                "systemCount": 0,
                "planetCount": 0,
                "bossCount": 1,
            },
        },
    )


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/chapter-review/session",
        json={"review_key": "review-secret"},
    )
    assert response.status_code == 204


def test_gpt_key_cannot_approve_draft(
    tmp_path: Path,
    monkeypatch,
) -> None:
    store = _configure(monkeypatch, tmp_path)
    draft = _preview_ready_draft(store)
    client = TestClient(create_app("mixed"))

    response = client.post(
        f"/api/chapter-review/{draft['draft_id']}/approve",
        headers={"Authorization": "Bearer authoring-secret"},
        json={
            "revision": draft["revision"],
            "content_hash": draft["content_hash"],
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"]["error_code"] == "review_auth_required"


def test_review_session_publishes_exact_preview_revision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    store = _configure(monkeypatch, tmp_path)
    draft = _preview_ready_draft(store)
    client = TestClient(create_app("mixed"))
    _login(client)

    response = client.post(
        f"/api/chapter-review/{draft['draft_id']}/approve",
        json={
            "revision": draft["revision"],
            "content_hash": draft["content_hash"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "published"
    assert payload["formal_publish_executed"] is True
    assert store.load(draft["draft_id"])["status"] == "published"
    assert (
        tmp_path
        / "published"
        / "backend"
        / "challenge_data"
        / "controlled_demo"
        / "challenge_graph.yaml"
    ).exists()


def test_approval_rejects_stale_hash(
    tmp_path: Path,
    monkeypatch,
) -> None:
    store = _configure(monkeypatch, tmp_path)
    draft = _preview_ready_draft(store)
    client = TestClient(create_app("mixed"))
    _login(client)

    response = client.post(
        f"/api/chapter-review/{draft['draft_id']}/approve",
        json={
            "revision": draft["revision"],
            "content_hash": "sha256:" + "0" * 64,
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]["error_code"]
        == "approval_revision_mismatch"
    )


def test_review_can_reject_current_revision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    store = _configure(monkeypatch, tmp_path)
    draft = _preview_ready_draft(store)
    client = TestClient(create_app("mixed"))
    _login(client)

    response = client.post(
        f"/api/chapter-review/{draft['draft_id']}/reject",
        json={
            "revision": draft["revision"],
            "reason": "核心模块需要重新划分",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "changes_requested"
