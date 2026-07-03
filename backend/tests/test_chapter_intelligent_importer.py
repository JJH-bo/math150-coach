from __future__ import annotations

from fastapi.testclient import TestClient

from app.challenge.chapter_intelligent_importer import build_intelligent_chapter_draft
from app.main import create_app
from app.training.session_log import ensure_no_trusted_fields

LOOSE_ODE_NOTES = """
微分方程这一章要先分类，再选方法。一阶可分离变量要把 dy 和 dx 分到两边；一阶线性用积分因子；
二阶常系数齐次方程看特征方程，非齐次方程要判断特解形式。常见错误是没有先识别类型，
直接套公式，或者通解里的任意常数和初值条件处理错。
"""


def test_intelligent_importer_generates_valid_logic_network_from_loose_notes() -> None:
    payload = build_intelligent_chapter_draft(
        LOOSE_ODE_NOTES,
        chapter_id="smart_ode_test",
        title="微分方程智能导入测试",
    )

    assert payload["mode"] == "intelligent_chapter_draft_generation"
    assert payload["profile"]["code"] == "ode"
    assert payload["profile"]["confidence"] == "high"
    assert payload["draft_validation"]["report"]["passed"] is True
    assert payload["draft_validation"]["preview"]["counts"]["micro_nodes"] == 6
    assert payload["candidate_preview"]["candidate_quality"]["grade"] == "pass"
    assert "## ErrorRepairMap" in payload["generated_markdown"]
    ensure_no_trusted_fields(payload)


def test_intelligent_importer_api_returns_candidate_preview() -> None:
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/authoring/chapter-draft/intelligent-generate",
        json={
            "source_text": LOOSE_ODE_NOTES,
            "chapter_id": "smart_ode_api_test",
            "title": "微分方程智能导入 API 测试",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["chapter_id"] == "smart_ode_api_test"
    assert payload["draft_validation"]["report"]["passed"] is True
    assert payload["candidate_preview"]["candidate_quality"]["grade"] == "pass"
    assert payload["human_review_required"] is True
