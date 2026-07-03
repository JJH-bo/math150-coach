from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from app.challenge.chapter_candidate_builder import deterministic_content_hash
from app.challenge.chapter_publish_plan import build_chapter_publish_plan_dry_run

CONTROLLED_PUBLISH_SCHEMA_VERSION = "chapter_controlled_publish_v1"
APPROVAL_PHRASE = "I_APPROVE_CHAPTER_CONTROLLED_PUBLISH"

ExecutionStatus = Literal["blocked", "dry_run_ready", "published", "rolled_back"]


@dataclass(frozen=True)
class PublishFileOperation:
    path: str
    content_hash: str
    action: Literal["create"]
    status: Literal["ready", "exists", "written", "rolled_back", "blocked"]
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "content_hash": self.content_hash,
            "action": self.action,
            "status": self.status,
            "reason": self.reason,
        }


def execute_chapter_controlled_publish(
    markdown: str,
    *,
    reviewer: str,
    decision: str,
    checklist: dict[str, bool] | None = None,
    notes: str | None = None,
    target_root: Path | None = None,
    allow_write: bool = False,
    approval_phrase: str | None = None,
    expected_publish_plan_hash: str | None = None,
) -> dict[str, Any]:
    """Execute the controlled publish phase, defaulting to non-writing dry-run.

    This is the first real publish-capable layer, but it is deliberately gated:
    - candidate build must pass;
    - candidate quality must pass;
    - publish plan must be ready;
    - writes require explicit approval phrase;
    - writes require the caller to pin the expected publish plan hash;
    - planned files use create-only semantics and refuse to overwrite existing files.
    """

    root = (target_root or Path.cwd()).resolve()
    plan = build_chapter_publish_plan_dry_run(
        markdown,
        reviewer=reviewer,
        decision=decision,
        checklist=checklist or {},
        notes=notes,
    )
    if plan.get("publish_plan_grade") != "ready":
        return _result("blocked", plan, [], ["publish_plan_not_ready"])

    plan_hash = str(plan.get("publish_plan_hash") or "")
    if expected_publish_plan_hash and expected_publish_plan_hash != plan_hash:
        return _result("blocked", plan, [], ["expected_publish_plan_hash_mismatch"])

    operations, path_errors = _planned_operations(plan, root)
    if path_errors:
        return _result("blocked", plan, operations, path_errors)

    existing = [operation.path for operation in operations if operation.status == "exists"]
    if existing:
        return _result("blocked", plan, operations, ["planned_file_already_exists"])

    if not allow_write:
        return _result("dry_run_ready", plan, operations, [])

    if approval_phrase != APPROVAL_PHRASE:
        return _result("blocked", plan, operations, ["approval_phrase_missing_or_invalid"])
    if expected_publish_plan_hash != plan_hash:
        return _result("blocked", plan, operations, ["expected_publish_plan_hash_required_for_write"])

    return _write_plan_files(plan, root, operations)


def _planned_operations(plan: dict[str, Any], root: Path) -> tuple[list[PublishFileOperation], list[str]]:
    operations: list[PublishFileOperation] = []
    errors: list[str] = []
    for planned in plan.get("planned_files", []):
        relative_path = str(planned.get("path") or "")
        if not _is_safe_relative_path(relative_path):
            errors.append(f"unsafe_planned_path:{relative_path}")
            operations.append(_operation(planned, "blocked", "unsafe_path"))
            continue
        target = (root / relative_path).resolve()
        if not _is_relative_to(target, root):
            errors.append(f"planned_path_escapes_target_root:{relative_path}")
            operations.append(_operation(planned, "blocked", "path_escapes_target_root"))
            continue
        if target.exists():
            operations.append(_operation(planned, "exists", "create_only_target_exists"))
        else:
            operations.append(_operation(planned, "ready", None))
    if not operations:
        errors.append("no_planned_files")
    return operations, errors


def _write_plan_files(plan: dict[str, Any], root: Path, operations: list[PublishFileOperation]) -> dict[str, Any]:
    written: list[Path] = []
    operation_by_path = {operation.path: operation for operation in operations}
    final_operations: list[PublishFileOperation] = []
    try:
        for planned in plan.get("planned_files", []):
            relative_path = str(planned["path"])
            target = (root / relative_path).resolve()
            content = str(planned.get("preview_content") or "")
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("x", encoding="utf-8") as file:
                file.write(content)
            written.append(target)
            final_operations.append(
                PublishFileOperation(
                    path=relative_path,
                    content_hash=str(planned.get("content_hash") or ""),
                    action="create",
                    status="written",
                )
            )
        return _result("published", plan, final_operations, [])
    except Exception as exc:  # pragma: no cover - defensive rollback path
        rollback_operations: list[PublishFileOperation] = []
        for path in reversed(written):
            relative = str(path.relative_to(root))
            try:
                path.unlink()
                rollback_operations.append(
                    PublishFileOperation(
                        path=relative,
                        content_hash=operation_by_path.get(relative, PublishFileOperation(relative, "", "create", "blocked")).content_hash,
                        action="create",
                        status="rolled_back",
                        reason="write_failure_rollback",
                    )
                )
            except Exception:
                rollback_operations.append(
                    PublishFileOperation(
                        path=relative,
                        content_hash="",
                        action="create",
                        status="blocked",
                        reason="rollback_failed",
                    )
                )
        return _result("rolled_back", plan, rollback_operations, [f"write_failed:{type(exc).__name__}"])


def _result(
    status: ExecutionStatus,
    plan: dict[str, Any],
    operations: list[PublishFileOperation],
    blocking_reasons: list[str],
) -> dict[str, Any]:
    return {
        "mode": "chapter_controlled_publish",
        "controlled_publish_schema_version": CONTROLLED_PUBLISH_SCHEMA_VERSION,
        "chapter_id": plan.get("chapter_id"),
        "status": status,
        "dry_run_only": status != "published",
        "formal_publish_executed": status == "published",
        "blocking_reasons": sorted(set(blocking_reasons)),
        "publish_plan_hash": plan.get("publish_plan_hash"),
        "candidate_content_hash": plan.get("content_hash"),
        "file_operations": [operation.to_dict() for operation in operations],
        "publish_manifest": _execution_manifest(status, plan, operations, blocking_reasons),
    }


def _execution_manifest(
    status: ExecutionStatus,
    plan: dict[str, Any],
    operations: list[PublishFileOperation],
    blocking_reasons: list[str],
) -> dict[str, Any]:
    manifest = {
        "controlled_publish_schema_version": CONTROLLED_PUBLISH_SCHEMA_VERSION,
        "chapter_id": plan.get("chapter_id"),
        "status": status,
        "publish_plan_hash": plan.get("publish_plan_hash"),
        "candidate_content_hash": plan.get("content_hash"),
        "blocking_reasons": sorted(set(blocking_reasons)),
        "file_operations": [operation.to_dict() for operation in operations],
    }
    manifest["execution_manifest_hash"] = deterministic_content_hash(manifest)
    return manifest


def _operation(planned: dict[str, Any], status: Literal["ready", "exists", "blocked"], reason: str | None) -> PublishFileOperation:
    return PublishFileOperation(
        path=str(planned.get("path") or ""),
        content_hash=str(planned.get("content_hash") or ""),
        action="create",
        status=status,
        reason=reason,
    )


def _is_safe_relative_path(path: str) -> bool:
    if not path or path.startswith("/") or "\x00" in path:
        return False
    parts = Path(path).parts
    return ".." not in parts


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
