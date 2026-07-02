from __future__ import annotations

from app.challenge.models import ChallengeGraph, MicroNodeType, NetworkEdgeType
from app.core.enums import ErrorType
from app.logic_graph.models import (
    LogicAbilityKind,
    LogicGraph,
    LogicEdgeType,
    LogicGraphQualityIssue,
    LogicGraphQualityReport,
    LogicQualitySeverity,
)


REQUIRED_MICRO_TYPES = {
    MicroNodeType.CONCEPT,
    MicroNodeType.TRIGGER,
    MicroNodeType.METHOD,
    MicroNodeType.TRANSFORMATION,
    MicroNodeType.CALCULATION,
    MicroNodeType.EXPRESSION,
}

DEFAULT_DIMENSIONS_BY_MICRO_TYPE = {
    MicroNodeType.CONCEPT: {"concept"},
    MicroNodeType.TRIGGER: {"trigger"},
    MicroNodeType.METHOD: {"method"},
    MicroNodeType.TRANSFORMATION: {"transformation"},
    MicroNodeType.CALCULATION: {"calculation"},
    MicroNodeType.EXPRESSION: {"expression", "final_answer"},
}

CORE_ERROR_TYPES = {
    ErrorType.CONCEPT_GAP,
    ErrorType.TRIGGER_FAILURE,
    ErrorType.METHOD_ERROR,
    ErrorType.TRANSFORMATION_ERROR,
    ErrorType.PROCESS_GAP,
    ErrorType.CALCULATION_ERROR,
    ErrorType.CONDITION_MISS,
    ErrorType.FORMULA_MEMORY_ERROR,
    ErrorType.KNOWLEDGE_CONFUSION,
    ErrorType.EXPRESSION_WEAKNESS,
    ErrorType.MIGRATION_FAILURE,
    ErrorType.SYNTHESIS_FAILURE,
}

VISIBLE_MICRO_WARNING_LIMIT = 8
VISIBLE_MICRO_ERROR_LIMIT = 12
CYCLE_EDGE_TYPES = {
    LogicEdgeType.REQUIRES,
    LogicEdgeType.BLOCKS,
    LogicEdgeType.DERIVES_TO,
}


class KnowledgeGraphQualityValidator:
    """Checks whether the visible challenge map is backed by a rigorous logic graph.

    The validator does not change training behavior. It is a content-quality gate
    for future authoring: visible nodes stay small, while hidden abilities and
    typed edges carry the rigorous prerequisite and repair logic.
    """

    def validate(self, challenge_graph: ChallengeGraph, logic_graph: LogicGraph | None) -> LogicGraphQualityReport:
        issues: list[LogicGraphQualityIssue] = []
        if logic_graph is None:
            issues.append(
                self._issue(
                    LogicQualitySeverity.ERROR,
                    "missing_logic_graph",
                    "Challenge graph has no hidden logic graph.",
                )
            )
            return self._report(challenge_graph.chapter_id, issues)

        micro_ids = {node.id for node in challenge_graph.micro_nodes}
        macro_ids = {node.id for node in challenge_graph.macro_nodes}
        challenge_ids = {node.id for node in challenge_graph.macro_challenges}
        ability_ids = {ability.id for ability in logic_graph.abilities}
        mapped_ability_ids = {
            ability_id
            for ids in logic_graph.node_ability_map.values()
            for ability_id in ids
        } | {
            ability_id
            for ids in logic_graph.error_ability_map.values()
            for ability_id in ids
        }
        edge_ability_ids = {
            ability_id
            for edge in logic_graph.edges
            for ability_id in (edge.source_id, edge.target_id)
        }

        self._check_macro_micro_structure(challenge_graph, issues)
        self._check_visible_node_budget(challenge_graph, issues)
        self._check_micro_ability_coverage(challenge_graph, logic_graph, issues)
        self._check_macro_challenge_coverage(challenge_graph, issues)
        self._check_repair_targets(logic_graph, micro_ids, macro_ids, issues)
        self._check_error_coverage(logic_graph, issues)
        self._check_root_cause_repair_targets(logic_graph, micro_ids, issues)
        self._check_compare_nodes(challenge_graph, logic_graph, issues)
        self._check_orphan_abilities(ability_ids, mapped_ability_ids | edge_ability_ids, issues)
        self._check_hidden_ability_evidence_sources(logic_graph, issues)
        self._check_logic_edges(logic_graph, issues)
        self._check_logic_cycles(logic_graph, issues)
        self._check_boss_edges(challenge_graph, challenge_ids, issues)
        self._check_boss_hidden_coverage(challenge_graph, logic_graph, issues)
        return self._report(challenge_graph.chapter_id, issues)

    def _check_macro_micro_structure(
        self,
        challenge_graph: ChallengeGraph,
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        for macro in challenge_graph.macro_nodes:
            micro_nodes = [
                micro for micro in challenge_graph.micro_nodes
                if micro.id in set(challenge_graph.contains.get(macro.id, []))
            ]
            present_types = {micro.type for micro in micro_nodes}
            missing = REQUIRED_MICRO_TYPES - present_types
            for micro_type in sorted(missing, key=lambda item: item.value):
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "macro_missing_required_micro_type",
                        f"Macro node is missing required micro type: {micro_type.value}.",
                        macro.id,
                    )
                )

    def _check_visible_node_budget(
        self,
        challenge_graph: ChallengeGraph,
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        for macro in challenge_graph.macro_nodes:
            micro_count = len(challenge_graph.contains.get(macro.id, []))
            if micro_count > VISIBLE_MICRO_ERROR_LIMIT:
                severity = LogicQualitySeverity.ERROR
                code = "macro_visible_micro_node_explosion"
            elif micro_count > VISIBLE_MICRO_WARNING_LIMIT:
                severity = LogicQualitySeverity.WARNING
                code = "macro_visible_micro_node_heavy"
            else:
                continue
            issues.append(
                self._issue(
                    severity,
                    code,
                    f"Macro node has too many visible trainable micro nodes: {micro_count}.",
                    macro.id,
                )
            )

    def _check_micro_ability_coverage(
        self,
        challenge_graph: ChallengeGraph,
        logic_graph: LogicGraph,
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        for micro in challenge_graph.micro_nodes:
            abilities = logic_graph.abilities_for_node(micro.id)
            if not abilities:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "micro_missing_hidden_ability",
                        "Trainable micro node has no hidden ability coverage.",
                        micro.id,
                    )
                )
                continue
            expected_dimension_values = (
                {dimension.value for dimension in micro.default_dimensions}
                if micro.default_dimensions
                else DEFAULT_DIMENSIONS_BY_MICRO_TYPE[micro.type]
            )
            if not any(
                expected_dimension_values.intersection({dimension.value for dimension in ability.dimensions})
                for ability in abilities
            ):
                issues.append(
                    self._issue(
                        LogicQualitySeverity.WARNING,
                        "micro_ability_dimension_mismatch",
                        "Hidden abilities do not share dimensions with this micro node.",
                        micro.id,
                    )
                )

    def _check_macro_challenge_coverage(
        self,
        challenge_graph: ChallengeGraph,
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        for challenge in challenge_graph.macro_challenges:
            contained = set(challenge_graph.contains.get(challenge.macro_node_id, []))
            covered = set(challenge.covers_micro_nodes)
            if not contained.issubset(covered):
                missing = ", ".join(sorted(contained - covered))
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "boss_missing_micro_coverage",
                        f"Macro challenge does not cover all contained micro nodes: {missing}.",
                        challenge.id,
                    )
                )

    def _check_repair_targets(
        self,
        logic_graph: LogicGraph,
        micro_ids: set[str],
        macro_ids: set[str],
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        valid_targets = micro_ids | macro_ids
        for ability in logic_graph.abilities:
            if ability.repair_target_node_id not in valid_targets:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "ability_repair_target_not_trainable",
                        "Hidden ability repair target must be a visible trainable node.",
                        ability.id,
                    )
                )
            elif ability.repair_target_node_id in macro_ids:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.WARNING,
                        "ability_repair_target_is_macro",
                        "Hidden ability repair target should usually point to a trainable micro node.",
                        ability.id,
                    )
                )

    def _check_error_coverage(
        self,
        logic_graph: LogicGraph,
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        missing = CORE_ERROR_TYPES - set(logic_graph.error_ability_map)
        for error_type in sorted(missing, key=lambda item: item.value):
            issues.append(
                self._issue(
                    LogicQualitySeverity.ERROR,
                    "error_missing_hidden_ability_mapping",
                    f"Core error type has no hidden ability mapping: {error_type.value}.",
                )
            )

    def _check_root_cause_repair_targets(
        self,
        logic_graph: LogicGraph,
        micro_ids: set[str],
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        for error_type, ability_ids in logic_graph.error_ability_map.items():
            abilities = logic_graph._abilities_from_ids(ability_ids)
            if not abilities:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "root_cause_has_no_repair_ability",
                        f"Root cause cannot map to a hidden repair ability: {error_type.value}.",
                    )
                )
                continue
            if not any(ability.repair_target_node_id in micro_ids for ability in abilities):
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "root_cause_has_no_micro_repair_target",
                        f"Root cause does not resolve to a trainable micro repair target: {error_type.value}.",
                    )
                )

    def _check_compare_nodes(
        self,
        challenge_graph: ChallengeGraph,
        logic_graph: LogicGraph,
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        confusion_targets = {
            edge.target_id for edge in challenge_graph.typed_edges if edge.edge_type == NetworkEdgeType.CONFUSION
        } | {
            edge.source_id for edge in challenge_graph.typed_edges if edge.edge_type == NetworkEdgeType.CONFUSION
        }
        for compare in challenge_graph.compare_nodes:
            if len(compare.node_ids) < 2:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "compare_node_not_comparing_two_nodes",
                        "Compare node must connect at least two confusable nodes.",
                        compare.id,
                    )
                )
            if compare.id not in confusion_targets:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.WARNING,
                        "compare_node_missing_confusion_edge",
                        "Compare node has no visible confusion edge.",
                        compare.id,
                    )
                )
            abilities = logic_graph.abilities_for_node(compare.id)
            if not abilities:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "compare_node_missing_misconception_ability",
                        "Compare node has no hidden misconception guard ability.",
                        compare.id,
                    )
                )
            elif not any(ability.kind == LogicAbilityKind.MISCONCEPTION_GUARD for ability in abilities):
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "compare_node_missing_guard_kind",
                        "Compare node hidden abilities must include a misconception guard.",
                        compare.id,
                    )
                )

    def _check_orphan_abilities(
        self,
        ability_ids: set[str],
        referenced_ability_ids: set[str],
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        for ability_id in sorted(ability_ids - referenced_ability_ids):
            issues.append(
                self._issue(
                    LogicQualitySeverity.WARNING,
                    "orphan_hidden_ability",
                    "Hidden ability is not referenced by node maps, error maps, or ability edges.",
                    ability_id,
                )
            )

    def _check_hidden_ability_evidence_sources(
        self,
        logic_graph: LogicGraph,
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        for ability in logic_graph.abilities:
            if not ability.evidence_sources:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.WARNING,
                        "hidden_ability_missing_evidence_source",
                        "Hidden ability should declare which evidence sources can support it.",
                        ability.id,
                    )
                )
            if not ability.why_exists:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.WARNING,
                        "hidden_ability_missing_why_exists",
                        "Hidden ability should explain why it exists in the graph.",
                        ability.id,
                    )
                )

    def _check_logic_edges(
        self,
        logic_graph: LogicGraph,
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        for edge in logic_graph.edges:
            if edge.source_id == edge.target_id:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "logic_edge_self_loop",
                        "Logic edge cannot connect an ability to itself.",
                        edge.id,
                    )
                )
            if not edge.label and not edge.reason:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.WARNING,
                        "logic_edge_missing_meaning",
                        "Logic edge should have a label or reason explaining why it exists.",
                        edge.id,
                    )
                )
            if edge.weight <= 0:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "logic_edge_zero_weight",
                        "Logic edge with zero weight is semantically meaningless.",
                        edge.id,
                    )
                )

    def _check_logic_cycles(
        self,
        logic_graph: LogicGraph,
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        adjacency: dict[str, list[str]] = {}
        for edge in logic_graph.edges:
            if edge.edge_type not in CYCLE_EDGE_TYPES:
                continue
            adjacency.setdefault(edge.source_id, []).append(edge.target_id)

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node_id: str, path: list[str]) -> None:
            if node_id in visiting:
                cycle_start = path.index(node_id) if node_id in path else 0
                cycle = " -> ".join([*path[cycle_start:], node_id])
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "logic_dependency_cycle",
                        f"Logic dependency cycle detected: {cycle}.",
                        node_id,
                    )
                )
                return
            if node_id in visited:
                return
            visiting.add(node_id)
            for target_id in adjacency.get(node_id, []):
                visit(target_id, [*path, node_id])
            visiting.remove(node_id)
            visited.add(node_id)

        for ability in logic_graph.abilities:
            visit(ability.id, [])

    def _check_boss_edges(
        self,
        challenge_graph: ChallengeGraph,
        challenge_ids: set[str],
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        boss_targets = {
            edge.target_id
            for edge in challenge_graph.typed_edges
            if edge.edge_type in {NetworkEdgeType.SYNTHESIS, NetworkEdgeType.BOSS_COVERS, NetworkEdgeType.ASSESSES}
        }
        for challenge_id in challenge_ids:
            if challenge_id not in boss_targets:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "boss_missing_synthesis_or_assessment_edge",
                        "Macro challenge has no synthesis/assessment edge feeding it.",
                        challenge_id,
                    )
                )

    def _check_boss_hidden_coverage(
        self,
        challenge_graph: ChallengeGraph,
        logic_graph: LogicGraph,
        issues: list[LogicGraphQualityIssue],
    ) -> None:
        boss_checked_targets = {
            edge.target_id
            for edge in logic_graph.edges
            if edge.edge_type == LogicEdgeType.BOSS_CHECKS
        } | {
            edge.source_id
            for edge in logic_graph.edges
            if edge.edge_type == LogicEdgeType.BOSS_CHECKS
        }
        for challenge in challenge_graph.macro_challenges:
            covered_ability_ids = {
                ability.id
                for micro_id in challenge.covers_micro_nodes
                for ability in logic_graph.abilities_for_node(micro_id)
            }
            if not covered_ability_ids:
                issues.append(
                    self._issue(
                        LogicQualitySeverity.ERROR,
                        "boss_missing_hidden_ability_coverage",
                        "Macro challenge covers no hidden abilities through its micro nodes.",
                        challenge.id,
                    )
                )
                continue
            if not covered_ability_ids.intersection(boss_checked_targets):
                issues.append(
                    self._issue(
                        LogicQualitySeverity.WARNING,
                        "boss_missing_hidden_boss_check_edge",
                        "Macro challenge coverage has no hidden boss_checks edge.",
                        challenge.id,
                    )
                )

    def _issue(
        self,
        severity: LogicQualitySeverity,
        code: str,
        message: str,
        node_id: str | None = None,
    ) -> LogicGraphQualityIssue:
        return LogicGraphQualityIssue(severity=severity, code=code, message=message, node_id=node_id)

    def _report(self, chapter_id: str, issues: list[LogicGraphQualityIssue]) -> LogicGraphQualityReport:
        error_count = sum(issue.severity == LogicQualitySeverity.ERROR for issue in issues)
        warning_count = sum(issue.severity == LogicQualitySeverity.WARNING for issue in issues)
        info_count = sum(issue.severity == LogicQualitySeverity.INFO for issue in issues)
        return LogicGraphQualityReport(
            chapter_id=chapter_id,
            issue_count=len(issues),
            error_count=error_count,
            warning_count=warning_count,
            info_count=info_count,
            issues=issues,
        )
