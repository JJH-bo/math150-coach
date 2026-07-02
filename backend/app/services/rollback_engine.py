from __future__ import annotations

from app.core.config import DEFAULT_ENGINE_CONFIG, EngineConfig
from app.core.enums import ErrorType, RollbackLevel
from app.core.schemas import ErrorItem, ErrorVector, KnowledgeNode, RollbackDecision


class RollbackEngine:
    R4_ALLOWED_SINGLE_ERROR_TYPES = {
        ErrorType.KNOWLEDGE_CONFUSION,
        ErrorType.SYNTHESIS_FAILURE,
    }

    def __init__(self, config: EngineConfig = DEFAULT_ENGINE_CONFIG) -> None:
        self.config = config

    def select_rollback_nodes(self, error_vector: ErrorVector, node: KnowledgeNode) -> list[str]:
        return self.decide_rollback(error_vector, node).rollback_nodes

    def decide_rollback(self, error_vector: ErrorVector, node: KnowledgeNode) -> RollbackDecision:
        candidate_errors = error_vector.primary_errors() or error_vector.secondary_errors()
        if not candidate_errors:
            return RollbackDecision(
                level=RollbackLevel.R1_INTERNAL,
                rollback_nodes=[],
                blocked_reason="no_errors",
                is_chapter_framework_rollback=False,
                explanation="No primary or secondary errors were found, so no rollback is selected.",
            )

        selected: list[str] = []
        for error in sorted(candidate_errors, key=lambda item: item.weight, reverse=True):
            selected.extend(self._targets_for_error(error, node))
            selected = self._dedupe(selected)
            if len(selected) >= self.config.max_rollback_nodes:
                break

        selected = selected[: self.config.max_rollback_nodes]
        selected = self._avoid_all_prerequisites_for_local_errors(selected, candidate_errors, node)
        level = self.determine_rollback_level(error_vector)
        is_all_prerequisites = self._is_all_prerequisites(selected, node)
        is_chapter_framework = level == RollbackLevel.R4_CHAPTER_FRAMEWORK
        blocked_reason = self._blocked_reason(selected, candidate_errors, node, is_chapter_framework)
        return RollbackDecision(
            level=level,
            rollback_nodes=selected,
            blocked_reason=blocked_reason,
            is_chapter_framework_rollback=is_chapter_framework,
            explanation=self._explain_decision(selected, candidate_errors, node, level, is_all_prerequisites),
        )

    def determine_rollback_level(self, error_vector: ErrorVector) -> RollbackLevel:
        candidate_errors = error_vector.primary_errors() or error_vector.secondary_errors()
        if not candidate_errors:
            return RollbackLevel.R1_INTERNAL
        top_error = sorted(candidate_errors, key=lambda item: item.weight, reverse=True)[0]
        return self._effective_rollback_level(top_error)

    def _targets_for_error(self, error: ErrorItem, node: KnowledgeNode) -> list[str]:
        if error.error_type == ErrorType.CALCULATION_ERROR:
            return [node.id]

        effective_level = self._effective_rollback_level(error)
        policy = node.rollback_policy.get(error.error_type.value)
        if policy and policy.target_nodes and policy.level == effective_level:
            targets = [self._resolve_target(target, node) for target in policy.target_nodes if self._resolve_target(target, node)]
            if effective_level != RollbackLevel.R4_CHAPTER_FRAMEWORK and self._is_all_prerequisites(targets, node):
                return targets[:1] or [node.id]
            return targets

        if effective_level == RollbackLevel.R1_INTERNAL:
            return [node.id]

        if node.prerequisites:
            if effective_level == RollbackLevel.R4_CHAPTER_FRAMEWORK:
                return node.prerequisites[: self.config.max_rollback_nodes]
            return [node.prerequisites[0]]

        return [node.id]

    def _effective_rollback_level(self, error: ErrorItem) -> RollbackLevel:
        if (
            error.suggested_rollback_level == RollbackLevel.R4_CHAPTER_FRAMEWORK
            and error.error_type not in self.R4_ALLOWED_SINGLE_ERROR_TYPES
        ):
            return RollbackLevel.R2_PREREQUISITE
        return error.suggested_rollback_level

    def _resolve_target(self, target: str, node: KnowledgeNode) -> str:
        if target == "__self__":
            return node.id
        if target == "__first_prerequisite__":
            return node.prerequisites[0] if node.prerequisites else node.id
        return target

    def _avoid_all_prerequisites_for_local_errors(
        self,
        selected: list[str],
        errors: list[ErrorItem],
        node: KnowledgeNode,
    ) -> list[str]:
        local_error_types = {
            ErrorType.CALCULATION_ERROR,
            ErrorType.EXPRESSION_WEAKNESS,
            ErrorType.PROCESS_GAP,
        }
        if any(error.error_type in local_error_types for error in errors):
            if self._is_all_prerequisites(selected, node):
                return [node.id]
        if self._is_all_prerequisites(selected, node):
            top_level = self._effective_rollback_level(sorted(errors, key=lambda item: item.weight, reverse=True)[0])
            if top_level != RollbackLevel.R4_CHAPTER_FRAMEWORK:
                return selected[:1]
        return selected

    def _is_all_prerequisites(self, selected: list[str], node: KnowledgeNode) -> bool:
        return bool(node.prerequisites) and set(selected) == set(node.prerequisites) and len(selected) == len(node.prerequisites)

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                deduped.append(value)
        return deduped

    def _blocked_reason(
        self,
        selected: list[str],
        errors: list[ErrorItem],
        node: KnowledgeNode,
        is_chapter_framework: bool,
    ) -> str:
        if not node.prerequisites:
            return "node_has_no_prerequisites"
        if self._is_all_prerequisites(selected, node):
            return "allowed_chapter_framework_rollback" if is_chapter_framework else "unexpected_all_prerequisites"
        top_error = sorted(errors, key=lambda item: item.weight, reverse=True)[0]
        if top_error.suggested_rollback_level == RollbackLevel.R4_CHAPTER_FRAMEWORK and not is_chapter_framework:
            return "illegal_r4_downgraded_to_targeted_rollback"
        return "targeted_rollback_prevents_full_prerequisite_reset"

    def _explain_decision(
        self,
        selected: list[str],
        errors: list[ErrorItem],
        node: KnowledgeNode,
        level: RollbackLevel,
        is_all_prerequisites: bool,
    ) -> str:
        top_error = sorted(errors, key=lambda item: item.weight, reverse=True)[0]
        if is_all_prerequisites and level == RollbackLevel.R4_CHAPTER_FRAMEWORK:
            return (
                f"Selected all prerequisites because {top_error.error_type.value} is an allowed "
                "chapter-framework rollback reason."
            )
        if node.prerequisites:
            return (
                f"Selected {selected} for {top_error.error_type.value}; did not return all prerequisites "
                "because the evidence supports a targeted rollback rather than a full prerequisite reset."
            )
        return f"Selected {selected} for {top_error.error_type.value}; the node has no prerequisites to roll back to."
