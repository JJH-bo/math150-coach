from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.tools.adapters.optimize_math import OptimizeMathAdapter, OptimizeMathInputError
from app.tools.contracts import ToolExecutionContext


def execute(tmp_path: Path, **arguments):
    return OptimizeMathAdapter().execute(
        arguments,
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def test_optimize_definition_is_verified_bounded_and_structured() -> None:
    definition = OptimizeMathAdapter().definition

    assert definition.tool_id == "math.optimize"
    assert definition.version == "1.0.0"
    assert definition.quality_tier.value == "verified"
    assert definition.required_scope.value == "studio.compute"
    assert definition.input_schema["additionalProperties"] is False
    assert "arbitrary_code_rejected" in definition.quality_gates


def test_linear_program_reports_solution_and_feasibility(tmp_path: Path) -> None:
    result = execute(
        tmp_path,
        operation="linear_program",
        variables=["x", "y"],
        goal="minimize",
        objective_coefficients=[3, 2],
        bounds=[[0, None], [0, None]],
        linear_constraints=[
            {"coefficients": [1, 1], "relation": ">=", "rhs": 4}
        ],
        tolerance=1e-9,
    ).result

    assert result["solver"] == "scipy.optimize.linprog.highs"
    assert result["success"] is True
    assert result["solution"] == pytest.approx({"x": 0.0, "y": 4.0}, abs=1e-8)
    assert result["objective_value"] == pytest.approx(8.0)
    assert result["constraint_violation"] <= 1e-9
    assert result["details"]["global_optimum"] is True
    assert "duality_gap" not in result["details"]
    assert result["details"]["crossover_iterations"] >= 0


def test_continuous_program_supports_safe_constraints(tmp_path: Path) -> None:
    result = execute(
        tmp_path,
        operation="continuous",
        variables=["x", "y"],
        goal="minimize",
        objective_expression="(x - 1)**2 + (y - 2)**2",
        initial_point=[0, 0],
        bounds=[[-5, 5], [-5, 5]],
        constraints=[
            {"expression": "x + y", "relation": ">=", "rhs": 3}
        ],
        tolerance=1e-9,
        max_iterations=500,
    ).result

    assert result["solver"] == "scipy.optimize.minimize.SLSQP"
    assert result["success"] is True
    assert result["solution"] == pytest.approx({"x": 1.0, "y": 2.0}, abs=1e-5)
    assert result["objective_value"] == pytest.approx(0.0, abs=1e-9)
    assert result["constraint_violation"] <= 1e-8
    assert result["details"]["global_optimum"] is False


def test_least_squares_reports_residual_evidence(tmp_path: Path) -> None:
    result = execute(
        tmp_path,
        operation="least_squares",
        variables=["x"],
        residual_expressions=["x - 1", "2*x - 2"],
        initial_point=[0],
        bounds=[[-10, 10]],
        tolerance=1e-10,
    ).result

    assert result["solver"] == "scipy.optimize.least_squares.trf"
    assert result["solution"] == pytest.approx({"x": 1.0}, abs=1e-8)
    assert result["objective_value"] == pytest.approx(0.0, abs=1e-12)
    assert result["optimality"] <= 1e-8
    assert result["details"]["residuals"] == pytest.approx([0.0, 0.0], abs=1e-8)


@pytest.mark.parametrize(
    "arguments",
    [
        {
            "operation": "continuous",
            "variables": ["x"],
            "objective_expression": "__import__('os').system('whoami')",
            "initial_point": [0],
            "bounds": [[-1, 1]],
        },
        {
            "operation": "continuous",
            "variables": ["x"],
            "objective_expression": "x**2",
            "initial_point": [0],
            "bounds": [[2, 1]],
        },
        {
            "operation": "linear_program",
            "variables": ["x", "y"],
            "objective_coefficients": [1],
            "bounds": [[0, 1], [0, 1]],
        },
    ],
)
def test_unsafe_or_inconsistent_programs_are_rejected(
    tmp_path: Path, arguments: dict
) -> None:
    with pytest.raises(OptimizeMathInputError):
        execute(tmp_path, **arguments)


def test_optimization_artifacts_are_deterministic_json_and_csv(
    tmp_path: Path,
) -> None:
    output = execute(
        tmp_path,
        operation="linear_program",
        variables=["x"],
        objective_coefficients=[1],
        bounds=[[2, 3]],
    )

    assert [artifact.name for artifact in output.artifacts] == [
        "optimization-result.json",
        "optimization-solution.csv",
    ]
    parsed = json.loads(
        (tmp_path / "optimization-result.json").read_text(encoding="utf-8")
    )
    assert parsed == output.result
    assert (tmp_path / "optimization-solution.csv").read_bytes().endswith(b"\n")
