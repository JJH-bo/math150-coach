from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from app.classroom.hashing import content_hash
from app.classroom.idempotency import IdempotencyLedger
from app.tools.contracts import (
    ToolError,
    ToolExecutionContext,
    ToolExecutionResult,
    ToolJob,
    ToolJobState,
    ToolScope,
)
from app.tools.registry import ToolRegistry
from app.tools.repository import ToolJobRepository, ToolJobRepositoryError


class ToolExecutionServiceError(ValueError):
    pass


class ToolScopeDeniedError(ToolExecutionServiceError):
    pass


class ToolArgumentValidationError(ToolExecutionServiceError):
    pass


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class ToolExecutionService:
    def __init__(
        self,
        registry: ToolRegistry,
        repository: ToolJobRepository,
        idempotency: IdempotencyLedger,
        *,
        timeout_cap_seconds: float | None = None,
    ) -> None:
        self.registry = registry
        self.repository = repository
        self.idempotency = idempotency
        self.timeout_cap_seconds = timeout_cap_seconds

    def submit(
        self,
        *,
        tool_id: str,
        tool_version: str | None,
        arguments: dict[str, Any],
        idempotency_key: str,
        granted_scopes: set[ToolScope],
    ) -> ToolJob:
        adapter = self.registry.get(tool_id, tool_version)
        definition = adapter.definition
        if definition.required_scope not in granted_scopes:
            raise ToolScopeDeniedError(
                f"tool {definition.tool_id} requires scope "
                f"{definition.required_scope.value}"
            )
        self._validate_arguments(arguments, definition.input_schema)
        if not idempotency_key.strip() or len(idempotency_key) > 200:
            raise ToolArgumentValidationError(
                "idempotency key must contain 1 to 200 characters"
            )

        request = {
            "tool_id": definition.tool_id,
            "tool_version": definition.version,
            "arguments": arguments,
            "granted_scopes": sorted(scope.value for scope in granted_scopes),
        }

        def create() -> dict[str, Any]:
            job = ToolJob(
                job_id=f"tj-{uuid.uuid4().hex[:24]}",
                tool_id=definition.tool_id,
                tool_version=definition.version,
                required_scope=definition.required_scope,
                state=ToolJobState.QUEUED,
                argument_hash=content_hash(arguments),
                arguments=arguments,
                created_at=utc_now(),
            )
            return self.repository.create(job).model_dump(mode="json", exclude_none=True)

        response = self.idempotency.execute(
            f"tool-submit:{definition.tool_id}",
            idempotency_key,
            request,
            create,
        )
        return ToolJob.model_validate(response)

    def run(self, job_id: str) -> ToolJob:
        job = self.repository.get(job_id)
        if job.state in {
            ToolJobState.SUCCEEDED,
            ToolJobState.FAILED,
            ToolJobState.CANCELLED,
        }:
            return job
        if job.cancellation_requested:
            return self._cancel_terminal(job)

        adapter = self.registry.get(job.tool_id, job.tool_version)
        definition = adapter.definition
        running = self.repository.update(
            job.model_copy(
                update={
                    "state": ToolJobState.RUNNING,
                    "started_at": utc_now(),
                    "error": None,
                }
            )
        )
        context = ToolExecutionContext(
            job_id=running.job_id,
            work_dir=self.repository.work_dir(running.job_id),
            is_cancellation_requested=lambda: self.repository.get(
                running.job_id
            ).cancellation_requested,
        )
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="studio-tool")
        future = executor.submit(adapter.execute, dict(running.arguments), context)
        timeout = float(definition.timeout_seconds)
        if self.timeout_cap_seconds is not None:
            timeout = min(timeout, self.timeout_cap_seconds)
        try:
            output = ToolExecutionResult.model_validate(future.result(timeout=timeout))
            self._validate_output(output.result, definition.output_schema)
            if len(output.artifacts) > definition.max_artifacts:
                raise ToolJobRepositoryError(
                    f"adapter produced {len(output.artifacts)} artifacts, "
                    f"limit is {definition.max_artifacts}"
                )
            remaining_bytes = definition.max_artifact_bytes
            artifacts = []
            for produced in output.artifacts:
                artifact = self.repository.promote_artifact(
                    running.job_id,
                    produced,
                    max_artifact_bytes=remaining_bytes,
                )
                remaining_bytes -= artifact.size_bytes
                artifacts.append(artifact)
            latest = self.repository.get(running.job_id)
            if latest.cancellation_requested:
                return self._cancel_terminal(latest)
            return self.repository.update(
                latest.model_copy(
                    update={
                        "state": ToolJobState.SUCCEEDED,
                        "finished_at": utc_now(),
                        "result": output.result,
                        "warnings": output.warnings,
                        "artifacts": artifacts,
                        "metrics": output.metrics,
                        "error": None,
                    }
                )
            )
        except FutureTimeoutError:
            future.cancel()
            return self._fail(
                running,
                ToolError(
                    code="tool_timeout",
                    message=(
                        f"tool {running.tool_id}@{running.tool_version} exceeded "
                        f"the {timeout:g} second execution limit"
                    ),
                    retryable=True,
                    repair_hint="Reduce the input size or choose a bounded operation.",
                ),
            )
        except _ToolOutputValidationError as exc:
            return self._fail(
                running,
                ToolError(
                    code="tool_output_invalid",
                    message=str(exc),
                    retryable=False,
                    repair_hint="Use a verified adapter version with a valid output contract.",
                ),
            )
        except ToolJobRepositoryError as exc:
            return self._fail(
                running,
                ToolError(
                    code="artifact_invalid",
                    message=str(exc)[:4000],
                    retryable=False,
                    repair_hint="Reduce or repair the declared artifact set.",
                ),
            )
        except Exception as exc:
            return self._fail(
                running,
                ToolError(
                    code="tool_execution_failed",
                    message=str(exc)[:4000] or type(exc).__name__,
                    retryable=False,
                    repair_hint="Inspect the arguments and retry with a verified operation.",
                ),
            )
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def get(self, job_id: str) -> ToolJob:
        return self.repository.get(job_id)

    def cancel(self, job_id: str) -> ToolJob:
        job = self.repository.get(job_id)
        if job.state in {
            ToolJobState.SUCCEEDED,
            ToolJobState.FAILED,
            ToolJobState.CANCELLED,
        }:
            return job
        requested = self.repository.request_cancel(job_id)
        if requested.state == ToolJobState.QUEUED:
            return self._cancel_terminal(requested)
        return requested

    def artifact(self, job_id: str, name: str) -> Path:
        return self.repository.artifact_path(job_id, name)

    def _cancel_terminal(self, job: ToolJob) -> ToolJob:
        return self.repository.update(
            job.model_copy(
                update={
                    "state": ToolJobState.CANCELLED,
                    "finished_at": job.finished_at or utc_now(),
                    "cancellation_requested": True,
                    "error": ToolError(
                        code="tool_cancelled",
                        message="tool job was cancelled",
                        retryable=True,
                        repair_hint="Submit a new job when execution should resume.",
                    ),
                }
            )
        )

    def _fail(self, job: ToolJob, error: ToolError) -> ToolJob:
        latest = self.repository.get(job.job_id)
        return self.repository.update(
            latest.model_copy(
                update={
                    "state": ToolJobState.FAILED,
                    "finished_at": utc_now(),
                    "error": error,
                }
            )
        )

    @staticmethod
    def _validate_arguments(
        arguments: dict[str, Any], schema: dict[str, Any]
    ) -> None:
        errors = sorted(
            Draft202012Validator(schema).iter_errors(arguments),
            key=lambda item: list(item.absolute_path),
        )
        if errors:
            error = errors[0]
            path = ".".join(str(item) for item in error.absolute_path) or "arguments"
            raise ToolArgumentValidationError(f"{path}: {error.message}")

    @staticmethod
    def _validate_output(result: dict[str, Any], schema: dict[str, Any]) -> None:
        errors = sorted(
            Draft202012Validator(schema).iter_errors(result),
            key=lambda item: list(item.absolute_path),
        )
        if errors:
            error = errors[0]
            path = ".".join(str(item) for item in error.absolute_path) or "result"
            raise _ToolOutputValidationError(f"{path}: {error.message}")


class _ToolOutputValidationError(ValueError):
    pass
