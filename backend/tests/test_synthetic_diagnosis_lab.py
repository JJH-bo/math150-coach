from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LAB_PATH = PROJECT_ROOT / "evals" / "run_synthetic_diagnosis_lab.py"
CASE_PATH = PROJECT_ROOT / "evals" / "synthetic_cases" / "ode_diagnosis_synthetic_cases.yaml"
FORMAL_MANIFEST_PATH = PROJECT_ROOT / "backend" / "catalog_data" / "manifest.yaml"


def load_lab_module():
    spec = importlib.util.spec_from_file_location("run_synthetic_diagnosis_lab", LAB_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_synthetic_lab_case_file_is_separate_from_golden_evals() -> None:
    assert CASE_PATH.exists()
    assert CASE_PATH.parent.name == "synthetic_cases"
    assert CASE_PATH.parent != PROJECT_ROOT / "evals" / "golden_cases"


def test_synthetic_lab_cases_are_structured_and_cover_diagnosis_edges() -> None:
    lab = load_lab_module()
    cases = lab.load_cases()
    structure_errors = lab.validate_cases(cases)
    categories = {case["category"] for case in cases}
    paths = Counter(case["scoring_path"] for case in cases)

    assert not structure_errors
    assert len(cases) >= 12
    assert paths["manual_override"] >= 1
    assert sum(count for path, count in paths.items() if path != "manual_override") >= 5
    assert {
        "process_right_calculation_wrong",
        "false_pass",
        "partial_concept",
        "transformation_root",
        "condition_miss",
        "missing_constant",
        "knowledge_confusion",
        "rule_only_weak_signal",
        "evidence_conflict",
        "hidden_logic_contradiction",
    }.issubset(categories)


def test_synthetic_lab_runner_passes_all_cases() -> None:
    lab = load_lab_module()

    assert lab.main() == 0


def test_synthetic_lab_does_not_write_formal_catalog_manifest() -> None:
    lab = load_lab_module()
    before = FORMAL_MANIFEST_PATH.read_text(encoding="utf-8")

    assert lab.main() == 0

    after = FORMAL_MANIFEST_PATH.read_text(encoding="utf-8")
    assert after == before
