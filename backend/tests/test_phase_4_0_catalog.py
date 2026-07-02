from __future__ import annotations

from copy import deepcopy

import pytest
import yaml

from app.catalog.models import validate_question_id
from app.catalog.repository import CatalogValidationError
from app.catalog.yaml_repository import YamlQuestionCatalogRepository
from app.core.enums import ScoreDimension


def test_catalog_uses_yaml_safe_load(monkeypatch) -> None:
    from app.catalog import yaml_repository

    calls: list[object] = []
    original = yaml_repository.yaml.safe_load

    def spy(stream):
        calls.append(stream)
        return original(stream)

    monkeypatch.setattr(yaml_repository.yaml, "safe_load", spy)
    YamlQuestionCatalogRepository().validate_catalog()

    assert len(calls) >= 5


def test_catalog_default_records_are_valid() -> None:
    YamlQuestionCatalogRepository().validate_catalog()


def test_catalog_gets_published_learner_record() -> None:
    record = YamlQuestionCatalogRepository().get_published("ode-sep-001")

    assert record is not None
    assert record.manifest.status == "published"
    assert record.manifest.audience == "learner"


def test_catalog_draft_record_is_not_published() -> None:
    assert YamlQuestionCatalogRepository().get_published("ode-sep-draft-001") is None


def test_catalog_retired_record_is_not_published() -> None:
    assert YamlQuestionCatalogRepository().get_published("ode-sep-retired-001") is None


def test_catalog_internal_record_is_not_published() -> None:
    assert YamlQuestionCatalogRepository().get_published("ode-sep-internal-001") is None


def test_catalog_list_published_by_node_only_returns_visible_learner_questions() -> None:
    records = YamlQuestionCatalogRepository().list_published_by_node("ode_separable")

    assert [record.manifest.question_id for record in records] == ["ode-sep-001"]


def test_catalog_public_view_does_not_contain_trusted_scoring_fields() -> None:
    record = YamlQuestionCatalogRepository().get_published("ode-sep-001")
    assert record is not None

    public_payload = record.to_public_question_view().model_dump(mode="json")

    assert "expected_answer" not in public_payload
    assert "rubric" not in public_payload
    assert "solution_outline" not in public_payload
    assert record.trusted_scoring.expected_answer


def test_catalog_domain_question_hydrates_trusted_scoring_server_side() -> None:
    record = YamlQuestionCatalogRepository().get_published("ode-sep-001")
    assert record is not None

    question = record.to_domain_question()

    assert question.expected_answer == "ln|y|=x^2+C"
    assert question.rubric is not None
    assert ScoreDimension.TRIGGER in question.tested_dimensions
    assert question.metadata["expected_answer_aliases"]
    assert question.metadata["requires_constant"] is True


def test_catalog_invalid_question_id_format_is_rejected() -> None:
    with pytest.raises(ValueError):
        validate_question_id("../secret")


def test_catalog_get_published_hides_invalid_question_id() -> None:
    assert YamlQuestionCatalogRepository().get_published("bad%idxx") is None


def test_catalog_rejects_duplicate_question_id(tmp_path) -> None:
    record = base_record("dup-qid-001")
    write_catalog(tmp_path, [record, deepcopy(record)])

    with pytest.raises(CatalogValidationError, match="duplicate question_id"):
        YamlQuestionCatalogRepository(tmp_path).validate_catalog()


def test_catalog_rejects_unknown_node_id(tmp_path) -> None:
    record = base_record("bad-node-001")
    record["manifest"]["node_id"] = "not_a_real_ode_node"
    record["presentation"]["node_id"] = "not_a_real_ode_node"
    write_catalog(tmp_path, [record])

    with pytest.raises(CatalogValidationError, match="unknown node_id"):
        YamlQuestionCatalogRepository(tmp_path).validate_catalog()


def test_catalog_rejects_invalid_status(tmp_path) -> None:
    record = base_record("bad-stat-001")
    record["manifest"]["status"] = "archived"
    write_catalog(tmp_path, [record])

    with pytest.raises(CatalogValidationError):
        YamlQuestionCatalogRepository(tmp_path).validate_catalog()


def test_catalog_rejects_invalid_audience(tmp_path) -> None:
    record = base_record("bad-audn-001")
    record["manifest"]["audience"] = "public"
    write_catalog(tmp_path, [record])

    with pytest.raises(CatalogValidationError):
        YamlQuestionCatalogRepository(tmp_path).validate_catalog()


def test_catalog_rejects_presentation_manifest_mismatch(tmp_path) -> None:
    record = base_record("mismatch-001")
    record["presentation"]["question_id"] = "mismatch-002"
    write_catalog(tmp_path, [record])

    with pytest.raises(CatalogValidationError, match="presentation.question_id"):
        YamlQuestionCatalogRepository(tmp_path).validate_catalog()


def test_catalog_rejects_validator_config_catalog_question_id_override(tmp_path) -> None:
    record = base_record("bad-vcfg-001")
    record["trusted_scoring"]["validator_config"] = {"catalog_question_id": "spoofed"}
    write_catalog(tmp_path, [record])

    with pytest.raises(CatalogValidationError, match="reserved metadata keys"):
        YamlQuestionCatalogRepository(tmp_path).validate_catalog()


def test_catalog_rejects_validator_config_expected_answer_aliases_override(tmp_path) -> None:
    record = base_record("bad-vcfg-002")
    record["trusted_scoring"]["validator_config"] = {"expected_answer_aliases": ["spoofed"]}
    write_catalog(tmp_path, [record])

    with pytest.raises(CatalogValidationError, match="reserved metadata keys"):
        YamlQuestionCatalogRepository(tmp_path).validate_catalog()


def test_catalog_rejects_validator_config_override_adapter_keys(tmp_path) -> None:
    record = base_record("bad-vcfg-003")
    record["trusted_scoring"]["validator_config"] = {"score_overrides": {"trigger": 100}, "manual_override": True}
    write_catalog(tmp_path, [record])

    with pytest.raises(CatalogValidationError, match="reserved metadata keys"):
        YamlQuestionCatalogRepository(tmp_path).validate_catalog()


def test_catalog_allows_normal_validator_config_to_enter_domain_metadata(tmp_path) -> None:
    record = base_record("good-vcfg-001")
    record["trusted_scoring"]["validator_config"] = {"requires_constant": True}
    write_catalog(tmp_path, [record])

    repository = YamlQuestionCatalogRepository(tmp_path)
    repository.validate_catalog()
    published = repository.get_published("good-vcfg-001")
    assert published is not None

    question = published.to_domain_question()

    assert question.metadata["requires_constant"] is True
    assert question.metadata["catalog_question_id"] == "good-vcfg-001"


def test_catalog_rejects_validator_config_version_override(tmp_path) -> None:
    record = base_record("bad-vcfg-004")
    record["trusted_scoring"]["validator_config"] = {"question_version": "spoofed"}
    write_catalog(tmp_path, [record])

    with pytest.raises(CatalogValidationError, match="reserved metadata keys"):
        YamlQuestionCatalogRepository(tmp_path).validate_catalog()


def test_catalog_rejects_manifest_path_escape(tmp_path) -> None:
    (tmp_path / "manifest.yaml").write_text(
        yaml.safe_dump({"catalog_schema_version": "1.0", "questions": ["../outside.yaml"]}),
        encoding="utf-8",
    )

    with pytest.raises(CatalogValidationError, match="escapes catalog root"):
        YamlQuestionCatalogRepository(tmp_path).validate_catalog()


def base_record(question_id: str) -> dict:
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


def write_catalog(tmp_path, records: list[dict]) -> None:
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
