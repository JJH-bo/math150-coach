from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import sympy as sp
from sympy.parsing.sympy_parser import (
    auto_symbol,
    convert_xor,
    parse_expr,
    standard_transformations,
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
    "simplify",
    "factor",
    "expand",
    "solve",
    "differentiate",
    "integrate",
    "limit",
    "series",
    "matrix",
    "equivalent",
)
MATRIX_OPERATIONS = ("determinant", "inverse", "rank", "eigenvalues")
ASSUMPTIONS = {
    "real",
    "positive",
    "negative",
    "nonzero",
    "integer",
    "finite",
    "complex",
    "nonnegative",
    "nonpositive",
}
SAFE_EXPRESSION = re.compile(r"^[A-Za-z0-9_+\-*/^().,\s<>=]+$")
SAFE_SYMBOL = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
ATTRIBUTE_ACCESS = re.compile(r"(?:[A-Za-z_][A-Za-z0-9_]*\s*\.|\.\s*[A-Za-z_])")
BLOCKED_WORDS = {"lambda", "import", "exec", "eval", "open", "globals", "locals"}

SAFE_FUNCTIONS: dict[str, Any] = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "exp": sp.exp,
    "log": sp.log,
    "sqrt": sp.sqrt,
    "Abs": sp.Abs,
    "gamma": sp.gamma,
    "factorial": sp.factorial,
    "floor": sp.floor,
    "ceiling": sp.ceiling,
    "Min": sp.Min,
    "Max": sp.Max,
    "pi": sp.pi,
    "E": sp.E,
    "I": sp.I,
    "oo": sp.oo,
}
SAFE_GLOBALS: dict[str, Any] = {
    "__builtins__": {},
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Symbol": sp.Symbol,
    "Add": sp.Add,
    "Mul": sp.Mul,
    "Pow": sp.Pow,
}
TRANSFORMATIONS = tuple(
    transformation
    for transformation in standard_transformations
    if transformation is not auto_symbol
) + (convert_xor,)


class SymbolicMathInputError(ValueError):
    pass


class SymbolicMathAdapter:
    def __init__(self, *, max_operations: int = 10_000) -> None:
        if max_operations < 1:
            raise ValueError("max_operations must be positive")
        self.max_operations = max_operations
        self.definition = ToolDefinition(
            tool_id="math.symbolic",
            version="1.0.0",
            title="Verified symbolic mathematics",
            description=(
                "Perform structured exact algebra, calculus, limits, series, "
                "equation solving, matrix operations, and equivalence checks."
            ),
            category="mathematics",
            quality_tier=ToolQualityTier.VERIFIED,
            required_scope=ToolScope.COMPUTE,
            execution_mode=ToolExecutionMode.ASYNC,
            deterministic=True,
            cacheable=True,
            timeout_seconds=30,
            max_artifacts=4,
            max_artifact_bytes=2 * 1024 * 1024,
            input_schema=self._input_schema(),
            output_schema=self._output_schema(),
            output_media_types=[
                "application/json",
                "text/plain; charset=utf-8",
                "text/x-tex",
            ],
            quality_gates=[
                "exact_reference_cases",
                "assumption_reporting",
                "safe_structured_parser",
                "operation_complexity_limit",
            ],
            upstream_project="https://www.sympy.org/",
            license="BSD-3-Clause",
        )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        operation = str(arguments.get("operation", ""))
        if operation not in OPERATIONS:
            raise SymbolicMathInputError(f"unsupported operation: {operation!r}")
        symbols, normalized_assumptions = self._symbols(arguments.get("symbols", {}))
        warnings: list[str] = []
        values: list[str] = []
        details: dict[str, Any] = {}
        equivalent: bool | None = None
        result_expression: Any

        if operation == "matrix":
            result_expression, values, details = self._matrix(arguments, symbols)
        else:
            expression = self._parse_required_expression(
                arguments.get("expression"), symbols
            )
            self._check_complexity(expression)
            variable = self._variable(arguments.get("variable"), symbols, expression)

            if operation == "simplify":
                result_expression = sp.simplify(expression)
            elif operation == "factor":
                result_expression = sp.factor(expression)
            elif operation == "expand":
                result_expression = sp.expand(expression)
            elif operation == "differentiate":
                order = self._order(arguments.get("order", 1), maximum=20)
                result_expression = sp.diff(expression, variable, order)
                details["order"] = order
            elif operation == "integrate":
                bounds = arguments.get("bounds")
                if bounds is None:
                    result_expression = sp.integrate(expression, variable)
                else:
                    if not isinstance(bounds, list) or len(bounds) != 2:
                        raise SymbolicMathInputError("bounds must contain lower and upper")
                    lower = self._parse(str(bounds[0]), symbols)
                    upper = self._parse(str(bounds[1]), symbols)
                    result_expression = sp.integrate(
                        expression,
                        (variable, lower, upper),
                    )
                    details["bounds"] = [sp.sstr(lower), sp.sstr(upper)]
            elif operation == "limit":
                point = self._parse(str(arguments.get("point", "0")), symbols)
                direction = str(arguments.get("direction", "+-"))
                if direction not in {"+", "-", "+-"}:
                    raise SymbolicMathInputError("direction must be '+', '-', or '+-'")
                result_expression = sp.limit(
                    expression,
                    variable,
                    point,
                    dir=direction,
                )
                details.update({"point": sp.sstr(point), "direction": direction})
            elif operation == "series":
                point = self._parse(str(arguments.get("point", "0")), symbols)
                order = self._order(arguments.get("order", 6), maximum=50)
                result_expression = sp.series(expression, variable, point, order)
                details.update({"point": sp.sstr(point), "order": order})
            elif operation == "solve":
                solutions = sp.solve(expression, variable)
                solutions = sorted(solutions, key=sp.default_sort_key)
                values = [sp.sstr(item) for item in solutions]
                result_expression = sp.Tuple(*solutions)
                details["solution_count"] = len(solutions)
            elif operation == "equivalent":
                other = self._parse_required_expression(
                    arguments.get("other_expression"), symbols
                )
                self._check_complexity(other)
                difference = sp.simplify(expression - other)
                equivalent = bool(difference == 0)
                result_expression = difference
                details["difference"] = sp.sstr(difference)
            else:  # pragma: no cover - guarded by the operation set
                raise SymbolicMathInputError(f"unsupported operation: {operation!r}")

        self._check_complexity(result_expression)
        if isinstance(result_expression, sp.Tuple):
            exact = f"[{', '.join(values)}]"
            latex_value = sp.latex(list(result_expression))
        else:
            exact = sp.sstr(result_expression)
            latex_value = sp.latex(result_expression)
        free_symbols = sorted(
            {str(item) for item in getattr(result_expression, "free_symbols", set())}
        )
        if getattr(result_expression, "has", lambda *_: False)(sp.Integral):
            warnings.append("result contains an unevaluated integral")

        result = {
            "operation": operation,
            "exact": exact,
            "latex": latex_value,
            "values": values,
            "equivalent": equivalent,
            "variables": free_symbols,
            "assumptions": normalized_assumptions,
            "warnings": warnings,
            "details": details,
        }
        artifacts = self._write_artifacts(context.work_dir, result)
        return ToolExecutionResult(
            result=result,
            warnings=warnings,
            artifacts=artifacts,
            metrics={"operation_count": int(sp.count_ops(result_expression))},
        )

    def _symbols(
        self, raw: Any
    ) -> tuple[dict[str, sp.Symbol], dict[str, dict[str, bool]]]:
        if not isinstance(raw, dict):
            raise SymbolicMathInputError("symbols must be an object")
        if len(raw) > 64:
            raise SymbolicMathInputError("no more than 64 symbols are allowed")
        symbols: dict[str, sp.Symbol] = {}
        normalized: dict[str, dict[str, bool]] = {}
        for name, assumptions in sorted(raw.items()):
            if not isinstance(name, str) or not SAFE_SYMBOL.fullmatch(name):
                raise SymbolicMathInputError(f"invalid symbol name: {name!r}")
            if not isinstance(assumptions, dict):
                raise SymbolicMathInputError(f"assumptions for {name} must be an object")
            unknown = set(assumptions) - ASSUMPTIONS
            if unknown:
                raise SymbolicMathInputError(
                    f"unsupported assumptions for {name}: {sorted(unknown)}"
                )
            if any(not isinstance(value, bool) for value in assumptions.values()):
                raise SymbolicMathInputError(
                    f"assumptions for {name} must contain booleans"
                )
            try:
                symbols[name] = sp.Symbol(name, **assumptions)
            except Exception as exc:
                raise SymbolicMathInputError(
                    f"inconsistent assumptions for {name}: {exc}"
                ) from exc
            normalized[name] = dict(sorted(assumptions.items()))
        return symbols, normalized

    def _parse_required_expression(
        self, raw: Any, symbols: dict[str, sp.Symbol]
    ) -> sp.Expr:
        if not isinstance(raw, str) or not raw.strip():
            raise SymbolicMathInputError("expression is required")
        return self._parse(raw, symbols)

    def _parse(self, raw: str, symbols: dict[str, sp.Symbol]) -> sp.Expr:
        text = raw.strip()
        if len(text) > 20_000:
            raise SymbolicMathInputError("expression exceeds 20,000 characters")
        if (
            not SAFE_EXPRESSION.fullmatch(text)
            or "__" in text
            or ATTRIBUTE_ACCESS.search(text)
        ):
            raise SymbolicMathInputError("expression contains code or attribute syntax")
        identifiers = set(IDENTIFIER.findall(text))
        allowed = set(symbols) | set(SAFE_FUNCTIONS)
        unknown = identifiers - allowed
        if unknown:
            label = "blocked" if unknown & BLOCKED_WORDS else "undeclared"
            raise SymbolicMathInputError(
                f"{label} identifiers in expression: {sorted(unknown)}"
            )
        try:
            value = parse_expr(
                text,
                local_dict={**SAFE_FUNCTIONS, **symbols},
                global_dict=SAFE_GLOBALS,
                transformations=TRANSFORMATIONS,
                evaluate=True,
            )
        except Exception as exc:
            raise SymbolicMathInputError(f"invalid symbolic expression: {exc}") from exc
        if not isinstance(value, sp.Basic):
            raise SymbolicMathInputError("expression did not produce a symbolic value")
        return value

    def _variable(
        self,
        raw: Any,
        symbols: dict[str, sp.Symbol],
        expression: sp.Expr,
    ) -> sp.Symbol:
        if raw is not None:
            name = str(raw)
            if name not in symbols:
                raise SymbolicMathInputError(f"variable {name!r} is not declared")
            return symbols[name]
        candidates = sorted(expression.free_symbols, key=lambda item: str(item))
        if len(candidates) != 1:
            raise SymbolicMathInputError(
                "variable is required when the expression has zero or multiple variables"
            )
        return candidates[0]

    @staticmethod
    def _order(raw: Any, *, maximum: int) -> int:
        if isinstance(raw, bool) or not isinstance(raw, int) or not 1 <= raw <= maximum:
            raise SymbolicMathInputError(f"order must be an integer from 1 to {maximum}")
        return raw

    def _matrix(
        self,
        arguments: dict[str, Any],
        symbols: dict[str, sp.Symbol],
    ) -> tuple[Any, list[str], dict[str, Any]]:
        raw = arguments.get("matrix")
        if (
            not isinstance(raw, list)
            or not raw
            or not all(isinstance(row, list) and row for row in raw)
        ):
            raise SymbolicMathInputError("matrix must be a non-empty rectangular array")
        widths = {len(row) for row in raw}
        if len(widths) != 1:
            raise SymbolicMathInputError("matrix rows must have the same length")
        if len(raw) > 20 or next(iter(widths)) > 20:
            raise SymbolicMathInputError("matrix dimensions cannot exceed 20 by 20")
        matrix = sp.Matrix(
            [[self._parse(str(item), symbols) for item in row] for row in raw]
        )
        matrix_operation = str(arguments.get("matrix_operation", ""))
        if matrix_operation not in MATRIX_OPERATIONS:
            raise SymbolicMathInputError(
                f"unsupported matrix operation: {matrix_operation!r}"
            )
        values: list[str] = []
        details: dict[str, Any] = {
            "shape": [matrix.rows, matrix.cols],
            "matrix_operation": matrix_operation,
        }
        if matrix_operation == "determinant":
            if matrix.rows != matrix.cols:
                raise SymbolicMathInputError("determinant requires a square matrix")
            result: Any = matrix.det()
        elif matrix_operation == "inverse":
            if matrix.rows != matrix.cols:
                raise SymbolicMathInputError("inverse requires a square matrix")
            try:
                result = matrix.inv()
            except Exception as exc:
                raise SymbolicMathInputError(f"matrix is not invertible: {exc}") from exc
            details["matrix"] = [
                [sp.sstr(result[row, column]) for column in range(result.cols)]
                for row in range(result.rows)
            ]
        elif matrix_operation == "rank":
            result = sp.Integer(matrix.rank())
        else:
            eigenvalues = matrix.eigenvals()
            ordered = sorted(eigenvalues, key=sp.default_sort_key)
            values = [sp.sstr(item) for item in ordered]
            details["multiplicities"] = {
                sp.sstr(item): int(eigenvalues[item]) for item in ordered
            }
            result = sp.Tuple(*ordered)
        return result, values, details

    def _check_complexity(self, value: Any) -> None:
        operations = int(sp.count_ops(value))
        if operations > self.max_operations:
            raise SymbolicMathInputError(
                f"expression complexity {operations} exceeds limit {self.max_operations}"
            )

    @staticmethod
    def _write_artifacts(
        work_dir: Path,
        result: dict[str, Any],
    ) -> list[ToolProducedArtifact]:
        work_dir.mkdir(parents=True, exist_ok=True)
        json_name = "symbolic-result.json"
        tex_name = "symbolic-result.tex"
        (work_dir / json_name).write_bytes(
            (
                json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
                + "\n"
            ).encode("utf-8")
        )
        (work_dir / tex_name).write_bytes((str(result["latex"]) + "\n").encode("utf-8"))
        return [
            ToolProducedArtifact(
                name=json_name,
                media_type="application/json",
                source_path=json_name,
            ),
            ToolProducedArtifact(
                name=tex_name,
                media_type="text/x-tex",
                source_path=tex_name,
            ),
        ]

    @staticmethod
    def _input_schema() -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": list(OPERATIONS)},
                "expression": {"type": "string", "minLength": 1, "maxLength": 20_000},
                "other_expression": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 20_000,
                },
                "symbols": {
                    "type": "object",
                    "maxProperties": 64,
                    "additionalProperties": {
                        "type": "object",
                        "propertyNames": {"enum": sorted(ASSUMPTIONS)},
                        "additionalProperties": {"type": "boolean"},
                    },
                },
                "variable": {"type": "string"},
                "point": {"type": "string"},
                "direction": {"type": "string", "enum": ["+", "-", "+-"]},
                "order": {"type": "integer", "minimum": 1, "maximum": 50},
                "bounds": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2,
                    "maxItems": 2,
                },
                "matrix": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "string"}},
                },
                "matrix_operation": {
                    "type": "string",
                    "enum": list(MATRIX_OPERATIONS),
                },
            },
            "required": ["operation", "symbols"],
            "additionalProperties": False,
        }

    @staticmethod
    def _output_schema() -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string"},
                "exact": {"type": "string"},
                "latex": {"type": "string"},
                "values": {"type": "array", "items": {"type": "string"}},
                "equivalent": {"type": ["boolean", "null"]},
                "variables": {"type": "array", "items": {"type": "string"}},
                "assumptions": {"type": "object"},
                "warnings": {"type": "array", "items": {"type": "string"}},
                "details": {"type": "object"},
            },
            "required": [
                "operation",
                "exact",
                "latex",
                "values",
                "equivalent",
                "variables",
                "assumptions",
                "warnings",
                "details",
            ],
            "additionalProperties": False,
        }
