from __future__ import annotations

from abc import ABC, abstractmethod

from app.catalog.models import CatalogQuestionRecord


class CatalogValidationError(ValueError):
    """Raised when server-side catalog data is invalid."""

    def __init__(self, message: str, error_code: str = "catalog_validation_error") -> None:
        super().__init__(message)
        self.error_code = error_code


class QuestionCatalogRepository(ABC):
    @abstractmethod
    def get_published(self, question_id: str) -> CatalogQuestionRecord | None:
        """Return a learner-visible published question, or None."""

    @abstractmethod
    def list_published_by_node(self, node_id: str) -> list[CatalogQuestionRecord]:
        """Return learner-visible published questions for a node."""

    @abstractmethod
    def validate_catalog(self) -> None:
        """Validate all catalog records and indexes."""
