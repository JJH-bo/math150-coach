from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from xml.etree import ElementTree

import pytest
from PIL import Image, ImageStat

from app.tools.adapters.geometry2d_visualization import (
    Geometry2dAdapter,
    Geometry2dInputError,
)
from app.tools.contracts import ToolExecutionContext


def require_runtime() -> None:
    if not (os.getenv("MODEL_PREVIEW_NODE") or shutil.which("node")):
        pytest.skip("Node runtime is unavailable")
    if not os.getenv("NODE_PATH"):
        pytest.skip("NODE_PATH is unavailable")


def arguments() -> dict:
    return {
        "title": "Scaling a vector preserves its direction",
        "alt_text": (
            "An interactive coordinate plane showing a reference ray with slope three "
            "halves and a vector whose endpoint is controlled by scale factor t, so its "
            "length changes while every endpoint remains on the same ray."
        ),
        "viewport": {"x_min": -1, "x_max": 5, "y_min": -1, "y_max": 7},
        "width": 1000,
        "height": 650,
        "theme": "dark",
        "parameters": [
            {
                "id": "t",
                "label": "Scale factor t",
                "minimum": 0.5,
                "maximum": 2.0,
                "step": 0.1,
                "value": 1.0,
            }
        ],
        "objects": [
            {
                "id": "reference-ray",
                "type": "polyline",
                "label": "y = 1.5x",
                "color": "#33C3FF",
                "points": [
                    {"x": 0, "y": 0},
                    {"x": 1, "y": 1.5},
                    {"x": 2, "y": 3},
                    {"x": 3, "y": 4.5},
                    {"x": 4, "y": 6},
                ],
            },
            {
                "id": "fixed",
                "type": "point",
                "label": "O",
                "color": "#F6C85F",
                "x": 0,
                "y": 0,
            },
            {
                "id": "moving",
                "type": "point",
                "label": "Q(t)",
                "color": "#FF6B8A",
                "x": {"parameter": "t", "scale": 2, "offset": 0},
                "y": {"parameter": "t", "scale": 3, "offset": 0},
            },
            {
                "id": "secant",
                "type": "vector",
                "label": "scaled vector",
                "color": "#FF6B8A",
                "x": 0,
                "y": 0,
                "dx": {"parameter": "t", "scale": 2, "offset": 0},
                "dy": {"parameter": "t", "scale": 3, "offset": 0},
            },
        ],
    }


def execute(tmp_path: Path, payload: dict):
    require_runtime()
    return Geometry2dAdapter().execute(
        payload,
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def test_definition_is_verified_structured_interactive_geometry() -> None:
    definition = Geometry2dAdapter().definition

    assert definition.tool_id == "visualization.geometry2d"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.render"
    assert "script" not in definition.input_schema["properties"]
    assert "interaction" in " ".join(definition.quality_gates)


def test_geometry_emits_accessible_interactive_and_exercised_artifacts(tmp_path: Path) -> None:
    output = execute(tmp_path, arguments())

    assert output.result["object_count"] == 4
    assert output.result["parameter_count"] == 1
    report = output.result["validation"]
    assert report["passed"] is True
    assert report["interaction_exercised"] is True
    assert report["interaction_changed"] is True
    assert report["clipped"] is False
    assert report["png_unique_colors"] >= 10
    assert [artifact.name for artifact in output.artifacts] == [
        "geometry.json",
        "geometry.svg",
        "geometry.html",
        "geometry.png",
        "interaction-001.png",
        "alt.txt",
        "validation.json",
    ]

    specification = json.loads((tmp_path / "geometry.json").read_text("utf-8"))
    assert specification["parameters"][0]["id"] == "t"
    svg = (tmp_path / "geometry.svg").read_text("utf-8")
    assert ElementTree.fromstring(svg).tag.endswith("svg")
    assert "scaled vector" in svg
    html = (tmp_path / "geometry.html").read_text("utf-8")
    assert "type=\"range\"" in html
    assert "aria-label=" in html
    assert re.search(r"(?:src|href)=\"https?://", html) is None
    for name in ("geometry.png", "interaction-001.png"):
        with Image.open(tmp_path / name) as image:
            assert image.size == (1000, 650)
            assert sum(ImageStat.Stat(image.convert("RGB")).var) > 1
    assert (tmp_path / "geometry.png").read_bytes() != (
        tmp_path / "interaction-001.png"
    ).read_bytes()


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.update({"alt_text": "too short"}),
        lambda payload: payload.update({"objects": []}),
        lambda payload: payload["parameters"].append(payload["parameters"][0].copy()),
        lambda payload: payload["objects"][2].update(
            {"x": {"parameter": "missing", "scale": 1, "offset": 0}}
        ),
        lambda payload: payload["objects"][0].update({"color": "red"}),
        lambda payload: payload["viewport"].update({"x_max": -2}),
        lambda payload: payload.update({"script": "fetch('/secrets')"}),
        lambda payload: payload["objects"][0]["points"].append(
            {"x": float("inf"), "y": 0}
        ),
    ],
)
def test_invalid_unsafe_or_nonfinite_geometry_fails(tmp_path: Path, mutate) -> None:
    payload = arguments()
    mutate(payload)

    with pytest.raises(Geometry2dInputError):
        execute(tmp_path, payload)


def test_geometry_specification_and_baseline_svg_are_deterministic(tmp_path: Path) -> None:
    execute(tmp_path / "first", arguments())
    execute(tmp_path / "second", arguments())

    for name in ("geometry.json", "geometry.svg"):
        assert (tmp_path / "first" / name).read_bytes() == (
            tmp_path / "second" / name
        ).read_bytes()
