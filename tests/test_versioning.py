from pathlib import Path
import json
import pytest
from module_b.edits import write_source
from module_b.versioning import inspect_version_bindings
from module_b.workspace import prepare_example

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = {'question':'Which filter checks are documented?', 'equipment_id':'EQ-FC-1002'}
VERSIONS = {'/v1/diagnose':{'module':'app.routes','model_env':'OPENROUTER_MODEL'},
            '/v2/diagnose':{'module':'app.diagnose_v2_routes','model_env':'FIELDCARE_DIAGNOSE_V2_MODEL'}}


def prepared(tmp_path):
    p=prepare_example(destination=tmp_path/'service')
    write_source(p,'app/diagnose_v2_routes.py',(ROOT/'examples/patterns/diagnose_v2_routes.py').read_text())
    main=(p/'app/main.py').read_text()
    write_source(p,'app/main.py',main+'\nfrom app.diagnose_v2_routes import router as pilot\napp.include_router(pilot)\n',expected=main)
    return p


def observe(p, versions=VERSIONS):
    return inspect_version_bindings(p, versions=versions, changed_route='/v2/diagnose',accepted_payload=PAYLOAD)


def test_independent_prompt_and_model_binding_without_file_changes(tmp_path,monkeypatch):
    p=prepared(tmp_path)
    before={x.relative_to(p):x.read_bytes() for x in p.rglob('*.py')}
    monkeypatch.setenv('OPENROUTER_API_KEY','PRIVATE-NEVER-TRANSMIT')
    report=observe(p)
    assert report['passed'],report
    rows=report['rounds']
    assert rows[0]['routes'][0]['observed_prompt_sha256']==rows[1]['routes'][0]['observed_prompt_sha256']
    assert rows[0]['routes'][1]['observed_prompt_sha256']!=rows[1]['routes'][1]['observed_prompt_sha256']
    assert rows[0]['routes'][0]['observed_model']==rows[1]['routes'][0]['observed_model']
    assert rows[0]['routes'][1]['observed_model']!=rows[1]['routes'][1]['observed_model']
    assert before=={x.relative_to(p):x.read_bytes() for x in p.rglob('*.py')}
    assert report['external_provider_calls']==0
    assert 'PRIVATE-NEVER-TRANSMIT' not in json.dumps(report)


def test_shared_model_env_fails(tmp_path):
    p=prepared(tmp_path)
    specs={path:dict(value) for path,value in VERSIONS.items()}
    specs['/v2/diagnose']['model_env']='OPENROUTER_MODEL'
    report=observe(p,specs)
    assert not report['passed']
    assert any('shared_binding' in err for err in report['errors'])


def test_wrong_prompt_wiring_fails(tmp_path):
    p=prepared(tmp_path)
    path=p/'app/diagnose_v2_routes.py'
    path.write_text(path.read_text().replace('system_prompt=SYSTEM_PROMPT','system_prompt="WRONG"'))
    report=observe(p)
    assert not report['passed']
    assert not report['rounds'][0]['routes'][1]['prompt_binding_ok']


def test_bad_model_binding_is_not_echoed(tmp_path):
    p=prepared(tmp_path)
    path=p/'app/diagnose_v2_routes.py'
    path.write_text(path.read_text().replace('model_name=MODEL_NAME','model_name="PRIVATE-HARDCODED"'))
    report=observe(p)
    assert not report['passed']
    assert 'PRIVATE-HARDCODED' not in json.dumps(report)


def test_shared_mutable_settings_fail_after_change(tmp_path):
    p=prepared(tmp_path)
    path=p/'app/diagnose_v2_routes.py'
    text=path.read_text().replace('from app.service import run_diagnosis','from app.service import run_diagnosis\nfrom app import routes as old')
    path.write_text(text.replace('system_prompt=SYSTEM_PROMPT, model_name=MODEL_NAME','system_prompt=old.SYSTEM_PROMPT, model_name=old.MODEL_NAME'))
    assert not observe(p)['passed']


def test_import_errors_are_safe(tmp_path):
    p=prepared(tmp_path)
    (p/'app/diagnose_v2_routes.py').write_text('raise RuntimeError("PRIVATE-ERROR")')
    report=observe(p)
    assert not report['passed']
    assert 'PRIVATE-ERROR' not in json.dumps(report)


def test_guarded_writes_preserve_edits_and_reject_symlinks(tmp_path):
    p=prepared(tmp_path)
    path=write_source(p,'app/new.py','first')
    write_source(p,'app/new.py','second',expected='first')
    with pytest.raises(FileExistsError):
        write_source(p,'app/new.py','third',expected='first')
    assert path.read_text()=='second'
    with pytest.raises(ValueError):
        write_source(p,'../outside.py','wrong')
    (p/'app/link.py').symlink_to(path)
    with pytest.raises(ValueError):
        write_source(p,'app/link.py','wrong')


@pytest.mark.parametrize('bad', ['../route', '/v2/diagnose?x=y'])
def test_invalid_configuration(tmp_path,bad):
    p=prepared(tmp_path)
    specs=dict(VERSIONS)
    specs[bad]=specs.pop('/v2/diagnose')
    with pytest.raises(ValueError):
        observe(p,specs)


def test_source_fingerprint_changes_when_observed_source_changes(tmp_path):
    from module_b.edits import source_fingerprint
    p=prepared(tmp_path)
    before=source_fingerprint(p)
    path=p/'app/diagnose_v2_routes.py'
    path.write_text(path.read_text()+'\n# Later edit\n')
    assert source_fingerprint(p)!=before
    unchanged=source_fingerprint(p)
    (p/'fixtures/later-evidence.json').write_text('{}')
    assert source_fingerprint(p)==unchanged
