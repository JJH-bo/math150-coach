from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

from app.catalog.repository import CatalogValidationError
from app.catalog.validator import CatalogValidator
from app.catalog.yaml_repository import YamlQuestionCatalogRepository
from app.main import create_app


GOOD_ANSWER = "This is separable; separate variables; dy/y = 2x dx; integrate; ln|y|=x^2+C."


def test_validator_default_catalog_validates() -> None:
    YamlQuestionCatalogRepository().validate_catalog()


def test_validator_rejects_duplicate_question_id(tmp_path) -> None:
    record = base_record("dup-qid-001")
    write_catalog(tmp_path, [record, deepcopy(record)])

    assert_catalog_error(tmp_path, "catalog_identity_error", "duplicate question_id")


def test_validator_rejects_manifest_presentation_question_id_mismatch(tmp_path) -> None:
    record = base_record("mismatch-001")
    record["presentation"]["question_id"] = "mismatch-002"
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_validation_error", "presentation.question_id")


def test_validator_rejects_manifest_presentation_node_id_mismatch(tmp_path) -> None:
    record = base_record("node-mis-001")
    record["presentation"]["node_id"] = "ode_first_order_linear"
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_validation_error", "presentation.node_id")


def test_validator_rejects_unknown_node_id(tmp_path) -> None:
    record = base_record("bad-node-001")
    record["manifest"]["node_id"] = "not_a_real_node"
    record["presentation"]["node_id"] = "not_a_real_node"
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_identity_error", "unknown node_id")


def test_validator_rejects_invalid_status(tmp_path) -> None:
    record = base_record("bad-stat-001")
    record["manifest"]["status"] = "archived"
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_validation_error", "Input should be")


def test_validator_rejects_invalid_audience(tmp_path) -> None:
    record = base_record("bad-audn-001")
    record["manifest"]["audience"] = "public"
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_validation_error", "Input should be")


def test_validator_rejects_invalid_question_id(tmp_path) -> None:
    record = base_record("bad/id-001")
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_validation_error", "question_id")


def test_validator_rejects_invalid_supersedes(tmp_path) -> None:
    record = base_record("supersed-001")
    record["manifest"]["supersedes"] = "missing-001"
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_identity_error", "supersedes")


def test_validator_rejects_supersedes_self_reference(tmp_path) -> None:
    record = base_record("self-ref-001")
    record["manifest"]["supersedes"] = "self-ref-001"
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_identity_error", "same question_id")


def test_validator_rejects_empty_title(tmp_path) -> None:
    record = base_record("emptytit-001")
    record["presentation"]["title"] = "   "
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_public_layer_error", "title")


def test_validator_rejects_empty_stem(tmp_path) -> None:
    record = base_record("emptystem-001")
    record["presentation"]["stem"] = ""
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_public_layer_error", "stem")


def test_validator_rejects_empty_prompt_markdown(tmp_path) -> None:
    record = base_record("emptypmt-001")
    record["presentation"]["prompt_markdown"] = " "
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_public_layer_error", "prompt_markdown")


def test_validator_rejects_invalid_answer_format(tmp_path) -> None:
    record = base_record("badfmt-001")
    record["presentation"]["answer_format"] = "multiple_choice"
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_public_layer_error", "answer_format")


def test_validator_rejects_invalid_response_step_mode(tmp_path) -> None:
    record = base_record("badstep-001")
    record["presentation"]["response_step_mode"] = "guided"
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_public_layer_error", "response_step_mode")


def test_validator_rejects_invalid_difficulty(tmp_path) -> None:
    record = base_record("baddiff-001")
    record["presentation"]["difficulty"] = "impossible"
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_public_layer_error", "difficulty")


def test_validator_rejects_public_prompt_expected_answer_leak(tmp_path) -> None:
    record = base_record("leakpmt-001")
    record["presentation"]["prompt_markdown"] = "Solve dy/dx=2xy. The answer is ln|y|=x^2+C."
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_leak_error", "expected_answer")


def test_validator_rejects_hints_public_answer_leak(tmp_path) -> None:
    record = base_record("leakhint-001")
    record["presentation"]["hints_public"] = ["You should get ln|y| = x^2 + C."]
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_leak_error", "expected_answer")


def test_validator_rejects_display_assets_trusted_field(tmp_path) -> None:
    record = base_record("assetbad-001")
    record["presentation"]["display_assets"] = [{"kind": "image", "expected_answer": "spoof"}]
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_leak_error", "expected_answer")


def test_validator_rejects_public_layer_trusted_field(tmp_path) -> None:
    record = base_record("publbad-001")
    record["presentation"]["rubric"] = {"items": []}
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_validation_error", "Extra inputs are not permitted")


def test_validator_rejects_published_learner_missing_expected_answer(tmp_path) -> None:
    record = base_record("noanswer-001")
    record["trusted_scoring"]["expected_answer"] = ""
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_trusted_layer_error", "expected_answer")


def test_validator_rejects_duplicate_answer_aliases(tmp_path) -> None:
    record = base_record("dupalias-001")
    record["trusted_scoring"]["answer_aliases"] = ["y=Ce^(x^2)", " y = c e^(x^2) "]
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_trusted_layer_error", "answer_aliases")


def test_validator_rejects_blank_answer_alias(tmp_path) -> None:
    record = base_record("blankals-001")
    record["trusted_scoring"]["answer_aliases"] = [" "]
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_trusted_layer_error", "answer_aliases")


def test_validator_rejects_missing_solution_outline(tmp_path) -> None:
    record = base_record("nosoln-001")
    record["trusted_scoring"]["solution_outline"] = ""
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_trusted_layer_error", "solution_outline")


def test_validator_rejects_missing_rubric(tmp_path) -> None:
    record = base_record("norubric-001")
    record["trusted_scoring"]["rubric"] = None
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_trusted_layer_error", "rubric")


def test_validator_rejects_rubric_item_missing_target_dimensions(tmp_path) -> None:
    record = base_record("notarget-001")
    del record["trusted_scoring"]["rubric"]["items"][0]["target_dimensions"]
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_validation_error", "target_dimensions")


def test_validator_rejects_rubric_item_invalid_dimension(tmp_path) -> None:
    record = base_record("baddimn-001")
    record["trusted_scoring"]["rubric"]["items"][0]["target_dimensions"] = ["not_a_dimension"]
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_validation_error", "Input should be")


def test_validator_rejects_rubric_item_nonpositive_weight(tmp_path) -> None:
    record = base_record("badwght-001")
    record["trusted_scoring"]["rubric"]["items"][0]["weight"] = 0
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_rubric_error", "weight")


def test_validator_rejects_duplicate_rubric_item_id(tmp_path) -> None:
    record = base_record("duprubr-001")
    item = deepcopy(record["trusted_scoring"]["rubric"]["items"][0])
    record["trusted_scoring"]["rubric"]["items"].append(item)
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_rubric_error", "duplicate rubric item id")


def test_validator_rejects_no_required_rubric_item(tmp_path) -> None:
    record = base_record("noreqrb-001")
    record["trusted_scoring"]["rubric"]["items"][0]["required"] = False
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_rubric_error", "required item")


def test_validator_rejects_validator_config_reserved_key(tmp_path) -> None:
    record = base_record("vcfgres-001")
    record["trusted_scoring"]["validator_config"] = {"score_overrides": {"trigger": 100}}
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_validation_error", "reserved metadata keys")


def test_validator_rejects_validator_config_unknown_key(tmp_path) -> None:
    record = base_record("vcfgunk-001")
    record["trusted_scoring"]["validator_config"] = {"requires_constant": True, "custom_flag": True}
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_trusted_layer_error", "unknown keys")


def test_validator_rejects_validator_config_wrong_value_type(tmp_path) -> None:
    record = base_record("vcfgtyp-001")
    record["trusted_scoring"]["validator_config"] = {"requires_constant": "yes"}
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_trusted_layer_error", "requires_constant")


def test_validator_accepts_normal_requires_constant(tmp_path) -> None:
    record = base_record("goodvcfg-001")
    record["trusted_scoring"]["validator_config"] = {"requires_constant": True}
    write_catalog(tmp_path, [record])

    YamlQuestionCatalogRepository(tmp_path).validate_catalog()


@pytest.mark.parametrize("mode", ["exact", "normalized", "symbolic"])
def test_validator_accepts_answer_equivalence_mode_values(tmp_path, mode: str) -> None:
    record = base_record(f"mode-{mode}-001")
    record["trusted_scoring"]["validator_config"] = {"answer_equivalence_mode": mode}
    write_catalog(tmp_path, [record])

    YamlQuestionCatalogRepository(tmp_path).validate_catalog()


def test_validator_rejects_invalid_answer_equivalence_mode(tmp_path) -> None:
    record = base_record("badmode-001")
    record["trusted_scoring"]["validator_config"] = {"answer_equivalence_mode": "approximate"}
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_trusted_layer_error", "answer_equivalence_mode")


def test_validator_rejects_dimension_outside_node_core_and_extensions(tmp_path) -> None:
    record = base_record("baddimx-001")
    record["trusted_scoring"]["rubric"]["items"][0]["target_dimensions"] = ["migration"]
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_dimension_error", "not a core or allowed extension")


def test_validator_rejects_no_node_core_dimension_covered(tmp_path) -> None:
    record = base_record("nocorex-001")
    record["trusted_scoring"]["rubric"]["items"][0]["target_dimensions"] = ["expression"]
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_dimension_error", "at least one node core dimension")


def test_validator_rejects_blank_question_version(tmp_path) -> None:
    record = base_record("blankqv-001")
    record["manifest"]["question_version"] = ""
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_version_error", "question_version")


def test_validator_rejects_blank_rubric_version(tmp_path) -> None:
    record = base_record("blankrv-001")
    record["manifest"]["rubric_version"] = " "
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_version_error", "rubric_version")


def test_validator_rejects_blank_answer_key_version(tmp_path) -> None:
    record = base_record("blankav-001")
    record["manifest"]["answer_key_version"] = ""
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_version_error", "answer_key_version")


def test_validator_rejects_invalid_content_hash_format(tmp_path) -> None:
    record = base_record("badhash-001")
    record["manifest"]["content_hash"] = "abc123"
    write_catalog(tmp_path, [record])

    assert_catalog_error(tmp_path, "catalog_hash_error", "content_hash")


def test_validator_accepts_valid_content_hash_format(tmp_path) -> None:
    record = base_record("goodhash-001")
    record["manifest"]["content_hash"] = "sha256:" + ("a" * 64)
    write_catalog(tmp_path, [record])

    YamlQuestionCatalogRepository(tmp_path).validate_catalog()


def test_validator_get_public_question_still_does_not_leak_trusted_fields() -> None:
    response = TestClient(create_app("learner")).get("/api/learner/v1/questions/ode-sep-001")

    assert response.status_code == 200
    assert "expected_answer" not in response.text
    assert "rubric" not in response.text
    assert "solution_outline" not in response.text


def test_validator_learner_submit_still_does_not_leak_trusted_fields() -> None:
    response = TestClient(create_app("learner")).post(
        "/api/learner/v1/attempts/submit",
        json={"question_id": "ode-sep-001", "user_answer": GOOD_ANSWER},
    )

    assert response.status_code == 200
    assert "expected_answer" not in response.text
    assert "rubric" not in response.text
    assert "solution_outline" not in response.text


def test_validator_draft_retired_internal_still_invisible() -> None:
    client = TestClient(create_app("learner"))

    assert client.get("/api/learner/v1/questions/ode-sep-draft-001").status_code == 404
    assert client.get("/api/learner/v1/questions/ode-sep-retired-001").status_code == 404
    assert client.get("/api/learner/v1/questions/ode-sep-internal-001").status_code == 404


def test_validator_learner_profile_route_gating_intact() -> None:
    client = TestClient(create_app("learner"))

    assert client.get("/api/learner/v1/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 404


def test_validator_internal_profile_route_gating_intact() -> None:
    client = TestClient(create_app("internal"))

    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/learner/v1/health").status_code == 404


def test_catalog_validator_service_is_importable() -> None:
    assert CatalogValidator().__class__.__name__ == "CatalogValidator"


def assert_catalog_error(tmp_path, error_code: str, message_part: str) -> None:
    with pytest.raises(CatalogValidationError) as exc_info:
        YamlQuestionCatalogRepository(tmp_path).validate_catalog()
    assert exc_info.value.error_code == error_code
    assert message_part in str(exc_info.value)


def base_record(question_id: str) -> dict[str, Any]:
    return {
        "manifest": {
            "question_id": question_id,
            "logical_question_id": f"{question_id}-logical",
            "question_family_id": "testfam-001",
            "node_id": "ode_separable",
            "status": "published",
            "audience": "learner",
            "question_version": "1.0",
            "rubric_version": "1.0",
            "answer_key_version": "1.0",
            "catalog_schema_version": "1.0",
            "tags": ["test"],
        },
        "presentation": {
            "question_id": question_id,
            "node_id": "ode_separable",
            "title": "Test question",
            "stem": "Solve.",
            "prompt_markdown": "Solve dy/dx = 2xy.",
            "answer_format": "expression",
            "response_step_mode": "optional",
            "difficulty": "basic",
        },
        "trusted_scoring": {
            "expected_answer": "ln|y|=x^2+C",
            "answer_aliases": ["y=Ce^(x^2)"],
            "rubric": {
                "items": [
                    {
                        "id": "trigger",
                        "description": "Trigger",
                        "target_dimensions": ["trigger"],
                        "required_keywords": ["separable"],
                        "weight": 1.0,
                        "required": True,
                        "evidence_on_hit": "hit",
                        "evidence_on_miss": "miss",
                    }
                ]
            },
            "solution_outline": "Separate and integrate.",
            "validator_config": {"requires_constant": True},
            "scoring_notes_internal": "test",
            "golden_case_refs": [],
            "authoring_metadata": {},
        },
    }


def write_catalog(tmp_path, records: list[dict[str, Any]]) -> None:
    questions_dir = tmp_path / "questions"
    questions_dir.mkdir()
    question_paths: list[str] = []
    for index, record in enumerate(records):
        path = questions_dir / f"q{index}.yaml"
        path.write_text(yaml.safe_dump(record, sort_keys=False), encoding="utf-8")
        question_paths.append(f"questions/q{index}.yaml")
    (tmp_path / "manifest.yaml").write_text(
        yaml.safe_dump({"catalog_schema_version": "1.0", "questions": question_paths}, sort_keys=False),
        encoding="utf-8",
    )
