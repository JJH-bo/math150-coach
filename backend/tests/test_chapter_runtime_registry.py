from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.challenge.atlas import ChallengeAtlasBuilder
from app.challenge.chapter_publish_executor import APPROVAL_PHRASE, execute_chapter_controlled_publish
from app.challenge.chapter_publish_plan import build_chapter_publish_plan_dry_run
from app.challenge.chapter_registry import ChapterRuntimeRegistry, ChapterRuntimeRegistryError
from app.challenge.engine import ChallengeEngine
from app.challenge.repository import ChallengeRepository
from app.main import create_app
from app.training.session_log import ensure_no_trusted_fields


REQUIRED_REVIEW_CHECKS = {
    "math_scope_checked",
    "macro_micro_structure_checked",
    "repair_targets_checked",
    "hidden_abilities_checked",
    "semantic_edges_checked",
    "boss_coverage_checked",
    "learner_surface_safe",
}

MARKDOWN = """# Runtime Registry Demo
chapter_id: runtime_registry_demo
title: Runtime Registry Demo

## MacroNodes
| id | title | knowledge_node_id |
| --- | --- | --- |
| runtime_registry_demo.macro | Main | runtime_registry_demo.macro |

## MicroNodes
| id | macro_node_id | type | title | description |
| --- | --- | --- | --- | --- |
| runtime_registry_demo.concept | runtime_registry_demo.macro | concept | Concept | Structure check |
| runtime_registry_demo.method | runtime_registry_demo.macro | method | Method | Method choice |

## MacroChallenges
| id | macro_node_id | title | covers_micro_nodes |
| --- | --- | --- | --- |
| runtime_registry_demo.boss | runtime_registry_demo.macro | Boss | runtime_registry_demo.concept, runtime_registry_demo.method |

## HiddenAbilities
| id | owner_node_id | title | dimensions | why_exists | evidence_sources | failure_modes | repair_target_node_id |
| --- | --- | --- | --- | --- | --- | --- | --- |
| runtime_registry_demo.hidden.concept | runtime_registry_demo.concept | Concept reason | concept | Prevent keyword-only answers | rubric,self_explanation | keyword only | runtime_registry_demo.concept |
| runtime_registry_demo.hidden.method | runtime_registry_demo.method | Method reason | method | Prevent method guessing | rubric,self_explanation | unclear entry | runtime_registry_demo.method |

## TransferNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| runtime_registry_demo.transfer.variant | Transfer | runtime_registry_demo.method | runtime_registry_demo.method | Variant transfer |

## SynthesisNodes
| id | title | owner_node_id | repair_target_node_id | why_exists |
| --- | --- | --- | --- | --- |
| runtime_registry_demo.synthesis.boss | Synthesis | runtime_registry_demo.boss | runtime_registry_demo.method | Boss decomposition |

## Edges
| id | edge_type | source_id | target_id | reason |
| --- | --- | --- | --- | --- |
| e1 | supports | runtime_registry_demo.hidden.concept | runtime_registry_demo.concept | Hidden supports concept |
| e2 | supports | runtime_registry_demo.hidden.method | runtime_registry_demo.method | Hidden supports method |
| e3 | transfers_to | runtime_registry_demo.transfer.variant | runtime_registry_demo.method | Transfer to method |
| e4 | boss_checks | runtime_registry_demo.synthesis.boss | runtime_registry_demo.boss | Boss checks synthesis |
| e5 | requires | runtime_registry_demo.concept | runtime_registry_demo.method | Concept before method |

## ErrorRepairMap
| root_cause | repair_target_node_id |
| --- | --- |
| concept_gap | runtime_registry_demo.concept |
| trigger_failure | runtime_registry_demo.concept |
| method_error | runtime_registry_demo.method |
| transformation_error | runtime_registry_demo.method |
| calculation_error | runtime_registry_demo.method |
| expression_weakness | runtime_registry_demo.method |
"""


def test_runtime_registry_marks_publish_missing_questions_as_pending(tmp_path: Path) -> None:
    _controlled_publish(tmp_path)
    (tmp_path / "backend" / "challenge_data" / "runtime_registry_demo" / "questions.yaml").unlink()

    repository = ChallengeRepository(tmp_path / "backend" / "challenge_data")
    registry = ChapterRuntimeRegistry(repository).build()
    entry = _chapter_entry(registry, "runtime_registry_demo")

    assert entry["runtime_status"] == "content_pending"
    assert entry["can_start"] is False
    assert entry["source"] == "controlled_publish"
    assert "questions_yaml_missing" in entry["blocking_reasons"]

    atlas = ChallengeAtlasBuilder(repository).build()
    region = _region(atlas, "runtime_registry_demo")
    assert region["runtime"]["can_start"] is False
    assert region["detail"]["start_endpoint"] is None

    with pytest.raises(ChapterRuntimeRegistryError):
        ChallengeEngine(repository=repository).start("runtime_registry_demo", session_id="blocked-session")


def test_runtime_registry_allows_start_after_controlled_publish_generates_questions(tmp_path: Path) -> None:
    _controlled_publish(tmp_path)

    repository = ChallengeRepository(tmp_path / "backend" / "challenge_data")
    registry = ChapterRuntimeRegistry(repository).build()
    entry = _chapter_entry(registry, "runtime_registry_demo")

    assert entry["runtime_status"] == "trainable"
    assert entry["can_start"] is True
    assert entry["blocking_reasons"] == []

    payload = ChallengeEngine(repository=repository).start(
        "runtime_registry_demo",
        session_id="runtime-registry-start",
        session_root=tmp_path / "sessions",
    )

    assert payload["challenge"]["chapter_id"] == "runtime_registry_demo"
    assert payload["challenge"]["current_question"]["question_id"].startswith("runtime_registry_demo.")


def test_runtime_registry_blocks_non_pass_publish_manifest_even_with_questions(tmp_path: Path) -> None:
    _controlled_publish(tmp_path)
    manifest_path = tmp_path / "backend" / "challenge_data" / "runtime_registry_demo" / "publish_manifest.json"
    manifest_path.write_text('{"candidate_quality_grade":"warn"}\n', encoding="utf-8")

    repository = ChallengeRepository(tmp_path / "backend" / "challenge_data")
    entry = _chapter_entry(ChapterRuntimeRegistry(repository).build(), "runtime_registry_demo")

    assert entry["runtime_status"] == "content_pending"
    assert entry["can_start"] is False
    assert "publish_manifest_quality_not_pass" in entry["blocking_reasons"]


def test_runtime_registry_api_is_read_only_and_learner_safe() -> None:
    client = TestClient(create_app("mixed"))

    response = client.get("/api/challenge/v1/chapters/registry")

    assert response.status_code == 200
    payload = response.json()
    assert payload["registry_version"] == "chapter_runtime_registry_v1"
    assert any(chapter["chapter_id"] == "ode_network_mvp" and chapter["can_start"] for chapter in payload["chapters"])
    ensure_no_trusted_fields(payload)


def _controlled_publish(root: Path) -> None:
    payload = execute_chapter_controlled_publish(
        MARKDOWN,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist={code: True for code in REQUIRED_REVIEW_CHECKS},
        notes="ready",
        target_root=root,
        allow_write=True,
        approval_phrase=APPROVAL_PHRASE,
        expected_publish_plan_hash=_plan_hash(),
    )
    assert payload["status"] == "published"


def _plan_hash() -> str:
    plan = build_chapter_publish_plan_dry_run(
        MARKDOWN,
        reviewer="reviewer-a",
        decision="approve_for_candidate",
        checklist={code: True for code in REQUIRED_REVIEW_CHECKS},
        notes="ready",
    )
    assert plan["publish_plan_grade"] == "ready"
    return plan["publish_plan_hash"]


def _chapter_entry(registry: dict, chapter_id: str) -> dict:
    return next(chapter for chapter in registry["chapters"] if chapter["chapter_id"] == chapter_id)


def _region(atlas: dict, chapter_id: str) -> dict:
    return next(region for region in atlas["regions"] if region["id"] == chapter_id)
