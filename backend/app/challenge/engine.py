from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.api.v1.nodes import load_node_catalog
from app.challenge.chapter_registry import ChapterRuntimeRegistry
from app.challenge.models import (
    ChallengeEvaluation,
    ChallengeGraph,
    ChallengeMasteryState,
    ChallengeNodeProgress,
    ChallengeProgress,
    ChallengeQuestion,
    ChallengeQuestionBank,
    ChallengeStatus,
    ChallengeTask,
    ChallengeTaskType,
    MicroNodeSpec,
    MicroNodeType,
)
from app.challenge.progress_store import ChallengeProgressStore
from app.challenge.repository import DEFAULT_CHALLENGE_ID, ChallengeRepository
from app.core.enums import ErrorType, NodeStatus, NodeType, PassState, QuestionType, ScoreDimension
from app.core.schemas import Attempt, KnowledgeNode, PassCriteria, Question
from app.logic_graph.models import LogicAbilityKind, LogicAbilityRole, LogicEdgeType
from app.logic_graph.repository import LogicGraphRepository
from app.services.learning_orchestrator import LearningOrchestrator
from app.training.coach_output import build_coach_output
from app.training.session_log import append_attempt, ensure_no_trusted_fields


DEFAULT_DIMENSIONS_BY_MICRO_TYPE: dict[MicroNodeType, list[ScoreDimension]] = {
    MicroNodeType.CONCEPT: [ScoreDimension.CONCEPT],
    MicroNodeType.TRIGGER: [ScoreDimension.TRIGGER],
    MicroNodeType.METHOD: [ScoreDimension.METHOD],
    MicroNodeType.TRANSFORMATION: [ScoreDimension.TRANSFORMATION],
    MicroNodeType.CALCULATION: [ScoreDimension.CALCULATION],
    MicroNodeType.EXPRESSION: [ScoreDimension.EXPRESSION, ScoreDimension.FINAL_ANSWER],
}

DEFAULT_ERROR_TO_MICRO_TYPE: dict[ErrorType, MicroNodeType] = {
    ErrorType.CONCEPT_GAP: MicroNodeType.CONCEPT,
    ErrorType.TRIGGER_FAILURE: MicroNodeType.TRIGGER,
    ErrorType.METHOD_ERROR: MicroNodeType.METHOD,
    ErrorType.TRANSFORMATION_ERROR: MicroNodeType.TRANSFORMATION,
    ErrorType.CALCULATION_ERROR: MicroNodeType.CALCULATION,
    ErrorType.FORMULA_MEMORY_ERROR: MicroNodeType.CALCULATION,
    ErrorType.EXPRESSION_WEAKNESS: MicroNodeType.EXPRESSION,
    ErrorType.PROCESS_GAP: MicroNodeType.EXPRESSION,
    ErrorType.CONDITION_MISS: MicroNodeType.TRIGGER,
    ErrorType.KNOWLEDGE_CONFUSION: MicroNodeType.TRIGGER,
    ErrorType.SYNTHESIS_FAILURE: MicroNodeType.METHOD,
    ErrorType.MIGRATION_FAILURE: MicroNodeType.METHOD,
}

ROOT_CAUSE_DIMENSIONS: dict[ErrorType, list[ScoreDimension]] = {
    ErrorType.CONCEPT_GAP: [ScoreDimension.CONCEPT],
    ErrorType.TRIGGER_FAILURE: [ScoreDimension.TRIGGER],
    ErrorType.METHOD_ERROR: [ScoreDimension.METHOD],
    ErrorType.TRANSFORMATION_ERROR: [ScoreDimension.TRANSFORMATION],
    ErrorType.PROCESS_GAP: [ScoreDimension.PROCESS],
    ErrorType.CALCULATION_ERROR: [ScoreDimension.CALCULATION, ScoreDimension.FINAL_ANSWER],
    ErrorType.CONDITION_MISS: [ScoreDimension.TRIGGER, ScoreDimension.PROCESS, ScoreDimension.FINAL_ANSWER],
    ErrorType.FORMULA_MEMORY_ERROR: [ScoreDimension.CALCULATION],
    ErrorType.KNOWLEDGE_CONFUSION: [ScoreDimension.CONCEPT, ScoreDimension.TRIGGER, ScoreDimension.METHOD],
    ErrorType.EXPRESSION_WEAKNESS: [ScoreDimension.EXPRESSION],
    ErrorType.MIGRATION_FAILURE: [ScoreDimension.MIGRATION, ScoreDimension.METHOD],
    ErrorType.SYNTHESIS_FAILURE: [ScoreDimension.TRIGGER, ScoreDimension.METHOD, ScoreDimension.PROCESS],
}

NODE_TYPE_BY_MICRO_TYPE = {
    MicroNodeType.CONCEPT: NodeType.CONCEPT,
    MicroNodeType.TRIGGER: NodeType.METHOD,
    MicroNodeType.METHOD: NodeType.METHOD,
    MicroNodeType.TRANSFORMATION: NodeType.TRANSFORMATION,
    MicroNodeType.CALCULATION: NodeType.CALCULATION,
    MicroNodeType.EXPRESSION: NodeType.CONCEPT,
}

EvaluationProcessor = Callable[[Question, Attempt, KnowledgeNode], ChallengeEvaluation]


class ChallengeEngineError(ValueError):
    """Raised when a local challenge operation cannot be completed."""


class ChallengeEngine:
    def __init__(
        self,
        repository: ChallengeRepository | None = None,
        store: ChallengeProgressStore | None = None,
        processor: EvaluationProcessor | None = None,
        logic_graph_repository: LogicGraphRepository | None = None,
    ) -> None:
        self.repository = repository or ChallengeRepository()
        self.store = store or ChallengeProgressStore()
        self.processor = processor or self._process_with_orchestrator
        self.logic_graph_repository = logic_graph_repository or LogicGraphRepository()
        self.runtime_registry = ChapterRuntimeRegistry(self.repository)

    def start(
        self,
        chapter_id: str = DEFAULT_CHALLENGE_ID,
        *,
        session_id: str,
        session_root: str | Path | None = None,
    ) -> dict[str, Any]:
        self.runtime_registry.ensure_trainable(chapter_id)
        graph = self.repository.load_graph(chapter_id)
        questions = self.repository.load_question_bank(chapter_id)
        progress = self._initial_progress(graph, session_id)
        self._ensure_mastery_states(graph, progress)
        self._refresh_unlocks(graph, progress)
        self._assign_current_task(graph, questions, progress)
        progress_path = self.store.save(progress, session_root)
        return self._status_payload(graph, questions, progress, progress_path=progress_path)

    def status(self, *, session_id: str, session_root: str | Path | None = None) -> dict[str, Any]:
        progress = self.store.load(session_id, session_root)
        self.runtime_registry.ensure_trainable(progress.chapter_id)
        graph = self.repository.load_graph(progress.chapter_id)
        questions = self.repository.load_question_bank(progress.chapter_id)
        self._ensure_mastery_states(graph, progress)
        self._refresh_unlocks(graph, progress)
        self._assign_current_task(graph, questions, progress)
        progress_path = self.store.save(progress, session_root)
        return self._status_payload(graph, questions, progress, progress_path=progress_path)

    def submit(
        self,
        *,
        session_id: str,
        answer: str,
        steps: list[str] | None = None,
        explanation: str | None = None,
        session_root: str | Path | None = None,
    ) -> dict[str, Any]:
        progress = self.store.load(session_id, session_root)
        self.runtime_registry.ensure_trainable(progress.chapter_id)
        graph = self.repository.load_graph(progress.chapter_id)
        questions = self.repository.load_question_bank(progress.chapter_id)
        self._ensure_mastery_states(graph, progress)
        self._refresh_unlocks(graph, progress)
        self._assign_current_task(graph, questions, progress)
        if progress.current_task is None:
            raise ChallengeEngineError("challenge has no active task")

        task = progress.current_task
        question_spec = self._current_question(graph, questions, progress)
        domain_question = self._to_domain_question(graph, question_spec)
        node = self._node_for_task(graph, task)
        attempt = Attempt(
            id=f"{session_id}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}",
            question_id=domain_question.id,
            user_answer=answer,
            response_steps=steps or [],
            self_explanation=explanation,
        )
        evaluation = self.processor(domain_question, attempt, node)
        self._apply_result(graph, progress, task, evaluation)
        self._update_mastery_from_evaluation(graph, progress, task, evaluation)
        self._refresh_unlocks(graph, progress)
        self._assign_current_task(graph, questions, progress)
        progress_path = self.store.save(progress, session_root)

        payload = dict(evaluation.coach_payload)
        payload["challenge"] = self._status_payload(graph, questions, progress, progress_path=progress_path)["challenge"]
        payload["challenge_attempt"] = {
            "task_type": task.task_type.value,
            "task_id": task.task_id,
            "question_id": question_spec.id,
            "pass_state": evaluation.pass_state.value,
            "root_cause": evaluation.root_cause.value if evaluation.root_cause else None,
            "repair_target_node_id": evaluation.repair_target_node_id,
        }
        self._apply_challenge_coach_overlay(payload, task, evaluation)
        ensure_no_trusted_fields(payload)

        append_attempt(
            self._session_log_record(
                session_id=session_id,
                task=task,
                question=question_spec,
                answer=answer,
                steps=steps or [],
                explanation=explanation,
                payload=payload,
            ),
            session_id=session_id,
            session_root=session_root,
        )
        payload["session_log_written"] = True
        payload["session_id"] = session_id
        ensure_no_trusted_fields(payload)
        return payload

    def reset(
        self,
        *,
        session_id: str,
        node_id: str | None = None,
        reset_all: bool = False,
        session_root: str | Path | None = None,
    ) -> dict[str, Any]:
        progress = self.store.load(session_id, session_root)
        self.runtime_registry.ensure_trainable(progress.chapter_id)
        graph = self.repository.load_graph(progress.chapter_id)
        questions = self.repository.load_question_bank(progress.chapter_id)
        self._ensure_mastery_states(graph, progress)
        if reset_all:
            progress = self._initial_progress(graph, session_id)
            self._ensure_mastery_states(graph, progress)
        elif node_id:
            self._reset_node(progress, node_id)
        else:
            raise ChallengeEngineError("challenge-reset requires --node-id or --all")
        self._refresh_unlocks(graph, progress)
        self._assign_current_task(graph, questions, progress)
        progress_path = self.store.save(progress, session_root)
        return self._status_payload(graph, questions, progress, progress_path=progress_path)

    def _initial_progress(self, graph: ChallengeGraph, session_id: str) -> ChallengeProgress:
        macro_nodes = {macro.id: ChallengeNodeProgress(status=ChallengeStatus.LOCKED) for macro in graph.macro_nodes}
        micro_nodes = {}
        for micro in graph.micro_nodes:
            status = ChallengeStatus.AVAILABLE if self._is_initial_micro(graph, micro.id) else ChallengeStatus.LOCKED
            micro_nodes[micro.id] = ChallengeNodeProgress(status=status)
        macro_challenges = {
            challenge.id: ChallengeNodeProgress(status=ChallengeStatus.LOCKED) for challenge in graph.macro_challenges
        }
        mastery = {
            **{macro.id: ChallengeMasteryState() for macro in graph.macro_nodes},
            **{micro.id: ChallengeMasteryState() for micro in graph.micro_nodes},
        }
        return ChallengeProgress(
            chapter_id=graph.chapter_id,
            session_id=session_id,
            macro_nodes=macro_nodes,
            micro_nodes=micro_nodes,
            macro_challenges=macro_challenges,
            mastery=mastery,
        )

    def _ensure_mastery_states(self, graph: ChallengeGraph, progress: ChallengeProgress) -> None:
        for macro in graph.macro_nodes:
            progress.mastery.setdefault(macro.id, ChallengeMasteryState())
        for micro in graph.micro_nodes:
            progress.mastery.setdefault(micro.id, ChallengeMasteryState())
        valid_ids = {macro.id for macro in graph.macro_nodes} | {micro.id for micro in graph.micro_nodes}
        for stale_id in [node_id for node_id in progress.mastery if node_id not in valid_ids]:
            del progress.mastery[stale_id]
        self._refresh_mastery_visuals(progress)

    def _is_initial_micro(self, graph: ChallengeGraph, micro_id: str) -> bool:
        for edge in graph.unlock_edges:
            if micro_id in edge.to_micro_node_ids:
                return False
        return True

    def _refresh_unlocks(self, graph: ChallengeGraph, progress: ChallengeProgress) -> None:
        for macro in graph.macro_nodes:
            macro_progress = progress.macro_nodes[macro.id]
            if macro_progress.status in {ChallengeStatus.MASTERED, ChallengeStatus.FAILED, ChallengeStatus.ACTIVE}:
                continue
            contained = graph.contains.get(macro.id, [])
            if contained and all(progress.micro_nodes[micro_id].status == ChallengeStatus.MASTERED for micro_id in contained):
                macro_progress.status = ChallengeStatus.AVAILABLE
                challenge = self._challenge_for_macro(graph, macro.id)
                progress.macro_challenges[challenge.id].status = ChallengeStatus.AVAILABLE

        for edge in graph.unlock_edges:
            if progress.macro_nodes[edge.from_macro_node_id].status != ChallengeStatus.MASTERED:
                continue
            for micro_id in edge.to_micro_node_ids:
                micro_progress = progress.micro_nodes[micro_id]
                if micro_progress.status == ChallengeStatus.LOCKED:
                    micro_progress.status = ChallengeStatus.AVAILABLE

        progress.completed = bool(progress.macro_nodes) and all(
            node.status == ChallengeStatus.MASTERED for node in progress.macro_nodes.values()
        )
        self._refresh_mastery_visuals(progress)

    def _assign_current_task(
        self,
        graph: ChallengeGraph,
        questions: ChallengeQuestionBank,
        progress: ChallengeProgress,
    ) -> None:
        if progress.completed:
            progress.current_task = None
            return

        for micro in graph.micro_nodes:
            if progress.micro_nodes[micro.id].status == ChallengeStatus.ACTIVE:
                progress.current_task = self._task_for_micro(graph, questions, micro.id, progress)
                self._refresh_mastery_visuals(progress)
                return
        for micro in graph.micro_nodes:
            if progress.micro_nodes[micro.id].status == ChallengeStatus.AVAILABLE:
                progress.micro_nodes[micro.id].status = ChallengeStatus.ACTIVE
                progress.current_task = self._task_for_micro(graph, questions, micro.id, progress)
                self._refresh_mastery_visuals(progress)
                return
        for challenge in graph.macro_challenges:
            if progress.macro_challenges[challenge.id].status == ChallengeStatus.AVAILABLE:
                progress.macro_challenges[challenge.id].status = ChallengeStatus.ACTIVE
                progress.macro_nodes[challenge.macro_node_id].status = ChallengeStatus.ACTIVE
                progress.current_task = self._task_for_macro_challenge(graph, questions, challenge.id, progress)
                self._refresh_mastery_visuals(progress)
                return
            if progress.macro_challenges[challenge.id].status == ChallengeStatus.ACTIVE:
                progress.current_task = self._task_for_macro_challenge(graph, questions, challenge.id, progress)
                self._refresh_mastery_visuals(progress)
                return
        progress.current_task = None
        self._refresh_mastery_visuals(progress)

    def _task_for_micro(
        self,
        graph: ChallengeGraph,
        questions: ChallengeQuestionBank,
        micro_id: str,
        progress: ChallengeProgress,
    ) -> ChallengeTask:
        micro = self._micro(graph, micro_id)
        question = self._select_question(questions, ChallengeTaskType.MICRO_NODE, micro_id, progress.micro_nodes[micro_id].attempts_used)
        return ChallengeTask(
            task_type=ChallengeTaskType.MICRO_NODE,
            task_id=micro_id,
            macro_node_id=micro.macro_node_id,
            question_id=question.id,
        )

    def _task_for_macro_challenge(
        self,
        graph: ChallengeGraph,
        questions: ChallengeQuestionBank,
        challenge_id: str,
        progress: ChallengeProgress,
    ) -> ChallengeTask:
        challenge = self._challenge(graph, challenge_id)
        question = self._select_question(
            questions,
            ChallengeTaskType.MACRO_CHALLENGE,
            challenge_id,
            progress.macro_challenges[challenge_id].attempts_used,
        )
        return ChallengeTask(
            task_type=ChallengeTaskType.MACRO_CHALLENGE,
            task_id=challenge_id,
            macro_node_id=challenge.macro_node_id,
            question_id=question.id,
        )

    def _apply_result(
        self,
        graph: ChallengeGraph,
        progress: ChallengeProgress,
        task: ChallengeTask,
        evaluation: ChallengeEvaluation,
    ) -> None:
        if task.task_type == ChallengeTaskType.MICRO_NODE:
            self._apply_micro_result(graph, progress, task.task_id, evaluation.pass_state)
            return
        self._apply_macro_result(graph, progress, task.task_id, evaluation)

    def _apply_micro_result(
        self,
        graph: ChallengeGraph,
        progress: ChallengeProgress,
        micro_id: str,
        pass_state: PassState,
    ) -> None:
        micro_progress = progress.micro_nodes[micro_id]
        if pass_state == PassState.PASS:
            micro_progress.status = ChallengeStatus.MASTERED
            micro_progress.attempts_used = 0
            return
        micro_progress.attempts_used += 1
        if micro_progress.attempts_used >= graph.attempt_limits.micro_node:
            micro_progress.failed_cycles += 1
            micro_progress.attempts_used = 0
        micro_progress.status = ChallengeStatus.ACTIVE

    def _apply_macro_result(
        self,
        graph: ChallengeGraph,
        progress: ChallengeProgress,
        challenge_id: str,
        evaluation: ChallengeEvaluation,
    ) -> None:
        challenge = self._challenge(graph, challenge_id)
        challenge_progress = progress.macro_challenges[challenge_id]
        macro_progress = progress.macro_nodes[challenge.macro_node_id]
        if evaluation.pass_state == PassState.PASS:
            challenge_progress.status = ChallengeStatus.MASTERED
            challenge_progress.attempts_used = 0
            macro_progress.status = ChallengeStatus.MASTERED
            macro_progress.attempts_used = 0
            return

        challenge_progress.attempts_used += 1
        macro_progress.attempts_used = challenge_progress.attempts_used
        if challenge_progress.attempts_used >= graph.attempt_limits.macro_challenge:
            challenge_progress.status = ChallengeStatus.FAILED
            macro_progress.status = ChallengeStatus.FAILED
            return

        target_micro_id = self._target_micro_for_evaluation(graph, challenge.macro_node_id, evaluation)
        target_progress = progress.micro_nodes[target_micro_id]
        target_progress.status = ChallengeStatus.ACTIVE
        target_progress.attempts_used = 0
        challenge_progress.status = ChallengeStatus.ACTIVE
        macro_progress.status = ChallengeStatus.ACTIVE

    def _target_micro_for_error(
        self,
        graph: ChallengeGraph,
        macro_node_id: str,
        root_cause: ErrorType | None,
    ) -> str:
        contained = graph.contains.get(macro_node_id, [])
        if not contained:
            raise ChallengeEngineError(f"macro node has no contained micro nodes: {macro_node_id}")
        if root_cause and root_cause in graph.error_to_micro_mapping:
            mapped = graph.error_to_micro_mapping[root_cause]
            if mapped in contained:
                return mapped
            for micro in self._micro_nodes_for_macro(graph, macro_node_id):
                if micro.type.value == mapped:
                    return micro.id
        if root_cause and root_cause in DEFAULT_ERROR_TO_MICRO_TYPE:
            target_type = DEFAULT_ERROR_TO_MICRO_TYPE[root_cause]
            for micro in self._micro_nodes_for_macro(graph, macro_node_id):
                if micro.type == target_type:
                    return micro.id
        return contained[0]

    def _target_micro_for_evaluation(
        self,
        graph: ChallengeGraph,
        macro_node_id: str,
        evaluation: ChallengeEvaluation,
    ) -> str:
        contained = set(graph.contains.get(macro_node_id, []))
        if evaluation.repair_target_node_id in contained:
            return str(evaluation.repair_target_node_id)
        return self._target_micro_for_error(graph, macro_node_id, evaluation.root_cause)

    def _reset_node(self, progress: ChallengeProgress, node_id: str) -> None:
        if node_id in progress.micro_nodes:
            progress.micro_nodes[node_id] = ChallengeNodeProgress(status=ChallengeStatus.AVAILABLE)
            progress.mastery[node_id] = ChallengeMasteryState(visual_state="available")
            return
        if node_id in progress.macro_nodes:
            progress.macro_nodes[node_id] = ChallengeNodeProgress(status=ChallengeStatus.LOCKED)
            progress.mastery[node_id] = ChallengeMasteryState()
            return
        if node_id in progress.macro_challenges:
            progress.macro_challenges[node_id] = ChallengeNodeProgress(status=ChallengeStatus.LOCKED)
            return
        raise ChallengeEngineError(f"unknown challenge node id: {node_id}")

    def _current_question(
        self,
        graph: ChallengeGraph,
        questions: ChallengeQuestionBank,
        progress: ChallengeProgress,
    ) -> ChallengeQuestion:
        if progress.current_task is None:
            raise ChallengeEngineError("challenge has no current task")
        if progress.current_task.question_id:
            return self._question_by_id(questions, progress.current_task.question_id)
        if progress.current_task.task_type == ChallengeTaskType.MICRO_NODE:
            attempts = progress.micro_nodes[progress.current_task.task_id].attempts_used
        else:
            attempts = progress.macro_challenges[progress.current_task.task_id].attempts_used
        return self._select_question(questions, progress.current_task.task_type, progress.current_task.task_id, attempts)

    def _select_question(
        self,
        questions: ChallengeQuestionBank,
        task_type: ChallengeTaskType,
        owner_id: str,
        attempts_used: int,
    ) -> ChallengeQuestion:
        candidates = [question for question in questions.questions if question.task_type == task_type and question.owner_id == owner_id]
        if not candidates:
            raise ChallengeEngineError(f"no challenge questions found for {task_type.value}:{owner_id}")
        return candidates[attempts_used % len(candidates)]

    def _to_domain_question(self, graph: ChallengeGraph, spec: ChallengeQuestion) -> Question:
        default_dimensions = self._default_dimensions_for_owner(graph, spec)
        if spec.target_dimensions and spec.target_dimension_mode == "override":
            target_dimensions = spec.target_dimensions
        elif spec.target_dimensions:
            target_dimensions = _dedupe_dimensions(default_dimensions + spec.target_dimensions)
        else:
            target_dimensions = default_dimensions
        metadata = {
            "challenge_chapter_id": graph.chapter_id,
            "expected_answer_aliases": list(spec.answer_aliases),
            **spec.validator_config,
        }
        return Question(
            id=spec.id,
            node_id=spec.node_id,
            question_type=QuestionType.DIAGNOSTIC,
            prompt=spec.prompt_markdown,
            expected_answer=spec.expected_answer,
            tested_dimensions=target_dimensions,
            solution_outline=spec.solution_outline,
            rubric=spec.rubric,
            metadata=metadata,
        )

    def _node_for_task(self, graph: ChallengeGraph, task: ChallengeTask) -> KnowledgeNode:
        if task.task_type == ChallengeTaskType.MACRO_CHALLENGE:
            macro = self._macro(graph, task.macro_node_id)
            return self._knowledge_node(macro.knowledge_node_id)
        return self._micro_node_adapter(graph, self._micro(graph, task.task_id))

    def _micro_node_adapter(self, graph: ChallengeGraph, micro: MicroNodeSpec) -> KnowledgeNode:
        dimensions = micro.default_dimensions or DEFAULT_DIMENSIONS_BY_MICRO_TYPE[micro.type]
        weight = 1 / len(dimensions)
        return KnowledgeNode(
            id=micro.id,
            name=micro.title,
            type=NODE_TYPE_BY_MICRO_TYPE[micro.type],
            status=NodeStatus.AVAILABLE,
            prerequisites=[],
            successors=[micro.macro_node_id],
            core_dimensions=dimensions,
            common_errors=[],
            description=micro.description or micro.title,
            scoring_weights={dimension: weight for dimension in dimensions},
            pass_criteria=PassCriteria(
                min_overall=70,
                min_required_dimensions={dimension: 70 for dimension in dimensions},
                max_primary_errors=0,
                allow_false_pass=False,
            ),
        )

    def _knowledge_node(self, node_id: str) -> KnowledgeNode:
        for node in load_node_catalog():
            if node.id == node_id:
                return node
        raise ChallengeEngineError(f"unknown macro KnowledgeNode: {node_id}")

    def _default_dimensions_for_owner(self, graph: ChallengeGraph, spec: ChallengeQuestion) -> list[ScoreDimension]:
        if spec.task_type == ChallengeTaskType.MICRO_NODE:
            micro = self._micro(graph, spec.owner_id)
            return micro.default_dimensions or DEFAULT_DIMENSIONS_BY_MICRO_TYPE[micro.type]
        challenge = self._challenge(graph, spec.owner_id)
        if challenge.target_dimensions:
            return challenge.target_dimensions
        dimensions: list[ScoreDimension] = []
        for micro_id in challenge.covers_micro_nodes:
            micro = self._micro(graph, micro_id)
            dimensions.extend(micro.default_dimensions or DEFAULT_DIMENSIONS_BY_MICRO_TYPE[micro.type])
        return _dedupe_dimensions(dimensions)

    def _process_with_orchestrator(self, question: Question, attempt: Attempt, node: KnowledgeNode) -> ChallengeEvaluation:
        orchestrated = LearningOrchestrator().process(question, attempt, node)
        response = {
            "scoring": {
                "score_vector": _score_vector_summary(orchestrated),
            },
            "diagnosis": {
                "pass_state": orchestrated.diagnosis_result.pass_state.value,
                "learner_explanation": orchestrated.diagnosis_result.learner_explanation,
                "ability_state": orchestrated.diagnosis_result.ability_state,
                "ability_state_label": orchestrated.diagnosis_result.ability_state_label,
                "ability_state_explanation": orchestrated.diagnosis_result.ability_state_explanation,
                "recommended_actions": [
                    action.model_dump(mode="json", exclude_none=True)
                    for action in orchestrated.diagnosis_result.recommended_actions
                ],
                "logic_insight": orchestrated.logic_insight.public_payload(),
            },
            "movement": {
                "rollback_required": bool(orchestrated.rollback_decision.rollback_nodes),
                "rollback_nodes": list(orchestrated.rollback_decision.rollback_nodes),
                "forward_allowed": bool(orchestrated.forward_decision.forward_nodes),
                "forward_nodes": list(orchestrated.forward_decision.forward_nodes),
            },
            "action": {
                "next_action_hint": orchestrated.next_action_hint,
            },
        }
        coach_payload = build_coach_output(
            {
                "question_id": question.id,
                "pass_state": response["diagnosis"]["pass_state"],
                "score_vector_summary": response["scoring"]["score_vector"],
                "learner_explanation": response["diagnosis"]["learner_explanation"],
                "ability_state": response["diagnosis"]["ability_state"],
                "ability_state_label": response["diagnosis"]["ability_state_label"],
                "ability_state_explanation": response["diagnosis"]["ability_state_explanation"],
                "recommended_actions": response["diagnosis"]["recommended_actions"],
                "logic_insight": response["diagnosis"]["logic_insight"],
                "rollback_required": response["movement"]["rollback_required"],
                "rollback_nodes": response["movement"]["rollback_nodes"],
                "forward_allowed": response["movement"]["forward_allowed"],
                "forward_nodes": response["movement"]["forward_nodes"],
                "next_action_hint": response["action"]["next_action_hint"],
                "response_evidence_present": {
                    "has_response_steps": bool(attempt.response_steps),
                    "response_step_count": len(attempt.response_steps),
                    "has_self_explanation": bool(attempt.self_explanation),
                },
                "session_log_written": False,
                "session_id": None,
            }
        )
        return ChallengeEvaluation(
            pass_state=orchestrated.diagnosis_result.pass_state,
            root_cause=orchestrated.diagnosis_result.root_cause,
            repair_target_node_id=orchestrated.logic_insight.primary_target_node_id,
            coach_payload=coach_payload,
        )

    def _status_payload(
        self,
        graph: ChallengeGraph,
        questions: ChallengeQuestionBank,
        progress: ChallengeProgress,
        *,
        progress_path: Path,
    ) -> dict[str, Any]:
        current_question = None
        if progress.current_task:
            question = self._current_question(graph, questions, progress)
            current_question = self._public_question_payload(question)
        payload = {
            "challenge": {
                "chapter_id": progress.chapter_id,
                "session_id": progress.session_id,
                "completed": progress.completed,
                "progress_path": str(progress_path),
                "network": self._public_network_payload(graph),
                "logic_overlay": self._logic_overlay_payload(graph),
                "current_task": progress.current_task.model_dump(mode="json") if progress.current_task else None,
                "current_question": current_question,
                "active_atom_hints": self._current_atom_hints(graph, progress),
                "macro_nodes": {
                    node_id: node_progress.model_dump(mode="json")
                    for node_id, node_progress in progress.macro_nodes.items()
                },
                "micro_nodes": {
                    node_id: node_progress.model_dump(mode="json")
                    for node_id, node_progress in progress.micro_nodes.items()
                },
                "macro_challenges": {
                    node_id: node_progress.model_dump(mode="json")
                    for node_id, node_progress in progress.macro_challenges.items()
                },
                "mastery": {
                    node_id: mastery.model_dump(mode="json", exclude_none=True)
                    for node_id, mastery in progress.mastery.items()
                },
            }
        }
        ensure_no_trusted_fields(payload)
        return payload

    def _public_network_payload(self, graph: ChallengeGraph) -> dict[str, Any]:
        return {
            "chapter_id": graph.chapter_id,
            "title": graph.title,
            "node_model": {
                "macro_node": "大知识节点",
                "micro_node": "可训练小能力节点",
                "atom_node": "隐藏原子前置能力，不直接作为地图关卡",
                "macro_challenge": "绑定到大节点的 Boss 综合验收任务",
                "compare_node": "相邻题型/方法的对比提醒节点",
                "guide_node": "非训练导航节点，用来表达桥接、关口、警示或 Boss 门槛",
            },
            "macro_nodes": [macro.model_dump(mode="json") for macro in graph.macro_nodes],
            "micro_nodes": [micro.model_dump(mode="json") for micro in graph.micro_nodes],
            "macro_challenges": [
                {**challenge.model_dump(mode="json"), "node_kind": "boss_challenge"}
                for challenge in graph.macro_challenges
            ],
            "atom_nodes": [atom.model_dump(mode="json") for atom in graph.atom_nodes],
            "compare_nodes": [compare.model_dump(mode="json") for compare in graph.compare_nodes],
            "guide_nodes": [guide.model_dump(mode="json") for guide in graph.guide_nodes],
            "typed_edges": [edge.model_dump(mode="json") for edge in graph.typed_edges],
        }

    def _logic_overlay_payload(self, graph: ChallengeGraph) -> dict[str, Any]:
        logic_graph = self.logic_graph_repository.try_load_graph(graph.chapter_id)
        if logic_graph is None:
            return {"active": False, "logic_nodes": [], "logic_edges": []}

        return {
            "active": True,
            "chapter_id": logic_graph.chapter_id,
            "title": logic_graph.title,
            "logic_nodes": [
                {
                    "id": ability.id,
                    "title": ability.title,
                    "node_kind": self._logic_overlay_node_kind(ability.kind, ability.role),
                    "ability_kind": ability.kind.value,
                    "role": ability.role.value,
                    "owner_node_id": ability.owner_node_id,
                    "anchor_node_id": ability.owner_node_id,
                    "repair_target_node_id": ability.repair_target_node_id,
                    "dimensions": [dimension.value for dimension in ability.dimensions],
                    "why_exists": ability.why_exists,
                    "evidence_requirements": list(ability.evidence_requirements),
                    "failure_modes": list(ability.failure_modes),
                    "repair_cues": list(ability.repair_cues),
                    "visibility_policy": ability.visibility_policy.value,
                    "trainable": False,
                }
                for ability in logic_graph.abilities
            ],
            "logic_edges": [
                {
                    "id": edge.id,
                    "edge_type": edge.edge_type.value,
                    "source_id": edge.source_id,
                    "target_id": edge.target_id,
                    "label": edge.label,
                    "reason": edge.reason,
                    "semantic_weight": edge.weight,
                    "decision_role": self._logic_overlay_edge_role(edge.edge_type),
                    "visible": True,
                }
                for edge in logic_graph.edges
            ],
        }

    def _logic_overlay_node_kind(self, kind: LogicAbilityKind, role: LogicAbilityRole) -> str:
        if role in {LogicAbilityRole.TRANSFER, LogicAbilityRole.TRANSFER_NODE}:
            return "transfer_node"
        if role in {LogicAbilityRole.SYNTHESIS, LogicAbilityRole.SYNTHESIS_NODE}:
            return "synthesis_node"
        if role == LogicAbilityRole.BOSS_CRITERION:
            return "boss_criterion"
        if role == LogicAbilityRole.CONFUSION_GUARD or kind == LogicAbilityKind.MISCONCEPTION_GUARD:
            return "compare_guard"
        return "hidden_ability"

    def _logic_overlay_edge_role(self, edge_type: LogicEdgeType) -> str:
        if edge_type == LogicEdgeType.REPAIRS:
            return "repair"
        if edge_type in {LogicEdgeType.TRANSFERS_TO, LogicEdgeType.CONTRASTS_WITH, LogicEdgeType.COMMONLY_CONFUSED_WITH}:
            return "advisory"
        if edge_type == LogicEdgeType.BLOCKS:
            return "progression"
        return "diagnostic"

    def _current_atom_hints(self, graph: ChallengeGraph, progress: ChallengeProgress) -> list[dict[str, Any]]:
        if progress.current_task is None or progress.current_task.task_type != ChallengeTaskType.MICRO_NODE:
            return []
        micro_id = progress.current_task.task_id
        mastery = progress.mastery.get(micro_id)
        repair_focus = bool(mastery and mastery.recent_root_causes)
        hints: list[dict[str, Any]] = []
        for atom in graph.atom_nodes:
            if atom.micro_node_id != micro_id:
                continue
            payload = atom.model_dump(mode="json")
            payload["repair_focus"] = repair_focus
            hints.append(payload)
        return hints

    def _update_mastery_from_evaluation(
        self,
        graph: ChallengeGraph,
        progress: ChallengeProgress,
        task: ChallengeTask,
        evaluation: ChallengeEvaluation,
    ) -> None:
        weak_dimensions = self._weak_dimensions_from_evaluation(evaluation)
        if task.task_type == ChallengeTaskType.MICRO_NODE:
            self._apply_mastery_delta(
                progress,
                task.task_id,
                evaluation.pass_state,
                evaluation.root_cause,
                weak_dimensions,
                passed_floor=72,
            )
            return

        macro_id = task.macro_node_id
        self._apply_mastery_delta(
            progress,
            macro_id,
            evaluation.pass_state,
            evaluation.root_cause,
            weak_dimensions,
            passed_floor=84,
        )
        if evaluation.pass_state != PassState.PASS:
            target_micro_id = self._target_micro_for_evaluation(graph, macro_id, evaluation)
            self._apply_mastery_delta(
                progress,
                target_micro_id,
                evaluation.pass_state,
                evaluation.root_cause,
                weak_dimensions or self._dimensions_for_micro(graph, target_micro_id),
                passed_floor=72,
                repair_penalty=True,
            )

    def _apply_mastery_delta(
        self,
        progress: ChallengeProgress,
        node_id: str,
        pass_state: PassState,
        root_cause: ErrorType | None,
        weak_dimensions: list[ScoreDimension],
        *,
        passed_floor: float,
        repair_penalty: bool = False,
    ) -> None:
        mastery = progress.mastery.setdefault(node_id, ChallengeMasteryState())
        mastery.evidence_count += 1
        mastery.last_pass_state = pass_state
        if root_cause is not None:
            mastery.recent_root_causes = _append_recent(mastery.recent_root_causes, root_cause, limit=4)
        if weak_dimensions:
            mastery.weak_dimensions = _dedupe_dimensions([*weak_dimensions, *mastery.weak_dimensions])[:5]

        if pass_state == PassState.PASS:
            mastery.mastery_score = min(100, max(passed_floor, mastery.mastery_score + 18))
            mastery.confidence = min(1, mastery.confidence + 0.16)
            mastery.stability = min(1, mastery.stability + 0.14)
            if mastery.stability >= 0.45:
                mastery.weak_dimensions = []
                mastery.recent_root_causes = []
            return

        if pass_state == PassState.PARTIAL_PASS:
            mastery.mastery_score = min(100, max(35, mastery.mastery_score + 4))
            mastery.confidence = min(1, mastery.confidence + 0.08)
            mastery.stability = max(0, mastery.stability - 0.06)
            return

        penalty = 16 if pass_state == PassState.FAIL else 10
        if repair_penalty:
            penalty += 6
        mastery.mastery_score = max(0, mastery.mastery_score - penalty)
        mastery.confidence = min(1, mastery.confidence + 0.1)
        mastery.stability = max(0, mastery.stability - 0.12)

    def _weak_dimensions_from_evaluation(self, evaluation: ChallengeEvaluation) -> list[ScoreDimension]:
        score_summary = evaluation.coach_payload.get("score_vector_summary", {})
        weak: list[ScoreDimension] = []
        if isinstance(score_summary, dict):
            for raw_dimension, value in score_summary.items():
                if not isinstance(value, dict) or value.get("score") is None:
                    continue
                try:
                    dimension = ScoreDimension(raw_dimension)
                except ValueError:
                    continue
                if float(value["score"]) < 70:
                    weak.append(dimension)
        if weak:
            return _dedupe_dimensions(weak)
        if evaluation.root_cause is None:
            return []
        return ROOT_CAUSE_DIMENSIONS.get(evaluation.root_cause, [])

    def _dimensions_for_micro(self, graph: ChallengeGraph, micro_id: str) -> list[ScoreDimension]:
        micro = self._micro(graph, micro_id)
        return micro.default_dimensions or DEFAULT_DIMENSIONS_BY_MICRO_TYPE[micro.type]

    def _refresh_mastery_visuals(self, progress: ChallengeProgress) -> None:
        for node_id, node_progress in {**progress.macro_nodes, **progress.micro_nodes}.items():
            mastery = progress.mastery.setdefault(node_id, ChallengeMasteryState())
            mastery.visual_state = self._visual_state_for(node_progress.status, mastery)

    def _visual_state_for(self, status: ChallengeStatus, mastery: ChallengeMasteryState) -> str:
        if status == ChallengeStatus.LOCKED:
            return "locked"
        if status == ChallengeStatus.FAILED:
            return "failed"
        if status == ChallengeStatus.ACTIVE and mastery.recent_root_causes:
            return "repair"
        if status == ChallengeStatus.ACTIVE:
            return "active"
        if status == ChallengeStatus.AVAILABLE:
            return "available"
        if status == ChallengeStatus.MASTERED:
            if mastery.mastery_score >= 88 and mastery.confidence >= 0.45 and mastery.stability >= 0.4:
                return "stable_mastery"
            return "lit_unstable"
        return status.value

    def _public_question_payload(self, question: ChallengeQuestion) -> dict[str, Any]:
        return {
            "question_id": question.id,
            "node_id": question.node_id,
            "title": question.title,
            "stem": question.stem,
            "prompt_markdown": question.prompt_markdown,
            "answer_format": question.answer_format,
            "response_step_mode": question.response_step_mode,
            "difficulty": question.difficulty,
            "hints_public": list(question.hints_public),
        }

    def _apply_challenge_coach_overlay(
        self,
        payload: dict[str, Any],
        task: ChallengeTask,
        evaluation: ChallengeEvaluation,
    ) -> None:
        challenge = payload.get("challenge", {})
        current_task = challenge.get("current_task")
        if evaluation.pass_state == PassState.PASS:
            if task.task_type == ChallengeTaskType.MICRO_NODE:
                payload["progression_advice"] = "已点亮当前小节点，继续挑战地图上高亮的下一个节点。"
                payload["next_step_plan"] = "点击当前高亮节点继续训练；这个点已进入掌握地图，但还需要后续证据确认稳定。"
            else:
                payload["progression_advice"] = "综合验收通过，大节点已点亮；后继节点会按知识网解锁。"
                payload["next_step_plan"] = "继续沿地图挑战新解锁的节点，必要时回看掌握度较低的分支。"
            return

        if task.task_type == ChallengeTaskType.MICRO_NODE:
            payload["progression_advice"] = "本小节点未通过，会保留在当前节点继续练；小节点失败不触发回溯。"
            atom_hints = challenge.get("active_atom_hints") or []
            if atom_hints:
                first_hint = atom_hints[0].get("title", "原子前置能力")
                payload["next_step_plan"] = f"继续做当前高亮小节点的新题；先盯住「{first_hint}」这个前置能力。"
            else:
                payload["next_step_plan"] = "继续做当前高亮小节点的新题，直到本节点点亮。"
            return

        if current_task and current_task.get("task_type") == ChallengeTaskType.MICRO_NODE:
            payload["progression_advice"] = "综合验收未通过，系统按根因只回到一个目标小节点修复。"
            payload["next_step_plan"] = "先完成地图上高亮的修复小节点，再回到大节点综合验收。"
            return

        payload["progression_advice"] = "综合验收机会已耗尽，大节点已标记失败，需要重置后再挑战。"
        payload["next_step_plan"] = "重置该闯关进度后，从该大节点的小节点重新建立证据。"

    def _session_log_record(
        self,
        *,
        session_id: str,
        task: ChallengeTask,
        question: ChallengeQuestion,
        answer: str,
        steps: list[str],
        explanation: str | None,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": session_id,
            "challenge_chapter_id": payload["challenge"]["chapter_id"],
            "challenge_task_type": task.task_type.value,
            "challenge_task_id": task.task_id,
            "macro_node_id": task.macro_node_id,
            "question_id": question.id,
            "node_id": question.node_id,
            "user_answer": answer,
            "response_steps": steps,
            "self_explanation": explanation,
            "pass_state": payload.get("pass_state"),
            "root_cause": payload.get("challenge_attempt", {}).get("root_cause"),
            "challenge": payload.get("challenge"),
            "coach_summary": payload.get("coach_summary"),
            "status_label": payload.get("status_label"),
            "progression_advice": payload.get("progression_advice"),
            "evidence_gaps": payload.get("evidence_gaps"),
            "friendly_score_summary": payload.get("friendly_score_summary"),
            "next_step_plan": payload.get("next_step_plan"),
            "logic_insight": payload.get("logic_insight"),
        }
        ensure_no_trusted_fields(record)
        return record

    def _macro(self, graph: ChallengeGraph, macro_id: str):
        for macro in graph.macro_nodes:
            if macro.id == macro_id:
                return macro
        raise ChallengeEngineError(f"unknown macro node: {macro_id}")

    def _micro(self, graph: ChallengeGraph, micro_id: str) -> MicroNodeSpec:
        for micro in graph.micro_nodes:
            if micro.id == micro_id:
                return micro
        raise ChallengeEngineError(f"unknown micro node: {micro_id}")

    def _challenge(self, graph: ChallengeGraph, challenge_id: str):
        for challenge in graph.macro_challenges:
            if challenge.id == challenge_id:
                return challenge
        raise ChallengeEngineError(f"unknown macro challenge: {challenge_id}")

    def _challenge_for_macro(self, graph: ChallengeGraph, macro_id: str):
        for challenge in graph.macro_challenges:
            if challenge.macro_node_id == macro_id:
                return challenge
        raise ChallengeEngineError(f"macro node has no macro challenge: {macro_id}")

    def _micro_nodes_for_macro(self, graph: ChallengeGraph, macro_id: str) -> list[MicroNodeSpec]:
        contained = set(graph.contains.get(macro_id, []))
        return [micro for micro in graph.micro_nodes if micro.id in contained]

    def _question_by_id(self, questions: ChallengeQuestionBank, question_id: str) -> ChallengeQuestion:
        for question in questions.questions:
            if question.id == question_id:
                return question
        raise ChallengeEngineError(f"unknown challenge question: {question_id}")


def _dedupe_dimensions(dimensions: list[ScoreDimension]) -> list[ScoreDimension]:
    seen: set[ScoreDimension] = set()
    deduped: list[ScoreDimension] = []
    for dimension in dimensions:
        if dimension not in seen:
            seen.add(dimension)
            deduped.append(dimension)
    return deduped


def _append_recent(values: list[ErrorType], value: ErrorType, *, limit: int) -> list[ErrorType]:
    return [value, *[item for item in values if item != value]][:limit]


def _score_vector_summary(orchestrated: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for dimension, dimension_score in orchestrated.score_result.score_vector.as_dimension_map().items():
        if dimension_score is None or dimension_score.score is None:
            summary[dimension.value] = None
            continue
        payload: dict[str, Any] = {"score": dimension_score.score}
        if dimension_score.notes:
            payload["notes"] = dimension_score.notes
        summary[dimension.value] = payload
    return summary
