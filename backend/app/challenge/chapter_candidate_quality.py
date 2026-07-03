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
        return {
            "severity": self.severity,
            "code": self.code,
            "target": self.target,
            "message": self.message,
            "suggested_fix": self.suggested_fix,
        }


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


@dataclass(frozen=True)
class CandidateQualityReport:
    grade: CandidateQualityGrade
    score: int
    max_score: int
    pass_threshold: int
    warning_threshold: int
    error_count: int
    warning_count: int
    dimensions: list[CandidateQualityDimension]
    next_action: str
    candidate_publish_gate: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": "chapter_candidate_quality_gate",
            "grade": self.grade,
            "score": self.score,
            "max_score": self.max_score,
            "pass_threshold": self.pass_threshold,
            "warning_threshold": self.warning_threshold,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "dimensions": [dimension.to_dict() for dimension in self.dimensions],
            "next_action": self.next_action,
            "candidate_publish_gate": self.candidate_publish_gate,
        }


def evaluate_chapter_candidate_quality(
    candidate: dict[str, Any] | None,
    *,
    content_hash: str | None,
    runtime_validation: dict[str, Any],
    formal_publish_allowed: bool,
) -> dict[str, Any]:
    """Evaluate whether a chapter candidate is strong enough to remain in the publish pipeline.

    This is not a formal publish decision. It is a quality gate for candidate preview.
    Formal publish remains locked. The evaluator is intentionally deterministic and
    inspectable so Codex and ChatGPT can debug exactly why a candidate is weak.
    """

    if candidate is None:
        report = CandidateQualityReport(
            grade="fail",
            score=0,
            max_score=sum(QUALITY_DIMENSION_WEIGHTS.values()),
            pass_threshold=85,
            warning_threshold=70,
            error_count=1,
            warning_count=0,
            dimensions=[
                CandidateQualityDimension(
                    code="candidate_presence",
                    score=0,
                    max_score=0,
                    state="fail",
                    issues=[
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
            next_action="fix_candidate_build_gate",
            candidate_publish_gate=_publish_gate(False, formal_publish_allowed, ["candidate_missing"]),
        )
        return report.to_dict()

    dimensions = [
        _runtime_shape_dimension(runtime_validation),
        _visible_topology_dimension(candidate),
        _repair_system_dimension(candidate),
        _logic_depth_dimension(candidate),
        _transfer_synthesis_dimension(candidate),
        _hash_integrity_dimension(content_hash),
        _learner_safety_dimension(candidate, formal_publish_allowed),
    ]
    score = sum(dimension.score for dimension in dimensions)
    max_score = sum(dimension.max_score for dimension in dimensions)
    issues = [issue for dimension in dimensions for issue in dimension.issues]
    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    grade = _grade(score, max_score, error_count)
    report = CandidateQualityReport(
        grade=grade,
        score=score,
        max_score=max_score,
        pass_threshold=85,
        warning_threshold=70,
        error_count=error_count,
        warning_count=warning_count,
        dimensions=dimensions,
        next_action=_next_action(grade),
        candidate_publish_gate=_publish_gate(
            grade == "pass",
            formal_publish_allowed,
            [issue.code for issue in issues if issue.severity == "error"],
        ),
    )
    return report.to_dict()


def _runtime_shape_dimension(runtime_validation: dict[str, Any]) -> CandidateQualityDimension:
    max_score = QUALITY_DIMENSION_WEIGHTS["runtime_shape"]
    if runtime_validation.get("passed") is True:
        return CandidateQualityDimension("runtime_shape", max_score, max_score, "pass", [])
    issues = [
        _issue(
            "error",
            "runtime_shape_invalid",
            "challenge_graph",
            str(message),
            "Make the candidate graph validate against ChallengeGraph before any publish path.",
        )
        for message in runtime_validation.get("errors", [])
    ] or [
        _issue(
            "error",
            "runtime_shape_invalid",
            "challenge_graph",
            "Runtime validation failed without a detailed error.",
            "Run the candidate through ChallengeGraph.model_validate and inspect the failure.",
        )
    ]
    return CandidateQualityDimension("runtime_shape", 0, max_score, "fail", issues)


def _visible_topology_dimension(candidate: dict[str, Any]) -> CandidateQualityDimension:
    graph = candidate.get("challenge_graph", {})
    max_score = QUALITY_DIMENSION_WEIGHTS["visible_topology"]
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

    micro_by_macro: dict[str, int] = {node.get("id", ""): 0 for node in macro_nodes}
    for micro in micro_nodes:
        macro_id = micro.get("macro_node_id", "")
        micro_by_macro[macro_id] = micro_by_macro.get(macro_id, 0) + 1
    for macro_id, count in micro_by_macro.items():
        if count == 0:
            issues.append(_issue("error", "macro_without_micro", macro_id, "MacroNode has no MicroNodes.", "Attach visible MicroNodes or remove the MacroNode."))
        elif count > 8:
            issues.append(_issue("warning", "visible_node_budget_high", macro_id, "MacroNode has more than 8 visible MicroNodes.", "Move fine-grained abilities into HiddenAbilities."))

    for challenge in macro_challenges:
        covered = challenge.get("covers_micro_nodes", [])
        if not covered:
            issues.append(_issue("error", "boss_covers_no_micro", challenge.get("id", "macro_challenge"), "MacroChallenge covers no MicroNodes.", "Make each Boss cover the core MicroNodes."))

    for macro_id, listed in contains.items():
        if sorted(listed) != sorted([micro.get("id") for micro in micro_nodes if micro.get("macro_node_id") == macro_id]):
            issues.append(_issue("warning", "contains_map_mismatch", macro_id, "contains map does not match MicroNode ownership.", "Regenerate contains from MicroNode macro_node_id."))

    return _dimension_from_issues("visible_topology", max_score, issues)


def _repair_system_dimension(candidate: dict[str, Any]) -> CandidateQualityDimension:
    graph = candidate.get("challenge_graph", {})
    max_score = QUALITY_DIMENSION_WEIGHTS["repair_system"]
    issues: list[CandidateQualityIssue] = []
    micro_ids = {node.get("id") for node in graph.get("micro_nodes", [])}
    mapping = graph.get("error_to_micro_mapping", {}) or candidate.get("error_repair_map", {})

    if not mapping:
        issues.append(_issue("error", "repair_mapping_missing", "error_to_micro_mapping", "No root-cause repair mapping exists.", "Map root causes to concrete MicroNodes."))
    missing_core = sorted(REQUIRED_ERROR_CAUSES - set(mapping))
    if missing_core:
        issues.append(_issue("warning", "core_error_mapping_incomplete", "error_to_micro_mapping", f"Missing core error mappings: {', '.join(missing_core)}.", "Add mappings for common Math150 diagnosis root causes."))
    invalid_targets = [target for target in mapping.values() if target not in micro_ids]
    if invalid_targets:
        issues.append(_issue("error", "repair_target_invalid", "error_to_micro_mapping", f"Repair targets are not MicroNodes: {', '.join(sorted(set(invalid_targets)))}.", "Point every root cause to an existing MicroNode."))

    target_counts: dict[str, int] = {}
    for target in mapping.values():
        target_counts[target] = target_counts.get(target, 0) + 1
    if len(target_counts) == 1 and len(mapping) >= 3:
        issues.append(_issue("warning", "repair_overfunnels_one_node", "error_to_micro_mapping", "Many root causes funnel to one MicroNode.", "Split repair targets so concept, trigger, method, transformation, calculation, and expression failures repair different abilities."))

    return _dimension_from_issues("repair_system", max_score, issues)


def _logic_depth_dimension(candidate: dict[str, Any]) -> CandidateQualityDimension:
    graph = candidate.get("challenge_graph", {})
    logic_graph = candidate.get("logic_graph", {})
    max_score = QUALITY_DIMENSION_WEIGHTS["logic_depth"]
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
        issues.append(_issue("warning", "micro_without_hidden_ability", "atom_nodes", f"MicroNodes without hidden ability support: {', '.join(uncovered)}.", "Add HiddenAbilities for the trainable nodes that require deeper diagnosis."))
    if atom_nodes and not logic_edges:
        issues.append(_issue("warning", "logic_edges_missing", "logic_edges", "Hidden abilities exist but no semantic edges connect them.", "Add edges explaining support, repair, contrast, or transfer relationships."))

    return _dimension_from_issues("logic_depth", max_score, issues)


def _transfer_synthesis_dimension(candidate: dict[str, Any]) -> CandidateQualityDimension:
    graph = candidate.get("challenge_graph", {})
    max_score = QUALITY_DIMENSION_WEIGHTS["transfer_synthesis"]
    issues: list[CandidateQualityIssue] = []
    guide_nodes = graph.get("guide_nodes", [])
    typed_edges = graph.get("typed_edges", [])
    has_transfer = any(node.get("kind") == "bridge" for node in guide_nodes) or any(edge.get("edge_type") == "transfers_to" for edge in typed_edges)
    has_synthesis = any(node.get("kind") == "boss_gate" for node in guide_nodes) or any(edge.get("edge_type") == "boss_covers" for edge in typed_edges)

    if not has_transfer:
        issues.append(_issue("warning", "transfer_route_missing", "transfer_nodes", "No transfer route is represented.", "Add TransferNodes or transfers_to edges so variants are part of the chapter design."))
    if not has_synthesis:
        issues.append(_issue("warning", "synthesis_route_missing", "synthesis_nodes", "No synthesis/Boss route is represented.", "Add SynthesisNodes or boss_checks edges so comprehensive problems are connected."))

    return _dimension_from_issues("transfer_synthesis", max_score, issues)


def _hash_integrity_dimension(content_hash: str | None) -> CandidateQualityDimension:
    max_score = QUALITY_DIMENSION_WEIGHTS["hash_integrity"]
    if content_hash and re.fullmatch(r"[0-9a-f]{64}", content_hash):
        return CandidateQualityDimension("hash_integrity", max_score, max_score, "pass", [])
    return CandidateQualityDimension(
        "hash_integrity",
        0,
        max_score,
        "fail",
        [_issue("error", "content_hash_invalid", "content_hash", "Content hash is missing or not a sha256 hex digest.", "Generate a deterministic sha256 hash from canonical candidate content.")],
    )


def _learner_safety_dimension(candidate: dict[str, Any], formal_publish_allowed: bool) -> CandidateQualityDimension:
    max_score = QUALITY_DIMENSION_WEIGHTS["learner_safety"]
    issues: list[CandidateQualityIssue] = []
    if formal_publish_allowed:
        issues.append(_issue("error", "formal_publish_unlocked", "formal_publish_allowed", "Formal publish is unlocked during candidate preview.", "Keep formal publish locked until a separate controlled publish phase exists."))
    leaked_fields = sorted(_find_trusted_markers(candidate))
    if leaked_fields:
        issues.append(_issue("error", "trusted_field_leak", "candidate", f"Candidate contains trusted fields: {', '.join(leaked_fields)}.", "Remove trusted answer, debug, and internal validator fields from candidate preview."))
    return _dimension_from_issues("learner_safety", max_score, issues)


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


def _dimension_from_issues(code: str, max_score: int, issues: list[CandidateQualityIssue]) -> CandidateQualityDimension:
    error_count = sum(1 for issue in issues if issue.severity == "error")
    warning_count = sum(1 for issue in issues if issue.severity == "warning")
    if error_count:
        score = 0
        state: Literal["pass", "warn", "fail"] = "fail"
    elif warning_count:
        score = max(1, int(max_score * 0.65))
        state = "warn"
    else:
        score = max_score
        state = "pass"
    return CandidateQualityDimension(code, score, max_score, state, issues)


def _grade(score: int, max_score: int, error_count: int) -> CandidateQualityGrade:
    if max_score <= 0 or error_count:
        return "fail"
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


def _publish_gate(candidate_quality_passed: bool, formal_publish_allowed: bool, blocking_codes: list[str]) -> dict[str, Any]:
    return {
        "candidate_quality_passed": candidate_quality_passed,
        "formal_publish_allowed": False,
        "formal_publish_lock_reason": "Formal publish is a separate future phase and remains locked even when candidate quality passes.",
        "invalid_formal_publish_flag_seen": formal_publish_allowed,
        "blocking_codes": blocking_codes,
    }


def _issue(
    severity: Literal["error", "warning", "info"],
    code: str,
    target: str,
    message: str,
    suggested_fix: str,
) -> CandidateQualityIssue:
    return CandidateQualityIssue(severity, code, target, message, suggested_fix)
