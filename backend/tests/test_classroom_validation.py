from __future__ import annotations

from app.classroom.models import ClassroomPackage
from app.classroom.validation import ClassroomPackageValidator
from classroom_fixtures import classroom_package_payload


def validate(payload: dict) -> object:
    package = ClassroomPackage.model_validate(payload)
    return ClassroomPackageValidator().validate(package)


def test_valid_package_passes_cross_object_validation() -> None:
    report = validate(classroom_package_payload())

    assert report.passed is True
    assert report.issues == []


def test_chapter_without_source_coverage_evidence_is_rejected() -> None:
    payload = classroom_package_payload()
    chapter = payload["courses"][0]["chapters"][0]
    chapter["source_sections"] = []
    chapter["knowledge_points"] = []
    chapter["coverage_map"] = []
    chapter["coverage_audit"] = None

    report = validate(payload)

    assert {
        "chapter_source_sections_required",
        "chapter_knowledge_points_required",
        "chapter_coverage_map_required",
        "chapter_coverage_audit_required",
    } <= {issue.code for issue in report.issues}


def test_every_source_section_and_knowledge_point_must_be_covered() -> None:
    payload = classroom_package_payload()
    chapter = payload["courses"][0]["chapters"][0]
    chapter["source_sections"].append(
        {
            "id": "orphan-source",
            "asset_id": "lecture-limit",
            "order": 2,
            "heading": "未建立知识点的来源",
            "content": "这一段没有被任何知识点引用。",
            "content_hash": "sha256:orphan-source",
        }
    )
    chapter["coverage_map"] = chapter["coverage_map"][:-1]

    report = validate(payload)

    assert {
        "source_section_unmapped",
        "knowledge_point_uncovered",
    } <= {issue.code for issue in report.issues}


def test_source_quotes_and_coverage_targets_are_verified() -> None:
    payload = classroom_package_payload()
    chapter = payload["courses"][0]["chapters"][0]
    chapter["knowledge_points"][0]["source_quotes"][0]["quote"] = "原文中不存在"
    chapter["coverage_map"][0]["baseline_content_ids"] = ["missing-block"]

    report = validate(payload)

    assert {
        "source_quote_not_found",
        "unknown_coverage_content",
    } <= {issue.code for issue in report.issues}


def test_coverage_audit_must_be_complete_and_resolved() -> None:
    payload = classroom_package_payload()
    audit = payload["courses"][0]["chapters"][0]["coverage_audit"]
    audit["knowledge_point_ids"] = audit["knowledge_point_ids"][:-1]
    audit["unresolved_items"] = ["尚未核对例题边界"]

    report = validate(payload)

    assert {
        "coverage_audit_incomplete",
        "coverage_audit_unresolved",
    } <= {issue.code for issue in report.issues}


def test_every_baseline_content_block_declares_taught_knowledge_points() -> None:
    payload = classroom_package_payload()
    block = payload["courses"][0]["chapters"][0]["modules"][0]["segments"][0][
        "blocks"
    ][0]
    block["knowledge_point_ids"] = []

    report = validate(payload)

    assert "content_knowledge_points_required" in {
        issue.code for issue in report.issues
    }


def test_every_declared_block_knowledge_point_must_be_reverse_mapped() -> None:
    payload = classroom_package_payload()
    block = payload["courses"][0]["chapters"][0]["modules"][0]["segments"][0][
        "blocks"
    ][0]
    block["knowledge_point_ids"].append("kp-limit-definition")

    report = validate(payload)

    assert "content_missing_from_coverage" in {
        issue.code for issue in report.issues
    }


def test_chapter_overview_is_required_and_must_order_every_module() -> None:
    payload = classroom_package_payload()
    payload["courses"][0]["chapters"][0]["overview"] = None

    report = validate(payload)

    assert "chapter_overview_required" in {
        issue.code for issue in report.issues
    }


def test_overview_cannot_be_disguised_as_a_core_module() -> None:
    payload = classroom_package_payload()
    module = payload["courses"][0]["chapters"][0]["modules"][0]
    module["title"] = "极限全章地图"
    module["core_question"] = "这一章有哪些内容以及学习顺序是什么？"

    report = validate(payload)

    assert "overview_module_forbidden" in {
        issue.code for issue in report.issues
    }


def test_module_dependencies_must_exist_and_be_acyclic() -> None:
    payload = classroom_package_payload()
    chapter = payload["courses"][0]["chapters"][0]
    first = chapter["modules"][0]
    second = {
        **first,
        "id": "limit-followup",
        "title": "极限记号如何表达邻域机制",
        "core_question": "极限记号怎样压缩邻域中的稳定接近过程？",
        "depends_on_module_ids": ["limit-core"],
    }
    first["depends_on_module_ids"] = ["limit-followup", "missing-module"]
    chapter["modules"].append(second)
    chapter["overview"]["module_order"] = ["limit-core", "limit-followup"]

    report = validate(payload)

    assert {
        "unknown_module_dependency",
        "module_dependency_cycle",
    } <= {issue.code for issue in report.issues}


def test_core_module_must_own_core_knowledge_and_match_coverage() -> None:
    payload = classroom_package_payload()
    module = payload["courses"][0]["chapters"][0]["modules"][0]
    module["knowledge_point_ids"] = ["kp-removable-example"]

    report = validate(payload)

    assert {
        "core_module_without_core_knowledge",
        "module_knowledge_responsibility_mismatch",
    } <= {issue.code for issue in report.issues}


def test_learning_segment_requires_substantive_teaching_content() -> None:
    payload = classroom_package_payload()
    segment = payload["courses"][0]["chapters"][0]["modules"][0]["segments"][0]
    segment["blocks"] = [
        {
            "id": "empty-heading-step",
            "kind": "heading",
            "knowledge_point_ids": ["kp-removable-example"],
            "data": {"text": "可去间断点"},
        }
    ]
    coverage = payload["courses"][0]["chapters"][0]["coverage_map"][2]
    coverage["baseline_content_ids"] = ["empty-heading-step"]

    report = validate(payload)

    assert "learning_segment_not_substantive" in {
        issue.code for issue in report.issues
    }


def test_every_core_module_publishes_a_real_detailed_expansion() -> None:
    payload = classroom_package_payload()
    module = payload["courses"][0]["chapters"][0]["modules"][0]
    for segment in module["segments"]:
        for block in segment["blocks"]:
            block["detail_branches"] = []
    payload["courses"][0]["chapters"][0]["coverage_map"][0][
        "detail_content_ids"
    ] = []

    report = validate(payload)

    assert "core_module_detail_expansion_required" in {
        issue.code for issue in report.issues
    }


def test_duplicate_content_ids_report_exact_path() -> None:
    payload = classroom_package_payload()
    module = payload["courses"][0]["chapters"][0]["modules"][0]
    module["segments"][1]["blocks"][0]["id"] = module["segments"][0][
        "blocks"
    ][0]["id"]

    report = validate(payload)

    assert report.passed is False
    issue = next(
        item for item in report.issues if item.code == "duplicate_object_id"
    )
    assert issue.path.endswith(".segments[1].blocks[0].id")


def test_unknown_relation_endpoint_is_rejected() -> None:
    payload = classroom_package_payload()
    chapter = payload["courses"][0]["chapters"][0]
    chapter["relations"] = [
        {
            "id": "relation-missing",
            "kind": "contrast",
            "source_module_id": "limit-core",
            "target_module_id": "missing-module",
        }
    ]

    report = validate(payload)

    assert {issue.code for issue in report.issues} == {"unknown_relation_target"}


def test_learner_analysis_keys_are_rejected_inside_flexible_data() -> None:
    payload = classroom_package_payload()
    block = payload["courses"][0]["chapters"][0]["modules"][0]["segments"][0][
        "blocks"
    ][0]
    block["data"]["mastery_state"] = {"score": 80}

    report = validate(payload)

    assert report.passed is False
    assert report.issues[0].code == "learner_analysis_field_forbidden"
    assert "mastery_state" in report.issues[0].path


def test_rendered_block_shapes_are_validated_before_publish() -> None:
    payload = classroom_package_payload()
    module = payload["courses"][0]["chapters"][0]["modules"][0]
    module["segments"][0]["blocks"].extend(
        [
            {
                "id": "empty-comparison",
                "kind": "comparison",
                "data": {"items": []},
            },
            {
                "id": "empty-formula",
                "kind": "formula_explanation",
                "data": {"title": "只有标题"},
            },
        ]
    )

    report = validate(payload)

    assert report.passed is False
    assert {issue.code for issue in report.issues} >= {
        "comparison_content_required",
        "formula_content_required",
    }


def test_gpt_shaped_comparison_and_formulae_are_publishable() -> None:
    payload = classroom_package_payload()
    module = payload["courses"][0]["chapters"][0]["modules"][0]
    module["segments"][0]["blocks"].extend(
        [
                {
                    "id": "comparison-items",
                    "kind": "comparison",
                    "knowledge_point_ids": ["kp-limit-neighborhood"],
                    "data": {
                    "items": [
                        {"title": "奇函数", "body": "正弦级数"},
                        {"title": "偶函数", "body": "余弦级数"},
                    ]
                },
            },
                {
                    "id": "formulae-list",
                    "kind": "formula_explanation",
                    "knowledge_point_ids": ["kp-limit-definition"],
                    "data": {
                    "title": "半区间展开",
                    "formulae": [
                        {
                            "latex": r"b_n=\frac{2}{l}\int_0^l f(x)\sin\frac{n\pi x}{l}\,dx",
                            "explanation": "奇延拓对应正弦级数。",
                        }
                    ],
                },
            },
        ]
    )
    chapter = payload["courses"][0]["chapters"][0]
    chapter["coverage_map"][0]["baseline_content_ids"].append(
        "comparison-items"
    )
    chapter["coverage_map"][1]["baseline_content_ids"].append(
        "formulae-list"
    )

    report = validate(payload)

    assert report.passed is True


def test_blank_comparison_cards_and_unexplained_formulae_are_rejected() -> None:
    payload = classroom_package_payload()
    segment = payload["courses"][0]["chapters"][0]["modules"][0]["segments"][0]
    segment["blocks"].extend(
        [
            {
                "id": "blank-card-comparison",
                "kind": "comparison",
                "knowledge_point_ids": ["kp-limit-neighborhood"],
                "data": {"items": [{}, {}]},
            },
            {
                "id": "unexplained-formula",
                "kind": "formula_explanation",
                "knowledge_point_ids": ["kp-limit-neighborhood"],
                "data": {
                    "latex": r"\lim_{x\to a}f(x)=L",
                    "explanation": "",
                },
            },
        ]
    )
    report = validate(payload)

    assert {
        "comparison_item_content_required",
        "formula_explanation_required",
    } <= {issue.code for issue in report.issues}
