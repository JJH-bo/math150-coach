from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from test_gpt_draft_store import _valid_authoring_markdown


AUTHORING_HEADERS = {
    "Authorization": "Bearer authoring-secret",
}


def _configure(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("GPT_AUTHORING_KEY", "authoring-secret")
    monkeypatch.setenv("CHAPTER_DRAFT_ROOT", str(tmp_path / "drafts"))
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://math.example")


def _submission(
    *,
    request_id: str = "request-001",
    markdown: str | None = None,
) -> dict:
    return {
        "chapter_id": "demo",
        "title": "Demo",
        "source_markdown": markdown or _valid_authoring_markdown(),
        "client_request_id": request_id,
        "contract_version": "chapter-galaxy-v1",
    }


def test_gpt_contract_requires_bearer_key(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _configure(monkeypatch, tmp_path)
    client = TestClient(create_app("mixed"))

    missing = client.get("/api/gpt/v1/contract")
    invalid = client.get(
        "/api/gpt/v1/contract",
        headers={"Authorization": "Bearer wrong"},
    )
    valid = client.get(
        "/api/gpt/v1/contract",
        headers=AUTHORING_HEADERS,
    )

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert valid.status_code == 200
    assert valid.json()["contract_version"] == "chapter-galaxy-v1"


def test_gpt_api_is_registered_only_on_mixed_profile(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _configure(monkeypatch, tmp_path)

    mixed_paths = set(TestClient(create_app("mixed")).get("/openapi.json").json()["paths"])
    learner_paths = set(TestClient(create_app("learner")).get("/openapi.json").json()["paths"])
    internal_paths = set(TestClient(create_app("internal")).get("/openapi.json").json()["paths"])

    assert "/api/gpt/v1/contract" in mixed_paths
    assert "/api/gpt/v1/contract" not in learner_paths
    assert "/api/gpt/v1/contract" not in internal_paths


def test_gpt_can_create_get_validate_and_update_draft(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _configure(monkeypatch, tmp_path)
    client = TestClient(create_app("mixed"))

    created = client.post(
        "/api/gpt/v1/drafts",
        headers=AUTHORING_HEADERS,
        json=_submission(),
    )

    assert created.status_code == 201
    payload = created.json()
    assert payload["status"] == "preview_ready"
    assert payload["preview_url"].startswith(
        "https://math.example/trainer/chapter-review/"
    )
    draft_id = payload["draft_id"]

    loaded = client.get(
        f"/api/gpt/v1/drafts/{draft_id}",
        headers=AUTHORING_HEADERS,
    )
    assert loaded.status_code == 200
    assert loaded.json()["revision"] == 1

    validated = client.post(
        f"/api/gpt/v1/drafts/{draft_id}/validate",
        headers=AUTHORING_HEADERS,
    )
    assert validated.status_code == 200
    assert validated.json()["validation"]["report"]["passed"] is True

    updated_markdown = _valid_authoring_markdown().replace(
        "title: Demo",
        "title: Demo Revised",
        1,
    )
    updated = client.put(
        f"/api/gpt/v1/drafts/{draft_id}",
        headers=AUTHORING_HEADERS,
        json={
            **_submission(
                request_id="request-002",
                markdown=updated_markdown,
            ),
            "title": "Demo Revised",
            "expected_revision": 1,
        },
    )

    assert updated.status_code == 200
    assert updated.json()["revision"] == 2
    assert updated.json()["title"] == "Demo"


def test_gpt_update_rejects_stale_revision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _configure(monkeypatch, tmp_path)
    client = TestClient(create_app("mixed"))
    created = client.post(
        "/api/gpt/v1/drafts",
        headers=AUTHORING_HEADERS,
        json=_submission(),
    ).json()
    first_update = client.put(
        f"/api/gpt/v1/drafts/{created['draft_id']}",
        headers=AUTHORING_HEADERS,
        json={
            **_submission(request_id="request-002"),
            "expected_revision": 1,
        },
    )
    assert first_update.status_code == 200

    response = client.put(
        f"/api/gpt/v1/drafts/{created['draft_id']}",
        headers=AUTHORING_HEADERS,
        json={
            **_submission(request_id="request-003"),
            "expected_revision": 1,
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error_code"] == "revision_conflict"
