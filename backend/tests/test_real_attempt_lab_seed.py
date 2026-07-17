from __future__ import annotations

from pathlib import Path

import yaml

from app.challenge.repository import ChallengeRepository
from app.core.enums import ErrorType


REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = REPO_ROOT / "backend" / "challenge_data" / "ode_network_mvp" / "real_attempt_lab_seed.yaml"


def test_real_attempt_lab_seed_references_known_ode_nodes_and_errors() -> None:
    with SEED_PATH.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}

    assert data["chapter_id"] == "ode_network_mvp"
    cases = data["cases"]
    assert len(cases) >= 8

    graph = ChallengeRepository().load_graph(data["chapter_id"])
    micro_ids = {micro.id for micro in graph.micro_nodes}
    error_values = {error.value for error in ErrorType}
    case_ids = [case["case_id"] for case in cases]

    assert len(case_ids) == len(set(case_ids))
    for case in cases:
        assert case["node_id"] in micro_ids
        assert case["expected_repair_target"] in micro_ids
        assert case["expected_primary_error"] in error_values
        assert case["learner_answer"].strip()
        assert case["learner_self_explanation"].strip()
        assert case["human_coaching_note"].strip()
