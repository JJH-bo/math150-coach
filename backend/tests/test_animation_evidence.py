from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageStat


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs" / "preview-artifacts" / "tool-platform-core"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_checked_in_animation_is_real_manim_media_with_frame_evidence() -> None:
    job = read_json(EVIDENCE / "animation-job.json")
    report = read_json(EVIDENCE / "animation" / "validation.json")
    video = (EVIDENCE / "animation" / "animation.mp4").read_bytes()

    assert job["state"] == "succeeded"
    assert job["tool_id"] == "visualization.animation"
    assert report["passed"] is True
    assert report["manim_version"] == "0.20.1"
    assert report["width"] == 640
    assert report["height"] == 360
    assert report["frame_count"] >= 30
    assert report["distinct_frame_count"] >= 3
    assert report["nonblank"] is True
    assert b"ftyp" in video[:32]
    with Image.open(EVIDENCE / "animation" / "poster.png") as poster:
        assert poster.size == (640, 360)
        assert sum(ImageStat.Stat(poster.convert("RGB")).var) > 1
    captions = (EVIDENCE / "animation" / "captions.vtt").read_text(
        encoding="utf-8"
    )
    assert captions.startswith("WEBVTT")
    assert "The point moves toward the origin" in captions
