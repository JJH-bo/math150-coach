from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.classroom.model_contracts import RegisteredModelRecord
from app.classroom.model_repository import ModelRepositoryError
from app.classroom.model_validation import parameter_value_is_valid
from app.classroom.models import (
    BindingEffect,
    BindingEffectKind,
    BindingTriggerKind,
    ClassroomPackage,
    ContentBlock,
    ContentBlockKind,
)


FORBIDDEN_LEARNER_ANALYSIS_KEYS = {
    "mastery_state",
    "diagnosis",
    "review_schedule",
    "question_bank",
    "boss_challenge",
    "learner_profile",
    "recommended_next_step",
    "ability_profile",
}


class ValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: Literal["error", "warning"]
    code: str
    path: str
    message: str


class ClassroomValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    issues: list[ValidationIssue]


RecordId = Callable[[str, str], None]
ModelResolver = Callable[[str, str], RegisteredModelRecord]


class ClassroomPackageValidator:
    def __init__(self, model_resolver: ModelResolver | None = None) -> None:
        self.model_resolver = model_resolver

    def validate(self, package: ClassroomPackage) -> ClassroomValidationReport:
        issues: list[ValidationIssue] = []
        seen_ids: dict[str, str] = {}

        def record_id(object_id: str, path: str) -> None:
            previous = seen_ids.get(object_id)
            if previous is not None:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="duplicate_object_id",
                        path=path,
                        message=f"Object id {object_id!r} is already used at {previous}.",
                    )
                )
            else:
                seen_ids[object_id] = path

        for course_index, course in enumerate(package.courses):
            course_path = f"courses[{course_index}]"
            record_id(course.id, f"{course_path}.id")
            for chapter_index, chapter in enumerate(course.chapters):
                chapter_path = f"{course_path}.chapters[{chapter_index}]"
                record_id(chapter.id, f"{chapter_path}.id")
                self._validate_coverage_contract(
                    chapter,
                    chapter_path,
                    record_id,
                    issues,
                )
                self._validate_teaching_contract(
                    chapter,
                    chapter_path,
                    issues,
                )
                knowledge_point_ids = {
                    point.id for point in chapter.knowledge_points
                }
                module_ids = {module.id for module in chapter.modules}
                for module_index, module in enumerate(chapter.modules):
                    module_path = f"{chapter_path}.modules[{module_index}]"
                    record_id(module.id, f"{module_path}.id")
                    for block_index, block in enumerate(module.blocks):
                        self._validate_block(
                            block,
                            f"{module_path}.blocks[{block_index}]",
                            record_id,
                            issues,
                            knowledge_point_ids,
                        )
                    for segment_index, segment in enumerate(module.segments):
                        segment_path = f"{module_path}.segments[{segment_index}]"
                        record_id(segment.id, f"{segment_path}.id")
                        for block_index, block in enumerate(segment.blocks):
                            self._validate_block(
                                block,
                                f"{segment_path}.blocks[{block_index}]",
                                record_id,
                                issues,
                                knowledge_point_ids,
                            )
                for relation_index, relation in enumerate(chapter.relations):
                    relation_path = f"{chapter_path}.relations[{relation_index}]"
                    record_id(relation.id, f"{relation_path}.id")
                    if relation.source_module_id not in module_ids:
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                code="unknown_relation_source",
                                path=f"{relation_path}.source_module_id",
                                message="Relation source module does not exist in this chapter.",
                            )
                        )
                    if relation.target_module_id not in module_ids:
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                code="unknown_relation_target",
                                path=f"{relation_path}.target_module_id",
                                message="Relation target module does not exist in this chapter.",
                            )
                        )

        instances: dict[str, tuple[object, RegisteredModelRecord]] = {}
        for instance_index, instance in enumerate(package.model_instances):
            path = f"model_instances[{instance_index}]"
            record_id(instance.instance_id, f"{path}.instance_id")
            if self.model_resolver is None:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="model_registry_unavailable",
                        path=f"{path}.model_version",
                        message="A model registry is required to validate model instances.",
                    )
                )
                continue
            try:
                registered = self.model_resolver(
                    instance.model_id,
                    instance.model_version,
                )
            except (LookupError, ModelRepositoryError):
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="unregistered_model_version",
                        path=f"{path}.model_version",
                        message="Model instance must pin an immutable registered version.",
                    )
                )
                continue
            instances[instance.instance_id] = (instance, registered)
            manifest = registered.manifest
            states = {state.id for state in manifest.states}
            if instance.initial_state not in states:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="unknown_model_state",
                        path=f"{path}.initial_state",
                        message="Initial state is not declared by the registered model.",
                    )
                )
            if instance.viewport_mode not in manifest.viewport_modes:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="unsupported_model_viewport",
                        path=f"{path}.viewport_mode",
                        message="Viewport mode is not supported by the registered model.",
                    )
                )
            if instance.quality_profile not in manifest.quality_profiles:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="unsupported_model_quality",
                        path=f"{path}.quality_profile",
                        message="Quality profile is not supported by the registered model.",
                    )
                )
            unsupported = set(instance.allowed_interactions) - set(
                manifest.interactions
            )
            if unsupported:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="unsupported_model_interaction",
                        path=f"{path}.allowed_interactions",
                        message=f"Unsupported interactions: {sorted(unsupported)}.",
                    )
                )
            parameters = {parameter.id: parameter for parameter in manifest.parameters}
            for parameter_id, value in instance.parameters.items():
                parameter = parameters.get(parameter_id)
                if parameter is None:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="unknown_model_parameter",
                            path=f"{path}.parameters.{parameter_id}",
                            message="Parameter is not declared by the registered model.",
                        )
                    )
                elif not parameter_value_is_valid(parameter, value):
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="invalid_model_parameter",
                            path=f"{path}.parameters.{parameter_id}",
                            message="Parameter value violates the registered model contract.",
                        )
                    )

        for binding_index, binding in enumerate(package.model_bindings):
            path = f"model_bindings[{binding_index}]"
            record_id(binding.id, f"{path}.id")
            if binding.content_id not in seen_ids:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="unknown_binding_content",
                        path=f"{path}.content_id",
                        message="Binding content target does not exist in the package.",
                    )
                )
            resolved = instances.get(binding.instance_id)
            if resolved is None:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="unknown_binding_instance",
                        path=f"{path}.instance_id",
                        message="Binding model instance does not exist or is unavailable.",
                    )
                )
                continue
            _, registered = resolved
            self._validate_effect(
                binding.effect,
                f"{path}.effect",
                registered,
                issues,
            )
            if binding.return_effect is not None:
                self._validate_effect(
                    binding.return_effect,
                    f"{path}.return_effect",
                    registered,
                    issues,
                )
            temporary = binding.trigger.kind in {
                BindingTriggerKind.BLOCK_ENTER,
                BindingTriggerKind.BLOCK_LEAVE,
                BindingTriggerKind.DETAIL_BRANCH_OPEN,
                BindingTriggerKind.DETAIL_BRANCH_CLOSE,
            }
            if temporary and not binding.restore_previous and binding.return_effect is None:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="binding_return_behavior_required",
                        path=path,
                        message="Temporary binding must restore the previous state or declare a return effect.",
                    )
                )

        return ClassroomValidationReport(
            passed=not any(issue.severity == "error" for issue in issues),
            issues=issues,
        )

    def _validate_block(
        self,
        block: ContentBlock,
        path: str,
        record_id: RecordId,
        issues: list[ValidationIssue],
        knowledge_point_ids: set[str],
    ) -> None:
        record_id(block.id, f"{path}.id")
        if not block.knowledge_point_ids:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="content_knowledge_points_required",
                    path=f"{path}.knowledge_point_ids",
                    message="Every teaching block must declare the knowledge points it teaches.",
                )
            )
        for point_id in block.knowledge_point_ids:
            if point_id not in knowledge_point_ids:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="unknown_content_knowledge_point",
                        path=f"{path}.knowledge_point_ids",
                        message=f"Knowledge point {point_id!r} is not declared by this chapter.",
                    )
                )
        self._validate_renderable_data(block, path, issues)
        self._find_forbidden_keys(block.data, f"{path}.data", issues)
        for branch_index, branch in enumerate(block.detail_branches):
            branch_path = f"{path}.detail_branches[{branch_index}]"
            record_id(branch.id, f"{branch_path}.id")
            for block_index, child in enumerate(branch.blocks):
                self._validate_block(
                    child,
                    f"{branch_path}.blocks[{block_index}]",
                    record_id,
                    issues,
                    knowledge_point_ids,
                )

    def _validate_coverage_contract(
        self,
        chapter: Any,
        path: str,
        record_id: RecordId,
        issues: list[ValidationIssue],
    ) -> None:
        required_collections = (
            (
                chapter.source_sections,
                "chapter_source_sections_required",
                "source_sections",
                "A chapter must retain its complete ordered source sections.",
            ),
            (
                chapter.knowledge_points,
                "chapter_knowledge_points_required",
                "knowledge_points",
                "A chapter must enumerate every source knowledge point.",
            ),
            (
                chapter.coverage_map,
                "chapter_coverage_map_required",
                "coverage_map",
                "A chapter must map every knowledge point into baseline teaching content.",
            ),
        )
        for values, code, field, message in required_collections:
            if not values:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code=code,
                        path=f"{path}.{field}",
                        message=message,
                    )
                )
        if chapter.coverage_audit is None:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="chapter_coverage_audit_required",
                    path=f"{path}.coverage_audit",
                    message="A second-pass coverage audit is required before publishing.",
                )
            )

        source_by_id = {}
        for index, section in enumerate(chapter.source_sections):
            section_path = f"{path}.source_sections[{index}]"
            record_id(section.id, f"{section_path}.id")
            source_by_id[section.id] = section

        knowledge_by_id = {}
        referenced_source_ids: set[str] = set()
        for point_index, point in enumerate(chapter.knowledge_points):
            point_path = f"{path}.knowledge_points[{point_index}]"
            record_id(point.id, f"{point_path}.id")
            knowledge_by_id[point.id] = point
            for source_id in point.source_section_ids:
                referenced_source_ids.add(source_id)
                if source_id not in source_by_id:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="unknown_knowledge_source",
                            path=f"{point_path}.source_section_ids",
                            message=f"Source section {source_id!r} does not exist.",
                        )
                    )
            for quote_index, quote in enumerate(point.source_quotes):
                quote_path = f"{point_path}.source_quotes[{quote_index}]"
                referenced_source_ids.add(quote.source_section_id)
                section = source_by_id.get(quote.source_section_id)
                if section is None:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="unknown_knowledge_source",
                            path=f"{quote_path}.source_section_id",
                            message="Quoted source section does not exist.",
                        )
                    )
                elif quote.quote not in section.content:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="source_quote_not_found",
                            path=f"{quote_path}.quote",
                            message="The quoted evidence is not present in the retained source section.",
                        )
                    )
        for source_index, section in enumerate(chapter.source_sections):
            if section.id not in referenced_source_ids:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="source_section_unmapped",
                        path=f"{path}.source_sections[{source_index}].id",
                        message="Every retained source section must contribute at least one knowledge point.",
                    )
                )

        module_ids = {module.id for module in chapter.modules}
        baseline_ids: set[str] = set()
        detail_ids: set[str] = set()
        baseline_knowledge_by_content: dict[str, set[str]] = {}
        detail_knowledge_by_content: dict[str, set[str]] = {}

        def collect_block(block: ContentBlock, *, detail: bool = False) -> None:
            (detail_ids if detail else baseline_ids).add(block.id)
            (
                detail_knowledge_by_content
                if detail
                else baseline_knowledge_by_content
            )[block.id] = set(block.knowledge_point_ids)
            for branch in block.detail_branches:
                for child in branch.blocks:
                    collect_block(child, detail=True)

        for module in chapter.modules:
            for block in module.blocks:
                collect_block(block)
            for segment in module.segments:
                for block in segment.blocks:
                    collect_block(block)

        covered_knowledge_ids: set[str] = set()
        covered_baseline_by_point: dict[str, set[str]] = {}
        covered_detail_by_point: dict[str, set[str]] = {}
        for coverage_index, coverage in enumerate(chapter.coverage_map):
            coverage_path = f"{path}.coverage_map[{coverage_index}]"
            point = knowledge_by_id.get(coverage.knowledge_point_id)
            if point is None:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="unknown_coverage_knowledge_point",
                        path=f"{coverage_path}.knowledge_point_id",
                        message="Coverage references an undeclared knowledge point.",
                    )
                )
            else:
                covered_knowledge_ids.add(point.id)
            covered_baseline_by_point.setdefault(
                coverage.knowledge_point_id, set()
            ).update(coverage.baseline_content_ids)
            covered_detail_by_point.setdefault(
                coverage.knowledge_point_id, set()
            ).update(coverage.detail_content_ids)
            if coverage.module_id not in module_ids:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="unknown_coverage_module",
                        path=f"{coverage_path}.module_id",
                        message="Coverage references an undeclared module.",
                    )
                )
            for content_id in coverage.baseline_content_ids:
                if content_id not in baseline_ids:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="unknown_coverage_content",
                            path=f"{coverage_path}.baseline_content_ids",
                            message=f"Baseline content {content_id!r} does not exist.",
                        )
                    )
            for content_id in coverage.detail_content_ids:
                if content_id not in detail_ids:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="unknown_coverage_detail",
                            path=f"{coverage_path}.detail_content_ids",
                            message=f"Detailed content {content_id!r} does not exist.",
                        )
                    )
        for point_index, point in enumerate(chapter.knowledge_points):
            if point.id not in covered_knowledge_ids:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="knowledge_point_uncovered",
                        path=f"{path}.knowledge_points[{point_index}].id",
                        message="Every knowledge point must be mapped to baseline teaching content.",
                    )
                )
        for content_id, point_ids in baseline_knowledge_by_content.items():
            for point_id in point_ids:
                if content_id not in covered_baseline_by_point.get(
                    point_id, set()
                ):
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="content_missing_from_coverage",
                            path=f"{path}.coverage_map",
                            message=(
                                f"Baseline content {content_id!r} declares "
                                f"knowledge point {point_id!r} but its coverage entry omits it."
                            ),
                        )
                    )
        for content_id, point_ids in detail_knowledge_by_content.items():
            for point_id in point_ids:
                if content_id not in covered_detail_by_point.get(
                    point_id, set()
                ):
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="content_missing_from_coverage",
                            path=f"{path}.coverage_map",
                            message=(
                                f"Detailed content {content_id!r} declares "
                                f"knowledge point {point_id!r} but its coverage entry omits it."
                            ),
                        )
                    )

        audit = chapter.coverage_audit
        if audit is None:
            return
        if (
            set(audit.source_section_ids) != set(source_by_id)
            or set(audit.knowledge_point_ids) != set(knowledge_by_id)
        ):
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="coverage_audit_incomplete",
                    path=f"{path}.coverage_audit",
                    message="Coverage audit must enumerate every retained source section and knowledge point.",
                )
            )
        if audit.unresolved_items:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="coverage_audit_unresolved",
                    path=f"{path}.coverage_audit.unresolved_items",
                    message="Coverage audit contains unresolved omissions or ambiguities.",
                )
            )

    @staticmethod
    def _validate_teaching_contract(
        chapter: Any,
        path: str,
        issues: list[ValidationIssue],
    ) -> None:
        module_ids = {module.id for module in chapter.modules}
        if chapter.overview is None:
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="chapter_overview_required",
                    path=f"{path}.overview",
                    message="Chapter overview must state the essential question and core-module route.",
                )
            )
        elif (
            len(chapter.overview.module_order)
            != len(set(chapter.overview.module_order))
            or set(chapter.overview.module_order) != module_ids
        ):
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="chapter_overview_module_order_incomplete",
                    path=f"{path}.overview.module_order",
                    message="Chapter overview must order every core module exactly once.",
                )
            )

        knowledge_by_id = {
            point.id: point for point in chapter.knowledge_points
        }
        coverage_by_module: dict[str, set[str]] = {
            module_id: set() for module_id in module_ids
        }
        coverage_count: dict[str, int] = {}
        for coverage in chapter.coverage_map:
            coverage_by_module.setdefault(coverage.module_id, set()).add(
                coverage.knowledge_point_id
            )
            coverage_count[coverage.knowledge_point_id] = (
                coverage_count.get(coverage.knowledge_point_id, 0) + 1
            )
        for point_id, count in coverage_count.items():
            if count > 1:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="duplicate_knowledge_coverage",
                        path=f"{path}.coverage_map",
                        message=f"Knowledge point {point_id!r} must have one responsible core module.",
                    )
                )

        overview_markers = (
            "全章地图",
            "章节地图",
            "学习地图",
            "全章总览",
            "章节总览",
            "chapter map",
            "chapter overview",
        )
        dependency_graph: dict[str, set[str]] = {}
        substantive_kinds = {
            ContentBlockKind.PROSE,
            ContentBlockKind.FORMULA_EXPLANATION,
            ContentBlockKind.DERIVATION,
            ContentBlockKind.COMPARISON,
            ContentBlockKind.WORKED_EXAMPLE,
            ContentBlockKind.CODE_EXPLANATION,
            ContentBlockKind.TABLE,
            ContentBlockKind.MATRIX,
            ContentBlockKind.IMAGE,
            ContentBlockKind.GROUP,
        }
        core_system_kinds = {
            "concept",
            "definition",
            "theorem",
            "mechanism",
            "method",
            "condition",
            "application",
        }
        for module_index, module in enumerate(chapter.modules):
            module_path = f"{path}.modules[{module_index}]"
            normalized_identity = (
                f"{module.title} {module.core_question}".casefold()
            )
            if any(marker in normalized_identity for marker in overview_markers):
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="overview_module_forbidden",
                        path=module_path,
                        message="A chapter map belongs in chapter.overview, not in the core-module list.",
                    )
                )
            dependency_graph[module.id] = set()
            for dependency in module.depends_on_module_ids:
                if dependency not in module_ids:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="unknown_module_dependency",
                            path=f"{module_path}.depends_on_module_ids",
                            message=f"Dependency module {dependency!r} does not exist.",
                        )
                    )
                else:
                    dependency_graph[module.id].add(dependency)

            points = [
                knowledge_by_id[point_id]
                for point_id in module.knowledge_point_ids
                if point_id in knowledge_by_id
            ]
            if not any(
                point.importance.value == "core"
                and point.kind.value in core_system_kinds
                for point in points
            ):
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="core_module_without_core_knowledge",
                        path=f"{module_path}.knowledge_point_ids",
                        message="A core module must own a core conceptual system, not only examples, formulas, tips, or boundaries.",
                    )
                )
            if set(module.knowledge_point_ids) != coverage_by_module.get(
                module.id, set()
            ):
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="module_knowledge_responsibility_mismatch",
                        path=f"{module_path}.knowledge_point_ids",
                        message="Module knowledge responsibility must exactly match the chapter coverage map.",
                    )
                )
            detail_branch_count = sum(
                len(block.detail_branches)
                for block in module.blocks
            ) + sum(
                len(block.detail_branches)
                for segment in module.segments
                for block in segment.blocks
            )
            if detail_branch_count < 1:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="core_module_detail_expansion_required",
                        path=module_path,
                        message="Every core module must publish at least one substantive detailed expansion at a real learning bottleneck.",
                    )
                )
            for segment_index, segment in enumerate(module.segments):
                segment_path = (
                    f"{module_path}.segments[{segment_index}]"
                )
                if not any(
                    block.kind in substantive_kinds
                    for block in segment.blocks
                ):
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="learning_segment_not_substantive",
                            path=f"{segment_path}.blocks",
                            message="A learning segment cannot be only a heading, formula, callout, or model reference.",
                        )
                    )
                if not set(segment.knowledge_point_ids) <= set(
                    module.knowledge_point_ids
                ):
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="segment_knowledge_outside_module",
                            path=f"{segment_path}.knowledge_point_ids",
                            message="A segment may only teach knowledge owned by its core module.",
                        )
                    )

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(module_id: str) -> bool:
            if module_id in visiting:
                return True
            if module_id in visited:
                return False
            visiting.add(module_id)
            has_cycle = any(
                visit(dependency)
                for dependency in dependency_graph.get(module_id, set())
            )
            visiting.remove(module_id)
            visited.add(module_id)
            return has_cycle

        if any(visit(module_id) for module_id in module_ids):
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="module_dependency_cycle",
                    path=f"{path}.modules",
                    message="Core-module dependencies must form an acyclic learning route.",
                )
            )

    @staticmethod
    def _validate_renderable_data(
        block: ContentBlock,
        path: str,
        issues: list[ValidationIssue],
    ) -> None:
        data = block.data
        if block.kind == ContentBlockKind.COMPARISON:
            items = data.get("items")
            has_items = (
                isinstance(items, list)
                and len(items) >= 2
                and all(isinstance(item, dict) for item in items)
            )
            has_pair = isinstance(data.get("left"), dict) and isinstance(
                data.get("right"), dict
            )
            if not has_items and not has_pair:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="comparison_content_required",
                        path=f"{path}.data",
                        message=(
                            "Comparison requires either two or more items or "
                            "both left and right entries."
                        ),
                    )
                )
            if has_items:
                for item_index, item in enumerate(items):
                    title = (
                        item.get("title")
                        or item.get("name")
                        or item.get("label")
                    )
                    body = (
                        item.get("body")
                        or item.get("text")
                        or item.get("description")
                        or item.get("focus")
                        or item.get("value")
                    )
                    if not (
                        isinstance(title, str)
                        and title.strip()
                        and isinstance(body, str)
                        and body.strip()
                    ):
                        issues.append(
                            ValidationIssue(
                                severity="error",
                                code="comparison_item_content_required",
                                path=f"{path}.data.items[{item_index}]",
                                message="Every comparison card requires a visible label and explanation.",
                            )
                        )
        if block.kind == ContentBlockKind.FORMULA_EXPLANATION:
            latex = data.get("latex") or data.get("formula")
            formulae = data.get("formulae")
            has_single = isinstance(latex, str) and bool(latex.strip())
            has_many = (
                isinstance(formulae, list)
                and bool(formulae)
                and all(
                    (
                        isinstance(item, str)
                        and bool(item.strip())
                    )
                    or (
                        isinstance(item, dict)
                        and isinstance(
                            item.get("latex") or item.get("formula"),
                            str,
                        )
                        and bool(
                            (item.get("latex") or item.get("formula")).strip()
                        )
                    )
                    for item in formulae
                )
            )
            if not has_single and not has_many:
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="formula_content_required",
                        path=f"{path}.data",
                        message=(
                            "Formula explanation requires latex/formula or a "
                            "non-empty formulae list."
                        ),
                    )
                )
            explanations = (
                [
                    item.get("explanation") or item.get("text")
                    if isinstance(item, dict)
                    else ""
                    for item in formulae
                ]
                if isinstance(formulae, list) and formulae
                else [data.get("explanation") or data.get("text")]
            )
            if not explanations or any(
                not isinstance(explanation, str)
                or not explanation.strip()
                for explanation in explanations
            ):
                issues.append(
                    ValidationIssue(
                        severity="error",
                        code="formula_explanation_required",
                        path=f"{path}.data",
                        message="Every displayed formula requires adjacent explanatory teaching copy.",
                    )
                )

    def _find_forbidden_keys(
        self,
        value: Any,
        path: str,
        issues: list[ValidationIssue],
    ) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in FORBIDDEN_LEARNER_ANALYSIS_KEYS:
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="learner_analysis_field_forbidden",
                            path=child_path,
                            message=f"Classroom content cannot contain learner-analysis field {key!r}.",
                        )
                    )
                self._find_forbidden_keys(child, child_path, issues)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self._find_forbidden_keys(child, f"{path}[{index}]", issues)

    @staticmethod
    def _validate_effect(
        effect: BindingEffect,
        path: str,
        registered: RegisteredModelRecord,
        issues: list[ValidationIssue],
    ) -> None:
        manifest = registered.manifest
        if (
            effect.kind == BindingEffectKind.SET_STATE
            and effect.target not in {state.id for state in manifest.states}
        ):
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="unknown_model_state",
                    path=f"{path}.target",
                    message="Binding state is not declared by the registered model.",
                )
            )
        elif (
            effect.kind == BindingEffectKind.PERFORM_ACTION
            and effect.target not in {action.id for action in manifest.actions}
        ):
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="unknown_model_action",
                    path=f"{path}.target",
                    message="Binding action is not declared by the registered model.",
                )
            )
        elif (
            effect.kind == BindingEffectKind.HIGHLIGHT_TARGET
            and effect.target not in manifest.targets
        ):
            issues.append(
                ValidationIssue(
                    severity="error",
                    code="unknown_model_target",
                    path=f"{path}.target",
                    message="Binding visual target is not declared by the registered model.",
                )
            )
        if effect.kind == BindingEffectKind.UPDATE_PARAMETERS:
            parameters = {parameter.id: parameter for parameter in manifest.parameters}
            for parameter_id, value in effect.payload.items():
                parameter = parameters.get(parameter_id)
                if parameter is None or not parameter_value_is_valid(parameter, value):
                    issues.append(
                        ValidationIssue(
                            severity="error",
                            code="invalid_model_parameter",
                            path=f"{path}.payload.{parameter_id}",
                            message="Binding parameter update violates the model contract.",
                        )
                    )
