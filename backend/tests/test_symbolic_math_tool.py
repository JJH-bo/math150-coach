from __future__ import annotations

from pathlib import Path

import pytest

from app.tools.adapters.symbolic_math import (
    SymbolicMathAdapter,
    SymbolicMathInputError,
)
from app.tools.contracts import (
    ToolExecutionContext,
    ToolQualityTier,
    ToolScope,
)


def execute(tmp_path: Path, **arguments):
    return SymbolicMathAdapter().execute(
        arguments,
        ToolExecutionContext(
            job_id="tj-0123456789abcdef01234567",
            work_dir=tmp_path,
        ),
    )


def test_definition_exposes_verified_structured_symbolic_contract() -> None:
    definition = SymbolicMathAdapter().definition

    assert definition.tool_id == "math.symbolic"
    assert definition.version == "1.0.0"
    assert definition.quality_tier == ToolQualityTier.VERIFIED
    assert definition.required_scope == ToolScope.COMPUTE
    assert "solve" in definition.input_schema["properties"]["operation"]["enum"]
    assert "text/x-tex" in definition.output_media_types


def test_factor_and_expand_are_exact_round_trip_operations(tmp_path: Path) -> None:
    factored = execute(
        tmp_path,
        operation="factor",
        expression="x**2 - 1",
        symbols={"x": {"real": True}},
    )
    expanded = execute(
        tmp_path,
        operation="expand",
        expression=factored.result["exact"],
        symbols={"x": {"real": True}},
    )

    assert factored.result["exact"] == "(x - 1)*(x + 1)"
    assert expanded.result["exact"] == "x**2 - 1"
    assert factored.result["latex"] == r"\left(x - 1\right) \left(x + 1\right)"


def test_differentiate_and_integrate_return_exact_and_latex(tmp_path: Path) -> None:
    derivative = execute(
        tmp_path,
        operation="differentiate",
        expression="sin(x)**2",
        variable="x",
        symbols={"x": {"real": True}},
    )
    integral = execute(
        tmp_path,
        operation="integrate",
        expression="2*x",
        variable="x",
        symbols={"x": {"real": True}},
    )

    assert derivative.result["exact"] == "2*sin(x)*cos(x)"
    assert integral.result["exact"] == "x**2"
    assert derivative.result["latex"]
    assert integral.result["latex"] == "x^{2}"


def test_limit_and_series_are_parameterized(tmp_path: Path) -> None:
    limit = execute(
        tmp_path,
        operation="limit",
        expression="sin(x)/x",
        variable="x",
        point="0",
        direction="+",
        symbols={"x": {"real": True}},
    )
    series = execute(
        tmp_path,
        operation="series",
        expression="exp(x)",
        variable="x",
        point="0",
        order=4,
        symbols={"x": {"real": True}},
    )

    assert limit.result["exact"] == "1"
    assert series.result["exact"] == "1 + x + x**2/2 + x**3/6 + O(x**4)"


def test_solve_returns_deterministically_sorted_exact_values(tmp_path: Path) -> None:
    result = execute(
        tmp_path,
        operation="solve",
        expression="x**2 - 1",
        variable="x",
        symbols={"x": {"real": True}},
    )

    assert result.result["values"] == ["-1", "1"]
    assert result.result["exact"] == "[-1, 1]"


def test_matrix_determinant_and_inverse_are_structured(tmp_path: Path) -> None:
    determinant = execute(
        tmp_path,
        operation="matrix",
        matrix_operation="determinant",
        matrix=[["1", "2"], ["3", "4"]],
        symbols={},
    )
    inverse = execute(
        tmp_path,
        operation="matrix",
        matrix_operation="inverse",
        matrix=[["1", "2"], ["3", "4"]],
        symbols={},
    )

    assert determinant.result["exact"] == "-2"
    assert inverse.result["details"]["matrix"] == [
        ["-2", "1"],
        ["3/2", "-1/2"],
    ]


def test_equivalence_respects_declared_symbol_assumptions(tmp_path: Path) -> None:
    result = execute(
        tmp_path,
        operation="equivalent",
        expression="sqrt(x**2)",
        other_expression="x",
        symbols={"x": {"positive": True}},
    )

    assert result.result["equivalent"] is True
    assert result.result["assumptions"]["x"]["positive"] is True


@pytest.mark.parametrize(
    "expression",
    [
        "__import__('os').system('whoami')",
        "x.__class__",
        "lambda: 1",
        "open('secret')",
        "[x for x in (1, 2)]",
    ],
)
def test_parser_rejects_code_and_attribute_syntax(
    tmp_path: Path,
    expression: str,
) -> None:
    with pytest.raises(SymbolicMathInputError):
        execute(
            tmp_path,
            operation="simplify",
            expression=expression,
            symbols={"x": {"real": True}},
        )


def test_adapter_rejects_undeclared_symbols_and_unknown_operations(tmp_path: Path) -> None:
    with pytest.raises(SymbolicMathInputError, match="undeclared"):
        execute(
            tmp_path,
            operation="simplify",
            expression="x + y",
            symbols={"x": {"real": True}},
        )
    with pytest.raises(SymbolicMathInputError, match="unsupported operation"):
        execute(
            tmp_path,
            operation="run_python",
            expression="x",
            symbols={"x": {"real": True}},
        )


def test_adapter_rejects_expression_over_complexity_limit(tmp_path: Path) -> None:
    adapter = SymbolicMathAdapter(max_operations=5)
    expression = "x"
    for _ in range(8):
        expression = f"sin({expression})"

    with pytest.raises(SymbolicMathInputError, match="complexity"):
        adapter.execute(
            {
                "operation": "simplify",
                "expression": expression,
                "symbols": {"x": {"real": True}},
            },
            ToolExecutionContext(
                job_id="tj-0123456789abcdef01234567",
                work_dir=tmp_path,
            ),
        )


def test_adapter_writes_deterministic_json_and_tex_artifacts(tmp_path: Path) -> None:
    result = execute(
        tmp_path,
        operation="factor",
        expression="x**2 - 1",
        symbols={"x": {"real": True}},
    )

    assert [artifact.name for artifact in result.artifacts] == [
        "symbolic-result.json",
        "symbolic-result.tex",
    ]
    assert (tmp_path / "symbolic-result.json").read_bytes().endswith(b"\n")
    assert (tmp_path / "symbolic-result.tex").read_text(encoding="utf-8") == (
        "\\left(x - 1\\right) \\left(x + 1\\right)\n"
    )
