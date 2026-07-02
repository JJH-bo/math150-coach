from __future__ import annotations

from pathlib import Path

import yaml

from app.logic_graph.models import LogicGraph


class LogicGraphRepositoryError(ValueError):
    """Raised when hidden logic graph data cannot be loaded."""


class LogicGraphRepository:
    def __init__(self, data_root: str | Path | None = None) -> None:
        self.data_root = Path(data_root) if data_root else Path(__file__).resolve().parents[2] / "challenge_data"

    def load_graph(self, chapter_id: str) -> LogicGraph:
        graph_path = self.data_root / chapter_id / "logic_graph.yaml"
        return LogicGraph.model_validate(self._load_yaml(graph_path))

    def try_load_graph(self, chapter_id: str | None) -> LogicGraph | None:
        if not chapter_id:
            return None
        graph_path = self.data_root / chapter_id / "logic_graph.yaml"
        if not graph_path.exists():
            return None
        return LogicGraph.model_validate(self._load_yaml(graph_path))

    def _load_yaml(self, path: Path) -> dict:
        if not path.exists():
            raise LogicGraphRepositoryError(f"logic graph data file not found: {path}")
        try:
            with path.open("r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}
        except yaml.YAMLError as exc:
            raise LogicGraphRepositoryError(f"invalid logic graph YAML: {path}") from exc
        if not isinstance(data, dict):
            raise LogicGraphRepositoryError(f"logic graph YAML root must be a mapping: {path}")
        return data

