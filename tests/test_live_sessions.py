import pytest
from module_b.workspace import prepare_example
from module_b.live_sessions import read_records, save_record, record_is_current


def test_pending_discussion_and_preservation(tmp_path):
    project = prepare_example(destination=tmp_path/'service')
    first = save_record(project, 1, observations={'status': 200}, reasoning={'boundary': ''}, origin='learner_service')
    assert first['review_status'] == 'pending' and first['grade'] is None
    save_record(project, 2, observations={'status': 200}, reasoning={'boundary': 'The registered route selects its own prompt.'}, origin='learner_service')
    assert set(read_records(project)) == {'LS01', 'LS02'}
    assert read_records(project)['LS01'] == first
    assert record_is_current(first, project)
    target = project/'app/routes.py'
    target.write_text(target.read_text()+'\n# changed after observation\n')
    assert not record_is_current(first, project)


def test_public_lab_provenance_and_invalid_write(tmp_path):
    project = prepare_example(destination=tmp_path/'service')
    lab = prepare_example(destination=tmp_path/'lab')
    (lab/'app/routes.py').write_text((lab/'app/routes.py').read_text()+'\n# distinct lab\n')
    record = save_record(project, 3, observations={'v1': 200}, reasoning={'decision': 'Retain the old contract.'}, origin='public_practice', observed_project=lab)
    assert record_is_current(record, lab) and not record_is_current(record, project)
    before = read_records(project)
    with pytest.raises(ValueError):
        save_record(project, 0, observations={}, reasoning={}, origin='learner_service')
    with pytest.raises(ValueError):
        save_record(project, 1, observations={'bad': float('nan')}, reasoning={}, origin='learner_service')
    assert read_records(project) == before
