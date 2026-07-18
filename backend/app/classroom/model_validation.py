from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.classroom.model_contracts import (
    ModelParameterSpec,
    ModelParameterType,
    ModelScenarioCommandKind,
    TeachingModelManifest,
)


REQUIRED_LIFECYCLE_METHODS = (
    "mount",
    "update",
    "perform",
    "pause",
    "resume",
    "reset",
    "snapshot",
    "dispose",
)
FORBIDDEN_SOURCE_PATTERNS = (
    ("require(", "CommonJS module loading"),
    ("process.", "Node process access"),
    ("child_process", "child process access"),
    ("fs.", "server filesystem access"),
    ("Deno.", "Deno runtime access"),
    ("WebSocket(", "direct network socket access"),
    ("fetch(", "direct network request access"),
    ("XMLHttpRequest", "direct network request access"),
)


class ModelValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: Literal["error", "warning"]
    code: str
    path: str
    message: str


class ModelValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    issues: list[ModelValidationIssue]


class TeachingModelValidator:
    def validate(
        self,
        manifest: TeachingModelManifest,
        source: str,
    ) -> ModelValidationReport:
        issues: list[ModelValidationIssue] = []
        for token, capability in FORBIDDEN_SOURCE_PATTERNS:
            if token in source:
                issues.append(
                    self._error(
                        "forbidden_model_source_capability",
                        "source",
                        f"Teaching model source cannot use {capability}.",
                    )
                )
        if not re.search(
            r"export\s+function\s+createTeachingModel\s*\(",
            source,
        ):
            issues.append(
                self._error(
                    "missing_model_factory_export",
                    "source",
                    "Source must export function createTeachingModel(context).",
                )
            )
        for method in REQUIRED_LIFECYCLE_METHODS:
            if not re.search(rf"\b{re.escape(method)}\s*\(", source):
                issues.append(
                    self._error(
                        "missing_lifecycle_method",
                        "source",
                        f"Model factory must return lifecycle method {method}().",
                    )
                )

        states = {state.id for state in manifest.states}
        actions = {action.id for action in manifest.actions}
        parameters = {parameter.id: parameter for parameter in manifest.parameters}
        for scenario_index, scenario in enumerate(manifest.scenarios):
            path = f"manifest.scenarios[{scenario_index}]"
            if scenario.initial_state not in states:
                issues.append(
                    self._error(
                        "unknown_scenario_state",
                        f"{path}.initial_state",
                        f"Scenario state {scenario.initial_state!r} is not declared.",
                    )
                )
            for parameter_id, value in scenario.parameters.items():
                parameter = parameters.get(parameter_id)
                if parameter is None:
                    issues.append(
                        self._error(
                            "unknown_scenario_parameter",
                            f"{path}.parameters.{parameter_id}",
                            f"Scenario parameter {parameter_id!r} is not declared.",
                        )
                    )
                elif not parameter_value_is_valid(parameter, value):
                    issues.append(
                        self._error(
                            "invalid_scenario_parameter",
                            f"{path}.parameters.{parameter_id}",
                            f"Scenario value is invalid for parameter {parameter_id!r}.",
                        )
                    )
            for command_index, command in enumerate(scenario.commands):
                command_path = f"{path}.commands[{command_index}]"
                if (
                    command.kind == ModelScenarioCommandKind.SET_STATE
                    and command.target not in states
                ):
                    issues.append(
                        self._error(
                            "unknown_scenario_state",
                            f"{command_path}.target",
                            f"Scenario state {command.target!r} is not declared.",
                        )
                    )
                if (
                    command.kind == ModelScenarioCommandKind.PERFORM_ACTION
                    and command.target not in actions
                ):
                    issues.append(
                        self._error(
                            "unknown_scenario_action",
                            f"{command_path}.target",
                            f"Scenario action {command.target!r} is not declared.",
                        )
                    )
                if command.kind == ModelScenarioCommandKind.UPDATE_PARAMETERS:
                    for parameter_id, value in command.payload.items():
                        parameter = parameters.get(parameter_id)
                        if parameter is None:
                            issues.append(
                                self._error(
                                    "unknown_scenario_parameter",
                                    f"{command_path}.payload.{parameter_id}",
                                    f"Scenario parameter {parameter_id!r} is not declared.",
                                )
                            )
                        elif not parameter_value_is_valid(parameter, value):
                            issues.append(
                                self._error(
                                    "invalid_scenario_parameter",
                                    f"{command_path}.payload.{parameter_id}",
                                    f"Scenario value is invalid for parameter {parameter_id!r}.",
                                )
                            )
        return ModelValidationReport(
            passed=not any(issue.severity == "error" for issue in issues),
            issues=issues,
        )

    @staticmethod
    def _error(code: str, path: str, message: str) -> ModelValidationIssue:
        return ModelValidationIssue(
            severity="error",
            code=code,
            path=path,
            message=message,
        )


def parameter_value_is_valid(parameter: ModelParameterSpec, value: Any) -> bool:
    if parameter.type == ModelParameterType.NUMBER:
        valid_type = not isinstance(value, bool) and isinstance(value, (int, float))
    elif parameter.type == ModelParameterType.INTEGER:
        valid_type = not isinstance(value, bool) and isinstance(value, int)
    elif parameter.type == ModelParameterType.BOOLEAN:
        valid_type = isinstance(value, bool)
    elif parameter.type == ModelParameterType.STRING:
        valid_type = isinstance(value, str)
    else:
        valid_type = value in parameter.choices
    if not valid_type:
        return False
    if parameter.minimum is not None and value < parameter.minimum:
        return False
    if parameter.maximum is not None and value > parameter.maximum:
        return False
    return True
