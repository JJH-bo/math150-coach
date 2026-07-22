from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import sympy as sp

from app.tools.adapters.symbolic_math import (
    SymbolicMathAdapter,
    SymbolicMathInputError,
)
from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolProducedArtifact,
    ToolQualityTier,
    ToolScope,
)


PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53)


class MathVerifyInputError(ValueError):
    pass


class MathVerifyAdapter:
    definition = ToolDefinition(
        tool_id="math.verify",
        version="1.0.0",
        title="Independent mathematical expression verification",
        description=(
            "Cross-check two declared expressions using exact symbolic reasoning "
            "and deterministic domain-aware numeric samples, reporting assumptions, "
            "excluded points, uncertainty, and a concrete counterexample when found."
        ),
        category="mathematics",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.COMPUTE,
        execution_mode=ToolExecutionMode.ASYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=30,
        max_artifacts=8,
        max_artifact_bytes=16 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["left_expression", "right_expression", "symbols"],
            "properties": {
                "left_expression": {"type": "string", "minLength": 1, "maxLength": 20_000},
                "right_expression": {"type": "string", "minLength": 1, "maxLength": 20_000},
                "symbols": {
                    "type": "object",
                    "maxProperties": 16,
                    "additionalProperties": {
                        "type": "object",
                        "additionalProperties": {"type": "boolean"},
                    },
                },
                "domains": {
                    "type": "object",
                    "maxProperties": 16,
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 2,
                        "maxItems": 2,
                    },
                },
                "tolerance": {
                    "type": "number",
                    "minimum": 1e-15,
                    "maximum": 0.1,
                },
                "sample_count": {"type": "integer", "minimum": 3, "maximum": 200},
            },
        },
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": [
                "verdict",
                "exact_equivalent",
                "symbolic_difference",
                "variables",
                "assumptions",
                "domains",
                "tolerance",
                "tested_sample_count",
                "excluded_sample_count",
                "excluded_points",
                "max_absolute_error",
                "max_relative_error",
                "counterexample",
                "sample_evidence",
            ],
            "properties": {
                "verdict": {
                    "type": "string",
                    "enum": ["equivalent", "not_equivalent", "inconclusive"],
                },
                "exact_equivalent": {"type": "boolean"},
                "symbolic_difference": {"type": "string"},
                "variables": {"type": "array", "items": {"type": "string"}},
                "assumptions": {"type": "object"},
                "domains": {"type": "object"},
                "tolerance": {"type": "number"},
                "tested_sample_count": {"type": "integer"},
                "excluded_sample_count": {"type": "integer"},
                "excluded_points": {"type": "array"},
                "max_absolute_error": {"type": ["number", "null"]},
                "max_relative_error": {"type": ["number", "null"]},
                "counterexample": {"type": ["object", "null"]},
                "sample_evidence": {"type": "array"},
            },
        },
        output_media_types=["application/json", "text/csv"],
        quality_gates=[
            "exact_symbolic_first",
            "domain_assumption_reporting",
            "deterministic_numeric_samples",
            "counterexample_evidence",
            "inconclusive_is_not_equivalent",
        ],
        upstream_project="https://www.sympy.org/ and https://numpy.org/",
        license="BSD-3-Clause",
    )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        parser = SymbolicMathAdapter()
        try:
            symbols, assumptions = parser._symbols(arguments.get("symbols"))
            left = parser._parse_required_expression(
                arguments.get("left_expression"), symbols
            )
            right = parser._parse_required_expression(
                arguments.get("right_expression"), symbols
            )
            parser._check_complexity(left)
            parser._check_complexity(right)
            difference = sp.simplify(left - right)
            parser._check_complexity(difference)
        except SymbolicMathInputError as exc:
            raise MathVerifyInputError(str(exc)) from exc

        tolerance = self._tolerance(arguments.get("tolerance", 1e-9))
        sample_count = arguments.get("sample_count", 32)
        if (
            isinstance(sample_count, bool)
            or not isinstance(sample_count, int)
            or not 3 <= sample_count <= 200
        ):
            raise MathVerifyInputError("sample_count must be an integer from 3 to 200")
        domains = self._domains(arguments.get("domains", {}), symbols, assumptions)
        ordered_names = sorted(symbols)
        ordered_symbols = [symbols[name] for name in ordered_names]
        left_function = sp.lambdify(ordered_symbols, left, modules=["numpy"])
        right_function = sp.lambdify(ordered_symbols, right, modules=["numpy"])

        samples: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        counterexample: dict[str, Any] | None = None
        max_absolute_error: float | None = None
        max_relative_error: float | None = None
        for inputs in self._sample_inputs(
            ordered_names,
            domains,
            assumptions,
            sample_count,
        ):
            values = [inputs[name] for name in ordered_names]
            try:
                with np.errstate(all="ignore"):
                    left_value = self._real_scalar(left_function(*values))
                    right_value = self._real_scalar(right_function(*values))
            except (ValueError, TypeError, ZeroDivisionError, OverflowError):
                excluded.append(
                    {"inputs": inputs, "reason": "undefined_or_nonfinite"}
                )
                continue
            absolute_error = abs(left_value - right_value)
            denominator = max(abs(left_value), abs(right_value), 1e-300)
            relative_error = absolute_error / denominator
            evidence = {
                "inputs": inputs,
                "left": left_value,
                "right": right_value,
                "absolute_error": absolute_error,
                "relative_error": relative_error,
            }
            samples.append(evidence)
            max_absolute_error = max(max_absolute_error or 0.0, absolute_error)
            max_relative_error = max(max_relative_error or 0.0, relative_error)
            if counterexample is None and absolute_error > tolerance and relative_error > tolerance:
                counterexample = evidence

        exact_equivalent = bool(difference == 0)
        if exact_equivalent:
            verdict = "equivalent"
        elif counterexample is not None:
            verdict = "not_equivalent"
        else:
            verdict = "inconclusive"
        result = {
            "verdict": verdict,
            "exact_equivalent": exact_equivalent,
            "symbolic_difference": sp.sstr(difference),
            "variables": ordered_names,
            "assumptions": assumptions,
            "domains": domains,
            "tolerance": tolerance,
            "tested_sample_count": len(samples),
            "excluded_sample_count": len(excluded),
            "excluded_points": excluded[:50],
            "max_absolute_error": max_absolute_error,
            "max_relative_error": max_relative_error,
            "counterexample": counterexample,
            "sample_evidence": samples,
        }
        artifacts = self._write_artifacts(context.work_dir, result, ordered_names)
        return ToolExecutionResult(
            result=result,
            warnings=(
                ["numeric evidence was inconclusive; do not claim equivalence"]
                if verdict == "inconclusive"
                else []
            ),
            artifacts=artifacts,
            metrics={
                "tested_sample_count": len(samples),
                "excluded_sample_count": len(excluded),
            },
        )

    def _domains(
        self,
        raw: Any,
        symbols: dict[str, sp.Symbol],
        assumptions: dict[str, dict[str, bool]],
    ) -> dict[str, list[float]]:
        if not isinstance(raw, dict):
            raise MathVerifyInputError("domains must be an object")
        unknown = set(raw) - set(symbols)
        if unknown:
            raise MathVerifyInputError(f"domains reference undeclared symbols: {sorted(unknown)}")
        domains: dict[str, list[float]] = {}
        for name in sorted(symbols):
            declared = raw.get(name)
            if declared is None:
                symbol_assumptions = assumptions.get(name, {})
                if symbol_assumptions.get("positive"):
                    declared = [0.1, 5.0]
                elif symbol_assumptions.get("negative"):
                    declared = [-5.0, -0.1]
                elif symbol_assumptions.get("nonnegative"):
                    declared = [0.0, 5.0]
                elif symbol_assumptions.get("nonpositive"):
                    declared = [-5.0, 0.0]
                else:
                    declared = [-5.0, 5.0]
            if not isinstance(declared, list) or len(declared) != 2:
                raise MathVerifyInputError(f"domain for {name} must contain lower and upper")
            lower = self._finite(declared[0], f"domain {name}")
            upper = self._finite(declared[1], f"domain {name}")
            if not lower < upper:
                raise MathVerifyInputError(f"domain for {name} must be strictly increasing")
            domains[name] = [lower, upper]
        return domains

    def _sample_inputs(
        self,
        names: list[str],
        domains: dict[str, list[float]],
        assumptions: dict[str, dict[str, bool]],
        count: int,
    ) -> list[dict[str, float]]:
        if not names:
            return [{}]
        output = []
        for index in range(count):
            point: dict[str, float] = {}
            for dimension, name in enumerate(names):
                lower, upper = domains[name]
                if index == 0:
                    fraction = 0.0
                elif index == 1:
                    fraction = 1.0
                elif index == 2:
                    fraction = 0.5
                else:
                    fraction = self._van_der_corput(index - 2, PRIMES[dimension])
                value = lower + fraction * (upper - lower)
                if assumptions.get(name, {}).get("integer"):
                    value = float(round(value))
                point[name] = value
            if point not in output:
                output.append(point)
        return output

    @staticmethod
    def _van_der_corput(index: int, base: int) -> float:
        result = 0.0
        denominator = 1.0
        while index:
            index, remainder = divmod(index, base)
            denominator *= base
            result += remainder / denominator
        return result

    @staticmethod
    def _real_scalar(raw: Any) -> float:
        array = np.asarray(raw)
        if array.size != 1:
            raise ValueError("expression is not scalar")
        value = complex(array.reshape(-1)[0])
        if not math.isfinite(value.real) or not math.isfinite(value.imag):
            raise ValueError("expression is non-finite")
        if abs(value.imag) > 1e-12:
            raise ValueError("expression is not real on this domain")
        return float(value.real)

    @staticmethod
    def _finite(raw: Any, name: str) -> float:
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise MathVerifyInputError(f"{name} values must be numbers")
        value = float(raw)
        if not math.isfinite(value):
            raise MathVerifyInputError(f"{name} values must be finite")
        return value

    def _tolerance(self, raw: Any) -> float:
        value = self._finite(raw, "tolerance")
        if not 1e-15 <= value <= 0.1:
            raise MathVerifyInputError("tolerance must be between 1e-15 and 0.1")
        return value

    @staticmethod
    def _write_artifacts(
        work_dir: Path,
        result: dict[str, Any],
        variable_names: list[str],
    ) -> list[ToolProducedArtifact]:
        work_dir.mkdir(parents=True, exist_ok=True)
        json_path = work_dir / "verification-result.json"
        csv_path = work_dir / "verification-samples.csv"
        json_path.write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n",
            encoding="utf-8",
        )
        with csv_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(
                [*variable_names, "left", "right", "absolute_error", "relative_error"]
            )
            for sample in result["sample_evidence"]:
                writer.writerow(
                    [
                        *[sample["inputs"][name] for name in variable_names],
                        sample["left"],
                        sample["right"],
                        sample["absolute_error"],
                        sample["relative_error"],
                    ]
                )
        return [
            ToolProducedArtifact(
                name=json_path.name,
                media_type="application/json",
                source_path=json_path.name,
            ),
            ToolProducedArtifact(
                name=csv_path.name,
                media_type="text/csv",
                source_path=csv_path.name,
            ),
        ]
