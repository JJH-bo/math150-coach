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
    ) -> None:
        record_id(block.id, f"{path}.id")
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
