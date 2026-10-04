"""Real Chroma regression tests for a reused notebook kernel changing directories."""
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from fastapi import FastAPI

from module_b.campus import start_demo_client
from module_b.retrieval import ChromaStore, ChromaStorageError


class Embeddings:
    def embed(self, texts):
        return [[1.0, 0.0, 0.5] for _ in texts]


def test_relative_indexes_are_isolated_across_workspaces_and_reruns(tmp_path, monkeypatch):
    first = tmp_path / 'first'
    second = tmp_path / 'second'
    first.mkdir(); second.mkdir()
    monkeypatch.chdir(first)
    one = ChromaStore(path='.chroma/fieldcare', collection_name='documents', client=Embeddings())
    one.index([{'id': 'first-doc', 'text': 'first workspace', 'metadata': {'workspace': 'first'}}])
    monkeypatch.chdir(second)
    two = ChromaStore(path='.chroma/fieldcare', collection_name='documents', client=Embeddings())
    assert two.all_ids() == set(), 'A changed cwd must not reuse the first cached Chroma system'
    two.index([{'id': 'second-doc', 'text': 'second workspace', 'metadata': {'workspace': 'second'}}])
    assert one.all_ids() == {'first-doc'}
    assert two.all_ids() == {'second-doc'}
    assert (second / '.chroma/fieldcare/chroma.sqlite3').is_file()
    monkeypatch.chdir(first)
    again = ChromaStore(path='.chroma/fieldcare', collection_name='documents', client=Embeddings())
    assert again.all_ids() == {'first-doc'}
    assert again.path.is_absolute()


def test_storage_path_conflict_is_actionable_and_preserves_existing_file(tmp_path):
    occupied = tmp_path / 'not-a-directory'
    occupied.write_text('preserve me')
    with pytest.raises(ChromaStorageError, match='PROJECT is preserved'):
        ChromaStore(path=occupied / 'index', collection_name='documents', client=Embeddings())
    assert occupied.read_text() == 'preserve me'


def test_native_open_error_has_safe_recovery_message(tmp_path, monkeypatch):
    import chromadb
    def fail(**kwargs):
        raise RuntimeError('Database error: (code: 14) unable to open database file')
    monkeypatch.setattr(chromadb, 'PersistentClient', fail)
    with pytest.raises(ChromaStorageError, match='Rerun the current Campus setup'):
        ChromaStore(path=tmp_path / 'index', collection_name='documents', client=Embeddings())


def test_failed_startup_does_not_prevent_following_successful_client():
    @asynccontextmanager
    async def broken(app):
        raise ChromaStorageError('Chroma could not open its local document index. Rerun setup.')
        yield
    with pytest.raises(RuntimeError, match='Rerun setup') as caught:
        start_demo_client(FastAPI(lifespan=broken))
    assert caught.value.__suppress_context__
    healthy = FastAPI()
    @healthy.get('/health')
    def health(): return {'status': 'ok'}
    client = start_demo_client(healthy)
    try:
        assert client.get('/health').json() == {'status': 'ok'}
    finally:
        client.__exit__(None, None, None)
