from __future__ import annotations

import re
from typing import Any

from app.challenge.chapter_candidate_builder import build_chapter_candidate_dry_run, deterministic_content_hash
from app.challenge.chapter_draft_importer import validate_chapter_markdown
from app.training.session_log import TRUSTED_FIELD_DENYLIST

REVIEW_CHECKS = {
    "math_scope_checked",
    "macro_micro_structure_checked",
    "repair_targets_checked",
    "hidden_abilities_checked",
    "semantic_edges_checked",
    "boss_coverage_checked",
    "learner_surface_safe",
}

PROFILES: dict[str, dict[str, Any]] = {
    "ode": {
        "title": "微分方程",
        "keywords": ["微分方程", "可分离", "一阶线性", "齐次", "伯努利", "二阶常系数", "特解"],
        "focus": ["方程分类", "题型入口", "解法选择", "条件转化", "计算求解", "通解表达"],
    },
    "limit": {
        "title": "极限",
        "keywords": ["极限", "等价无穷小", "洛必达", "泰勒", "夹逼", "单调有界"],
        "focus": ["极限对象", "结构题眼", "方法选择", "等价转化", "主部计算", "结果表达"],
    },
    "integral": {
        "title": "积分",
        "keywords": ["积分", "换元", "分部", "定积分", "变上限", "反常积分"],
        "focus": ["积分对象", "结构题眼", "方法选择", "换元转化", "积分计算", "结论表达"],
    },
    "series": {
        "title": "无穷级数",
        "keywords": ["级数", "收敛", "发散", "幂级数", "收敛域", "求和函数"],
        "focus": ["级数类型", "判别入口", "方法选择", "端点转化", "半径计算", "区间表达"],
    },
    "linear_algebra": {
        "title": "线性代数",
        "keywords": ["矩阵", "行列式", "向量组", "秩", "方程组", "特征值", "二次型"],
        "focus": ["概念主线", "条件题眼", "方法选择", "矩阵转化", "秩与特征计算", "结构结论"],
    },
    "probability": {
        "title": "概率论",
        "keywords": ["概率", "随机变量", "分布", "密度", "期望", "方差", "条件概率", "贝叶斯"],
        "focus": ["模型对象", "条件题眼", "公式选择", "区域转化", "概率计算", "分布表达"],
    },
}

MICRO_TYPES = ["concept", "trigger", "method", "transformation", "calculation", "expression"]
ERROR_TARGETS = {
    "concept_gap": "concept",
    "trigger_failure": "trigger",
    "method_error": "method",
    "transformation_error": "transformation",
    "calculation_error": "calculation",
    "expression_weakness": "expression",
}


def build_intelligent_chapter_draft(
    source_text: str,
    *,
    chapter_id: str | None = None,
    title: str | None = None,
    build_candidate: bool = True,
) -> dict[str, Any]:
    source = re.sub(r"\s+", " ", source_text.strip())
    profile_code, matched = _profile(source)
    profile = PROFILES[profile_code]
    final_title = _title(source, title, profile["title"])
    final_id = _chapter_id(source, chapter_id, profile_code)
    network = _network(final_id, final_title, profile, matched, source)
    markdown = _markdown(final_id, final_title, network)
    validation = validate_chapter_markdown(markdown)
    candidate = None
    if build_candidate and validation.get("report", {}).get("passed") is True:
        candidate = build_chapter_candidate_dry_run(
            markdown,
            reviewer="intelligent_importer",
            decision="approve_for_candidate",
            checklist={code: True for code in REVIEW_CHECKS},
            notes="auto candidate preview only",
        )
    return {
        "mode": "intelligent_chapter_draft_generation",
        "workflow_stage": "intelligent_draft_generation",
        "chapter_id": final_id,
        "title": final_title,
        "profile": {"code": profile_code, "title": profile["title"], "matched_keywords": matched, "confidence": _confidence(matched)},
        "source_hash": deterministic_content_hash(source),
        "knowledge_network": _public_payload(network),
        "generated_markdown": markdown,
        "draft_validation": _public_payload(validation),
        "candidate_preview": _public_payload(candidate),
        "human_review_required": True,
        "precision_report": _precision_report(source, matched, candidate),
    }


def _profile(source: str) -> tuple[str, list[str]]:
    best_code = "ode"
    best_matches: list[str] = []
    for code, profile in PROFILES.items():
        matches = [word for word in profile["keywords"] if word in source]
        if len(matches) > len(best_matches):
            best_code = code
            best_matches = matches
    return best_code, best_matches


def _title(source: str, title: str | None, fallback: str) -> str:
    if title and title.strip():
        return title.strip()[:80]
    first = re.split(r"[。.!！?？]", source)[0].strip()
    return first[:40] if 4 <= len(first) <= 40 else f"智能导入：{fallback}"


def _chapter_id(source: str, chapter_id: str | None, profile_code: str) -> str:
    if chapter_id and re.fullmatch(r"[a-zA-Z0-9_.-]{3,80}", chapter_id):
        return chapter_id
    return f"smart_{profile_code}_{deterministic_content_hash(source).replace('sha256:', '')[:8]}"


def _network(chapter_id: str, title: str, profile: dict[str, Any], matched: list[str], source: str) -> dict[str, Any]:
    return {
        "macro_nodes": [
            {"id": f"{chapter_id}.entry", "title": f"{profile['title']}入口识别", "knowledge_node_id": f"{chapter_id}.entry"},
            {"id": f"{chapter_id}.execution", "title": f"{profile['title']}执行链路", "knowledge_node_id": f"{chapter_id}.execution"},
        ],
        "micro_nodes": [_micro(chapter_id, index, micro_type, profile["focus"][index]) for index, micro_type in enumerate(MICRO_TYPES)],
        "macro_challenges": [
            {"id": f"{chapter_id}.entry.boss", "macro_node_id": f"{chapter_id}.entry", "title": "入口识别验收", "covers_micro_nodes": [f"{chapter_id}.concept", f"{chapter_id}.trigger", f"{chapter_id}.method"]},
            {"id": f"{chapter_id}.execution.boss", "macro_node_id": f"{chapter_id}.execution", "title": "执行链路验收", "covers_micro_nodes": [f"{chapter_id}.transformation", f"{chapter_id}.calculation", f"{chapter_id}.expression"]},
        ],
        "hidden_abilities": [_hidden(chapter_id, micro_type) for micro_type in MICRO_TYPES],
        "compare_guards": [
            {"id": f"{chapter_id}.compare.entry_method", "title": "入口与方法边界", "node_ids": [f"{chapter_id}.trigger", f"{chapter_id}.method"], "contrast": "入口识别回答从哪进，方法选择回答用什么做"},
            {"id": f"{chapter_id}.compare.transform_calc", "title": "转化与计算边界", "node_ids": [f"{chapter_id}.transformation", f"{chapter_id}.calculation"], "contrast": "条件转化负责变形，计算执行负责稳定求值"},
        ],
        "transfer_nodes": [{"id": f"{chapter_id}.transfer.variant", "title": "变式迁移", "owner_node_id": f"{chapter_id}.method", "repair_target_node_id": f"{chapter_id}.method", "why_exists": "防止只会原材料表述"}],
        "synthesis_nodes": [{"id": f"{chapter_id}.synthesis.boss", "title": "综合拆解", "owner_node_id": f"{chapter_id}.execution.boss", "repair_target_node_id": f"{chapter_id}.transformation", "why_exists": "把入口、转化、计算、表达连成得分链"}],
        "edges": _edges(chapter_id),
        "error_repair_map": [{"root_cause": cause, "repair_target_node_id": f"{chapter_id}.{suffix}"} for cause, suffix in ERROR_TARGETS.items()],
        "source_evidence": {"title": title, "matched_keywords": matched, "source_excerpt": source[:300]},
    }


def _micro(chapter_id: str, index: int, micro_type: str, title: str) -> dict[str, str]:
    macro = "entry" if index < 3 else "execution"
    return {"id": f"{chapter_id}.{micro_type}", "macro_node_id": f"{chapter_id}.{macro}", "type": micro_type, "title": title, "description": f"围绕{title}生成训练节点"}


def _hidden(chapter_id: str, micro_type: str) -> dict[str, str]:
    return {"id": f"{chapter_id}.hidden.{micro_type}", "owner_node_id": f"{chapter_id}.{micro_type}", "title": f"{micro_type}隐藏能力", "dimensions": micro_type, "why_exists": "防止看懂解析但不能迁移", "evidence_sources": "source,coach_schema,self_explanation", "failure_modes": "入口不稳或迁移失败", "repair_target_node_id": f"{chapter_id}.{micro_type}"}


def _edges(chapter_id: str) -> list[dict[str, str]]:
    edges = [{"id": f"{chapter_id}.e.support.{kind}", "edge_type": "supports", "source_id": f"{chapter_id}.hidden.{kind}", "target_id": f"{chapter_id}.{kind}", "reason": "隐藏能力支撑训练节点"} for kind in MICRO_TYPES]
    for left, right in zip(MICRO_TYPES, MICRO_TYPES[1:]):
        edges.append({"id": f"{chapter_id}.e.requires.{left}.{right}", "edge_type": "requires", "source_id": f"{chapter_id}.{left}", "target_id": f"{chapter_id}.{right}", "reason": "形成完整得分链"})
    edges.extend([
        {"id": f"{chapter_id}.e.transfer", "edge_type": "transfers_to", "source_id": f"{chapter_id}.transfer.variant", "target_id": f"{chapter_id}.method", "reason": "迁移回方法选择"},
        {"id": f"{chapter_id}.e.synthesis", "edge_type": "boss_checks", "source_id": f"{chapter_id}.synthesis.boss", "target_id": f"{chapter_id}.execution.boss", "reason": "综合题检查链路"},
        {"id": f"{chapter_id}.e.compare.1", "edge_type": "contrasts_with", "source_id": f"{chapter_id}.compare.entry_method", "target_id": f"{chapter_id}.method", "reason": "区分入口和方法"},
        {"id": f"{chapter_id}.e.compare.2", "edge_type": "contrasts_with", "source_id": f"{chapter_id}.compare.transform_calc", "target_id": f"{chapter_id}.calculation", "reason": "区分转化和计算"},
    ])
    return edges


def _markdown(chapter_id: str, title: str, network: dict[str, Any]) -> str:
    lines = [f"# {title}", f"chapter_id: {chapter_id}", f"title: {title}", ""]
    lines += _table("MacroNodes", ["id", "title", "knowledge_node_id"], network["macro_nodes"])
    lines += _table("MicroNodes", ["id", "macro_node_id", "type", "title", "description"], network["micro_nodes"])
    lines += _table("MacroChallenges", ["id", "macro_node_id", "title", "covers_micro_nodes"], [{**row, "covers_micro_nodes": ", ".join(row["covers_micro_nodes"])} for row in network["macro_challenges"]])
    lines += _table("HiddenAbilities", ["id", "owner_node_id", "title", "dimensions", "why_exists", "evidence_sources", "failure_modes", "repair_target_node_id"], network["hidden_abilities"])
    lines += _table("CompareGuards", ["id", "title", "node_ids", "contrast"], [{**row, "node_ids": ", ".join(row["node_ids"])} for row in network["compare_guards"]])
    lines += _table("TransferNodes", ["id", "title", "owner_node_id", "repair_target_node_id", "why_exists"], network["transfer_nodes"])
    lines += _table("SynthesisNodes", ["id", "title", "owner_node_id", "repair_target_node_id", "why_exists"], network["synthesis_nodes"])
    lines += _table("Edges", ["id", "edge_type", "source_id", "target_id", "reason"], network["edges"])
    lines += _table("ErrorRepairMap", ["root_cause", "repair_target_node_id"], network["error_repair_map"])
    return "\n".join(lines).strip() + "\n"


def _table(section: str, headers: list[str], rows: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {section}", "| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(header, "")).replace("|", "，") for header in headers) + " |")
    lines.append("")
    return lines


def _confidence(matched: list[str]) -> str:
    return "high" if len(matched) >= 3 else "medium" if len(matched) >= 1 else "low"


def _precision_report(source: str, matched: list[str], candidate: dict[str, Any] | None) -> dict[str, Any]:
    gaps = []
    if len(source) < 80:
        gaps.append("source_too_short")
    if not matched:
        gaps.append("profile_uncertain")
    return {"precision_level": "publish_candidate" if not gaps else "review_required", "gaps": gaps, "candidate_quality_grade": (candidate or {}).get("candidate_quality", {}).get("grade")}


def _public_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _public_payload(child)
            for key, child in value.items()
            if key not in TRUSTED_FIELD_DENYLIST
        }
    if isinstance(value, list):
        return [_public_payload(item) for item in value]
    return value
