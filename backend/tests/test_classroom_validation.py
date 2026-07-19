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


def test_duplicate_content_ids_report_exact_path() -> None:
    payload = classroom_package_payload()
    module = payload["courses"][0]["chapters"][0]["modules"][0]
    module["blocks"][1]["id"] = module["blocks"][0]["id"]

    report = validate(payload)

    assert report.passed is False
    assert report.issues[0].code == "duplicate_object_id"
    assert report.issues[0].path.endswith(".blocks[1].id")


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
    block = payload["courses"][0]["chapters"][0]["modules"][0]["blocks"][0]
    block["data"]["mastery_state"] = {"score": 80}

    report = validate(payload)

    assert report.passed is False
    assert report.issues[0].code == "learner_analysis_field_forbidden"
    assert "mastery_state" in report.issues[0].path


def test_rendered_block_shapes_are_validated_before_publish() -> None:
    payload = classroom_package_payload()
    module = payload["courses"][0]["chapters"][0]["modules"][0]
    module["blocks"].extend(
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
    module["blocks"].extend(
        [
            {
                "id": "comparison-items",
                "kind": "comparison",
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

    report = validate(payload)

    assert report.passed is True
