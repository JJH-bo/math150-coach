from __future__ import annotations

from copy import deepcopy
from typing import Any

from pydantic import ValidationError

from app.challenge.chapter_candidate_builder import deterministic_content_hash
from app.challenge.chapter_candidate_quality import evaluate_chapter_candidate_quality
from app.challenge.chapter_training_question_builder import build_chapter_training_question_package
from app.challenge.models import ChallengeGraph


CORRECTION_SCHEMA_VERSION = "chapter_correction_regeneration_v1"

COLLECTION_TARGETS = {
    "micro_node": ("challenge_graph", "micro_nodes"),
    "macro_node": ("challenge_graph", "macro_nodes"),
    "macro_challenge": ("challenge_graph", "macro_challenges"),
    "atom_node": ("challenge_graph", "atom_nodes"),
    "compare_node": ("challenge_graph", "compare_nodes"),
    "guide_node": ("challenge_graph", "guide_nodes"),
    "typed_edge": ("challenge_graph", "typed_edges"),
}


def build_chapter_correction_dry_run(
    candidate: dict[str, Any],
    *,
    corrections: list[dict[str, Any]],
    editor: str,
    notes: str | None = None,
) -> dict[str, Any]:
    """Patch a chapter candidate and regenerate dependent preview assets."""

    original_candidate = deepcopy(candidate)
    corrected_candidate = deepcopy(candidate)
    before_question_package = build_chapter_training_question_package(original_candidate)
    before_question_hashes = _question_hashes(before_question_package)
    before_candidate_hash = deterministic_content_hash(original_candidate)

    operation_errors: list[dict[str, str]] = []
    changed_paths: list[str] = []
    affected_node_ids: set[str] = set()
    for index, operation in enumerate(corrections):
        result = _apply_operation(corrected_candidate, operation)
        if result["error"]:
            operation_errors.append(
                {
                    "index": str(index),
                    "code": result["error"],
                    "target": str(operation.get("target", "")),
                    "message": result["message"],
                }
            )
            continue
        if result["changed_path"]:
            changed_paths.append(result["changed_path"])
        if result["node_id"]:
            affected_node_ids.add(result["node_id"])

    after_candidate_hash = deterministic_content_hash(corrected_candidate)
    runtime_validation = _runtime_validation_report(corrected_candidate.get("challenge_graph"))
    candidate_quality = evaluate_chapter_candidate_quality(
        corrected_candidate,
        content_hash=after_candidate_hash,
        runtime_validation=runtime_validation,
        formal_publish_allowed=False,
    )
    after_question_package = build_chapter_training_question_package(corrected_candidate)
    after_question_hashes = _question_hashes(after_question_package)
    changed_question_ids = _changed_question_ids(before_question_hashes, after_question_hashes)
    question_quality = after_question_package.get("quality_report", {})

    status = _correction_status(
        operation_errors=operation_errors,
        runtime_validation=runtime_validation,
        candidate_quality=candidate_quality,
        question_quality=question_quality,
    )
    return {
        "mode": "chapter_correction_dry_run",
        "workflow_stage": "chapter_package_correction",
        "correction_schema_version": CORRECTION_SCHEMA_VERSION,
        "dry_run_only": True,
        "formal_publish_allowed": False,
        "correction_record": {
            "record_id": _record_id(corrected_candidate, after_candidate_hash),
            "chapter_id": corrected_candidate.get("chapter_id"),
            "editor": editor,
            "status": status,
            "notes": notes,
            "operations": deepcopy(corrections),
            "operation_errors": operation_errors,
            "changed_paths": changed_paths,
        },
        "before": {
            "candidate_content_hash": before_candidate_hash,
            "question_bank_content_hash": deterministic_content_hash(before_question_hashes),
            "question_package_quality_grade": before_question_package.get("quality_report", {}).get("grade"),
        },
        "after": {
            "candidate_content_hash": after_candidate_hash,
            "candidate": corrected_candidate,
            "runtime_validation": runtime_validation,
            "candidate_quality": candidate_quality,
            "question_package": after_question_package,
            "question_bank_content_hash": deterministic_content_hash(after_question_hashes),
        },
        "diff": {
            "changed_paths": changed_paths,
            "changed_question_ids": changed_question_ids,
            "added_question_ids": sorted(set(after_question_hashes) - set(before_question_hashes)),
            "removed_question_ids": sorted(set(before_question_hashes) - set(after_question_hashes)),
        },
        "affected_content": {
            "node_ids": sorted(affected_node_ids),
            "question_ids": changed_question_ids,
        },
        "regeneration_scope": _regeneration_scope(changed_paths, changed_question_ids),
        "required_next_action": _required_next_action(status),
    }


def _apply_operation(candidate: dict[str, Any], operation: dict[str, Any]) -> dict[str, str | None]:
    if operation.get("op") != "replace":
        return _operation_result(error="unsupported_operation", message="Only replace operations are supported.")

    target = str(operation.get("target") or "")
    field = str(operation.get("field") or "")
    if not field:
        return _operation_result(error="field_missing", message="Correction field is required.")

    if target == "chapter":
        return _replace_chapter_field(candidate, field, operation.get("value"))
    if target == "material_evidence":
        candidate.setdefault("material_evidence", {})
        candidate["material_evidence"][field] = deepcopy(operation.get("value"))
        return _operation_result(changed_path=f"material_evidence.{field}")
    if target == "error_repair_map":
        value = deepcopy(operation.get("value"))
        candidate.setdefault("error_repair_map", {})[field] = value
        candidate.setdefault("challenge_graph", {}).setdefault("error_to_micro_mapping", {})[field] = value
        return _operation_result(changed_path=f"challenge_graph.error_to_micro_mapping.{field}", node_id=str(value))
    if target in COLLECTION_TARGETS:
        return _replace_collection_field(candidate, target, operation, field)
    return _operation_result(error="unsupported_target", message=f"Unsupported correction target: {target}")


def _replace_chapter_field(candidate: dict[str, Any], field: str, value: Any) -> dict[str, str | None]:
    candidate[field] = deepcopy(value)
    changed_path = f"{field}"
    if field == "title":
        graph = candidate.setdefault("challenge_graph", {})
        logic_graph = candidate.setdefault("logic_graph", {})
        graph["title"] = value
        logic_graph["title"] = value
        changed_path = "title"
    return _operation_result(changed_path=changed_path)


def _replace_collection_field(
    candidate: dict[str, Any],
    target: str,
    operation: dict[str, Any],
    field: str,
) -> dict[str, str | None]:
    item_id = str(operation.get("id") or "")
    if not item_id:
        return _operation_result(error="id_missing", message=f"{target} corrections require an id.")
    graph_key, collection_key = COLLECTION_TARGETS[target]
    collection = candidate.get(graph_key, {}).get(collection_key, [])
    if not isinstance(collection, list):
        return _operation_result(error="collection_missing", message=f"Candidate collection is missing: {collection_key}")
    for item in collection:
        if isinstance(item, dict) and item.get("id") == item_id:
            item[field] = deepcopy(operation.get("value"))
            return _operation_result(
                changed_path=f"{graph_key}.{collection_key}[{item_id}].{field}",
                node_id=item_id,
            )
    return _operation_result(error="id_not_found", message=f"{target} not found: {item_id}")


def _runtime_validation_report(challenge_graph: Any) -> dict[str, Any]:
    if not isinstance(challenge_graph, dict):
        return {"passed": False, "errors": ["candidate challenge_graph is missing"], "warnings": []}
    try:
        ChallengeGraph.model_validate(challenge_graph)
    except ValidationError as exc:
        return {
            "passed": False,
            "errors": [str(error.get("msg", "candidate runtime validation failed")) for error in exc.errors()],
            "warnings": [],
        }
    except ValueError as exc:
        return {"passed": False, "errors": [str(exc)], "warnings": []}
    return {"passed": True, "errors": [], "warnings": []}


def _question_hashes(question_package: dict[str, Any]) -> dict[str, str]:
    question_bank = question_package.get("question_bank")
    if not isinstance(question_bank, dict):
        return {}
    questions = question_bank.get("questions")
    if not isinstance(questions, list):
        return {}
    hashes: dict[str, str] = {}
    for question in questions:
        if isinstance(question, dict) and question.get("id"):
            hashes[str(question["id"])] = deterministic_content_hash(question)
    return hashes


def _changed_question_ids(before: dict[str, str], after: dict[str, str]) -> list[str]:
    ids = set(before) | set(after)
    return sorted(question_id for question_id in ids if before.get(question_id) != after.get(question_id))


def _correction_status(
    *,
    operation_errors: list[dict[str, str]],
    runtime_validation: dict[str, Any],
    candidate_quality: dict[str, Any],
    question_quality: dict[str, Any],
) -> str:
    if operation_errors:
        return "blocked"
    if runtime_validation.get("passed") is not True:
        return "blocked"
    if candidate_quality.get("grade") != "pass":
        return "blocked"
    if question_quality.get("grade") != "pass":
        return "blocked"
    return "accepted"


def _regeneration_scope(changed_paths: list[str], changed_question_ids: list[str]) -> list[str]:
    scope = ["candidate", "quality_report"]
    if changed_question_ids or changed_paths:
        scope.extend(["questions.yaml", "publish_manifest"])
    return scope


def _record_id(candidate: dict[str, Any], candidate_hash: str) -> str:
    chapter_id = str(candidate.get("chapter_id") or "chapter")
    digest = candidate_hash.removeprefix("sha256:")[:12]
    return f"{chapter_id}.correction.{digest}"


def _required_next_action(status: str) -> str:
    if status == "accepted":
        return "review_correction_diff_then_build_publish_plan_dry_run"
    return "fix_correction_errors_before_regeneration"


def _operation_result(
    *,
    changed_path: str | None = None,
    node_id: str | None = None,
    error: str | None = None,
    message: str = "",
) -> dict[str, str | None]:
    return {
        "changed_path": changed_path,
        "node_id": node_id,
        "error": error,
        "message": message,
    }
