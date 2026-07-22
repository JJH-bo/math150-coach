from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.classroom.hashing import content_hash
from app.classroom.models import ClassroomPackage
from classroom_fixtures import classroom_package_payload


def test_package_uses_semantic_segments_for_the_fixed_learning_route() -> None:
    package = ClassroomPackage.model_validate(classroom_package_payload())

    module = package.courses[0].chapters[0].modules[0]
    assert module.id == "limit-core"
    assert module.blocks == []
    assert len(module.segments) == 3
    detail = module.segments[0].blocks[0].detail_branches[0]
    assert detail.blocks[0].kind == "prose"


def test_chapter_accepts_a_source_to_knowledge_coverage_contract() -> None:
    payload = classroom_package_payload()
    chapter = payload["courses"][0]["chapters"][0]
    chapter["source_sections"] = [
        {
            "id": "source-limit-definition",
            "asset_id": "lecture-limit",
            "filename": "极限讲义.pdf",
            "order": 1,
            "page": "1",
            "heading": "极限的定义",
            "content": "当 x 趋近 a 时，如果 f(x) 任意接近 L，就称 L 为函数的极限。",
            "content_hash": "sha256:source-limit-definition",
        }
    ]
    chapter["knowledge_points"] = [
        {
            "id": "kp-limit-neighborhood",
            "statement": "极限描述自变量趋近时函数值的邻域行为。",
            "kind": "concept",
            "importance": "core",
            "source_section_ids": ["source-limit-definition"],
            "source_quotes": [
                {
                    "source_section_id": "source-limit-definition",
                    "quote": "当 x 趋近 a 时，如果 f(x) 任意接近 L",
                }
            ],
        }
    ]
    chapter["coverage_map"] = [
        {
            "knowledge_point_id": "kp-limit-neighborhood",
            "module_id": "limit-core",
            "baseline_content_ids": ["limit-intro"],
            "detail_content_ids": ["limit-intro-detail-prose"],
            "model_instance_ids": [],
        }
    ]
    chapter["coverage_audit"] = {
        "source_section_ids": ["source-limit-definition"],
        "knowledge_point_ids": ["kp-limit-neighborhood"],
        "unresolved_items": [],
        "auditor_summary": "来源区段、知识点和课堂内容已经逐项核对。",
    }
    chapter["modules"][0]["knowledge_point_ids"] = ["kp-limit-neighborhood"]
    chapter["modules"][0]["segments"][0]["blocks"][0]["knowledge_point_ids"] = [
        "kp-limit-neighborhood"
    ]

    package = ClassroomPackage.model_validate(payload)

    contract = package.courses[0].chapters[0]
    assert contract.source_sections[0].content.startswith("当 x 趋近")
    assert contract.knowledge_points[0].importance == "core"
    assert contract.coverage_map[0].baseline_content_ids == ["limit-intro"]
    assert contract.coverage_audit.unresolved_items == []


def test_core_modules_and_segments_express_the_novice_learning_contract() -> None:
    payload = classroom_package_payload()
    chapter = payload["courses"][0]["chapters"][0]
    chapter["overview"] = {
        "essential_question": "函数在某一点附近不断接近时，怎样描述稳定的目标值？",
        "learning_route_summary": "先区分点值与邻域行为，再建立极限记号，最后用可去间断点落地。",
        "module_order": ["limit-core"],
    }
    module = chapter["modules"][0]
    module["core_question"] = "函数在点上未定义时，为什么仍然可以有极限？"
    module["chapter_role"] = "建立极限的邻域观点，为连续、导数和积分提供共同语言。"
    module["why_indispensable"] = "没有邻域观点，后续所有极限运算都会退化成容易失效的代入技巧。"
    module["depends_on_module_ids"] = []
    module["novice_bridge"] = {
        "known_before": ["会读取函数值", "理解自变量可以不断接近某个数"],
        "missing_bridge": "需要把关注点从 x=a 的单个点转向 a 周围的一整段邻域。",
        "concrete_anchor": "沿着 y=x+1 的图像从左右两侧走向 x=1。",
        "bridge_strategy": "先观察动态图，再把稳定接近的过程压缩成极限记号。",
    }
    segment = module["segments"][0]
    segment["question_answered"] = "可去间断点为什么不妨碍极限存在？"
    segment["bridge_from_previous"] = "已经把极限看成邻域行为，现在用一个点上有洞的函数检验这个观点。"
    segment["mechanism"] = "约去只在 x=1 处为零的公共因子后，去心邻域内的函数与 x+1 完全相同。"
    segment["entry_assumptions"] = ["理解趋近不等于取到", "会做因式分解"]
    segment["exit_understanding"] = "能够解释点值与极限为什么可以不同。"
    segment["knowledge_point_ids"] = ["kp-removable-example"]

    package = ClassroomPackage.model_validate(payload)

    result = package.courses[0].chapters[0]
    assert result.overview.module_order == ["limit-core"]
    assert result.modules[0].core_question.endswith("？")
    assert result.modules[0].novice_bridge.concrete_anchor.startswith("沿着")
    assert result.modules[0].segments[0].mechanism.startswith("约去")


def test_static_detail_expansion_records_the_obstacle_bridge_and_return() -> None:
    payload = classroom_package_payload()
    branch = payload["courses"][0]["chapters"][0]["modules"][0]["segments"][0][
        "blocks"
    ][0]["detail_branches"][0]
    branch.update(
        {
            "trigger_question": "为什么函数在 x=a 处没有值，极限却仍然存在？",
            "learning_obstacle": "把极限误认为把 a 直接代入函数后得到的点值。",
            "representation": "counterexample",
            "focus_relation": "点值属于单个位置，极限属于去心邻域中的共同趋势。",
            "bridge_steps": [
                "先遮住图像上 x=a 的单个点，只观察两侧曲线。",
                "再任意改变这个点的取值，比较两侧趋近趋势是否变化。",
            ],
            "return_connection": "回到极限记号时，x→a 表示接近但不要求 x=a。",
        }
    )

    package = ClassroomPackage.model_validate(payload)

    result = (
        package.courses[0]
        .chapters[0]
        .modules[0]
        .segments[0]
        .blocks[0]
        .detail_branches[0]
    )
    assert result.representation == "counterexample"
    assert len(result.bridge_steps) == 2


def test_one_block_detail_expansion_is_rejected_as_too_shallow() -> None:
    payload = classroom_package_payload()
    branch = payload["courses"][0]["chapters"][0]["modules"][0]["segments"][0][
        "blocks"
    ][0]["detail_branches"][0]
    branch["blocks"] = branch["blocks"][:1]

    with pytest.raises(ValidationError, match="at least 2 items"):
        ClassroomPackage.model_validate(payload)


def test_module_without_semantic_learning_segments_is_rejected() -> None:
    payload = classroom_package_payload()
    payload["courses"][0]["chapters"][0]["modules"][0]["segments"] = []

    with pytest.raises(ValidationError, match="at least 1 item"):
        ClassroomPackage.model_validate(payload)


def test_module_can_use_only_segments_without_top_level_blocks() -> None:
    payload = classroom_package_payload()
    payload["courses"][0]["chapters"][0]["modules"][0]["blocks"] = []

    module = ClassroomPackage.model_validate(payload).courses[0].chapters[0].modules[0]

    assert module.blocks == []
    assert module.segments


def test_empty_module_is_rejected() -> None:
    payload = classroom_package_payload()
    module = payload["courses"][0]["chapters"][0]["modules"][0]
    module["blocks"] = []
    module["segments"] = []

    with pytest.raises(ValidationError, match="at least 1 item"):
        ClassroomPackage.model_validate(payload)


def test_unknown_content_block_fields_are_rejected() -> None:
    payload = classroom_package_payload()
    payload["courses"][0]["chapters"][0]["modules"][0]["segments"][0][
        "blocks"
    ][0]["score"] = 1

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ClassroomPackage.model_validate(payload)


def test_content_hash_is_stable_across_mapping_order() -> None:
    payload = classroom_package_payload()
    reordered = {key: payload[key] for key in reversed(payload)}

    assert content_hash(payload) == content_hash(reordered)
    assert content_hash(payload).startswith("sha256:")


def test_checked_in_seed_matches_the_valid_package_contract() -> None:
    seed_path = (
        Path(__file__).resolve().parents[1]
        / "classroom_data"
        / "seed"
        / "calculus-foundations.json"
    )
    seed = json.loads(seed_path.read_text(encoding="utf-8"))

    package = ClassroomPackage.model_validate(seed)

    assert package.package_id == "calculus-foundations"
    assert package.courses[0].chapters[0].modules[0].id == "limit-core"
