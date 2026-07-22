from __future__ import annotations

import hmac
from typing import Any

from app.classroom.runtime import ClassroomRuntimeService
from app.classroom.session_models import (
    BaselineStepSnapshot,
    LearningSession,
    LearningSessionAccess,
    LearningSessionEvent,
    ScenePatch,
)
from app.classroom.session_repository import (
    LearningSessionConflictError,
    LearningSessionRepository,
    LearningSessionRepositoryError,
)


class LearningSessionAccessError(LearningSessionRepositoryError):
    pass


class LearningSessionService:
    def __init__(
        self,
        repository: LearningSessionRepository,
        runtime: ClassroomRuntimeService,
    ) -> None:
        self.repository = repository
        self.runtime = runtime

    def create(
        self,
        *,
        package_id: str,
        module_id: str,
    ) -> LearningSessionAccess:
        module_payload = self.runtime.module(package_id, module_id)
        baseline_steps = self._project_baseline_steps(module_payload["module"])
        return self.repository.create(
            package_id=package_id,
            release_version=module_payload["version"],
            module_id=module_id,
            baseline_steps=baseline_steps,
        )

    def get_for_learner(
        self,
        session_id: str,
        *,
        access_token: str,
    ) -> LearningSession:
        stored = self.repository.get(session_id)
        supplied_hash = self.repository.hash_access_token(access_token)
        if not hmac.compare_digest(supplied_hash, stored.access_token_hash):
            raise LearningSessionAccessError("invalid learning session access token")
        return stored.session

    def get_for_studio(self, session_id: str) -> LearningSession:
        return self.repository.get(session_id).session

    def reveal(
        self,
        session_id: str,
        *,
        access_token: str,
        expected_revision: int,
    ) -> LearningSession:
        self.get_for_learner(session_id, access_token=access_token)
        return self.repository.reveal(
            session_id,
            expected_revision=expected_revision,
        )

    def set_active_content(
        self,
        session_id: str,
        *,
        access_token: str,
        expected_revision: int,
        content_id: str,
    ) -> LearningSession:
        self.get_for_learner(session_id, access_token=access_token)
        revision = expected_revision
        conflict: LearningSessionConflictError | None = None
        for _ in range(3):
            try:
                return self.repository.set_active_content(
                    session_id,
                    expected_revision=revision,
                    content_id=content_id,
                )
            except LearningSessionConflictError as exc:
                conflict = exc
                revision = self.repository.get(session_id).session.revision
        assert conflict is not None
        raise conflict

    def events(
        self,
        session_id: str,
        *,
        access_token: str,
        after_revision: int,
    ) -> list[LearningSessionEvent]:
        self.get_for_learner(session_id, access_token=access_token)
        return self.repository.events_after(
            session_id,
            revision=after_revision,
        )

    def list_for_studio(self, *, limit: int = 20) -> dict[str, Any]:
        sessions = self.repository.list_recent(limit=limit)
        return {
            "sessions": [
                {
                    "session_id": session.session_id,
                    "package_id": session.package_id,
                    "release_version": session.release_version,
                    "module_id": session.module_id,
                    "revision": session.revision,
                    "active_content_id": session.active_content_id,
                    "active_expansion_id": (
                        session.expansion_stack[-1]
                        if session.expansion_stack
                        else None
                    ),
                    "updated_at": session.updated_at,
                    "recommended_for_update": index == 0,
                    "selection_reason": (
                        "most_recently_active" if index == 0 else "older_session"
                    ),
                }
                for index, session in enumerate(sessions)
            ],
            "selection_policy": (
                "Use the single recommended session. If no session is "
                "recommended, create or ask to start learning before patching."
            ),
        }

    def patch(
        self,
        session_id: str,
        patch: ScenePatch,
        *,
        idempotency_key: str,
    ) -> LearningSession:
        return self.repository.apply_patch(
            session_id,
            patch,
            idempotency_key=idempotency_key,
        )

    def return_to_parent(
        self,
        session_id: str,
        *,
        expected_revision: int,
        idempotency_key: str,
    ) -> LearningSession:
        return self.repository.return_to_parent(
            session_id,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
        )

    def return_for_learner(
        self,
        session_id: str,
        *,
        access_token: str,
        expected_revision: int,
        idempotency_key: str,
    ) -> LearningSession:
        self.get_for_learner(session_id, access_token=access_token)
        return self.return_to_parent(
            session_id,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
        )

    @classmethod
    def _project_baseline_steps(
        cls,
        module: dict[str, Any],
    ) -> list[BaselineStepSnapshot]:
        steps: list[BaselineStepSnapshot] = []
        for block in module.get("blocks", []):
            steps.append(
                BaselineStepSnapshot(
                    id=block["id"],
                    title=cls._block_title(block),
                    blocks=[block],
                )
            )
        for segment in module.get("segments", []):
            steps.append(
                BaselineStepSnapshot(
                    id=segment["id"],
                    title=segment.get("title") or "继续建立完整模型",
                    question_answered=segment.get("question_answered"),
                    bridge_from_previous=segment.get("bridge_from_previous"),
                    mechanism=segment.get("mechanism"),
                    entry_assumptions=segment.get("entry_assumptions") or [],
                    exit_understanding=segment.get("exit_understanding"),
                    knowledge_point_ids=segment.get("knowledge_point_ids") or [],
                    blocks=segment["blocks"],
                )
            )
        if not steps:
            raise ValueError("core module has no baseline learning content")
        return steps

    @staticmethod
    def _block_title(block: dict[str, Any]) -> str:
        data = block.get("data") or {}
        for key in ("title", "prompt", "text", "markdown", "explanation"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                compact = " ".join(value.strip().split())
                return compact[:80]
        labels = {
            "formula_explanation": "把公式接回它表达的机制",
            "math": "观察数学关系",
            "derivation": "逐步建立推导",
            "comparison": "对比两个容易混淆的对象",
            "worked_example": "用完整例子落地",
            "model_reference": "在教学模型中观察",
        }
        return labels.get(block.get("kind"), "继续建立核心模型")
