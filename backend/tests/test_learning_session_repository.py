from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.classroom.session_models import (
    BaselineStepSnapshot,
    DetailedExpansion,
    ExpansionRepresentation,
    ScenePatch,
)
from app.classroom.session_repository import (
    LearningSessionConflictError,
    LearningSessionRepository,
)


def baseline_steps() -> list[BaselineStepSnapshot]:
    return [
        BaselineStepSnapshot(
            id="frequency-intuition",
            title="不同频率是不同方向",
            blocks=[
                {
                    "id": "frequency-intuition-text",
                    "kind": "prose",
                    "data": {"markdown": "先建立频率方向的直觉。"},
                }
            ],
        ),
        BaselineStepSnapshot(
            id="orthogonality",
            title="积分为什么能筛选频率",
            blocks=[
                {
                    "id": "orthogonality-formula",
                    "kind": "formula_explanation",
                    "data": {
                        "latex": r"\int_{-\pi}^{\pi}\sin(mx)\sin(nx)\,dx=0",
                        "explanation": "不同频率的正负面积抵消。",
                    },
                }
            ],
        ),
    ]


def expansion(
    *,
    expansion_id: str = "why-cancel",
    parent_content_id: str = "orthogonality-formula",
    parent_expansion_id: str | None = None,
) -> DetailedExpansion:
    return DetailedExpansion(
        id=expansion_id,
        title="为什么正负面积会抵消",
        parent_content_id=parent_content_id,
        parent_expansion_id=parent_expansion_id,
        learner_question="为什么不同频率一定抵消？",
        preserved_context=["不同频率代表不同方向"],
        focus_relation="异频乘积在完整周期上的正负面积配对",
        representation=ExpansionRepresentation.ANIMATED_VISUAL,
        blocks=[
            {
                "id": f"{expansion_id}-bridge",
                "kind": "prose",
                "data": {"markdown": "先把一个完整周期分成成对的小区间。"},
            }
        ],
        return_connection="面积抵消就是正交积分等于零的几何含义。",
    )


def test_session_starts_with_only_first_baseline_step_revealed(tmp_path) -> None:
    repository = LearningSessionRepository(tmp_path / "sessions.sqlite3")

    access = repository.create(
        package_id="fourier-series",
        release_version="r-123",
        module_id="fourier-coefficients",
        baseline_steps=baseline_steps(),
    )

    assert access.access_token
    assert access.session.revision == 1
    assert access.session.revealed_step_ids == ["frequency-intuition"]
    assert access.session.active_content_id == "frequency-intuition-text"
    assert repository.get(access.session.session_id).access_token_hash != (
        access.access_token
    )


def test_reveal_advances_fixed_baseline_without_generating_content(tmp_path) -> None:
    repository = LearningSessionRepository(tmp_path / "sessions.sqlite3")
    session = repository.create(
        package_id="fourier-series",
        release_version="r-123",
        module_id="fourier-coefficients",
        baseline_steps=baseline_steps(),
    ).session

    revealed = repository.reveal(
        session.session_id,
        expected_revision=1,
    )

    assert revealed.revision == 2
    assert revealed.revealed_step_ids == ["frequency-intuition", "orthogonality"]
    assert revealed.active_content_id == "orthogonality-formula"
    assert revealed.expansions == []


def test_patch_inserts_expansion_at_exact_active_content_target(tmp_path) -> None:
    repository = LearningSessionRepository(tmp_path / "sessions.sqlite3")
    session = repository.create(
        package_id="fourier-series",
        release_version="r-123",
        module_id="fourier-coefficients",
        baseline_steps=baseline_steps(),
    ).session
    session = repository.reveal(session.session_id, expected_revision=1)

    patched = repository.apply_patch(
        session.session_id,
        ScenePatch(
            expected_revision=2,
            pedagogical_intent="把抽象正交性换成面积抵消动画。",
            expansion=expansion(),
        ),
        idempotency_key="patch-1",
    )

    assert patched.revision == 3
    assert patched.expansions[0].parent_content_id == "orthogonality-formula"
    assert patched.expansion_stack == ["why-cancel"]
    assert patched.active_content_id == "why-cancel-bridge"


def test_patch_rejects_wrong_target_and_stale_revision(tmp_path) -> None:
    repository = LearningSessionRepository(tmp_path / "sessions.sqlite3")
    session = repository.create(
        package_id="fourier-series",
        release_version="r-123",
        module_id="fourier-coefficients",
        baseline_steps=baseline_steps(),
    ).session

    with pytest.raises(ValueError, match="not present in the revealed scene"):
        repository.apply_patch(
            session.session_id,
            ScenePatch(
                expected_revision=1,
                pedagogical_intent="错误目标必须被拒绝。",
                expansion=expansion(parent_content_id="orthogonality-formula"),
            ),
            idempotency_key="hidden-target",
        )

    with pytest.raises(LearningSessionConflictError, match="expected revision 9"):
        repository.reveal(session.session_id, expected_revision=9)


def test_patch_retry_is_idempotent_and_nested_expansion_can_return(tmp_path) -> None:
    repository = LearningSessionRepository(tmp_path / "sessions.sqlite3")
    session = repository.create(
        package_id="fourier-series",
        release_version="r-123",
        module_id="fourier-coefficients",
        baseline_steps=baseline_steps(),
    ).session
    session = repository.reveal(session.session_id, expected_revision=1)
    first_patch = ScenePatch(
        expected_revision=2,
        pedagogical_intent="解释面积抵消。",
        expansion=expansion(),
    )
    first = repository.apply_patch(
        session.session_id,
        first_patch,
        idempotency_key="same-patch",
    )
    retried = repository.apply_patch(
        session.session_id,
        first_patch,
        idempotency_key="same-patch",
    )

    assert retried == first

    nested = repository.apply_patch(
        session.session_id,
        ScenePatch(
            expected_revision=3,
            pedagogical_intent="把周期切分再缩小一层。",
            expansion=expansion(
                expansion_id="paired-intervals",
                parent_content_id="why-cancel-bridge",
                parent_expansion_id="why-cancel",
            ),
        ),
        idempotency_key="nested-patch",
    )
    returned = repository.return_to_parent(
        session.session_id,
        expected_revision=4,
        idempotency_key="return-one",
    )

    assert nested.expansion_stack == ["why-cancel", "paired-intervals"]
    assert returned.expansion_stack == ["why-cancel"]
    assert returned.active_content_id == "why-cancel-bridge"


def test_session_models_reject_learner_analysis_fields() -> None:
    payload = expansion().model_dump(mode="json")
    payload["blocks"][0]["data"]["mastery_state"] = 0.8

    with pytest.raises(ValidationError, match="mastery_state"):
        DetailedExpansion.model_validate(payload)
