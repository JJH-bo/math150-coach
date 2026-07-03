from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.challenge.chapter_publish_executor import APPROVAL_PHRASE, execute_chapter_controlled_publish
from app.challenge.chapter_publish_plan import build_chapter_publish_plan_dry_run
from app.main import create_app

REQUIRED_REVIEW_CHECKS = {
    "math_scope_checked",
    "macro_micro_structure_checked",
    "repair_targets_checked",
    "hidden_abilities_checked",
    "semantic_edges_checked",
    "boss_coverage_checked",
    "learner_surface_safe",
}

MARKDOWN = """# Controlled Demo
chapter_id: controlled_demo
title: Controlled Demo

## MacroNodes
| id | title | knowledge_node_id |
| --- | --- | --- |
| controlled_demo.macro | Main | controlled_demo.macro |

## MicroNodes
| id | macro_node_id | type | title | description |
| --- | --- | --- | --- | --- |
| controlled_demo.concept | controlled_demo.macro | concept | Concept | Structure check |
| controlled_demo.method | controlled_demo.macro | method | Method | Method choice |

## MacroChallenges
| id | macro_node_id | title | covers_micro_nodes |
| --- | --- | --- | --- |
| controlled_demo.boss | controlled_demo.macro | Boss | controlled_demo.concept, controlled_demo.method |

## HiddenAbilities
| id | owner_node_id | title | dimensions | why_exists | evidence_sources | failure_modes | repair_target_node_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| controlled_demo.hidden.concept | controlled_demo.concept | Concept reason | concept | Prevent keyword-only answers | rubric,self_explanation | keyword only | controlled_demo.concept |
| controlled_demo.hidden.method | controlled_demo.method | Method reason | method | Prevent method guessing | rubric,self_explanation | unclear entry | controlled_demo.method |

## TransferNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| controlled_demo.transfer.variant | Transfer | controlled_demo.method | controlled_demo.method | Variant transfer |

## SynthesisNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| controlled_demo.synthesis.boss | Synthesis | controlled_demo.boss | controlled_demo.method | Boss decomposition |

## Edges
| id | edge_type | source_id | target_id | reason |
| --- | --- | --- | --- | --- |
| e1 | supports | controlled_demo.hidden.concept | controlled_demo.concept | Hidden supports concept |
| e2 | supports | controlled_demo.hidden.method | controlled_demo.method | Hidden supports method |
| e3 | transfers_to | controlled_demo.transfer.variant | controlled_demo.method | Transfer to method |
| e4 | boss_checks | controlled_demo.synthesis.boss | controlled_demo.boss | Boss checks synthesis |
| e5 | requires | controlled_demo.concept | controlled_demo.method | Concept before method |

## ErrorRepairMap
| root_cause | repair_target_node_id |
| --- | --- |
| concept_gap | controlled_demo.concept |
| trigger_failure | controlled_demo.concept |
| method_error | controlled_demo.method |
| transformation_error | controlled_demo.method |
| calculation_error | controlled_demo.method |
| expression_weakness | controlled_demo.method |
"""


def _checklist() -> dict[str, bool]:
    return {code: True for code in REQUIRED_REVIEW_CHECKS}


def _plan_hash() -> str:
    plan = build_chapter_publish_plan_dry_run(
        MARKDOWN,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=_checklist(),
        notes="ready",
    )
    assert plan["publish_plan_grade"] == "ready"
    return plan["publish_plan_hash"]


def test_controlled_publish_dry_run_does_not_create_files(tmp_path: Path) -> None:
    payload = execute_chapter_controlled_publish(
        MARKDOWN,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=_checklist(),
        notes="ready",
        target_root=tmp_path,
    )

    assert payload["status"] == "dry_run_ready"
    assert payload["dry_run_only"] is True
    assert payload["formal_publish_executed"] is False
    assert payload["file_operations"]
    assert not (tmp_path / "backend" / "challenge_data" / "controlled_demo").exists()


def test_controlled_publish_blocks_write_without_phrase(tmp_path: Path) -> None:
    payload = execute_chapter_controlled_publish(
        MARKDOWN,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=_checklist(),
        notes="ready",
        target_root=tmp_path,
        allow_write=True,
        expected_publish_plan_hash=_plan_hash(),
    )

    assert payload["status"] == "blocked"
    assert "approval_phrase_missing_or_invalid" in payload["blocking_reasons"]
    assert payload["formal_publish_executed"] is False


def test_controlled_publish_creates_files_with_phrase_and_hash(tmp_path: Path) -> None:
    payload = execute_chapter_controlled_publish(
        MARKDOWN,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist=_checklist(),
        notes="ready",
        target_root=tmp_path,
        allow_write=True,
        approval_phrase=APPROVAL_PHRASE,
        expected_publish_plan_hash=_plan_hash(),
    )

    chapter_dir = tmp_path / "backend" / "challenge_data" / "controlled_demo"
    record_path = chapter_dir / "publish_execution_manifest.json"
    assert payload["status"] == "published"
    assert payload["formal_publish_executed"] is True
    assert (chapter_dir / "challenge_graph.yaml").exists()
    assert (chapter_dir / "logic_graph.yaml").exists()
    assert (chapter_dir / "publish_manifest.json").exists()
    assert record_path.exists()
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert record["status"] == "published"
    assert record["rollback_policy"] == "delete_created_files_on_mid_write_failure"
    assert record["execution_manifest_hash"].startswith("sha256:")
    operation_paths = {operation["path"] for operation in payload["file_operations"]}
    assert "backend/challenge_data/controlled_demo/publish_execution_manifest.json" in operation_paths


def test_controlled_publish_api_defaults_to_non_writing_dry_run() -> None:
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/authoring/chapter-draft/controlled-publish",
        json={
            "markdown": MARKDOWN,
            "reviewer": "reviewer-a",
            "decision": "approve_for_candidate",
            "checklist": _checklist(),
            "notes": "ready",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "dry_run_ready"
    assert payload["dry_run_only"] is True
    assert payload["formal_publish_executed"] is False


def test_controlled_publish_api_blocks_write_by_default() -> None:
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/authoring/chapter-draft/controlled-publish",
        json={
            "markdown": MARKDOWN,
            "reviewer": "reviewer-a",
            "decision": "approve_for_candidate",
            "checklist": _checklist(),
            "notes": "ready",
            "allow_write": True,
            "approval_phrase": APPROVAL_PHRASE,
            "expected_publish_plan_hash": _plan_hash(),
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error_code"] == "chapter_controlled_publish_write_disabled"
