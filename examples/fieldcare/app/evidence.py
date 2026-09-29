"""Tiny supplied data/tool slice; no vector store or full Module A engine."""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def get_equipment_record(equipment_id: str) -> dict | None:
    """A local fixture lookup standing in for Module A's equipment tool."""
    records = json.loads((DATA / "equipment_records.json").read_text())
    return next((row for row in records if row["equipment_id"] == equipment_id), None)


def get_documents(*, safety: bool = False) -> list[dict]:
    """Select current supplied documents; this is not semantic retrieval."""
    documents = json.loads((DATA / "service_docs.json").read_text())
    ids = {"DOC-FC-SAF-001"} if safety else {"DOC-FC-TS-001", "DOC-FC-MP-014"}
    return [doc for doc in documents if doc["current"] and doc["doc_id"] in ids]
