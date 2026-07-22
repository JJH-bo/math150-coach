from __future__ import annotations

import json
import re
from typing import Any

from app.tools.adapters.reveal_export import RevealExportAdapter
from app.tools.contracts import (
    ToolDefinition,
    ToolExecutionContext,
    ToolExecutionMode,
    ToolExecutionResult,
    ToolProducedArtifact,
    ToolQualityTier,
    ToolScope,
)
from app.tools.lesson_contracts import SemanticLesson
from app.tools.lesson_validation import normalize_lesson


EXTERNAL_RESOURCE = re.compile(
    r"<(?:script|link|img)[^>]+(?:src|href)=\"(https?://[^\"]+)\"",
    re.IGNORECASE,
)


class HtmlExportError(ValueError):
    pass


class HtmlExportAdapter:
    definition = ToolDefinition(
        tool_id="export.html",
        version="1.0.0",
        title="Verified self-contained browser lesson export",
        description=(
            "Create one offline-capable lesson HTML file with embedded "
            "presentation runtime and mathematics, per-slide evidence, and a "
            "strict external-resource and content-identity audit."
        ),
        category="export",
        quality_tier=ToolQualityTier.VERIFIED,
        required_scope=ToolScope.RENDER,
        execution_mode=ToolExecutionMode.ASYNC,
        deterministic=True,
        cacheable=True,
        timeout_seconds=120,
        max_artifacts=40,
        max_artifact_bytes=256 * 1024 * 1024,
        input_schema=SemanticLesson.model_json_schema(),
        output_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["schema_version", "content_hash", "slide_count", "html_audit"],
            "properties": {
                "schema_version": {"type": "string"},
                "content_hash": {"type": "string"},
                "slide_count": {"type": "integer"},
                "html_audit": {"type": "object"},
            },
        },
        output_media_types=["application/json", "text/html", "image/png"],
        quality_gates=[
            "semantic_lesson_contract",
            "self_contained_no_external_resources",
            "content_hash_embedded",
            "no_internal_paths_or_secrets",
            "browser_render_report_passed",
        ],
        upstream_project="https://revealjs.com/ and https://playwright.dev/",
        license="MIT and Apache-2.0",
    )

    def execute(
        self,
        arguments: dict[str, Any],
        context: ToolExecutionContext,
    ) -> ToolExecutionResult:
        lesson = normalize_lesson(arguments)
        reveal = RevealExportAdapter().execute(arguments, context)
        content_hash = reveal.result["content_hash"]
        html_path = context.work_dir / "lesson.html"
        html = html_path.read_text(encoding="utf-8")
        external_urls = EXTERNAL_RESOURCE.findall(html)
        content_hash_matches = (
            f'<meta name="lesson-content-hash" content="{content_hash}">' in html
        )
        forbidden_tokens = [
            token
            for token in ("STUDIO_API_KEY", "OPENAI_API_KEY", str(context.work_dir))
            if token in html
        ]
        audit = {
            "passed": (
                not external_urls
                and content_hash_matches
                and not forbidden_tokens
                and reveal.result["render_report"]["passed"]
            ),
            "content_hash_matches": content_hash_matches,
            "external_resource_urls": external_urls,
            "forbidden_tokens": forbidden_tokens,
            "html_bytes": html_path.stat().st_size,
            "slide_count": len(lesson.slides),
            "source_render_report": reveal.result["render_report"],
        }
        audit_path = context.work_dir / "html-audit.json"
        audit_path.write_text(
            json.dumps(audit, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        if not audit["passed"]:
            raise HtmlExportError("HTML self-containment quality report did not pass")
        screenshot_paths = [
            context.work_dir / f"slide-{index:03d}.png"
            for index in range(1, len(lesson.slides) + 1)
        ]
        paths = [context.work_dir / "lesson-spec.json", html_path, audit_path, *screenshot_paths]
        media_types = {".json": "application/json", ".html": "text/html", ".png": "image/png"}
        return ToolExecutionResult(
            result={
                "schema_version": lesson.schema_version,
                "content_hash": content_hash,
                "slide_count": len(lesson.slides),
                "html_audit": audit,
            },
            artifacts=[
                ToolProducedArtifact(
                    name=path.name,
                    media_type=media_types[path.suffix],
                    source_path=path.name,
                )
                for path in paths
            ],
            metrics={"html_bytes": html_path.stat().st_size, "slide_count": len(lesson.slides)},
        )
