from __future__ import annotations

import base64
import re
import zipfile
from io import BytesIO
from typing import Any
from xml.etree import ElementTree

from app.challenge.chapter_candidate_builder import deterministic_content_hash


MATERIAL_UNDERSTANDING_SCHEMA_VERSION = "chapter_material_understanding_v1"

MATERIAL_TYPE_ALIASES = {
    "md": "markdown",
    "markdown": "markdown",
    "txt": "text",
    "text": "text",
    "plain_text": "text",
    "note": "notes",
    "notes": "notes",
    "wrong_answer": "wrong_answers",
    "wrong_answers": "wrong_answers",
    "mistakes": "wrong_answers",
    "problem_solution": "problem_solution",
    "framework": "framework",
    "chapter_framework": "framework",
    "pdf": "pdf",
    "docx": "docx",
    "word": "docx",
    "pptx": "pptx",
    "powerpoint": "pptx",
}

SIGNAL_SPECS = {
    "core_concepts": {
        "labels": ["核心概念", "概念", "concepts", "core concepts"],
        "split": True,
    },
    "core_formulas": {
        "labels": ["核心公式", "公式", "formula", "formulas"],
        "split": False,
    },
    "core_theorems": {
        "labels": ["核心定理", "定理", "theorem", "theorems"],
        "split": False,
    },
    "typical_problem_types": {
        "labels": ["典型题型", "题型", "problem types", "typical problems"],
        "split": True,
    },
    "entry_triggers": {
        "labels": ["题眼入口", "题眼", "入口", "trigger", "entry signal"],
        "split": False,
    },
    "method_choices": {
        "labels": ["方法选择", "方法", "method", "methods"],
        "split": True,
    },
    "key_transformations": {
        "labels": ["关键转化", "条件转化", "转化", "transformation", "transformations"],
        "split": False,
    },
    "confusions": {
        "labels": ["易混点", "易混", "混淆", "confusion", "confusions"],
        "split": True,
    },
    "common_errors": {
        "labels": ["常见错误", "错误", "错题材料", "common errors", "mistakes"],
        "split": True,
    },
    "prerequisites": {
        "labels": ["前置依赖", "前置", "prerequisite", "prerequisites"],
        "split": True,
    },
    "downstream_uses": {
        "labels": ["后续服务", "后续", "服务内容", "downstream", "used later"],
        "split": True,
    },
}


def build_chapter_material_understanding(
    materials: list[dict[str, Any]] | None,
    *,
    source_text: str | None = None,
) -> dict[str, Any]:
    """Read mixed chapter materials and extract training-ability evidence."""

    material_inputs = list(materials or [])
    if source_text and source_text.strip():
        material_inputs.insert(
            0,
            {
                "material_type": "text",
                "filename": "source_text",
                "text": source_text,
            },
        )

    extracted = [_extract_material(index, item) for index, item in enumerate(material_inputs)]
    readable = [item for item in extracted if item["extraction_status"] == "ok" and item["text"]]
    combined_text = _normalize_text("\n".join(item["text"] for item in readable))
    ability_signals = _ability_signals(combined_text)
    quality_report = _quality_report(extracted, ability_signals, combined_text)
    material_types = sorted({item["material_type"] for item in extracted})
    return {
        "mode": "chapter_material_understanding",
        "schema_version": MATERIAL_UNDERSTANDING_SCHEMA_VERSION,
        "material_count": len(extracted),
        "material_types": material_types,
        "source_hash": deterministic_content_hash(combined_text) if combined_text else None,
        "chapter_topic": _chapter_topic(combined_text),
        "subject_area": _subject_area(combined_text),
        "combined_text": combined_text,
        "combined_text_excerpt": combined_text[:600],
        "materials": [
            {
                "index": item["index"],
                "filename": item["filename"],
                "material_type": item["material_type"],
                "text_char_count": len(item["text"]),
                "extraction_status": item["extraction_status"],
                "extraction_error": item["extraction_error"],
                "excerpt": item["text"][:180],
            }
            for item in extracted
        ],
        "ability_signals": ability_signals,
        "training_ability_summary": _training_ability_summary(ability_signals),
        "quality_report": quality_report,
    }


def public_material_understanding_summary(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    return {
        "mode": payload.get("mode"),
        "schema_version": payload.get("schema_version"),
        "material_count": payload.get("material_count", 0),
        "material_types": list(payload.get("material_types", [])),
        "chapter_topic": payload.get("chapter_topic"),
        "subject_area": payload.get("subject_area"),
        "source_hash": payload.get("source_hash"),
        "combined_text_excerpt": payload.get("combined_text_excerpt", ""),
        "materials": list(payload.get("materials", [])),
        "ability_signals": payload.get("ability_signals", {}),
        "training_ability_summary": payload.get("training_ability_summary", ""),
        "quality_report": payload.get("quality_report", {}),
    }


def _extract_material(index: int, item: dict[str, Any]) -> dict[str, Any]:
    filename = str(item.get("filename") or f"material_{index}")
    material_type = _material_type(str(item.get("material_type") or ""), filename)
    try:
        text = str(item.get("text") or "")
        if not text and item.get("content_base64"):
            raw = base64.b64decode(str(item["content_base64"]), validate=True)
            text = _extract_text_from_bytes(raw, material_type)
        elif item.get("content_base64") and material_type in {"pdf", "docx", "pptx"}:
            raw = base64.b64decode(str(item["content_base64"]), validate=True)
            text = _extract_text_from_bytes(raw, material_type)
        else:
            text = _normalize_text(text)
        return {
            "index": index,
            "filename": filename,
            "material_type": material_type,
            "text": _normalize_text(text),
            "extraction_status": "ok" if text.strip() else "empty",
            "extraction_error": None,
        }
    except Exception as exc:
        return {
            "index": index,
            "filename": filename,
            "material_type": material_type,
            "text": "",
            "extraction_status": "error",
            "extraction_error": str(exc),
        }


def _material_type(raw_type: str, filename: str) -> str:
    raw = raw_type.strip().lower().replace("-", "_")
    if raw in MATERIAL_TYPE_ALIASES:
        return MATERIAL_TYPE_ALIASES[raw]
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return MATERIAL_TYPE_ALIASES.get(suffix, "text")


def _extract_text_from_bytes(raw: bytes, material_type: str) -> str:
    if material_type == "docx":
        return _extract_docx_text(raw)
    if material_type == "pptx":
        return _extract_pptx_text(raw)
    if material_type == "pdf":
        return _extract_pdf_text(raw)
    return raw.decode("utf-8", errors="ignore")


def _extract_docx_text(raw: bytes) -> str:
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.startswith("word/") and name.endswith(".xml")
        ]
        return _extract_xml_texts(archive, names)


def _extract_pptx_text(raw: bytes) -> str:
    with zipfile.ZipFile(BytesIO(raw)) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.startswith("ppt/slides/") and name.endswith(".xml")
        ]
        return _extract_xml_texts(archive, sorted(names))


def _extract_xml_texts(archive: zipfile.ZipFile, names: list[str]) -> str:
    chunks: list[str] = []
    for name in names:
        xml = archive.read(name)
        try:
            root = ElementTree.fromstring(xml)
        except ElementTree.ParseError:
            continue
        chunks.extend(text.strip() for text in root.itertext() if text and text.strip())
    return _normalize_text(" ".join(chunks))


def _extract_pdf_text(raw: bytes) -> str:
    library_text = _extract_pdf_with_optional_library(raw)
    if library_text.strip():
        return library_text
    chunks: list[str] = []
    for match in re.finditer(rb"\((.*?)\)\s*Tj", raw, flags=re.DOTALL):
        chunks.append(_decode_pdf_literal(match.group(1)))
    for match in re.finditer(rb"\[(.*?)\]\s*TJ", raw, flags=re.DOTALL):
        chunks.extend(_decode_pdf_literal(item) for item in re.findall(rb"\((.*?)\)", match.group(1), flags=re.DOTALL))
    if chunks:
        return _normalize_text(" ".join(chunks))
    return raw.decode("utf-8", errors="ignore")


def _extract_pdf_with_optional_library(raw: bytes) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        try:
            from PyPDF2 import PdfReader  # type: ignore
        except Exception:
            return ""
    try:
        reader = PdfReader(BytesIO(raw))
        return _normalize_text("\n".join(page.extract_text() or "" for page in reader.pages))
    except Exception:
        return ""


def _decode_pdf_literal(value: bytes) -> str:
    value = value.replace(rb"\(", b"(").replace(rb"\)", b")").replace(rb"\\", b"\\")
    return value.decode("utf-8", errors="ignore")


def _ability_signals(text: str) -> dict[str, Any]:
    signals = {key: _dedupe(_extract_label_values(text, spec["labels"], split=bool(spec["split"]))) for key, spec in SIGNAL_SPECS.items()}
    signals["math1_value"] = _math1_value(text)
    signals["false_pass_risks"] = _false_pass_risks(text)
    return signals


def _extract_label_values(text: str, labels: list[str], *, split: bool) -> list[str]:
    values: list[str] = []
    for label in labels:
        pattern = rf"{re.escape(label)}\s*[:：]?\s*([^。；;\n]+)"
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            values.extend(_split_value(match.group(1), split=split))
    return [value for value in values if value]


def _split_value(value: str, *, split: bool) -> list[str]:
    clean = _clean_value(value)
    if not split:
        return [clean] if clean else []
    parts = re.split(r"[、；;，\n]+", clean)
    return [_clean_value(part) for part in parts if _clean_value(part)]


def _clean_value(value: str) -> str:
    clean = value.strip(" ：:，,。；; \t\r\n")
    clean = re.sub(r"\s+", " ", clean)
    return clean


def _math1_value(text: str) -> dict[str, str]:
    raw_values = _extract_label_values(text, ["考研数学一得分价值", "数学一得分价值", "得分价值", "math1 value"], split=False)
    raw = raw_values[0] if raw_values else ""
    lowered = raw.lower()
    level = "high" if any(token in raw for token in ["高", "重要", "核心"]) or "high" in lowered else "medium" if raw else "unknown"
    return {
        "level": level,
        "evidence": raw,
    }


def _false_pass_risks(text: str) -> list[str]:
    risks = []
    if re.search(r"只写最终答案|最终答案|final answer", text, flags=re.IGNORECASE):
        risks.append("只写最终答案")
    if re.search(r"解释不足|证据不足|关键词|keyword", text, flags=re.IGNORECASE):
        risks.append("解释或证据不足")
    if re.search(r"false\s*pass", text, flags=re.IGNORECASE):
        risks.append("false pass")
    return _dedupe(risks)


def _chapter_topic(text: str) -> str:
    for pattern in [r"^#\s*([^\n#]+)", r"章节主题\s*[:：]\s*([^\n。]+)", r"chapter\s*[:：]\s*([^\n。]+)"]:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return _clean_value(match.group(1))[:80]
    first = _clean_value(re.split(r"[。；;\n]", text)[0] if text else "")
    return first[:80]


def _subject_area(text: str) -> str:
    checks = [
        ("calculus", ["极限", "导数", "微分", "积分", "多元", "偏导", "级数"]),
        ("linear_algebra", ["矩阵", "行列式", "向量", "特征值", "二次型"]),
        ("probability", ["概率", "随机变量", "分布", "期望", "方差"]),
    ]
    for area, keywords in checks:
        if any(keyword in text for keyword in keywords):
            return area
    return "unknown"


def _training_ability_summary(signals: dict[str, Any]) -> str:
    concepts = "、".join(signals.get("core_concepts", [])[:3]) or "核心概念"
    triggers = "、".join(signals.get("entry_triggers", [])[:2]) or "题眼入口"
    methods = "、".join(signals.get("method_choices", [])[:3]) or "方法选择"
    errors = "、".join(signals.get("common_errors", [])[:2]) or "常见错误"
    return f"本章主要训练 {concepts} 的识别与使用，通过 {triggers} 进入题型，选择 {methods}，并重点拦截 {errors}。"


def _quality_report(extracted: list[dict[str, Any]], signals: dict[str, Any], combined_text: str) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not extracted:
        errors.append(_issue("material_missing", "materials", "No chapter materials were provided.", severity="error"))
    if not combined_text:
        errors.append(_issue("material_text_empty", "materials", "No readable text could be extracted from provided materials.", severity="error"))
    required = [
        "core_concepts",
        "typical_problem_types",
        "entry_triggers",
        "method_choices",
        "common_errors",
    ]
    missing = [key for key in required if not signals.get(key)]
    if missing:
        warnings.append(_issue("ability_signal_incomplete", ",".join(missing), "Core ability evidence is incomplete."))
    if signals.get("math1_value", {}).get("level") == "unknown":
        warnings.append(_issue("math1_value_missing", "math1_value", "Mathematics I value is not explicit."))
    if not signals.get("false_pass_risks"):
        warnings.append(_issue("false_pass_risk_missing", "false_pass_risks", "False-pass risks are not explicit."))
    grade = "fail" if errors else "warn" if warnings else "pass"
    return {
        "grade": grade,
        "passed": grade == "pass",
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "coverage": {
            "readable_materials": sum(1 for item in extracted if item["extraction_status"] == "ok" and item["text"]),
            "signal_categories_present": sum(1 for key, value in signals.items() if value),
            "text_char_count": len(combined_text),
        },
    }


def _issue(code: str, target: str, message: str, *, severity: str = "warning") -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "target": target,
        "message": message,
    }


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\x00", " ")).strip()


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
