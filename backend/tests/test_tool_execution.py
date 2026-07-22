from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pytest

from app.classroom.idempotency import IdempotencyConflictError, IdempotencyLedger
from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolJobState,
    ToolProducedArtifact,
    ToolQualityTier,
    ToolScope,
)
from app.tools.execution import (
    ToolArgumentValidationError,
    ToolExecutionService,
    ToolScopeDeniedError,
)
from app.tools.registry import ToolRegistry
from app.tools.repository import ToolJobRepository


class Adapter:
    def __init__(
        self,
        *,
        behavior: str = "success",
        required_scope: ToolScope = ToolScope.COMPUTE,
    ) -> None:
        self.behavior = behavior
        self.definition = ToolDefinition(
            tool_id="math.symbolic",
            version="1.0.0",
            title="Symbolic mathematics",
            description="Reference test adapter.",
            category="mathematics",
            quality_tier=ToolQualityTier.VERIFIED,
            required_scope=required_scope,
            execution_mode=ToolExecutionMode.ASYNC,
            deterministic=True,
            cacheable=True,
            timeout_seconds=1,
            max_artifacts=2,
            max_artifact_bytes=1024,
            input_schema={
                "type": "object",
                "properties": {"expression": {"type": "string", "minLength": 1}},
                "required": ["expression"],
                "additionalProperties": False,
            },
            output_schema={
                "type": "object",
                "properties": {"text": {"type": "string"}},
                "required": ["text"],
                "additionalProperties": False,
            },
            output_media_types=["application/json", "text/plain"],
            quality_gates=["reference_cases"],
            upstream_project="https://example.test/symbolic",
            license="MIT",
        )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        if self.behavior == "raise":
            raise ValueError("adapter exploded")
        if self.behavior == "slow":
            time.sleep(0.08)
        if self.behavior == "invalid_output":
            return ToolExecutionResult(result={"wrong": True})
        if self.behavior == "artifact":
            (context.work_dir / "result.txt").write_bytes(b"2*x\n")
            return ToolExecutionResult(
                result={"text": "2*x"},
                artifacts=[
                    ToolProducedArtifact(
                        name="result.txt",
                        media_type="text/plain; charset=utf-8",
                        source_path="result.txt",
                    )
                ],
            )
        return ToolExecutionResult(result={"text": arguments["expression"]})


def service(
    tmp_path: Path,
    adapter: Adapter | None = None,
    *,
    timeout_cap_seconds: float | None = None,
) -> ToolExecutionService:
    return ToolExecutionService(
        ToolRegistry([adapter or Adapter()]),
        ToolJobRepository(tmp_path),
        IdempotencyLedger(tmp_path / "tool-idempotency"),
        timeout_cap_seconds=timeout_cap_seconds,
    )


def submit(
    runtime: ToolExecutionService,
    *,
    arguments: dict[str, Any] | None = None,
    key: str = "tool-submit-1",
    scopes: set[ToolScope] | None = None,
):
    return runtime.submit(
        tool_id="math.symbolic",
        tool_version=None,
        arguments=arguments or {"expression": "x + x"},
        idempotency_key=key,
        granted_scopes=scopes or {ToolScope.COMPUTE},
    )


def test_submit_rejects_missing_required_scope_before_job_creation(tmp_path: Path) -> None:
    runtime = service(tmp_path)

    with pytest.raises(ToolScopeDeniedError, match="studio.compute"):
        submit(runtime, scopes={ToolScope.READ})

    assert not (tmp_path / "tool-jobs").exists()


def test_submit_rejects_arguments_against_registered_json_schema(tmp_path: Path) -> None:
    runtime = service(tmp_path)

    with pytest.raises(ToolArgumentValidationError, match="expression"):
        submit(runtime, arguments={"unexpected": 1})


def test_submit_is_durable_and_idempotent(tmp_path: Path) -> None:
    runtime = service(tmp_path)

    first = submit(runtime)
    replay = submit(runtime)

    assert first == replay
    assert first.state == ToolJobState.QUEUED
    assert runtime.get(first.job_id) == first


def test_submit_rejects_idempotency_key_reuse_with_different_arguments(
    tmp_path: Path,
) -> None:
    runtime = service(tmp_path)
    submit(runtime, arguments={"expression": "x"})

    with pytest.raises(IdempotencyConflictError):
        submit(runtime, arguments={"expression": "y"})


def test_run_persists_success_result_and_validated_artifact(tmp_path: Path) -> None:
    runtime = service(tmp_path, Adapter(behavior="artifact"))
    queued = submit(runtime)

    completed = runtime.run(queued.job_id)

    assert completed.state == ToolJobState.SUCCEEDED
    assert completed.result == {"text": "2*x"}
    assert completed.started_at and completed.finished_at
    assert completed.artifacts[0].sha256.startswith("sha256:")
    assert runtime.artifact(completed.job_id, "result.txt").read_bytes() == b"2*x\n"


def test_run_turns_adapter_exception_into_structured_failure(tmp_path: Path) -> None:
    runtime = service(tmp_path, Adapter(behavior="raise"))
    queued = submit(runtime)

    failed = runtime.run(queued.job_id)

    assert failed.state == ToolJobState.FAILED
    assert failed.error is not None
    assert failed.error.code == "tool_execution_failed"
    assert "adapter exploded" in failed.error.message


def test_run_rejects_adapter_output_that_breaks_registered_schema(tmp_path: Path) -> None:
    runtime = service(tmp_path, Adapter(behavior="invalid_output"))
    queued = submit(runtime)

    failed = runtime.run(queued.job_id)

    assert failed.state == ToolJobState.FAILED
    assert failed.error is not None
    assert failed.error.code == "tool_output_invalid"


def test_run_records_timeout_without_promoting_success(tmp_path: Path) -> None:
    runtime = service(
        tmp_path,
        Adapter(behavior="slow"),
        timeout_cap_seconds=0.01,
    )
    queued = submit(runtime)

    failed = runtime.run(queued.job_id)

    assert failed.state == ToolJobState.FAILED
    assert failed.error is not None
    assert failed.error.code == "tool_timeout"
    assert failed.error.retryable is True


def test_cancel_queued_job_is_terminal_and_idempotent(tmp_path: Path) -> None:
    runtime = service(tmp_path)
    queued = submit(runtime)

    cancelled = runtime.cancel(queued.job_id)
    replay = runtime.cancel(queued.job_id)

    assert cancelled.state == ToolJobState.CANCELLED
    assert cancelled.finished_at
    assert replay == cancelled
