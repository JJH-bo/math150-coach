from __future__ import annotations

from copy import deepcopy

from app.challenge.chapter_candidate_quality import evaluate_chapter_candidate_quality


def _candidate() -> dict:
    graph = {
        "chapter_id": "quality_demo",
        "title": "质量门样例",
        "macro_nodes": [{"id": "quality_demo.macro", "title": "大节点", "knowledge_node_id": "quality_demo.macro"}],
        "micro_nodes": [
            {"id": "quality_demo.concept", "macro_node_id": "quality_demo.macro", "type": "concept", "title": "概念", "description": "概念判断", "default_dimensions": ["concept"]},
            {"id": "quality_demo.method", "macro_node_id": "quality_demo.macro", "type": "method", "title": "方法", "description": "方法选择", "default_dimensions": ["method"]},
        ],
        "macro_challenges": [
            {"id": "quality_demo.boss", "macro_node_id": "quality_demo.macro", "title": "综合验收", "covers_micro_nodes": ["quality_demo.concept", "quality_demo.method"], "target_dimensions": ["concept", "method"]}
        ],
        "atom_nodes": [
            {"id": "quality_demo.hidden.concept", "micro_node_id": "quality_demo.concept", "title": "概念依据", "description": "防止只背关键词", "dimensions": ["concept"], "repair_cues": ["只写关键词"]},
            {"id": "quality_demo.hidden.method", "micro_node_id": "quality_demo.method", "title": "方法依据", "description": "防止乱套方法", "dimensions": ["method"], "repair_cues": ["入口不清"]},
        ],
        "compare_nodes": [],
        "guide_nodes": [
            {"id": "quality_demo.transfer.variant", "kind": "bridge", "title": "变式迁移", "description": "防止只会原题", "related_node_ids": ["quality_demo.method"], "focus_dimensions": ["method"], "map_hint": "迁移路线", "trainable": False},
            {"id": "quality_demo.synthesis.boss", "kind": "boss_gate", "title": "综合拆解", "description": "Boss 前拆解链路", "related_node_ids": ["quality_demo.boss", "quality_demo.method"], "focus_dimensions": ["method"], "map_hint": "综合路线", "trainable": False},
        ],
        "typed_edges": [
            {"id": "e1", "edge_type": "support", "source_id": "quality_demo.hidden.concept", "target_id": "quality_demo.concept", "label": "supports", "reason": "隐藏能力支撑概念节点", "semantic_weight": 1, "decision_role": "diagnostic", "visible": False},
            {"id": "e2", "edge_type": "transfers_to", "source_id": "quality_demo.transfer.variant", "target_id": "quality_demo.method", "label": "transfers_to", "reason": "变式迁移回方法节点", "semantic_weight": 1, "decision_role": "progression", "visible": True},
            {"id": "e3", "edge_type": "boss_covers", "source_id": "quality_demo.synthesis.boss", "target_id": "quality_demo.boss", "label": "boss_checks", "reason": "Boss 检查综合拆解", "semantic_weight": 1, "decision_role": "diagnostic", "visible": True},
        ],
        "contains": {"quality_demo.macro": ["quality_demo.concept", "quality_demo.method"]},
        "unlock_edges": [],
        "error_to_micro_mapping": {
            "concept_gap": "quality_demo.concept",
            "trigger_failure": "quality_demo.concept",
            "method_error": "quality_demo.method",
            "transformation_error": "quality_demo.method",
            "calculation_error": "quality_demo.method",
            "expression_weakness": "quality_demo.method",
        },
    }
    return {
        "content_schema_version": "chapter_candidate_v1",
        "chapter_id": "quality_demo",
        "title": "质量门样例",
        "challenge_graph": graph,
        "logic_graph": {"chapter_id": "quality_demo", "title": "质量门样例 逻辑能力网", "abilities": [], "edges": [{"id": "e1"}]},
        "error_repair_map": graph["error_to_micro_mapping"],
    }


def test_candidate_quality_passes_strong_candidate_but_keeps_formal_publish_locked() -> None:
    report = evaluate_chapter_candidate_quality(
        _candidate(),
        content_hash="sha256:" + "a" * 64,
        runtime_validation={"passed": True, "errors": [], "warnings": []},
        formal_publish_allowed=False,
    )

    assert report["grade"] == "pass"
    assert report["candidate_publish_gate"]["candidate_quality_passed"] is True
    assert report["candidate_publish_gate"]["formal_publish_allowed"] is False
    assert report["candidate_publish_gate"]["blocking_codes"] == []


def test_candidate_quality_fails_when_repair_target_is_invalid() -> None:
    candidate = deepcopy(_candidate())
    candidate["challenge_graph"]["error_to_micro_mapping"]["method_error"] = "missing.node"

    report = evaluate_chapter_candidate_quality(
        candidate,
        content_hash="sha256:" + "b" * 64,
        runtime_validation={"passed": True, "errors": [], "warnings": []},
        formal_publish_allowed=False,
    )

    assert report["grade"] == "fail"
    assert "repair_target_invalid" in report["candidate_publish_gate"]["blocking_codes"]


def test_candidate_quality_warns_when_core_error_mapping_is_incomplete() -> None:
    candidate = deepcopy(_candidate())
    del candidate["challenge_graph"]["error_to_micro_mapping"]["expression_weakness"]

    report = evaluate_chapter_candidate_quality(
        candidate,
        content_hash="sha256:" + "d" * 64,
        runtime_validation={"passed": True, "errors": [], "warnings": []},
        formal_publish_allowed=False,
    )

    assert report["grade"] == "warn"
    assert report["candidate_publish_gate"]["candidate_quality_passed"] is False
    assert report["candidate_publish_gate"]["blocking_codes"] == []


def test_candidate_quality_blocks_trusted_field_leaks() -> None:
    candidate = deepcopy(_candidate())
    candidate["challenge_graph"]["expected_answer"] = "answer"

    report = evaluate_chapter_candidate_quality(
        candidate,
        content_hash="sha256:" + "c" * 64,
        runtime_validation={"passed": True, "errors": [], "warnings": []},
        formal_publish_allowed=False,
    )

    assert report["grade"] == "fail"
    assert "trusted_field_leak" in report["candidate_publish_gate"]["blocking_codes"]
