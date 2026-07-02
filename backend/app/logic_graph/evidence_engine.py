from __future__ import annotations

from app.core.enums import ErrorType, PassState, ScoreDimension
from app.core.schemas import Attempt, CompositeScoreResult, DiagnosisResult, Question
from app.logic_graph.models import (
    AbilityEvidence,
    AbilityEvidenceStatus,
    LogicAbilitySpec,
    LogicDiagnosisInsight,
    LogicEdgeType,
    LogicGraph,
)
from app.logic_graph.repository import LogicGraphRepository


FRIENDLY_SIGNAL_BY_SCORER = {
    "RubricScorer": "grading_rule",
    "MathValidatorScorer": "math_validator",
    "RuleScorer": "weak_rule_signal",
    "ManualOverrideScorer": "imported_manual_score",
}


class LogicEvidenceEngine:
    """Maps scoring/diagnosis evidence onto hidden abilities.

    This service is advisory only. It does not decide pass state, rollback, or
    forward movement; those remain owned by the existing engines.
    """

    def __init__(self, repository: LogicGraphRepository | None = None) -> None:
        self.repository = repository or LogicGraphRepository()

    def analyze(
        self,
        question: Question,
        attempt: Attempt,
        composite_result: CompositeScoreResult,
        diagnosis_result: DiagnosisResult,
    ) -> LogicDiagnosisInsight:
        chapter_id = str(question.metadata.get("challenge_chapter_id") or question.metadata.get("logic_chapter_id") or "")
        graph = self.repository.try_load_graph(chapter_id)
        if graph is None:
            return LogicDiagnosisInsight(active=False, learner_message="No hidden logic graph is available for this task.")

        abilities = self._candidate_abilities(graph, question, diagnosis_result.root_cause)
        if not abilities:
            return LogicDiagnosisInsight(
                active=False,
                chapter_id=graph.chapter_id,
                learner_message="No hidden ability target is configured for this task.",
            )

        evidence = [
            self._evaluate_ability(graph, ability, attempt, composite_result, diagnosis_result)
            for ability in abilities
        ]
        primary = self._select_primary_ability(evidence, graph, diagnosis_result.root_cause)
        chain = self._ability_chain_summary(evidence, primary, diagnosis_result.root_cause)
        return LogicDiagnosisInsight(
            active=True,
            chapter_id=graph.chapter_id,
            primary_ability_id=primary.ability_id if primary else None,
            primary_target_node_id=primary.target_node_id if primary else None,
            ability_evidence=evidence,
            ability_chain_summary=chain,
            repair_cues=list(primary.repair_cues[:3]) if primary else [],
            confidence=primary.confidence if primary else 0,
            learner_message=self._learner_message(primary, diagnosis_result.pass_state, diagnosis_result.root_cause),
        )

    def _candidate_abilities(
        self,
        graph: LogicGraph,
        question: Question,
        root_cause: ErrorType | None,
    ) -> list[LogicAbilitySpec]:
        by_id: dict[str, LogicAbilitySpec] = {}
        for ability in graph.abilities_for_node(question.node_id):
            by_id[ability.id] = ability
        for ability in graph.abilities_for_error(root_cause):
            by_id[ability.id] = ability
        for dimension in question.tested_dimensions:
            for ability in graph.abilities:
                if ability.owner_node_id == question.node_id and dimension in ability.dimensions:
                    by_id[ability.id] = ability
        for ability in list(by_id.values()):
            for connected in self._connected_context_abilities(graph, ability):
                by_id.setdefault(connected.id, connected)
        return list(by_id.values())

    def _evaluate_ability(
        self,
        graph: LogicGraph,
        ability: LogicAbilitySpec,
        attempt: Attempt,
        composite_result: CompositeScoreResult,
        diagnosis_result: DiagnosisResult,
    ) -> AbilityEvidence:
        scores = [
            composite_result.score_vector.get_dimension(dimension).score
            for dimension in ability.dimensions
            if composite_result.score_vector.get_dimension(dimension) is not None
            and composite_result.score_vector.get_dimension(dimension).score is not None
        ]
        signals = self._signals_for_ability(ability, composite_result, diagnosis_result)
        response_signals = self._response_signals_for_ability(ability, attempt)
        signals = _dedupe([*signals, *response_signals])
        positive_count = sum(signal.startswith("response_positive:") for signal in signals)
        weak_count = sum(signal.startswith("response_weak:") for signal in signals)

        status = AbilityEvidenceStatus.UNKNOWN
        confidence = 0.35
        if any(signal.startswith("response_contradiction:") for signal in signals):
            status = AbilityEvidenceStatus.CONTRADICTED
            confidence = min(0.92, 0.78 + ability.diagnostic_weight * 0.12)
        elif self._root_targets_ability(ability, diagnosis_result.root_cause, composite_result):
            status = AbilityEvidenceStatus.MISSING
            confidence = min(0.92, 0.76 + ability.diagnostic_weight * 0.12)
        elif any("required_missed" in signal for signal in signals):
            status = AbilityEvidenceStatus.MISSING
            confidence = min(0.88, 0.68 + ability.diagnostic_weight * 0.12)
        elif any("validator_missed" in signal for signal in signals):
            status = AbilityEvidenceStatus.MISSING
            confidence = 0.82
        elif positive_count >= ability.minimum_positive_cues:
            status = AbilityEvidenceStatus.DEMONSTRATED
            confidence = min(0.78, 0.56 + positive_count * 0.08 + ability.diagnostic_weight * 0.06)
        elif weak_count:
            status = AbilityEvidenceStatus.WEAK
            confidence = min(0.58, 0.42 + weak_count * 0.06)
        elif scores:
            lowest = min(scores)
            if lowest < 55:
                status = AbilityEvidenceStatus.MISSING
                confidence = 0.75
            elif lowest < 75:
                status = AbilityEvidenceStatus.WEAK
                confidence = 0.62
            elif min(scores) >= 85:
                status = AbilityEvidenceStatus.DEMONSTRATED
                confidence = 0.72
            else:
                status = AbilityEvidenceStatus.WEAK
                confidence = 0.55

        if diagnosis_result.pass_state == PassState.PASS and status == AbilityEvidenceStatus.UNKNOWN:
            status = AbilityEvidenceStatus.DEMONSTRATED
            confidence = 0.52

        return AbilityEvidence(
            ability_id=ability.id,
            title=ability.title,
            kind=ability.kind,
            role=ability.role,
            status=status,
            confidence=confidence,
            dimensions=list(ability.dimensions),
            signals=signals,
            source_labels=list(ability.evidence_sources),
            failure_modes=list(ability.failure_modes),
            repair_cues=list(ability.repair_cues),
            target_node_id=ability.repair_target_node_id,
            upstream_ability_ids=self._upstream_ability_ids(graph, ability.id),
            downstream_ability_ids=self._downstream_ability_ids(graph, ability),
            contradiction_peer_ids=list(ability.confusion_peer_ids),
        )

    def _signals_for_ability(
        self,
        ability: LogicAbilitySpec,
        composite_result: CompositeScoreResult,
        diagnosis_result: DiagnosisResult,
    ) -> list[str]:
        signals: list[str] = []
        for scorer_result in composite_result.scorer_results:
            if not scorer_result.is_active:
                continue
            source = FRIENDLY_SIGNAL_BY_SCORER.get(scorer_result.scorer_name, "scoring_signal")
            for evidence in scorer_result.evidence:
                if evidence.dimension not in ability.dimensions:
                    continue
                if evidence.matched_items:
                    signals.append(f"{source}:matched")
                for missed in evidence.required_missed:
                    signals.append(f"{source}:required_missed:{missed}")
                for missed in evidence.optional_missed:
                    signals.append(f"{source}:optional_missed:{missed}")
                for missed in evidence.missed_items:
                    signals.append(f"{source}:validator_missed:{missed}")
        for error in diagnosis_result.error_vector.errors:
            if any(dimension in ability.dimensions for dimension in error.related_dimensions):
                signals.append(f"diagnosis:{error.error_type.value}")
        return _dedupe(signals)

    def _response_signals_for_ability(
        self,
        ability: LogicAbilitySpec,
        attempt: Attempt,
    ) -> list[str]:
        text = " ".join(
            [
                attempt.user_answer or "",
                " ".join(str(step) for step in attempt.response_steps),
                attempt.self_explanation or "",
            ]
        ).lower()
        signals: list[str] = []
        for cue in ability.positive_cues:
            if _cue_in_text(cue, text):
                signals.append(f"response_positive:{cue}")
        for cue in ability.weak_cues:
            if _cue_in_text(cue, text):
                signals.append(f"response_weak:{cue}")
        for cue in ability.contradiction_cues:
            if _cue_in_text(cue, text):
                signals.append(f"response_contradiction:{cue}")
        return signals

    def _root_targets_ability(
        self,
        ability: LogicAbilitySpec,
        root_cause: ErrorType | None,
        composite_result: CompositeScoreResult,
    ) -> bool:
        if root_cause is None:
            return False
        root_dimensions = {
            ErrorType.CONCEPT_GAP: {ScoreDimension.CONCEPT},
            ErrorType.TRIGGER_FAILURE: {ScoreDimension.TRIGGER},
            ErrorType.METHOD_ERROR: {ScoreDimension.METHOD},
            ErrorType.TRANSFORMATION_ERROR: {ScoreDimension.TRANSFORMATION},
            ErrorType.CALCULATION_ERROR: {ScoreDimension.CALCULATION, ScoreDimension.FINAL_ANSWER},
            ErrorType.CONDITION_MISS: {ScoreDimension.FINAL_ANSWER, ScoreDimension.PROCESS},
            ErrorType.EXPRESSION_WEAKNESS: {ScoreDimension.EXPRESSION},
            ErrorType.KNOWLEDGE_CONFUSION: {ScoreDimension.CONCEPT, ScoreDimension.TRIGGER, ScoreDimension.METHOD},
            ErrorType.SYNTHESIS_FAILURE: {ScoreDimension.TRIGGER, ScoreDimension.METHOD, ScoreDimension.PROCESS},
        }.get(root_cause, set())
        if not root_dimensions.intersection(ability.dimensions):
            return False
        for dimension in ability.dimensions:
            dimension_score = composite_result.score_vector.get_dimension(dimension)
            if dimension_score is not None and dimension_score.score is not None and dimension_score.score >= 80:
                return False
        return True

    def _select_primary_ability(
        self,
        evidence: list[AbilityEvidence],
        graph: LogicGraph,
        root_cause: ErrorType | None,
    ) -> AbilityEvidence | None:
        if not evidence:
            return None
        root_ability_ids = {ability.id for ability in graph.abilities_for_error(root_cause)}
        for item in sorted(evidence, key=self._ability_sort_key, reverse=True):
            if item.ability_id in root_ability_ids and item.status in {
                AbilityEvidenceStatus.MISSING,
                AbilityEvidenceStatus.WEAK,
                AbilityEvidenceStatus.CONTRADICTED,
            }:
                return item
        actionable = [
            item for item in evidence
            if item.status in {AbilityEvidenceStatus.MISSING, AbilityEvidenceStatus.WEAK, AbilityEvidenceStatus.CONTRADICTED}
        ]
        if actionable:
            return sorted(actionable, key=self._ability_sort_key, reverse=True)[0]
        return sorted(evidence, key=lambda item: item.confidence, reverse=True)[0]

    def _connected_context_abilities(
        self,
        graph: LogicGraph,
        ability: LogicAbilitySpec,
    ) -> list[LogicAbilitySpec]:
        connected_ids: list[str] = []
        for edge in graph.edges:
            if edge.edge_type not in {
                LogicEdgeType.REQUIRES,
                LogicEdgeType.SUPPORTS,
                LogicEdgeType.CHECKS,
                LogicEdgeType.CONTRASTS_WITH,
                LogicEdgeType.DERIVES_TO,
                LogicEdgeType.COMMONLY_CONFUSED_WITH,
                LogicEdgeType.BLOCKS,
                LogicEdgeType.REPAIRS,
                LogicEdgeType.BOSS_CHECKS,
                LogicEdgeType.TRANSFERS_TO,
            }:
                continue
            if edge.source_id == ability.id:
                connected_ids.append(edge.target_id)
            if edge.target_id == ability.id and edge.edge_type in {
                LogicEdgeType.REQUIRES,
                LogicEdgeType.SUPPORTS,
                LogicEdgeType.DERIVES_TO,
                LogicEdgeType.BLOCKS,
                LogicEdgeType.COMMONLY_CONFUSED_WITH,
                LogicEdgeType.REPAIRS,
                LogicEdgeType.BOSS_CHECKS,
            }:
                connected_ids.append(edge.source_id)
        connected: list[LogicAbilitySpec] = []
        for ability_id in _dedupe(connected_ids):
            item = graph.ability_by_id(ability_id)
            if item is not None:
                connected.append(item)
        return connected

    def _upstream_ability_ids(self, graph: LogicGraph, ability_id: str) -> list[str]:
        upstream: list[str] = []
        for edge in graph.edges:
            if edge.target_id != ability_id:
                continue
            if edge.edge_type in {
                LogicEdgeType.REQUIRES,
                LogicEdgeType.SUPPORTS,
                LogicEdgeType.DERIVES_TO,
                LogicEdgeType.BLOCKS,
                LogicEdgeType.BOSS_CHECKS,
            }:
                upstream.append(edge.source_id)
        return _dedupe(upstream)

    def _downstream_ability_ids(self, graph: LogicGraph, ability: LogicAbilitySpec) -> list[str]:
        downstream = list(ability.downstream_ability_ids)
        for edge in graph.edges:
            if edge.source_id == ability.id and edge.edge_type in {
                LogicEdgeType.REQUIRES,
                LogicEdgeType.SUPPORTS,
                LogicEdgeType.DERIVES_TO,
                LogicEdgeType.TRANSFORMS_TO,
                LogicEdgeType.TRANSFERS_TO,
                LogicEdgeType.BLOCKS,
                LogicEdgeType.REPAIRS,
                LogicEdgeType.BOSS_CHECKS,
            }:
                downstream.append(edge.target_id)
        return _dedupe(downstream)

    def _ability_sort_key(self, item: AbilityEvidence) -> tuple[int, float]:
        status_priority = {
            AbilityEvidenceStatus.CONTRADICTED: 4,
            AbilityEvidenceStatus.MISSING: 3,
            AbilityEvidenceStatus.WEAK: 2,
            AbilityEvidenceStatus.UNKNOWN: 1,
            AbilityEvidenceStatus.DEMONSTRATED: 0,
        }[item.status]
        return status_priority, item.confidence

    def _ability_chain_summary(
        self,
        evidence: list[AbilityEvidence],
        primary: AbilityEvidence | None,
        root_cause: ErrorType | None,
    ) -> list[str]:
        if primary is None:
            return ["hidden ability graph found no actionable focus"]
        chain = [
            f"root_cause:{root_cause.value if root_cause else 'none'}",
            f"primary_ability:{primary.ability_id}",
            f"repair_target:{primary.target_node_id}",
        ]
        weak = [item.ability_id for item in evidence if item.status in {AbilityEvidenceStatus.MISSING, AbilityEvidenceStatus.WEAK}]
        if weak:
            chain.append(f"weak_or_missing:{','.join(weak[:4])}")
        return chain

    def _learner_message(
        self,
        primary: AbilityEvidence | None,
        pass_state: PassState,
        root_cause: ErrorType | None,
    ) -> str:
        if primary is None:
            return "这次作答还没有定位到明确的隐藏能力焦点，先补充题眼、方法依据和关键步骤。"
        if primary.status == AbilityEvidenceStatus.CONTRADICTED:
            return (
                f"这次最值得注意的是矛盾证据：你写到了「{primary.title}」相关内容，"
                f"但作答信号和它的要求冲突。先回到 {primary.target_node_id}，把判断依据重新说清。"
            )
        if pass_state == PassState.PASS:
            return f"当前关卡可以点亮；隐藏能力层面最稳定的证据来自「{primary.title}」，后续用变式题确认它能迁移。"
        root_text = root_cause.value if root_cause else "证据不足"
        return (
            f"这次不只是看对错：系统把根因 {root_text} 落到隐藏能力「{primary.title}」。"
            f"先修复它对应的训练点 {primary.target_node_id}，不要一次拉起太多节点。"
        )


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _cue_in_text(cue: str, text: str) -> bool:
    normalized = cue.strip().lower()
    if not normalized:
        return False
    return normalized in text
