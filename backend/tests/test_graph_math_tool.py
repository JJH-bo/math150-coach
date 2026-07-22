from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.tools.adapters.graph_math import GraphMathAdapter, GraphMathInputError
from app.tools.contracts import ToolExecutionContext


NODES = [
    {"id": "a", "label": "Definition"},
    {"id": "b", "label": "Theorem"},
    {"id": "c", "label": "Example"},
]


def execute(tmp_path: Path, **arguments):
    return GraphMathAdapter().execute(
        arguments,
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def test_definition_is_verified_graph_algorithm_tool() -> None:
    definition = GraphMathAdapter().definition

    assert definition.tool_id == "math.graph"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.compute"


def test_summary_and_components_are_canonically_ordered(tmp_path: Path) -> None:
    summary = execute(
        tmp_path,
        operation="summary",
        nodes=NODES,
        edges=[{"source": "a", "target": "b"}],
        directed=False,
    ).result
    components = execute(
        tmp_path,
        operation="components",
        nodes=NODES,
        edges=[{"source": "a", "target": "b"}],
        directed=False,
    ).result

    assert summary["result"] == {
        "node_count": 3,
        "edge_count": 1,
        "density": pytest.approx(1 / 3),
        "is_connected": False,
        "component_count": 2,
    }
    assert components["result"]["components"] == [["a", "b"], ["c"]]


def test_weighted_shortest_path_returns_nodes_edges_and_distance(tmp_path: Path) -> None:
    result = execute(
        tmp_path,
        operation="shortest_path",
        nodes=NODES,
        edges=[
            {"source": "a", "target": "b", "weight": 2},
            {"source": "b", "target": "c", "weight": 1},
            {"source": "a", "target": "c", "weight": 5},
        ],
        directed=True,
        weighted=True,
        source="a",
        target="c",
    ).result["result"]

    assert result["path"] == ["a", "b", "c"]
    assert result["distance"] == pytest.approx(3)
    assert result["path_edges"] == [
        {"source": "a", "target": "b"},
        {"source": "b", "target": "c"},
    ]


def test_cycles_and_topological_order_respect_direction(tmp_path: Path) -> None:
    dag = execute(
        tmp_path,
        operation="topological_order",
        nodes=NODES,
        edges=[
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
        ],
        directed=True,
    ).result
    cycles = execute(
        tmp_path,
        operation="cycles",
        nodes=NODES,
        edges=[
            {"source": "a", "target": "b"},
            {"source": "b", "target": "a"},
        ],
        directed=True,
    ).result

    assert dag["result"]["order"] == ["a", "b", "c"]
    assert cycles["result"]["cycles"] == [["a", "b"]]


def test_centrality_and_seeded_layout_are_deterministic(tmp_path: Path) -> None:
    arguments = {
        "nodes": NODES,
        "edges": [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
        ],
        "directed": False,
    }
    centrality = execute(
        tmp_path / "centrality",
        operation="centrality",
        algorithm="betweenness",
        **arguments,
    ).result
    first = execute(
        tmp_path / "first",
        operation="layout",
        algorithm="spring",
        **arguments,
    ).result
    second = execute(
        tmp_path / "second",
        operation="layout",
        algorithm="spring",
        **arguments,
    ).result

    assert centrality["result"]["scores"]["b"] == pytest.approx(1.0)
    assert first["result"]["positions"] == second["result"]["positions"]
    assert set(first["result"]["positions"]) == {"a", "b", "c"}


@pytest.mark.parametrize(
    "arguments",
    [
        {
            "operation": "summary",
            "nodes": [{"id": "a"}, {"id": "a"}],
            "edges": [],
        },
        {
            "operation": "summary",
            "nodes": [{"id": "a"}],
            "edges": [{"source": "a", "target": "missing"}],
        },
        {
            "operation": "shortest_path",
            "nodes": [{"id": "a"}, {"id": "b"}],
            "edges": [{"source": "a", "target": "b", "weight": -1}],
            "weighted": True,
            "source": "a",
            "target": "b",
        },
        {
            "operation": "topological_order",
            "nodes": [{"id": "a"}, {"id": "b"}],
            "edges": [{"source": "a", "target": "b"}],
            "directed": False,
        },
    ],
)
def test_invalid_graph_contracts_fail(tmp_path: Path, arguments: dict) -> None:
    with pytest.raises(GraphMathInputError):
        execute(tmp_path, **arguments)


def test_graph_artifacts_preserve_result_and_tables(tmp_path: Path) -> None:
    output = execute(
        tmp_path,
        operation="summary",
        nodes=NODES,
        edges=[{"source": "a", "target": "b"}],
    )

    assert [artifact.name for artifact in output.artifacts] == [
        "graph-result.json",
        "graph-nodes.csv",
        "graph-edges.csv",
    ]
    assert json.loads((tmp_path / "graph-result.json").read_text("utf-8")) == output.result
