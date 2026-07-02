from __future__ import annotations

from app.services.composite_scoring_engine import CompositeScoringEngine
from app.services.legacy_scenario_scorer import LegacyScenarioScorer
from app.services.manual_override_scorer import ManualOverrideScorer
from app.services.math_validator_scorer import MathValidatorScorer
from app.services.rubric_scorer import RubricScorer
from app.services.rule_scorer import RuleScorer


class ScoringEngine(LegacyScenarioScorer):
    """Deprecated deterministic adapter kept for Phase 0.x test compatibility.

    Production-like Phase 1 scoring should use CompositeScoringEngine. This
    compatibility class may read scenario/default scores and is intentionally
    excluded from CompositeScoringEngine's default scorer list.
    """


__all__ = [
    "CompositeScoringEngine",
    "LegacyScenarioScorer",
    "ManualOverrideScorer",
    "MathValidatorScorer",
    "RubricScorer",
    "RuleScorer",
    "ScoringEngine",
]
