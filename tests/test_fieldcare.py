import httpx
import pytest
from module_b.data import load_fixture
from module_b.fieldcare import trace_paths, demo_service
from module_b.workspace import prepare_example
from module_b.runtime import ServiceProcess


def test_tcp_demo_and_isolated_trace(tmp_path, monkeypatch):
    project = prepare_example(destination=tmp_path / 'project')
    # Demo must not inherit provider configuration from a teacher's shell.
    monkeypatch.setenv('OPENROUTER_API_KEY', 'TEST-NEVER-TRANSMIT')
    monkeypatch.setenv('FIELDCARE_MODE', 'live')
    with demo_service(project) as service:
        valid = httpx.post(f'{service.base_url}/v1/diagnose', json=load_fixture(project, 'valid-request'))
        assert valid.status_code == 200
        assert valid.json() == load_fixture(project, 'expected-demo-response')
        invalid = httpx.post(f'{service.base_url}/v1/diagnose', json=load_fixture(project, 'invalid-request'))
        assert invalid.status_code == 422
        incomplete = httpx.post(f'{service.base_url}/v1/diagnose', json=load_fixture(project, 'incomplete-request'))
        assert incomplete.json()['status'] == 'needs_clarification'
    rows = trace_paths(project)
    assert [(r['status_code'],r['handler_service_calls'],r['adapter_calls'],r['provider_calls']) for r in rows] == [(200,1,1,0),(422,0,0,0),(200,1,0,0)]


def test_fixture_cannot_escape_project(tmp_path):
    with pytest.raises(ValueError):
        load_fixture(tmp_path, '../outside')


def test_demo_profile_cannot_be_overridden(tmp_path):
    with pytest.raises(ValueError, match='owns its demo environment'):
        demo_service(tmp_path, env={'FIELDCARE_MODE': 'live'})
