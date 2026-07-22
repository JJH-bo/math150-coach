from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs" / "preview-artifacts" / "tool-platform-core"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_checked_in_asset_evidence_is_real_and_secret_free() -> None:
    registry = read_json(EVIDENCE / "tool-registry.json")
    ingest = read_json(EVIDENCE / "asset-ingest-job.json")
    transformed = read_json(EVIDENCE / "asset-transform-job.json")
    browser = read_json(EVIDENCE / "asset-transform" / "browser-report.json")

    assert registry["total"] == 18
    assert ingest["state"] == transformed["state"] == "succeeded"
    assert ingest["result"]["validation"]["source_kind"] == "studio_job_artifact"
    assert transformed["result"]["asset"]["uri"].startswith(
        "/api/classroom/v1/assets/a-"
    )
    assert browser["natural_width"] == 640
    assert browser["natural_height"] == 360
    assert browser["nonblank"] is True
    assert browser["console_errors"] == []
    assert browser["failed_requests"] == []

    serialized = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (
            EVIDENCE / "asset-ingest-job.json",
            EVIDENCE / "asset-transform-job.json",
            EVIDENCE / "asset-transform" / "browser-report.json",
        )
    ).lower()
    assert "studio_api_key" not in serialized
    assert "temporary-evidence-key" not in serialized
    assert "math150-tool-evidence-" not in serialized
