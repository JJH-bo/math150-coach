from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.challenge.chapter_candidate_builder import build_chapter_candidate_dry_run
from app.main import create_app
from app.training.session_log import ensure_no_trusted_fields

REQUIRED_REVIEW_CHECKS = {
    "math_scope_checked",
    "macro_micro_structure_checked",
    "repair_targets_checked",
    "hidden_abilities_checked",
    "semantic_edges_checked",
    "boss_coverage_checked",
    "learner_surface_safe",
}

MARKDOWN = """# 候选构建样例
chapter_id: candidate_demo
title: 候选构建样例

## MacroNodes
| id | title | knowledge_node_id |
| --- | --- | --- |
| candidate_demo.macro | 候选大节点 | candidate_demo.macro |

## MicroNodes
| id | macro_node_id | type | title | description |
| --- | --- | --- | --- | --- |
| candidate_demo.macro.concept | candidate_demo.macro | concept | 概念判断 | 判断结构 |
| candidate_demo.macro.method | candidate_demo.macro | method | 方法选择 | 选择方法 |

## MacroChallenges
| id | macro_node_id | title | covers_micro_nodes |
| --- | --- | --- | --- |
| candidate_demo.macro.boss | candidate_demo.macro | 综合验收 | candidate_demo.macro.concept, candidate_demo.macro.method |

## HiddenAbilities
| id | owner_node_id | title | dimensions | why_exists | evidence_sources | failure_modes | repair_target_node_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_demo.hidden.concept_reason | candidate_demo.macro.concept | 概念依据 | concept | 防止只背关键词 | rubric,self_explanation | 只说会但说不出依据 | candidate_demo.macro.concept |

## CompareGuards
| id | title | node_ids | contrast |
| --- | --- | --- | --- |
| candidate_demo.compare.concept_method | 概念方法边界 | candidate_demo.macro.concept, candidate_demo.macro.method | 一个判断结构，一个执行方法 |

## TransferNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| candidate_demo.transfer.variant | 变式迁移 | candidate_demo.macro.method | candidate_demo.macro.method | 防止只会原题 |

## SynthesisNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| candidate_demo.synthesis.boss | 综合拆解 | candidate_demo.macro.boss | candidate_demo.macro.method | Boss 前拆解链路 |

## Edges
| id | edge_type | source_id | target_id | reason |
| --- | --- | --- | --- | --- |
| edge1 | supports | candidate_demo.hidden.concept_reason | candidate_demo.macro.concept | 隐藏能力支撑概念节点 |
| edge2 | requires | candidate_demo.macro.concept | candidate_demo.macro.method | 先判断再选方法 |
| edge3 | boss_checks | candidate_demo.synthesis.boss | candidate_demo.macro.boss | Boss 检查综合拆解 |
| edge4 | transfers_to | candidate_demo.transfer.variant | candidate_demo.macro.method | 变式迁移回方法节点 |
| edge5 | contrasts_with | candidate_demo.compare.concept_method | candidate_demo.macro.method | 对比概念与方法 |

## ErrorRepairMap
| root_cause | repair_target_node_id |
| --- | --- |
| concept_gap | candidate_demo.macro.concept |
| method_error | candidate_demo.macro.method |
"""


def _checklist() -> dict[str, bool]:
    return {code: True for code in REQUIRED_REVIEW_CHECKS}


def test_candidate_dry_run_builds_runtime_payload_and_stable_hash() -> None:
    payload = build_chapter_candidate_dry_run(
        MARKDOWN,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=_checklist(),
        notes="ready",
    )
    same_content_payload = build_chapter_candidate_dry_run(
        MARKDOWN,
        reviewer="different-reviewer",
        decision="approve_for_candidate",
        checklist=_checklist(),
        notes="different notes should not change content hash",
    )

    assert payload["candidate_build_allowed"] is True
    assert payload["dry_run_only"] is True
    assert payload["formal_publish_allowed"] is False
    assert payload["runtime_validation"]["passed"] is True
    assert payload["content_hash"].startswith("sha256:")
    assert len(payload["content_hash"]) == len("sha256:") + 64
    assert payload["content_hash"] == same_content_payload["content_hash"]
    assert payload["candidate"]["challenge_graph"]["contains"]["candidate_demo.macro"] == [
        "candidate_demo.macro.concept",
        "candidate_demo.macro.method",
    ]
    ensure_no_trusted_fields(payload["candidate"])
    serialized_candidate = json.dumps(payload["candidate"], ensure_ascii=False)
    assert "reviewer-a" not in serialized_candidate
    assert "ready" not in serialized_candidate
    assert "evidence_sources" not in serialized_candidate


def test_candidate_dry_run_blocks_when_review_is_incomplete() -> None:
    checklist = _checklist()
    checklist["semantic_edges_checked"] = False

    payload = build_chapter_candidate_dry_run(
        MARKDOWN,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=checklist,
        notes="missing edge check",
    )

    assert payload["candidate_build_allowed"] is False
    assert payload["candidate"] is None
    assert payload["content_hash"] is None
    assert payload["formal_publish_allowed"] is False
    assert "human_review_checklist_incomplete" in payload["candidate_gate"]["reasons"]


def test_candidate_dry_run_api_returns_candidate_preview_only() -> None:
    client = TestClient(create_app("mixed"))

    for path in [
        "/api/challenge/v1/authoring/chapter-draft/candidate-dry-run",
        "/api/challenge/v1/authoring/chapter-draft/candidate-build-dry-run",
    ]:
        response = client.post(
            path,
            json={
                "markdown": MARKDOWN,
                "reviewer": "reviewer-a",
                "decision": "approve_for_candidate",
                "checklist": _checklist(),
                "notes": "ready",
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["mode"] == "chapter_candidate_build_dry_run"
        assert payload["publish_state"] == "candidate_preview_only"
        assert payload["candidate_build_allowed"] is True
        assert payload["formal_publish_allowed"] is False
        assert payload["content_hash"].startswith("sha256:")
