from __future__ import annotations

from typing import Any

from app.api.v1.schemas import action_payloads, score_vector_summary
from app.core.schemas import Attempt


class LearnerAttemptAssembler:
    """Create a domain Attempt from learner-safe fields only."""

    def to_attempt(
        self,
        *,
        question_id: str,
        user_answer: str,
        response_steps: list[str] | None = None,
        self_explanation: str | None = None,
    ) -> Attempt:
        return Attempt(
            id=f"learner_attempt_{question_id}",
            question_id=question_id,
            user_answer=user_answer,
            response_steps=response_steps or [],
            self_explanation=self_explanation,
            metadata={},
        )


class LearnerResponseProjector:
    """Project orchestrated engine output to the learner-safe public contract."""

    def from_orchestrated(self, orchestrated: Any) -> dict[str, Any]:
        diagnosis = orchestrated.diagnosis_result
        rollback = orchestrated.rollback_decision
        forward = orchestrated.forward_decision
        return {
            "scoring": {
                "score_vector": score_vector_summary(orchestrated.score_result),
            },
            "diagnosis": {
                "pass_state": diagnosis.pass_state.value,
                "learner_explanation": diagnosis.learner_explanation,
                "recommended_actions": action_payloads(diagnosis.recommended_actions),
            },
            "movement": {
                "rollback_required": bool(rollback.rollback_nodes),
                "rollback_nodes": list(rollback.rollback_nodes),
                "forward_allowed": bool(forward.forward_nodes),
                "forward_nodes": list(forward.forward_nodes),
            },
            "action": {
                "next_action_hint": orchestrated.next_action_hint,
            },
        }

