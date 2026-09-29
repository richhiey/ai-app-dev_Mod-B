"""Exercise the facilitator solution without putting it in learner helpers."""
from pathlib import Path
import shutil

import httpx
import pytest
from module_b.workspace import prepare_example, export_workspace, restore_workspace
from module_b.fieldcare import demo_service, inspect_route_bindings
from module_b.data import load_json, load_fixture

ROOT = Path(__file__).resolve().parents[1]
ROUTES = {'/v1/diagnose': 'app.routes', '/v1/dispatch-handover': 'app.handover_routes'}


@pytest.fixture
def project(tmp_path):
    project = prepare_example(destination=tmp_path/'reference')
    for name in ('main.py', 'handover_routes.py'):
        shutil.copy2(ROOT/'instructor/sprint_1/04_dispatch_handover'/name, project/'app'/name)
    return project


def test_reference_actual_http_and_reusable_checkpoint(project, tmp_path):
    bank = load_json(ROOT, 'examples/patterns/handover_requests.json')
    with demo_service(project) as server:
        for path in ROUTES:
            for name, payload in bank.items():
                response = httpx.post(server.base_url+path, json=payload)
                assert response.status_code == 200, name
                assert response.json()['status'] == 'ready'
                assert response.json()['mode'] == 'demo'
                assert response.json()['citations'] == ['DOC-FC-TS-001','DOC-FC-MP-014']
            assert httpx.post(server.base_url+path, json=load_fixture(project,'invalid-request')).status_code == 422
            for payload in [load_fixture(project,'incomplete-request'),
                            {'question':'There is smoke near the filter.', 'equipment_id':'EQ-FC-1002'},
                            {'question':'Is this filter covered by warranty?', 'equipment_id':'EQ-FC-1002'}]:
                response=httpx.post(server.base_url+path,json=payload)
                assert response.status_code==200
                assert response.json()['status']=='needs_clarification'
    (project/'trace-record.md').write_text('Live wording pending; structural checks only.')
    archive=export_workspace(project,tmp_path/'checkpoint.zip')
    restored=restore_workspace(archive,tmp_path/'restored')
    assert (restored/'app/handover_routes.py').read_bytes()==(project/'app/handover_routes.py').read_bytes()
    assert (restored/'trace-record.md').read_text().startswith('Live wording pending')
    report=inspect_route_bindings(restored,ROUTES)
    assert report['passed'],report
    assert report['external_provider_calls']==0


def test_reference_keeps_baseline_files(project):
    for path in (ROOT/'examples/fieldcare/app').glob('*.py'):
        if path.name!='main.py':
            assert (project/'app'/path.name).read_bytes()==path.read_bytes()
    assert (project/'app/main.py').read_text().startswith((ROOT/'examples/fieldcare/app/main.py').read_text())
