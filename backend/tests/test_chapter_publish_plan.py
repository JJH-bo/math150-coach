from __future__ import annotations

from fastapi.testclient import TestClient

from app.challenge import chapter_publish_plan
from app.challenge.chapter_publish_plan import build_chapter_publish_plan_dry_run
from app.main import create_app

REQUIRED_REVIEW_CHECKS = {
    "math_scope_checked",
    "macro_micro_structure_checked",
    "repair_targets_checked",
    "hidden_abilities_checked",
    "semantic_edges_checked",
    "boss_coverage_checked",
    "learner_surface_safe",
}

MARKDOWN = """# 发布计划样例
chapter_id: publish_demo
title: 发布计划样例

## MacroNodes
| id | title | knowledge_node_id |
| --- | --- | --- |
| publish_demo.macro | 发布大节点 | publish_demo.macro |

## MicroNodes
| id | macro_node_id | type | title | description |
| --- | --- | --- | --- | --- |
| publish_demo.concept | publish_demo.macro | concept | 概念判断 | 判断结构 |
| publish_demo.method | publish_demo.macro | method | 方法选择 | 选择方法 |

## MacroChallenges
| id | macro_node_id | title | covers_micro_nodes |
| --- | --- | --- | --- |
| publish_demo.boss | publish_demo.macro | 综合验收 | publish_demo.concept, publish_demo.method |

## HiddenAbilities
| id | owner_node_id | title | dimensions | why_exists | evidence_sources | failure_modes | repair_target_node_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| publish_demo.hidden.concept | publish_demo.concept | 概念依据 | concept | 防止只背关键词 | rubric,self_explanation | 只写关键词 | publish_demo.concept |
| publish_demo.hidden.method | publish_demo.method | 方法依据 | method | 防止乱套方法 | rubric,self_explanation | 入口不清 | publish_demo.method |

## TransferNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| publish_demo.transfer.variant | 变式迁移 | publish_demo.method | publish_demo.method | 防止只会原题 |

## SynthesisNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| publish_demo.synthesis.boss | 综合拆解 | publish_demo.boss | publish_demo.method | Boss 前拆解链路 |

## Edges
| id | edge_type | source_id | target_id | reason |
| --- | --- | --- | --- | --- |
| e1 | supports | publish_demo.hidden.concept | publish_demo.concept | 隐藏能力支撑概念节点 |
| e2 | supports | publish_demo.hidden.method | publish_demo.method | 隐藏能力支撑方法节点 |
| e3 | transfers_to | publish_demo.transfer.variant | publish_demo.method | 变式迁移回方法节点 |
| e4 | boss_checks | publish_demo.synthesis.boss | publish_demo.boss | Boss 检查综合拆解 |
| e5 | requires | publish_demo.concept | publish_demo.method | 先判断再选方法 |

## ErrorRepairMap
| root_cause | repair_target_node_id |
| --- | --- |
| concept_gap | publish_demo.concept |
| trigger_failure | publish_demo.concept |
| method_error | publish_demo.method |
| transformation_error | publish_demo.method |
| calculation_error | publish_demo.method |
| expression_weakness | publish_demo.method |
"""


def _checklist() -> dict[str, bool]:
    return {code: True for code in REQUIRED_REVIEW_CHECKS}


def test_publish_plan_dry_run_builds_planned_files_without_unlocking_publish() -> None:
    payload = build_chapter_publish_plan_dry_run(
        MARKDOWN,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=_checklist(),
        notes="ready",
    )

    assert payload["mode"] == "chapter_publish_plan_dry_run"
    assert payload["publish_plan_grade"] == "ready"
    assert payload["dry_run_only"] is True
    assert payload["formal_publish_allowed"] is False
    assert payload["publish_plan_hash"].startswith("sha256:")
    planned_paths = {item["path"] for item in payload["planned_files"]}
    assert planned_paths == {
        "backend/challenge_data/publish_demo/challenge_graph.yaml",
        "backend/challenge_data/publish_demo/logic_graph.yaml",
        "backend/challenge_data/publish_demo/questions.yaml",
        "backend/challenge_data/publish_demo/publish_manifest.json",
    }
    assert payload["question_package_summary"]["quality_passed"] is True
    assert payload["question_package_summary"]["question_count"] >= 3
    assert all(item["write_mode"] == "create_only" for item in payload["planned_files"])


def test_synthesis_edge_can_route_a_micro_owned_guide_to_its_challenge() -> None:
    markdown = MARKDOWN.replace(
        "| publish_demo.synthesis.boss | 综合拆解 | publish_demo.boss | publish_demo.method |",
        "| publish_demo.synthesis.boss | 综合拆解 | publish_demo.method | publish_demo.method |",
    )
    assert markdown != MARKDOWN

    payload = build_chapter_publish_plan_dry_run(
        markdown,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=_checklist(),
        notes="ready",
    )

    assert payload["publish_plan_grade"] == "ready"
    assert (
        "synthesis_decomposition"
        in payload["question_package_summary"]["question_kinds"]
    )


def test_publish_plan_blocks_when_candidate_quality_is_not_pass() -> None:
    weak_markdown = MARKDOWN.replace("| expression_weakness | publish_demo.method |", "")

    payload = build_chapter_publish_plan_dry_run(
        weak_markdown,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=_checklist(),
        notes="ready",
    )

    assert payload["publish_plan_grade"] == "blocked"
    assert payload["planned_files"] == []
    assert "candidate_quality:warn" in payload["blocking_reasons"]
    assert any(
        issue["code"] == "core_error_mapping_incomplete"
        for issue in payload["blocking_issues"]
    )
    assert payload["formal_publish_allowed"] is False


def test_publish_plan_blocks_when_question_package_has_warnings(monkeypatch) -> None:
    def warn_question_package(candidate: dict) -> dict:
        return {
            "question_package_schema_version": "test_question_package_v1",
            "question_bank": {"chapter_id": candidate["chapter_id"], "questions": []},
            "mastery_criteria": {"schema_version": "test_mastery_v1"},
            "quality_report": {
                "passed": True,
                "grade": "warn",
                "error_count": 0,
                "warning_count": 1,
                "errors": [],
                "warnings": [{"code": "transfer_question_missing", "target": "guide_nodes"}],
                "coverage": {"question_count": 0, "question_kinds": [], "rubric_dimensions": []},
            },
        }

    monkeypatch.setattr(chapter_publish_plan, "build_chapter_training_question_package", warn_question_package)

    payload = build_chapter_publish_plan_dry_run(
        MARKDOWN,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=_checklist(),
        notes="ready",
    )

    assert payload["publish_plan_grade"] == "blocked"
    assert payload["planned_files"] == []
    assert "question_package_quality:warn" in payload["blocking_reasons"]


def test_publish_plan_api_returns_dry_run_only_plan() -> None:
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/authoring/chapter-draft/publish-plan-dry-run",
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
    assert payload["publish_state"] == "publish_plan_preview_only"
    assert payload["publish_plan_grade"] == "ready"
    assert payload["formal_publish_allowed"] is False
