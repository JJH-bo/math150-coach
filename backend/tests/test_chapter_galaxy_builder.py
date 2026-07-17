from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.chapter_galaxy_builder import build_chapter_asset, write_javascript_module


def _training_block(node_id: str, title: str) -> str:
    return f"""
### {node_id}
training_goal: 训练{title}
entry_trigger: 看到{title}题眼
mastery_criteria: 能解释{title}

#### CoreQuestion
question_id: {node_id}.core
question_kind: concept_judgement
difficulty: basic
stem: |
  {title}的核心题干。
  第二行题干。
expected_answer: |
  {title}的标准答案。
solution_outline:
  1. 写出第一步。

#### TransferVariant
question_id: {node_id}.variant
variant_relation: 改变结构而不是只改数字
stem: |
  {title}的迁移题。
expected_answer: |
  {title}的迁移答案。
"""


def _chapter_markdown() -> str:
    nodes = [
        ("demo.system_01.concept", "demo.system_01", "concept", "概念入口"),
        ("demo.system_01.trigger", "demo.system_01", "trigger", "题眼识别"),
        ("demo.system_01.method", "demo.system_01", "method", "方法执行"),
        ("demo.system_02.concept", "demo.system_02", "concept", "对象理解"),
        ("demo.system_02.transform", "demo.system_02", "transformation", "结构变换"),
        ("demo.system_02.expression", "demo.system_02", "expression", "规范表达"),
    ]
    micro_rows = "\n".join(
        f"| {node_id} | {macro_id} | {node_type} | {title} | {title}的可观察能力。 |"
        for node_id, macro_id, node_type, title in nodes
    )
    training = "\n".join(_training_block(node_id, title) for node_id, _, _, title in nodes)
    return f"""# 演示章节
chapter_id: demo
title: 演示章节
generation_status: final

## GalaxyPlan
| system_id | macro_node_id | title | core_question | learning_order | visual_priority | recommended_depth | preferred_sector | planet_count | prerequisite_system_ids | boss_contribution | spacing_reason | source_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| demo.system_01 | demo.system_01 | 第一星系 | 第一核心问题 | 1 | high | far | upper_left | 3 | [] | 贡献一 | 分开显示 | 材料A第1页 |
| demo.system_02 | demo.system_02 | 第二星系 | 第二核心问题 | 2 | medium | near | lower_left | 3 | demo.system_01 | 贡献二 | 分开显示 | 材料A第2页 |

## GalaxyBoss
| id | title | covers_system_ids | integrated_learning_goal | entry_requirements | challenge_brief | success_evidence | failure_routing | source_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| demo.boss | 演示Boss | demo.system_01,demo.system_02 | 综合调用 | 两个星系通过 | 完成综合题 | 完整过程 | 失败回节点 | 材料A全章 |

## MacroNodes
| id | title | knowledge_node_id |
| --- | --- | --- |
| demo.system_01 | 第一星系 | first |
| demo.system_02 | 第二星系 | second |

## MicroNodes
| id | macro_node_id | type | title | description |
| --- | --- | --- | --- | --- |
{micro_rows}

## Edges
| id | edge_type | source_id | target_id | reason |
| --- | --- | --- | --- | --- |
| demo.edge.01 | supports | demo.system_01.concept | demo.system_01.trigger | 训练顺序 |
| demo.edge.02 | supports | demo.system_01.trigger | demo.system_01.method | 训练顺序 |
| demo.edge.03 | supports | demo.system_02.concept | demo.system_02.transform | 训练顺序 |
| demo.edge.04 | supports | demo.system_02.transform | demo.system_02.expression | 训练顺序 |

## TrainingAssets
{training}

## BossTrainingAsset
boss_id: demo.boss
question_kind: boss_acceptance
title: 演示Boss综合题
stem: |
  完成两个阶段的综合任务。
expected_answer: |
  给出完整的综合答案。
"""


def test_build_chapter_asset_preserves_system_order_and_training_content() -> None:
    asset = build_chapter_asset(_chapter_markdown())

    assert asset["chapterId"] == "demo"
    assert [system["id"] for system in asset["systems"]] == ["demo.system_01", "demo.system_02"]
    assert [len(system["planets"]) for system in asset["systems"]] == [3, 3]
    first = asset["systems"][0]["planets"][0]
    assert first["id"] == "demo.system_01.concept"
    assert first["training"]["stem"] == "概念入口的核心题干。\n第二行题干。"
    assert first["training"]["expectedAnswer"] == "概念入口的标准答案。"
    assert first["training"]["variant"]["stem"] == "概念入口的迁移题。"
    assert asset["boss"]["id"] == "demo.boss"
    assert asset["boss"]["training"]["stem"] == "完成两个阶段的综合任务。"
    assert asset["metrics"] == {"systemCount": 2, "planetCount": 6, "bossCount": 1}
    assert asset["systems"][0]["links"] == [
        {
            "sourceId": "demo.system_01.concept",
            "targetId": "demo.system_01.trigger",
            "edgeType": "supports",
        },
        {
            "sourceId": "demo.system_01.trigger",
            "targetId": "demo.system_01.method",
            "edgeType": "supports",
        },
    ]


def test_build_chapter_asset_rejects_planet_count_mismatch() -> None:
    markdown = _chapter_markdown().replace(
        "| demo.system_01 | demo.system_01 | 第一星系 | 第一核心问题 | 1 | high | far | upper_left | 3 |",
        "| demo.system_01 | demo.system_01 | 第一星系 | 第一核心问题 | 1 | high | far | upper_left | 4 |",
    )

    with pytest.raises(ValueError, match="planet_count"):
        build_chapter_asset(markdown)


def test_write_javascript_module_is_deterministic(tmp_path: Path) -> None:
    asset = build_chapter_asset(_chapter_markdown())
    output = tmp_path / "chapter-data.mjs"

    write_javascript_module(asset, output)

    source = output.read_text(encoding="utf-8")
    assert source.startswith("export default ")
    payload = json.loads(source.removeprefix("export default ").removesuffix(";\n"))
    assert payload == asset
