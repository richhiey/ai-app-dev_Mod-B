import json
from pathlib import Path
import httpx
import pytest
from module_b.contracts import inspect_contract
from module_b.fieldcare import demo_service
from module_b.workspace import prepare_example

REPO = Path(__file__).resolve().parents[1]
ACCEPTED = {'question': 'Which filter and airflow checks are documented?', 'equipment_id': 'EQ-FC-1002'}
INCOMPLETE = {'question': 'Which filter checks are documented?'}


def prepared(tmp_path, limit=300, route='/practice/technician-note', module='contract_routes'):
    project = prepare_example(destination=tmp_path/'project')
    schema = (REPO/'instructor/sprint_1/05_contract_rehearsal/contract_schemas.py').read_text()
    (project/'app/contract_schemas.py').write_text(schema.replace('max_length=240', f'max_length={limit}'))
    route_source = (REPO/'examples/patterns/contract_routes.py').read_text().replace('/practice/technician-note', route)
    (project/f'app/{module}.py').write_text(route_source)
    main = project/'app/main.py'
    main.write_text(main.read_text()+f'\nfrom app.{module} import router as contract_router\napp.include_router(contract_router)\n')
    return project


def observe(project, **changes):
    arguments = dict(route='/practice/technician-note', route_module='app.contract_routes', max_length=300,
                     accepted_payload=ACCEPTED, incomplete_payload=INCOMPLETE,
                     output_examples=json.loads((REPO/'examples/patterns/contract_output_examples.json').read_text()))
    arguments.update(changes)
    return inspect_contract(project, **arguments)


def test_boundaries_and_fault_isolation(tmp_path, monkeypatch):
    monkeypatch.setenv('FIELDCARE_MODE','live')
    monkeypatch.setenv('OPENROUTER_API_KEY','TEST-NEVER-TRANSMIT')
    project = prepared(tmp_path)
    before = {p.relative_to(project):p.read_bytes() for p in project.rglob('*.py')}
    report = observe(project)
    assert report['passed'], report
    assert [(r['status_code'],r['adapter_calls']) for r in report['cases']] == [(200,1),(200,1),(422,0),(422,0),(200,0),(500,1)]
    assert report['external_provider_calls'] == 0
    assert {k:v['schema_valid'] for k,v in report['output_examples'].items()} == {
        'schema_invalid':False,'valid_but_unsupported':True,'valid_wording_variant':True}
    assert not any(v['quality_evaluated'] for v in report['output_examples'].values())
    assert before == {p.relative_to(project):p.read_bytes() for p in project.rglob('*.py')}
    with demo_service(project) as service:
        assert httpx.post(service.base_url+'/practice/technician-note', json=ACCEPTED).status_code == 200
        assert httpx.post(service.base_url+'/v1/diagnose', json=ACCEPTED).status_code == 200


def test_reusable_route_module_and_limit(tmp_path):
    project = prepared(tmp_path, limit=240, route='/practice/compact', module='compact')
    report = observe(project, route='/practice/compact', route_module='app.compact', max_length=240)
    assert report['passed'], report
    assert report['declared_max_length'] == 240


def test_wrong_constraint_does_not_pass(tmp_path):
    project = prepared(tmp_path)
    report = observe(project, max_length=240)
    assert not report['passed']
    assert not report['input_constraint_matches']
    assert next(r for r in report['cases'] if r['case']=='over_limit')['status_code'] == 200


def test_mandatory_equipment_context_is_detected(tmp_path):
    project = prepared(tmp_path)
    schema = project/'app/contract_schemas.py'
    schema.write_text(schema.read_text().replace('str | None = Field(default=None,', 'str = Field('))
    report = observe(project)
    assert not report['passed']
    assert next(r for r in report['cases'] if r['case']=='missing_optional_context')['status_code'] == 422


def test_import_errors_report_safely(tmp_path):
    project = prepared(tmp_path)
    (project/'app/contract_routes.py').write_text('raise RuntimeError("PRIVATE-EXCEPTION-TEXT")')
    report = observe(project)
    assert not report['passed']
    assert 'PRIVATE-EXCEPTION-TEXT' not in json.dumps(report)


@pytest.mark.parametrize('changes', [dict(max_length=0), dict(route='../escape'),dict(route_module='bad/module'),dict(input_field='bad field')])
def test_bad_probe_configuration(tmp_path, changes):
    project=prepared(tmp_path)
    with pytest.raises(ValueError):
        observe(project, **changes)


def test_changed_response_contract_is_detected(tmp_path):
    project = prepared(tmp_path)
    route = project/'app/contract_routes.py'
    text = route.read_text().replace('router = APIRouter()', 'class ChangedOutput(DiagnosticResponse):\n    internal_note: str = "extra"\n\nrouter = APIRouter()')
    route.write_text(text.replace('response_model=DiagnosticResponse', 'response_model=ChangedOutput'))
    report = observe(project)
    assert not report['passed']
    assert not report['output_contract_matches']


def test_expected_input_contract_keeps_other_constraints(tmp_path):
    project = prepared(tmp_path)
    report = observe(project, expected_input_model='app.schemas.DiagnosticRequest')
    assert report['passed'] and report['input_contract_matches']


@pytest.mark.parametrize('weak_source', [
    'from pydantic import BaseModel, Field\nclass TechnicianNoteRequest(BaseModel):\n question: str = Field(max_length=300)\n equipment_id: str | None = None\n',
    'from pydantic import BaseModel, Field, ConfigDict\nclass TechnicianNoteRequest(BaseModel):\n model_config = ConfigDict(extra="forbid")\n question: str = Field(min_length=1,max_length=300)\n equipment_id: str | None = Field(default=None,min_length=1,max_length=64)\n',
])
def test_weakened_input_contract_is_rejected(tmp_path,weak_source):
    project=prepared(tmp_path)
    (project/'app/contract_schemas.py').write_text(weak_source)
    report=observe(project, expected_input_model='app.schemas.DiagnosticRequest')
    assert not report['passed']
    assert not report['input_contract_matches']


def test_input_schema_documentation_does_not_change_validation_contract(tmp_path):
    project = prepared(tmp_path)
    schema = project/'app/contract_schemas.py'
    schema.write_text(schema.read_text().replace('max_length=300)', 'max_length=300, description="Text for the caller", examples=["A question"])'))
    report = observe(project, expected_input_model='app.schemas.DiagnosticRequest')
    assert report['passed'], report
    assert report['input_contract_matches']


def test_schema_annotations_do_not_erase_instance_values_or_property_names():
    from module_b._contract_probe import validation_schema
    schema = {'title': 'Documentation', 'properties': {'description': {'type': 'object',
        'description': 'Documentation', 'default': {'title': 'actual value'},
        'const': {'description': 'actual value'}, 'enum': [{'title': 'actual value'}]}}}
    normalized = validation_schema(schema)
    assert 'title' not in normalized
    field = normalized['properties']['description']
    assert 'description' not in field
    assert field['default'] == {'title': 'actual value'}
    assert field['const'] == {'description': 'actual value'}
    assert field['enum'] == [{'title': 'actual value'}]
