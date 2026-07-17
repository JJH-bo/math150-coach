from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.challenge.chapter_correction_regeneration import build_chapter_correction_dry_run
from app.challenge.chapter_intelligent_importer import build_intelligent_chapter_draft
from app.main import create_app


def test_chapter_correction_dry_run_patches_candidate_and_regenerates_questions() -> None:
    candidate = _candidate_from_materials()
    corrected_formula = "dz=f_x dx+f_y dy + teacher_checked_path"
    corrected_title = "teacher calibrated calculation execution"

    payload = build_chapter_correction_dry_run(
        candidate,
        corrections=[
            {
                "op": "replace",
                "target": "material_evidence",
                "field": "core_formulas",
                "value": [corrected_formula],
            },
            {
                "op": "replace",
                "target": "micro_node",
                "id": "correction_pkg.calculation",
                "field": "title",
                "value": corrected_title,
            },
        ],
        editor="teacher-a",
        notes="calculation formula needs a teacher-reviewed wording",
    )

    assert payload["mode"] == "chapter_correction_dry_run"
    assert payload["dry_run_only"] is True
    assert payload["formal_publish_allowed"] is False
    assert payload["correction_record"]["editor"] == "teacher-a"
    assert payload["correction_record"]["status"] == "accepted"
    assert payload["before"]["candidate_content_hash"] != payload["after"]["candidate_content_hash"]
    assert payload["after"]["candidate"]["material_evidence"]["core_formulas"] == [corrected_formula]
    assert payload["after"]["question_package"]["quality_report"]["grade"] == "pass"
    assert payload["after"]["candidate_quality"]["grade"] == "pass"

    assert "candidate" in payload["regeneration_scope"]
    assert "questions.yaml" in payload["regeneration_scope"]
    assert "quality_report" in payload["regeneration_scope"]
    assert payload["diff"]["changed_paths"] == [
        "material_evidence.core_formulas",
        "challenge_graph.micro_nodes[correction_pkg.calculation].title",
    ]
    assert payload["diff"]["changed_question_ids"]
    assert any("calculation" in question_id for question_id in payload["diff"]["changed_question_ids"])
    assert "correction_pkg.calculation" in payload["affected_content"]["node_ids"]
    assert payload["affected_content"]["question_ids"] == payload["diff"]["changed_question_ids"]

    serialized_questions = json.dumps(payload["after"]["question_package"]["question_bank"], ensure_ascii=False)
    assert corrected_formula in serialized_questions
    assert corrected_title in serialized_questions


def test_chapter_correction_dry_run_api_returns_preview_only_payload() -> None:
    candidate = _candidate_from_materials()
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/authoring/chapter-package/correction-dry-run",
        json={
            "candidate": candidate,
            "corrections": [
                {
                    "op": "replace",
                    "target": "micro_node",
                    "id": "correction_pkg.calculation",
                    "field": "title",
                    "value": "api calibrated calculation execution",
                }
            ],
            "editor": "api-teacher",
            "notes": "api correction preview",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "chapter_correction_dry_run"
    assert payload["dry_run_only"] is True
    assert payload["formal_publish_allowed"] is False
    assert payload["correction_record"]["status"] == "accepted"
    assert payload["after"]["question_package"]["quality_report"]["passed"] is True


def _candidate_from_materials() -> dict:
    generated = build_intelligent_chapter_draft(
        source_text=None,
        chapter_id="correction_pkg",
        title="Correction Package",
        materials=[
            {
                "material_type": "markdown",
                "filename": "multi_variable.md",
                "text": "\n".join(
                    [
                        "# Multi-variable differential chapter",
                        "core concepts: partial derivative;",
                        "formula: dz=f_x dx+f_y dy;",
                        "theorem: differentiability implies continuity;",
                        "typical problems: composite function differential;",
                        "trigger: z=f(u,v), u=x+y, v=xy;",
                        "method: chain rule;",
                        "transformation: draw dependency chain before differentiating;",
                        "confusion: treating partial derivative existence as differentiability;",
                        "common errors: writing only the final answer, false pass;",
                        "prerequisite: one-variable derivative rules;",
                        "downstream: total differential and tangent plane;",
                        "math1 value: high;",
                    ]
                ),
            }
        ],
        build_candidate=True,
    )
    candidate_preview = generated["candidate_preview"]
    assert candidate_preview["candidate_build_allowed"] is True
    assert candidate_preview["candidate_quality"]["grade"] == "pass"
    candidate = candidate_preview["candidate"]
    assert candidate["material_evidence"]["core_formulas"] == ["dz=f_x dx+f_y dy"]
    return candidate
