from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolQualityTier,
    ToolScope,
)
from app.tools.registry import (
    ToolNotFoundError,
    ToolRegistry,
    ToolRegistryConflictError,
)


class FakeAdapter:
    def __init__(
        self,
        tool_id: str,
        version: str,
        *,
        category: str = "mathematics",
        quality_tier: ToolQualityTier = ToolQualityTier.VERIFIED,
    ) -> None:
        self.definition = ToolDefinition(
            tool_id=tool_id,
            version=version,
            title=f"{tool_id} title",
            description=f"Verified adapter for {tool_id}.",
            category=category,
            quality_tier=quality_tier,
            required_scope=ToolScope.COMPUTE,
            execution_mode=ToolExecutionMode.ASYNC,
            deterministic=True,
            cacheable=True,
            timeout_seconds=30,
            max_artifacts=4,
            max_artifact_bytes=1024,
            input_schema={
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"],
                "additionalProperties": False,
            },
            output_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
                "additionalProperties": False,
            },
            output_media_types=["application/json"],
            quality_gates=["reference_cases"],
            upstream_project="https://example.test/tool",
            license="MIT",
        )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        return ToolExecutionResult(result={"text": arguments["expression"]})


def test_registry_discovers_verified_tools_without_internal_ids() -> None:
    registry = ToolRegistry(
        [
            FakeAdapter("visualization.plot", "1.0.0", category="visualization"),
            FakeAdapter("math.symbolic", "1.0.0"),
        ]
    )

    result = registry.list(query="symbolic")

    assert [item.tool_id for item in result] == ["math.symbolic"]
    assert result[0].quality_tier == ToolQualityTier.VERIFIED


def test_registry_filters_category_and_quality_tier() -> None:
    registry = ToolRegistry(
        [
            FakeAdapter("math.symbolic", "1.0.0"),
            FakeAdapter(
                "math.experimental",
                "0.1.0",
                quality_tier=ToolQualityTier.EXPERIMENTAL,
            ),
            FakeAdapter("visualization.plot", "1.0.0", category="visualization"),
        ]
    )

    result = registry.list(
        category="mathematics",
        quality_tier=ToolQualityTier.VERIFIED,
    )

    assert [item.tool_id for item in result] == ["math.symbolic"]


def test_registry_selects_highest_semantic_version_by_default() -> None:
    registry = ToolRegistry(
        [
            FakeAdapter("math.symbolic", "1.9.0"),
            FakeAdapter("math.symbolic", "1.10.0"),
            FakeAdapter("math.symbolic", "2.0.0"),
        ]
    )

    assert registry.get("math.symbolic").definition.version == "2.0.0"
    assert registry.get("math.symbolic", "1.9.0").definition.version == "1.9.0"


def test_registry_rejects_duplicate_tool_versions() -> None:
    with pytest.raises(ToolRegistryConflictError, match="math.symbolic@1.0.0"):
        ToolRegistry(
            [
                FakeAdapter("math.symbolic", "1.0.0"),
                FakeAdapter("math.symbolic", "1.0.0"),
            ]
        )


def test_registry_reports_unknown_tool_or_version() -> None:
    registry = ToolRegistry([FakeAdapter("math.symbolic", "1.0.0")])

    with pytest.raises(ToolNotFoundError, match="math.unknown"):
        registry.get("math.unknown")
    with pytest.raises(ToolNotFoundError, match="2.0.0"):
        registry.get("math.symbolic", "2.0.0")


def test_tool_definition_rejects_unusable_contracts() -> None:
    payload = FakeAdapter("math.symbolic", "1.0.0").definition.model_dump()
    payload["version"] = "latest"
    payload["output_media_types"] = []

    with pytest.raises(ValidationError):
        ToolDefinition.model_validate(payload)
