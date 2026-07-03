from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any


MICRO_TYPES = {"concept", "trigger", "method", "transformation", "calculation", "expression"}
EDGE_TYPES = {
    "requires",
    "supports",
    "derives_to",
    "transforms_to",
    "contrasts_with",
    "commonly_confused_with",
    "checks",
    "repairs",
    "transfers_to",
    "boss_checks",
    "blocks",
}
ERROR_TYPES = {
    "concept_gap",
    "trigger_failure",
    "method_error",
    "transformation_error",
    "process_gap",
    "calculation_error",
    "condition_miss",
    "formula_memory_error",
    "knowledge_confusion",
    "expression_weakness",
    "migration_failure",
    "synthesis_failure",
}


def validate_chapter_markdown(markdown: str) -> dict[str, Any]:
    importer = ChapterDraftImporter()
    return importer.validate(markdown)


class ChapterDraftImporter:
    """Deterministic structured-Markdown importer for chapter graph drafts."""

    def validate(self, markdown: str) -> dict[str, Any]:
        metadata, sections = self._parse(markdown)
        draft = self._build_draft(metadata, sections)
        report = self._validate_draft(draft)
        preview = self._preview(draft)
        return {
            "mode": "structured_markdown_draft",
            "publish_state": "draft_only",
            "workflow_stage": "draft_preview",
            "report": report,
            "draft": draft,
            "preview": preview,
            "readiness": self._readiness(draft, report, preview),
            "template": self.template(),
        }

    @staticmethod
    def template() -> str:
        return """# 一阶微分方程扩展示例
chapter_id: ode_extension_demo
title: 一阶微分方程扩展示例

## MacroNodes
| id | title | knowledge_node_id |
| --- | --- | --- |
| ode_demo | 示例大节点 | ode_demo |

## MicroNodes
| id | macro_node_id | type | title | description |
| --- | --- | --- | --- | --- |
| ode_demo.concept | ode_demo | concept | 概念判断 | 说明这个节点训练什么 |

## MacroChallenges
| id | macro_node_id | title | covers_micro_nodes |
| --- | --- | --- | --- |
| ode_demo.macro_challenge | ode_demo | 示例综合验收 | ode_demo.concept |

## HiddenAbilities
| id | owner_node_id | title | dimensions | why_exists | evidence_sources | failure_modes | repair_target_node_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ode_demo.hidden.concept_basis | ode_demo.concept | 概念依据说清 | concept | 判断是否真懂概念 | rubric, self_explanation | 只写关键词 | ode_demo.concept |

## CompareGuards
| id | title | node_ids | contrast |
| --- | --- | --- | --- |
| ode_demo.compare.demo_vs_other | 示例对比 | ode_demo.concept, ode_demo.macro_challenge | 题眼差异 |

## TransferNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| ode_demo.transfer.variant | 变式迁移 | ode_demo.concept | ode_demo.concept | 防止只会原题 |

## SynthesisNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| ode_demo.synthesis.boss | 综合拆解 | ode_demo.macro_challenge | ode_demo.concept | Boss 前拆解能力链 |

## Edges
| id | edge_type | source_id | target_id | reason |
| --- | --- | --- | --- | --- |
| e1 | supports | ode_demo.hidden.concept_basis | ode_demo.concept | 隐藏能力支撑训练节点 |

## ErrorRepairMap
| root_cause | repair_target_node_id |
| --- | --- |
| concept_gap | ode_demo.concept |
"""

    def _parse(self, markdown: str) -> tuple[dict[str, str], dict[str, list[dict[str, str]]]]:
        metadata: dict[str, str] = {}
        raw_sections: dict[str, list[str]] = defaultdict(list)
        current_section = "__meta__"
        for raw_line in markdown.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("# "):
                metadata.setdefault("title", line[2:].strip())
                continue
            if line.startswith("## "):
                current_section = self._normalize_section(line[3:].strip())
                continue
            if current_section == "__meta__" and ":" in line and not line.startswith("|"):
                key, value = line.split(":", 1)
                metadata[key.strip().lower()] = value.strip()
                continue
            raw_sections[current_section].append(line)

        sections = {
            section: self._parse_table(lines)
            for section, lines in raw_sections.items()
            if section != "__meta__"
        }
        return metadata, sections

    @staticmethod
    def _normalize_section(section: str) -> str:
        key = re.sub(r"[^a-z0-9]+", "_", section.strip().lower()).strip("_")
        aliases = {
            "macro_nodes": "macronodes",
            "micro_nodes": "micronodes",
            "macro_challenges": "macrochallenges",
            "hidden_abilities": "hiddenabilities",
            "compare_guards": "compareguards",
            "transfer_nodes": "transfernodes",
            "synthesis_nodes": "synthesisnodes",
            "error_repair_map": "errorrepairmap",
        }
        return aliases.get(key, key)

    @staticmethod
    def _parse_table(lines: list[str]) -> list[dict[str, str]]:
        table_lines = [line for line in lines if line.startswith("|") and line.endswith("|")]
        if len(table_lines) < 2:
            return []
        headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
        rows: list[dict[str, str]] = []
        for line in table_lines[2:]:
            values = [cell.strip() for cell in line.strip("|").split("|")]
            values += [""] * max(0, len(headers) - len(values))
            rows.append({headers[index]: values[index] for index in range(len(headers))})
        return rows

    def _build_draft(self, metadata: dict[str, str], sections: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
        chapter_id = metadata.get("chapter_id", "")
        title = metadata.get("title", chapter_id)
        macros = [
            {
                "id": row.get("id", ""),
                "title": row.get("title", ""),
                "knowledge_node_id": row.get("knowledge_node_id", "") or row.get("id", ""),
            }
            for row in sections.get("macronodes", [])
        ]
        micros = [
            {
                "id": row.get("id", ""),
                "macro_node_id": row.get("macro_node_id", ""),
                "type": row.get("type", ""),
                "title": row.get("title", ""),
                "description": row.get("description", ""),
            }
            for row in sections.get("micronodes", [])
        ]
        challenges = [
            {
                "id": row.get("id", ""),
                "macro_node_id": row.get("macro_node_id", ""),
                "title": row.get("title", ""),
                "covers_micro_nodes": self._split_list(row.get("covers_micro_nodes", "")),
            }
            for row in sections.get("macrochallenges", [])
        ]
        abilities = self._logic_abilities(sections)
        compare_guards = [
            {
                "id": row.get("id", ""),
                "title": row.get("title", ""),
                "node_ids": self._split_list(row.get("node_ids", "")),
                "contrast": row.get("contrast", ""),
                "node_kind": "compare_guard",
            }
            for row in sections.get("compareguards", [])
        ]
        edges = [
            {
                "id": row.get("id", ""),
                "edge_type": row.get("edge_type", ""),
                "source_id": row.get("source_id", ""),
                "target_id": row.get("target_id", ""),
                "reason": row.get("reason", ""),
            }
            for row in sections.get("edges", [])
        ]
        repair_map = [
            {
                "root_cause": row.get("root_cause", ""),
                "repair_target_node_id": row.get("repair_target_node_id", ""),
            }
            for row in sections.get("errorrepairmap", [])
        ]
        return {
            "chapter_id": chapter_id,
            "title": title,
            "macro_nodes": macros,
            "micro_nodes": micros,
            "macro_challenges": challenges,
            "logic_nodes": abilities + compare_guards,
            "logic_edges": edges,
            "error_repair_map": repair_map,
            "challenge_graph_draft": {
                "chapter_id": chapter_id,
                "title": title,
                "macro_nodes": macros,
                "micro_nodes": micros,
                "macro_challenges": challenges,
            },
            "logic_graph_draft": {
                "chapter_id": chapter_id,
                "title": f"{title} 逻辑能力网",
                "abilities": abilities + compare_guards,
                "edges": edges,
            },
        }

    def _logic_abilities(self, sections: dict[str, list[dict[str, str]]]) -> list[dict[str, Any]]:
        abilities: list[dict[str, Any]] = []
        for section, node_kind in [
            ("hiddenabilities", "hidden_ability"),
            ("transfernodes", "transfer_node"),
            ("synthesisnodes", "synthesis_node"),
        ]:
            for row in sections.get(section, []):
                abilities.append(
                    {
                        "id": row.get("id", ""),
                        "title": row.get("title", ""),
                        "node_kind": node_kind,
                        "owner_node_id": row.get("owner_node_id", ""),
                        "repair_target_node_id": row.get("repair_target_node_id", ""),
                        "dimensions": self._split_list(row.get("dimensions", "")),
                        "why_exists": row.get("why_exists", ""),
                        "evidence_sources": self._split_list(row.get("evidence_sources", "")),
                        "failure_modes": self._split_list(row.get("failure_modes", "")),
                    }
                )
        return abilities

    def _validate_draft(self, draft: dict[str, Any]) -> dict[str, Any]:
        errors: list[dict[str, str]] = []
        warnings: list[dict[str, str]] = []
        self._basic_checks(draft, errors)
        self._reference_checks(draft, errors, warnings)
        self._quality_checks(draft, errors, warnings)
        return {
            "passed": not errors,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
        }

    def _basic_checks(self, draft: dict[str, Any], errors: list[dict[str, str]]) -> None:
        if not re.fullmatch(r"[a-zA-Z0-9_.-]+", draft.get("chapter_id", "")):
            errors.append(self._issue("chapter_id", "chapter_id 必须存在，并且只能包含字母、数字、下划线、点或短横线。"))
        for collection in ["macro_nodes", "micro_nodes", "macro_challenges", "logic_nodes", "logic_edges"]:
            ids = [item.get("id", "") for item in draft.get(collection, [])]
            missing = [item for item in draft.get(collection, []) if not item.get("id")]
            if missing:
                errors.append(self._issue(collection, "存在缺少 id 的条目。"))
            duplicates = [node_id for node_id, count in Counter(ids).items() if node_id and count > 1]
            if duplicates:
                errors.append(self._issue(collection, f"id 重复：{', '.join(duplicates)}。"))

    def _reference_checks(
        self,
        draft: dict[str, Any],
        errors: list[dict[str, str]],
        warnings: list[dict[str, str]],
    ) -> None:
        macro_ids = {node["id"] for node in draft.get("macro_nodes", []) if node.get("id")}
        micro_ids = {node["id"] for node in draft.get("micro_nodes", []) if node.get("id")}
        challenge_ids = {node["id"] for node in draft.get("macro_challenges", []) if node.get("id")}
        logic_ids = {node["id"] for node in draft.get("logic_nodes", []) if node.get("id")}
        known_ids = macro_ids | micro_ids | challenge_ids | logic_ids

        for micro in draft.get("micro_nodes", []):
            if micro.get("macro_node_id") not in macro_ids:
                errors.append(self._issue(micro.get("id", "micro_nodes"), "MicroNode 引用了不存在的 MacroNode。"))
            if micro.get("type") not in MICRO_TYPES:
                errors.append(self._issue(micro.get("id", "micro_nodes"), f"MicroNode type 必须是：{', '.join(sorted(MICRO_TYPES))}。"))

        for challenge in draft.get("macro_challenges", []):
            if challenge.get("macro_node_id") not in macro_ids:
                errors.append(self._issue(challenge.get("id", "macro_challenges"), "MacroChallenge 引用了不存在的 MacroNode。"))
            for micro_id in challenge.get("covers_micro_nodes", []):
                if micro_id not in micro_ids:
                    errors.append(self._issue(challenge.get("id", "macro_challenges"), f"Boss 覆盖了不存在的 MicroNode：{micro_id}。"))

        for logic in draft.get("logic_nodes", []):
            if logic.get("node_kind") == "compare_guard":
                node_ids = logic.get("node_ids", [])
                if len(node_ids) < 2:
                    errors.append(self._issue(logic.get("id", "compare_guard"), "CompareGuard 至少要连接两个易混节点。"))
                if not logic.get("contrast"):
                    errors.append(self._issue(logic.get("id", "compare_guard"), "CompareGuard 必须写清 contrast/题眼差异。"))
                for node_id in node_ids:
                    if node_id not in known_ids:
                        errors.append(self._issue(logic.get("id", "compare_guard"), f"CompareGuard 引用了不存在的节点：{node_id}。"))
                continue
            if logic.get("owner_node_id") and logic.get("owner_node_id") not in known_ids:
                errors.append(self._issue(logic.get("id", "logic_nodes"), "逻辑节点 owner_node_id 不存在。"))
            if logic.get("repair_target_node_id") not in micro_ids:
                errors.append(self._issue(logic.get("id", "logic_nodes"), "逻辑节点必须指向明确的 MicroNode repair_target_node_id。"))

        for edge in draft.get("logic_edges", []):
            if edge.get("edge_type") not in EDGE_TYPES:
                errors.append(self._issue(edge.get("id", "logic_edges"), f"edge_type 不在允许集合内：{edge.get('edge_type')}。"))
            if edge.get("source_id") == edge.get("target_id"):
                errors.append(self._issue(edge.get("id", "logic_edges"), "语义边不能自连。"))
            for field in ["source_id", "target_id"]:
                if edge.get(field) not in known_ids:
                    errors.append(self._issue(edge.get("id", "logic_edges"), f"{field} 引用了不存在的节点：{edge.get(field)}。"))
            if not edge.get("reason"):
                warnings.append(
                    self._issue(
                        edge.get("id", "logic_edges"),
                        "语义边缺少 reason，后续解释力会变弱。",
                        severity="warning",
                    )
                )

    def _quality_checks(
        self,
        draft: dict[str, Any],
        errors: list[dict[str, str]],
        warnings: list[dict[str, str]],
    ) -> None:
        micro_by_macro: dict[str, int] = defaultdict(int)
        micro_ids = {node["id"] for node in draft.get("micro_nodes", []) if node.get("id")}
        logic_ids = {node["id"] for node in draft.get("logic_nodes", []) if node.get("id")}
        for micro in draft.get("micro_nodes", []):
            micro_by_macro[micro.get("macro_node_id", "")] += 1
        for macro_id, count in micro_by_macro.items():
            if count > 12:
                errors.append(self._issue(macro_id, "单个 MacroNode 可见 MicroNode 超过 12 个，地图会膨胀。"))
            elif count > 8:
                warnings.append(
                    self._issue(
                        macro_id,
                        "单个 MacroNode 可见 MicroNode 超过 8 个，建议合并或转为 HiddenAbility。",
                        severity="warning",
                    )
                )

        for logic in draft.get("logic_nodes", []):
            if logic.get("node_kind") == "compare_guard":
                continue
            if not logic.get("why_exists"):
                errors.append(self._issue(logic.get("id", "logic_nodes"), "隐藏/迁移/综合能力必须写 why_exists。"))
            if logic.get("node_kind") == "hidden_ability" and not logic.get("evidence_sources"):
                errors.append(self._issue(logic.get("id", "logic_nodes"), "HiddenAbility 必须写 evidence_sources。"))

        mapped_errors = set()
        for item in draft.get("error_repair_map", []):
            root_cause = item.get("root_cause", "")
            repair_target = item.get("repair_target_node_id", "")
            if root_cause not in ERROR_TYPES:
                errors.append(self._issue(root_cause or "error_repair_map", "root_cause 不在已知错因集合内。"))
            if repair_target not in micro_ids:
                errors.append(self._issue(root_cause or "error_repair_map", "每个 root_cause 必须映射到明确的 MicroNode repair target。"))
            mapped_errors.add(root_cause)
        if not mapped_errors:
            errors.append(self._issue("error_repair_map", "必须提供至少一个 root cause 到 repair target 的映射。"))

        edge_connected_logic = {
            edge.get("source_id")
            for edge in draft.get("logic_edges", [])
            if edge.get("source_id") in logic_ids or edge.get("target_id") in logic_ids
        } | {
            edge.get("target_id")
            for edge in draft.get("logic_edges", [])
            if edge.get("source_id") in logic_ids or edge.get("target_id") in logic_ids
        }
        orphan_logic = sorted(logic_ids - edge_connected_logic)
        if orphan_logic:
            warnings.append(
                self._issue(
                    "logic_edges",
                    f"存在未被语义边连接的逻辑节点：{', '.join(orphan_logic)}。",
                    severity="warning",
                )
            )

    @staticmethod
    def _preview(draft: dict[str, Any]) -> dict[str, Any]:
        nodes = []
        for collection, kind in [
            ("macro_nodes", "macro_node"),
            ("micro_nodes", "micro_node"),
            ("macro_challenges", "macro_challenge"),
            ("logic_nodes", "logic_node"),
        ]:
            for node in draft.get(collection, []):
                nodes.append(
                    {
                        "id": node.get("id"),
                        "title": node.get("title"),
                        "node_kind": node.get("node_kind", kind),
                    }
                )
        return {
            "nodes": nodes,
            "edges": draft.get("logic_edges", []),
            "counts": {
                "macro_nodes": len(draft.get("macro_nodes", [])),
                "micro_nodes": len(draft.get("micro_nodes", [])),
                "macro_challenges": len(draft.get("macro_challenges", [])),
                "logic_nodes": len(draft.get("logic_nodes", [])),
                "logic_edges": len(draft.get("logic_edges", [])),
            },
        }

    def _readiness(
        self,
        draft: dict[str, Any],
        report: dict[str, Any],
        preview: dict[str, Any],
    ) -> dict[str, Any]:
        error_count = int(report.get("error_count", 0) or 0)
        warning_count = int(report.get("warning_count", 0) or 0)
        max_micro_per_macro = self._max_micro_per_macro(draft)
        repair_blocking_codes = {"invalid_repair_target", "invalid_root_cause", "missing_repair_map"}
        repair_errors = [
            error
            for error in report.get("errors", [])
            if error.get("code") in repair_blocking_codes
            or "repair" in error.get("message", "")
            or "repair_target" in error.get("message", "")
        ]
        has_repair_map = bool(draft.get("error_repair_map"))

        visible_budget_state = "pass"
        if max_micro_per_macro > 12:
            visible_budget_state = "fail"
        elif max_micro_per_macro > 8:
            visible_budget_state = "warn"

        repair_targets_state = "pass"
        if repair_errors or not has_repair_map:
            repair_targets_state = "fail"

        return {
            "status": "blocked" if error_count else "review_ready",
            "publish_allowed": False,
            "blocking_error_count": error_count,
            "warning_count": warning_count,
            "next_action": "fix_validation_errors" if error_count else "human_review",
            "counts": dict(preview.get("counts", {})),
            "visible_budget": {
                "max_micro_per_macro": max_micro_per_macro,
                "recommended_max": 8,
                "hard_max": 12,
            },
            "checks": [
                {
                    "code": "graph_valid",
                    "label": "Graph validation",
                    "state": "fail" if error_count else "pass",
                    "summary": f"{error_count} blocking errors" if error_count else "No blocking validation errors",
                },
                {
                    "code": "visible_budget",
                    "label": "Visible node budget",
                    "state": visible_budget_state,
                    "summary": f"Max {max_micro_per_macro} visible MicroNodes per MacroNode",
                },
                {
                    "code": "repair_targets",
                    "label": "Repair targets",
                    "state": repair_targets_state,
                    "summary": (
                        "Repair targets mapped to visible MicroNodes"
                        if repair_targets_state == "pass"
                        else "Repair target coverage needs fixes"
                    ),
                },
                {
                    "code": "human_review_required",
                    "label": "Human review",
                    "state": "locked",
                    "summary": "Human review is required before candidate build",
                },
                {
                    "code": "formal_publish_locked",
                    "label": "Formal publish",
                    "state": "locked",
                    "summary": "Formal publish is not available from draft preview",
                },
            ],
        }

    @staticmethod
    def _max_micro_per_macro(draft: dict[str, Any]) -> int:
        counts = Counter(
            micro.get("macro_node_id", "")
            for micro in draft.get("micro_nodes", [])
            if micro.get("macro_node_id")
        )
        return max(counts.values(), default=0)

    @staticmethod
    def _split_list(value: str) -> list[str]:
        if not value:
            return []
        return [item.strip() for item in re.split(r"[,，;；]", value) if item.strip()]

    @classmethod
    def _issue(
        cls,
        target: str,
        message: str,
        *,
        severity: str = "error",
        code: str | None = None,
        target_kind: str | None = None,
        suggested_fix: str | None = None,
    ) -> dict[str, str]:
        profile = cls._issue_profile(target, message, severity)
        return {
            "target": target,
            "message": message,
            "code": code or profile["code"],
            "severity": severity,
            "target_kind": target_kind or profile["target_kind"],
            "suggested_fix": suggested_fix or profile["suggested_fix"],
        }

    @classmethod
    def _issue_profile(cls, target: str, message: str, severity: str) -> dict[str, str]:
        text = f"{target} {message}".lower()
        target_kind = cls._issue_target_kind(target)

        code = "draft_validation_warning" if severity == "warning" else "draft_validation_error"
        suggested_fix = "根据提示修正这个草稿条目后重新校验。"

        if target == "chapter_id":
            code = "invalid_chapter_id"
            target_kind = "chapter"
            suggested_fix = "填写只包含字母、数字、下划线、点或短横线的 chapter_id。"
        elif "缺少 id" in message:
            code = "missing_item_id"
            suggested_fix = "为该表格中的每个条目补充唯一 id。"
        elif "重复" in message and "id" in text:
            code = "duplicate_item_id"
            suggested_fix = "保留一个 id，并把重复条目改成新的唯一 id。"
        elif "micronode" in text and "12" in text:
            code = "visible_node_budget_exceeded"
            target_kind = "macro_nodes"
            suggested_fix = "减少该 MacroNode 下的可见 MicroNode，或迁移为 HiddenAbility。"
        elif "micronode" in text and "8" in text:
            code = "visible_node_budget_warning"
            target_kind = "macro_nodes"
            suggested_fix = "考虑合并相近 MicroNode，或把细粒度能力转为 HiddenAbility。"
        elif "macrochallenge" in text and "macronode" in text:
            code = "invalid_macro_challenge_macro"
            suggested_fix = "把 MacroChallenge 绑定到已存在的 MacroNode。"
        elif "boss" in text and "micronode" in text:
            code = "invalid_macro_challenge_coverage"
            suggested_fix = "只在 covers_micro_nodes 中填写已存在的 MicroNode。"
        elif "micronode" in text and "macronode" in text:
            code = "invalid_micro_macro"
            suggested_fix = "把 MicroNode 的 macro_node_id 改为已存在的 MacroNode。"
        elif "micronode type" in text:
            code = "invalid_micro_type"
            suggested_fix = "把 MicroNode type 改为允许集合中的一种。"
        elif "compareguard" in text and "contrast" in text:
            code = "missing_compare_contrast"
            target_kind = "logic_nodes"
            suggested_fix = "补充 CompareGuard 的 contrast，写清两个节点容易混淆的题眼差异。"
        elif "compareguard" in text:
            code = "invalid_compare_guard"
            target_kind = "logic_nodes"
            suggested_fix = "让 CompareGuard 至少连接两个已存在且容易混淆的节点。"
        elif "owner_node_id" in text:
            code = "invalid_logic_owner"
            target_kind = "logic_nodes"
            suggested_fix = "把 owner_node_id 改为已存在的可见节点、Boss 或逻辑节点。"
        elif target == "error_repair_map" and "root cause" in text:
            code = "missing_repair_map"
            target_kind = "error_repair_map"
            suggested_fix = "至少补充一个 root_cause 到 MicroNode repair target 的映射。"
        elif "root_cause" in text and "repair target" not in text:
            code = "invalid_root_cause"
            target_kind = "error_repair_map"
            suggested_fix = "把 root_cause 改为系统已知错因集合中的一种。"
        elif "repair target" in text or "repair_target_node_id" in text:
            code = "invalid_repair_target"
            suggested_fix = "把修复目标改为已存在的 MicroNode id。"
        elif "edge_type" in text:
            code = "invalid_edge_type"
            target_kind = "logic_edges"
            suggested_fix = "把 edge_type 改为允许的语义边类型。"
        elif "自连" in message:
            code = "self_loop_edge"
            target_kind = "logic_edges"
            suggested_fix = "把这条边改成连接两个不同节点。"
        elif "source_id" in text or "target_id" in text:
            code = "invalid_edge_endpoint"
            target_kind = "logic_edges"
            suggested_fix = "把边的 source_id 和 target_id 都改为已存在节点。"
        elif "reason" in text and severity == "warning":
            code = "missing_edge_reason"
            target_kind = "logic_edges"
            suggested_fix = "补一句这条语义边存在的原因。"
        elif "why_exists" in text:
            code = "missing_why_exists"
            target_kind = "logic_nodes"
            suggested_fix = "补充该隐藏、迁移或综合能力为什么必须存在。"
        elif "evidence_sources" in text:
            code = "missing_evidence_sources"
            target_kind = "logic_nodes"
            suggested_fix = "为 HiddenAbility 补充 rubric、self_explanation 或 response_steps 等证据来源。"
        elif target == "logic_edges" and severity == "warning":
            code = "orphan_logic_node"
            target_kind = "logic_edges"
            suggested_fix = "为这些逻辑节点补充 supports、checks、contrasts 或 repairs 等语义边。"

        return {
            "code": code,
            "target_kind": target_kind,
            "suggested_fix": suggested_fix,
        }

    @staticmethod
    def _issue_target_kind(target: str) -> str:
        if target == "chapter_id":
            return "chapter"
        if target in {"macro_nodes", "micro_nodes", "macro_challenges", "logic_nodes", "logic_edges"}:
            return target
        if target == "error_repair_map" or target in ERROR_TYPES:
            return "error_repair_map"
        if target == "compare_guard":
            return "logic_nodes"
        lowered = target.lower()
        if re.fullmatch(r"e\d+", lowered):
            return "logic_edges"
        if ".macro_challenge" in lowered:
            return "macro_challenges"
        if ".hidden." in lowered or ".transfer." in lowered or ".synthesis." in lowered or ".compare." in lowered:
            return "logic_nodes"
        if ".macro." in lowered:
            return "micro_nodes"
        return "draft_item"
