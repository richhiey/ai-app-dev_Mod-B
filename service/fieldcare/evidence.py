"""Load the supplied FieldCare records and searchable service documents."""

import json
from pathlib import Path

from module_b.openrouter import OpenRouterClient
from module_b.retrieval import ChromaStore

DATA = Path(__file__).resolve().parent.parent / "data"
COLLECTION = "fieldcare_service_docs"


def get_equipment_record(equipment_id: str) -> dict | None:
    records = json.loads((DATA / "equipment_records.json").read_text())
    return next((row for row in records if row["equipment_id"] == equipment_id), None)


def _documents() -> list[dict]:
    rows = json.loads((DATA / "service_docs.json").read_text())
    return [row for row in rows if row["current"]]


def _as_document(row: dict) -> dict:
    metadata = {
        key: value
        for key, value in row.items()
        if key not in {"text", "topics", "applies_to_models", "supersedes"}
    }
    metadata["topics"] = ", ".join(row["topics"])
    metadata["applies_to_models"] = ", ".join(row["applies_to_models"])
    return {
        "id": row["doc_id"],
        "text": row["title"] + "\n\n" + row["text"],
        "metadata": metadata,
    }


def build_document_store(client: OpenRouterClient, path: str | Path) -> ChromaStore:
    """Index current source documents in the Module B Chroma store."""
    store = ChromaStore(path=path, collection_name=COLLECTION, client=client)
    expected = {row["doc_id"] for row in _documents()}
    indexed = store.all_ids()
    if indexed != expected:
        store.delete(indexed)
        store.index([_as_document(row) for row in _documents()])
    return store


def get_safety_citations() -> list[str]:
    return [row["doc_id"] for row in _documents() if row["safety_level"] == "safety"]
