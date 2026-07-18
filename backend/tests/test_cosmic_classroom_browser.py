from __future__ import annotations

import os

import pytest

from tools.generate_project_c_evidence import generate


@pytest.mark.skipif(
    not all(os.getenv(name) for name in ("MODEL_PREVIEW_NODE", "NODE_PATH", "MODEL_PREVIEW_BROWSER")),
    reason="real classroom browser environment is not configured",
)
def test_cosmic_classroom_real_browser_flow(tmp_path) -> None:
    report = generate(tmp_path)
    checks = report["checks"]

    assert report["errors"] == []
    assert checks["module_destinations"] >= 1
    assert checks["formula_pair_visible"] is True
    assert checks["model_visible"] is True
    assert checks["detail_open"] is True
    assert checks["detail_model_state"]["highlightedTarget"] == "target-value"
    assert checks["fullscreen_open"] is True
    assert checks["fullscreen_return_scroll_delta"] <= 1
    assert checks["reload_restored_module"] is True
    assert checks["reload_restored_detail"] is True
    assert checks["return_reload_stays_atlas"] is True
    assert checks["desktop_horizontal_overflow"] <= 0
    assert checks["mobile_horizontal_overflow"] <= 0
    assert checks["mobile_model_visible"] is True
    assert checks["legacy_requests"] == []
    assert "score" not in report["scene_snapshot"]
    assert "diagnosis" not in report["scene_snapshot"]
