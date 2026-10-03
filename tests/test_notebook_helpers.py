from pathlib import Path
import json
import pytest
from module_b.notebook import apply_student_edits, baseline, fresh, revision, preserved, register_source
from module_b.workspace import prepare_example
ROOT=Path(__file__).resolve().parents[1]

def test_edits_validate_all_before_writing(tmp_path):
    (tmp_path/'app').mkdir()
    with pytest.raises(ValueError):
        apply_student_edits(tmp_path,{'app/valid.py':'x=1','../outside.py':'x=2'})
    assert not (tmp_path/'app/valid.py').exists()
    with pytest.raises(SyntaxError):
        apply_student_edits(tmp_path,{'app/valid.py':'x=1','app/bad.py':'x='})
    assert not (tmp_path/'app/valid.py').exists()

def test_baseline_and_registration_preserve_work(tmp_path):
    project=prepare_example(destination=tmp_path/'service',repo_root=ROOT)
    original=baseline(project,'entry',['/v1/diagnose'])
    registration='\n# student extension\nx = 1\n'
    register_source(project,registration); register_source(project,registration)
    assert (project/'app/main.py').read_text().count('x = 1')==1
    assert baseline(project,'entry',[])==original
    assert all(preserved(project,original).values())
    (project/'app/routes.py').write_text('# lost route\n')
    assert not preserved(project,original)['source_preserved']

def test_evidence_expires_on_data_or_selection_change(tmp_path):
    project=prepare_example(destination=tmp_path/'service',repo_root=ROOT)
    report={'source_revision':revision(project),'selection':{'route':'/v1/diagnose'}}
    assert fresh(report,project,report['selection'])
    assert not fresh(report,project,{'route':'/v2/diagnose'})
    file=next((project/'data').rglob('*.json')); file.write_text(file.read_text()+'\n')
    assert not fresh(report,project)

def test_one_clean_campus_and_one_clean_live_notebook_per_sprint():
    files=list((ROOT/'notebooks').rglob('*.ipynb'))
    assert {p.name for p in files}=={'sprint_1_service_foundations.ipynb','sprint_2_secure_service.ipynb','sprint_3_observable_service.ipynb', 'sprint_1_live_workshops.ipynb', 'sprint_2_live_workshops.ipynb', 'sprint_3_live_workshops.ipynb'}
    for file in files:
        notebook=json.loads(file.read_text()); cells=notebook['cells']
        assert len({c['id'] for c in cells})==len(cells)
        assert sum(c['id']=='setup' for c in cells)==1
        assert sum(c['id']=='save-checkpoint' for c in cells)==1
        for cell in cells:
            if cell['cell_type']=='code':
                assert cell['execution_count'] is None and cell['outputs']==[]
                compile(''.join(cell['source']),cell['id'],'exec')

