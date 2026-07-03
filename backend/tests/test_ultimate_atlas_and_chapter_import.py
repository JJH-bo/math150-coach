from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.challenge.chapter_draft_importer import validate_chapter_markdown
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


VALID_CHAPTER_MARKDOWN = """# 章节导入验收样例
chapter_id: import_demo
title: 章节导入验收样例

## MacroNodes
| id | title | knowledge_node_id |
| --- | --- | --- |
| import_demo.macro | 导入大节点 | import_demo.macro |

## MicroNodes
| id | macro_node_id | type | title | description |
| --- | --- | --- | --- | --- |
| import_demo.macro.concept | import_demo.macro | concept | 概念判断 | 先判断结构 |
| import_demo.macro.method | import_demo.macro | method | 方法选择 | 再选择方法 |

## MacroChallenges
| id | macro_node_id | title | covers_micro_nodes |
| --- | --- | --- | --- |
| import_demo.macro.macro_challenge | import_demo.macro | 综合验收 | import_demo.macro.concept, import_demo.macro.method |

## HiddenAbilities
| id | owner_node_id | title | dimensions | why_exists | evidence_sources | failure_modes | repair_target_node_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| import_demo.hidden.concept_reason | import_demo.macro.concept | 概念依据 | concept | 防止只背关键词 | rubric,self_explanation | 只有关键词 | import_demo.macro.concept |

## CompareGuards
| id | title | node_ids | contrast |
| --- | --- | --- | --- |
| import_demo.compare.concept_method | 概念与方法边界 | import_demo.macro.concept, import_demo.macro.method | 一个判断结构，一个执行方法 |

## TransferNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| import_demo.transfer.variant | 变式迁移 | import_demo.macro.method | import_demo.macro.method | 防止只会原题 |

## SynthesisNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| import_demo.synthesis.boss | Boss 拆解 | import_demo.macro.macro_challenge | import_demo.macro.method | 综合题先拆链路 |

## Edges
| id | edge_type | source_id | target_id | reason |
| --- | --- | --- | --- | --- |
| e1 | supports | import_demo.hidden.concept_reason | import_demo.macro.concept | 原子能力支撑概念节点 |
| e2 | requires | import_demo.macro.concept | import_demo.macro.method | 先会判断再选方法 |
| e3 | boss_checks | import_demo.synthesis.boss | import_demo.macro.macro_challenge | Boss 检查综合拆解 |
| e4 | transfers_to | import_demo.transfer.variant | import_demo.macro.method | 迁移回方法节点 |

| e5 | contrasts_with | import_demo.compare.concept_method | import_demo.macro.method | Compare guard links concept and method |

## ErrorRepairMap
| root_cause | repair_target_node_id |
| --- | --- |
| concept_gap | import_demo.macro.concept |
| method_error | import_demo.macro.method |
"""


def test_challenge_atlas_is_lightweight_and_lazy() -> None:
    client = TestClient(create_app("mixed"))

    response = client.get("/api/challenge/v1/atlas")

    assert response.status_code == 200
    payload = response.json()
    assert payload["atlas_version"] == "course_atlas_v1"
    assert payload["render_policy"]["detail_loading"] == "lazy"
    assert payload["regions"]
    text = json.dumps(payload, ensure_ascii=False)
    assert "logic_overlay" not in text
    assert "current_question" not in text
    assert "micro_nodes" not in payload["regions"][0]
    ensure_no_trusted_fields(payload)


def test_structured_markdown_chapter_import_returns_draft_preview() -> None:
    payload = validate_chapter_markdown(VALID_CHAPTER_MARKDOWN)

    assert payload["publish_state"] == "draft_only"
    assert payload["report"]["passed"] is True
    assert payload["preview"]["counts"]["macro_nodes"] == 1
    assert payload["preview"]["counts"]["micro_nodes"] == 2
    assert payload["draft"]["challenge_graph_draft"]["chapter_id"] == "import_demo"
    assert payload["draft"]["logic_graph_draft"]["abilities"]


def test_structured_markdown_chapter_import_returns_authoring_readiness() -> None:
    payload = validate_chapter_markdown(VALID_CHAPTER_MARKDOWN)

    assert payload["workflow_stage"] == "draft_preview"
    readiness = payload["readiness"]
    assert readiness["status"] == "review_ready"
    assert readiness["publish_allowed"] is False
    assert readiness["blocking_error_count"] == 0
    assert readiness["warning_count"] == 0
    assert readiness["next_action"] == "human_review"
    checks = {check["code"]: check for check in readiness["checks"]}
    assert checks["graph_valid"]["state"] == "pass"
    assert checks["visible_budget"]["state"] == "pass"
    assert checks["repair_targets"]["state"] == "pass"
    assert checks["human_review_required"]["state"] == "locked"
    assert checks["formal_publish_locked"]["state"] == "locked"


def test_chapter_import_rejects_missing_hidden_evidence_and_repair_target() -> None:
    markdown = VALID_CHAPTER_MARKDOWN.replace("rubric,self_explanation", "").replace(
        "只有关键词 | import_demo.macro.concept |",
        "只有关键词 | unknown.node |",
    )

    payload = validate_chapter_markdown(markdown)

    assert payload["report"]["passed"] is False
    messages = " ".join(item["message"] for item in payload["report"]["errors"])
    assert "HiddenAbility 必须写 evidence_sources" in messages
    assert "repair_target_node_id" in messages


def test_structured_markdown_chapter_import_blocks_readiness_when_validation_fails() -> None:
    markdown = VALID_CHAPTER_MARKDOWN.replace(
        "| method_error | import_demo.macro.method |",
        "| method_error | unknown.node |",
    )

    payload = validate_chapter_markdown(markdown)

    assert payload["workflow_stage"] == "draft_preview"
    readiness = payload["readiness"]
    assert readiness["status"] == "blocked"
    assert readiness["publish_allowed"] is False
    assert readiness["blocking_error_count"] > 0
    assert readiness["next_action"] == "fix_validation_errors"
    checks = {check["code"]: check for check in readiness["checks"]}
    assert checks["graph_valid"]["state"] == "fail"
    assert checks["formal_publish_locked"]["state"] == "locked"


def test_markdown_chapter_import_returns_structured_error_issues() -> None:
    markdown = VALID_CHAPTER_MARKDOWN.replace(
        "| method_error | import_demo.macro.method |",
        "| method_error | import_demo.unknown_method |",
    )

    payload = validate_chapter_markdown(markdown)

    issues_by_code = {issue["code"]: issue for issue in payload["report"]["errors"]}
    issue = issues_by_code["invalid_repair_target"]
    assert issue["target"] == "method_error"
    assert issue["severity"] == "error"
    assert issue["target_kind"] == "error_repair_map"
    assert issue["message"]
    assert issue["suggested_fix"]


def test_markdown_chapter_import_returns_structured_warning_issues() -> None:
    markdown = VALID_CHAPTER_MARKDOWN.replace(
        "| e5 | contrasts_with | import_demo.compare.concept_method | import_demo.macro.method | Compare guard links concept and method |",
        "",
    )

    payload = validate_chapter_markdown(markdown)

    issue = payload["report"]["warnings"][0]
    assert issue["severity"] == "warning"
    assert issue["code"] == "orphan_logic_node"
    assert issue["target_kind"] == "logic_edges"
    assert issue["target"] == "logic_edges"
    assert issue["suggested_fix"]


def test_markdown_chapter_import_marks_visible_budget_warning_as_macro_target() -> None:
    method_row = next(
        line for line in VALID_CHAPTER_MARKDOWN.splitlines() if line.startswith("| import_demo.macro.method |")
    )
    extra_micro_rows = "\n".join(
        f"| import_demo.macro.extra_{index} | import_demo.macro | concept | Extra {index} | Extra node |"
        for index in range(1, 8)
    )
    markdown = VALID_CHAPTER_MARKDOWN.replace(method_row, f"{method_row}\n{extra_micro_rows}")

    payload = validate_chapter_markdown(markdown)

    issues_by_code = {issue["code"]: issue for issue in payload["report"]["warnings"]}
    issue = issues_by_code["visible_node_budget_warning"]
    assert issue["target"] == "import_demo.macro"
    assert issue["severity"] == "warning"
    assert issue["target_kind"] == "macro_nodes"
    assert issue["suggested_fix"]


def test_chapter_draft_validate_api_never_publishes_formal_chapter() -> None:
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/authoring/chapter-draft/validate",
        json={"markdown": VALID_CHAPTER_MARKDOWN},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["publish_state"] == "draft_only"
    assert payload["workflow_stage"] == "draft_preview"
    assert payload["readiness"]["publish_allowed"] is False
    assert payload["report"]["passed"] is True


def test_chapter_draft_validation_returns_human_review_packet() -> None:
    payload = validate_chapter_markdown(VALID_CHAPTER_MARKDOWN)

    review = payload["human_review"]
    assert review["required"] is True
    assert review["status"] == "pending"
    assert review["candidate_build_allowed"] is False
    assert review["formal_publish_allowed"] is False
    assert {item["code"] for item in review["required_checklist"]} == REQUIRED_REVIEW_CHECKS


def test_chapter_human_review_blocks_candidate_when_validation_has_errors() -> None:
    from app.challenge.chapter_draft_importer import record_chapter_human_review

    markdown = VALID_CHAPTER_MARKDOWN.replace(
        "| method_error | import_demo.macro.method |",
        "| method_error | unknown.node |",
    )

    payload = record_chapter_human_review(
        markdown,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=_complete_review_checklist(),
        notes="looks ready",
    )

    assert payload["workflow_stage"] == "human_review"
    assert payload["candidate_build_allowed"] is False
    assert payload["formal_publish_allowed"] is False
    assert payload["review_record"]["status"] == "blocked_by_validation"
    assert payload["review_record"]["blocking_issue_count"] > 0


def test_chapter_human_review_allows_candidate_after_complete_review_only() -> None:
    from app.challenge.chapter_draft_importer import record_chapter_human_review

    incomplete = _complete_review_checklist()
    incomplete["semantic_edges_checked"] = False

    incomplete_payload = record_chapter_human_review(
        VALID_CHAPTER_MARKDOWN,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=incomplete,
        notes="missing edge review",
    )
    assert incomplete_payload["candidate_build_allowed"] is False
    assert incomplete_payload["review_record"]["status"] == "review_incomplete"

    approved_payload = record_chapter_human_review(
        VALID_CHAPTER_MARKDOWN,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=_complete_review_checklist(),
        notes="ready for candidate dry-run",
    )
    assert approved_payload["candidate_build_allowed"] is True
    assert approved_payload["formal_publish_allowed"] is False
    assert approved_payload["review_record"]["status"] == "approved_for_candidate"
    assert approved_payload["review_record"]["decision"] == "approve_for_candidate"


def test_chapter_human_review_api_records_review_without_publishing() -> None:
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/authoring/chapter-draft/human-review",
        json={
            "markdown": VALID_CHAPTER_MARKDOWN,
            "reviewer": "reviewer-a",
            "decision": "approve_for_candidate",
            "checklist": _complete_review_checklist(),
            "notes": "ready for candidate dry-run",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "chapter_draft_human_review"
    assert payload["workflow_stage"] == "human_review"
    assert payload["publish_state"] == "draft_only"
    assert payload["candidate_build_allowed"] is True
    assert payload["formal_publish_allowed"] is False
    assert payload["review_record"]["reviewer"] == "reviewer-a"


def _complete_review_checklist() -> dict[str, bool]:
    return {code: True for code in REQUIRED_REVIEW_CHECKS}
