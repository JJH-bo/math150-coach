from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.api.challenge.v1 import router as challenge_router
from app.logic_graph.models import LogicGraphQualityIssue, LogicGraphQualityReport, LogicQualitySeverity
from app.logic_graph.repository import LogicGraphRepositoryError
from app.main import create_app
from app.training.session_log import ensure_no_trusted_fields


def test_runtime_quality_report_endpoint_is_read_only_and_learner_safe() -> None:
    client = TestClient(create_app("mixed"))

    response = client.get("/api/challenge/v1/quality/ode_network_mvp")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "runtime_graph_quality"
    assert payload["publish_state"] == "read_only"
    assert payload["chapter_id"] == "ode_network_mvp"
    assert payload["report"]["passed"] is True
    assert payload["report"]["error_count"] == 0
    assert isinstance(payload["report"]["issues"], list)
    assert all("node_id" not in issue for issue in payload["report"]["issues"])
    text = json.dumps(payload, ensure_ascii=False)
    assert "logic_overlay" not in text
    assert "current_question" not in text
    assert "expected_answer" not in text
    assert "solution_outline" not in text
    ensure_no_trusted_fields(payload)


def test_runtime_quality_report_sanitizes_quality_issue_details(monkeypatch) -> None:
    raw_hidden_id = "hidden_ability_alpha"

    def fake_validate(self, graph, logic_graph) -> LogicGraphQualityReport:
        return LogicGraphQualityReport(
            chapter_id=graph.chapter_id,
            issue_count=1,
            error_count=1,
            issues=[
                LogicGraphQualityIssue(
                    severity=LogicQualitySeverity.ERROR,
                    code="micro_missing_hidden_ability",
                    message=f"Hidden ability is exposed: {raw_hidden_id}.",
                    node_id=raw_hidden_id,
                )
            ],
        )

    monkeypatch.setattr(challenge_router.KnowledgeGraphQualityValidator, "validate", fake_validate)
    client = TestClient(create_app("mixed"))

    response = client.get("/api/challenge/v1/quality/ode_network_mvp")

    assert response.status_code == 200
    payload = response.json()
    assert payload["report"]["passed"] is False
    assert payload["report"]["error_count"] == 1
    assert payload["report"]["issues"] == [
        {"severity": "error", "code": "micro_missing_hidden_ability"}
    ]
    assert raw_hidden_id not in json.dumps(payload, ensure_ascii=False)
    ensure_no_trusted_fields(payload)


def test_runtime_quality_report_returns_structured_error_for_logic_graph_load_failure(monkeypatch) -> None:
    def fail_try_load_graph(self, chapter_id):
        raise LogicGraphRepositoryError("invalid logic graph YAML: hidden_ability_alpha")

    monkeypatch.setattr(challenge_router.LogicGraphRepository, "try_load_graph", fail_try_load_graph)
    client = TestClient(create_app("mixed"), raise_server_exceptions=False)

    response = client.get("/api/challenge/v1/quality/ode_network_mvp")

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "challenge_error"
    assert "hidden_ability_alpha" not in json.dumps(response.json(), ensure_ascii=False)


def test_atlas_exposes_cosmic_visual_grammar_without_detail_graph() -> None:
    client = TestClient(create_app("mixed"))

    response = client.get("/api/challenge/v1/atlas")

    assert response.status_code == 200
    payload = response.json()
    assert payload["visual_grammar"]["subject_role"] == "subject_galaxy"
    assert payload["visual_grammar"]["chapter_role"] == "chapter_nebula"
    assert payload["visual_grammar"]["detail_role"] == "knowledge_constellation"
    region = payload["regions"][0]
    assert region["visual_role"]["celestial_role"] == "chapter_nebula"
    assert region["visual_role"]["primary_tone"] in {"cyan", "gold", "green"}
    assert region["visual_role"]["detail_entry"] == "lazy_drilldown"
    text = json.dumps(payload, ensure_ascii=False)
    assert "logic_overlay" not in text
    assert "current_question" not in text
    ensure_no_trusted_fields(payload)
