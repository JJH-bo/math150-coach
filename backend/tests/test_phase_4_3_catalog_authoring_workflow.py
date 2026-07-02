from __future__ import annotations

from copy import deepcopy
from typing import Any, get_args

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.nodes import load_node_catalog
from app.catalog.authoring_models import (
    AuthoringDraft,
    AuthoringStatus,
    HumanReviewChecklist,
    SourceMetadata,
    SourceType,
)
from app.catalog.authoring_workflow import CatalogAuthoringWorkflow
from app.catalog.hash_utils import canonical_runtime_record_payload, compute_runtime_content_hash
from app.catalog.models import CatalogQuestionRecord, CatalogStatus, PublicQuestionView
from app.catalog.repository import CatalogValidationError
from app.catalog.validation_report import CatalogValidationReport, ValidationSeverity
from app.catalog.validator import CatalogValidator
from app.catalog.yaml_repository import YamlQuestionCatalogRepository
from app.main import create_app


GOOD_ANSWER = "This is separable; separate variables; dy/y = 2x dx; integrate; ln|y|=x^2+C."


def test_authoring_status_is_independent_from_runtime_catalog_status() -> None:
    runtime_statuses = set(get_args(CatalogStatus))

    assert AuthoringStatus.VALIDATED.value not in runtime_statuses
    assert AuthoringStatus.REVIEW_REQUIRED.value not in runtime_statuses
    assert AuthoringStatus.APPROVED.value not in runtime_statuses


def test_source_metadata_is_not_public_presentation() -> None:
    source = sample_source_metadata()
    record = sample_record("auth-src-001")

    assert "source_metadata" not in record.presentation.model_dump()
    assert source.source_name not in str(record.presentation.model_dump())
    with pytest.raises(ValidationError):
        PublicQuestionView.model_validate({**record.presentation.model_dump(), "source_metadata": source.model_dump()})


def test_authoring_draft_wraps_catalog_record_without_mutating_it() -> None:
    record = sample_record("auth-wrap-001")
    before = record.model_dump()

    draft = sample_draft(record=record, source_metadata=sample_source_metadata())

    assert draft.candidate_record is record
    assert record.model_dump() == before


def test_human_review_checklist_defaults_to_not_publish_ready() -> None:
    checklist = HumanReviewChecklist()

    assert checklist.is_publish_ready() is False
    assert checklist.publish_approved is False


def test_complete_human_review_checklist_is_publish_ready() -> None:
    checklist = complete_review_checklist()

    assert checklist.is_publish_ready() is True


def test_validation_report_valid_draft_passes_and_marks_draft_validated() -> None:
    draft = sample_draft(question_id="auth-valid-001")

    report = workflow().validate_draft(draft, load_node_catalog())

    assert report.passed is True
    assert report.issues == []
    assert report.candidate_id == "auth-valid-001"
    assert draft.status == AuthoringStatus.VALIDATED
    assert draft.validation_report == report


def test_validation_report_invalid_draft_fails_and_marks_validation_failed() -> None:
    record = sample_record("auth-badn-001")
    record = record_with_manifest(record, node_id="not_a_real_node")
    record = record.model_copy(update={"presentation": record.presentation.model_copy(update={"node_id": "not_a_real_node"})})
    draft = sample_draft(record=record)

    report = workflow().validate_draft(draft, load_node_catalog())

    assert report.passed is False
    assert draft.status == AuthoringStatus.VALIDATION_FAILED


def test_validation_report_includes_error_code() -> None:
    draft = sample_draft(record=record_with_bad_hash("auth-hash-001"))

    report = workflow().validate_draft(draft, load_node_catalog())

    assert report.passed is False
    assert report.issues[0].error_code == "catalog_hash_error"
    assert report.issues[0].severity == ValidationSeverity.ERROR


def test_validation_report_includes_candidate_id() -> None:
    draft = sample_draft(record=record_with_bad_hash("auth-hash-002"), import_batch_id="batch-001")

    report = workflow().validate_draft(draft, load_node_catalog())

    assert report.candidate_id == "auth-hash-002"
    assert report.batch_id == "batch-001"
    assert report.issues[0].candidate_id == "auth-hash-002"
    assert report.issues[0].batch_id == "batch-001"


def test_validation_failed_draft_cannot_publish() -> None:
    draft = sample_draft(record=record_with_bad_hash("auth-hash-003"), review_checklist=complete_review_checklist())
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())

    with pytest.raises(ValueError, match="pass CatalogValidator"):
        authoring.build_publish_candidate(draft, load_node_catalog())


def test_runtime_catalog_validator_remains_fail_fast() -> None:
    record = record_with_bad_hash("auth-ffst-001")

    with pytest.raises(CatalogValidationError) as exc_info:
        CatalogValidator().validate_record(record, node_by_id(), {record.manifest.question_id})

    assert exc_info.value.error_code == "catalog_hash_error"


def test_content_hash_format_is_sha256_lowercase_hex() -> None:
    digest = compute_runtime_content_hash(sample_record("auth-hfmt-001"))

    assert digest.startswith("sha256:")
    assert len(digest) == 71
    assert digest == digest.lower()


def test_same_record_hash_is_stable() -> None:
    record = sample_record("auth-hstb-001")

    assert compute_runtime_content_hash(record) == compute_runtime_content_hash(record)


def test_dict_field_order_does_not_affect_hash() -> None:
    raw = sample_record("auth-hord-001").model_dump(mode="json")
    reordered = {
        "trusted_scoring": raw["trusted_scoring"],
        "presentation": raw["presentation"],
        "manifest": raw["manifest"],
    }

    assert compute_runtime_content_hash(CatalogQuestionRecord.model_validate(raw)) == compute_runtime_content_hash(
        CatalogQuestionRecord.model_validate(reordered)
    )


def test_content_hash_field_itself_is_excluded_from_hash() -> None:
    record = sample_record("auth-hexcl-001")
    with_hash = record_with_manifest(record, content_hash="sha256:" + ("a" * 64))

    assert compute_runtime_content_hash(record) == compute_runtime_content_hash(with_hash)


def test_authoring_metadata_is_excluded_from_hash() -> None:
    record = sample_record("auth-hmeta-001")
    trusted = record.trusted_scoring.model_copy(update={"authoring_metadata": {"source": "draft note changed"}})
    with_authoring_metadata = record.model_copy(update={"trusted_scoring": trusted})

    assert compute_runtime_content_hash(record) == compute_runtime_content_hash(with_authoring_metadata)


def test_source_metadata_is_excluded_from_hash() -> None:
    record = sample_record("auth-hsrc-001")
    draft_a = sample_draft(record=record, source_metadata=sample_source_metadata(source_name="Source A"))
    draft_b = sample_draft(record=record, source_metadata=sample_source_metadata(source_name="Source B"))

    assert compute_runtime_content_hash(draft_a.candidate_record) == compute_runtime_content_hash(draft_b.candidate_record)


def test_changing_presentation_changes_hash() -> None:
    record = sample_record("auth-hprs-001")
    changed = record.model_copy(update={"presentation": record.presentation.model_copy(update={"title": "Changed title"})})

    assert compute_runtime_content_hash(record) != compute_runtime_content_hash(changed)


def test_changing_trusted_scoring_changes_hash() -> None:
    record = sample_record("auth-htru-001")
    changed = record.model_copy(
        update={"trusted_scoring": record.trusted_scoring.model_copy(update={"expected_answer": "ln|y|=x^2+C+1"})}
    )

    assert compute_runtime_content_hash(record) != compute_runtime_content_hash(changed)


def test_canonical_payload_excludes_content_hash_and_authoring_metadata() -> None:
    record = sample_record("auth-hpay-001")
    record = record_with_manifest(record, content_hash="sha256:" + ("b" * 64))

    payload = canonical_runtime_record_payload(record)

    assert "content_hash" not in payload["manifest"]
    assert "authoring_metadata" not in payload["trusted_scoring"]


def test_valid_draft_can_enter_validated_path() -> None:
    draft = sample_draft(question_id="auth-path-001")

    workflow().validate_draft(draft, load_node_catalog())

    assert draft.status in {AuthoringStatus.VALIDATED, AuthoringStatus.REVIEW_REQUIRED}


def test_draft_without_review_cannot_build_publish_candidate() -> None:
    draft = sample_draft(question_id="auth-norev-001")
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())

    with pytest.raises(ValueError, match="human review"):
        authoring.build_publish_candidate(draft, load_node_catalog())


def test_incomplete_review_cannot_build_publish_candidate() -> None:
    draft = sample_draft(question_id="auth-incv-001", review_checklist=HumanReviewChecklist(publish_approved=True))
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())

    with pytest.raises(ValueError, match="human review"):
        authoring.build_publish_candidate(draft, load_node_catalog())


def test_complete_review_can_build_publish_candidate() -> None:
    draft = sample_draft(question_id="auth-comp-001", review_checklist=complete_review_checklist())
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())

    candidate = authoring.build_publish_candidate(draft, load_node_catalog())

    assert candidate.manifest.status == "published"
    assert candidate.manifest.question_id == "auth-comp-001"


def test_ai_assisted_draft_cannot_auto_publish_without_review() -> None:
    draft = sample_draft(question_id="auth-aiun-001", ai_assisted=True)
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())

    with pytest.raises(ValueError, match="human review"):
        authoring.build_publish_candidate(draft, load_node_catalog())


def test_ai_assisted_draft_can_build_candidate_only_after_review() -> None:
    draft = sample_draft(question_id="auth-airv-001", ai_assisted=True, review_checklist=complete_review_checklist())
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())

    candidate = authoring.build_publish_candidate(draft, load_node_catalog())

    assert candidate.manifest.content_hash


def test_publish_candidate_gets_content_hash_generated() -> None:
    draft = sample_draft(question_id="auth-phsh-001", review_checklist=complete_review_checklist())
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())

    candidate = authoring.build_publish_candidate(draft, load_node_catalog())

    assert candidate.manifest.content_hash is not None
    assert candidate.manifest.content_hash.startswith("sha256:")


def test_publish_candidate_passes_catalog_validator() -> None:
    draft = sample_draft(question_id="auth-pval-001", review_checklist=complete_review_checklist())
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())
    candidate = authoring.build_publish_candidate(draft, load_node_catalog())

    CatalogValidator().validate_record(candidate, node_by_id(), {candidate.manifest.question_id})


def test_source_metadata_not_copied_into_runtime_candidate() -> None:
    source = sample_source_metadata(source_name="Private Lecture Source")
    draft = sample_draft(question_id="auth-nosrc-001", source_metadata=source, review_checklist=complete_review_checklist())
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())

    candidate = authoring.build_publish_candidate(draft, load_node_catalog())

    assert "Private Lecture Source" not in str(candidate.model_dump())
    assert "source_metadata" not in str(candidate.model_dump())


def test_validation_report_not_copied_into_runtime_candidate() -> None:
    draft = sample_draft(question_id="auth-norp-001", review_checklist=complete_review_checklist())
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())

    candidate = authoring.build_publish_candidate(draft, load_node_catalog())

    assert "validation_report" not in candidate.model_dump()


def test_review_checklist_not_copied_into_runtime_candidate() -> None:
    draft = sample_draft(question_id="auth-norv-001", review_checklist=complete_review_checklist())
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())

    candidate = authoring.build_publish_candidate(draft, load_node_catalog())

    assert "review_checklist" not in candidate.model_dump()


def test_rejected_draft_cannot_publish() -> None:
    draft = sample_draft(question_id="auth-rejt-001", review_checklist=complete_review_checklist())
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())
    authoring.reject_draft(draft, "Not in scope")

    with pytest.raises(ValueError, match="rejected"):
        authoring.build_publish_candidate(draft, load_node_catalog())


def test_reject_draft_records_reason_without_formal_catalog_write() -> None:
    draft = sample_draft(question_id="auth-rsnx-001")

    rejected = workflow().reject_draft(draft, "duplicate source")

    assert rejected.status == AuthoringStatus.REJECTED
    assert rejected.rejection_reason == "duplicate source"
    assert YamlQuestionCatalogRepository().get_published("auth-rsnx-001") is None


def test_authoring_drafts_are_not_served_by_learner_api() -> None:
    draft = sample_draft(question_id="auth-drft-001", review_checklist=complete_review_checklist())
    authoring = workflow()
    authoring.validate_draft(draft, load_node_catalog())
    authoring.build_publish_candidate(draft, load_node_catalog())

    response = TestClient(create_app("learner")).get("/api/learner/v1/questions/auth-drft-001")

    assert response.status_code == 404


def test_source_metadata_does_not_appear_in_learner_get_question() -> None:
    response = TestClient(create_app("learner")).get("/api/learner/v1/questions/ode-sep-001")

    assert response.status_code == 200
    assert "source_metadata" not in response.text
    assert "source_fingerprint" not in response.text
    assert "copyright_note" not in response.text


def test_source_metadata_does_not_appear_in_learner_submit_response() -> None:
    response = TestClient(create_app("learner")).post(
        "/api/learner/v1/attempts/submit",
        json={"question_id": "ode-sep-001", "user_answer": GOOD_ANSWER},
    )

    assert response.status_code == 200
    assert "source_metadata" not in response.text
    assert "source_fingerprint" not in response.text
    assert "copyright_note" not in response.text


def test_formal_catalog_default_still_validates() -> None:
    YamlQuestionCatalogRepository().validate_catalog()


def test_learner_api_leak_regression_still_passes() -> None:
    response = TestClient(create_app("learner")).get("/api/learner/v1/questions/ode-sep-001")

    assert response.status_code == 200
    assert "expected_answer" not in response.text
    assert "rubric" not in response.text
    assert "solution_outline" not in response.text


def test_learner_profile_route_gating_still_intact() -> None:
    client = TestClient(create_app("learner"))

    assert client.get("/api/learner/v1/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 404


def test_internal_profile_route_gating_still_intact() -> None:
    client = TestClient(create_app("internal"))

    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/learner/v1/health").status_code == 404


def workflow() -> CatalogAuthoringWorkflow:
    return CatalogAuthoringWorkflow()


def node_by_id() -> dict[str, Any]:
    return {node.id: node for node in load_node_catalog()}


def sample_source_metadata(source_name: str = "Manual authoring note") -> SourceMetadata:
    return SourceMetadata(
        source_type=SourceType.MANUAL,
        source_name=source_name,
        source_section="ODE basics",
        page_range="p.1",
        problem_number="1",
        original_problem_ref="local-ref-001",
        author_notes="internal note only",
        copyright_note="do not expose source text",
        imported_by="phase_4_3_test",
        source_fingerprint="source:fingerprint:001",
    )


def complete_review_checklist() -> HumanReviewChecklist:
    return HumanReviewChecklist(
        math_i_scope_confirmed=True,
        module_topic_type_confirmed=True,
        node_id_confirmed=True,
        public_prompt_clear=True,
        expected_answer_checked=True,
        aliases_checked=True,
        solution_outline_checked=True,
        rubric_checked=True,
        target_dimensions_checked=True,
        validator_config_checked=True,
        no_public_leak_confirmed=True,
        question_id_version_checked=True,
        publish_approved=True,
        reviewer="human-reviewer",
    )


def sample_draft(
    question_id: str = "auth-draft-001",
    *,
    record: CatalogQuestionRecord | None = None,
    source_metadata: SourceMetadata | None = None,
    review_checklist: HumanReviewChecklist | None = None,
    ai_assisted: bool = False,
    import_batch_id: str | None = None,
) -> AuthoringDraft:
    record = record or sample_record(question_id)
    return AuthoringDraft(
        draft_id=f"draft-{record.manifest.question_id}",
        import_batch_id=import_batch_id,
        status=AuthoringStatus.DRAFT,
        candidate_record=record,
        source_metadata=source_metadata,
        review_checklist=review_checklist,
        ai_assisted=ai_assisted,
    )


def sample_record(question_id: str) -> CatalogQuestionRecord:
    return CatalogQuestionRecord.model_validate(sample_record_data(question_id))


def record_with_bad_hash(question_id: str) -> CatalogQuestionRecord:
    return record_with_manifest(sample_record(question_id), content_hash="not-a-valid-hash")


def record_with_manifest(record: CatalogQuestionRecord, **updates: Any) -> CatalogQuestionRecord:
    return record.model_copy(update={"manifest": record.manifest.model_copy(update=updates)})


def sample_record_data(question_id: str) -> dict[str, Any]:
    data = {
        "manifest": {
            "question_id": question_id,
            "logical_question_id": f"{question_id}-logical",
            "question_family_id": "authfam-001",
            "node_id": "ode_separable",
            "status": "draft",
            "audience": "learner",
            "question_version": "1.0",
            "rubric_version": "1.0",
            "answer_key_version": "1.0",
            "catalog_schema_version": "1.0",
            "tags": ["authoring", "test"],
        },
        "presentation": {
            "question_id": question_id,
            "node_id": "ode_separable",
            "title": "Authoring test question",
            "stem": "Solve.",
            "prompt_markdown": "Solve dy/dx = 2xy and explain why separation applies.",
            "answer_format": "expression_with_reasoning",
            "response_step_mode": "optional",
            "difficulty": "basic",
            "display_assets": [],
            "hints_public": ["Look for whether variables can be separated."],
        },
        "trusted_scoring": {
            "expected_answer": "ln|y|=x^2+C",
            "answer_aliases": ["y=Ce^(x^2)"],
            "rubric": {
                "items": [
                    {
                        "id": "trigger",
                        "description": "Recognizes separable structure.",
                        "target_dimensions": ["trigger"],
                        "required_keywords": ["separable"],
                        "weight": 1.0,
                        "required": True,
                        "evidence_on_hit": "Identified separable structure.",
                        "evidence_on_miss": "Did not identify separable structure.",
                    },
                    {
                        "id": "method",
                        "description": "Chooses separation of variables.",
                        "target_dimensions": ["method"],
                        "required_keywords": ["separate variables"],
                        "weight": 1.0,
                        "required": True,
                        "evidence_on_hit": "Chose separation of variables.",
                        "evidence_on_miss": "Did not choose separation of variables.",
                    },
                ]
            },
            "solution_outline": "Separate dy/y = 2x dx, integrate to ln|y| = x^2 + C.",
            "validator_config": {"requires_constant": True},
            "scoring_notes_internal": "authoring workflow test",
            "golden_case_refs": [],
            "authoring_metadata": {"draft_note": "excluded from hash"},
        },
    }
    return deepcopy(data)
