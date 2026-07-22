from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs" / "preview-artifacts" / "tool-platform-core"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_checked_in_classroom_patch_is_validated_and_non_mutating() -> None:
    job = read_json(EVIDENCE / "classroom-patch-job.json")
    report = read_json(EVIDENCE / "classroom-patch" / "patch-report.json")
    package = read_json(EVIDENCE / "classroom-patch" / "patched-package.json")

    assert job["state"] == "succeeded"
    assert job["tool_id"] == "classroom.patch"
    assert job["result"]["applied"] is False
    assert job["result"]["publish_ready"] is True
    assert job["result"]["source_content_hash"] != job["result"][
        "candidate_content_hash"
    ]
    assert report["validation"] == {"passed": True, "issues": []}
    assert report["next_action"].startswith("Call updateClassroomDraft")
    block = package["courses"][0]["chapters"][0]["modules"][0]["segments"][0][
        "blocks"
    ][0]
    assert "checked through a typed Studio patch" in block["data"]["markdown"]
