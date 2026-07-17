from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from app.challenge.chapter_draft_importer import validate_chapter_markdown
from app.challenge.chapter_galaxy_asset import build_chapter_galaxy_asset
from app.challenge.gpt_authoring_contract import CONTRACT_VERSION
from app.challenge.gpt_draft_store import ChapterDraftStore


@dataclass(frozen=True)
class DraftSubmission:
    chapter_id: str
    title: str
    source_markdown: str
    client_request_id: str
    contract_version: str


class GptAuthoringService:
    def __init__(
        self,
        store: ChapterDraftStore,
        public_base_url: str = "",
    ) -> None:
        self.store = store
        self.public_base_url = public_base_url.rstrip("/")

    def create(self, submission: DraftSubmission) -> dict[str, Any]:
        validation, asset = self._evaluate(submission)
        record = self.store.create_revision(
            chapter_id=submission.chapter_id,
            title=submission.title,
            source_markdown=submission.source_markdown,
            client_request_id=submission.client_request_id,
            contract_version=submission.contract_version,
            validation_report=validation,
            galaxy_asset=asset,
        )
        return self.response(record)

    def revise(
        self,
        draft_id: str,
        *,
        expected_revision: int,
        submission: DraftSubmission,
    ) -> dict[str, Any]:
        validation, asset = self._evaluate(submission)
        current = self.store.load(draft_id)
        if current["chapter_id"] != submission.chapter_id:
            raise ValueError("chapter_id cannot change between revisions")
        record = self.store.revise(
            draft_id,
            expected_revision=expected_revision,
            source_markdown=submission.source_markdown,
            validation_report=validation,
            galaxy_asset=asset,
        )
        return self.response(record)

    def get(self, draft_id: str) -> dict[str, Any]:
        return self.response(self.store.load(draft_id))

    def validate(self, draft_id: str) -> dict[str, Any]:
        record = self.store.load(draft_id)
        validation = validate_chapter_markdown(record["source_markdown"])
        return {
            **self.response(record),
            "validation": validation,
        }

    def response(self, record: dict[str, Any]) -> dict[str, Any]:
        asset = record.get("galaxy_asset") or {}
        report = record.get("validation_report", {}).get("report", {})
        issues = [
            *report.get("errors", []),
            *report.get("warnings", []),
        ]
        query = (
            f"draft={quote(str(record['draft_id']))}"
            f"&revision={int(record['revision'])}"
        )
        return {
            "draft_id": record["draft_id"],
            "chapter_id": record["chapter_id"],
            "title": record["title"],
            "status": record["status"],
            "revision": record["revision"],
            "content_hash": record["content_hash"],
            "metrics": asset.get("metrics", {}),
            "issues": issues,
            "preview_url": (
                f"{self.public_base_url}/trainer/chapter-review/?{query}"
            ),
        }

    def _evaluate(
        self,
        submission: DraftSubmission,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        if submission.contract_version != CONTRACT_VERSION:
            raise ValueError(
                f"unsupported contract version: {submission.contract_version}"
            )
        validation = validate_chapter_markdown(submission.source_markdown)
        report = validation.get("report", {})
        asset: dict[str, Any] | None = None
        galaxy_error: ValueError | None = None
        try:
            asset = build_chapter_galaxy_asset(
                submission.source_markdown,
            )
            if asset.get("chapterId") != submission.chapter_id:
                raise ValueError("submitted chapter_id does not match Markdown")
            if asset.get("title") != submission.title:
                raise ValueError("submitted title does not match Markdown")
        except ValueError as exc:
            galaxy_error = exc

        if int(report.get("error_count", 0) or 0) > 0:
            asset = None
        if galaxy_error is not None:
            report.setdefault("errors", []).append(
                {
                    "target": "galaxy_asset",
                    "message": str(galaxy_error),
                    "code": "galaxy_asset_invalid",
                    "severity": "error",
                }
            )
            report["error_count"] = int(
                report.get("error_count", 0) or 0
            ) + 1
            report["passed"] = False
            asset = None
        return validation, asset
