from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

import yaml

from app.challenge.chapter_candidate_builder import build_chapter_candidate_dry_run, deterministic_content_hash

PublishPlanGrade = Literal["ready", "blocked"]

PUBLISH_PLAN_SCHEMA_VERSION = "chapter_publish_plan_v1"
FORMAL_PUBLISH_LOCK_REASON = "Formal publish remains locked; this endpoint only builds a dry-run publish plan."


@dataclass(frozen=True)
class PlannedFile:
    path: str
    content_format: Literal["yaml", "json"]
    content_hash: str
    write_mode: Literal["create_only", "update_requires_explicit_publish_phase"]
    preview_content: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "content_format": self.content_format,
            "content_hash": self.content_hash,
            "write_mode": self.write_mode,
            "preview_content": self.preview_content,
        }


def build_chapter_publish_plan_dry_run(
    markdown: str,
    *,
    reviewer: str,
    decision: str,
    checklist: dict[str, bool] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Build a dry-run publish plan from a reviewed candidate.

    This function intentionally does not write catalog files. It gives the future
    controlled-publish phase an exact manifest of what would be written, why it is
    blocked or ready, and which content hashes must be preserved.
    """

    candidate_result = build_chapter_candidate_dry_run(
        markdown,
        reviewer=reviewer,
        decision=decision,
        checklist=checklist or {},
        notes=notes,
    )
    candidate = candidate_result.get("candidate")
    candidate_quality = candidate_result.get("candidate_quality", {})
    chapter_id = candidate_result.get("chapter_id") or "chapter_draft"
    blocking_reasons = _blocking_reasons(candidate_result)

    if blocking_reasons or candidate is None:
        return {
            "mode": "chapter_publish_plan_dry_run",
            "workflow_stage": "publish_plan_dry_run",
            "publish_state": "publish_plan_blocked",
            "chapter_id": chapter_id,
            "publish_plan_schema_version": PUBLISH_PLAN_SCHEMA_VERSION,
            "dry_run_only": True,
            "formal_publish_allowed": False,
            "formal_publish_lock_reason": FORMAL_PUBLISH_LOCK_REASON,
            "publish_plan_grade": "blocked",
            "blocking_reasons": blocking_reasons or ["candidate_missing"],
            "candidate_summary": _candidate_summary(candidate_result),
            "planned_files": [],
            "required_next_action": "fix_candidate_gate_or_candidate_quality_before_publish_plan",
        }

    planned_files = _planned_files(chapter_id, candidate, candidate_result)
    plan_hash = _plan_hash(chapter_id, candidate_result, planned_files)
    return {
        "mode": "chapter_publish_plan_dry_run",
        "workflow_stage": "publish_plan_dry_run",
        "publish_state": "publish_plan_preview_only",
        "chapter_id": chapter_id,
        "publish_plan_schema_version": PUBLISH_PLAN_SCHEMA_VERSION,
        "dry_run_only": True,
        "formal_publish_allowed": False,
        "formal_publish_lock_reason": FORMAL_PUBLISH_LOCK_REASON,
        "publish_plan_grade": "ready",
        "blocking_reasons": [],
        "candidate_summary": _candidate_summary(candidate_result),
        "content_hash": candidate_result.get("content_hash"),
        "publish_plan_hash": plan_hash,
        "planned_files": [file.to_dict() for file in planned_files],
        "required_next_action": "codex_local_verify_then_user_approval_for_separate_controlled_publish_phase",
    }


def _blocking_reasons(candidate_result: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if candidate_result.get("candidate_build_allowed") is not True:
        reasons.append("candidate_build_not_allowed")
    gate = candidate_result.get("candidate_gate", {})
    reasons.extend(str(reason) for reason in gate.get("reasons", []) if reason)
    runtime = candidate_result.get("runtime_validation", {})
    if runtime.get("passed") is not True:
        reasons.append("runtime_validation_failed")
    quality = candidate_result.get("candidate_quality", {})
    if quality.get("grade") != "pass":
        reasons.append(f"candidate_quality:{quality.get('grade', 'missing')}")
    quality_gate = quality.get("candidate_publish_gate", {})
    reasons.extend(str(code) for code in quality_gate.get("blocking_codes", []) if code)
    return sorted(set(reasons))


def _candidate_summary(candidate_result: dict[str, Any]) -> dict[str, Any]:
    candidate = candidate_result.get("candidate") or {}
    graph = candidate.get("challenge_graph", {})
    quality = candidate_result.get("candidate_quality", {})
    return {
        "candidate_build_allowed": candidate_result.get("candidate_build_allowed"),
        "content_hash": candidate_result.get("content_hash"),
        "candidate_quality_grade": quality.get("grade"),
        "candidate_quality_score": quality.get("score"),
        "runtime_validation_passed": candidate_result.get("runtime_validation", {}).get("passed"),
        "counts": {
            "macro_nodes": len(graph.get("macro_nodes", [])),
            "micro_nodes": len(graph.get("micro_nodes", [])),
            "macro_challenges": len(graph.get("macro_challenges", [])),
            "atom_nodes": len(graph.get("atom_nodes", [])),
            "compare_nodes": len(graph.get("compare_nodes", [])),
            "guide_nodes": len(graph.get("guide_nodes", [])),
            "typed_edges": len(graph.get("typed_edges", [])),
        },
    }


def _planned_files(chapter_id: str, candidate: dict[str, Any], candidate_result: dict[str, Any]) -> list[PlannedFile]:
    challenge_graph_yaml = _yaml_dump(candidate["challenge_graph"])
    logic_graph_yaml = _yaml_dump(candidate["logic_graph"])
    manifest = _manifest(chapter_id, candidate_result, candidate)
    manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    base = f"backend/challenge_data/{chapter_id}"
    return [
        PlannedFile(
            path=f"{base}/challenge_graph.yaml",
            content_format="yaml",
            content_hash=deterministic_content_hash(candidate["challenge_graph"]),
            write_mode="create_only",
            preview_content=challenge_graph_yaml,
        ),
        PlannedFile(
            path=f"{base}/logic_graph.yaml",
            content_format="yaml",
            content_hash=deterministic_content_hash(candidate["logic_graph"]),
            write_mode="create_only",
            preview_content=logic_graph_yaml,
        ),
        PlannedFile(
            path=f"{base}/publish_manifest.json",
            content_format="json",
            content_hash=deterministic_content_hash(manifest),
            write_mode="create_only",
            preview_content=manifest_json,
        ),
    ]


def _manifest(chapter_id: str, candidate_result: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    quality = candidate_result.get("candidate_quality", {})
    return {
        "publish_plan_schema_version": PUBLISH_PLAN_SCHEMA_VERSION,
        "chapter_id": chapter_id,
        "content_schema_version": candidate.get("content_schema_version"),
        "candidate_content_hash": candidate_result.get("content_hash"),
        "candidate_quality_grade": quality.get("grade"),
        "candidate_quality_score": quality.get("score"),
        "formal_publish_allowed": False,
        "formal_publish_lock_reason": FORMAL_PUBLISH_LOCK_REASON,
        "source": "chapter_draft_candidate_dry_run",
    }


def _plan_hash(chapter_id: str, candidate_result: dict[str, Any], planned_files: list[PlannedFile]) -> str:
    return deterministic_content_hash(
        {
            "publish_plan_schema_version": PUBLISH_PLAN_SCHEMA_VERSION,
            "chapter_id": chapter_id,
            "candidate_content_hash": candidate_result.get("content_hash"),
            "planned_files": [
                {
                    "path": file.path,
                    "content_format": file.content_format,
                    "content_hash": file.content_hash,
                    "write_mode": file.write_mode,
                }
                for file in planned_files
            ],
            "formal_publish_allowed": False,
        }
    )


def _yaml_dump(value: dict[str, Any]) -> str:
    return yaml.safe_dump(value, allow_unicode=True, sort_keys=True)
