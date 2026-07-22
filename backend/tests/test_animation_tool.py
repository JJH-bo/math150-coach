from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest
from PIL import Image, ImageStat

from app.tools.adapters.animation_visualization import (
    AnimationAdapter,
    AnimationInputError,
)
from app.tools.contracts import ToolExecutionContext


def require_manim() -> None:
    python = os.getenv("MANIM_PYTHON")
    if not python or not Path(python).is_file():
        pytest.skip("MANIM_PYTHON is unavailable")
    check = subprocess.run(
        [python, "-c", "import manim"],
        capture_output=True,
        timeout=20,
        check=False,
    )
    if check.returncode != 0:
        pytest.skip("Manim is unavailable in MANIM_PYTHON")


def arguments(output_format: str = "mp4") -> dict:
    return {
        "title": "A point follows a sampled quadratic curve",
        "alt_text": (
            "An animated coordinate plane draws a blue quadratic curve, then moves a "
            "yellow point from the left branch toward the minimum at the origin."
        ),
        "width": 640,
        "height": 360,
        "fps": 15,
        "background": "#0B1119",
        "output_format": output_format,
        "objects": [
            {
                "id": "axes",
                "type": "axes",
                "x_range": [-3, 3, 1],
                "y_range": [0, 5, 1],
                "x_length": 8,
                "y_length": 4.5,
                "position": [0, -0.3],
                "color": "#9FB0C3",
            },
            {
                "id": "curve",
                "type": "polyline",
                "axes_id": "axes",
                "points": [[-2, 4], [-1.5, 2.25], [-1, 1], [0, 0], [1, 1], [1.5, 2.25], [2, 4]],
                "color": "#33C3FF",
                "stroke_width": 6,
            },
            {
                "id": "moving-point",
                "type": "dot",
                "position": [-2.65, 1.5],
                "radius": 0.12,
                "color": "#F6C85F",
            },
            {
                "id": "label",
                "type": "text",
                "text": "x² approaches its minimum",
                "position": [0, 3.3],
                "font_size": 30,
                "color": "#F4F7FB",
            },
        ],
        "timeline": [
            {
                "action": "create",
                "object_id": "axes",
                "duration": 0.3,
                "caption": "A coordinate plane establishes the input and output scales.",
            },
            {
                "action": "create",
                "object_id": "curve",
                "duration": 0.5,
                "caption": "The sampled quadratic curve appears symmetrically around the origin.",
            },
            {
                "action": "write",
                "object_id": "label",
                "duration": 0.3,
                "caption": "The label states that the curve approaches its minimum.",
            },
            {
                "action": "fade_in",
                "object_id": "moving-point",
                "duration": 0.2,
                "caption": "A yellow point marks a location on the left branch.",
            },
            {
                "action": "move_to",
                "object_id": "moving-point",
                "to": [0, -0.3],
                "duration": 0.8,
                "caption": "The point moves toward the origin and the minimum value.",
            },
            {
                "action": "indicate",
                "object_id": "moving-point",
                "duration": 0.4,
                "caption": "The origin is highlighted as the minimum of the quadratic.",
            },
            {
                "action": "wait",
                "duration": 0.3,
                "caption": "The final frame holds the completed mathematical relationship.",
            },
        ],
    }


def execute(tmp_path: Path, output_format: str = "mp4"):
    require_manim()
    return AnimationAdapter().execute(
        arguments(output_format),
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def test_definition_is_verified_structured_manim_animation() -> None:
    definition = AnimationAdapter().definition

    assert definition.tool_id == "visualization.animation"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.render"
    assert definition.upstream_project == "Manim Community 0.20.1"
    assert "python" not in definition.input_schema["properties"]
    assert "script" not in definition.input_schema["properties"]
    assert definition.input_schema["properties"]["output_format"]["enum"] == [
        "mp4",
        "webm",
        "gif",
    ]


@pytest.mark.parametrize("output_format", ["mp4", "webm", "gif"])
def test_animation_emits_real_video_frames_captions_and_validation(
    tmp_path: Path, output_format: str
) -> None:
    output = execute(tmp_path, output_format)

    report = output.result["validation"]
    assert report["passed"] is True
    assert report["manim_version"] == "0.20.1"
    assert report["width"] == 640
    assert report["height"] == 360
    assert report["frame_count"] >= 30
    assert report["distinct_frame_count"] >= 3
    assert report["nonblank"] is True
    assert [artifact.name for artifact in output.artifacts] == [
        "animation.json",
        f"animation.{output_format}",
        "poster.png",
        "frame-sheet.png",
        "captions.vtt",
        "alt.txt",
        "validation.json",
    ]
    with Image.open(tmp_path / "poster.png") as poster:
        assert poster.size == (640, 360)
        assert sum(ImageStat.Stat(poster.convert("RGB")).var) > 1
    captions = (tmp_path / "captions.vtt").read_text(encoding="utf-8")
    assert captions.startswith("WEBVTT")
    assert "The point moves toward the origin" in captions
    specification = json.loads((tmp_path / "animation.json").read_text("utf-8"))
    assert specification["timeline"][-1]["end_seconds"] > 2


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.update({"script": "import os"}),
        lambda payload: payload["objects"].append(payload["objects"][0].copy()),
        lambda payload: payload["objects"][1].update({"axes_id": "missing"}),
        lambda payload: payload["objects"][2].update({"position": [99, 0]}),
        lambda payload: payload["timeline"][0].update({"object_id": "missing"}),
        lambda payload: payload["timeline"][4].update({"to": [0, float("inf")]}),
        lambda payload: payload["timeline"][0].update({"caption": "short"}),
        lambda payload: payload.update({"output_format": "mov"}),
    ],
)
def test_animation_rejects_unsafe_or_unbounded_scene(tmp_path: Path, mutate) -> None:
    payload = arguments()
    mutate(payload)

    with pytest.raises(AnimationInputError):
        AnimationAdapter().execute(
            payload,
            ToolExecutionContext(
                job_id="tj-000000000000000000000000",
                work_dir=tmp_path,
            ),
        )
