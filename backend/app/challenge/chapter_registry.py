from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from app.challenge.models import ChallengeGraph, ChallengeQuestionBank, ChallengeTaskType
from app.challenge.repository import ChallengeRepository, ChallengeRepositoryError


CHAPTER_RUNTIME_REGISTRY_VERSION = "chapter_runtime_registry_v1"
ChapterRuntimeStatus = Literal["trainable", "content_pending", "invalid"]


class ChapterRuntimeRegistryError(ValueError):
    """Raised when a chapter is not eligible for runtime training."""


class ChapterRuntimeRegistry:
    """Builds the runtime-facing chapter registry from published chapter assets.

    A chapter directory is not enough to make a trainable package. The runtime
    contract requires a valid graph, a valid question bank, and complete question
    coverage for every MicroNode and MacroChallenge/Boss.
    """

    def __init__(self, repository: ChallengeRepository | None = None) -> None:
        self.repository = repository or ChallengeRepository()

    def build(self) -> dict[str, Any]:
        chapters = [self._entry_for(chapter_id) for chapter_id in self._discover_chapter_ids()]
        warnings = [
            f"{entry['chapter_id']}:{reason}"
            for entry in chapters
            for reason in entry.get("blocking_reasons", [])
            if entry.get("can_start") is not True
        ]
        return {
            "registry_version": CHAPTER_RUNTIME_REGISTRY_VERSION,
            "publish_state": "runtime_registry_read_only",
            "chapters": chapters,
            "warnings": warnings,
        }

    def chapter_entry(self, chapter_id: str) -> dict[str, Any] | None:
        for entry in self.build()["chapters"]:
            if entry["chapter_id"] == chapter_id:
                return entry
        return None

    def ensure_trainable(self, chapter_id: str) -> dict[str, Any]:
        entry = self.chapter_entry(chapter_id)
        if entry is None:
            raise ChapterRuntimeRegistryError(f"chapter is not registered in runtime registry: {chapter_id}")
        if entry.get("can_start") is not True:
            reasons = ", ".join(entry.get("blocking_reasons", [])) or "chapter_not_trainable"
            raise ChapterRuntimeRegistryError(f"chapter is not trainable yet: {chapter_id}; {reasons}")
        return entry

    def _discover_chapter_ids(self) -> list[str]:
        root = Path(self.repository.data_root)
        if not root.exists():
            return []
        chapter_ids = [
            path.name
            for path in root.iterdir()
            if path.is_dir()
            and (
                (path / "challenge_graph.yaml").exists()
                or (path / "questions.yaml").exists()
                or (path / "publish_manifest.json").exists()
            )
        ]
        return sorted(chapter_ids, key=_chapter_sort_key)

    def _entry_for(self, chapter_id: str) -> dict[str, Any]:
        chapter_dir = Path(self.repository.data_root) / chapter_id
        files = _runtime_files(chapter_dir)
        manifest = _load_publish_manifest(chapter_dir / "publish_manifest.json")
        source = "controlled_publish" if files["publish_manifest"] else "seed_or_legacy"
        blocking_reasons: list[str] = []
        graph: ChallengeGraph | None = None
        questions: ChallengeQuestionBank | None = None

        if files["publish_manifest"]:
            if manifest.get("manifest_read_error"):
                blocking_reasons.append("publish_manifest_invalid")
            elif manifest.get("candidate_quality_grade") != "pass":
                blocking_reasons.append("publish_manifest_quality_not_pass")

        try:
            graph = self.repository.load_graph(chapter_id)
        except ChallengeRepositoryError:
            blocking_reasons.append("challenge_graph_invalid_or_missing")

        if graph is not None:
            if not files["questions"]:
                blocking_reasons.append("questions_yaml_missing")
            else:
                try:
                    questions = self.repository.load_question_bank(chapter_id)
                except ChallengeRepositoryError:
                    blocking_reasons.append("questions_yaml_invalid")

        if graph is not None and questions is not None:
            blocking_reasons.extend(_question_coverage_reasons(graph, questions))

        runtime_status = _runtime_status(graph, questions, blocking_reasons)
        return {
            "chapter_id": chapter_id,
            "title": graph.title if graph is not None else chapter_id,
            "runtime_status": runtime_status,
            "can_start": runtime_status == "trainable",
            "source": source,
            "files": files,
            "counts": _counts(graph),
            "quality": _quality_summary(manifest),
            "blocking_reasons": sorted(set(blocking_reasons)),
        }


def _runtime_files(chapter_dir: Path) -> dict[str, bool]:
    return {
        "challenge_graph": (chapter_dir / "challenge_graph.yaml").exists(),
        "questions": (chapter_dir / "questions.yaml").exists(),
        "logic_graph": (chapter_dir / "logic_graph.yaml").exists(),
        "publish_manifest": (chapter_dir / "publish_manifest.json").exists(),
    }


def _load_publish_manifest(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"manifest_read_error": True}
    return payload if isinstance(payload, dict) else {"manifest_read_error": True}


def _question_coverage_reasons(graph: ChallengeGraph, questions: ChallengeQuestionBank) -> list[str]:
    reasons: list[str] = []
    if questions.chapter_id != graph.chapter_id:
        reasons.append("questions_chapter_id_mismatch")

    micro_ids = {micro.id for micro in graph.micro_nodes}
    challenge_ids = {challenge.id for challenge in graph.macro_challenges}
    known_node_ids = micro_ids | challenge_ids | {macro.id for macro in graph.macro_nodes}

    micro_question_owners = {
        question.owner_id
        for question in questions.questions
        if question.task_type == ChallengeTaskType.MICRO_NODE
    }
    challenge_question_owners = {
        question.owner_id
        for question in questions.questions
        if question.task_type == ChallengeTaskType.MACRO_CHALLENGE
    }

    missing_micro = sorted(micro_ids - micro_question_owners)
    missing_challenges = sorted(challenge_ids - challenge_question_owners)
    invalid_targets = sorted(
        question.id
        for question in questions.questions
        if question.owner_id not in micro_ids | challenge_ids or question.node_id not in known_node_ids
    )

    if missing_micro:
        reasons.append("missing_micro_node_questions")
    if missing_challenges:
        reasons.append("missing_macro_challenge_questions")
    if invalid_targets:
        reasons.append("invalid_question_targets")
    if not questions.questions:
        reasons.append("empty_question_bank")
    return reasons


def _runtime_status(
    graph: ChallengeGraph | None,
    questions: ChallengeQuestionBank | None,
    blocking_reasons: list[str],
) -> ChapterRuntimeStatus:
    if graph is None:
        return "invalid"
    if questions is None or blocking_reasons:
        return "content_pending"
    return "trainable"


def _counts(graph: ChallengeGraph | None) -> dict[str, int]:
    if graph is None:
        return {
            "macro_nodes": 0,
            "micro_nodes": 0,
            "macro_challenges": 0,
            "atom_nodes": 0,
            "compare_nodes": 0,
            "guide_nodes": 0,
            "typed_edges": 0,
        }
    return {
        "macro_nodes": len(graph.macro_nodes),
        "micro_nodes": len(graph.micro_nodes),
        "macro_challenges": len(graph.macro_challenges),
        "atom_nodes": len(graph.atom_nodes),
        "compare_nodes": len(graph.compare_nodes),
        "guide_nodes": len(graph.guide_nodes),
        "typed_edges": len(graph.typed_edges),
    }


def _quality_summary(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_quality_grade": manifest.get("candidate_quality_grade"),
        "candidate_quality_score": manifest.get("candidate_quality_score"),
        "candidate_content_hash": manifest.get("candidate_content_hash"),
        "publish_plan_schema_version": manifest.get("publish_plan_schema_version"),
        "manifest_read_error": manifest.get("manifest_read_error", False),
    }


def _chapter_sort_key(chapter_id: str) -> tuple[int, int, str]:
    priority = 0 if chapter_id == "ode_network_mvp" else 1
    legacy_priority = 0 if chapter_id == "ode_mvp" else 1
    return (priority, legacy_priority, chapter_id)
