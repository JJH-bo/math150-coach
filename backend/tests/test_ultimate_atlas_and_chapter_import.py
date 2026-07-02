from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.challenge.chapter_draft_importer import validate_chapter_markdown
from app.main import create_app
from app.training.session_log import ensure_no_trusted_fields


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


def test_chapter_draft_validate_api_never_publishes_formal_chapter() -> None:
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/authoring/chapter-draft/validate",
        json={"markdown": VALID_CHAPTER_MARKDOWN},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["publish_state"] == "draft_only"
    assert payload["report"]["passed"] is True
