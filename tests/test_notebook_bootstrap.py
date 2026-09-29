"""Execute the real setup cell against local Git; no fabricated remote availability."""
import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
NOTEBOOKS=sorted((ROOT/'notebooks').rglob('*.ipynb'))


def setup_source(file=NOTEBOOKS[0]):
    return ''.join(next(c['source'] for c in json.loads(file.read_text())['cells'] if c['id']=='setup'))


def test_all_six_notebooks_use_the_same_github_bootstrap():
    assert len(NOTEBOOKS) == 6
    assert len({setup_source(p) for p in NOTEBOOKS}) == 1
    assert 'files.upload' not in setup_source()


@pytest.mark.parametrize('ref_kind',['tag','commit'])
def test_clone_pinned_revision_and_preserve_rerun(tmp_path,monkeypatch,ref_kind):
    remote=tmp_path/'remote';remote.mkdir()
    actual_run=subprocess.run
    def git(*args):
        return actual_run(['git','-C',str(remote),*args],check=True,capture_output=True,text=True).stdout.strip()
    git('init');git('config','user.email','fixture@example.invalid');git('config','user.name','Fixture')
    (remote/'src/module_b').mkdir(parents=True)
    (remote/'src/module_b/notebook.py').write_text('# reviewed revision\n')
    (remote/'requirements.lock').write_text('')
    git('add','.');git('commit','-m','Reviewed course source')
    wanted=git('rev-parse','HEAD');git('tag','course-fixture')
    (remote/'src/module_b/notebook.py').write_text('# moving branch\n')
    git('add','.');git('commit','-m','Later unreviewed change')
    destination=tmp_path/'student-checkout'
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('MODULE_B_REPO',str(destination))
    monkeypatch.setenv('MODULE_B_REPO_URL','https://github.com/course/module-b.git')
    monkeypatch.setenv('MODULE_B_REPO_REF','refs/tags/course-fixture' if ref_kind=='tag' else wanted)
    monkeypatch.setattr(sys,'path',sys.path.copy())
    calls=[]
    def run(args,**kwargs):
        calls.append(list(args))
        if args[0]=='git':
            args=[str(remote) if value=='https://github.com/course/module-b.git' else value for value in args]
            return actual_run(args,**kwargs,capture_output=True,text=True)
        assert args[1:4]==['-m','pip','install']
        return subprocess.CompletedProcess(args,0)
    monkeypatch.setattr(subprocess,'run',run)
    namespace={};exec(setup_source(),namespace)
    assert namespace['REPO']==destination
    assert (destination/'src/module_b/notebook.py').read_text()=='# reviewed revision\n'
    head=actual_run(['git','-C',str(destination),'rev-parse','HEAD'],check=True,capture_output=True,text=True).stdout.strip()
    assert head==wanted
    (destination/'work').mkdir();(destination/'work/my-work.py').write_text('# student work\n')
    source=destination/'src/module_b/notebook.py';source.write_text('# local edit\n')
    calls.clear();exec(setup_source(),{})
    assert not any(c[0]=='git' for c in calls)
    assert source.read_text()=='# local edit\n'
    assert (destination/'work/my-work.py').read_text()=='# student work\n'


def test_unpublished_repository_reports_configuration_without_downloading(tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path);monkeypatch.setenv('MODULE_B_REPO',str(tmp_path/'checkout'))
    monkeypatch.setenv('MODULE_B_REPO_URL','');monkeypatch.setenv('MODULE_B_REPO_REF','')
    def no_run(*args,**kwargs):raise AssertionError('Missing config must not start a command.')
    monkeypatch.setattr(subprocess,'run',no_run)
    with pytest.raises(RuntimeError,match='author must set GITHUB_REPO'):
        exec(setup_source(),{})
    assert not (tmp_path/'checkout').exists()
