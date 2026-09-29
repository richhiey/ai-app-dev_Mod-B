"""Reusable notebook mechanics; route/schema/prompt decisions remain in student cells."""
from contextlib import contextmanager
from datetime import datetime, timezone
from html import escape
import ast
import hashlib
import json
from pathlib import Path
import re
import httpx
from .edits import write_source, content_fingerprint, preserves_statements
from .fieldcare import demo_service
from .contracts import inspect_contract
from .versioning import inspect_version_bindings
from .workspace import export_workspace
from .data import load_fixture


def revision(project):
    return content_fingerprint(project, directories=('app', 'data'), suffixes=('.py', '.json'))


def table(rows, columns=None):
    """Display selected safe fields, with escaping; never pass headers/environment values."""
    from IPython.display import HTML, display
    if not rows:
        print('No observations yet.')
        return
    columns = columns or list(rows[0])
    head=''.join('<th>'+escape(str(c))+'</th>' for c in columns)
    body=''.join('<tr>'+''.join('<td>'+escape(str(row.get(c,'')))+'</td>' for c in columns)+'</tr>' for row in rows)
    display(HTML('<table><thead><tr>'+head+'</tr></thead><tbody>'+body+'</tbody></table>'))


def apply_student_edits(project, edits):
    """Apply only explicit student-supplied Python source; empty dict is a no-op.

    All paths and syntax validate before writing. The dict is the student's chosen
    replacement, unlike a supplied worked example (which uses guarded write_source).
    """
    project=Path(project).resolve()
    for name,source in edits.items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or len(path.parts)<2 or path.parts[0]!='app' or path.suffix!='.py':
            raise ValueError('Student edits must be relative app/*.py paths.')
        target=project
        for part in path.parts:
            target/=part
            if target.is_symlink():raise ValueError('Do not edit symbolic links.')
        ast.parse(source,filename=name)
    for name,source in edits.items():
        path=project/name
        write_source(project,name,source,expected=path.read_text() if path.exists() else None)
    print('Saved:', ', '.join(edits) if edits else 'no changes; complete the exercise or use the file editor.')


def register_source(project, registration):
    """Append the visible registration block once. Retain all other source."""
    path=Path(project)/'app/main.py';source=path.read_text()
    if registration not in source:
        write_source(project,'app/main.py',source+registration,expected=source)


def baseline(project, name, paths):
    """Persist a stage's incoming source/data once; reruns retain the pre-edit state."""
    if not re.fullmatch(r'[a-z0-9-]+',name):raise ValueError('Use a simple stage name.')
    project=Path(project); file=project/'fixtures'/f'{name}-baseline.json'
    if file.exists():return json.loads(file.read_text())
    result={'inherited_paths':list(paths),
            'inherited_source':{p.relative_to(project).as_posix():p.read_text() for p in sorted((project/'app').rglob('*.py'))},
            'inherited_data_sha256':{p.relative_to(project).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((project/'data').rglob('*.json'))}}
    file.write_text(json.dumps(result,indent=2)+'\n')
    return result


def preserved(project, inherited, *, mutable=()):
    """Check inherited files; main.py may add statements but cannot remove old ones."""
    project=Path(project)
    source_ok=all((project/name).is_file() and (project/name).read_text()==source
        for name,source in inherited['inherited_source'].items()
        if name not in {'app/main.py', *mutable})
    main_ok=preserves_statements(inherited['inherited_source']['app/main.py'],(project/'app/main.py').read_text())
    data_ok=all((project/name).is_file() and hashlib.sha256((project/name).read_bytes()).hexdigest()==digest
        for name,digest in inherited['inherited_data_sha256'].items())
    return {'source_preserved':source_ok,'registration_preserved':main_ok,'data_preserved':data_ok}


def observe_change(project, *, route, route_module, model_env, max_length,
                   accepted_requests, incomplete_request, inherited, bindings):
    """Generic public checks for an added versioned FieldCare operation.

    Combines existing contract/binding helpers and actual demo HTTP. Does not create
    a solution, evaluate answer quality, award a grade or call an external provider.
    """
    if not re.fullmatch(r'/v[1-9][0-9]*/[A-Za-z0-9_/-]+',route) or route in inherited['inherited_paths']:
        raise ValueError('Choose a new versioned route, retaining inherited operations.')
    if not accepted_requests or not all(isinstance(p,dict) for p in accepted_requests) or not isinstance(incomplete_request,dict):
        raise ValueError('Supply accepted request mappings and one missing-context mapping.')
    project=Path(project); before=revision(project)
    selection={'route':route,'route_module':route_module,'model_env':model_env,'max_length':max_length,
               'accepted_requests':accepted_requests,'incomplete_request':incomplete_request}
    unchanged=all((project/name).is_file() and (project/name).read_text()==source for name,source in inherited['inherited_source'].items() if name!='app/main.py')
    registration_ok=preserves_statements(inherited['inherited_source']['app/main.py'],(project/'app/main.py').read_text())
    data_ok=all((project/name).is_file() and hashlib.sha256((project/name).read_bytes()).hexdigest()==digest for name,digest in inherited['inherited_data_sha256'].items())
    contract=inspect_contract(project,route=route,route_module=route_module,max_length=max_length,
        expected_input_model='app.schemas.DiagnosticRequest',accepted_payload=accepted_requests[0],incomplete_payload=incomplete_request)
    regression_request=load_fixture(project,'valid-request')
    pairing={p:inspect_version_bindings(project,versions={p:spec,route:{'module':route_module,'model_env':model_env}},changed_route=route,accepted_payload=regression_request) for p,spec in bindings.items()}
    cases=[(f'accepted_{i+1}',p,200,'ready') for i,p in enumerate(accepted_requests)]
    cases += [('missing_context',incomplete_request,200,'needs_clarification'),
              ('missing_question',{},422,None),('blank',dict(accepted_requests[0],question='  '),422,None),
              ('extra_field',dict(accepted_requests[0],unexpected=True),422,None),
              ('boundary',dict(accepted_requests[0],question='filter '+ 'x'*(max_length-7)),200,'ready'),
              ('over_limit',dict(accepted_requests[0],question='filter '+ 'x'*(max_length-6)),422,None)]
    rows=[]
    with demo_service(project) as service:
        for label,payload,expected,semantic in cases:
            response=httpx.post(service.base_url+route,json=payload);body=response.json()
            okay=response.status_code==expected
            if expected==200:okay=okay and set(body)=={'answer','status','citations','mode'} and body['mode']=='demo' and body['status']==semantic
            rows.append({'case':label,'path':route,'status':response.status_code,'expected':expected,'passed':okay})
        preserved={p:httpx.post(service.base_url+p,json=regression_request).status_code for p in inherited['inherited_paths']}
    return {'passed':bool(unchanged and registration_ok and data_ok and contract['passed'] and all(r['passed'] for r in pairing.values()) and all(r['passed'] for r in rows) and all(v==200 for v in preserved.values()) and before==revision(project)),
            'source_revision':before,'selection':json.loads(json.dumps(selection)),
            'http':rows,'inherited_statuses':preserved,'inherited_source_unchanged':unchanged,
            'registration_preserved':registration_ok,'data_preserved':data_ok,'contract':contract,'bindings':pairing,
            'evidence_kind':'actual_local_http_demo_plus_separate_mocked_provider','external_provider_calls':0}


def fresh(report, project, selection=None):
    return bool(report.get('source_revision')==revision(project) and (selection is None or report.get('selection')==selection))


@contextmanager
def provider_service(project, *, models):
    """Explicit opt-in only: hidden input, runtime-only value, discarded process output.

    Call from a learner-enabled branch. The surrounding notebook keeps requests and
    answer review visible. Do not pass this helper to an automated no-provider run.
    """
    from getpass import getpass
    from .runtime import ServiceProcess
    if not models or any(not k or not v.strip() for k,v in models.items()):
        raise ValueError('Supply the course-approved model settings first.')
    key=getpass('Provider key (hidden; not saved): ').strip()
    if not key:raise ValueError('Provider key was not supplied.')
    runner=ServiceProcess(project_dir=project,env={**models,'FIELDCARE_MODE':'live','OPENROUTER_API_KEY':key})
    del key
    try:
        with runner as service:yield service
    finally:
        runner.stop()
        # The runner object must not retain a credential after this context exits.
        runner._env.clear()


def export_progress(project, destination, *, sprint, evidence, notes, readiness):
    """One final source/evidence archive, never an extra notebook. No auto-download."""
    project=Path(project);stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    record={'sprint':sprint,'saved_at':stamp,'source_revision':revision(project),'readiness':readiness,
            'observations':evidence,'notes':notes,'instructor_review':'pending'}
    file=project/'fixtures'/f'sprint-{sprint}-progress.json'
    file.write_text(json.dumps(record,indent=2)+'\n')
    archive=export_workspace(project,Path(destination)/f'sprint-{sprint}-checkpoint-{stamp}.zip')
    print('Source/evidence checkpoint:',archive)
    print('Save your notebook separately. Download this ZIP before a temporary runtime ends.')
    return archive
