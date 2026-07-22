from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Callable

import numpy as np
from scipy import optimize

from app.tools.adapters.numeric_math import NumericMathAdapter, NumericMathInputError
from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolProducedArtifact,
    ToolQualityTier,
    ToolScope,
)


OPERATIONS = ("continuous", "linear_program", "least_squares")
RELATIONS = ("<=", "==", ">=")
MAX_VARIABLES = 64
MAX_CONSTRAINTS = 256
MAX_RESIDUALS = 512
ROOT_FIELDS = {
    "operation",
    "variables",
    "goal",
    "objective_expression",
    "objective_coefficients",
    "residual_expressions",
    "initial_point",
    "bounds",
    "constraints",
    "linear_constraints",
    "tolerance",
    "max_iterations",
}


class OptimizeMathInputError(ValueError):
    pass


class OptimizeMathAdapter:
    definition = ToolDefinition(
        tool_id="math.optimize",
        version="1.0.0",
        title="Verified bounded mathematical optimization",
        description=(
            "Solve structured continuous nonlinear programs, linear programs, and "
            "bounded nonlinear least-squares problems with SciPy. Inputs declare "
            "variables, bounds, objectives, residuals, and constraints explicitly; "
            "Python, callbacks, solver code, files, URLs, and shell commands are never accepted."
        ),
        category="mathematics",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.COMPUTE,
        execution_mode=ToolExecutionMode.ASYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=30,
        max_artifacts=4,
        max_artifact_bytes=16 * 1024 * 1024,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["operation", "variables"],
            "properties": {
                "operation": {"type": "string", "enum": list(OPERATIONS)},
                "variables": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": MAX_VARIABLES,
                    "items": {"type": "string", "maxLength": 64},
                },
                "goal": {"type": "string", "enum": ["minimize", "maximize"]},
                "objective_expression": {"type": "string", "maxLength": 20_000},
                "objective_coefficients": {
                    "type": "array",
                    "maxItems": MAX_VARIABLES,
                    "items": {"type": "number"},
                },
                "residual_expressions": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": MAX_RESIDUALS,
                    "items": {"type": "string", "maxLength": 20_000},
                },
                "initial_point": {
                    "type": "array",
                    "maxItems": MAX_VARIABLES,
                    "items": {"type": "number"},
                },
                "bounds": {
                    "type": "array",
                    "maxItems": MAX_VARIABLES,
                    "items": {
                        "type": "array",
                        "prefixItems": [
                            {"type": ["number", "null"]},
                            {"type": ["number", "null"]},
                        ],
                        "minItems": 2,
                        "maxItems": 2,
                    },
                },
                "constraints": {
                    "type": "array",
                    "maxItems": MAX_CONSTRAINTS,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["expression", "relation", "rhs"],
                        "properties": {
                            "expression": {"type": "string", "maxLength": 20_000},
                            "relation": {"type": "string", "enum": list(RELATIONS)},
                            "rhs": {"type": "number"},
                        },
                    },
                },
                "linear_constraints": {
                    "type": "array",
                    "maxItems": MAX_CONSTRAINTS,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["coefficients", "relation", "rhs"],
                        "properties": {
                            "coefficients": {
                                "type": "array",
                                "maxItems": MAX_VARIABLES,
                                "items": {"type": "number"},
                            },
                            "relation": {"type": "string", "enum": list(RELATIONS)},
                            "rhs": {"type": "number"},
                        },
                    },
                },
                "tolerance": {
                    "type": "number",
                    "minimum": 1e-15,
                    "maximum": 0.1,
                },
                "max_iterations": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10_000,
                },
            },
        },
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": [
                "operation",
                "solver",
                "success",
                "status",
                "goal",
                "variables",
                "solution",
                "objective_value",
                "constraint_violation",
                "optimality",
                "iterations",
                "evaluations",
                "details",
            ],
            "properties": {
                "operation": {"type": "string"},
                "solver": {"type": "string"},
                "success": {"type": "boolean"},
                "status": {"type": "string"},
                "goal": {"type": "string"},
                "variables": {"type": "array", "items": {"type": "string"}},
                "solution": {"type": "object", "additionalProperties": {"type": "number"}},
                "objective_value": {"type": "number"},
                "constraint_violation": {"type": "number", "minimum": 0},
                "optimality": {"type": ["number", "null"]},
                "iterations": {"type": "integer", "minimum": 0},
                "evaluations": {"type": "integer", "minimum": 0},
                "details": {"type": "object"},
            },
        },
        output_media_types=["application/json", "text/csv"],
        quality_gates=[
            "arbitrary_code_rejected",
            "bounded_variables_and_constraints",
            "finite_solution_and_objective",
            "solver_success_required",
            "postsolve_feasibility_check",
            "local_vs_global_optimum_disclosed",
            "deterministic_reference_cases",
        ],
        upstream_project="SciPy 1.17.1",
        license="BSD-3-Clause",
    )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        if not isinstance(arguments, dict):
            raise OptimizeMathInputError("optimization arguments must be an object")
        unknown = set(arguments) - ROOT_FIELDS
        if unknown:
            raise OptimizeMathInputError(f"unsupported optimization fields: {sorted(unknown)}")
        operation = arguments.get("operation")
        if operation not in OPERATIONS:
            raise OptimizeMathInputError(f"unsupported operation: {operation!r}")
        variables = self._variables(arguments.get("variables"))
        tolerance = self._tolerance(arguments.get("tolerance", 1e-9))
        max_iterations = self._max_iterations(arguments.get("max_iterations", 1000))
        handlers = {
            "continuous": self._continuous,
            "linear_program": self._linear_program,
            "least_squares": self._least_squares,
        }
        result = handlers[operation](
            arguments, variables, tolerance, max_iterations
        )
        self._finite_json(result)
        if not result["success"]:
            raise OptimizeMathInputError(f"optimization did not succeed: {result['status']}")
        if result["constraint_violation"] > max(tolerance * 10, 1e-8):
            raise OptimizeMathInputError(
                "optimization result failed the postsolve feasibility check"
            )
        artifacts = self._write_artifacts(context.work_dir, result)
        return ToolExecutionResult(
            result=result,
            artifacts=artifacts,
            metrics={
                "variable_count": len(variables),
                "iterations": result["iterations"],
                "evaluations": result["evaluations"],
                "constraint_violation": result["constraint_violation"],
            },
        )

    def _continuous(
        self,
        arguments: dict[str, Any],
        variables: list[str],
        tolerance: float,
        max_iterations: int,
    ) -> dict[str, Any]:
        goal = self._goal(arguments.get("goal", "minimize"))
        objective = self._callable(arguments.get("objective_expression"), variables)
        bounds = self._bounds(arguments.get("bounds"), len(variables))
        initial = self._initial(arguments.get("initial_point"), bounds)
        constraints = self._nonlinear_constraints(
            arguments.get("constraints", []), variables
        )
        trace: list[dict[str, Any]] = []

        def actual_objective(point: np.ndarray) -> float:
            return self._scalar(objective(*point))

        direction = 1.0 if goal == "minimize" else -1.0

        def callback(point: np.ndarray) -> None:
            if len(trace) < max_iterations:
                trace.append(
                    {
                        "iteration": len(trace) + 1,
                        "point": [float(value) for value in point],
                        "objective": actual_objective(point),
                    }
                )

        scipy_constraints = []
        for item in constraints:
            function = item["function"]
            rhs = item["rhs"]
            relation = item["relation"]
            if relation == "==":
                scipy_constraints.append(
                    {"type": "eq", "fun": lambda point, f=function, r=rhs: self._scalar(f(*point)) - r}
                )
            elif relation == ">=":
                scipy_constraints.append(
                    {"type": "ineq", "fun": lambda point, f=function, r=rhs: self._scalar(f(*point)) - r}
                )
            else:
                scipy_constraints.append(
                    {"type": "ineq", "fun": lambda point, f=function, r=rhs: r - self._scalar(f(*point))}
                )
        solved = optimize.minimize(
            lambda point: direction * actual_objective(point),
            np.asarray(initial, dtype=float),
            method="SLSQP",
            bounds=bounds,
            constraints=scipy_constraints,
            callback=callback,
            options={
                "ftol": tolerance,
                "maxiter": max_iterations,
                "disp": False,
            },
        )
        point = np.asarray(solved.x, dtype=float)
        objective_value = actual_objective(point)
        violation, evidence = self._nonlinear_violation(point, constraints, bounds)
        jacobian = np.asarray(getattr(solved, "jac", []), dtype=float)
        optimality = (
            float(np.linalg.norm(jacobian, ord=np.inf))
            if jacobian.size and np.all(np.isfinite(jacobian))
            else None
        )
        return self._result(
            operation="continuous",
            solver="scipy.optimize.minimize.SLSQP",
            solved=solved,
            goal=goal,
            variables=variables,
            point=point,
            objective_value=objective_value,
            violation=violation,
            optimality=optimality,
            iterations=int(getattr(solved, "nit", 0)),
            evaluations=int(getattr(solved, "nfev", 0)),
            details={
                "global_optimum": False,
                "optimum_scope": "local",
                "constraint_evidence": evidence,
                "trace": trace,
            },
        )

    def _linear_program(
        self,
        arguments: dict[str, Any],
        variables: list[str],
        tolerance: float,
        _: int,
    ) -> dict[str, Any]:
        goal = self._goal(arguments.get("goal", "minimize"))
        coefficients = self._vector(
            arguments.get("objective_coefficients"),
            "objective_coefficients",
            len(variables),
        )
        bounds = self._bounds(arguments.get("bounds"), len(variables))
        constraints = self._linear_constraints(
            arguments.get("linear_constraints", []), len(variables)
        )
        ub_rows: list[list[float]] = []
        ub_rhs: list[float] = []
        eq_rows: list[list[float]] = []
        eq_rhs: list[float] = []
        for item in constraints:
            row = item["coefficients"]
            rhs = item["rhs"]
            if item["relation"] == "==":
                eq_rows.append(row)
                eq_rhs.append(rhs)
            elif item["relation"] == "<=":
                ub_rows.append(row)
                ub_rhs.append(rhs)
            else:
                ub_rows.append([-value for value in row])
                ub_rhs.append(-rhs)
        direction = 1.0 if goal == "minimize" else -1.0
        solved = optimize.linprog(
            c=direction * np.asarray(coefficients, dtype=float),
            A_ub=np.asarray(ub_rows, dtype=float) if ub_rows else None,
            b_ub=np.asarray(ub_rhs, dtype=float) if ub_rhs else None,
            A_eq=np.asarray(eq_rows, dtype=float) if eq_rows else None,
            b_eq=np.asarray(eq_rhs, dtype=float) if eq_rhs else None,
            bounds=bounds,
            method="highs",
            options={"primal_feasibility_tolerance": max(tolerance, 1e-10)},
        )
        point = np.asarray(solved.x if solved.x is not None else [], dtype=float)
        if point.size != len(variables):
            raise OptimizeMathInputError(f"linear program failed: {solved.message}")
        objective_value = float(np.dot(coefficients, point))
        violation, evidence = self._linear_violation(point, constraints, bounds)
        return self._result(
            operation="linear_program",
            solver="scipy.optimize.linprog.highs",
            solved=solved,
            goal=goal,
            variables=variables,
            point=point,
            objective_value=objective_value,
            violation=violation,
            optimality=None,
            iterations=int(getattr(solved, "nit", 0)),
            evaluations=0,
            details={
                "global_optimum": True,
                "optimum_scope": "global_for_declared_linear_program",
                "constraint_evidence": evidence,
                "crossover_iterations": int(
                    getattr(solved, "crossover_nit", 0) or 0
                ),
            },
        )

    def _least_squares(
        self,
        arguments: dict[str, Any],
        variables: list[str],
        tolerance: float,
        max_iterations: int,
    ) -> dict[str, Any]:
        if arguments.get("goal", "minimize") != "minimize":
            raise OptimizeMathInputError("least_squares supports only goal=minimize")
        raw_residuals = arguments.get("residual_expressions")
        if not isinstance(raw_residuals, list) or not 1 <= len(raw_residuals) <= MAX_RESIDUALS:
            raise OptimizeMathInputError(
                f"residual_expressions must contain 1 to {MAX_RESIDUALS} expressions"
            )
        residuals = [self._callable(item, variables) for item in raw_residuals]
        bounds = self._bounds(arguments.get("bounds"), len(variables))
        initial = self._initial(arguments.get("initial_point"), bounds)
        lower = np.asarray([-np.inf if item[0] is None else item[0] for item in bounds])
        upper = np.asarray([np.inf if item[1] is None else item[1] for item in bounds])

        def residual_vector(point: np.ndarray) -> np.ndarray:
            values = [self._scalar(function(*point)) for function in residuals]
            return np.asarray(values, dtype=float)

        solved = optimize.least_squares(
            residual_vector,
            np.asarray(initial, dtype=float),
            bounds=(lower, upper),
            method="trf",
            ftol=tolerance,
            xtol=tolerance,
            gtol=tolerance,
            max_nfev=max_iterations,
        )
        point = np.asarray(solved.x, dtype=float)
        final_residuals = residual_vector(point)
        violation = self._bounds_violation(point, bounds)
        return self._result(
            operation="least_squares",
            solver="scipy.optimize.least_squares.trf",
            solved=solved,
            goal="minimize",
            variables=variables,
            point=point,
            objective_value=float(0.5 * np.dot(final_residuals, final_residuals)),
            violation=violation,
            optimality=float(solved.optimality),
            iterations=0,
            evaluations=int(solved.nfev),
            details={
                "global_optimum": False,
                "optimum_scope": "local_least_squares",
                "residuals": [float(value) for value in final_residuals],
                "residual_norm": float(np.linalg.norm(final_residuals)),
                "active_mask": [int(value) for value in solved.active_mask],
            },
        )

    @staticmethod
    def _result(
        *,
        operation: str,
        solver: str,
        solved: Any,
        goal: str,
        variables: list[str],
        point: np.ndarray,
        objective_value: float,
        violation: float,
        optimality: float | None,
        iterations: int,
        evaluations: int,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "operation": operation,
            "solver": solver,
            "success": bool(solved.success),
            "status": str(solved.message),
            "goal": goal,
            "variables": variables,
            "solution": {
                name: float(point[index]) for index, name in enumerate(variables)
            },
            "objective_value": float(objective_value),
            "constraint_violation": float(violation),
            "optimality": None if optimality is None else float(optimality),
            "iterations": max(0, int(iterations)),
            "evaluations": max(0, int(evaluations)),
            "details": details,
        }

    def _variables(self, raw: Any) -> list[str]:
        if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_VARIABLES:
            raise OptimizeMathInputError(f"variables must contain 1 to {MAX_VARIABLES} names")
        if any(not isinstance(name, str) or not name for name in raw):
            raise OptimizeMathInputError("variable names must be non-empty strings")
        if len(set(raw)) != len(raw):
            raise OptimizeMathInputError("variable names must be unique")
        try:
            NumericMathAdapter()._safe_callable(" + ".join(raw), raw)
        except NumericMathInputError as exc:
            raise OptimizeMathInputError(str(exc)) from exc
        return list(raw)

    def _callable(self, raw: Any, variables: list[str]) -> Callable[..., Any]:
        try:
            return NumericMathAdapter()._safe_callable(raw, variables)
        except NumericMathInputError as exc:
            raise OptimizeMathInputError(str(exc)) from exc

    def _bounds(
        self, raw: Any, dimension: int
    ) -> list[tuple[float | None, float | None]]:
        if raw is None:
            return [(None, None) for _ in range(dimension)]
        if not isinstance(raw, list) or len(raw) != dimension:
            raise OptimizeMathInputError("bounds must contain one pair per variable")
        output = []
        for index, item in enumerate(raw):
            if not isinstance(item, list) or len(item) != 2:
                raise OptimizeMathInputError(f"bound {index} must contain lower and upper")
            lower = None if item[0] is None else self._finite(item[0], f"bound {index} lower")
            upper = None if item[1] is None else self._finite(item[1], f"bound {index} upper")
            if lower is not None and upper is not None and lower > upper:
                raise OptimizeMathInputError(f"bound {index} lower cannot exceed upper")
            output.append((lower, upper))
        return output

    def _initial(
        self,
        raw: Any,
        bounds: list[tuple[float | None, float | None]],
    ) -> list[float]:
        if raw is None:
            values = []
            for lower, upper in bounds:
                if lower is not None and upper is not None:
                    values.append((lower + upper) / 2)
                elif lower is not None:
                    values.append(max(lower, 0.0))
                elif upper is not None:
                    values.append(min(upper, 0.0))
                else:
                    values.append(0.0)
        else:
            values = self._vector(raw, "initial_point", len(bounds))
        if self._bounds_violation(np.asarray(values), bounds) > 0:
            raise OptimizeMathInputError("initial_point must satisfy every variable bound")
        return values

    def _nonlinear_constraints(
        self, raw: Any, variables: list[str]
    ) -> list[dict[str, Any]]:
        if not isinstance(raw, list) or len(raw) > MAX_CONSTRAINTS:
            raise OptimizeMathInputError(f"constraints must contain at most {MAX_CONSTRAINTS} items")
        output = []
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) != {"expression", "relation", "rhs"}:
                raise OptimizeMathInputError(f"constraint {index} fields are invalid")
            relation = item["relation"]
            if relation not in RELATIONS:
                raise OptimizeMathInputError(f"constraint {index} relation is invalid")
            output.append(
                {
                    "expression": item["expression"],
                    "function": self._callable(item["expression"], variables),
                    "relation": relation,
                    "rhs": self._finite(item["rhs"], f"constraint {index} rhs"),
                }
            )
        return output

    def _linear_constraints(self, raw: Any, dimension: int) -> list[dict[str, Any]]:
        if not isinstance(raw, list) or len(raw) > MAX_CONSTRAINTS:
            raise OptimizeMathInputError(
                f"linear_constraints must contain at most {MAX_CONSTRAINTS} items"
            )
        output = []
        for index, item in enumerate(raw):
            if not isinstance(item, dict) or set(item) != {"coefficients", "relation", "rhs"}:
                raise OptimizeMathInputError(f"linear constraint {index} fields are invalid")
            relation = item["relation"]
            if relation not in RELATIONS:
                raise OptimizeMathInputError(f"linear constraint {index} relation is invalid")
            output.append(
                {
                    "coefficients": self._vector(
                        item["coefficients"], f"linear constraint {index} coefficients", dimension
                    ),
                    "relation": relation,
                    "rhs": self._finite(item["rhs"], f"linear constraint {index} rhs"),
                }
            )
        return output

    def _nonlinear_violation(
        self,
        point: np.ndarray,
        constraints: list[dict[str, Any]],
        bounds: list[tuple[float | None, float | None]],
    ) -> tuple[float, list[dict[str, Any]]]:
        maximum = self._bounds_violation(point, bounds)
        evidence = []
        for item in constraints:
            value = self._scalar(item["function"](*point))
            violation = self._relation_violation(value, item["relation"], item["rhs"])
            maximum = max(maximum, violation)
            evidence.append(
                {
                    "expression": item["expression"],
                    "relation": item["relation"],
                    "rhs": item["rhs"],
                    "value": value,
                    "violation": violation,
                }
            )
        return maximum, evidence

    def _linear_violation(
        self,
        point: np.ndarray,
        constraints: list[dict[str, Any]],
        bounds: list[tuple[float | None, float | None]],
    ) -> tuple[float, list[dict[str, Any]]]:
        maximum = self._bounds_violation(point, bounds)
        evidence = []
        for item in constraints:
            value = float(np.dot(item["coefficients"], point))
            violation = self._relation_violation(value, item["relation"], item["rhs"])
            maximum = max(maximum, violation)
            evidence.append(
                {
                    "coefficients": item["coefficients"],
                    "relation": item["relation"],
                    "rhs": item["rhs"],
                    "value": value,
                    "violation": violation,
                }
            )
        return maximum, evidence

    @staticmethod
    def _relation_violation(value: float, relation: str, rhs: float) -> float:
        if relation == "<=":
            return max(0.0, value - rhs)
        if relation == ">=":
            return max(0.0, rhs - value)
        return abs(value - rhs)

    @staticmethod
    def _bounds_violation(
        point: np.ndarray,
        bounds: list[tuple[float | None, float | None]],
    ) -> float:
        maximum = 0.0
        for value, (lower, upper) in zip(point, bounds):
            if lower is not None:
                maximum = max(maximum, lower - float(value))
            if upper is not None:
                maximum = max(maximum, float(value) - upper)
        return max(0.0, maximum)

    @staticmethod
    def _goal(raw: Any) -> str:
        if raw not in {"minimize", "maximize"}:
            raise OptimizeMathInputError("goal must be minimize or maximize")
        return str(raw)

    def _vector(self, raw: Any, name: str, dimension: int) -> list[float]:
        if not isinstance(raw, list) or len(raw) != dimension:
            raise OptimizeMathInputError(f"{name} must contain one value per variable")
        return [self._finite(value, name) for value in raw]

    @staticmethod
    def _finite(raw: Any, name: str) -> float:
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise OptimizeMathInputError(f"{name} must be numeric")
        value = float(raw)
        if not math.isfinite(value):
            raise OptimizeMathInputError(f"{name} must be finite")
        return value

    def _scalar(self, raw: Any) -> float:
        array = np.asarray(raw)
        if array.size != 1:
            raise OptimizeMathInputError("expression must return one numeric value")
        return self._finite(float(array.reshape(-1)[0]), "expression output")

    def _tolerance(self, raw: Any) -> float:
        value = self._finite(raw, "tolerance")
        if not 1e-15 <= value <= 0.1:
            raise OptimizeMathInputError("tolerance must be between 1e-15 and 0.1")
        return value

    @staticmethod
    def _max_iterations(raw: Any) -> int:
        if isinstance(raw, bool) or not isinstance(raw, int) or not 1 <= raw <= 10_000:
            raise OptimizeMathInputError("max_iterations must be an integer from 1 to 10000")
        return raw

    @staticmethod
    def _finite_json(value: Any) -> None:
        try:
            json.dumps(value, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise OptimizeMathInputError(f"optimization result is not finite JSON: {exc}") from exc

    @staticmethod
    def _write_artifacts(
        work_dir: Path, result: dict[str, Any]
    ) -> list[ToolProducedArtifact]:
        work_dir.mkdir(parents=True, exist_ok=True)
        json_path = work_dir / "optimization-result.json"
        csv_path = work_dir / "optimization-solution.csv"
        json_path.write_text(
            json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
            + "\n",
            encoding="utf-8",
        )
        with csv_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(["variable", "value"])
            for name in result["variables"]:
                writer.writerow([name, result["solution"][name]])
            writer.writerow(["objective_value", result["objective_value"]])
            writer.writerow(["constraint_violation", result["constraint_violation"]])
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
