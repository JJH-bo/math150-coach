from __future__ import annotations

from pathlib import Path

import yaml

from app.challenge.models import ChallengeGraph, ChallengeQuestionBank


DEFAULT_CHALLENGE_ID = "ode_mvp"


class ChallengeRepositoryError(ValueError):
    """Raised when challenge graph or question data cannot be loaded."""


class ChallengeRepository:
    def __init__(self, data_root: str | Path | None = None) -> None:
        self.data_root = Path(data_root) if data_root else Path(__file__).resolve().parents[2] / "challenge_data"

    def load_graph(self, chapter_id: str = DEFAULT_CHALLENGE_ID) -> ChallengeGraph:
        graph_path = self.data_root / chapter_id / "challenge_graph.yaml"
        return ChallengeGraph.model_validate(self._load_yaml(graph_path))

    def load_question_bank(self, chapter_id: str = DEFAULT_CHALLENGE_ID) -> ChallengeQuestionBank:
        questions_path = self.data_root / chapter_id / "questions.yaml"
        return ChallengeQuestionBank.model_validate(self._load_yaml(questions_path))

    def _load_yaml(self, path: Path) -> dict:
        if not path.exists():
            raise ChallengeRepositoryError(f"challenge data file not found: {path}")
        try:
            with path.open("r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}
        except yaml.YAMLError as exc:
            raise ChallengeRepositoryError(f"invalid challenge YAML: {path}") from exc
        if not isinstance(data, dict):
            raise ChallengeRepositoryError(f"challenge YAML root must be a mapping: {path}")
        return data

