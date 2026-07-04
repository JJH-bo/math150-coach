from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any

from pydantic import ValidationError

from app.challenge.chapter_candidate_quality import evaluate_chapter_candidate_quality
from app.challenge.chapter_draft_importer import record_chapter_human_review, validate_chapter_markdown
from app.challenge.models import ChallengeGraph
from app.training.session_log import TRUSTED_FIELD_DENYLIST

CONTENT_SCHEMA_VERSION = "chapter_candidate_v1"

EDGE_TYPE_MAP = {
    "requires": "prerequisite",
    "supports": "support",
    "derives_to": "bridge",
    "transforms_to": "bridge",
    "contrasts_with": "confusion",
    "commonly_confused_with": "confusion",
    "checks": "assesses",
    "repairs": "repair",
    "transfers_to": "transfers_to",
    "boss_checks": "boss_covers",
    "blocks": "blocks",
}

GUIDE_KIND_BY_LOGIC_KIND = {
    "transfer_node": "bridge",
    "synthesis_node": "boss_gate",
}


class ChapterCandidateBuildError(ValueError):
    """Raised when a chapter candidate dry run cannot be produced."""


def build_chapter_candidate_dry_run(
    markdown: str,
    *,
    reviewer: str,
    decision: str,
    checklist: dict[str, bool] | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic candidate preview without publishing anything.

    This is the high gate between authoring drafts and any future formal publish.
    The function intentionally records a human review and rebuilds validation from the
    markdown so the candidate content hash never depends on reviewer identity, notes,
    timestamps, or other authoring metadata.
    """

    validation = validate_chapter_markdown(markdown)
    review = record_chapter_human_review(
        markdown,
        reviewer=reviewer,
        decision=decision,
        checklist=checklist or {},
        notes=notes,
    )
    gate = _candidate_gate(validation, review)
    if not gate["allowed"]:
        return _blocked_payload(validation, review, gate)

    draft = validation["draft"]
    candidate = _candidate_payload_from_draft(draft)
    runtime_report = _runtime_validation_report(candidate["challenge_graph"])
    if not runtime_report["passed"]:
        gate = {
            "allowed": False,
            "status": "blocked_by_runtime_candidate_validation",
            "reasons": runtime_report["errors"],
        }
        return _blocked_payload(validation, review, gate, runtime_report=runtime_report)

    content_hash = deterministic_content_hash(candidate)
    candidate_quality = evaluate_chapter_candidate_quality(
        candidate,
        content_hash=content_hash,
        runtime_validation=runtime_report,
        formal_publish_allowed=False,
    )
    return {
        "mode": "chapter_candidate_build_dry_run",
        "workflow_stage": "candidate_dry_run",
        "publish_state": "candidate_preview_only",
        "chapter_id": draft.get("chapter_id"),
        "dry_run_only": True,
        "formal_publish_allowed": False,
        "candidate_build_allowed": True,
        "candidate_gate": gate,
        "candidate_quality": candidate_quality,
        "content_schema_version": CONTENT_SCHEMA_VERSION,
        "content_hash": content_hash,
        "hash_algorithm": "sha256",
        "hash_excludes": [
            "reviewer",
            "review notes",
            "authoring timestamps",
            "validation issue wording order outside canonical content",
            "UI preview state",
        ],
        "candidate": candidate,
        "runtime_validation": runtime_report,
        "validation": {
            "report": validation["report"],
            "readiness": validation["readiness"],
        },
        "human_review": {
            "status": review["review_record"]["status"],
            "missing_checklist_codes": review["review_record"]["missing_checklist_codes"],
            "blocking_issue_count": review["review_record"]["blocking_issue_count"],
        },
    }


def deterministic_content_hash(candidate: dict[str, Any]) -> str:
    canonical = canonical_content(candidate)
    encoded = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(encoded.encode('utf-8')).hexdigest()}"


def canonical_content(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: canonical_content(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        normalized = [canonical_content(item) for item in value]
        if all(isinstance(item, dict) and "id" in item for item in normalized):
            return sorted(normalized, key=lambda item: str(item["id"]))
        if all(not isinstance(item, (dict, list)) for item in normalized):
            return sorted(normalized, key=lambda item: str(item))
        return normalized
    return value


def _candidate_gate(validation: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    report = validation.get("report", {})
    review_record = review.get("review_record", {})
    if int(report.get("error_count", 0) or 0):
        reasons.append("validation_errors_present")
    if review_record.get("status") != "approved_for_candidate":
        reasons.append(f"human_review_status:{review_record.get('status')}")
    if review_record.get("missing_checklist_codes"):
        reasons.append("human_review_checklist_incomplete")
    return {
        "allowed": not reasons,
        "status": "allowed_for_candidate_dry_run" if not reasons else "blocked",
        "reasons": reasons,
    }


def _blocked_payload(
    validation: dict[str, Any],
    review: dict[str, Any],
    gate: dict[str, Any],
    *,
    runtime_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    draft = validation.get("draft", {})
    runtime_validation = runtime_report or {"passed": False, "errors": [], "warnings": []}
    return {
        "mode": "chapter_candidate_build_dry_run",
        "workflow_stage": "candidate_dry_run",
        "publish_state": "draft_only",
        "chapter_id": draft.get("chapter_id"),
        "dry_run_only": True,
        "formal_publish_allowed": False,
        "candidate_build_allowed": False,
        "candidate_gate": gate,
        "candidate_quality": evaluate_chapter_candidate_quality(
            None,
            content_hash=None,
            runtime_validation=runtime_validation,
            formal_publish_allowed=False,
        ),
        "content_schema_version": CONTENT_SCHEMA_VERSION,
        "content_hash": None,
        "hash_algorithm": "sha256",
        "candidate": None,
        "runtime_validation": runtime_validation,
        "validation": {
            "report": validation.get("report"),
            "readiness": validation.get("readiness"),
        },
        "human_review": {
            "status": review.get("review_record", {}).get("status"),
            "missing_checklist_codes": review.get("review_record", {}).get("missing_checklist_codes", []),
            "blocking_issue_count": review.get("review_record", {}).get("blocking_issue_count"),
        },
    }


def _candidate_payload_from_draft(draft: dict[str, Any]) -> dict[str, Any]:
    challenge_graph = _runtime_challenge_graph_from_draft(draft)
    logic_graph = _logic_graph_from_draft(draft)
    candidate = {
        "content_schema_version": CONTENT_SCHEMA_VERSION,
        "chapter_id": draft["chapter_id"],
        "title": draft["title"],
        "challenge_graph": challenge_graph,
        "logic_graph": logic_graph,
        "material_evidence": _material_evidence_from_draft(draft),
        "error_repair_map": _error_repair_mapping(draft),
    }
    return canonical_content(_candidate_safe_content(candidate))


def _material_evidence_from_draft(draft: dict[str, Any]) -> dict[str, Any]:
    evidence = draft.get("source_evidence")
    if not isinstance(evidence, dict):
        return {}
    allowed_keys = {
        "chapter_topic",
        "subject_area",
        "core_concepts",
        "core_formulas",
        "core_theorems",
        "typical_problem_types",
        "entry_triggers",
        "method_choices",
        "key_transformations",
        "confusions",
        "common_errors",
        "prerequisites",
        "downstream_uses",
        "math1_value",
        "false_pass_risks",
    }
    return {
        key: deepcopy(value)
        for key, value in evidence.items()
        if key in allowed_keys and value
    }


def _candidate_safe_content(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _candidate_safe_content(child)
            for key, child in value.items()
            if key not in TRUSTED_FIELD_DENYLIST
        }
    if isinstance(value, list):
        return [_candidate_safe_content(item) for item in value]
    return value


def _runtime_challenge_graph_from_draft(draft: dict[str, Any]) -> dict[str, Any]:
    macro_nodes = deepcopy(draft.get("macro_nodes", []))
    micro_nodes = [
        {
            "id": node["id"],
            "macro_node_id": node["macro_node_id"],
            "type": node["type"],
            "title": node["title"],
            "description": node.get("description", ""),
            "default_dimensions": _default_dimensions_for_micro_type(node.get("type", "")),
        }
        for node in draft.get("micro_nodes", [])
    ]
    macro_challenges = [
        {
            "id": challenge["id"],
            "macro_node_id": challenge["macro_node_id"],
            "title": challenge["title"],
            "covers_micro_nodes": list(challenge.get("covers_micro_nodes", [])),
            "target_dimensions": _dimensions_for_micro_ids(draft, challenge.get("covers_micro_nodes", [])),
        }
        for challenge in draft.get("macro_challenges", [])
    ]
    return {
        "chapter_id": draft["chapter_id"],
        "title": draft["title"],
        "attempt_limits": {"micro_node": 5, "macro_challenge": 3},
        "macro_nodes": macro_nodes,
        "micro_nodes": micro_nodes,
        "macro_challenges": macro_challenges,
        "atom_nodes": _atom_nodes_from_logic(draft),
        "compare_nodes": _compare_nodes_from_logic(draft),
        "guide_nodes": _guide_nodes_from_logic(draft),
        "typed_edges": _typed_edges_from_draft(draft),
        "contains": _contains_map(draft),
        "unlock_edges": _unlock_edges(draft),
        "error_to_micro_mapping": _error_repair_mapping(draft),
    }


def _logic_graph_from_draft(draft: dict[str, Any]) -> dict[str, Any]:
    return {
        "chapter_id": draft["chapter_id"],
        "title": f"{draft['title']} 逻辑能力网",
        "abilities": deepcopy(draft.get("logic_nodes", [])),
        "edges": deepcopy(draft.get("logic_edges", [])),
        "visibility_policy": "authoring_candidate_preview",
    }


def _contains_map(draft: dict[str, Any]) -> dict[str, list[str]]:
    contains: dict[str, list[str]] = {node["id"]: [] for node in draft.get("macro_nodes", [])}
    for micro in draft.get("micro_nodes", []):
        contains.setdefault(micro["macro_node_id"], []).append(micro["id"])
    return {key: sorted(value) for key, value in contains.items()}


def _unlock_edges(draft: dict[str, Any]) -> list[dict[str, Any]]:
    macros = [node["id"] for node in draft.get("macro_nodes", [])]
    contains = _contains_map(draft)
    edges: list[dict[str, Any]] = []
    for index, macro_id in enumerate(macros[:-1]):
        next_macro = macros[index + 1]
        edges.append({"from_macro_node_id": macro_id, "to_micro_node_ids": contains.get(next_macro, [])})
    return edges


def _error_repair_mapping(draft: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in draft.get("error_repair_map", []):
        root = item.get("root_cause")
        target = item.get("repair_target_node_id")
        if root and target:
            mapping[root] = target
    return mapping


def _atom_nodes_from_logic(draft: dict[str, Any]) -> list[dict[str, Any]]:
    atoms: list[dict[str, Any]] = []
    for node in draft.get("logic_nodes", []):
        if node.get("node_kind") != "hidden_ability":
            continue
        atoms.append(
            {
                "id": node["id"],
                "micro_node_id": node["repair_target_node_id"],
                "title": node.get("title", ""),
                "description": node.get("why_exists", ""),
                "dimensions": _clean_dimensions(node.get("dimensions", [])),
                "repair_cues": list(node.get("failure_modes", [])),
            }
        )
    return atoms


def _compare_nodes_from_logic(draft: dict[str, Any]) -> list[dict[str, Any]]:
    compares: list[dict[str, Any]] = []
    for node in draft.get("logic_nodes", []):
        if node.get("node_kind") != "compare_guard":
            continue
        compares.append(
            {
                "id": node["id"],
                "title": node.get("title", ""),
                "node_ids": list(node.get("node_ids", [])),
                "description": node.get("contrast", ""),
                "focus_dimensions": [],
                "confusion_cues": [node.get("contrast", "")] if node.get("contrast") else [],
            }
        )
    return compares


def _guide_nodes_from_logic(draft: dict[str, Any]) -> list[dict[str, Any]]:
    guides: list[dict[str, Any]] = []
    for node in draft.get("logic_nodes", []):
        node_kind = node.get("node_kind")
        if node_kind not in GUIDE_KIND_BY_LOGIC_KIND:
            continue
        related = [node_id for node_id in [node.get("owner_node_id"), node.get("repair_target_node_id")] if node_id]
        guides.append(
            {
                "id": node["id"],
                "kind": GUIDE_KIND_BY_LOGIC_KIND[node_kind],
                "title": node.get("title", ""),
                "description": node.get("why_exists", ""),
                "related_node_ids": related,
                "focus_dimensions": _clean_dimensions(node.get("dimensions", [])),
                "map_hint": node.get("why_exists", ""),
                "trainable": False,
            }
        )
    return guides


def _typed_edges_from_draft(draft: dict[str, Any]) -> list[dict[str, Any]]:
    typed: list[dict[str, Any]] = []
    for edge in draft.get("logic_edges", []):
        raw_type = edge.get("edge_type", "")
        mapped = EDGE_TYPE_MAP.get(raw_type, "bridge")
        typed.append(
            {
                "id": edge["id"],
                "edge_type": mapped,
                "source_id": edge.get("source_id", ""),
                "target_id": edge.get("target_id", ""),
                "label": raw_type,
                "reason": edge.get("reason", ""),
                "semantic_weight": 1,
                "decision_role": _decision_role_for_edge(mapped),
                "visible": mapped in {"prerequisite", "confusion", "boss_covers", "transfers_to"},
            }
        )
    return typed


def _decision_role_for_edge(edge_type: str) -> str:
    if edge_type == "repair":
        return "repair"
    if edge_type in {"support", "assesses", "boss_covers"}:
        return "diagnostic"
    if edge_type in {"prerequisite", "transfers_to"}:
        return "progression"
    return "navigation"


def _runtime_validation_report(challenge_graph: dict[str, Any]) -> dict[str, Any]:
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


def _dimensions_for_micro_ids(draft: dict[str, Any], micro_ids: list[str]) -> list[str]:
    by_id = {node["id"]: node for node in draft.get("micro_nodes", [])}
    dimensions: list[str] = []
    for micro_id in micro_ids:
        dimensions.extend(_default_dimensions_for_micro_type(by_id.get(micro_id, {}).get("type", "")))
    return sorted(set(dimensions))


def _default_dimensions_for_micro_type(micro_type: str) -> list[str]:
    defaults = {
        "concept": ["concept"],
        "trigger": ["trigger"],
        "method": ["method"],
        "transformation": ["transformation"],
        "calculation": ["calculation"],
        "expression": ["expression", "final_answer"],
    }
    return defaults.get(micro_type, [])


def _clean_dimensions(raw: list[str]) -> list[str]:
    allowed = {
        "concept",
        "trigger",
        "method",
        "transformation",
        "process",
        "calculation",
        "final_answer",
        "expression",
        "migration",
    }
    return [item for item in raw if item in allowed]
