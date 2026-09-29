"""Synthetic live workshop mechanics; visible prevention source stays in fixtures.

Only creates/inspects a dedicated marked directory. No real repository scanning,
external calls, credentials, history rewriting or automatic student repairs.
"""
import json
import re
import subprocess
from pathlib import Path

_SENTINEL = '.module-b-synthetic-secret-workshop'


def _root(folder):
    root = Path(folder).resolve()
    if not (root/_SENTINEL).is_file():
        raise ValueError('Use only a directory created by prepare_secret_workshop.')
    return root


def git_fixture(folder, *args):
    """Run the visible Git operation only inside the disposable marked fixture."""
    root = _root(folder)
    return subprocess.run(['git','-c','user.name=Synthetic lesson fixture',
        '-c','user.email=lesson@example.invalid',*args],cwd=root,check=True,
        capture_output=True,text=True).stdout.strip()


def prepare_secret_workshop(folder, *, marker, repo_root=None):
    if not re.fullmatch(r'SYNTHETIC_[A-Z0-9_]{3,80}_NOT_A_CREDENTIAL',marker):
        raise ValueError('Use an explicitly nonfunctional synthetic marker.')
    root = Path(folder).resolve()
    if root.exists():
        _root(root)
        if json.loads((root/_SENTINEL).read_text())['marker'] != marker:
            raise ValueError('Existing fixture uses another marker. Choose a new fixture name.')
        return root  # Preserve learner edits and evidence on rerun.
    root.mkdir(parents=True)
    (root/_SENTINEL).write_text(json.dumps({'marker':marker}))
    repo = Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
    source = repo/'examples/patterns/secret_workshop'
    for name in ('log','prompt'):
        (root/f'{name}_policy.py').write_text((source/f'{name}_unsafe.py').read_text())
    git_fixture(root,'init','-q')
    (root/'.env').write_text('FAKE_MARKER='+marker+'\n')
    git_fixture(root,'add','.env')
    git_fixture(root,'commit','-qm','Intentionally exposed synthetic marker; no functional key')
    (root/'local.key').write_text(marker+'\n')
    return root


def inspect_secret_workshop(folder):
    """Execute trusted teaching functions and inspect the actual saved sinks.

    This is a bounded marker check, not a general scanner or security guarantee.
    Every returned value is safe because the inputs are generated synthetic data.
    """
    root = _root(folder)
    marker = json.loads((root/_SENTINEL).read_text())['marker']
    modules = {}
    for name in ('log','prompt'):
        namespace = {}
        exec(compile((root/f'{name}_policy.py').read_text(),str(root/f'{name}_policy.py'),'exec'),namespace)
        modules[name] = namespace
    event = {'request_id':'synthetic-request-17','route':'/v1/diagnose',
             'status':502,'headers':{'X-API-Key':marker}}
    ordinary = modules['log']['log_record']({**event,'status':200})
    failure = modules['log']['log_record'](event,RuntimeError('Fake upstream detail '+marker))
    log_path = root/'observed.log'
    log_path.write_text(json.dumps(ordinary)+'\n'+json.dumps(failure)+'\n')
    prompt = modules['prompt']['build_prompt']('Which filter check comes next?',
        'Synthetic HX filter: inspect the intake.',{'provider_key':marker})
    payload_path = root/'outbound-payload.json'
    payload_path.write_text(json.dumps(prompt,indent=2)+'\n')
    tracked = bool(git_fixture(root,'ls-files','.env'))
    ignored = subprocess.run(['git','check-ignore','-q','local.key'],cwd=root).returncode == 0
    initial_commit = git_fixture(root,'rev-list','--max-parents=0','HEAD').splitlines()[0]
    history = git_fixture(root,'show',initial_commit+':.env')
    checks = {
        'ordinary_log_excludes_marker':marker not in json.dumps(ordinary),
        'exception_log_excludes_marker':marker not in json.dumps(failure),
        'diagnostic_fields_retained':all(v.get('request_id')=='synthetic-request-17' and v.get('route')=='/v1/diagnose' for v in (ordinary,failure)) and ordinary.get('status')==200 and failure.get('status')==502 and failure.get('error_code')=='upstream_failed',
        'saved_log_excludes_marker':marker not in log_path.read_text(),
        'prompt_excludes_marker':marker not in payload_path.read_text(),
        'task_context_retained':'Which filter check comes next?' in payload_path.read_text() and 'inspect the intake' in payload_path.read_text(),
        'new_local_file_ignored':ignored,
        'environment_untracked':not tracked,
        'historical_exposure_still_visible':marker in history,
    }
    return {'checks':checks,'passed':all(checks.values()),'real_credentials_used':False,
        'external_provider_calls':0,'evidence_kind':'synthetic_local_fixture',
        'artifacts':['observed.log','outbound-payload.json','Git index and initial commit'],
        'history_is_not_repaired':True}
