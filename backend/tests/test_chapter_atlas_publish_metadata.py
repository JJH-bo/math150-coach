from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.training.session_log import ensure_no_trusted_fields


def test_challenge_atlas_exposes_publish_catalog_metadata_without_detail_graph() -> None:
    client = TestClient(create_app("mixed"))

    response = client.get("/api/challenge/v1/atlas")

    assert response.status_code == 200
    payload = response.json()
    assert payload["catalog_summary"]["chapter_count"] == len(payload["regions"])
    assert "controlled_published_count" in payload["catalog_summary"]
    assert "legacy_runtime_count" in payload["catalog_summary"]
    assert payload["regions"]
    region = payload["regions"][0]
    assert region["publish_status"] in {"legacy_runtime", "controlled_published"}
    assert "publish_metadata" in region
    assert "candidate_content_hash" in region["summary"]
    assert region["detail"]["quality_endpoint"].endswith(region["id"])
    assert "micro_nodes" not in region
    ensure_no_trusted_fields(payload)
