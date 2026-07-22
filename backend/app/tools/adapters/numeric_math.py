from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Callable

import numpy as np
import sympy as sp
from scipy import integrate, interpolate, optimize, stats

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


OPERATIONS = (
    "statistics",
    "linear_solve",
    "eigenvalues",
    "quadrature",
    "root",
    "minimize_scalar",
    "interpolate",
    "ode",
    "fft",
    "distribution",
)
MAX_VALUES = 20_000
MAX_MATRIX_DIMENSION = 200
DEFAULT_TOLERANCE = 1e-9


class NumericMathInputError(ValueError):
    pass


class NumericMathAdapter:
    definition = ToolDefinition(
        tool_id="math.numeric",
        version="1.0.0",
        title="Verified numerical mathematics",
        description=(
            "Run bounded numerical statistics, linear algebra, quadrature, root "
            "finding, scalar optimization, interpolation, ODE, FFT, and named "
            "probability distribution operations without arbitrary code execution."
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
            "required": ["operation"],
            "properties": {
                "operation": {"type": "string", "enum": list(OPERATIONS)},
                "values": {"type": "array", "maxItems": MAX_VALUES},
                "quantiles": {
                    "type": "array",
                    "items": {"type": "number", "minimum": 0, "maximum": 1},
                    "maxItems": 101,
                },
                "matrix": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "number"}},
                    "maxItems": MAX_MATRIX_DIMENSION,
                },
                "vector": {"type": "array", "items": {"type": "number"}},
                "expression": {"type": "string", "maxLength": 20_000},
                "expressions": {
                    "type": "array",
                    "items": {"type": "string", "maxLength": 20_000},
                    "maxItems": 64,
                },
                "variable": {"type": "string", "maxLength": 64},
                "variables": {
                    "type": "array",
                    "items": {"type": "string", "maxLength": 64},
                    "maxItems": 65,
                },
                "interval": {
                    "type": "array",
                    "prefixItems": [
                        {"type": ["number", "string"]},
                        {"type": ["number", "string"]},
                    ],
                    "minItems": 2,
                    "maxItems": 2,
                },
                "bracket": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 2,
                    "maxItems": 2,
                },
                "bounds": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 2,
                    "maxItems": 2,
                },
                "tolerance": {"type": "number", "exclusiveMinimum": 0},
                "x": {"type": "array", "items": {"type": "number"}},
                "y": {"type": "array", "items": {"type": "number"}},
                "query_points": {
                    "type": "array",
                    "items": {"type": "number"},
                    "maxItems": MAX_VALUES,
                },
                "method": {"type": "string", "maxLength": 40},
                "initial_values": {
                    "type": "array",
                    "items": {"type": "number"},
                    "maxItems": 64,
                },
                "sample_count": {"type": "integer", "minimum": 2, "maximum": 5000},
                "sample_spacing": {"type": "number", "exclusiveMinimum": 0},
                "distribution": {
                    "type": "string",
                    "enum": ["normal", "binomial", "poisson"],
                },
                "distribution_operation": {
                    "type": "string",
                    "enum": ["pdf", "pmf", "cdf", "ppf"],
                },
                "parameters": {
                    "type": "object",
                    "additionalProperties": {"type": "number"},
                    "maxProperties": 10,
                },
                "points": {
                    "type": "array",
                    "items": {"type": "number"},
                    "maxItems": MAX_VALUES,
                },
            },
        },
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["operation", "method", "success", "scalar", "values", "details"],
            "properties": {
                "operation": {"type": "string"},
                "method": {"type": "string"},
                "success": {"type": "boolean"},
                "scalar": {"type": ["number", "null"]},
                "values": {"type": "array"},
                "details": {"type": "object"},
            },
        },
        output_media_types=["application/json", "text/csv"],
        quality_gates=[
            "finite_outputs",
            "convergence_reporting",
            "reference_cases",
            "safe_structured_expressions",
            "bounded_arrays",
        ],
        upstream_project="https://numpy.org/ and https://scipy.org/",
        license="BSD-3-Clause",
    )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        operation = str(arguments.get("operation", ""))
        if operation not in OPERATIONS:
            raise NumericMathInputError(f"unsupported operation: {operation!r}")
        tolerance = self._tolerance(arguments.get("tolerance", DEFAULT_TOLERANCE))
        handlers: dict[str, Callable[[dict[str, Any], float], dict[str, Any]]] = {
            "statistics": self._statistics,
            "linear_solve": self._linear_solve,
            "eigenvalues": self._eigenvalues,
            "quadrature": self._quadrature,
            "root": self._root,
            "minimize_scalar": self._minimize_scalar,
            "interpolate": self._interpolate,
            "ode": self._ode,
            "fft": self._fft,
            "distribution": self._distribution,
        }
        result = handlers[operation](arguments, tolerance)
        self._require_json_finite(result)
        artifacts = self._write_artifacts(context.work_dir, result)
        point_count = len(result["values"])
        return ToolExecutionResult(
            result=result,
            artifacts=artifacts,
            metrics={"output_value_count": point_count},
        )

    def _statistics(self, arguments: dict[str, Any], _: float) -> dict[str, Any]:
        values = self._vector(arguments.get("values"), "values", minimum=1)
        quantiles = self._vector(
            arguments.get("quantiles", [0.25, 0.5, 0.75]),
            "quantiles",
            minimum=0,
            maximum=101,
        )
        if any(not 0 <= value <= 1 for value in quantiles):
            raise NumericMathInputError("quantiles must be between 0 and 1")
        array = np.asarray(values, dtype=float)
        details = {
            "count": len(values),
            "minimum": float(np.min(array)),
            "maximum": float(np.max(array)),
            "mean": float(np.mean(array)),
            "median": float(np.median(array)),
            "population_variance": float(np.var(array)),
            "population_std": float(np.std(array)),
            "sample_variance": float(np.var(array, ddof=1)) if len(values) > 1 else None,
            "sample_std": float(np.std(array, ddof=1)) if len(values) > 1 else None,
            "quantile_probabilities": quantiles,
            "quantiles": [float(item) for item in np.quantile(array, quantiles)],
        }
        return self._result("statistics", "numpy", details=details)

    def _linear_solve(self, arguments: dict[str, Any], _: float) -> dict[str, Any]:
        matrix = self._matrix(arguments.get("matrix"), square=True)
        vector = np.asarray(
            self._vector(arguments.get("vector"), "vector", minimum=1),
            dtype=float,
        )
        if matrix.shape[0] != vector.size:
            raise NumericMathInputError("vector length must match the matrix dimension")
        condition = float(np.linalg.cond(matrix))
        if not math.isfinite(condition) or condition > 1e14:
            raise NumericMathInputError("matrix is singular or numerically ill-conditioned")
        try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError as exc:
            raise NumericMathInputError(f"linear system cannot be solved: {exc}") from exc
        residual = float(np.linalg.norm(matrix @ solution - vector))
        return self._result(
            "linear_solve",
            "numpy.linalg.solve",
            values=[float(item) for item in solution],
            details={"condition_number": condition, "residual_norm": residual},
        )

    def _eigenvalues(self, arguments: dict[str, Any], tolerance: float) -> dict[str, Any]:
        matrix = self._matrix(arguments.get("matrix"), square=True)
        try:
            raw = np.linalg.eigvals(matrix)
        except np.linalg.LinAlgError as exc:
            raise NumericMathInputError(f"eigenvalue computation failed: {exc}") from exc
        values = []
        for item in sorted(raw, key=lambda value: (float(value.real), float(value.imag))):
            real = 0.0 if abs(float(item.real)) <= tolerance else float(item.real)
            imag = 0.0 if abs(float(item.imag)) <= tolerance else float(item.imag)
            values.append({"real": real, "imag": imag})
        return self._result(
            "eigenvalues",
            "numpy.linalg.eigvals",
            values=values,
            details={"matrix_dimension": int(matrix.shape[0])},
        )

    def _quadrature(self, arguments: dict[str, Any], tolerance: float) -> dict[str, Any]:
        variable = self._single_variable(arguments)
        function = self._safe_callable(arguments.get("expression"), [variable])
        lower, upper = self._interval(arguments.get("interval"))
        try:
            value, error = integrate.quad(
                lambda item: self._scalar(function(item)),
                lower,
                upper,
                epsabs=tolerance,
                epsrel=tolerance,
                limit=200,
            )
        except Exception as exc:
            raise NumericMathInputError(f"quadrature failed: {exc}") from exc
        if not math.isfinite(value) or not math.isfinite(error):
            raise NumericMathInputError("quadrature produced a non-finite result")
        return self._result(
            "quadrature",
            "scipy.integrate.quad",
            scalar=float(value),
            details={"estimated_absolute_error": float(error), "interval": [lower, upper]},
        )

    def _root(self, arguments: dict[str, Any], tolerance: float) -> dict[str, Any]:
        variable = self._single_variable(arguments)
        function = self._safe_callable(arguments.get("expression"), [variable])
        bracket = self._numeric_pair(arguments.get("bracket"), "bracket")
        try:
            solved = optimize.root_scalar(
                lambda item: self._scalar(function(item)),
                bracket=bracket,
                method="brentq",
                xtol=tolerance,
                rtol=max(tolerance, 4 * np.finfo(float).eps),
            )
        except Exception as exc:
            raise NumericMathInputError(f"root finding failed: {exc}") from exc
        if not solved.converged:
            raise NumericMathInputError("root finding did not converge")
        return self._result(
            "root",
            "scipy.optimize.brentq",
            scalar=float(solved.root),
            details={"iterations": int(solved.iterations), "function_calls": int(solved.function_calls)},
        )

    def _minimize_scalar(
        self, arguments: dict[str, Any], tolerance: float
    ) -> dict[str, Any]:
        variable = self._single_variable(arguments)
        function = self._safe_callable(arguments.get("expression"), [variable])
        bounds = self._numeric_pair(arguments.get("bounds"), "bounds")
        if bounds[0] >= bounds[1]:
            raise NumericMathInputError("bounds must be strictly increasing")
        solved = optimize.minimize_scalar(
            lambda item: self._scalar(function(item)),
            bounds=bounds,
            method="bounded",
            options={"xatol": tolerance, "maxiter": 1000},
        )
        if not solved.success or not math.isfinite(float(solved.fun)):
            raise NumericMathInputError(f"scalar minimization failed: {solved.message}")
        return self._result(
            "minimize_scalar",
            "scipy.optimize.bounded",
            scalar=float(solved.x),
            details={"function_value": float(solved.fun), "iterations": int(solved.nit)},
        )

    def _interpolate(self, arguments: dict[str, Any], _: float) -> dict[str, Any]:
        x = self._vector(arguments.get("x"), "x", minimum=2)
        y = self._vector(arguments.get("y"), "y", minimum=2)
        query = self._vector(arguments.get("query_points"), "query_points", minimum=1)
        if len(x) != len(y):
            raise NumericMathInputError("x and y must have equal lengths")
        if any(right <= left for left, right in zip(x, x[1:])):
            raise NumericMathInputError("x must be strictly increasing")
        method = str(arguments.get("method", "linear"))
        if method not in {"linear", "nearest", "quadratic", "cubic"}:
            raise NumericMathInputError("unsupported interpolation method")
        if method in {"quadratic", "cubic"} and len(x) < (3 if method == "quadratic" else 4):
            raise NumericMathInputError(f"{method} interpolation needs more source points")
        if min(query) < x[0] or max(query) > x[-1]:
            raise NumericMathInputError("query points must stay inside the source x range")
        function = interpolate.interp1d(x, y, kind=method, assume_sorted=True)
        values = [float(item) for item in function(query)]
        return self._result(
            "interpolate",
            f"scipy.interpolate.{method}",
            values=values,
            details={"query_points": query, "source_count": len(x)},
        )

    def _ode(self, arguments: dict[str, Any], tolerance: float) -> dict[str, Any]:
        variables = arguments.get("variables")
        initial_values = self._vector(
            arguments.get("initial_values"), "initial_values", minimum=1, maximum=64
        )
        if not isinstance(variables, list) or len(variables) != len(initial_values) + 1:
            raise NumericMathInputError(
                "variables must contain time followed by one name per initial value"
            )
        expressions = arguments.get("expressions")
        if expressions is None:
            expressions = [arguments.get("expression")]
        if not isinstance(expressions, list) or len(expressions) != len(initial_values):
            raise NumericMathInputError("one ODE expression is required per initial value")
        functions = [self._safe_callable(item, variables) for item in expressions]
        lower, upper = self._interval(arguments.get("interval"))
        if not lower < upper:
            raise NumericMathInputError("ODE interval must be strictly increasing")
        sample_count = arguments.get("sample_count", 101)
        if isinstance(sample_count, bool) or not isinstance(sample_count, int) or not 2 <= sample_count <= 5000:
            raise NumericMathInputError("sample_count must be an integer from 2 to 5000")
        sample_times = np.linspace(lower, upper, sample_count)

        def derivative(time_value: float, state: np.ndarray) -> list[float]:
            inputs = [time_value, *state]
            return [self._scalar(function(*inputs)) for function in functions]

        solved = integrate.solve_ivp(
            derivative,
            (lower, upper),
            initial_values,
            t_eval=sample_times,
            rtol=tolerance,
            atol=tolerance,
        )
        if not solved.success:
            raise NumericMathInputError(f"ODE integration failed: {solved.message}")
        values = [
            [float(solved.t[index]), *[float(row[index]) for row in solved.y]]
            for index in range(solved.t.size)
        ]
        return self._result(
            "ode",
            "scipy.integrate.solve_ivp",
            values=values,
            details={"variables": variables, "function_evaluations": int(solved.nfev)},
        )

    def _fft(self, arguments: dict[str, Any], _: float) -> dict[str, Any]:
        values = self._vector(arguments.get("values"), "values", minimum=2)
        spacing = self._positive(arguments.get("sample_spacing", 1.0), "sample_spacing")
        spectrum = np.fft.rfft(values)
        frequencies = np.fft.rfftfreq(len(values), spacing)
        output = [
            {
                "frequency": float(frequency),
                "real": float(value.real),
                "imag": float(value.imag),
                "magnitude": float(abs(value) / len(values)),
            }
            for frequency, value in zip(frequencies, spectrum)
        ]
        return self._result(
            "fft",
            "numpy.fft.rfft",
            values=output,
            details={"sample_count": len(values), "sample_spacing": spacing},
        )

    def _distribution(self, arguments: dict[str, Any], _: float) -> dict[str, Any]:
        name = str(arguments.get("distribution", ""))
        operation = str(arguments.get("distribution_operation", ""))
        points = self._vector(arguments.get("points"), "points", minimum=1)
        parameters = arguments.get("parameters", {})
        if not isinstance(parameters, dict):
            raise NumericMathInputError("parameters must be an object")
        if name == "normal":
            allowed = {"loc", "scale"}
            unknown = set(parameters) - allowed
            if unknown:
                raise NumericMathInputError(f"unsupported normal parameters: {sorted(unknown)}")
            scale = self._positive(parameters.get("scale", 1), "scale")
            distribution: Any = stats.norm(loc=self._finite(parameters.get("loc", 0), "loc"), scale=scale)
            supported = {"pdf", "cdf", "ppf"}
        elif name == "binomial":
            allowed = {"n", "p"}
            unknown = set(parameters) - allowed
            if unknown:
                raise NumericMathInputError(f"unsupported binomial parameters: {sorted(unknown)}")
            n = parameters.get("n")
            p = self._finite(parameters.get("p"), "p")
            if isinstance(n, bool) or not isinstance(n, int) or n < 0 or not 0 <= p <= 1:
                raise NumericMathInputError("binomial requires integer n >= 0 and 0 <= p <= 1")
            distribution = stats.binom(n=n, p=p)
            supported = {"pmf", "cdf", "ppf"}
        elif name == "poisson":
            unknown = set(parameters) - {"mu"}
            if unknown:
                raise NumericMathInputError(f"unsupported Poisson parameters: {sorted(unknown)}")
            mu = self._positive(parameters.get("mu"), "mu")
            distribution = stats.poisson(mu=mu)
            supported = {"pmf", "cdf", "ppf"}
        else:
            raise NumericMathInputError("distribution must be normal, binomial, or poisson")
        if operation not in supported:
            raise NumericMathInputError(f"{operation!r} is not supported for {name}")
        raw = getattr(distribution, operation)(points)
        values = [float(item) for item in np.atleast_1d(raw)]
        return self._result(
            "distribution",
            f"scipy.stats.{name}.{operation}",
            values=values,
            details={"distribution": name, "distribution_operation": operation, "points": points},
        )

    @staticmethod
    def _result(
        operation: str,
        method: str,
        *,
        scalar: float | None = None,
        values: list[Any] | None = None,
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "operation": operation,
            "method": method,
            "success": True,
            "scalar": scalar,
            "values": values or [],
            "details": details or {},
        }

    def _safe_callable(self, expression: Any, variables: list[str]) -> Callable[..., Any]:
        if not isinstance(expression, str) or not expression.strip():
            raise NumericMathInputError("expression is required")
        if len(set(variables)) != len(variables) or not variables:
            raise NumericMathInputError("variables must be unique and non-empty")
        parser = SymbolicMathAdapter()
        try:
            symbols, _ = parser._symbols({name: {"real": True} for name in variables})
            parsed = parser._parse_required_expression(expression, symbols)
            parser._check_complexity(parsed)
        except SymbolicMathInputError as exc:
            raise NumericMathInputError(str(exc)) from exc
        ordered = [symbols[name] for name in variables]
        return sp.lambdify(ordered, parsed, modules=["numpy"])

    def _single_variable(self, arguments: dict[str, Any]) -> str:
        variable = arguments.get("variable")
        if not isinstance(variable, str) or not variable:
            raise NumericMathInputError("variable is required")
        return variable

    def _interval(self, raw: Any) -> tuple[float, float]:
        if not isinstance(raw, list) or len(raw) != 2:
            raise NumericMathInputError("interval must contain lower and upper")
        return self._bound(raw[0]), self._bound(raw[1])

    def _bound(self, raw: Any) -> float:
        if isinstance(raw, (int, float)) and not isinstance(raw, bool):
            return self._finite(raw, "interval bound")
        if not isinstance(raw, str):
            raise NumericMathInputError("interval bounds must be numbers or constants")
        parser = SymbolicMathAdapter()
        try:
            value = parser._parse(raw, {})
        except SymbolicMathInputError as exc:
            raise NumericMathInputError(str(exc)) from exc
        if value.free_symbols:
            raise NumericMathInputError("interval bounds cannot contain variables")
        return self._finite(float(value.evalf()), "interval bound")

    def _matrix(self, raw: Any, *, square: bool) -> np.ndarray:
        if not isinstance(raw, list) or not raw or len(raw) > MAX_MATRIX_DIMENSION:
            raise NumericMathInputError("matrix must be a non-empty bounded array")
        if not all(isinstance(row, list) and row for row in raw):
            raise NumericMathInputError("matrix rows must be non-empty arrays")
        width = len(raw[0])
        if width > MAX_MATRIX_DIMENSION or any(len(row) != width for row in raw):
            raise NumericMathInputError("matrix must be rectangular and bounded")
        if square and len(raw) != width:
            raise NumericMathInputError("operation requires a square matrix")
        values = [[self._finite(item, "matrix value") for item in row] for row in raw]
        return np.asarray(values, dtype=float)

    def _vector(
        self,
        raw: Any,
        name: str,
        *,
        minimum: int,
        maximum: int = MAX_VALUES,
    ) -> list[float]:
        if not isinstance(raw, list) or not minimum <= len(raw) <= maximum:
            raise NumericMathInputError(
                f"{name} must contain {minimum} to {maximum} finite values"
            )
        return [self._finite(item, name) for item in raw]

    def _numeric_pair(self, raw: Any, name: str) -> tuple[float, float]:
        values = self._vector(raw, name, minimum=2, maximum=2)
        return values[0], values[1]

    @staticmethod
    def _finite(raw: Any, name: str) -> float:
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise NumericMathInputError(f"{name} must contain only numbers")
        value = float(raw)
        if not math.isfinite(value):
            raise NumericMathInputError(f"{name} must contain only finite numbers")
        return value

    def _positive(self, raw: Any, name: str) -> float:
        value = self._finite(raw, name)
        if value <= 0:
            raise NumericMathInputError(f"{name} must be positive")
        return value

    def _tolerance(self, raw: Any) -> float:
        value = self._positive(raw, "tolerance")
        if value < 1e-15 or value > 0.1:
            raise NumericMathInputError("tolerance must be between 1e-15 and 0.1")
        return value

    def _scalar(self, raw: Any) -> float:
        array = np.asarray(raw)
        if array.size != 1:
            raise NumericMathInputError("expression must return one numeric value")
        return self._finite(float(array.reshape(-1)[0]), "expression output")

    def _require_json_finite(self, value: Any) -> None:
        try:
            json.dumps(value, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise NumericMathInputError(f"numeric result is not finite JSON: {exc}") from exc

    @staticmethod
    def _write_artifacts(
        work_dir: Path, result: dict[str, Any]
    ) -> list[ToolProducedArtifact]:
        work_dir.mkdir(parents=True, exist_ok=True)
        json_path = work_dir / "numeric-result.json"
        csv_path = work_dir / "numeric-table.csv"
        json_path.write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n",
            encoding="utf-8",
        )
        with csv_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(["index", "value"])
            for index, value in enumerate(result["values"]):
                writer.writerow([index, json.dumps(value, ensure_ascii=False, sort_keys=True)])
            if not result["values"] and result["scalar"] is not None:
                writer.writerow([0, result["scalar"]])
        return [
            ToolProducedArtifact(
                name="numeric-result.json",
                media_type="application/json",
                source_path=json_path.name,
            ),
            ToolProducedArtifact(
                name="numeric-table.csv",
                media_type="text/csv",
                source_path=csv_path.name,
            ),
        ]
