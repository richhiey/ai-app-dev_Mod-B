"""Minimal persistent Chroma index used by the FieldCare service."""

from dataclasses import dataclass
from pathlib import Path

from module_b.openrouter import OpenRouterClient


class ChromaStorageError(RuntimeError):
    """Actionable storage failure without exposing a native database traceback."""


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
        # Chroma caches systems by the path string. A relative string can select
        # another notebook workspace's cached system after os.chdir(). Resolve
        # before handing it to Chroma, and prepare the complete parent path.
        self.path = Path(path).expanduser().resolve()
        try:
            self.path.mkdir(parents=True, exist_ok=True)
            self._db = chromadb.PersistentClient(path=str(self.path))
            self._collection = self._db.get_or_create_collection(collection_name)
        except Exception as error:
            if isinstance(error, OSError) or "unable to open database file" in str(error).lower():
                raise ChromaStorageError(
                    "Chroma could not open its local document index. Rerun the current "
                    "Campus setup to prepare a fresh demo folder; your PROJECT is preserved. "
                    "For your own service, check that its .chroma folder is writable."
                ) from None
            raise

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
