from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from app.tools.adapters.plot_visualization import PlotAdapter, PlotInputError
from app.tools.contracts import ToolExecutionContext


def execute(tmp_path: Path, **arguments):
    return PlotAdapter().execute(
        arguments,
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def base_arguments() -> dict:
    return {
        "title": "Quadratic growth",
        "x_label": "Input x",
        "y_label": "Output x squared",
        "alt_text": (
            "A line plot of x squared from negative two to two, with its minimum "
            "at the origin and symmetric growth on both sides."
        ),
        "traces": [
            {
                "type": "line",
                "name": "x squared",
                "x": [-2, -1, 0, 1, 2],
                "y": [4, 1, 0, 1, 4],
                "color": "#33C3FF",
            }
        ],
        "width": 800,
        "height": 520,
        "theme": "dark",
    }


def test_definition_is_verified_render_tool() -> None:
    definition = PlotAdapter().definition

    assert definition.tool_id == "visualization.plot"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.render"
    assert "alt" in " ".join(definition.quality_gates)


def test_line_plot_emits_interactive_static_and_validation_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv(
        "MODEL_PREVIEW_BROWSER",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    )
    output = execute(tmp_path, **base_arguments())

    assert output.result["trace_count"] == 1
    assert output.result["point_count"] == 5
    assert output.result["validation"]["passed"] is True
    assert output.result["validation"]["png_unique_colors"] >= 10
    assert [artifact.name for artifact in output.artifacts] == [
        "figure.json",
        "figure.html",
        "figure.png",
        "figure.svg",
        "alt.txt",
        "validation.json",
    ]
    with Image.open(tmp_path / "figure.png") as image:
        assert image.size == (800, 520)
    assert (tmp_path / "figure.svg").read_text("utf-8").lstrip().startswith("<svg")
    html = (tmp_path / "figure.html").read_text("utf-8")
    assert "aria-label=" in html
    assert "plotly" in html.lower()
    assert output.result["alt_text"] in html


def test_heatmap_builds_a_nonblank_static_visual(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(
        "MODEL_PREVIEW_BROWSER",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    )
    output = execute(
        tmp_path,
        title="Multiplication surface",
        x_label="Column",
        y_label="Row",
        alt_text=(
            "A three by three heatmap whose color increases from the upper left "
            "toward the lower right as row and column products increase."
        ),
        traces=[
            {
                "type": "heatmap",
                "name": "products",
                "x": [1, 2, 3],
                "y": [1, 2, 3],
                "z": [[1, 2, 3], [2, 4, 6], [3, 6, 9]],
            }
        ],
        width=700,
        height=500,
        theme="light",
    )

    figure = json.loads((tmp_path / "figure.json").read_text("utf-8"))
    assert figure["data"][0]["type"] == "heatmap"
    assert output.result["validation"]["png_channel_variance"] > 1


@pytest.mark.parametrize(
    "mutation",
    [
        {"alt_text": "too short"},
        {"traces": []},
        {
            "traces": [
                {"type": "line", "name": "bad", "x": [0, 1], "y": [1]}
            ]
        },
        {
            "traces": [
                {
                    "type": "heatmap",
                    "name": "bad grid",
                    "z": [[1, 2], [3]],
                }
            ]
        },
        {"width": 300},
        {
            "traces": [
                {
                    "type": "scatter",
                    "name": "nonfinite",
                    "x": [0, float("inf")],
                    "y": [0, 1],
                }
            ]
        },
    ],
)
def test_empty_inaccessible_mismatched_or_nonfinite_plots_fail(
    tmp_path: Path, mutation: dict
) -> None:
    arguments = {**base_arguments(), **mutation}
    with pytest.raises(PlotInputError):
        execute(tmp_path, **arguments)


def test_plot_json_is_deterministic_for_identical_input(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv(
        "MODEL_PREVIEW_BROWSER",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    )
    execute(tmp_path / "first", **base_arguments())
    execute(tmp_path / "second", **base_arguments())

    assert (tmp_path / "first" / "figure.json").read_bytes() == (
        tmp_path / "second" / "figure.json"
    ).read_bytes()
