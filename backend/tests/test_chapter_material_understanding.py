from __future__ import annotations

import base64
import zipfile
from io import BytesIO

from fastapi.testclient import TestClient

from app.challenge.chapter_material_understanding import build_chapter_material_understanding
from app.main import create_app


def test_material_understanding_extracts_multi_file_ability_evidence() -> None:
    payload = build_chapter_material_understanding(
        [
            {
                "material_type": "markdown",
                "filename": "chapter-outline.md",
                "text": """
# 多元函数微分法
核心概念：偏导数、全微分、梯度。
典型题型：复合函数求偏导、隐函数求导。
题眼入口：看到 z=f(u,v), u=x+y, v=xy 先画依赖链。
""",
            },
            {
                "material_type": "docx",
                "filename": "theorem-notes.docx",
                "content_base64": _b64(_docx_bytes("核心公式 dz=f_x dx+f_y dy。核心定理 可微推出连续。常见错误 把偏导存在当可微。")),
            },
            {
                "material_type": "pptx",
                "filename": "method-slides.pptx",
                "content_base64": _b64(_pptx_bytes("方法选择 链式法则。关键转化 写出中间变量依赖图。易混点 偏导存在 与 可微。")),
            },
            {
                "material_type": "pdf",
                "filename": "exam-value.pdf",
                "content_base64": _b64(_simple_pdf_bytes("前置依赖 一元导数。后续服务 多元极值。考研数学一得分价值 高。")),
            },
            {
                "material_type": "wrong_answers",
                "filename": "wrong-answer.txt",
                "text": "错题材料：只写最终答案，解释不足，证据不足，容易 false pass。",
            },
        ]
    )

    assert payload["mode"] == "chapter_material_understanding"
    assert payload["quality_report"]["grade"] == "pass"
    assert payload["material_count"] == 5
    assert set(payload["material_types"]) == {"markdown", "docx", "pptx", "pdf", "wrong_answers"}

    signals = payload["ability_signals"]
    assert "偏导数" in signals["core_concepts"]
    assert "dz=f_x dx+f_y dy" in signals["core_formulas"]
    assert "可微推出连续" in signals["core_theorems"]
    assert "复合函数求偏导" in signals["typical_problem_types"]
    assert "看到 z=f(u,v), u=x+y, v=xy 先画依赖链" in signals["entry_triggers"]
    assert "链式法则" in signals["method_choices"]
    assert "写出中间变量依赖图" in signals["key_transformations"]
    assert "偏导存在 与 可微" in signals["confusions"]
    assert "把偏导存在当可微" in signals["common_errors"]
    assert "一元导数" in signals["prerequisites"]
    assert "多元极值" in signals["downstream_uses"]
    assert signals["math1_value"]["level"] == "high"
    assert "false pass" in signals["false_pass_risks"]


def test_intelligent_generate_accepts_materials_without_plain_source_text() -> None:
    client = TestClient(create_app("mixed"))

    response = client.post(
        "/api/challenge/v1/authoring/chapter-draft/intelligent-generate",
        json={
            "chapter_id": "multi_material_calc_test",
            "title": "多元函数微分法材料导入",
            "materials": [
                {
                    "material_type": "markdown",
                    "filename": "outline.md",
                    "text": "核心概念：偏导数。核心公式 dz=f_x dx+f_y dy。典型题型：复合函数求偏导。题眼入口：先画依赖链。方法选择：链式法则。考研数学一得分价值：高。",
                },
                {
                    "material_type": "wrong_answers",
                    "filename": "wrong.txt",
                    "text": "常见错误：把偏导存在当可微。错题材料：只写最终答案，解释不足，false pass。",
                },
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["material_understanding"]["quality_report"]["grade"] == "pass"
    assert "dz=f_x dx+f_y dy" in payload["material_understanding"]["ability_signals"]["core_formulas"]
    assert payload["candidate_preview"]["candidate_quality"]["grade"] == "pass"
    assert payload["training_question_package"]["quality_passed"] is True


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _docx_bytes(text: str) -> bytes:
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
    )
    return _zip_bytes({"word/document.xml": document_xml})


def _pptx_bytes(text: str) -> bytes:
    slide_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
        f"<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>"
    )
    return _zip_bytes({"ppt/slides/slide1.xml": slide_xml})


def _zip_bytes(files: dict[str, str]) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    return buffer.getvalue()


def _simple_pdf_bytes(text: str) -> bytes:
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET"
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >> endobj",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        f"5 0 obj << /Length {len(stream.encode('utf-8'))} >> stream\n{stream}\nendstream endobj",
    ]
    body = "\n".join(objects)
    return f"%PDF-1.4\n{body}\ntrailer << /Root 1 0 R >>\n%%EOF\n".encode("utf-8")
