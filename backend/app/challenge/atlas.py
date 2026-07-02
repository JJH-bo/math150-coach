from __future__ import annotations

from pathlib import Path
from typing import Any

from app.challenge.repository import ChallengeRepository, ChallengeRepositoryError


class ChallengeAtlasBuilder:
    """Builds a lightweight course-level atlas without exposing chapter internals."""

    def __init__(self, repository: ChallengeRepository | None = None) -> None:
        self.repository = repository or ChallengeRepository()

    def build(self) -> dict[str, Any]:
        chapter_ids = self._discover_chapter_ids()
        regions: list[dict[str, Any]] = []
        warnings: list[str] = []
        for index, chapter_id in enumerate(chapter_ids):
            try:
                graph = self.repository.load_graph(chapter_id)
            except ChallengeRepositoryError as exc:
                warnings.append(str(exc))
                continue
            macro_count = len(graph.macro_nodes)
            micro_count = len(graph.micro_nodes)
            boss_count = len(graph.macro_challenges)
            guide_count = len(graph.guide_nodes)
            compare_count = len(graph.compare_nodes)
            x = 22 + (index % 3) * 28
            y = 34 + (index // 3) * 24
            regions.append(
                {
                    "id": graph.chapter_id,
                    "title": graph.title,
                    "region_kind": "chapter_galaxy",
                    "status": "available",
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
                    },
                    "macro_regions": [
                        {
                            "id": macro.id,
                            "title": macro.title,
                            "micro_count": len(graph.contains.get(macro.id, [])),
                            "boss_id": self._boss_id_for_macro(graph, macro.id),
                        }
                        for macro in graph.macro_nodes
                    ],
                    "detail": {
                        "load_policy": "lazy_on_chapter_click",
                        "start_endpoint": "/api/challenge/v1/start",
                        "chapter_id": graph.chapter_id,
                    },
                }
            )

        return {
            "atlas_version": "course_atlas_v1",
            "title": "Math150 Coach 课程星图",
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
            },
            "regions": regions,
            "bridges": self._bridges(regions),
            "warnings": warnings,
        }

    def _discover_chapter_ids(self) -> list[str]:
        root = Path(self.repository.data_root)
        if not root.exists():
            return []
        chapter_ids = [
            path.name
            for path in root.iterdir()
            if path.is_dir() and (path / "challenge_graph.yaml").exists()
        ]
        return sorted(chapter_ids, key=lambda chapter_id: (chapter_id != "ode_network_mvp", chapter_id))

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
                "label": "章节前后承接",
                "visible": True,
            }
            for index in range(len(regions) - 1)
        ]
