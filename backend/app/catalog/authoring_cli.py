from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.api.v1.nodes import load_node_catalog
from app.catalog.authoring_io import (
    AuthoringParseError,
    AuthoringPathError,
    load_authoring_draft,
    load_import_manifest,
    load_review_checklist,
    resolve_inside,
    validation_error_message,
    write_json_report,
    write_yaml_preview,
)
from app.catalog.authoring_models import AuthoringDraft, AuthoringStatus
from app.catalog.authoring_workflow import CatalogAuthoringWorkflow
from app.catalog.batch_report import BatchDraftResult, BatchReport
from app.catalog.import_manifest import ImportDraftEntry, ImportManifest, merge_source_metadata


EXIT_SUCCESS = 0
EXIT_VALIDATION_FAILED = 1
EXIT_SCHEMA_OR_PARSE_ERROR = 2
EXIT_PATH_ERROR = 3
EXIT_HUMAN_REVIEW_FAILED = 4
EXIT_INTERNAL_ERROR = 5


@dataclass(frozen=True)
class CliResult:
    exit_code: int
    payload: dict[str, Any]
    output_path: str | None = None
    error_message: str | None = None


def run_validate_draft(args: argparse.Namespace) -> CliResult:
    try:
        draft = load_authoring_draft(args.draft_path, args.authoring_root)
        report = CatalogAuthoringWorkflow().validate_draft(draft, load_node_catalog())
        payload = {"dry_run_only": True, "validation_report": report.model_dump(mode="json")}
        output_path = _write_optional_json(payload, args.output, args.authoring_root, "reports")
        return CliResult(
            exit_code=EXIT_SUCCESS if report.passed else EXIT_VALIDATION_FAILED,
            payload=payload,
            output_path=output_path,
        )
    except AuthoringPathError as exc:
        return _path_error(exc, debug=args.debug)
    except (AuthoringParseError, ValidationError, ValueError) as exc:
        return _schema_error(exc, debug=args.debug)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return _internal_error(exc, debug=args.debug)


def run_validate_batch(args: argparse.Namespace) -> CliResult:
    try:
        manifest = load_import_manifest(args.manifest_path, args.authoring_root)
        report = _validate_batch_manifest(manifest, args.authoring_root)
        payload = report.model_dump(mode="json")
        output_root = _report_root(args.authoring_root, manifest.output_report_dir)
        output_path = _write_optional_json(payload, args.output, output_root, ".")
        exit_code = EXIT_VALIDATION_FAILED if manifest.strict_mode and report.failed else EXIT_SUCCESS
        return CliResult(exit_code=exit_code, payload=payload, output_path=output_path)
    except AuthoringPathError as exc:
        return _path_error(exc, debug=args.debug)
    except (AuthoringParseError, ValidationError) as exc:
        return _schema_error(exc, debug=args.debug)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return _internal_error(exc, debug=args.debug)


def run_build_candidate_dry_run(args: argparse.Namespace) -> CliResult:
    try:
        draft = _load_build_target(args)
        if draft.status == AuthoringStatus.REJECTED:
            payload = {
                "dry_run_only": True,
                "error_code": "human_review_gate_failed",
                "message": "rejected drafts cannot build publish candidate previews",
                "draft_id": draft.draft_id,
            }
            return CliResult(exit_code=EXIT_HUMAN_REVIEW_FAILED, payload=payload, error_message=payload["message"])
        authoring = CatalogAuthoringWorkflow()
        validation_report = authoring.validate_draft(draft, load_node_catalog())
        if not validation_report.passed:
            payload = {"dry_run_only": True, "validation_report": validation_report.model_dump(mode="json")}
            return CliResult(exit_code=EXIT_VALIDATION_FAILED, payload=payload, error_message="validation failed")
        if draft.status == AuthoringStatus.REJECTED or not authoring.require_human_review(draft):
            payload = {
                "dry_run_only": True,
                "error_code": "human_review_gate_failed",
                "message": "complete human review is required before building a publish candidate",
                "draft_id": draft.draft_id,
            }
            return CliResult(exit_code=EXIT_HUMAN_REVIEW_FAILED, payload=payload, error_message=payload["message"])

        candidate = authoring.build_publish_candidate(draft, load_node_catalog())
        payload = {
            "dry_run_only": True,
            "candidate_record": candidate.model_dump(mode="json"),
            "content_hash": candidate.manifest.content_hash,
        }
        output_path = _write_optional_preview(payload, args.output, args.authoring_root)
        return CliResult(exit_code=EXIT_SUCCESS, payload=payload, output_path=output_path)
    except AuthoringPathError as exc:
        return _path_error(exc, debug=args.debug)
    except (AuthoringParseError, ValidationError, ValueError) as exc:
        return _schema_error(exc, debug=args.debug)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        return _internal_error(exc, debug=args.debug)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m app.catalog.authoring_cli")
    parser.add_argument("--authoring-root", default=".", help="Root directory for authoring drafts and reports.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_draft = subparsers.add_parser("validate-draft")
    validate_draft.add_argument("draft_path")
    validate_draft.add_argument("--output")
    validate_draft.add_argument("--debug", action="store_true")
    validate_draft.set_defaults(handler=run_validate_draft)

    validate_batch = subparsers.add_parser("validate-batch")
    validate_batch.add_argument("manifest_path")
    validate_batch.add_argument("--output")
    validate_batch.add_argument("--debug", action="store_true")
    validate_batch.set_defaults(handler=run_validate_batch)

    build_candidate = subparsers.add_parser("build-candidate-dry-run")
    build_target = build_candidate.add_mutually_exclusive_group(required=True)
    build_target.add_argument("--draft-path")
    build_target.add_argument("--manifest-path")
    build_candidate.add_argument("--draft-id")
    build_candidate.add_argument("--output")
    build_candidate.add_argument("--debug", action="store_true")
    build_candidate.set_defaults(handler=run_build_candidate_dry_run)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result: CliResult = args.handler(args)
    payload = dict(result.payload)
    if result.output_path:
        payload["output_path"] = result.output_path
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    return result.exit_code


def _validate_batch_manifest(manifest: ImportManifest, authoring_root: str | Path) -> BatchReport:
    per_draft_results: list[BatchDraftResult] = []
    issues = []
    for entry in manifest.drafts:
        try:
            draft = _load_manifest_draft(entry, manifest, authoring_root)
            report = CatalogAuthoringWorkflow().validate_draft(draft, load_node_catalog())
            review_status = "ready" if draft.review_checklist and draft.review_checklist.is_publish_ready() else "missing_or_incomplete"
            per_draft_results.append(
                BatchDraftResult(
                    draft_id=draft.draft_id,
                    question_id=draft.candidate_record.manifest.question_id,
                    status="validation_passed" if report.passed else "validation_failed",
                    validation_report=report,
                    human_review_status=review_status,
                )
            )
        except (AuthoringParseError, AuthoringPathError, ValidationError, ValueError) as exc:
            message = validation_error_message(exc) if isinstance(exc, ValidationError) else str(exc)
            per_draft_results.append(
                BatchDraftResult(
                    draft_id=entry.draft_id,
                    status="load_failed",
                    validation_report=None,
                    human_review_status="unknown",
                )
            )
            from app.catalog.validation_report import ValidationIssue

            issues.append(
                ValidationIssue(
                    error_code="authoring_draft_load_error",
                    message=message,
                    candidate_id=entry.expected_question_id,
                    batch_id=manifest.import_batch_id,
                )
            )

    passed = sum(1 for result in per_draft_results if result.status == "validation_passed")
    failed = len(per_draft_results) - passed
    return BatchReport(
        import_batch_id=manifest.import_batch_id,
        total=len(per_draft_results),
        passed=passed,
        failed=failed,
        candidates_built=0,
        issues=issues,
        per_draft_results=per_draft_results,
    )


def _load_manifest_draft(entry: ImportDraftEntry, manifest: ImportManifest, authoring_root: str | Path) -> AuthoringDraft:
    draft = load_authoring_draft(entry.path, authoring_root)
    if entry.draft_id != draft.draft_id:
        raise ValueError(f"manifest draft_id does not match draft file: {entry.draft_id}")
    if entry.expected_question_id and entry.expected_question_id != draft.candidate_record.manifest.question_id:
        raise ValueError("expected_question_id does not match draft candidate question_id")
    source_metadata = merge_source_metadata(manifest.default_source_metadata, entry.source_metadata_override)
    if source_metadata is not None:
        draft.source_metadata = source_metadata
    if entry.review_checklist_path:
        draft.review_checklist = load_review_checklist(entry.review_checklist_path, authoring_root)
    if entry.ai_assisted is not None:
        draft.ai_assisted = entry.ai_assisted
    if draft.import_batch_id is None:
        draft.import_batch_id = manifest.import_batch_id
    return draft


def _load_build_target(args: argparse.Namespace) -> AuthoringDraft:
    if args.draft_path:
        return load_authoring_draft(args.draft_path, args.authoring_root)
    if not args.draft_id:
        raise ValueError("--draft-id is required when using --manifest-path")
    manifest = load_import_manifest(args.manifest_path, args.authoring_root)
    for entry in manifest.drafts:
        if entry.draft_id == args.draft_id:
            return _load_manifest_draft(entry, manifest, args.authoring_root)
    raise ValueError(f"draft_id not found in import manifest: {args.draft_id}")


def _report_root(authoring_root: str | Path, output_report_dir: str | None = None) -> Path:
    reports_root = Path(authoring_root) / "reports"
    if not output_report_dir:
        return reports_root
    report_subdir = Path(output_report_dir)
    if report_subdir.is_absolute():
        raise AuthoringPathError("output_report_dir must be relative to authoring reports root")
    if report_subdir.parts and report_subdir.parts[0] == "reports":
        raise AuthoringPathError("output_report_dir must be a subdirectory below reports, not reports itself")
    return resolve_inside(report_subdir, reports_root, label="output_report_dir", must_exist=False)


def _write_optional_json(payload: dict[str, Any], output: str | None, authoring_root: str | Path, default_dir: str) -> str | None:
    if not output:
        return None
    allowed_root = Path(authoring_root) / default_dir
    written = write_json_report(payload, output, allowed_root)
    return str(written)


def _write_optional_preview(payload: dict[str, Any], output: str | None, authoring_root: str | Path) -> str | None:
    if not output:
        return None
    output_path = Path(output)
    allowed_root = Path(authoring_root) / "previews"
    if output_path.suffix.lower() in {".yaml", ".yml"}:
        written = write_yaml_preview(payload, output, allowed_root)
    else:
        written = write_json_report(payload, output, allowed_root)
    return str(written)


def _schema_error(exc: Exception, *, debug: bool) -> CliResult:
    message = validation_error_message(exc) if isinstance(exc, ValidationError) else str(exc)
    payload = {"dry_run_only": True, "error_code": "schema_or_parse_error", "message": message}
    if debug:
        payload["debug"] = repr(exc)
    return CliResult(exit_code=EXIT_SCHEMA_OR_PARSE_ERROR, payload=payload, error_message=message)


def _path_error(exc: Exception, *, debug: bool) -> CliResult:
    payload = {"dry_run_only": True, "error_code": "path_or_file_access_error", "message": str(exc)}
    if debug:
        payload["debug"] = repr(exc)
    return CliResult(exit_code=EXIT_PATH_ERROR, payload=payload, error_message=str(exc))


def _internal_error(exc: Exception, *, debug: bool) -> CliResult:
    payload = {"dry_run_only": True, "error_code": "internal_unexpected_error", "message": "unexpected authoring CLI error"}
    if debug:
        payload["debug"] = repr(exc)
    return CliResult(exit_code=EXIT_INTERNAL_ERROR, payload=payload, error_message=str(exc))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
