from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from fastapi import APIRouter

from app.api.v1.schemas import api_error, model_to_json
from app.core.schemas import KnowledgeNode


router = APIRouter(prefix="/nodes", tags=["nodes"])
NODES_PATH = Path(__file__).resolve().parents[2] / "seed" / "ode_nodes.yaml"


@lru_cache(maxsize=1)
def load_node_catalog() -> tuple[KnowledgeNode, ...]:
    with NODES_PATH.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return tuple(KnowledgeNode(**node) for node in data.get("nodes", []))


def get_node_or_404(node_id: str) -> KnowledgeNode:
    for node in load_node_catalog():
        if node.id == node_id:
            return node
    raise api_error(404, "node_not_found", f"Knowledge node not found: {node_id}", "node_id")


@router.get("")
def list_nodes() -> dict[str, object]:
    nodes = load_node_catalog()
    return {
        "count": len(nodes),
        "nodes": [model_to_json(node) for node in nodes],
    }


@router.get("/{node_id}")
def get_node(node_id: str) -> dict[str, object]:
    return {"node": model_to_json(get_node_or_404(node_id))}
