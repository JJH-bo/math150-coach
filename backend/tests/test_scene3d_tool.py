from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

import pytest
from PIL import Image, ImageStat

from app.tools.adapters.scene3d_visualization import Scene3dAdapter, Scene3dInputError
from app.tools.contracts import ToolExecutionContext


def require_runtime() -> None:
    if not (os.getenv("MODEL_PREVIEW_NODE") or shutil.which("node")):
        pytest.skip("Node runtime is unavailable")
    if not os.getenv("NODE_PATH"):
        pytest.skip("NODE_PATH is unavailable")


def arguments() -> dict:
    axis = [value / 2 for value in range(-4, 5)]
    return {
        "title": "A saddle bends in opposite directions",
        "alt_text": (
            "An interactive three-dimensional scene of the saddle surface z equals x "
            "squared minus y squared, with colored axes and camera orbit controls that "
            "reveal upward curvature along x and downward curvature along y."
        ),
        "width": 1000,
        "height": 650,
        "theme": "dark",
        "camera": {
            "azimuth": 42,
            "elevation": 28,
            "distance": 16,
            "target": [0, 0, 0],
        },
        "objects": [
            {
                "id": "saddle",
                "type": "surface",
                "label": "z = x² - y²",
                "color": "#33C3FF",
                "opacity": 1.0,
                "x": axis,
                "y": axis,
                "z": [[x * x - y * y for x in axis] for y in axis],
            },
            {
                "id": "normal",
                "type": "vector",
                "label": "normal at the origin",
                "color": "#FF6B8A",
                "origin": [0, 0, 0],
                "direction": [0, 0, 2.5],
            },
            {
                "id": "origin",
                "type": "point",
                "label": "origin",
                "color": "#F6C85F",
                "position": [0, 0, 0],
                "size": 0.16,
            },
        ],
    }


def execute(tmp_path: Path, payload: dict):
    require_runtime()
    return Scene3dAdapter().execute(
        payload,
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def test_definition_is_verified_structured_three_scene() -> None:
    definition = Scene3dAdapter().definition

    assert definition.tool_id == "visualization.scene3d"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.render"
    assert "script" not in definition.input_schema["properties"]
    assert "webgl" in " ".join(definition.quality_gates).lower()


def test_scene_emits_self_contained_webgl_and_interaction_evidence(tmp_path: Path) -> None:
    output = execute(tmp_path, arguments())

    assert output.result["object_count"] == 3
    report = output.result["validation"]
    assert report["passed"] is True
    assert report["webgl_renderer"]
    assert report["interaction_exercised"] is True
    assert report["interaction_changed"] is True
    assert report["rendered_object_count"] == 3
    assert report["frustum_clipped"] is False
    assert report["poster_unique_colors"] >= 20
    assert [artifact.name for artifact in output.artifacts] == [
        "scene.json",
        "scene.html",
        "poster.png",
        "interaction.png",
        "alt.txt",
        "validation.json",
    ]

    specification = json.loads((tmp_path / "scene.json").read_text("utf-8"))
    assert specification["objects"][0]["z"][0][0] == 0
    html = (tmp_path / "scene.html").read_text("utf-8")
    assert "type=\"range\"" in html
    assert "aria-label=" in html
    assert re.search(r"(?:src|href)=\"https?://", html) is None
    for name in ("poster.png", "interaction.png"):
        with Image.open(tmp_path / name) as image:
            assert image.size == (1000, 650)
            assert sum(ImageStat.Stat(image.convert("RGB")).var) > 1
    assert (tmp_path / "poster.png").read_bytes() != (
        tmp_path / "interaction.png"
    ).read_bytes()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.update({"alt_text": "too short"}),
        lambda payload: payload.update({"objects": []}),
        lambda payload: payload["camera"].update({"distance": 0}),
        lambda payload: payload["objects"][0].update({"color": "blue"}),
        lambda payload: payload["objects"][0]["z"].append([0, 1]),
        lambda payload: payload["objects"][1].update({"direction": [0, 0, 0]}),
        lambda payload: payload["objects"][2].update({"position": [0, float("nan"), 0]}),
        lambda payload: payload.update({"script": "window.open('/admin')"}),
    ],
)
def test_invalid_unsafe_or_nonfinite_scenes_fail(tmp_path: Path, mutate) -> None:
    payload = arguments()
    mutate(payload)

    with pytest.raises(Scene3dInputError):
        execute(tmp_path, payload)


def test_scene_specification_is_deterministic(tmp_path: Path) -> None:
    execute(tmp_path / "first", arguments())
    execute(tmp_path / "second", arguments())

    assert (tmp_path / "first" / "scene.json").read_bytes() == (
        tmp_path / "second" / "scene.json"
    ).read_bytes()
