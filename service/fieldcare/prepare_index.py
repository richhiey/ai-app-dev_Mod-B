"""Explicit, paid embedding preparation. Run with the service stopped."""

import json
import os
from fieldcare.config import work_dir
from fieldcare.evidence import _documents, _as_document
from fieldcare.resources import index_signature
from module_b.openrouter import OpenRouterClient
from module_b.retrieval import ChromaStore


def main():
    if not os.getenv("OPENROUTER_API_KEY", "").strip():
        raise SystemExit("Set OPENROUTER_API_KEY in the repository's .env first.")
    print(
        "Indexing supplied service documents with OpenRouter embeddings (uses provider quota)…"
    )
    client = OpenRouterClient(app_title="masterschool-local-index")
    try:
        store = ChromaStore(
            path=work_dir() / "chroma",
            collection_name="fieldcare_service_docs",
            client=client,
        )
        documents = [_as_document(row) for row in _documents()]
        store.delete(store.all_ids() - {row["id"] for row in documents})
        store.index(documents)
        # Publish readiness only after every embedding has been stored.
        marker = work_dir() / "index.json"
        temporary = marker.with_suffix(".tmp")
        temporary.write_text(json.dumps(index_signature(), indent=2) + "\n")
        temporary.replace(marker)
        print("Index ready. Start the server, then make a supported request.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
