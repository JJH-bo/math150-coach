from __future__ import annotations

import re

from app.core.config import DEFAULT_ENGINE_CONFIG, EngineConfig
from app.core.enums import ErrorType, ForwardLevel, PassState, RollbackLevel, ScoreDimension
from app.core.schemas import (
    Attempt,
    CompositeScoreResult,
    DiagnosisTrace,
    DiagnosisResult,
    ErrorChainItem,
    ErrorEvidence,
    ErrorItem,
    ErrorVector,
    KnowledgeNode,
    Question,
    RecommendedAction,
    ScoreVector,
)
from app.logic_graph.models import LogicAbilityKind, LogicEdgeType
from app.logic_graph.repository import LogicGraphRepository
from app.services.diagnosis_policy import DiagnosisPolicy


class DiagnosisEngine:
    def __init__(
        self,
        config: EngineConfig = DEFAULT_ENGINE_CONFIG,
        policy: DiagnosisPolicy | None = None,
        logic_graph_repository: LogicGraphRepository | None = None,
    ) -> None:
        self.config = config
        self.policy = policy or DiagnosisPolicy()
        self.logic_graph_repository = logic_graph_repository or LogicGraphRepository()

    def diagnose(
        self,
        score_vector: ScoreVector,
        question: Question,
        attempt: Attempt,
        node: KnowledgeNode,
    ) -> ErrorVector:
        errors: list[ErrorItem] = []

        for dimension, error_type in self.config.dimension_error_map.items():
            dimension_score = score_vector.get_dimension(dimension)
            if dimension_score is None or dimension_score.score is None:
                continue
            if dimension_score.score >= 70:
                continue
            errors.append(
                self._build_error(
                    error_type=error_type,
                    dimension=dimension,
                    score=dimension_score.score,
                    evidence=dimension_score.evidence or f"Low {dimension.value} score.",
                )
            )

        errors = self._merge_duplicate_errors(errors)
        errors = self._infer_contextual_errors(score_vector, question, attempt, node, errors)
        false_pass_signal = self._has_false_pass_signal(score_vector)
        errors = self._promote_false_pass_errors(score_vector, errors)
        errors = self._align_with_node_policy(errors, node, false_pass_signal=false_pass_signal)
        return ErrorVector(errors=sorted(errors, key=lambda error: error.weight, reverse=True))

    def classify_pass_state(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
        node: KnowledgeNode,
    ) -> PassState:
        if self._has_false_pass_signal(score_vector):
            return PassState.FALSE_PASS

        primary_errors = error_vector.primary_errors()
        if self._only_expression_primary(primary_errors) and score_vector.overall_score(node.scoring_weights):
            return PassState.PARTIAL_PASS
        if len(primary_errors) > node.pass_criteria.max_primary_errors:
            return PassState.FAIL

        overall = score_vector.overall_score(node.scoring_weights)
        if overall is None:
            return PassState.FAIL

        required_dimensions_met = self._required_dimensions_met(score_vector, node)
        if overall >= node.pass_criteria.min_overall and required_dimensions_met:
            return PassState.PASS

        if overall >= 70 and not primary_errors:
            return PassState.PARTIAL_PASS

        return PassState.FAIL

    def diagnose_detailed(
        self,
        composite_result: CompositeScoreResult,
        question: Question,
        attempt: Attempt,
        node: KnowledgeNode,
    ) -> DiagnosisResult:
        from app.services.forward_engine import ForwardEngine
        from app.services.rollback_engine import RollbackEngine

        score_vector = composite_result.score_vector
        trace, evidence_sources = self._trace_from_composite_result(composite_result)
        self._augment_trace_with_logic_graph(trace, question, attempt)
        base_errors = self.diagnose(score_vector, question, attempt, node).errors
        evidence_errors = self._augment_errors_from_evidence(base_errors, trace, score_vector, question, node)
        root_cause, policy_hit = self.policy.select_root_cause(evidence_errors, score_vector, trace, question, node)
        trace.policy_hits.append(policy_hit)
        error_vector, error_chain = self._apply_causal_roles(evidence_errors, root_cause, trace, score_vector)
        confidence = self.policy.confidence(root_cause, trace, len(evidence_sources))
        pass_state = self._classify_pass_state_detailed(score_vector, error_vector, node, trace)

        rollback_decision = RollbackEngine(self.config).decide_rollback(error_vector, node)
        forward_decision = ForwardEngine(self.config).decide_forward(score_vector, error_vector, node)
        recommended_actions = self._recommended_actions(root_cause, trace, node, pass_state)
        ability_state, ability_state_label, ability_state_explanation = self._ability_state(
            score_vector=score_vector,
            root_cause=root_cause,
            pass_state=pass_state,
            trace=trace,
        )
        learner_explanation = self._coach_explanation(
            root_cause=root_cause,
            pass_state=pass_state,
            trace=trace,
            recommended_actions=recommended_actions,
            forward_level=forward_decision.level,
        )
        explanation = self._debug_explanation(
            root_cause=root_cause,
            confidence=confidence,
            trace=trace,
            error_chain=error_chain,
            rollback_level=rollback_decision.level,
            forward_level=forward_decision.level,
        )

        return DiagnosisResult(
            score_vector=score_vector,
            error_vector=error_vector,
            pass_state=pass_state,
            rollback_nodes=rollback_decision.rollback_nodes,
            forward_nodes=forward_decision.forward_nodes,
            rollback_level=rollback_decision.level,
            forward_level=forward_decision.level,
            explanation=explanation,
            learner_explanation=learner_explanation,
            next_action_hint=self._next_action_from_recommendations(recommended_actions),
            root_cause=root_cause,
            primary_errors=[error.error_type for error in error_vector.primary_errors()],
            secondary_errors=[error.error_type for error in error_vector.secondary_errors()],
            derived_errors=self._derived_error_types(error_chain, root_cause),
            downstream_result_errors=self._role_error_types(error_chain, {"downstream_result", "derived_result"}, root_cause),
            weak_signal_errors=self._role_error_types(error_chain, {"weak_signal"}, root_cause),
            evidence_gap_errors=self._role_error_types(error_chain, {"evidence_gap"}, root_cause),
            error_chain=error_chain,
            confidence=confidence,
            evidence_sources=evidence_sources,
            recommended_actions=recommended_actions,
            diagnosis_trace=trace,
            ability_state=ability_state,
            ability_state_label=ability_state_label,
            ability_state_explanation=ability_state_explanation,
        )

    def build_result(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
        node: KnowledgeNode,
        rollback_nodes: list[str],
        forward_nodes: list[str],
        rollback_level: RollbackLevel,
        forward_level: ForwardLevel,
    ) -> DiagnosisResult:
        pass_state = self.classify_pass_state(score_vector, error_vector, node)
        explanation = self.explain(score_vector, error_vector, pass_state, rollback_nodes, forward_nodes)
        learner_explanation = self.learner_explain(error_vector, pass_state, rollback_nodes, forward_nodes)
        next_action_hint = self.next_action_hint(pass_state, rollback_nodes, forward_nodes)
        return DiagnosisResult(
            score_vector=score_vector,
            error_vector=error_vector,
            pass_state=pass_state,
            rollback_nodes=rollback_nodes,
            forward_nodes=forward_nodes,
            rollback_level=rollback_level,
            forward_level=forward_level,
            explanation=explanation,
            learner_explanation=learner_explanation,
            next_action_hint=next_action_hint,
        )

    def _trace_from_composite_result(
        self,
        composite_result: CompositeScoreResult,
    ) -> tuple[DiagnosisTrace, list[ErrorEvidence]]:
        active_scorers = composite_result.get_active_scorer_names()
        dimension_sources = composite_result.get_dimension_sources()
        trace = DiagnosisTrace(
            active_scorers=active_scorers,
            dimension_sources=dimension_sources,
            rule_only=active_scorers == ["RuleScorer"],
            notes=list(composite_result.merge_notes),
        )
        self._bundle_add(trace, "active_scorers", active_scorers)
        self._bundle_add(
            trace,
            "score_vector",
            [
                f"{dimension.value}:{dimension_score.score}"
                for dimension, dimension_score in composite_result.score_vector.as_dimension_map().items()
                if dimension_score is not None and dimension_score.score is not None
            ],
        )
        for dimension, sources in dimension_sources.items():
            self._bundle_add(trace, "dimension_sources", [f"{dimension.value}:{','.join(sources)}"])
        evidence_sources: list[ErrorEvidence] = []

        for scorer_result in composite_result.scorer_results:
            for scorer_evidence in scorer_result.evidence:
                tags: list[str] = []
                tags.extend(f"matched:{item}" for item in scorer_evidence.matched_items)
                tags.extend(f"missed:{item}" for item in scorer_evidence.missed_items)
                tags.extend(f"required_missed:{item}" for item in scorer_evidence.required_missed)
                tags.extend(f"optional_missed:{item}" for item in scorer_evidence.optional_missed)

                for item in scorer_evidence.required_missed:
                    trace.required_missed.append(f"{scorer_evidence.dimension.value}:{item}")
                for item in scorer_evidence.optional_missed:
                    trace.optional_missed.append(f"{scorer_evidence.dimension.value}:{item}")
                if scorer_result.scorer_name == "MathValidatorScorer":
                    trace.validator_flags.extend(scorer_evidence.missed_items)
                if scorer_result.scorer_name == "RuleScorer":
                    self._bundle_add(trace, "weak_rule_signal", [scorer_evidence.evidence])

                evidence_sources.append(
                    ErrorEvidence(
                        source_type="scorer",
                        source_name=scorer_result.scorer_name,
                        dimension=scorer_evidence.dimension,
                        rubric_item_id=(scorer_evidence.missed_items + scorer_evidence.matched_items or [None])[0],
                        evidence=scorer_evidence.evidence,
                        strength=(scorer_evidence.score or 0) / 100 if scorer_evidence.score is not None else 0,
                        confidence=scorer_evidence.confidence,
                        tags=tags,
                    )
                )

        trace.required_missed = self._dedupe_strings(trace.required_missed)
        trace.optional_missed = self._dedupe_strings(trace.optional_missed)
        trace.validator_flags = self._dedupe_strings(trace.validator_flags)
        self._bundle_add(trace, "rubric_required_missed", trace.required_missed)
        self._bundle_add(trace, "rubric_optional_missed", trace.optional_missed)
        self._bundle_add(trace, "math_validator_flags", trace.validator_flags)
        trace.optional_only = bool(trace.optional_missed) and not trace.required_missed and not trace.validator_flags
        if not active_scorers:
            trace.notes.append("No active scorer supplied diagnostic evidence.")
        return trace, evidence_sources

    def _augment_trace_with_logic_graph(
        self,
        trace: DiagnosisTrace,
        question: Question,
        attempt: Attempt,
    ) -> None:
        chapter_id = str(question.metadata.get("challenge_chapter_id") or question.metadata.get("logic_chapter_id") or "")
        logic_graph = self.logic_graph_repository.try_load_graph(chapter_id)
        if logic_graph is None:
            trace.notes.append("No logic graph was available for diagnosis evidence.")
            return

        text = self._attempt_text(attempt)
        if not text:
            return
        if attempt.response_steps:
            trace.response_evidence.append(f"response_steps:{len(attempt.response_steps)}")
        if attempt.self_explanation:
            trace.response_evidence.append("self_explanation:present")
        self._bundle_add(trace, "response_steps", [str(step) for step in attempt.response_steps])
        if attempt.self_explanation:
            self._bundle_add(trace, "self_explanation", [attempt.self_explanation])

        weak_hits = 0
        positive_hits = 0
        contradiction_hits = 0
        node_abilities = logic_graph.abilities_for_node(question.node_id)
        node_ability_ids = {ability.id for ability in node_abilities}
        for edge in logic_graph.edges:
            if edge.source_id in node_ability_ids or edge.target_id in node_ability_ids:
                trace.graph_edge_semantics.append(
                    f"{edge.edge_type.value}:{edge.source_id}->{edge.target_id}"
                )
        for ability in node_abilities:
            for cue in ability.positive_cues:
                if self._cue_in_text(cue, text):
                    positive_hits += 1
                    trace.logic_ability_signals.append(
                        self._logic_signal("positive", ability.kind, ability.id, cue)
                    )
            for cue in ability.weak_cues:
                if self._cue_in_text(cue, text):
                    weak_hits += 1
                    signal = self._logic_signal("weak", ability.kind, ability.id, cue)
                    trace.logic_ability_signals.append(signal)
                    trace.logic_weak_signals.append(signal)
            for cue in ability.contradiction_cues:
                if self._cue_in_text(cue, text):
                    contradiction_hits += 1
                    signal = self._logic_signal("contradiction", ability.kind, ability.id, cue)
                    trace.logic_ability_signals.append(signal)
                    trace.logic_contradictions.append(signal)

        trace.logic_ability_signals = self._dedupe_strings(trace.logic_ability_signals)
        trace.logic_weak_signals = self._dedupe_strings(trace.logic_weak_signals)
        trace.logic_contradictions = self._dedupe_strings(trace.logic_contradictions)
        trace.response_evidence = self._dedupe_strings(trace.response_evidence)
        trace.graph_edge_semantics = self._dedupe_strings(trace.graph_edge_semantics)
        self._bundle_add(trace, "hidden_ability_evidence", trace.logic_ability_signals)
        self._bundle_add(trace, "graph_edge_semantics", trace.graph_edge_semantics)
        if weak_hits and not positive_hits and not contradiction_hits and not trace.required_missed and not trace.validator_flags:
            trace.surface_keyword_only = True
            trace.evidence_gaps.append("surface_keyword_without_structural_evidence")

    def _augment_errors_from_evidence(
        self,
        base_errors: list[ErrorItem],
        trace: DiagnosisTrace,
        score_vector: ScoreVector,
        question: Question,
        node: KnowledgeNode,
    ) -> list[ErrorItem]:
        del question
        errors_by_type: dict[ErrorType, ErrorItem] = {error.error_type: error for error in base_errors}

        for entry in trace.required_missed:
            dimension = self._dimension_from_trace_entry(entry)
            if dimension is None:
                continue
            error_type = self.config.dimension_error_map.get(dimension)
            if error_type is None:
                continue
            self._upsert_error(
                errors_by_type,
                error_type=error_type,
                weight=0.85,
                related_dimensions=[dimension],
                evidence=f"Required rubric evidence was missed: {entry}.",
                suggested_rollback_level=self.config.default_rollback_level_by_error[error_type],
            )

        if self._required_condition_missed(trace):
            self._upsert_error(
                errors_by_type,
                error_type=ErrorType.CONDITION_MISS,
                weight=0.86,
                related_dimensions=[ScoreDimension.PROCESS, ScoreDimension.FINAL_ANSWER],
                evidence="Required rubric evidence indicates a missed problem condition or initial-value resolution.",
                suggested_rollback_level=self.config.default_rollback_level_by_error[ErrorType.CONDITION_MISS],
            )

        for entry in trace.optional_missed:
            dimension = self._dimension_from_trace_entry(entry)
            if dimension is None:
                continue
            error_type = self.config.dimension_error_map.get(dimension)
            if error_type is None or error_type in errors_by_type:
                continue
            self._upsert_error(
                errors_by_type,
                error_type=error_type,
                weight=0.25,
                related_dimensions=[dimension],
                evidence=f"Optional rubric evidence was missed: {entry}.",
                suggested_rollback_level=self.config.default_rollback_level_by_error[error_type],
            )

        if "constant_C" in trace.validator_flags:
            self._upsert_error(
                errors_by_type,
                error_type=ErrorType.CALCULATION_ERROR,
                weight=0.78,
                related_dimensions=[ScoreDimension.CALCULATION, ScoreDimension.FINAL_ANSWER],
                evidence="MathValidatorScorer found a missing arbitrary constant C; this is an answer/computation completeness issue.",
                suggested_rollback_level=self.config.default_rollback_level_by_error[ErrorType.CALCULATION_ERROR],
            )

        if "initial_value_resolution" in trace.validator_flags:
            self._upsert_error(
                errors_by_type,
                error_type=ErrorType.CONDITION_MISS,
                weight=0.9,
                related_dimensions=[ScoreDimension.PROCESS, ScoreDimension.FINAL_ANSWER],
                evidence="MathValidatorScorer found that the initial condition was not resolved into a special solution.",
                suggested_rollback_level=self.config.default_rollback_level_by_error[ErrorType.CONDITION_MISS],
            )

        for signal in trace.logic_contradictions:
            error_type = self._error_type_from_logic_signal(signal)
            if error_type is None:
                continue
            self._upsert_error(
                errors_by_type,
                error_type=error_type,
                weight=0.88 if error_type == ErrorType.KNOWLEDGE_CONFUSION else 0.82,
                related_dimensions=self._dimensions_for_logic_error(error_type),
                evidence=f"Hidden logic graph contradiction detected: {signal}.",
                suggested_rollback_level=self.config.default_rollback_level_by_error[error_type],
            )

        if trace.surface_keyword_only:
            self._upsert_error(
                errors_by_type,
                error_type=ErrorType.TRIGGER_FAILURE,
                weight=0.45,
                related_dimensions=[ScoreDimension.TRIGGER],
                evidence="Only weak surface keyword evidence was found; the trigger condition is not proven.",
                suggested_rollback_level=self.config.default_rollback_level_by_error[ErrorType.TRIGGER_FAILURE],
            )

        if self._knowledge_confusion_signal(score_vector, node):
            self._upsert_error(
                errors_by_type,
                error_type=ErrorType.KNOWLEDGE_CONFUSION,
                weight=0.92,
                related_dimensions=[ScoreDimension.CONCEPT, ScoreDimension.TRIGGER, ScoreDimension.METHOD],
                evidence="Node policy plus low concept/trigger/method evidence indicates confusion between nearby ODE nodes.",
                suggested_rollback_level=self.config.default_rollback_level_by_error[ErrorType.KNOWLEDGE_CONFUSION],
            )

        if self._synthesis_failure_signal(score_vector, node):
            self._upsert_error(
                errors_by_type,
                error_type=ErrorType.SYNTHESIS_FAILURE,
                weight=0.92,
                related_dimensions=[ScoreDimension.TRIGGER, ScoreDimension.METHOD, ScoreDimension.PROCESS],
                evidence="The answer does not break the compound task into a recognizable solving path.",
                suggested_rollback_level=self.config.default_rollback_level_by_error[ErrorType.SYNTHESIS_FAILURE],
            )

        return self._merge_duplicate_errors(list(errors_by_type.values()))

    def _required_condition_missed(self, trace: DiagnosisTrace) -> bool:
        return any(
            token in entry.lower()
            for entry in trace.required_missed
            for token in ("initial_condition", "initial", "ivp", "condition_check", "constant_resolution")
        )

    def _apply_causal_roles(
        self,
        errors: list[ErrorItem],
        root_cause: ErrorType | None,
        trace: DiagnosisTrace,
        score_vector: ScoreVector,
    ) -> tuple[ErrorVector, list[ErrorChainItem]]:
        adjusted_errors: list[ErrorItem] = []
        error_chain: list[ErrorChainItem] = []

        for error in sorted(errors, key=lambda item: item.weight, reverse=True):
            role = self._diagnostic_role_for_error(error, root_cause, trace)
            adjusted_weight = self._adjusted_weight_for_role(error, role, root_cause)
            adjusted_error = ErrorItem(
                error_type=error.error_type,
                weight=adjusted_weight,
                related_dimensions=error.related_dimensions,
                evidence=f"{error.evidence} Causal role: {role}.",
                suggested_rollback_level=error.suggested_rollback_level,
            )
            adjusted_errors.append(adjusted_error)
            error_chain.append(
                ErrorChainItem(
                    error_type=adjusted_error.error_type,
                    role=role,
                    weight=adjusted_error.weight,
                    related_dimensions=adjusted_error.related_dimensions,
                    evidence_refs=[adjusted_error.evidence],
                    derived_from=root_cause if role == "derived" else None,
                    reason=self._chain_reason(adjusted_error.error_type, role, root_cause, trace),
                    suggested_rollback_level=adjusted_error.suggested_rollback_level,
                )
            )

        if root_cause and self.policy.final_answer_is_downstream(root_cause):
            final_answer = score_vector.get_dimension(ScoreDimension.FINAL_ANSWER)
            if final_answer is not None and final_answer.score is not None and final_answer.score < 70:
                error_chain.append(
                    ErrorChainItem(
                        error_type=root_cause,
                        role="downstream_result",
                        weight=0.5,
                        related_dimensions=[ScoreDimension.FINAL_ANSWER],
                        evidence_refs=[final_answer.evidence or "Final answer score is low."],
                        derived_from=root_cause,
                        reason="The final answer score is a downstream result of the root cause, not an independent root error.",
                        suggested_rollback_level=self.config.default_rollback_level_by_error[root_cause],
                    )
                )
                error_chain.append(
                    ErrorChainItem(
                        error_type=root_cause,
                        role="derived_result",
                        weight=0.5,
                        related_dimensions=[ScoreDimension.FINAL_ANSWER],
                        evidence_refs=[final_answer.evidence or "Final answer score is low."],
                        derived_from=root_cause,
                        reason="The final answer score is treated as a downstream result of the root cause, not an independent root error.",
                        suggested_rollback_level=self.config.default_rollback_level_by_error[root_cause],
                    )
                )

        return ErrorVector(errors=sorted(adjusted_errors, key=lambda item: item.weight, reverse=True)), error_chain

    def _diagnostic_role_for_error(
        self,
        error: ErrorItem,
        root_cause: ErrorType | None,
        trace: DiagnosisTrace,
    ) -> str:
        if trace.rule_only or trace.surface_keyword_only:
            return "weak_signal"
        if trace.optional_only and error.weight < self.policy.primary_weight_threshold:
            return "weak_signal"
        if error.weight < self.policy.secondary_weight_threshold:
            return "weak_signal"
        if root_cause is None:
            return "evidence_gap" if trace.required_missed or trace.validator_flags else "secondary"
        return self.policy.role_for_error(error.error_type, root_cause)

    def _adjusted_weight_for_role(
        self,
        error: ErrorItem,
        role: str,
        root_cause: ErrorType | None,
    ) -> float:
        if role == "weak_signal":
            return min(error.weight, 0.3)
        if role == "evidence_gap":
            return min(error.weight, 0.65)
        return self.policy.adjusted_weight(error, role, root_cause)

    def _classify_pass_state_detailed(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
        node: KnowledgeNode,
        trace: DiagnosisTrace,
    ) -> PassState:
        if self._has_detailed_false_pass_signal(score_vector):
            return PassState.FALSE_PASS
        if trace.rule_only or not trace.active_scorers:
            return PassState.FAIL
        if self._partial_concept_understanding(score_vector, error_vector):
            return PassState.PARTIAL_PASS
        return self.classify_pass_state(score_vector, error_vector, node)

    def _recommended_actions(
        self,
        root_cause: ErrorType | None,
        trace: DiagnosisTrace,
        node: KnowledgeNode,
        pass_state: PassState,
    ) -> list[RecommendedAction]:
        if pass_state == PassState.PASS and not trace.rule_only and root_cause is None:
            return [
                RecommendedAction(
                    action_type="variant_training",
                    target_node_ids=[node.id],
                    training_mode="direct_successor_or_variant",
                    priority=3,
                    reason="Current-node evidence is stable; follow the forward decision and keep one same-node variant as a light check.",
                )
            ]

        action_type = self.policy.action_type_for(root_cause, trace)
        priority = 1 if action_type in {"need_more_evidence", "chapter_framework_review"} else 2
        reason = self._action_reason(action_type, root_cause)
        return [
            RecommendedAction(
                action_type=action_type,
                target_node_ids=[node.id],
                training_mode=action_type,
                priority=priority,
                reason=reason,
            )
        ]

    def _coach_explanation(
        self,
        root_cause: ErrorType | None,
        pass_state: PassState,
        trace: DiagnosisTrace,
        recommended_actions: list[RecommendedAction],
        forward_level: ForwardLevel,
    ) -> str:
        action_text = recommended_actions[0].reason if recommended_actions else "先补一题带完整过程的同节点诊断题。"
        progress_text = (
            "暂不允许推进，先把当前节点的证据补稳。"
            if forward_level in {ForwardLevel.P0_NONE, ForwardLevel.P1_PARTIAL}
            else "可以有限推进，但仍要保留当前节点的复盘任务。"
        )

        if trace.rule_only or root_cause is None:
            return (
                "根因判断：当前证据不足，还不能给出强根因。"
                "为什么不是另一个常见错因：现在主要只有表面关键词或零散证据，不能直接判成题眼、方法或计算问题。"
                f"是否允许推进：{progress_text}"
                f"下一步训练动作：{action_text}"
            )

        root_text = self._human_error_name(root_cause)
        contrast = self._not_other_errors_text(root_cause)
        if pass_state == PassState.FALSE_PASS:
            return (
                f"根因判断：主要问题是{root_text}。答案不能证明掌握，因为题眼、方法或过程证据没有交代清楚。"
                f"为什么不是另一个常见错因：{contrast}"
                f"是否允许推进：{progress_text}"
                f"下一步训练动作：{action_text}"
            )
        return (
            f"根因判断：主要问题是{root_text}。"
            f"为什么不是另一个常见错因：{contrast}"
            f"是否允许推进：{progress_text}"
            f"下一步训练动作：{action_text}"
        )

    def _debug_explanation(
        self,
        root_cause: ErrorType | None,
        confidence: float,
        trace: DiagnosisTrace,
        error_chain: list[ErrorChainItem],
        rollback_level: RollbackLevel,
        forward_level: ForwardLevel,
    ) -> str:
        chain = [f"{item.role}:{item.error_type.value}" for item in error_chain]
        return (
            f"root_cause={root_cause.value if root_cause else 'none'}; "
            f"confidence={confidence:.2f}; "
            f"active_scorers={trace.active_scorers}; "
            f"required_missed={trace.required_missed}; "
            f"optional_missed={trace.optional_missed}; "
            f"validator_flags={trace.validator_flags}; "
            f"logic_contradictions={trace.logic_contradictions}; "
            f"surface_keyword_only={trace.surface_keyword_only}; "
            f"evidence_bundle_keys={list(trace.evidence_bundle)}; "
            f"policy_hits={trace.policy_hits}; "
            f"error_chain={chain}; "
            f"rollback_level={rollback_level.value}; "
            f"forward_level={forward_level.value}."
        )

    def _ability_state(
        self,
        *,
        score_vector: ScoreVector,
        root_cause: ErrorType | None,
        pass_state: PassState,
        trace: DiagnosisTrace,
    ) -> tuple[str, str, str]:
        if trace.rule_only or root_cause is None:
            return (
                "needs_more_evidence",
                "证据还不够",
                "目前只有弱信号或零散线索，系统不能把它包装成稳定掌握；需要补题眼、方法依据或关键步骤。",
            )

        if pass_state == PassState.PASS:
            return (
                "stable_for_current_node",
                "当前节点可点亮",
                "本题在当前考察维度上形成了足够证据，但后续仍要靠变式和综合验收确认稳定性。",
            )

        if pass_state == PassState.FALSE_PASS:
            return (
                "answer_without_evidence",
                "答案有但证据不足",
                "最终答案或关键词不能单独证明掌握；需要把题眼、方法选择和关键过程说清楚。",
            )

        if root_cause == ErrorType.CONCEPT_GAP:
            concept = score_vector.get_dimension(ScoreDimension.CONCEPT)
            if concept is not None and concept.score is not None and concept.score >= 45:
                return (
                    "understands_but_imprecise",
                    "大意知道但不精确",
                    "你已经碰到概念核心，但定义对象、适用条件或表述还不够精确，容易在相邻题型中摇摆。",
                )
            return (
                "concept_object_unstable",
                "概念对象不稳",
                "当前主要不是书写问题，而是概念对象和适用条件本身还没有站稳。",
            )

        if root_cause == ErrorType.TRIGGER_FAILURE:
            return (
                "recognizes_pattern_without_reason",
                "题眼依据不足",
                "你可能看到了某些关键词，但还没有说明它为什么指向这个题型入口。",
            )

        if root_cause == ErrorType.METHOD_ERROR:
            return (
                "method_by_memory_not_justified",
                "会想方法但依据不足",
                "当前像是在套熟悉方法，但方法选择依据没有闭合，所以后续过程很容易跑偏。",
            )

        if root_cause == ErrorType.TRANSFORMATION_ERROR:
            return (
                "transformation_unstable",
                "转化链条不稳",
                "题型和方法可能已经接近，但标准形、换元或等价变形这一步还没有稳定。",
            )

        if root_cause == ErrorType.CALCULATION_ERROR:
            if self._score_at_least(score_vector, ScoreDimension.METHOD, 70) and self._score_at_least(
                score_vector, ScoreDimension.TRANSFORMATION, 70
            ):
                return (
                    "calculation_slip",
                    "局部计算滑点",
                    "题眼、方法和转化证据基本成立，当前优先修局部积分、化简或常数处理。",
                )
            return (
                "calculation_chain_unstable",
                "计算链条不稳",
                "计算低分还没有足够证据证明只是手误，需要补充完整计算链条。",
            )

        if root_cause == ErrorType.CONDITION_MISS:
            return (
                "condition_tracking_unstable",
                "条件跟踪不稳",
                "主要问题是没有把初值、定义域或限制条件带到最后，不应简单归成计算错。",
            )

        if root_cause == ErrorType.EXPRESSION_WEAKNESS:
            return (
                "expression_imprecise",
                "表达不够严谨",
                "核心思路可以追踪，但通解形式、常数说明或结论书写还不够规范。",
            )

        if root_cause == ErrorType.KNOWLEDGE_CONFUSION:
            return (
                "neighbor_knowledge_confused",
                "相邻知识点混在一起",
                "当前像是把相邻题型的入口和方法混用了，需要先做对比辨析，而不是只刷同一种题。",
            )

        if root_cause == ErrorType.SYNTHESIS_FAILURE:
            return (
                "synthesis_path_missing",
                "综合拆题路径缺失",
                "问题不在某一个公式，而是在综合题第一步没有拆出可执行路线。",
            )

        return (
            "current_node_unstable",
            "当前节点不稳定",
            "已有错误证据指向当前节点能力不稳，需要先补本节点证据再推进。",
        )

    def explain(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
        pass_state: PassState,
        rollback_nodes: list[str],
        forward_nodes: list[str],
    ) -> str:
        overall = score_vector.overall_score()
        overall_text = f"{overall:.1f}" if overall is not None else "none"
        primary = [error.error_type.value for error in error_vector.primary_errors()]
        return (
            f"overall_score={overall_text}; "
            f"pass_state={pass_state.value}; "
            f"primary_errors={primary}; "
            f"rollback_nodes={rollback_nodes}; "
            f"forward_nodes={forward_nodes}."
        )

    def learner_explain(
        self,
        error_vector: ErrorVector,
        pass_state: PassState,
        rollback_nodes: list[str],
        forward_nodes: list[str],
    ) -> str:
        primary_errors = [error.error_type.value for error in error_vector.primary_errors()]
        if primary_errors and rollback_nodes:
            return f"根因判断：主要问题是 {', '.join(primary_errors)}。下一步训练动作：先回到 {', '.join(rollback_nodes)} 做针对训练。"
        if pass_state == PassState.PASS and forward_nodes:
            return f"根因判断：当前节点证据较稳定。是否允许推进：可以进入 {forward_nodes[0]}。"
        if pass_state == PassState.FALSE_PASS:
            return "根因判断：答案看似正确但证据不足。为什么不是另一个常见错因：不能只看最终答案，需要补题眼和方法说明。"
        return "根因判断：当前证据还不够稳定。下一步训练动作：继续做本节点复盘或变式练习。"

    def next_action_hint(
        self,
        pass_state: PassState,
        rollback_nodes: list[str],
        forward_nodes: list[str],
    ) -> str:
        if pass_state in {PassState.FAIL, PassState.FALSE_PASS} and rollback_nodes:
            return f"Review targeted rollback nodes first: {', '.join(rollback_nodes)}."
        if pass_state == PassState.PARTIAL_PASS:
            return "Do a short review task before normal progression."
        if forward_nodes:
            return f"Proceed to next node candidate: {forward_nodes[0]}."
        return "Stay on the current node and collect more evidence."

    def _upsert_error(
        self,
        errors_by_type: dict[ErrorType, ErrorItem],
        error_type: ErrorType,
        weight: float,
        related_dimensions: list[ScoreDimension],
        evidence: str,
        suggested_rollback_level: RollbackLevel,
    ) -> None:
        existing = errors_by_type.get(error_type)
        if existing is not None and existing.weight >= weight:
            existing.related_dimensions = self._dedupe_dimensions([*existing.related_dimensions, *related_dimensions])
            if evidence not in existing.evidence:
                existing.evidence = f"{existing.evidence} {evidence}"
            return
        errors_by_type[error_type] = ErrorItem(
            error_type=error_type,
            weight=weight,
            related_dimensions=related_dimensions,
            evidence=evidence,
            suggested_rollback_level=suggested_rollback_level,
        )

    def _dimension_from_trace_entry(self, entry: str) -> ScoreDimension | None:
        raw_dimension = entry.split(":", 1)[0]
        try:
            return ScoreDimension(raw_dimension)
        except ValueError:
            return None

    def _knowledge_confusion_signal(self, score_vector: ScoreVector, node: KnowledgeNode) -> bool:
        if ErrorType.KNOWLEDGE_CONFUSION not in node.common_errors:
            return False
        low_core = [
            self._score_below(score_vector, ScoreDimension.CONCEPT, 55),
            self._score_below(score_vector, ScoreDimension.TRIGGER, 55),
            self._score_below(score_vector, ScoreDimension.METHOD, 55),
        ]
        return sum(low_core) >= 2

    def _synthesis_failure_signal(self, score_vector: ScoreVector, node: KnowledgeNode) -> bool:
        if ErrorType.SYNTHESIS_FAILURE not in node.common_errors:
            return False
        return (
            self._score_below(score_vector, ScoreDimension.TRIGGER, 50)
            and self._score_below(score_vector, ScoreDimension.METHOD, 50)
            and self._score_below(score_vector, ScoreDimension.PROCESS, 50)
        )

    def _has_detailed_false_pass_signal(self, score_vector: ScoreVector) -> bool:
        final_answer = score_vector.get_dimension(ScoreDimension.FINAL_ANSWER)
        if final_answer is None or final_answer.score is None or final_answer.score < self.config.false_pass_final_answer_min:
            return False
        for dimension in (ScoreDimension.TRIGGER, ScoreDimension.METHOD, ScoreDimension.PROCESS):
            dimension_score = score_vector.get_dimension(dimension)
            if dimension_score is None or dimension_score.score is None or dimension_score.score < self.config.false_pass_dimension_max:
                return True
        return False

    def _chain_reason(
        self,
        error_type: ErrorType,
        role: str,
        root_cause: ErrorType | None,
        trace: DiagnosisTrace,
    ) -> str:
        if role == "weak_signal" or trace.rule_only:
            return "Only weak RuleScorer evidence is active, so this is not treated as a strong root cause."
        if role == "evidence_gap":
            return f"{error_type.value} is an evidence gap: required proof is missing, but no root cause is strong enough yet."
        if role in {"downstream_result", "derived_result"} and root_cause is not None:
            return f"{error_type.value} is the downstream final-answer result of {root_cause.value}."
        if role == "root":
            return f"{error_type.value} has the strongest causal support after applying diagnosis policy."
        if role == "derived" and root_cause is not None:
            return f"{error_type.value} is treated as downstream of {root_cause.value}."
        return f"{error_type.value} is present but not selected as the root cause."

    def _action_reason(self, action_type: str, root_cause: ErrorType | None) -> str:
        if action_type == "need_more_evidence":
            return "补做一题同节点诊断题，必须写出题眼、方法依据和关键过程。"
        if action_type == "calculation_repair":
            return "做局部计算修复训练，重点检查积分、符号、常数和化简，不回退概念。"
        if action_type == "trigger_drill":
            return "先做题眼识别训练，对比题目条件为什么指向这个节点。"
        if action_type == "method_comparison":
            return "做方法对比训练，写清楚为什么选这个方法而不是相邻方法。"
        if action_type == "transformation_drill":
            return "做条件转化训练，把原式一步步化到标准形并说明等价性。"
        if action_type == "condition_check":
            return "使用审题条件清单，特别检查初值、定义域、非零条件和最终形式。"
        if action_type == "expression_rewrite":
            return "重写解答表达，补齐定义、常数说明、变量含义和最终结论。"
        if action_type == "chapter_framework_review":
            return "回到章节框架做相邻知识点对比，再回到本题重做拆解。"
        if action_type == "variant_training":
            return "做一个同节点变式题，检验方法能否迁移。"
        return f"复盘当前节点，聚焦 {root_cause.value if root_cause else '证据不足'}。"

    def _next_action_from_recommendations(self, actions: list[RecommendedAction]) -> str:
        if not actions:
            return "Stay on the current node and collect more evidence."
        return actions[0].reason

    def _attempt_text(self, attempt: Attempt) -> str:
        return " ".join(
            [
                attempt.user_answer or "",
                " ".join(str(step) for step in attempt.response_steps),
                attempt.self_explanation or "",
            ]
        ).lower()

    def _cue_in_text(self, cue: str, text: str) -> bool:
        normalized = cue.strip().lower()
        return bool(normalized) and normalized in text

    def _logic_signal(
        self,
        signal_type: str,
        ability_kind: LogicAbilityKind,
        ability_id: str,
        cue: str,
    ) -> str:
        return f"{signal_type}:{ability_kind.value}:{ability_id}:{cue}"

    def _error_type_from_logic_signal(self, signal: str) -> ErrorType | None:
        parts = signal.split(":", 3)
        if len(parts) < 3:
            return None
        try:
            ability_kind = LogicAbilityKind(parts[1])
        except ValueError:
            return None
        return {
            LogicAbilityKind.CONCEPT_CRITERION: ErrorType.CONCEPT_GAP,
            LogicAbilityKind.TRIGGER_PATTERN: ErrorType.TRIGGER_FAILURE,
            LogicAbilityKind.METHOD_STEP: ErrorType.METHOD_ERROR,
            LogicAbilityKind.TRANSFORMATION_RULE: ErrorType.TRANSFORMATION_ERROR,
            LogicAbilityKind.CALCULATION_SKILL: ErrorType.CALCULATION_ERROR,
            LogicAbilityKind.EXPRESSION_RULE: ErrorType.EXPRESSION_WEAKNESS,
            LogicAbilityKind.CONDITION_RULE: ErrorType.CONDITION_MISS,
            LogicAbilityKind.MISCONCEPTION_GUARD: ErrorType.KNOWLEDGE_CONFUSION,
            LogicAbilityKind.SYNTHESIS_PATH: ErrorType.SYNTHESIS_FAILURE,
        }.get(ability_kind)

    def _dimensions_for_logic_error(self, error_type: ErrorType) -> list[ScoreDimension]:
        return {
            ErrorType.CONCEPT_GAP: [ScoreDimension.CONCEPT],
            ErrorType.TRIGGER_FAILURE: [ScoreDimension.TRIGGER],
            ErrorType.METHOD_ERROR: [ScoreDimension.METHOD],
            ErrorType.TRANSFORMATION_ERROR: [ScoreDimension.TRANSFORMATION],
            ErrorType.CALCULATION_ERROR: [ScoreDimension.CALCULATION, ScoreDimension.FINAL_ANSWER],
            ErrorType.CONDITION_MISS: [ScoreDimension.PROCESS, ScoreDimension.FINAL_ANSWER],
            ErrorType.EXPRESSION_WEAKNESS: [ScoreDimension.EXPRESSION],
            ErrorType.KNOWLEDGE_CONFUSION: [ScoreDimension.CONCEPT, ScoreDimension.TRIGGER, ScoreDimension.METHOD],
            ErrorType.SYNTHESIS_FAILURE: [ScoreDimension.TRIGGER, ScoreDimension.METHOD, ScoreDimension.PROCESS],
        }.get(error_type, [ScoreDimension.PROCESS])

    def _partial_concept_understanding(
        self,
        score_vector: ScoreVector,
        error_vector: ErrorVector,
    ) -> bool:
        primary_errors = error_vector.primary_errors()
        if not primary_errors or any(error.error_type != ErrorType.CONCEPT_GAP for error in primary_errors):
            return False
        concept = score_vector.get_dimension(ScoreDimension.CONCEPT)
        if concept is None or concept.score is None:
            return False
        if not 50 <= concept.score < 70:
            return False
        blockers = {
            ErrorType.TRIGGER_FAILURE,
            ErrorType.METHOD_ERROR,
            ErrorType.TRANSFORMATION_ERROR,
            ErrorType.KNOWLEDGE_CONFUSION,
            ErrorType.SYNTHESIS_FAILURE,
        }
        return not any(error.error_type in blockers and error.weight >= 0.4 for error in error_vector.errors)

    def _derived_error_types(
        self,
        error_chain: list[ErrorChainItem],
        root_cause: ErrorType | None,
    ) -> list[ErrorType]:
        derived: list[ErrorType] = []
        for item in error_chain:
            if item.role not in {"derived", "derived_result", "downstream_result"}:
                continue
            if item.error_type == root_cause and item.role in {"derived_result", "downstream_result"}:
                continue
            if item.error_type not in derived:
                derived.append(item.error_type)
        return derived

    def _role_error_types(
        self,
        error_chain: list[ErrorChainItem],
        roles: set[str],
        root_cause: ErrorType | None,
    ) -> list[ErrorType]:
        values: list[ErrorType] = []
        for item in error_chain:
            if item.role not in roles:
                continue
            if item.error_type == root_cause and item.role == "derived_result":
                continue
            if item.error_type not in values:
                values.append(item.error_type)
        return values

    def _human_error_name(self, error_type: ErrorType) -> str:
        names = {
            ErrorType.CONCEPT_GAP: "概念理解漏洞",
            ErrorType.TRIGGER_FAILURE: "题眼识别失败",
            ErrorType.METHOD_ERROR: "方法选择依据不足",
            ErrorType.TRANSFORMATION_ERROR: "条件转化或标准形处理失败",
            ErrorType.PROCESS_GAP: "解题过程链条断裂",
            ErrorType.CALCULATION_ERROR: "局部计算执行错误",
            ErrorType.CONDITION_MISS: "审题条件遗漏",
            ErrorType.FORMULA_MEMORY_ERROR: "公式或标准形式记忆不稳",
            ErrorType.KNOWLEDGE_CONFUSION: "相邻知识点混淆",
            ErrorType.EXPRESSION_WEAKNESS: "数学表达不严谨",
            ErrorType.MIGRATION_FAILURE: "变式迁移不足",
            ErrorType.SYNTHESIS_FAILURE: "综合题拆题路径失败",
        }
        return names[error_type]

    def _not_other_errors_text(self, root_cause: ErrorType) -> str:
        if root_cause == ErrorType.CALCULATION_ERROR:
            return "不是主要的方法问题，因为题眼、方法和转化证据已经比较完整，最终答案错主要是计算环节的下游结果。"
        if root_cause == ErrorType.TRIGGER_FAILURE:
            return "不是主要的计算问题，因为最先缺失的是看出题目属于哪类方程的证据。"
        if root_cause == ErrorType.METHOD_ERROR:
            return "不是主要的计算问题，因为开始计算前，方法路线本身还没有被正确说明或选择。"
        if root_cause == ErrorType.TRANSFORMATION_ERROR:
            return "不是主要的计算问题，因为计算之前，条件转化或标准形已经断掉了。"
        if root_cause == ErrorType.CONDITION_MISS:
            return "不是主要的计算问题，因为遗漏条件会让看似可行的答案变成不完整答案。"
        if root_cause == ErrorType.EXPRESSION_WEAKNESS:
            return "不是概念漏洞，因为核心概念证据基本存在，问题主要在书写不够严谨。"
        if root_cause == ErrorType.SYNTHESIS_FAILURE:
            return "不是单个公式问题，因为这类题先需要建立拆题路径，再谈具体公式。"
        if root_cause == ErrorType.KNOWLEDGE_CONFUSION:
            return "不是孤立步骤错误，因为多个相邻节点的题眼和方法信号被混在了一起。"
        if root_cause == ErrorType.CONCEPT_GAP:
            return "不是单纯表达问题，因为概念对象或适用条件本身已经出现偏差。"
        return "其他低分被视为下游结果或次要证据，不作为当前主根因。"

    def _dedupe_strings(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                deduped.append(value)
        return deduped

    def _bundle_add(self, trace: DiagnosisTrace, key: str, values: list[str]) -> None:
        cleaned = [value for value in values if value]
        if not cleaned:
            return
        trace.evidence_bundle[key] = self._dedupe_strings([*trace.evidence_bundle.get(key, []), *cleaned])

    def _dedupe_dimensions(self, values: list[ScoreDimension]) -> list[ScoreDimension]:
        seen: set[ScoreDimension] = set()
        deduped: list[ScoreDimension] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                deduped.append(value)
        return deduped

    def _build_error(
        self,
        error_type: ErrorType,
        dimension: ScoreDimension,
        score: float,
        evidence: str,
    ) -> ErrorItem:
        weight = self._weight_from_score(score)
        related_dimensions = [dimension]
        if error_type == ErrorType.CALCULATION_ERROR:
            related_dimensions.append(ScoreDimension.FINAL_ANSWER)
        return ErrorItem(
            error_type=error_type,
            weight=weight,
            related_dimensions=related_dimensions,
            evidence=evidence,
            is_primary=weight >= self.config.primary_error_threshold,
            suggested_rollback_level=self.config.default_rollback_level_by_error[error_type],
        )

    def _weight_from_score(self, score: float) -> float:
        if score < 30:
            return 0.9
        if score < 50:
            return 0.75
        if score < 70:
            return 0.5
        return 0.0

    def _merge_duplicate_errors(self, errors: list[ErrorItem]) -> list[ErrorItem]:
        merged: dict[ErrorType, ErrorItem] = {}
        for error in errors:
            existing = merged.get(error.error_type)
            if existing is None or error.weight > existing.weight:
                merged[error.error_type] = error
            elif existing:
                existing.related_dimensions = list({*existing.related_dimensions, *error.related_dimensions})
        return list(merged.values())

    def _promote_false_pass_errors(self, score_vector: ScoreVector, errors: list[ErrorItem]) -> list[ErrorItem]:
        if not self._has_false_pass_signal(score_vector):
            return errors

        existing_types = {error.error_type for error in errors}
        for dimension, error_type in (
            (ScoreDimension.TRIGGER, ErrorType.TRIGGER_FAILURE),
            (ScoreDimension.METHOD, ErrorType.METHOD_ERROR),
        ):
            dimension_score = score_vector.get_dimension(dimension)
            if (
                dimension_score is not None
                and dimension_score.score is not None
                and dimension_score.score < self.config.false_pass_dimension_max
                and error_type not in existing_types
            ):
                errors.append(
                    ErrorItem(
                        error_type=error_type,
                        weight=0.8 if dimension == ScoreDimension.TRIGGER else 0.7,
                        related_dimensions=[dimension],
                        evidence=dimension_score.evidence or "False-pass signal: final answer is high but reasoning evidence is weak.",
                        is_primary=True,
                        suggested_rollback_level=self.config.default_rollback_level_by_error[error_type],
                    )
                )
        return errors

    def _infer_contextual_errors(
        self,
        score_vector: ScoreVector,
        question: Question,
        attempt: Attempt,
        node: KnowledgeNode,
        errors: list[ErrorItem],
    ) -> list[ErrorItem]:
        existing_types = {error.error_type for error in errors}

        if ErrorType.FORMULA_MEMORY_ERROR in node.common_errors and ErrorType.FORMULA_MEMORY_ERROR not in existing_types:
            formula_signal = self._score_below(score_vector, ScoreDimension.CALCULATION, 50) or (
                self._score_below(score_vector, ScoreDimension.TRANSFORMATION, 60)
                and self._score_below(score_vector, ScoreDimension.FINAL_ANSWER, 70)
            )
            if formula_signal:
                errors.append(
                    ErrorItem(
                        error_type=ErrorType.FORMULA_MEMORY_ERROR,
                        weight=0.85,
                        related_dimensions=[ScoreDimension.METHOD, ScoreDimension.TRANSFORMATION],
                        evidence="Node policy and score pattern indicate an unstable formula or standard form.",
                        suggested_rollback_level=self.config.default_rollback_level_by_error[ErrorType.FORMULA_MEMORY_ERROR],
                    )
                )

        if ErrorType.KNOWLEDGE_CONFUSION in node.common_errors and ErrorType.KNOWLEDGE_CONFUSION not in existing_types:
            if self._score_below(score_vector, ScoreDimension.CONCEPT, 50) and self._score_below(score_vector, ScoreDimension.METHOD, 40):
                errors.append(
                    ErrorItem(
                        error_type=ErrorType.KNOWLEDGE_CONFUSION,
                        weight=0.95,
                        related_dimensions=[ScoreDimension.CONCEPT, ScoreDimension.TRIGGER, ScoreDimension.METHOD],
                        evidence="Low concept, trigger, and method evidence indicate confusion between nearby ODE types.",
                        suggested_rollback_level=self.config.default_rollback_level_by_error[ErrorType.KNOWLEDGE_CONFUSION],
                    )
                )

        if ErrorType.SYNTHESIS_FAILURE in node.common_errors and ErrorType.SYNTHESIS_FAILURE not in existing_types:
            if (
                self._score_below(score_vector, ScoreDimension.TRIGGER, 40)
                and self._score_below(score_vector, ScoreDimension.METHOD, 40)
                and self._score_below(score_vector, ScoreDimension.PROCESS, 40)
            ):
                errors.append(
                    ErrorItem(
                        error_type=ErrorType.SYNTHESIS_FAILURE,
                        weight=0.95,
                        related_dimensions=[ScoreDimension.TRIGGER, ScoreDimension.METHOD, ScoreDimension.PROCESS],
                        evidence="The attempt cannot decompose a compound ODE task into recognizable substeps.",
                        suggested_rollback_level=self.config.default_rollback_level_by_error[ErrorType.SYNTHESIS_FAILURE],
                    )
                )

        if ErrorType.CONDITION_MISS not in existing_types and self._condition_miss_signal(score_vector, question, attempt, node):
            errors.append(
                ErrorItem(
                    error_type=ErrorType.CONDITION_MISS,
                    weight=0.85,
                    related_dimensions=[ScoreDimension.PROCESS, ScoreDimension.FINAL_ANSWER],
                    evidence="The solution path is mostly valid but required conditions such as an initial value were not used.",
                    suggested_rollback_level=self.config.default_rollback_level_by_error[ErrorType.CONDITION_MISS],
                )
            )

        return self._merge_duplicate_errors(errors)

    def _condition_miss_signal(
        self,
        score_vector: ScoreVector,
        question: Question,
        attempt: Attempt,
        node: KnowledgeNode,
    ) -> bool:
        del node, attempt
        mentions_condition = (
            bool(question.metadata.get("requires_initial_condition"))
            or bool(question.metadata.get("requires_condition_check"))
            or bool(re.search(r"y\s*\([^)]*\)\s*=", question.prompt, flags=re.IGNORECASE))
            or "initial condition" in question.prompt.lower()
            or "ivp" in question.prompt.lower()
            or "初值" in question.prompt
        )
        method_ok = not self._score_below(score_vector, ScoreDimension.METHOD, 70)
        final_low = self._score_below(score_vector, ScoreDimension.FINAL_ANSWER, 60)
        process_soft = self._score_below(score_vector, ScoreDimension.PROCESS, 75)
        return mentions_condition and method_ok and final_low and process_soft

    def _score_below(self, score_vector: ScoreVector, dimension: ScoreDimension, threshold: float) -> bool:
        dimension_score = score_vector.get_dimension(dimension)
        return dimension_score is not None and dimension_score.score is not None and dimension_score.score < threshold

    def _score_at_least(self, score_vector: ScoreVector, dimension: ScoreDimension, threshold: float) -> bool:
        dimension_score = score_vector.get_dimension(dimension)
        return dimension_score is not None and dimension_score.score is not None and dimension_score.score >= threshold

    def _align_with_node_policy(
        self,
        errors: list[ErrorItem],
        node: KnowledgeNode,
        false_pass_signal: bool = False,
    ) -> list[ErrorItem]:
        for error in errors:
            if false_pass_signal and error.error_type in {ErrorType.TRIGGER_FAILURE, ErrorType.METHOD_ERROR}:
                error.suggested_rollback_level = RollbackLevel.R1_INTERNAL
                continue
            policy = node.rollback_policy.get(error.error_type.value)
            if policy:
                error.suggested_rollback_level = policy.level
        return errors

    def _has_false_pass_signal(self, score_vector: ScoreVector) -> bool:
        final_answer = score_vector.get_dimension(ScoreDimension.FINAL_ANSWER)
        if final_answer is None or final_answer.score is None:
            return False
        if final_answer.score < self.config.false_pass_final_answer_min:
            return False
        for dimension in (ScoreDimension.TRIGGER, ScoreDimension.METHOD):
            dimension_score = score_vector.get_dimension(dimension)
            if (
                dimension_score is not None
                and dimension_score.score is not None
                and dimension_score.score < self.config.false_pass_dimension_max
            ):
                return True
        return False

    def _required_dimensions_met(self, score_vector: ScoreVector, node: KnowledgeNode) -> bool:
        for dimension, minimum in node.pass_criteria.min_required_dimensions.items():
            dimension_score = score_vector.get_dimension(dimension)
            if dimension_score is None or dimension_score.score is None:
                return False
            if dimension_score.score < minimum:
                return False
        return True

    def _only_expression_primary(self, primary_errors: list[ErrorItem]) -> bool:
        return bool(primary_errors) and all(error.error_type == ErrorType.EXPRESSION_WEAKNESS for error in primary_errors)
