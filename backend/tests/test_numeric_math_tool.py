from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from app.tools.adapters.numeric_math import NumericMathAdapter, NumericMathInputError
from app.tools.contracts import ToolExecutionContext


def execute(tmp_path: Path, **arguments):
    return NumericMathAdapter().execute(
        arguments,
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def test_numeric_definition_is_verified_and_structured() -> None:
    definition = NumericMathAdapter().definition

    assert definition.tool_id == "math.numeric"
    assert definition.version == "1.0.0"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.compute"
    assert definition.input_schema["additionalProperties"] is False


def test_statistics_return_reference_values(tmp_path: Path) -> None:
    result = execute(
        tmp_path,
        operation="statistics",
        values=[1, 2, 3, 4],
        quantiles=[0.25, 0.5, 0.75],
    ).result

    assert result["scalar"] is None
    assert result["details"]["count"] == 4
    assert result["details"]["mean"] == pytest.approx(2.5)
    assert result["details"]["sample_std"] == pytest.approx(math.sqrt(5 / 3))
    assert result["details"]["quantiles"] == pytest.approx([1.75, 2.5, 3.25])


def test_linear_system_and_eigenvalues_are_structured(tmp_path: Path) -> None:
    solved = execute(
        tmp_path,
        operation="linear_solve",
        matrix=[[2, 1], [1, -1]],
        vector=[5, 1],
    ).result
    eigen = execute(
        tmp_path,
        operation="eigenvalues",
        matrix=[[0, -1], [1, 0]],
    ).result

    assert solved["values"] == pytest.approx([2.0, 1.0])
    assert solved["details"]["residual_norm"] < 1e-12
    assert eigen["values"] == [
        {"real": 0.0, "imag": -1.0},
        {"real": 0.0, "imag": 1.0},
    ]


def test_quadrature_root_and_minimization_use_safe_expressions(tmp_path: Path) -> None:
    integral = execute(
        tmp_path,
        operation="quadrature",
        expression="sin(x)",
        variable="x",
        interval=[0, "pi"],
        tolerance=1e-10,
    ).result
    root = execute(
        tmp_path,
        operation="root",
        expression="cos(x) - x",
        variable="x",
        bracket=[0, 1],
        tolerance=1e-12,
    ).result
    minimum = execute(
        tmp_path,
        operation="minimize_scalar",
        expression="(x - 3)**2 + 2",
        variable="x",
        bounds=[-10, 10],
        tolerance=1e-10,
    ).result

    assert integral["scalar"] == pytest.approx(2.0, rel=1e-10)
    assert root["scalar"] == pytest.approx(0.7390851332, rel=1e-10)
    assert minimum["scalar"] == pytest.approx(3.0, abs=1e-7)
    assert minimum["details"]["function_value"] == pytest.approx(2.0)


def test_interpolation_ode_and_fft_reference_cases(tmp_path: Path) -> None:
    interpolated = execute(
        tmp_path,
        operation="interpolate",
        x=[0, 1, 2],
        y=[0, 1, 4],
        query_points=[0.5, 1.5],
        method="linear",
    ).result
    ode = execute(
        tmp_path,
        operation="ode",
        expression="y",
        variables=["t", "y"],
        interval=[0, 1],
        initial_values=[1],
        sample_count=5,
        tolerance=1e-9,
    ).result
    fft = execute(
        tmp_path,
        operation="fft",
        values=[0, 1, 0, -1],
        sample_spacing=0.25,
    ).result

    assert interpolated["values"] == pytest.approx([0.5, 2.5])
    assert ode["values"][-1][1] == pytest.approx(math.e, rel=1e-7)
    dominant = max(fft["values"][1:], key=lambda item: item["magnitude"])
    assert dominant["frequency"] == pytest.approx(1.0)


def test_named_probability_distributions_are_bounded(tmp_path: Path) -> None:
    normal = execute(
        tmp_path,
        operation="distribution",
        distribution="normal",
        distribution_operation="cdf",
        parameters={"loc": 0, "scale": 1},
        points=[0],
    ).result
    binomial = execute(
        tmp_path,
        operation="distribution",
        distribution="binomial",
        distribution_operation="pmf",
        parameters={"n": 4, "p": 0.5},
        points=[2],
    ).result

    assert normal["values"] == pytest.approx([0.5])
    assert binomial["values"] == pytest.approx([0.375])


@pytest.mark.parametrize(
    "arguments",
    [
        {"operation": "statistics", "values": [1, float("nan")]},
        {
            "operation": "quadrature",
            "expression": "__import__('os').system('whoami')",
            "variable": "x",
            "interval": [0, 1],
        },
        {
            "operation": "linear_solve",
            "matrix": [[1, 2], [2, 4]],
            "vector": [1, 2],
        },
        {"operation": "fft", "values": [1] * 20_001},
    ],
)
def test_invalid_nonfinite_unsafe_singular_and_oversized_inputs_fail(
    tmp_path: Path, arguments: dict
) -> None:
    with pytest.raises(NumericMathInputError):
        execute(tmp_path, **arguments)


def test_numeric_artifacts_are_deterministic_json_and_csv(tmp_path: Path) -> None:
    output = execute(
        tmp_path,
        operation="statistics",
        values=[1, 2, 3],
    )

    assert [artifact.name for artifact in output.artifacts] == [
        "numeric-result.json",
        "numeric-table.csv",
    ]
    parsed = json.loads((tmp_path / "numeric-result.json").read_text("utf-8"))
    assert parsed == output.result
    assert (tmp_path / "numeric-table.csv").read_bytes().endswith(b"\n")
