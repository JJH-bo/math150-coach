from __future__ import annotations

from collections.abc import Iterable

from app.catalog.authoring_models import AuthoringDraft, AuthoringStatus
from app.catalog.hash_utils import compute_runtime_content_hash
from app.catalog.models import CatalogQuestionRecord
from app.catalog.repository import CatalogValidationError
from app.catalog.validation_report import CatalogValidationReport
from app.catalog.validator import CatalogValidator
from app.core.schemas import KnowledgeNode


class CatalogAuthoringWorkflow:
    """Authoring/import dry-run workflow that never writes the formal catalog."""

    def __init__(self, validator: CatalogValidator | None = None) -> None:
        self.validator = validator or CatalogValidator()

    def validate_draft(
        self,
        draft: AuthoringDraft,
        node_catalog: Iterable[KnowledgeNode],
    ) -> CatalogValidationReport:
        candidate_id = draft.candidate_record.manifest.question_id
        batch_id = draft.import_batch_id
        try:
            self._validate_record(draft.candidate_record, node_catalog)
        except CatalogValidationError as exc:
            report = CatalogValidationReport.failed_report(candidate_id=candidate_id, batch_id=batch_id, error=exc)
            draft.validation_report = report
            draft.status = AuthoringStatus.VALIDATION_FAILED
            return report

        report = CatalogValidationReport.passed_report(candidate_id=candidate_id, batch_id=batch_id)
        draft.validation_report = report
        draft.status = AuthoringStatus.VALIDATED
        return report

    def require_human_review(self, draft: AuthoringDraft) -> bool:
        return bool(draft.review_checklist and draft.review_checklist.is_publish_ready())

    def build_publish_candidate(
        self,
        draft: AuthoringDraft,
        node_catalog: Iterable[KnowledgeNode],
    ) -> CatalogQuestionRecord:
        if draft.status == AuthoringStatus.REJECTED:
            raise ValueError("rejected drafts cannot become publish candidates")
        if not draft.has_passed_validation():
            raise ValueError("draft must pass CatalogValidator before publish candidate creation")
        if not self.require_human_review(draft):
            raise ValueError("human review checklist must approve publish candidate creation")

        manifest_without_hash = draft.candidate_record.manifest.model_copy(
            update={"status": "published", "content_hash": None}
        )
        candidate_without_hash = draft.candidate_record.model_copy(
            deep=True,
            update={"manifest": manifest_without_hash},
        )
        content_hash = compute_runtime_content_hash(candidate_without_hash)
        manifest_with_hash = manifest_without_hash.model_copy(update={"content_hash": content_hash})
        publish_candidate = candidate_without_hash.model_copy(update={"manifest": manifest_with_hash})
        self._validate_record(publish_candidate, node_catalog)
        return publish_candidate

    def reject_draft(self, draft: AuthoringDraft, reason: str) -> AuthoringDraft:
        draft.status = AuthoringStatus.REJECTED
        draft.rejection_reason = reason
        return draft

    def _validate_record(
        self,
        record: CatalogQuestionRecord,
        node_catalog: Iterable[KnowledgeNode],
    ) -> None:
        node_by_id = {node.id: node for node in node_catalog}
        question_ids = {record.manifest.question_id}
        if record.manifest.supersedes:
            question_ids.add(record.manifest.supersedes)
        self.validator.validate_record(record, node_by_id, question_ids)
