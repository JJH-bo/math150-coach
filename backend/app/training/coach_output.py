from __future__ import annotations

from copy import deepcopy
from typing import Any


RAW_SCORER_NAME_REPLACEMENTS = {
    "RubricScorer": "题目评分规则",
    "MathValidatorScorer": "答案/计算校验",
    "RuleScorer": "关键词/结构信号",
}

STATUS_LABELS = {
    "pass": "稳定通过",
    "fail": "未通过",
    "false_pass": "疑似会做但证据不足",
    "partial_pass": "部分通过",
    "need_more_evidence": "证据不足",
}

DIMENSION_LABELS = {
    "concept": "概念理解",
    "trigger": "题眼识别",
    "method": "方法选择",
    "transformation": "条件转化",
    "process": "过程完整性",
    "calculation": "计算执行",
    "final_answer": "最终答案",
    "expression": "表达严谨性",
    "migration": "变式迁移",
}

MISSING_GAP_MESSAGES = {
    "process": "请写出关键步骤，而不是只给结论。",
    "concept": "请说明为什么本题适用该方法。",
    "expression": "请规范写出通解形式、任意常数和必要说明。",
}

LOW_GAP_MESSAGES = {
    "transformation": "请补条件转化/标准形过程。",
    "trigger": "请补题眼识别依据。",
    "method": "请说明方法选择依据。",
    "calculation": "请检查计算链条。",
    "final_answer": "请检查最终结果形式。",
    "concept": "请补充概念依据。",
    "process": "请补全关键过程。",
    "expression": "请加强表达严谨性。",
    "migration": "请补充变式迁移证据。",
}

UNSCORED_DIMENSION_MESSAGES = {
    "concept": "当前评分还没有对【概念理解】形成单独分数；这不等于你没有写概念说明，而是本题当前评分维度尚未覆盖它。",
    "process": "你已经提交了步骤/解释，但当前评分还没有把这部分转成【过程完整性】分数；这不等于你没有写过程。",
    "expression": "当前评分还没有对【表达严谨性】形成单独分数；需要后续评分规则补充后才能判断。",
    "migration": "当前单题没有对【变式迁移】形成分数；这不是本次必须补写的内容。",
}

NEXT_STEP_BY_ACTION = {
    "need_more_evidence": "补写题眼、方法依据和关键过程，然后再提交一次同题或同节点题。",
    "transformation_drill": "先练条件转化，把原式一步步化成标准形，并说明每一步为什么等价。",
    "trigger_drill": "先做题眼识别训练，说明为什么题目指向当前节点。",
    "method_comparison": "先做方法对比训练，写清楚为什么选这个方法而不是相邻方法。",
    "calculation_repair": "先修复局部计算链条，逐步检查变形、积分和常数处理。",
    "condition_check": "先列出题目条件清单，确认初值、边界条件或限制条件没有遗漏。",
    "expression_rewrite": "先重写表达，补齐通解形式、任意常数和必要说明。",
    "variant_training": "先做同节点变式训练，确认方法不是只对当前题偶然有效。",
    "current_node_review": "先复盘当前节点，把题眼、方法和关键步骤补完整。",
    "chapter_framework_review": "先做章节框架复盘，对比相邻知识点和题型入口。",
}


def build_coach_output(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a learner-facing copy of a Local Trainer submit payload."""

    projected = deepcopy(payload)
    projected["response_evidence_present"] = normalize_response_evidence_present(
        projected.get("response_evidence_present")
    )
    projected["score_vector_summary"] = sanitize_score_vector_summary(
        projected.get("score_vector_summary", {})
    )
    projected["status_label"] = build_status_label(projected.get("pass_state"))
    projected["unscored_dimensions"] = build_unscored_dimensions(
        projected.get("score_vector_summary", {}),
        projected.get("response_evidence_present", {}),
    )
    projected["evidence_gaps"] = build_evidence_gaps(
        projected.get("score_vector_summary", {}),
        projected.get("response_evidence_present", {}),
    )
    projected["friendly_score_summary"] = build_friendly_score_summary(
        projected.get("score_vector_summary", {}),
        projected.get("response_evidence_present", {}),
    )
    projected["progression_advice"] = build_progression_advice(projected)
    projected["next_step_plan"] = build_next_step_plan(projected)
    projected["coach_summary"] = build_coach_summary(projected)
    return projected


def sanitize_score_vector_summary(score_vector_summary: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}
    for dimension, value in (score_vector_summary or {}).items():
        if value is None:
            sanitized[dimension] = None
            continue
        if not isinstance(value, dict):
            sanitized[dimension] = value
            continue
        clean_value = dict(value)
        if clean_value.get("notes"):
            clean_value["notes"] = _sanitize_note(str(clean_value["notes"]))
        sanitized[dimension] = clean_value
    return sanitized


def build_friendly_score_summary(
    score_vector_summary: dict[str, Any],
    response_evidence_present: dict[str, Any] | None = None,
) -> dict[str, Any]:
    friendly: dict[str, Any] = {}
    response_evidence = normalize_response_evidence_present(response_evidence_present)
    for dimension, value in (score_vector_summary or {}).items():
        label = DIMENSION_LABELS.get(dimension, dimension)
        if value is None or not isinstance(value, dict) or value.get("score") is None:
            if _is_unscored_dimension(dimension, response_evidence):
                friendly[dimension] = {
                    "label": label,
                    "score": None,
                    "status": "当前未评分",
                    "comment": UNSCORED_DIMENSION_MESSAGES.get(
                        dimension,
                        f"{label}当前没有形成单独分数；这不等于学习者没有提交相关内容。",
                    ),
                }
                continue
            friendly[dimension] = {
                "label": label,
                "score": None,
                "status": "缺少证据",
                "comment": MISSING_GAP_MESSAGES.get(dimension, f"{label}暂未形成有效证据。"),
            }
            continue
        score = float(value["score"])
        friendly[dimension] = {
            "label": label,
            "score": score,
            "status": _score_status(score),
            "comment": _score_comment(dimension, score),
        }
    return friendly


def build_status_label(pass_state: str | None) -> str:
    return STATUS_LABELS.get(pass_state or "", "状态不明确")


def build_progression_advice(payload: dict[str, Any]) -> str:
    pass_state = payload.get("pass_state")
    rollback_required = bool(payload.get("rollback_required"))
    forward_allowed = bool(payload.get("forward_allowed"))

    if rollback_required:
        return "先修复当前节点，不建议推进。"
    if pass_state == "false_pass" and forward_allowed:
        return "允许弱推进/预备推进，但不能视为稳定掌握；优先补同节点证据。"
    if forward_allowed and pass_state == "pass":
        return "可以推进，但仍建议保留一次复刷记录确认稳定性。"
    if not forward_allowed:
        return "不建议推进，先完成当前节点训练。"
    if pass_state == "fail":
        return "当前未通过，不能包装成通过。"
    return "请根据下一步计划补齐当前证据。"


def build_evidence_gaps(
    score_vector_summary: dict[str, Any],
    response_evidence_present: dict[str, Any] | None = None,
) -> list[str]:
    gaps: list[str] = []
    response_evidence = normalize_response_evidence_present(response_evidence_present)
    for dimension, value in (score_vector_summary or {}).items():
        if value is None or not isinstance(value, dict) or value.get("score") is None:
            if _is_unscored_dimension(dimension, response_evidence):
                continue
            message = MISSING_GAP_MESSAGES.get(dimension)
            if message:
                gaps.append(message)
            continue
        score = float(value["score"])
        if score < 60:
            gaps.append(LOW_GAP_MESSAGES.get(dimension, f"{DIMENSION_LABELS.get(dimension, dimension)}明显薄弱。"))
        elif score < 80:
            gaps.append(f"{LOW_GAP_MESSAGES.get(dimension, DIMENSION_LABELS.get(dimension, dimension) + '需要补强。')} 当前证据还不够稳。")
    return gaps


def build_unscored_dimensions(
    score_vector_summary: dict[str, Any],
    response_evidence_present: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    response_evidence = normalize_response_evidence_present(response_evidence_present)
    unscored: list[dict[str, Any]] = []
    for dimension, value in (score_vector_summary or {}).items():
        if value is not None and isinstance(value, dict) and value.get("score") is not None:
            continue
        if not _is_unscored_dimension(dimension, response_evidence):
            continue
        unscored.append(
            {
                "dimension": dimension,
                "label": DIMENSION_LABELS.get(dimension, dimension),
                "reason": UNSCORED_DIMENSION_MESSAGES.get(
                    dimension,
                    f"{DIMENSION_LABELS.get(dimension, dimension)}当前没有形成单独分数；这不等于学习者没有提交相关内容。",
                ),
            }
        )
    return unscored


def build_next_step_plan(payload: dict[str, Any]) -> str:
    actions = payload.get("recommended_actions") or []
    action_type = None
    if actions and isinstance(actions[0], dict):
        action_type = actions[0].get("action_type")
    if action_type == "need_more_evidence" and _has_response_evidence(payload.get("response_evidence_present")):
        return "你已经提交步骤和解释；下一步不是简单重复写步骤，而是做同节点诊断题，确认题眼、方法依据和关键过程能稳定复现。"
    if action_type in NEXT_STEP_BY_ACTION:
        return NEXT_STEP_BY_ACTION[action_type]
    hint = payload.get("next_action_hint")
    if hint:
        return f"按下一步提示完成当前训练：{hint}"
    return "先补齐题眼、方法依据和关键过程，再进行下一次提交。"


def build_coach_summary(payload: dict[str, Any]) -> str:
    pass_state = payload.get("pass_state")
    actions = payload.get("recommended_actions") or []
    action_type = actions[0].get("action_type") if actions and isinstance(actions[0], dict) else None
    forward_allowed = bool(payload.get("forward_allowed"))

    if pass_state == "false_pass":
        if _has_response_evidence(payload.get("response_evidence_present")):
            return "这题方向和主要步骤已有可用信号，但当前评分规则尚未对部分过程/概念/表达维度形成分数，所以仍不能认为稳定掌握。优先做同节点诊断题或补充可评分证据。"
        if forward_allowed:
            return "这题方向基本正确，但还不能算稳定掌握，因为关键过程证据不足；可以弱推进预览后续，但优先补完整步骤。"
        return "这题看起来有部分正确信号，但证据不足，先补题眼、方法依据和关键过程。"
    if action_type == "transformation_drill":
        return "这题主要卡在条件转化/标准形处理，先不要推进，先把原式如何一步步变形写清楚。"
    if action_type == "trigger_drill":
        return "这题首先是题眼识别失败。你没有看出它指向当前方法，先回到题型识别训练。"
    if pass_state == "pass":
        return "这题已基本通过，可以推进，但建议保留一次复刷确认稳定性。"
    if pass_state == "fail":
        return "这题当前未通过，先按下一步计划修复当前节点的关键证据。"
    return "当前状态还不明确，先补充完整过程和方法依据。"


def normalize_response_evidence_present(value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {
            "has_response_steps": False,
            "response_step_count": 0,
            "has_self_explanation": False,
        }
    step_count = value.get("response_step_count", 0)
    if not isinstance(step_count, int):
        step_count = 0
    step_count = max(step_count, 0)
    return {
        "has_response_steps": bool(value.get("has_response_steps")) or step_count > 0,
        "response_step_count": step_count,
        "has_self_explanation": bool(value.get("has_self_explanation")),
    }


def _has_response_evidence(value: dict[str, Any] | None) -> bool:
    normalized = normalize_response_evidence_present(value)
    return normalized["has_response_steps"] or normalized["has_self_explanation"]


def _is_unscored_dimension(dimension: str, response_evidence_present: dict[str, Any]) -> bool:
    if dimension == "migration":
        return True
    if dimension in {"concept", "process", "expression"}:
        return _has_response_evidence(response_evidence_present)
    return False


def _sanitize_note(note: str) -> str:
    sanitized = note
    for raw, friendly in RAW_SCORER_NAME_REPLACEMENTS.items():
        sanitized = sanitized.replace(raw, friendly)
    sanitized = sanitized.replace("Merged by confidence from", "综合依据")
    sanitized = sanitized.replace("['", "").replace("']", "").replace("', '", "、")
    sanitized = sanitized.replace("[", "").replace("]", "")
    return sanitized


def _score_status(score: float) -> str:
    if score >= 85:
        return "较强"
    if score >= 80:
        return "基本可用"
    if score >= 60:
        return "需要补强"
    return "薄弱"


def _score_comment(dimension: str, score: float) -> str:
    label = DIMENSION_LABELS.get(dimension, dimension)
    if score >= 85:
        return f"{label}证据较强。"
    if score >= 80:
        return f"{label}基本可用，但还可以更稳。"
    if score >= 60:
        return LOW_GAP_MESSAGES.get(dimension, f"{label}需要补强。")
    return LOW_GAP_MESSAGES.get(dimension, f"{label}明显薄弱。")
