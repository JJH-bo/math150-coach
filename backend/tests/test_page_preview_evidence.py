from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs" / "preview-artifacts" / "tool-platform-core"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_checked_in_page_preview_uses_real_desktop_and_mobile_runtime() -> None:
    job = read_json(EVIDENCE / "page-preview-job.json")
    report = read_json(EVIDENCE / "page-preview" / "preview-report.json")

    assert job["state"] == "succeeded"
    assert job["tool_id"] == "page.preview"
    assert report["passed"] is True
    assert report["runtime"] == "classroom_runtime_v1"
    assert [item["name"] for item in report["viewports"]] == [
        "desktop",
        "mobile",
    ]
    for viewport in report["viewports"]:
        assert viewport["baseline_steps"] >= 2
        assert viewport["unrendered_math"] == 0
        assert viewport["horizontal_overflow"] <= 1
        assert viewport["clipped_text"] == []
        assert viewport["accessibility_issues"] == []
        assert viewport["console_errors"] == []
        assert viewport["failed_requests"] == []
        screenshot = EVIDENCE / "page-preview" / viewport["screenshot"]
        with Image.open(screenshot) as image:
            assert image.size == (
                viewport["viewport_width"],
                viewport["viewport_height"],
            )
            assert sum(ImageStat.Stat(image.convert("RGB")).var) > 1
