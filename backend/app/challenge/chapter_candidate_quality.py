from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Literal

CandidateQualityGrade = Literal["pass", "warn", "fail"]

REQUIRED_ERROR_CAUSES = {
    "concept_gap",
    "trigger_failure",
    "method_error",
    "transformation_error",
    "calculation_error",
    "expression_weakness",
}

QUALITY_DIMENSION_WEIGHTS = {
    "runtime_shape": 20,
    "visible_topology": 15,
    "repair_system": 20,
    "logic_depth": 15,
    "transfer_synthesis": 10,
    "hash_integrity": 10,
    "learner_safety": 10,
}

TRUSTED_FIELD_MARKERS = {
    "expected_answer",
    "answer_aliases",
    "solution_outline",
    "trusted_answer",
    "debug_explanation",
    "internal_rubric",
    "validator_secret",
}


@dataclass(frozen=True)
class CandidateQualityIssue:
    severity: Literal["error", "warning", "info"]
    code: str
    target: str
    message: str
    suggested_fix: str

    def to_dict(self) -> dict[str, str]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class CandidateQualityDimension:
    code: str
    score: int
    max_score: int
    state: Literal["pass", "warn", "fail"]
    issues: list[CandidateQualityIssue]

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "score": self.score,
            "max_score": self.max_score,
            "state": self.state,
            "issues": [issue.to_dict() for issue in self.issues],
        }


def evaluate_chapter_candidate_quality(
    candidate: dict[str, Any] | None,
    *,
    content_hash: str | None,
    runtime_validation: dict[str, Any],
    formal_publish_allowed: bool,
) -> dict[str, Any]:
    if candidate is None:
        return _report(
            dimensions=[
                CandidateQualityDimension(
                    "candidate_presence",
                    0,
                    0,
                    "fail",
                    [
                        _issue(
                            "error",
                            "candidate_missing",
                            "candidate",
                            "Candidate payload is missing because an earlier gate blocked the build.",
                            "Fix validation or human review gates before quality evaluation.",
                        )
                    ],
                )
            ],
            formal_publish_allowed=formal_publish_allowed,
            next_action="fix_candidate_build_gate",
        )

    dimensions = [
        _runtime_shape_dimension(runtime_validation),
        _visible_topology_dimension(candidate),
        _repair_system_dimension(candidate),
        _logic_depth_dimension(candidate),
        _transfer_synthesis_dimension(candidate),
        _hash_integrity_dimension(content_hash),
        _learner_safety_dimension(candidate, formal_publish_allowed),
    ]
    return _report(
        dimensions=dimensions,
        formal_publish_allowed=formal_publish_allowed,
        next_action=None,
    )


def _report(
    *,
    dimensions: list[CandidateQualityDimension],
    formal_publish_allowed: bool,
    next_action: str | None,
) -> dict[str, Any]:
    score = sum(dimension.score for dimension in dimensions)
    max_score = sum(dimension.max_score for dimension in dimensions) or sum(QUALITY_DIMENSION_WEIGHTS.values())
    issues = [issue for dimension in dimensions for issue in dimension.issues]
    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    grade = _grade(score, max_score, error_count, warning_count)
    blocking_codes = [issue.code for issue in issues if issue.severity == "error"]
    return {
        "mode": "chapter_candidate_quality_gate",
        "grade": grade,
        "score": score,
        "max_score": max_score,
        "pass_threshold": 85,
        "warning_threshold": 70,
        "error_count": error_count,
        "warning_count": warning_count,
        "dimensions": [dimension.to_dict() for dimension in dimensions],
        "next_action": next_action or _next_action(grade),
        "candidate_publish_gate": {
            "candidate_quality_passed": grade == "pass",
            "formal_publish_allowed": False,
            "formal_publish_lock_reason": "Formal publish is a separate future phase and remains locked even when candidate quality passes.",
            "invalid_formal_publish_flag_seen": formal_publish_allowed,
            "blocking_codes": blocking_codes,
        },
    }


def _runtime_shape_dimension(runtime_validation: dict[str, Any]) -> CandidateQualityDimension:
    max_score = QUALITY_DIMENSION_WEIGHTS["runtime_shape"]
    if runtime_validation.get("passed") is True:
        return CandidateQualityDimension("runtime_shape", max_score, max_score, "pass", [])
    errors = runtime_validation.get("errors", []) or ["Runtime validation failed without detail."]
    return CandidateQualityDimension(
        "runtime_shape",
        0,
        max_score,
        "fail",
        [
            _issue(
                "error",
                "runtime_shape_invalid",
                "challenge_graph",
                str(error),
                "Make the candidate graph validate against ChallengeGraph before any publish path.",
            )
            for error in errors
        ],
    )


def _visible_topology_dimension(candidate: dict[str, Any]) -> CandidateQualityDimension:
    graph = candidate.get("challenge_graph", {})
    issues: list[CandidateQualityIssue] = []
    macro_nodes = graph.get("macro_nodes", [])
    micro_nodes = graph.get("micro_nodes", [])
    macro_challenges = graph.get("macro_challenges", [])
    contains = graph.get("contains", {})
    if not macro_nodes:
        issues.append(_issue("error", "no_macro_nodes", "macro_nodes", "No MacroNodes exist.", "Add at least one visible MacroNode."))
    if not micro_nodes:
        issues.append(_issue("error", "no_micro_nodes", "micro_nodes", "No MicroNodes exist.", "Add trainable MicroNodes under MacroNodes."))
    if not macro_challenges:
        issues.append(_issue("error", "no_macro_challenges", "macro_challenges", "No MacroChallenges exist.", "Add Boss/MacroChallenge checks."))
    micro_by_macro = {node.get("id", ""): 0 for node in macro_nodes}
    for micro in micro_nodes:
        macro_id = micro.get("macro_node_id", "")
        micro_by_macro[macro_id] = micro_by_macro.get(macro_id, 0) + 1
    for macro_id, count in micro_by_macro.items():
        if count == 0:
            issues.append(_issue("error", "macro_without_micro", macro_id, "MacroNode has no MicroNodes.", "Attach visible MicroNodes or remove the MacroNode."))
        elif count > 8:
            issues.append(_issue("warning", "visible_node_budget_high", macro_id, "MacroNode has more than 8 visible MicroNodes.", "Move fine-grained abilities into HiddenAbilities."))
    for challenge in macro_challenges:
        if not challenge.get("covers_micro_nodes"):
            issues.append(_issue("error", "boss_covers_no_micro", challenge.get("id", "macro_challenge"), "MacroChallenge covers no MicroNodes.", "Make each Boss cover core MicroNodes."))
    for macro_id, listed in contains.items():
        expected = sorted([micro.get("id") for micro in micro_nodes if micro.get("macro_node_id") == macro_id])
        if sorted(listed) != expected:
            issues.append(_issue("warning", "contains_map_mismatch", macro_id, "contains map does not match MicroNode ownership.", "Regenerate contains from MicroNode macro_node_id."))
    return _dimension("visible_topology", issues)


def _repair_system_dimension(candidate: dict[str, Any]) -> CandidateQualityDimension:
    graph = candidate.get("challenge_graph", {})
    issues: list[CandidateQualityIssue] = []
    micro_ids = {node.get("id") for node in graph.get("micro_nodes", [])}
    mapping = graph.get("error_to_micro_mapping", {}) or candidate.get("error_repair_map", {})
    if not mapping:
        issues.append(_issue("error", "repair_mapping_missing", "error_to_micro_mapping", "No root-cause repair mapping exists.", "Map root causes to concrete MicroNodes."))
    missing_core = sorted(REQUIRED_ERROR_CAUSES - set(mapping))
    if missing_core:
        issues.append(_issue("warning", "core_error_mapping_incomplete", "error_to_micro_mapping", f"Missing core error mappings: {', '.join(missing_core)}.", "Add mappings for common Math150 root causes."))
    invalid_targets = sorted({target for target in mapping.values() if target not in micro_ids})
    if invalid_targets:
        issues.append(_issue("error", "repair_target_invalid", "error_to_micro_mapping", f"Repair targets are not MicroNodes: {', '.join(invalid_targets)}.", "Point every root cause to an existing MicroNode."))
    target_counts: dict[str, int] = {}
    for target in mapping.values():
        target_counts[target] = target_counts.get(target, 0) + 1
    if len(target_counts) == 1 and len(mapping) >= 3:
        issues.append(_issue("warning", "repair_overfunnels_one_node", "error_to_micro_mapping", "Many root causes funnel to one MicroNode.", "Split repair targets across different trainable abilities."))
    return _dimension("repair_system", issues)


def _logic_depth_dimension(candidate: dict[str, Any]) -> CandidateQualityDimension:
    graph = candidate.get("challenge_graph", {})
    logic_graph = candidate.get("logic_graph", {})
    issues: list[CandidateQualityIssue] = []
    atom_nodes = graph.get("atom_nodes", [])
    micro_nodes = graph.get("micro_nodes", [])
    logic_edges = logic_graph.get("edges", [])
    if not atom_nodes:
        issues.append(_issue("error", "hidden_ability_missing", "atom_nodes", "No HiddenAbility-derived atom nodes exist.", "Add hidden abilities with evidence sources for diagnosis."))
    micro_ids = {node.get("id") for node in micro_nodes}
    atom_targets = {node.get("micro_node_id") for node in atom_nodes}
    uncovered = sorted(str(node_id) for node_id in micro_ids - atom_targets)
    if uncovered:
        issues.append(_issue("warning", "micro_without_hidden_ability", "atom_nodes", f"MicroNodes without hidden ability support: {', '.join(uncovered)}.", "Add HiddenAbilities for trainable nodes that require deeper diagnosis."))
    if atom_nodes and not logic_edges:
        issues.append(_issue("warning", "logic_edges_missing", "logic_edges", "Hidden abilities exist but no semantic edges connect them.", "Add edges explaining support, repair, contrast, or transfer relationships."))
    return _dimension("logic_depth", issues)


def _transfer_synthesis_dimension(candidate: dict[str, Any]) -> CandidateQualityDimension:
    graph = candidate.get("challenge_graph", {})
    issues: list[CandidateQualityIssue] = []
    guide_nodes = graph.get("guide_nodes", [])
    typed_edges = graph.get("typed_edges", [])
    has_transfer = any(node.get("kind") == "bridge" for node in guide_nodes) or any(edge.get("edge_type") == "transfers_to" for edge in typed_edges)
    has_synthesis = any(node.get("kind") == "boss_gate" for node in guide_nodes) or any(edge.get("edge_type") == "boss_covers" for edge in typed_edges)
    if not has_transfer:
        issues.append(_issue("warning", "transfer_route_missing", "transfer_nodes", "No transfer route is represented.", "Add TransferNodes or transfers_to edges."))
    if not has_synthesis:
        issues.append(_issue("warning", "synthesis_route_missing", "synthesis_nodes", "No synthesis/Boss route is represented.", "Add SynthesisNodes or boss_checks edges."))
    return _dimension("transfer_synthesis", issues)


def _hash_integrity_dimension(content_hash: str | None) -> CandidateQualityDimension:
    hash_value = (content_hash or "").removeprefix("sha256:")
    if re.fullmatch(r"[0-9a-f]{64}", hash_value):
        return CandidateQualityDimension("hash_integrity", QUALITY_DIMENSION_WEIGHTS["hash_integrity"], QUALITY_DIMENSION_WEIGHTS["hash_integrity"], "pass", [])
    return CandidateQualityDimension(
        "hash_integrity",
        0,
        QUALITY_DIMENSION_WEIGHTS["hash_integrity"],
        "fail",
        [_issue("error", "content_hash_invalid", "content_hash", "Content hash is missing or not a sha256 digest.", "Generate a deterministic sha256 hash from canonical candidate content.")],
    )


def _learner_safety_dimension(candidate: dict[str, Any], formal_publish_allowed: bool) -> CandidateQualityDimension:
    issues: list[CandidateQualityIssue] = []
    if formal_publish_allowed:
        issues.append(_issue("error", "formal_publish_unlocked", "formal_publish_allowed", "Formal publish is unlocked during candidate preview.", "Keep formal publish locked until a separate controlled publish phase exists."))
    leaked_fields = sorted(_find_trusted_markers(candidate))
    if leaked_fields:
        issues.append(_issue("error", "trusted_field_leak", "candidate", f"Candidate contains trusted fields: {', '.join(leaked_fields)}.", "Remove trusted answer, debug, and internal validator fields from candidate preview."))
    return _dimension("learner_safety", issues)


def _find_trusted_markers(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in TRUSTED_FIELD_MARKERS:
                found.add(key)
            found |= _find_trusted_markers(child)
    elif isinstance(value, list):
        for child in value:
            found |= _find_trusted_markers(child)
    return found


def _dimension(code: str, issues: list[CandidateQualityIssue]) -> CandidateQualityDimension:
    max_score = QUALITY_DIMENSION_WEIGHTS[code]
    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    if error_count:
        return CandidateQualityDimension(code, 0, max_score, "fail", issues)
    if warning_count:
        return CandidateQualityDimension(code, max(1, int(max_score * 0.65)), max_score, "warn", issues)
    return CandidateQualityDimension(code, max_score, max_score, "pass", issues)


def _grade(score: int, max_score: int, error_count: int, warning_count: int) -> CandidateQualityGrade:
    if max_score <= 0 or error_count:
        return "fail"
    if warning_count:
        return "warn"
    percentage = score / max_score * 100
    if percentage >= 85:
        return "pass"
    if percentage >= 70:
        return "warn"
    return "fail"


def _next_action(grade: CandidateQualityGrade) -> str:
    if grade == "pass":
        return "codex_local_verify_then_prepare_controlled_publish_design"
    if grade == "warn":
        return "strengthen_candidate_quality_before_publish_design"
    return "fix_blocking_candidate_quality_issues"


def _issue(
    severity: Literal["error", "warning", "info"],
    code: str,
    target: str,
    message: str,
    suggested_fix: str,
) -> CandidateQualityIssue:
    return CandidateQualityIssue(severity, code, target, message, suggested_fix)
