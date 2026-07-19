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
    assert report["failed_responses"] == []
    assert report["base_url"] == "<local-classroom-server>"
    assert report["requests"][0] == "/"
    assert not any("127.0.0.1" in request for request in report["requests"])
    assert checks["root_redirected_to_classroom"] is True
    assert checks["module_destinations"] >= 1
    assert checks["initial_revealed_steps"] == 1
    assert checks["reveal_added_one_stable_step"] is True
    assert checks["formula_pair_visible"] is True
    assert checks["formula_typeset"] is True
    assert checks["model_visible"] is True
    assert checks["gpt_expansion_inserted_in_place"] is True
    assert checks["gpt_expansion_has_substantial_content"] is True
    assert checks["nested_expansion_visible"] is True
    assert checks["return_restored_parent_expansion"] is True
    assert checks["detail_open"] is True
    assert checks["detail_model_state"]["highlightedTarget"] == "target-value"
    assert checks["fullscreen_open"] is True
    assert checks["fullscreen_return_scroll_delta"] <= 1
    assert checks["reload_restored_module"] is True
    assert checks["reload_restored_detail"] is True
    assert checks["reload_restored_model_state"] is True
    assert checks["return_reload_stays_atlas"] is True
    assert checks["desktop_horizontal_overflow"] <= 0
    assert checks["mobile_horizontal_overflow"] <= 0
    assert checks["mobile_model_visible"] is True
    assert checks["forbidden_product_requests"] == []
    assert "score" not in report["scene_snapshot"]
    assert "diagnosis" not in report["scene_snapshot"]
