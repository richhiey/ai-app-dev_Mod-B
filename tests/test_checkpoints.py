from pathlib import Path
import pytest
from module_b.checkpoints import prepare_checkpoint
from module_b.workspace import prepare_example


def test_recovery_and_repeat_preserve_learner_edits(tmp_path):
    source='VALUE = "starting"\n'
    p, baseline=prepare_checkpoint(tmp_path/'target',recovery_files={'app/extension.py':source})
    assert baseline['inherited_source']['app/extension.py']==source
    (p/'app/extension.py').write_text('VALUE = "learner edit"\n')
    again, repeated=prepare_checkpoint(p,recovery_files={'app/extension.py':source})
    assert again==p and repeated==baseline
    assert (p/'app/extension.py').read_text()=='VALUE = "learner edit"\n'


def test_copy_is_independent_and_missing_source_does_not_fall_back(tmp_path):
    prior=prepare_example(destination=tmp_path/'prior')
    (prior/'app/extension.py').write_text('VALUE = 7\n')
    p,baseline=prepare_checkpoint(tmp_path/'target',checkpoint=prior)
    assert baseline['provenance']=='learner checkpoint copied; original retained'
    (p/'app/extension.py').write_text('VALUE = 8\n')
    assert (prior/'app/extension.py').read_text()=='VALUE = 7\n'
    with pytest.raises(FileNotFoundError):
        prepare_checkpoint(tmp_path/'missing-target',checkpoint=tmp_path/'absent',recovery_files={'app/extension.py':'VALUE = 1'})
    assert not (tmp_path/'missing-target').exists()


def test_existing_unbaselined_workspace_is_preserved(tmp_path):
    prior=prepare_example(destination=tmp_path/'prior')
    with pytest.raises(FileExistsError):
        prepare_checkpoint(prior,recovery_files={'app/routes.py':'bad replacement'})
    assert (prior/'app/routes.py').read_text()!='bad replacement'


def test_requires_explicit_starting_source(tmp_path):
    with pytest.raises(ValueError):prepare_checkpoint(tmp_path/'target')
    with pytest.raises(ValueError):prepare_checkpoint(tmp_path/'target',baseline_name='../unsafe.json')
    assert not (tmp_path/'target').exists()


def test_registration_preservation_ignores_documentation_but_rejects_replacement():
    from module_b.edits import preserves_statements
    before='from app.routes import router\napp.include_router(router)\n'
    assert preserves_statements(before,'# extra comment\n'+before+'app.include_router(pilot)\n')
    assert preserves_statements(before,'from app.routes import router\nfrom app.pilot import pilot\napp.include_router(router)\n')
    assert not preserves_statements(before,before.replace('app.include_router(router)','app.include_router(other)'))
    assert not preserves_statements(before,'this is invalid (')


def test_evidence_snapshot_and_content_fingerprint_detect_data_changes(tmp_path):
    import hashlib
    from module_b.edits import content_fingerprint
    p, baseline = prepare_checkpoint(tmp_path/'target', recovery_files={'app/extension.py':'VALUE = 1\n'})
    record = p/'data/equipment_records.json'
    assert baseline['inherited_data_sha256']['data/equipment_records.json'] == hashlib.sha256(record.read_bytes()).hexdigest()
    before = content_fingerprint(p, directories=('app', 'data'), suffixes=('.py', '.json'))
    record.write_text(record.read_text()+'\n')
    assert before != content_fingerprint(p, directories=('app', 'data'), suffixes=('.py', '.json'))
