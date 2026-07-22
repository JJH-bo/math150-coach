from __future__ import annotations

import csv
import itertools
import json
import math
import re
from pathlib import Path
from typing import Any

import networkx as nx

from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolProducedArtifact,
    ToolQualityTier,
    ToolScope,
)


OPERATIONS = (
    "summary",
    "shortest_path",
    "components",
    "cycles",
    "topological_order",
    "centrality",
    "layout",
)
SAFE_NODE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")
MAX_NODES = 500
MAX_EDGES = 5000


class GraphMathInputError(ValueError):
    pass


class GraphMathAdapter:
    definition = ToolDefinition(
        tool_id="math.graph",
        version="1.0.0",
        title="Verified graph algorithms and layout data",
        description=(
            "Analyze bounded directed or undirected graphs with summaries, paths, "
            "components, cycles, topological order, centrality, and deterministic "
            "layout coordinates for teaching diagrams."
        ),
        category="mathematics",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.COMPUTE,
        execution_mode=ToolExecutionMode.ASYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=30,
        max_artifacts=8,
        max_artifact_bytes=32 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["operation", "nodes", "edges"],
            "properties": {
                "operation": {"type": "string", "enum": list(OPERATIONS)},
                "nodes": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": MAX_NODES,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["id"],
                        "properties": {
                            "id": {"type": "string", "pattern": SAFE_NODE_ID.pattern},
                            "label": {"type": "string", "maxLength": 200},
                            "group": {"type": "string", "maxLength": 100},
                        },
                    },
                },
                "edges": {
                    "type": "array",
                    "maxItems": MAX_EDGES,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["source", "target"],
                        "properties": {
                            "source": {"type": "string", "pattern": SAFE_NODE_ID.pattern},
                            "target": {"type": "string", "pattern": SAFE_NODE_ID.pattern},
                            "weight": {"type": "number"},
                            "label": {"type": "string", "maxLength": 200},
                        },
                    },
                },
                "directed": {"type": "boolean"},
                "weighted": {"type": "boolean"},
                "source": {"type": "string", "pattern": SAFE_NODE_ID.pattern},
                "target": {"type": "string", "pattern": SAFE_NODE_ID.pattern},
                "algorithm": {"type": "string", "maxLength": 40},
            },
        },
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["operation", "directed", "weighted", "nodes", "edges", "result"],
            "properties": {
                "operation": {"type": "string"},
                "directed": {"type": "boolean"},
                "weighted": {"type": "boolean"},
                "nodes": {"type": "array"},
                "edges": {"type": "array"},
                "result": {"type": "object"},
            },
        },
        output_media_types=["application/json", "text/csv"],
        quality_gates=[
            "valid_node_references",
            "finite_nonnegative_path_weights",
            "canonical_ordering",
            "deterministic_layout_seed",
            "reference_algorithms",
        ],
        upstream_project="https://networkx.org/",
        license="BSD-3-Clause",
    )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        operation = str(arguments.get("operation", ""))
        if operation not in OPERATIONS:
            raise GraphMathInputError(f"unsupported operation: {operation!r}")
        directed = arguments.get("directed", False)
        weighted = arguments.get("weighted", False)
        if not isinstance(directed, bool) or not isinstance(weighted, bool):
            raise GraphMathInputError("directed and weighted must be booleans")
        nodes = self._nodes(arguments.get("nodes"))
        edges = self._edges(arguments.get("edges"), nodes, directed, weighted)
        graph: nx.Graph = nx.DiGraph() if directed else nx.Graph()
        for node in nodes:
            graph.add_node(node["id"], **{key: value for key, value in node.items() if key != "id"})
        for edge in edges:
            graph.add_edge(
                edge["source"],
                edge["target"],
                weight=edge["weight"],
                label=edge.get("label"),
            )

        if operation == "summary":
            result = self._summary(graph, directed)
        elif operation == "components":
            result = self._components(graph, directed)
        elif operation == "shortest_path":
            result = self._shortest_path(graph, arguments, weighted)
        elif operation == "cycles":
            result = self._cycles(graph, directed)
        elif operation == "topological_order":
            result = self._topological_order(graph, directed)
        elif operation == "centrality":
            result = self._centrality(graph, arguments, weighted)
        else:
            result = self._layout(graph, arguments)
        payload = {
            "operation": operation,
            "directed": directed,
            "weighted": weighted,
            "nodes": nodes,
            "edges": edges,
            "result": result,
        }
        artifacts = self._write_artifacts(context.work_dir, payload)
        return ToolExecutionResult(
            result=payload,
            artifacts=artifacts,
            metrics={"node_count": len(nodes), "edge_count": len(edges)},
        )

    def _nodes(self, raw: Any) -> list[dict[str, str]]:
        if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_NODES:
            raise GraphMathInputError(f"nodes must contain 1 to {MAX_NODES} records")
        nodes: list[dict[str, str]] = []
        seen: set[str] = set()
        for item in raw:
            if not isinstance(item, dict) or set(item) - {"id", "label", "group"}:
                raise GraphMathInputError("each node must contain only id, label, and group")
            node_id = item.get("id")
            if not isinstance(node_id, str) or not SAFE_NODE_ID.fullmatch(node_id):
                raise GraphMathInputError(f"invalid node id: {node_id!r}")
            if node_id in seen:
                raise GraphMathInputError(f"duplicate node id: {node_id}")
            seen.add(node_id)
            node = {"id": node_id}
            for key in ("label", "group"):
                value = item.get(key)
                if value is not None:
                    if not isinstance(value, str) or not value.strip():
                        raise GraphMathInputError(f"node {key} must be non-blank text")
                    node[key] = value
            nodes.append(node)
        return sorted(nodes, key=lambda item: item["id"])

    def _edges(
        self,
        raw: Any,
        nodes: list[dict[str, str]],
        directed: bool,
        weighted: bool,
    ) -> list[dict[str, Any]]:
        if not isinstance(raw, list) or len(raw) > MAX_EDGES:
            raise GraphMathInputError(f"edges must be an array with at most {MAX_EDGES} records")
        known = {node["id"] for node in nodes}
        edges: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for item in raw:
            if not isinstance(item, dict) or set(item) - {"source", "target", "weight", "label"}:
                raise GraphMathInputError("each edge contains source, target, weight, and label only")
            source = item.get("source")
            target = item.get("target")
            if source not in known or target not in known:
                raise GraphMathInputError(f"edge references an unknown endpoint: {source!r}->{target!r}")
            key = (source, target) if directed else tuple(sorted((source, target)))
            if key in seen:
                raise GraphMathInputError(f"duplicate edge: {source!r}->{target!r}")
            seen.add(key)
            raw_weight = item.get("weight", 1.0)
            if isinstance(raw_weight, bool) or not isinstance(raw_weight, (int, float)):
                raise GraphMathInputError("edge weight must be numeric")
            weight = float(raw_weight)
            if not math.isfinite(weight):
                raise GraphMathInputError("edge weight must be finite")
            if weighted and weight < 0:
                raise GraphMathInputError("weighted path operations require nonnegative weights")
            edge: dict[str, Any] = {"source": source, "target": target, "weight": weight}
            label = item.get("label")
            if label is not None:
                if not isinstance(label, str) or not label.strip():
                    raise GraphMathInputError("edge label must be non-blank text")
                edge["label"] = label
            edges.append(edge)
        return sorted(edges, key=lambda item: (item["source"], item["target"], item["weight"]))

    def _summary(self, graph: nx.Graph, directed: bool) -> dict[str, Any]:
        component_count = (
            nx.number_weakly_connected_components(graph)
            if directed
            else nx.number_connected_components(graph)
        )
        return {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "density": float(nx.density(graph)),
            "is_connected": component_count == 1,
            "component_count": component_count,
        }

    def _components(self, graph: nx.Graph, directed: bool) -> dict[str, Any]:
        raw = (
            nx.weakly_connected_components(graph) if directed else nx.connected_components(graph)
        )
        components = sorted(
            (sorted(component) for component in raw),
            key=lambda component: (component[0], len(component), component),
        )
        return {"components": components, "component_count": len(components)}

    def _shortest_path(
        self, graph: nx.Graph, arguments: dict[str, Any], weighted: bool
    ) -> dict[str, Any]:
        source = arguments.get("source")
        target = arguments.get("target")
        if source not in graph or target not in graph:
            raise GraphMathInputError("shortest_path requires known source and target nodes")
        weight = "weight" if weighted else None
        try:
            path = nx.shortest_path(graph, source, target, weight=weight, method="dijkstra")
            distance = nx.shortest_path_length(
                graph, source, target, weight=weight, method="dijkstra"
            )
        except nx.NetworkXNoPath as exc:
            raise GraphMathInputError(f"no path exists from {source} to {target}") from exc
        return {
            "path": path,
            "path_edges": [
                {"source": left, "target": right} for left, right in zip(path, path[1:])
            ],
            "distance": float(distance),
        }

    def _cycles(self, graph: nx.Graph, directed: bool) -> dict[str, Any]:
        raw_cycles = (
            list(itertools.islice(nx.simple_cycles(graph, length_bound=100), 1001))
            if directed
            else nx.cycle_basis(graph)
        )
        if len(raw_cycles) > 1000:
            raise GraphMathInputError("graph contains more than 1000 bounded cycles")
        normalized = sorted({tuple(self._canonical_cycle(cycle, directed)) for cycle in raw_cycles})
        return {"cycles": [list(cycle) for cycle in normalized], "cycle_count": len(normalized)}

    @staticmethod
    def _canonical_cycle(cycle: list[str], directed: bool) -> list[str]:
        if not cycle:
            return []
        rotations = [cycle[index:] + cycle[:index] for index in range(len(cycle))]
        if not directed:
            reverse = list(reversed(cycle))
            rotations.extend(
                reverse[index:] + reverse[:index] for index in range(len(reverse))
            )
        return min(rotations)

    def _topological_order(self, graph: nx.Graph, directed: bool) -> dict[str, Any]:
        if not directed:
            raise GraphMathInputError("topological_order requires a directed graph")
        if not nx.is_directed_acyclic_graph(graph):
            raise GraphMathInputError("topological_order requires an acyclic graph")
        return {"order": list(nx.lexicographical_topological_sort(graph, key=str))}

    def _centrality(
        self, graph: nx.Graph, arguments: dict[str, Any], weighted: bool
    ) -> dict[str, Any]:
        algorithm = str(arguments.get("algorithm", "degree"))
        weight = "weight" if weighted else None
        if algorithm == "degree":
            scores = nx.degree_centrality(graph)
        elif algorithm == "betweenness":
            scores = nx.betweenness_centrality(graph, weight=weight, normalized=True)
        elif algorithm == "closeness":
            scores = nx.closeness_centrality(graph, distance=weight)
        elif algorithm == "pagerank":
            scores = nx.pagerank(graph, weight=weight, max_iter=500, tol=1e-12)
        else:
            raise GraphMathInputError("centrality algorithm must be degree, betweenness, closeness, or pagerank")
        ordered = {node: float(scores[node]) for node in sorted(scores)}
        return {"algorithm": algorithm, "scores": ordered}

    def _layout(self, graph: nx.Graph, arguments: dict[str, Any]) -> dict[str, Any]:
        algorithm = str(arguments.get("algorithm", "spring"))
        if algorithm == "spring":
            positions = nx.spring_layout(graph, seed=42, iterations=100, weight="weight")
        elif algorithm == "circular":
            positions = nx.circular_layout(graph)
        elif algorithm == "shell":
            positions = nx.shell_layout(graph)
        else:
            raise GraphMathInputError("layout algorithm must be spring, circular, or shell")
        normalized = {
            node: [round(float(positions[node][0]), 10), round(float(positions[node][1]), 10)]
            for node in sorted(positions)
        }
        return {"algorithm": algorithm, "positions": normalized, "seed": 42 if algorithm == "spring" else None}

    @staticmethod
    def _write_artifacts(
        work_dir: Path, payload: dict[str, Any]
    ) -> list[ToolProducedArtifact]:
        work_dir.mkdir(parents=True, exist_ok=True)
        json_path = work_dir / "graph-result.json"
        nodes_path = work_dir / "graph-nodes.csv"
        edges_path = work_dir / "graph-edges.csv"
        json_path.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n",
            encoding="utf-8",
        )
        with nodes_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(["id", "label", "group"])
            for node in payload["nodes"]:
                writer.writerow([node["id"], node.get("label", ""), node.get("group", "")])
        with edges_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(["source", "target", "weight", "label"])
            for edge in payload["edges"]:
                writer.writerow(
                    [edge["source"], edge["target"], edge["weight"], edge.get("label", "")]
                )
        return [
            ToolProducedArtifact(
                name=json_path.name,
                media_type="application/json",
                source_path=json_path.name,
            ),
            ToolProducedArtifact(
                name=nodes_path.name,
                media_type="text/csv",
                source_path=nodes_path.name,
            ),
            ToolProducedArtifact(
                name=edges_path.name,
                media_type="text/csv",
                source_path=edges_path.name,
            ),
        ]
