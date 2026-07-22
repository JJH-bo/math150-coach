from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.tools.adapters.math_verify import MathVerifyAdapter, MathVerifyInputError
from app.tools.contracts import ToolExecutionContext


def execute(tmp_path: Path, **arguments):
    return MathVerifyAdapter().execute(
        arguments,
        ToolExecutionContext(
            job_id="tj-000000000000000000000000",
            work_dir=tmp_path,
        ),
    )


def test_definition_is_verified_independent_comparison() -> None:
    definition = MathVerifyAdapter().definition

    assert definition.tool_id == "math.verify"
    assert definition.quality_tier.value == "verified"
    assert "counterexample" in definition.description.lower()


def test_exact_equivalence_respects_positive_assumption(tmp_path: Path) -> None:
    result = execute(
        tmp_path,
        left_expression="sqrt(x**2)",
        right_expression="x",
        symbols={"x": {"positive": True}},
    ).result

    assert result["verdict"] == "equivalent"
    assert result["exact_equivalent"] is True
    assert result["counterexample"] is None
    assert result["assumptions"]["x"]["positive"] is True


def test_non_equivalence_returns_deterministic_counterexample(tmp_path: Path) -> None:
    result = execute(
        tmp_path,
        left_expression="sin(x)",
        right_expression="x",
        symbols={"x": {"real": True}},
        domains={"x": [-1, 1]},
        tolerance=1e-10,
        sample_count=32,
    ).result

    assert result["verdict"] == "not_equivalent"
    assert result["exact_equivalent"] is False
    assert result["tested_sample_count"] >= 1
    assert result["counterexample"]["absolute_error"] > 1e-10
    assert set(result["counterexample"]["inputs"]) == {"x"}


def test_removable_domain_points_are_excluded_without_false_failure(
    tmp_path: Path,
) -> None:
    result = execute(
        tmp_path,
        left_expression="(x**2 - 1)/(x - 1)",
        right_expression="x + 1",
        symbols={"x": {"real": True}},
        domains={"x": [-2, 2]},
        sample_count=33,
    ).result

    assert result["verdict"] == "equivalent"
    assert result["exact_equivalent"] is True
    assert result["excluded_points"]
    assert result["excluded_points"][0]["reason"] == "undefined_or_nonfinite"


def test_near_equal_but_not_proven_can_be_inconclusive(tmp_path: Path) -> None:
    result = execute(
        tmp_path,
        left_expression="x",
        right_expression="x + 1/1000000000000",
        symbols={"x": {"real": True}},
        domains={"x": [-1, 1]},
        tolerance=1e-9,
        sample_count=16,
    ).result

    assert result["verdict"] == "inconclusive"
    assert result["exact_equivalent"] is False
    assert result["max_absolute_error"] < 1e-9


@pytest.mark.parametrize(
    "arguments",
    [
        {
            "left_expression": "x.__class__",
            "right_expression": "x",
            "symbols": {"x": {"real": True}},
        },
        {
            "left_expression": "x",
            "right_expression": "x",
            "symbols": {"x": {"real": True}},
            "domains": {"y": [0, 1]},
        },
        {
            "left_expression": "x",
            "right_expression": "x",
            "symbols": {"x": {"real": True}},
            "domains": {"x": [1, 1]},
        },
    ],
)
def test_unsafe_or_invalid_domain_inputs_fail(
    tmp_path: Path, arguments: dict
) -> None:
    with pytest.raises(MathVerifyInputError):
        execute(tmp_path, **arguments)


def test_verification_artifacts_include_json_and_sample_evidence(tmp_path: Path) -> None:
    output = execute(
        tmp_path,
        left_expression="x**2",
        right_expression="x*x",
        symbols={"x": {"real": True}},
    )

    assert [item.name for item in output.artifacts] == [
        "verification-result.json",
        "verification-samples.csv",
    ]
    assert json.loads(
        (tmp_path / "verification-result.json").read_text(encoding="utf-8")
    ) == output.result
