from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "docs" / "preview-artifacts" / "tool-platform-core"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_checked_in_compose_and_optimization_evidence_is_real_and_secret_free() -> None:
    registry = read_json(EVIDENCE / "tool-registry.json")
    composed = read_json(EVIDENCE / "classroom-compose-job.json")
    optimized = read_json(EVIDENCE / "optimization-job.json")
    compose_report = read_json(
        EVIDENCE / "classroom-compose" / "composition-report.json"
    )
    optimization_report = read_json(
        EVIDENCE / "optimization" / "optimization-result.json"
    )

    assert registry["total"] == 22
    tool_ids = {item["tool_id"] for item in registry["tools"]}
    assert {"classroom.compose", "math.optimize"} <= tool_ids
    assert composed["state"] == optimized["state"] == "succeeded"
    assert composed["result"]["publish_ready"] is True
    assert composed["result"]["applied"] is False
    assert compose_report["validation"]["passed"] is True
    assert optimized["result"]["success"] is True
    assert optimized["result"]["solution"] == {"x": 1.0, "y": 2.0}
    assert optimized["result"]["constraint_violation"] <= 1e-8
    assert optimization_report == optimized["result"]

    serialized = "\n".join(
        path.read_text(encoding="utf-8", errors="ignore")
        for path in (
            EVIDENCE / "classroom-compose-job.json",
            EVIDENCE / "optimization-job.json",
            EVIDENCE / "classroom-compose" / "composition-report.json",
            EVIDENCE / "optimization" / "optimization-result.json",
        )
    ).lower()
    assert "studio_api_key" not in serialized
    assert "temporary-evidence-key" not in serialized
    assert "math150-tool-evidence-" not in serialized
