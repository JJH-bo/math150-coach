from __future__ import annotations

import json

from app.classroom.models import ClassroomPackage
from app.classroom.quality_migration import (
    migrate_persistent_classrooms,
    upgrade_legacy_package,
)
from app.classroom.repository import ClassroomRepository
from app.classroom.validation import ClassroomPackageValidator


def legacy_package() -> dict:
    return {
        "schema_version": "classroom_package_v1",
        "package_id": "legacy-fourier",
        "title": "傅里叶级数",
        "courses": [
            {
                "id": "math",
                "title": "高等数学",
                "chapters": [
                    {
                        "id": "fourier",
                        "title": "傅里叶级数",
                        "modules": [
                            {
                                "id": "fourier-map",
                                "title": "傅里叶级数全章地图",
                                "summary": "从系数走到收敛与延拓。",
                                "blocks": [
                                    {
                                        "id": "map-copy",
                                        "kind": "prose",
                                        "data": {
                                            "text": "本章研究周期函数如何分解为不同频率。"
                                        },
                                        "detail_branches": [],
                                    }
                                ],
                                "segments": [],
                            },
                            {
                                "id": "coefficients",
                                "title": "三角级数与傅里叶系数",
                                "summary": "从正交性得到系数。",
                                "blocks": [],
                                "segments": [
                                    {
                                        "id": "orthogonality",
                                        "title": "为什么积分能筛出一个频率",
                                        "blocks": [
                                            {
                                                "id": "orthogonality-copy",
                                                "kind": "prose",
                                                "data": {
                                                    "text": "不同频率在整周期积分后互相抵消。"
                                                },
                                                "detail_branches": [
                                                    {
                                                        "id": "old-detail",
                                                        "title": "为什么会抵消",
                                                        "blocks": [
                                                            {
                                                                "id": "old-detail-copy",
                                                                "kind": "prose",
                                                                "data": {
                                                                    "text": "先看一正一负的面积。"
                                                                },
                                                                "detail_branches": [],
                                                            }
                                                        ],
                                                    }
                                                ],
                                            },
                                            {
                                                "id": "coefficient-formula",
                                                "kind": "math",
                                                "data": {
                                                    "latex": "a_n=\\frac1l\\int_{-l}^{l}f(x)\\cos\\frac{n\\pi x}{l}\\,dx"
                                                },
                                                "detail_branches": [],
                                            },
                                        ],
                                    }
                                ],
                            },
                            {
                                "id": "convergence",
                                "title": "收敛与函数还原",
                                "summary": "判断连续点和跳跃点的级数和。",
                                "blocks": [],
                                "segments": [
                                    {
                                        "id": "dirichlet",
                                        "title": "间断点为什么取左右极限平均",
                                        "blocks": [
                                            {
                                                "id": "limits-comparison",
                                                "kind": "comparison",
                                                "data": {
                                                    "title": "两种位置",
                                                    "items": [
                                                        "连续点：左右极限相等",
                                                        "跳跃点：左右极限不等",
                                                    ],
                                                },
                                                "detail_branches": [],
                                            }
                                        ],
                                    }
                                ],
                            },
                        ],
                        "relations": [
                            {
                                "id": "map-to-coefficients",
                                "kind": "conceptual_dependency",
                                "source_module_id": "fourier-map",
                                "target_module_id": "coefficients",
                            },
                            {
                                "id": "coefficients-to-convergence",
                                "kind": "conceptual_dependency",
                                "source_module_id": "coefficients",
                                "target_module_id": "convergence",
                            },
                        ],
                    }
                ],
            }
        ],
        "model_instances": [],
        "model_bindings": [],
        "assets": [],
    }


def test_legacy_classroom_is_upgraded_into_a_valid_learning_contract() -> None:
    upgraded = upgrade_legacy_package(legacy_package())
    package = ClassroomPackage.model_validate(upgraded)
    report = ClassroomPackageValidator().validate(package)
    chapter = package.courses[0].chapters[0]

    assert report.passed, report.issues
    assert [module.id for module in chapter.modules] == [
        "coefficients",
        "convergence",
    ]
    assert chapter.overview.module_order == ["coefficients", "convergence"]
    assert len(chapter.source_sections) == 2
    assert len(chapter.knowledge_points) == 2
    assert chapter.coverage_audit.unresolved_items == []
    assert all(module.core_question for module in chapter.modules)
    assert all(module.novice_bridge for module in chapter.modules)
    assert all(
        any(block.detail_branches for segment in module.segments for block in segment.blocks)
        for module in chapter.modules
    )
    comparison = chapter.modules[1].segments[0].blocks[0]
    assert all(isinstance(item, dict) for item in comparison.data["items"])


def test_quality_upgrade_is_idempotent() -> None:
    first = upgrade_legacy_package(legacy_package())

    assert upgrade_legacy_package(first) == first


def test_known_fourier_modules_receive_subject_specific_learning_bridges() -> None:
    payload = legacy_package()
    payload["package_id"] = "fourier-series-class"
    chapter = payload["courses"][0]["chapters"][0]
    module = chapter["modules"][1]
    module["id"] = "trigonometric-series"
    module["title"] = "星系一：三角级数与傅里叶系数"
    module["segments"][0]["id"] = "formula-core"
    module["segments"][0]["title"] = "系数公式与展开式"
    module["segments"][0]["blocks"][0]["detail_branches"][0]["id"] = (
        "coeff-why-divide-l"
    )
    chapter["relations"] = []

    upgraded = ClassroomPackage.model_validate(upgrade_legacy_package(payload))
    upgraded_module = upgraded.courses[0].chapters[0].modules[0]

    assert upgraded_module.core_question == (
        "怎样把一个周期函数拆成不同频率的正弦波和余弦波，"
        "并算出每个频率在原函数中占多少？"
    )
    assert upgraded_module.novice_bridge.concrete_anchor == (
        "先把一条复杂周期曲线看成几种简单波形叠加："
        "常数控制整体高度，余弦和正弦控制不同频率的起伏。"
    )
    assert "正交积分" in upgraded_module.novice_bridge.missing_bridge
    segment = upgraded_module.segments[0]
    assert segment.question_answered == (
        "三个积分公式分别在测量什么，为什么整周期积分能只筛出对应频率？"
    )
    assert "正交" in segment.mechanism
    detail = segment.blocks[0].detail_branches[0]
    assert detail.trigger_question == "系数公式为什么除以 l，而不是除以 2l？"
    assert "基函数平方" in detail.learning_obstacle


def test_persistent_legacy_active_release_and_drafts_are_republished(tmp_path) -> None:
    package = legacy_package()
    draft_root = tmp_path / "drafts"
    release_root = (
        tmp_path
        / "packages"
        / package["package_id"]
        / "releases"
    )
    active_root = tmp_path / "active"
    draft_root.mkdir(parents=True)
    release_root.mkdir(parents=True)
    active_root.mkdir(parents=True)
    (draft_root / "legacy-draft.json").write_text(
        json.dumps(
            {
                "draft_id": "legacy-draft",
                "revision": 1,
                "content_hash": "sha256:legacy",
                "package": package,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (release_root / "r-legacy.json").write_text(
        json.dumps(
            {
                "package_id": package["package_id"],
                "version": "r-legacy",
                "content_hash": "sha256:legacy",
                "package": package,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (active_root / f"{package['package_id']}.json").write_text(
        json.dumps(
            {
                "package_id": package["package_id"],
                "active_version": "r-legacy",
                "content_hash": "sha256:legacy",
            }
        ),
        encoding="utf-8",
    )

    result = migrate_persistent_classrooms(tmp_path)
    repository = ClassroomRepository(tmp_path)
    active = repository.get_active_release(package["package_id"])

    assert result["migrated_drafts"] == ["legacy-draft"]
    assert result["republished_packages"] == ["legacy-fourier"]
    assert active.version != "r-legacy"
    assert active.package.courses[0].chapters[0].coverage_audit
    assert repository.get_draft("legacy-draft").package.courses[0].chapters[
        0
    ].overview
