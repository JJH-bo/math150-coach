from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.nodes import load_node_catalog
from app.api.v1.schemas import api_error, model_to_json
from app.catalog.yaml_repository import get_catalog_repository


router = APIRouter(tags=["learner-questions"])


def question_not_found() -> Exception:
    return api_error(404, "question_not_found", "Question not found.", "question_id")


@router.get("/questions/{question_id}")
def get_public_question(question_id: str) -> dict[str, object]:
    record = get_catalog_repository().get_published(question_id)
    if record is None:
        raise question_not_found()
    return {"question": model_to_json(record.to_public_question_view())}


@router.get("/nodes/{node_id}/questions")
def list_public_questions_by_node(node_id: str) -> dict[str, object]:
    known_node_ids = {node.id for node in load_node_catalog()}
    if node_id not in known_node_ids:
        raise api_error(404, "node_not_found", "Knowledge node not found.", "node_id")
    records = get_catalog_repository().list_published_by_node(node_id)
    return {
        "node_id": node_id,
        "count": len(records),
        "questions": [model_to_json(record.to_public_question_view()) for record in records],
    }

