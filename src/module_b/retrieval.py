"""Minimal persistent Chroma index used by the FieldCare service."""

from dataclasses import dataclass
from pathlib import Path

from module_b.openrouter import OpenRouterClient


@dataclass(frozen=True)
class RetrievedDocument:
    id: str
    text: str
    metadata: dict
    distance: float


class ChromaStore:
    """Index documents with OpenRouter embeddings and retrieve by similarity."""

    def __init__(self, *, path: str | Path, collection_name: str, client: OpenRouterClient):
        import chromadb

        self.client = client
        self._db = chromadb.PersistentClient(path=str(path))
        self._collection = self._db.get_or_create_collection(collection_name)

    def all_ids(self) -> set[str]:
        return set(self._collection.get()["ids"])

    def delete(self, document_ids: set[str]) -> None:
        if document_ids:
            self._collection.delete(ids=sorted(document_ids))

    def index(self, documents: list[dict]) -> None:
        if not documents:
            raise ValueError("The Chroma index needs at least one document.")
        embeddings = self.client.embed([row["text"] for row in documents])
        self._collection.upsert(
            ids=[row["id"] for row in documents],
            documents=[row["text"] for row in documents],
            metadatas=[row["metadata"] for row in documents],
            embeddings=embeddings,
        )

    def search(self, query: str, *, top_k: int, where: dict) -> list[RetrievedDocument]:
        if top_k <= 0:
            return []
        result = self._collection.query(
            query_embeddings=self.client.embed([query]),
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        ids, texts, metadata, distances = (
            result[key][0] for key in ("ids", "documents", "metadatas", "distances")
        )
        return [
            RetrievedDocument(str(doc_id), text, row_metadata or {}, float(distance))
            for doc_id, text, row_metadata, distance in zip(ids, texts, metadata, distances)
            if text is not None and distance is not None
        ]
