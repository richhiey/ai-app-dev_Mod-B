"""Check the teaching probe using an unrelated route, not a C04 answer."""
import json
from pathlib import Path

import pytest

from module_b.fieldcare import inspect_route_bindings
from module_b.workspace import prepare_example


def extension(tmp_path: Path):
    project = prepare_example(destination=tmp_path / 'service')
    # This test-only echo-summary route supplies no dispatch lesson solution.
    route = (project / 'app/routes.py').read_text().replace(
        '"/v1/diagnose"', '"/testing/summary"').replace(
        'in a short paragraph.', 'as a concise test summary.')
    (project / 'app/test_routes.py').write_text(route)
    with (project / 'app/main.py').open('a') as main:
        main.write('\nfrom app.test_routes import router as test_router\napp.include_router(test_router)\n')
    return project


def check(project):
    return inspect_route_bindings(project, {'/v1/diagnose': 'app.routes', '/testing/summary': 'app.test_routes'})


def test_success_counts_and_no_inherited_secrets(tmp_path, monkeypatch):
    project = extension(tmp_path)
    monkeypatch.setenv('OPENROUTER_API_KEY', 'PRIVATE-NEVER-IN-REPORT')
    report = check(project)
    assert report['passed'], report
    assert report['external_provider_calls'] == 0
    assert report['evidence_kind'] == 'in_process_mocked_provider'
    assert report['routes'][0]['distinct_from_baseline'] is None
    assert report['routes'][1]['distinct_from_baseline'] is True
    for row in report['routes']:
        assert row['request_schema_ok'] and row['response_schema_ok'] and row['prompt_binding_ok']
        assert [(c['status_code'], c['model_calls'], c['provider_calls']) for c in row['cases']] == [
            (200, 1, 1), (422, 0, 0), (200, 0, 0)]
    assert 'PRIVATE-NEVER-IN-REPORT' not in json.dumps(report)
    assert 'concise test summary' not in json.dumps(report)


def test_wrong_binding_is_detected(tmp_path):
    project = extension(tmp_path)
    path = project / 'app/test_routes.py'
    text = path.read_text().replace('system_prompt=SYSTEM_PROMPT', 'system_prompt="wrong prompt"')
    path.write_text(text)
    report = check(project)
    assert not report['passed']
    assert report['routes'][0]['passed']
    assert not report['routes'][1]['prompt_binding_ok']


def test_duplicate_prompt_is_detected(tmp_path):
    project = extension(tmp_path)
    path = project / 'app/test_routes.py'
    path.write_text(path.read_text().replace('as a concise test summary.', 'in a short paragraph.'))
    row = check(project)['routes'][1]
    assert row['prompt_binding_ok']
    assert not row['distinct_from_baseline'] and not row['passed']


@pytest.mark.parametrize('change', ['request', 'response', 'remove_response_model'])
def test_schema_changes_are_detected(tmp_path, change):
    project = extension(tmp_path)
    if change == 'remove_response_model':
        path = project / 'app/test_routes.py'
        # Returning a dict avoids FastAPI inferring the original output model.
        path.write_text(path.read_text().replace(', response_model=DiagnosticResponse', '').replace(
            ') -> DiagnosticResponse:', ') -> dict:').replace(
            'model_name=MODEL_NAME)', 'model_name=MODEL_NAME).model_dump()'))
    else:
        path = project / 'app/schemas.py'
        text = path.read_text()
        text = text.replace('max_length=2000', 'max_length=1000') if change == 'request' else text.replace(
            'citations: list[str]', 'citations: list[str] = []')
        path.write_text(text)
    row = check(project)['routes'][1]
    assert not row['passed']
    assert not row['request_schema_ok'] if change == 'request' else not row['response_schema_ok']


def test_unregistered_module_shows_actual_404(tmp_path):
    project = extension(tmp_path)
    path = project / 'app/main.py'
    path.write_text(path.read_text().replace('app.include_router(test_router)', ''))
    row = check(project)['routes'][1]
    assert not row['registered'] and not row['passed']
    assert [case['status_code'] for case in row['cases']] == [404, 404, 404]


def test_missing_module_returns_helpful_failure(tmp_path):
    project = prepare_example(destination=tmp_path / 'service')
    report = inspect_route_bindings(project, {'/testing/missing': 'app.absent'})
    assert not report['passed']
    assert report['routes'][0]['errors'][0].startswith('module_import_failed:')


def test_import_error_is_redacted(tmp_path):
    project = extension(tmp_path)
    (project / 'app/test_routes.py').write_text('print("PRIVATE-OUTPUT")\nraise RuntimeError("PRIVATE-EXCEPTION")')
    report = check(project)
    assert not report['passed']
    assert report['errors'][0].startswith('app_import_failed:')
    assert 'PRIVATE-' not in json.dumps(report)


def test_rechecks_updated_code_in_fresh_process(tmp_path):
    project = extension(tmp_path)
    assert check(project)['passed']
    path = project / 'app/test_routes.py'
    path.write_text(path.read_text().replace('system_prompt=SYSTEM_PROMPT', 'system_prompt="changed"'))
    assert not check(project)['passed']


def test_network_requests_are_blocked(tmp_path):
    project = extension(tmp_path)
    path = project / 'app/main.py'
    path.write_text(path.read_text() + '\nimport socket\nsocket.create_connection(("example.com", 443))\n')
    report = check(project)
    assert not report['passed']
    assert report['external_provider_calls'] == 0


def test_wrong_module_registration_is_detected(tmp_path):
    project = extension(tmp_path)
    report = inspect_route_bindings(project, {'/v1/diagnose': 'app.test_routes'})
    assert not report['routes'][0]['registered']
    assert not report['passed']


@pytest.mark.parametrize('routes', [{}, {'relative': 'app.routes'}, {'/testing/test': '../routes'}])
def test_invalid_probe_arguments(tmp_path, routes):
    with pytest.raises(ValueError):
        inspect_route_bindings(tmp_path, routes)


def test_extra_model_call_is_detected(tmp_path):
    project = extension(tmp_path)
    path = project / 'app/test_routes.py'
    call = 'run_diagnosis(request, system_prompt=SYSTEM_PROMPT, model_name=MODEL_NAME)'
    path.write_text(path.read_text().replace('return ' + call, call + '\n        return ' + call))
    row = check(project)['routes'][1]
    assert not row['passed']
    assert row['cases'][0]['model_calls'] == 2
    assert row['cases'][0]['provider_calls'] == 2
    assert not row['cases'][0]['passed']


def test_incomplete_context_must_not_call_model(tmp_path):
    project = extension(tmp_path)
    path = project / 'app/service.py'
    path.write_text(path.read_text().replace('if request.equipment_id is None:',
        'if request.equipment_id is None:\n        generate_answer(request.question, {}, system_prompt=system_prompt, model_name=model_name, mode=mode)'))
    row = check(project)['routes'][1]
    assert not row['passed']
    case = row['cases'][2]
    assert case['status_code'] == 200
    assert case['model_calls'] == 1 and case['provider_calls'] == 1
    assert not case['passed']


def test_app_is_imported_once_per_report(tmp_path):
    project = extension(tmp_path)
    path = project / 'app/main.py'
    path.write_text(path.read_text() + '\nfrom pathlib import Path\n'
                    'counter = Path(__file__).parent / "import-counter.txt"\n'
                    'counter.write_text(counter.read_text() + "1" if counter.exists() else "1")\n')
    assert check(project)['passed']
    assert (project / 'app/import-counter.txt').read_text() == '1'
