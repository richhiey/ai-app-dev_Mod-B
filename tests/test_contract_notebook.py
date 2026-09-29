"""A worked cell must not silently discard a student's changed source."""
import json
from pathlib import Path
import pytest
from module_b.edits import write_source
from module_b.notebook import register_source
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('filename',['contract_schemas.py','contract_routes.py'])
def test_worked_contract_preserves_edits(tmp_path,filename):
    lab=tmp_path/'lab'; (lab/'app').mkdir(parents=True)
    target=lab/'app'/filename; target.write_text('# student edit\n')
    notebook=json.loads((ROOT/'notebooks/sprint_1/sprint_1_service_foundations.ipynb').read_text())
    source=''.join(next(c['source'] for c in notebook['cells'] if c['id']=='contract-schema'))
    with pytest.raises(FileExistsError):
        exec(source,{'lab':lab,'REPO':ROOT,'write_source':write_source,'register_source':register_source})
    assert target.read_text()=='# student edit\n'
