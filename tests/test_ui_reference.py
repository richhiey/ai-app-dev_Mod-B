"""Public reference behavior; no provider requests or assessment answers."""
import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from module_b.ui_reference import create_app

BODY = {"question": "Which filter and airflow checks are documented?", "equipment_id": "EQ-FC-1002"}


def test_fixture_trace_clarification_guards_and_allowance(tmp_path, monkeypatch):
    monkeypatch.setenv("FIELDCARE_REFERENCE_KEY", "test-only-reference-key")
    path = tmp_path / "events.jsonl"
    with TestClient(create_app(log_path=path)) as client:
        assert client.get('/health').json()['mode'] == 'fixture'
        assert client.post('/v1/diagnose-stream', json=BODY).status_code == 401
        headers = {'X-API-Key': 'test-only-reference-key'}
        result = client.post('/v1/diagnose-stream', json=BODY, headers=headers)
        events = [json.loads(line) for line in result.text.splitlines()]
        assert events[0]['mode'] == 'fixture'
        assert events[-1]['type'] == 'complete'
        assert events[0]['request_id'] == events[-1]['request_id'] == result.headers['x-request-id']
        assert 'FIXTURE ONLY' in ''.join(e.get('text', '') for e in events)
        clarification = client.post('/v1/diagnose-stream', json={'question': BODY['question']}, headers=headers)
        assert clarification.json()['status'] == 'needs_clarification'
        assert clarification.json()['mode'] == 'fixture'
        assert client.post('/v1/diagnose-stream', json={'question': ''}, headers=headers).status_code == 422
        assert client.post('/v1/diagnose-stream', json=BODY, headers=headers).status_code == 200
        limited = client.post('/v1/diagnose-stream', json=BODY, headers=headers)
        assert limited.status_code == 429 and int(limited.headers['retry-after']) > 0
    records = [json.loads(line) for line in path.read_text().splitlines()]
    record = next(row for row in records if row['request_id'] == result.headers['x-request-id'])
    assert record['source'] == 'none' and record['outcome'] == 'completed'
    assert all('question' not in row and 'answer' not in row for row in records)
    assert 'test-only-reference-key' not in path.read_text()


def test_canonical_transport_matches_recovery_copy():
    root = Path(__file__).resolve().parents[1] / 'examples' / 'lovable'
    for relative in ('src/routes/api.fieldcare.ts', 'src/lib/fieldcareClient.ts'):
        assert (root / relative).read_text() == (root / 'reference-ui' / relative).read_text()


def test_provider_uses_real_route_without_silent_fixture_fallback(tmp_path, monkeypatch):
    monkeypatch.setenv('FIELDCARE_REFERENCE_KEY', 'test-only-reference-key')
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    monkeypatch.setenv('FIELDCARE_WORK_DIR', str(tmp_path / 'unprepared'))
    with TestClient(create_app('provider', log_path=tmp_path / 'provider.jsonl')) as client:
        result = client.post('/v1/diagnose-stream', json=BODY, headers={'X-API-Key': 'test-only-reference-key'})
        assert result.status_code == 503
        assert 'FIXTURE' not in result.text


def test_init_creates_private_pair_and_refuses_overwrite(tmp_path, monkeypatch):
    from module_b import ui_reference
    monkeypatch.setattr(ui_reference, 'STATE', tmp_path / 'state')
    ui = tmp_path / 'ui'
    ui.mkdir()
    (ui / 'package.json').write_text('{}')
    ui_reference.initialize(ui)
    service = (tmp_path / 'state/reference.env').read_text()
    browser_server = (ui / '.env.local').read_text()
    key = service.strip().split('=', 1)[1]
    assert len(key) > 30 and key in browser_server
    assert '.env.local' in (ui / '.gitignore').read_text()
    with pytest.raises(ValueError, match='already exists'):
        ui_reference.initialize(ui)
    assert (ui / '.env.local').read_text() == browser_server
