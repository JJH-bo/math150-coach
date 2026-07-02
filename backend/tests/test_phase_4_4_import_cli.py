from __future__ import annotations

import json
from argparse import Namespace
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.v1.nodes import load_node_catalog
from app.catalog.authoring_cli import (
    EXIT_HUMAN_REVIEW_FAILED,
    EXIT_PATH_ERROR,
    EXIT_SCHEMA_OR_PARSE_ERROR,
    EXIT_SUCCESS,
    EXIT_VALIDATION_FAILED,
    main,
    run_build_candidate_dry_run,
    run_validate_batch,
    run_validate_draft,
)
from app.catalog.authoring_io import AuthoringPathError, load_authoring_draft, load_import_manifest, load_review_checklist
from app.catalog.hash_utils import compute_runtime_content_hash
from app.catalog.import_manifest import ImportManifest, merge_source_metadata
from app.catalog.validator import CatalogValidator
from app.catalog.yaml_repository import YamlQuestionCatalogRepository
from app.main import create_app


GOOD_ANSWER = "This is separable; separate variables; dy/y = 2x dx; integrate; ln|y|=x^2+C."


def test_import_manifest_parse_success(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-man-001", draft_id="draft-one")
    write_manifest(root, drafts=[{"draft_id": "draft-one", "path": "drafts/one.yaml"}])

    manifest = load_import_manifest("import_manifest.yaml", root)

    assert manifest.import_batch_id == "batch-001"
    assert manifest.drafts[0].draft_id == "draft-one"


def test_import_manifest_invalid_path_rejected(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)

    with pytest.raises(AuthoringPathError):
        load_import_manifest("missing.yaml", root)


def test_import_manifest_path_escape_rejected(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    outside = tmp_path / "outside.yaml"
    write_yaml(outside, {"import_batch_id": "batch-out", "drafts": []})

    with pytest.raises(AuthoringPathError):
        load_import_manifest("../outside.yaml", root)


def test_import_manifest_duplicate_draft_id_rejected() -> None:
    with pytest.raises(ValidationError):
        ImportManifest.model_validate(
            {
                "import_batch_id": "batch-dup",
                "drafts": [
                    {"draft_id": "draft-one", "path": "drafts/one.yaml"},
                    {"draft_id": "draft-one", "path": "drafts/two.yaml"},
                ],
            }
        )


def test_expected_question_id_mismatch_rejected(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-exp-001", draft_id="draft-one")
    write_manifest(
        root,
        drafts=[{"draft_id": "draft-one", "path": "drafts/one.yaml", "expected_question_id": "cli-other-001"}],
    )

    result = run_validate_batch(batch_args(root))

    assert result.exit_code == EXIT_VALIDATION_FAILED
    assert result.payload["failed"] == 1
    assert result.payload["issues"][0]["error_code"] == "authoring_draft_load_error"


def test_source_metadata_merge_works() -> None:
    base = {"source_type": "manual", "source_name": "Base source", "source_section": "ODE"}
    override = {"source_name": "Override source", "problem_number": "7"}

    merged = merge_source_metadata(
        default_source_metadata=merge_source_metadata(None, base),
        override=override,
    )

    assert merged is not None
    assert merged.source_name == "Override source"
    assert merged.source_section == "ODE"
    assert merged.problem_number == "7"


def test_missing_draft_file_rejected_in_batch(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_manifest(root, drafts=[{"draft_id": "missing-draft", "path": "drafts/missing.yaml"}])

    result = run_validate_batch(batch_args(root))

    assert result.exit_code == EXIT_VALIDATION_FAILED
    assert result.payload["failed"] == 1


def test_authoring_draft_yaml_parse_success(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-yaml-001", draft_id="draft-one")

    draft = load_authoring_draft("drafts/one.yaml", root)

    assert draft.draft_id == "draft-one"
    assert draft.candidate_record.manifest.question_id == "cli-yaml-001"


def test_invalid_draft_schema_rejected(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_yaml(root / "drafts" / "bad.yaml", {"draft_id": "bad"})

    with pytest.raises(ValidationError):
        load_authoring_draft("drafts/bad.yaml", root)


def test_draft_candidate_record_validates(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-cand-001", draft_id="draft-one")
    draft = load_authoring_draft("drafts/one.yaml", root)

    CatalogValidator().validate_record(
        draft.candidate_record,
        {node.id: node for node in load_node_catalog()},
        {draft.candidate_record.manifest.question_id},
    )


def test_draft_source_metadata_internal_only(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-src-001", draft_id="draft-one", source_name="Private Source")
    draft = load_authoring_draft("drafts/one.yaml", root)

    assert draft.source_metadata is not None
    assert "Private Source" not in str(draft.candidate_record.presentation.model_dump())


def test_draft_review_checklist_parsed(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_review(root, "reviews/review.yaml", complete=True)

    checklist = load_review_checklist("reviews/review.yaml", root)

    assert checklist.is_publish_ready() is True


def test_validate_draft_success_exit_0(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-vd-001", draft_id="draft-one")

    result = run_validate_draft(validate_draft_args(root, "drafts/one.yaml"))

    assert result.exit_code == EXIT_SUCCESS
    assert result.payload["dry_run_only"] is True


def test_validate_draft_validation_failure_exit_1(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/bad.yaml", question_id="cli-vd-002", draft_id="draft-bad", bad_hash=True)

    result = run_validate_draft(validate_draft_args(root, "drafts/bad.yaml"))

    assert result.exit_code == EXIT_VALIDATION_FAILED


def test_validate_draft_schema_parse_error_exit_2(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    (root / "drafts" / "bad.yaml").write_text("[:", encoding="utf-8")

    result = run_validate_draft(validate_draft_args(root, "drafts/bad.yaml"))

    assert result.exit_code == EXIT_SCHEMA_OR_PARSE_ERROR
    assert result.payload["error_code"] == "schema_or_parse_error"


def test_validate_draft_path_error_exit_3(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)

    result = run_validate_draft(validate_draft_args(root, "../outside.yaml"))

    assert result.exit_code == EXIT_PATH_ERROR


def test_validation_failure_report_contains_error_code(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/bad.yaml", question_id="cli-vd-003", draft_id="draft-bad", bad_hash=True)

    result = run_validate_draft(validate_draft_args(root, "drafts/bad.yaml"))

    assert result.payload["validation_report"]["issues"][0]["error_code"] == "catalog_hash_error"


def test_validation_report_contains_candidate_id(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/bad.yaml", question_id="cli-vd-004", draft_id="draft-bad", bad_hash=True)

    result = run_validate_draft(validate_draft_args(root, "drafts/bad.yaml"))

    assert result.payload["validation_report"]["candidate_id"] == "cli-vd-004"


def test_validate_batch_all_pass(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-bat-001", draft_id="draft-one")
    write_manifest(root, drafts=[{"draft_id": "draft-one", "path": "drafts/one.yaml"}])

    result = run_validate_batch(batch_args(root))

    assert result.exit_code == EXIT_SUCCESS
    assert result.payload["passed"] == 1


def test_validate_batch_partial_failure_report(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/ok.yaml", question_id="cli-bat-002", draft_id="draft-ok")
    write_draft(root, "drafts/bad.yaml", question_id="cli-bat-003", draft_id="draft-bad", bad_hash=True)
    write_manifest(
        root,
        drafts=[
            {"draft_id": "draft-ok", "path": "drafts/ok.yaml"},
            {"draft_id": "draft-bad", "path": "drafts/bad.yaml"},
        ],
    )

    result = run_validate_batch(batch_args(root))

    assert result.payload["passed"] == 1
    assert result.payload["failed"] == 1


def test_strict_mode_partial_failure_exit_nonzero(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/bad.yaml", question_id="cli-bat-004", draft_id="draft-bad", bad_hash=True)
    write_manifest(root, drafts=[{"draft_id": "draft-bad", "path": "drafts/bad.yaml"}], strict_mode=True)

    result = run_validate_batch(batch_args(root))

    assert result.exit_code == EXIT_VALIDATION_FAILED


def test_non_strict_mode_mixed_report_can_exit_0(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/bad.yaml", question_id="cli-bat-005", draft_id="draft-bad", bad_hash=True)
    write_manifest(root, drafts=[{"draft_id": "draft-bad", "path": "drafts/bad.yaml"}], strict_mode=False)

    result = run_validate_batch(batch_args(root))

    assert result.exit_code == EXIT_SUCCESS
    assert result.payload["failed"] == 1


def test_batch_report_has_passed_failed_counts(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-bat-006", draft_id="draft-one")
    write_manifest(root, drafts=[{"draft_id": "draft-one", "path": "drafts/one.yaml"}])

    result = run_validate_batch(batch_args(root))

    assert result.payload["total"] == 1
    assert result.payload["passed"] == 1
    assert result.payload["failed"] == 0


def test_batch_report_has_dry_run_only_true(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_manifest(root, drafts=[])

    result = run_validate_batch(batch_args(root))

    assert result.payload["dry_run_only"] is True


def test_validate_batch_output_report_dir_parent_escape_rejected(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-dir-001", draft_id="draft-one")
    write_manifest(
        root,
        drafts=[{"draft_id": "draft-one", "path": "drafts/one.yaml"}],
        output_report_dir="../outside",
    )

    result = run_validate_batch(batch_args(root, output="report.json"))

    assert result.exit_code == EXIT_PATH_ERROR


def test_validate_batch_output_report_dir_absolute_outside_rejected(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    outside = tmp_path / "outside_reports"
    write_draft(root, "drafts/one.yaml", question_id="cli-dir-002", draft_id="draft-one")
    write_manifest(
        root,
        drafts=[{"draft_id": "draft-one", "path": "drafts/one.yaml"}],
        output_report_dir=str(outside),
    )

    result = run_validate_batch(batch_args(root, output="report.json"))

    assert result.exit_code == EXIT_PATH_ERROR


def test_validate_batch_output_report_dir_subdir_allowed(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-dir-003", draft_id="draft-one")
    write_manifest(
        root,
        drafts=[{"draft_id": "draft-one", "path": "drafts/one.yaml"}],
        output_report_dir="batch_001",
    )

    result = run_validate_batch(batch_args(root, output="report.json"))

    assert result.exit_code == EXIT_SUCCESS
    assert result.output_path is not None
    assert Path(result.output_path).parent == root / "reports" / "batch_001"


def test_validate_batch_rejects_output_to_formal_catalog_path(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-dir-004", draft_id="draft-one")
    write_manifest(root, drafts=[{"draft_id": "draft-one", "path": "drafts/one.yaml"}])
    formal_output = Path(__file__).resolve().parents[1] / "catalog_data" / "bad-report.json"

    result = run_validate_batch(batch_args(root, output=str(formal_output)))

    assert result.exit_code == EXIT_PATH_ERROR


def test_formal_catalog_manifest_unchanged_after_validate_batch_output(tmp_path: Path) -> None:
    before = formal_manifest_text()
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-dir-005", draft_id="draft-one")
    write_manifest(root, drafts=[{"draft_id": "draft-one", "path": "drafts/one.yaml"}], output_report_dir="batch_001")

    result = run_validate_batch(batch_args(root, output="report.json"))

    assert result.exit_code == EXIT_SUCCESS
    assert formal_manifest_text() == before


def test_reviewed_draft_builds_candidate(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/reviewed.yaml", question_id="cli-bld-001", draft_id="draft-reviewed", review=True)

    result = run_build_candidate_dry_run(build_args(root, "drafts/reviewed.yaml"))

    assert result.exit_code == EXIT_SUCCESS
    assert result.payload["candidate_record"]["manifest"]["status"] == "published"


def test_unreviewed_draft_fails_with_exit_4(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/unreviewed.yaml", question_id="cli-bld-002", draft_id="draft-unreviewed")

    result = run_build_candidate_dry_run(build_args(root, "drafts/unreviewed.yaml"))

    assert result.exit_code == EXIT_HUMAN_REVIEW_FAILED


def test_ai_assisted_unreviewed_draft_fails_with_exit_4(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/ai.yaml", question_id="cli-bld-003", draft_id="draft-ai", ai_assisted=True)

    result = run_build_candidate_dry_run(build_args(root, "drafts/ai.yaml"))

    assert result.exit_code == EXIT_HUMAN_REVIEW_FAILED


def test_rejected_draft_fails_build(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/rejected.yaml", question_id="cli-bld-004", draft_id="draft-rejected", review=True, rejected=True)

    result = run_build_candidate_dry_run(build_args(root, "drafts/rejected.yaml"))

    assert result.exit_code == EXIT_HUMAN_REVIEW_FAILED


def test_candidate_has_content_hash(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/reviewed.yaml", question_id="cli-bld-005", draft_id="draft-reviewed", review=True)

    result = run_build_candidate_dry_run(build_args(root, "drafts/reviewed.yaml"))

    assert result.payload["content_hash"].startswith("sha256:")


def test_candidate_passes_catalog_validator(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/reviewed.yaml", question_id="cli-bld-006", draft_id="draft-reviewed", review=True)

    result = run_build_candidate_dry_run(build_args(root, "drafts/reviewed.yaml"))

    from app.catalog.models import CatalogQuestionRecord
    candidate = CatalogQuestionRecord.model_validate(result.payload["candidate_record"])
    CatalogValidator().validate_record(candidate, {node.id: node for node in load_node_catalog()}, {candidate.manifest.question_id})


def test_candidate_preview_has_dry_run_only_true(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/reviewed.yaml", question_id="cli-bld-007", draft_id="draft-reviewed", review=True)

    result = run_build_candidate_dry_run(build_args(root, "drafts/reviewed.yaml"))

    assert result.payload["dry_run_only"] is True


def test_candidate_not_written_to_formal_catalog(tmp_path: Path) -> None:
    before = formal_manifest_text()
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/reviewed.yaml", question_id="cli-bld-008", draft_id="draft-reviewed", review=True)

    run_build_candidate_dry_run(build_args(root, "drafts/reviewed.yaml"))

    assert formal_manifest_text() == before


def test_learner_api_cannot_fetch_dry_run_candidate(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/reviewed.yaml", question_id="cli-bld-009", draft_id="draft-reviewed", review=True)
    run_build_candidate_dry_run(build_args(root, "drafts/reviewed.yaml"))

    response = TestClient(create_app("learner")).get("/api/learner/v1/questions/cli-bld-009")

    assert response.status_code == 404


def test_hash_stable_through_dry_run_candidate_build(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/reviewed.yaml", question_id="cli-hsh-001", draft_id="draft-reviewed", review=True)

    result_a = run_build_candidate_dry_run(build_args(root, "drafts/reviewed.yaml"))
    result_b = run_build_candidate_dry_run(build_args(root, "drafts/reviewed.yaml"))

    assert result_a.payload["content_hash"] == result_b.payload["content_hash"]


def test_hash_excludes_authoring_metadata(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    data = draft_data("cli-hsh-002", "draft-one", review=True)
    changed = deepcopy(data)
    changed["candidate_record"]["trusted_scoring"]["authoring_metadata"] = {"note": "changed"}

    write_yaml(root / "drafts" / "one.yaml", data)
    write_yaml(root / "drafts" / "two.yaml", changed)
    draft_a = load_authoring_draft("drafts/one.yaml", root)
    draft_b = load_authoring_draft("drafts/two.yaml", root)

    assert compute_runtime_content_hash(draft_a.candidate_record) == compute_runtime_content_hash(draft_b.candidate_record)


def test_output_path_escape_rejected(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-out-001", draft_id="draft-one")

    result = run_validate_draft(validate_draft_args(root, "drafts/one.yaml", output="../escape.json"))

    assert result.exit_code == EXIT_PATH_ERROR


def test_formal_catalog_manifest_unchanged_after_commands(tmp_path: Path) -> None:
    before = formal_manifest_text()
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-safe-001", draft_id="draft-one", review=True)
    write_manifest(root, drafts=[{"draft_id": "draft-one", "path": "drafts/one.yaml"}])

    run_validate_draft(validate_draft_args(root, "drafts/one.yaml"))
    run_validate_batch(batch_args(root))
    run_build_candidate_dry_run(build_args(root, "drafts/one.yaml"))

    assert formal_manifest_text() == before


def test_source_metadata_not_in_learner_response() -> None:
    response = TestClient(create_app("learner")).get("/api/learner/v1/questions/ode-sep-001")

    assert response.status_code == 200
    assert "source_metadata" not in response.text
    assert "copyright_note" not in response.text


def test_report_does_not_include_long_source_text(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    long_source_text = "COPYRIGHTED SOURCE TEXT " * 50
    write_draft(root, "drafts/one.yaml", question_id="cli-rpt-001", draft_id="draft-one")
    write_manifest(
        root,
        default_source_metadata={
            "source_type": "manual",
            "source_name": "Short source ref",
            "author_notes": long_source_text,
            "copyright_note": "internal only",
        },
        drafts=[{"draft_id": "draft-one", "path": "drafts/one.yaml"}],
    )

    result = run_validate_batch(batch_args(root))

    assert long_source_text not in str(result.payload)
    assert "Short source ref" not in str(result.payload)


def test_default_formal_catalog_validates() -> None:
    YamlQuestionCatalogRepository().validate_catalog()


def test_learner_api_leak_regression() -> None:
    response = TestClient(create_app("learner")).get("/api/learner/v1/questions/ode-sep-001")

    assert response.status_code == 200
    assert "expected_answer" not in response.text
    assert "solution_outline" not in response.text
    assert "rubric" not in response.text


def test_app_profile_learner_internal_gating_regression() -> None:
    learner = TestClient(create_app("learner"))
    internal = TestClient(create_app("internal"))

    assert learner.get("/api/learner/v1/health").status_code == 200
    assert learner.get("/api/v1/health").status_code == 404
    assert internal.get("/api/v1/health").status_code == 200
    assert internal.get("/api/learner/v1/health").status_code == 404


def test_cli_main_smoke_validate_draft(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-main-001", draft_id="draft-one")

    exit_code = main(["--authoring-root", str(root), "validate-draft", "drafts/one.yaml"])

    assert exit_code == EXIT_SUCCESS


def test_cli_main_validate_draft_stdout_json_without_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-std-001", draft_id="draft-one")

    exit_code = main(["--authoring-root", str(root), "validate-draft", "drafts/one.yaml"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == EXIT_SUCCESS
    assert payload["dry_run_only"] is True


def test_cli_main_validate_draft_failure_stdout_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/bad.yaml", question_id="cli-std-002", draft_id="draft-bad", bad_hash=True)

    exit_code = main(["--authoring-root", str(root), "validate-draft", "drafts/bad.yaml"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == EXIT_VALIDATION_FAILED
    assert payload["validation_report"]["issues"][0]["error_code"] == "catalog_hash_error"


def test_cli_main_build_candidate_stdout_json_contains_hash(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/reviewed.yaml", question_id="cli-std-003", draft_id="draft-reviewed", review=True)

    exit_code = main(["--authoring-root", str(root), "build-candidate-dry-run", "--draft-path", "drafts/reviewed.yaml"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == EXIT_SUCCESS
    assert payload["dry_run_only"] is True
    assert payload["content_hash"].startswith("sha256:")


def test_cli_main_stdout_is_json_not_python_repr(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-std-004", draft_id="draft-one")

    main(["--authoring-root", str(root), "validate-draft", "drafts/one.yaml"])
    stdout = capsys.readouterr().out

    assert json.loads(stdout)["dry_run_only"] is True
    assert "'dry_run_only': True" not in stdout


def test_validate_draft_writes_report_only_under_reports(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-wrt-001", draft_id="draft-one")

    result = run_validate_draft(validate_draft_args(root, "drafts/one.yaml", output="report.json"))

    assert result.exit_code == EXIT_SUCCESS
    assert result.output_path is not None
    assert Path(result.output_path).relative_to(root / "reports")


def test_build_candidate_writes_preview_only_under_previews(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-wrt-002", draft_id="draft-one", review=True)

    result = run_build_candidate_dry_run(build_args(root, "drafts/one.yaml", output="preview.json"))

    assert result.exit_code == EXIT_SUCCESS
    assert result.output_path is not None
    assert Path(result.output_path).relative_to(root / "previews")


def test_build_candidate_from_manifest_and_draft_id(tmp_path: Path) -> None:
    root = authoring_root(tmp_path)
    write_draft(root, "drafts/one.yaml", question_id="cli-mbld-001", draft_id="draft-one", review=False)
    write_review(root, "reviews/one.yaml", complete=True)
    write_manifest(
        root,
        drafts=[{"draft_id": "draft-one", "path": "drafts/one.yaml", "review_checklist_path": "reviews/one.yaml"}],
    )

    args = Namespace(
        draft_path=None,
        manifest_path="import_manifest.yaml",
        draft_id="draft-one",
        authoring_root=root,
        output=None,
        debug=False,
    )
    result = run_build_candidate_dry_run(args)

    assert result.exit_code == EXIT_SUCCESS
    assert result.payload["candidate_record"]["manifest"]["question_id"] == "cli-mbld-001"


def authoring_root(tmp_path: Path) -> Path:
    root = tmp_path / "catalog_authoring"
    for child in ("drafts", "reviews", "reports", "previews"):
        (root / child).mkdir(parents=True, exist_ok=True)
    return root


def validate_draft_args(root: Path, draft_path: str, output: str | None = None) -> Namespace:
    return Namespace(draft_path=draft_path, authoring_root=root, output=output, debug=False)


def batch_args(root: Path, output: str | None = None) -> Namespace:
    return Namespace(manifest_path="import_manifest.yaml", authoring_root=root, output=output, debug=False)


def build_args(root: Path, draft_path: str, output: str | None = None) -> Namespace:
    return Namespace(
        draft_path=draft_path,
        manifest_path=None,
        draft_id=None,
        authoring_root=root,
        output=output,
        debug=False,
    )


def write_manifest(
    root: Path,
    *,
    drafts: list[dict[str, Any]],
    strict_mode: bool = True,
    default_source_metadata: dict[str, Any] | None = None,
    output_report_dir: str | None = None,
) -> None:
    data: dict[str, Any] = {
        "import_batch_id": "batch-001",
        "batch_name": "Test batch",
        "source_summary": "short internal source reference",
        "created_by": "test",
        "default_source_metadata": default_source_metadata,
        "drafts": drafts,
        "output_report_dir": output_report_dir,
        "strict_mode": strict_mode,
    }
    if default_source_metadata is None:
        data.pop("default_source_metadata")
    if output_report_dir is None:
        data.pop("output_report_dir")
    write_yaml(root / "import_manifest.yaml", data)


def write_review(root: Path, relative_path: str, *, complete: bool) -> None:
    write_yaml(root / relative_path, review_data(complete=complete))


def write_draft(
    root: Path,
    relative_path: str,
    *,
    question_id: str,
    draft_id: str,
    review: bool = False,
    rejected: bool = False,
    ai_assisted: bool = False,
    bad_hash: bool = False,
    source_name: str | None = None,
) -> None:
    write_yaml(
        root / relative_path,
        draft_data(
            question_id,
            draft_id,
            review=review,
            rejected=rejected,
            ai_assisted=ai_assisted,
            bad_hash=bad_hash,
            source_name=source_name,
        ),
    )


def draft_data(
    question_id: str,
    draft_id: str,
    *,
    review: bool = False,
    rejected: bool = False,
    ai_assisted: bool = False,
    bad_hash: bool = False,
    source_name: str | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "draft_id": draft_id,
        "status": "rejected" if rejected else "draft",
        "candidate_record": record_data(question_id, bad_hash=bad_hash),
        "ai_assisted": ai_assisted,
    }
    if review:
        data["review_checklist"] = review_data(complete=True)
    if source_name:
        data["source_metadata"] = {"source_type": "manual", "source_name": source_name, "copyright_note": "internal only"}
    return data


def review_data(*, complete: bool) -> dict[str, Any]:
    fields = {
        "math_i_scope_confirmed": complete,
        "module_topic_type_confirmed": complete,
        "node_id_confirmed": complete,
        "public_prompt_clear": complete,
        "expected_answer_checked": complete,
        "aliases_checked": complete,
        "solution_outline_checked": complete,
        "rubric_checked": complete,
        "target_dimensions_checked": complete,
        "validator_config_checked": complete,
        "no_public_leak_confirmed": complete,
        "question_id_version_checked": complete,
        "publish_approved": complete,
        "reviewer": "test-reviewer",
    }
    return fields


def record_data(question_id: str, *, bad_hash: bool = False) -> dict[str, Any]:
    return {
        "manifest": {
            "question_id": question_id,
            "logical_question_id": f"{question_id}-logic",
            "question_family_id": "clifam-001",
            "node_id": "ode_separable",
            "status": "draft",
            "audience": "learner",
            "question_version": "1.0",
            "rubric_version": "1.0",
            "answer_key_version": "1.0",
            "catalog_schema_version": "1.0",
            "tags": ["authoring-cli"],
            "content_hash": "bad-hash" if bad_hash else None,
        },
        "presentation": {
            "question_id": question_id,
            "node_id": "ode_separable",
            "title": "CLI authoring question",
            "stem": "Solve.",
            "prompt_markdown": "Solve dy/dx = 2xy and explain why separation applies.",
            "answer_format": "expression_with_reasoning",
            "response_step_mode": "optional",
            "difficulty": "basic",
            "display_assets": [],
            "hints_public": ["Look for separable variables."],
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
                    }
                ]
            },
            "solution_outline": "Separate dy/y = 2x dx, integrate to ln|y| = x^2 + C.",
            "validator_config": {"requires_constant": True},
            "scoring_notes_internal": "authoring CLI test",
            "golden_case_refs": [],
            "authoring_metadata": {"draft_note": "excluded from runtime hash"},
        },
    }


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def formal_manifest_text() -> str:
    return (Path(__file__).resolve().parents[1] / "catalog_data" / "manifest.yaml").read_text(encoding="utf-8")
