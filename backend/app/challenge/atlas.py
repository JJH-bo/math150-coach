from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.challenge.chapter_registry import ChapterRuntimeRegistry
from app.challenge.repository import ChallengeRepository, ChallengeRepositoryError


class ChallengeAtlasBuilder:
    """Builds a lightweight course-level atlas without exposing chapter internals."""

    def __init__(self, repository: ChallengeRepository | None = None) -> None:
        self.repository = repository or ChallengeRepository()
        self.registry = ChapterRuntimeRegistry(self.repository)

    def build(self) -> dict[str, Any]:
        registry = self.registry.build()
        chapter_entries = registry["chapters"]
        regions: list[dict[str, Any]] = []
        warnings: list[str] = list(registry.get("warnings", []))
        for index, chapter_entry in enumerate(chapter_entries):
            chapter_id = chapter_entry["chapter_id"]
            try:
                graph = self.repository.load_graph(chapter_id)
            except ChallengeRepositoryError as exc:
                warnings.append(str(exc))
                continue
            can_start = chapter_entry.get("can_start") is True
            runtime_status = chapter_entry.get("runtime_status", "content_pending")
            macro_count = len(graph.macro_nodes)
            micro_count = len(graph.micro_nodes)
            boss_count = len(graph.macro_challenges)
            guide_count = len(graph.guide_nodes)
            compare_count = len(graph.compare_nodes)
            publish_metadata = self._publish_metadata(chapter_id)
            x = 22 + (index % 3) * 28
            y = 34 + (index // 3) * 24
            regions.append(
                {
                    "id": graph.chapter_id,
                    "title": graph.title,
                    "region_kind": "chapter_galaxy",
                    "status": "available" if can_start else runtime_status,
                    "publish_status": publish_metadata["publish_status"],
                    "position": {"x": x, "y": y},
                    "visual_role": {
                        "celestial_role": "chapter_nebula",
                        "primary_tone": self._tone_for_index(index),
                        "density": self._density_label(macro_count, micro_count),
                        "detail_entry": "lazy_drilldown",
                    },
                    "summary": {
                        "macro_count": macro_count,
                        "micro_count": micro_count,
                        "boss_count": boss_count,
                        "guide_count": guide_count,
                        "compare_count": compare_count,
                        "candidate_content_hash": publish_metadata.get("candidate_content_hash"),
                    },
                    "publish_metadata": publish_metadata,
                    "macro_regions": [
                        {
                            "id": macro.id,
                            "title": macro.title,
                            "micro_count": len(graph.contains.get(macro.id, [])),
                            "boss_id": self._boss_id_for_macro(graph, macro.id),
                        }
                        for macro in graph.macro_nodes
                    ],
                    "runtime": {
                        "can_start": can_start,
                        "runtime_status": runtime_status,
                        "source": chapter_entry.get("source"),
                        "files": dict(chapter_entry.get("files", {})),
                        "blocking_reasons": list(chapter_entry.get("blocking_reasons", [])),
                    },
                    "detail": {
                        "load_policy": "lazy_on_chapter_click" if can_start else "blocked_until_trainable_package",
                        "start_endpoint": "/api/challenge/v1/start" if can_start else None,
                        "quality_endpoint": f"/api/challenge/v1/quality/{graph.chapter_id}",
                        "chapter_id": graph.chapter_id,
                    },
                }
            )

        return {
            "atlas_version": "course_atlas_v1",
            "title": "Math150 Coach 璇剧▼鏄熷浘",
            "catalog_summary": self._catalog_summary(regions),
            "visual_grammar": {
                "subject_role": "subject_galaxy",
                "chapter_role": "chapter_nebula",
                "detail_role": "knowledge_constellation",
                "edge_role": "light_language",
                "pod_role": "diagnostic_dock",
            },
            "render_policy": {
                "default_layer": "chapter_summary",
                "detail_loading": "lazy",
                "do_not_embed_detail_graph": True,
                "start_requires_runtime_registry": True,
            },
            "regions": regions,
            "bridges": self._bridges(regions),
            "warnings": warnings,
        }

    def _publish_metadata(self, chapter_id: str) -> dict[str, Any]:
        chapter_root = Path(self.repository.data_root) / chapter_id
        manifest_path = chapter_root / "publish_manifest.json"
        execution_manifest_path = chapter_root / "publish_execution_manifest.json"
        metadata: dict[str, Any] = {
            "publish_status": "legacy_runtime",
            "manifest_path": None,
            "execution_manifest_path": None,
            "candidate_content_hash": None,
            "publish_plan_schema_version": None,
            "controlled_publish_schema_version": None,
            "execution_manifest_hash": None,
        }
        manifest = self._load_json_if_present(manifest_path)
        if manifest:
            metadata.update(
                {
                    "publish_status": "controlled_published",
                    "manifest_path": self._relative_path(manifest_path),
                    "candidate_content_hash": manifest.get("candidate_content_hash"),
                    "publish_plan_schema_version": manifest.get("publish_plan_schema_version"),
                }
            )
        execution_manifest = self._load_json_if_present(execution_manifest_path)
        if execution_manifest:
            metadata.update(
                {
                    "execution_manifest_path": self._relative_path(execution_manifest_path),
                    "controlled_publish_schema_version": execution_manifest.get("controlled_publish_schema_version"),
                    "execution_manifest_hash": execution_manifest.get("execution_manifest_hash"),
                }
            )
        return metadata

    def _relative_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.repository.data_root))
        except ValueError:
            return str(path)

    @staticmethod
    def _load_json_if_present(path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    @staticmethod
    def _catalog_summary(regions: list[dict[str, Any]]) -> dict[str, int]:
        controlled = sum(1 for region in regions if region.get("publish_status") == "controlled_published")
        legacy = sum(1 for region in regions if region.get("publish_status") == "legacy_runtime")
        trainable = sum(1 for region in regions if region.get("runtime", {}).get("can_start") is True)
        content_pending = sum(1 for region in regions if region.get("runtime", {}).get("runtime_status") == "content_pending")
        invalid = sum(1 for region in regions if region.get("runtime", {}).get("runtime_status") == "invalid")
        return {
            "chapter_count": len(regions),
            "controlled_published_count": controlled,
            "legacy_runtime_count": legacy,
            "trainable_count": trainable,
            "content_pending_count": content_pending,
            "invalid_count": invalid,
        }

    @staticmethod
    def _boss_id_for_macro(graph, macro_id: str) -> str | None:
        for challenge in graph.macro_challenges:
            if challenge.macro_node_id == macro_id:
                return challenge.id
        return None

    @staticmethod
    def _tone_for_index(index: int) -> str:
        return ["cyan", "gold", "green"][index % 3]

    @staticmethod
    def _density_label(macro_count: int, micro_count: int) -> str:
        if macro_count >= 6 or micro_count >= 36:
            return "dense"
        if macro_count >= 3 or micro_count >= 18:
            return "medium"
        return "light"

    @staticmethod
    def _bridges(regions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(regions) < 2:
            return []
        return [
            {
                "id": f"{regions[index]['id']}__to__{regions[index + 1]['id']}",
                "source_id": regions[index]["id"],
                "target_id": regions[index + 1]["id"],
                "edge_type": "course_prerequisite",
                "label": "绔犺妭鍓嶅悗鎵挎帴",
                "visible": True,
            }
            for index in range(len(regions) - 1)
        ]
