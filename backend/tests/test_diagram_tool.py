from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path
from xml.etree import ElementTree

import pytest
from PIL import Image, ImageStat

from app.tools.adapters.diagram_visualization import DiagramAdapter, DiagramInputError
from app.tools.contracts import ToolExecutionContext


def require_runtime() -> None:
    if not (os.getenv("MODEL_PREVIEW_NODE") or shutil.which("node")):
        pytest.skip("Node runtime is unavailable")
    if not os.getenv("NODE_PATH"):
        pytest.skip("NODE_PATH is unavailable")


def arguments() -> dict:
    return {
        "title": "From informal approach to a precise limit",
        "alt_text": (
            "A left-to-right concept flow from observing nearby values, through "
            "choosing an output tolerance and a matching input tolerance, to a "
            "verified finite-limit statement."
        ),
        "direction": "LR",
        "theme": "dark",
        "width": 1000,
        "height": 620,
        "nodes": [
            {"id": "observe", "label": "Observe nearby values", "shape": "rounded"},
            {"id": "epsilon", "label": "Choose output tolerance ε", "shape": "rectangle"},
            {"id": "delta", "label": "Find input tolerance δ", "shape": "rectangle"},
            {"id": "verify", "label": "Verify the limit claim", "shape": "stadium"},
        ],
        "edges": [
            {"source": "observe", "target": "epsilon", "label": "focus output"},
            {"source": "epsilon", "target": "delta", "label": "control input"},
            {"source": "delta", "target": "verify", "label": "check all points"},
        ],
    }


def execute(tmp_path: Path, payload: dict):
    require_runtime()
    return DiagramAdapter().execute(
        payload,
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def test_definition_is_verified_structured_diagram_renderer() -> None:
    definition = DiagramAdapter().definition

    assert definition.tool_id == "visualization.diagram"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.render"
    assert "source" not in definition.input_schema["properties"]
    assert "alt" in " ".join(definition.quality_gates)


def test_diagram_emits_structured_accessible_and_rendered_artifacts(tmp_path: Path) -> None:
    output = execute(tmp_path, arguments())

    assert output.result["node_count"] == 4
    assert output.result["edge_count"] == 3
    assert output.result["validation"]["passed"] is True
    assert output.result["validation"]["png_unique_colors"] >= 10
    assert output.result["validation"]["clipped"] is False
    assert output.result["validation"]["minimum_effective_font_px"] >= 14
    assert [artifact.name for artifact in output.artifacts] == [
        "diagram.json",
        "diagram.mmd",
        "diagram.svg",
        "diagram.html",
        "diagram.png",
        "alt.txt",
        "validation.json",
    ]

    specification = json.loads((tmp_path / "diagram.json").read_text("utf-8"))
    assert specification["nodes"][1]["label"].endswith("ε")
    source = (tmp_path / "diagram.mmd").read_text("utf-8")
    assert source.startswith("flowchart LR")
    assert "click " not in source
    svg = (tmp_path / "diagram.svg").read_text("utf-8")
    svg_root = ElementTree.fromstring(svg)
    assert svg_root.tag.endswith("svg")
    assert "Observe nearby values" in " ".join(" ".join(svg_root.itertext()).split())
    html = (tmp_path / "diagram.html").read_text("utf-8")
    assert "aria-label=" in html
    assert re.search(r"(?:src|href)=\"https?://", html) is None
    with Image.open(tmp_path / "diagram.png") as image:
        assert image.size == (1000, 620)
        assert sum(ImageStat.Stat(image.convert("RGB")).var) > 1


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.update({"alt_text": "too short"}),
        lambda payload: payload.update({"nodes": []}),
        lambda payload: payload["nodes"].append(
            {"id": "observe", "label": "duplicate", "shape": "rectangle"}
        ),
        lambda payload: payload["edges"].append(
            {"source": "missing", "target": "verify", "label": "bad"}
        ),
        lambda payload: payload["nodes"][0].update(
            {"label": "unsafe <script>alert(1)</script>"}
        ),
        lambda payload: payload.update({"width": 300}),
        lambda payload: payload.update({"unknown": True}),
    ],
)
def test_inaccessible_invalid_or_unsafe_diagrams_fail(tmp_path: Path, mutate) -> None:
    payload = arguments()
    mutate(payload)

    with pytest.raises(DiagramInputError):
        execute(tmp_path, payload)


def test_diagram_source_and_svg_are_deterministic(tmp_path: Path) -> None:
    execute(tmp_path / "first", arguments())
    execute(tmp_path / "second", arguments())

    for name in ("diagram.json", "diagram.mmd", "diagram.svg"):
        assert (tmp_path / "first" / name).read_bytes() == (
            tmp_path / "second" / name
        ).read_bytes()
