"""Safe reusable notebook infrastructure; learners keep attachment/config visible."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from .checkpoints import prepare_checkpoint
from .runtime import ServiceProcess


def runtime_keys(caller_env):
    """Fresh ephemeral local-only keys, returned in memory. Do not print this dict."""
    return {name: secrets.token_urlsafe(32) for name in caller_env.values()}


def demo_runtime(project, env):
    return ServiceProcess(project_dir=project, env={**env, 'FIELDCARE_MODE':'demo',
        'OPENROUTER_API_KEY':None, 'OPENROUTER_MODEL':None})


def prepare_security_workspace(destination, *, checkpoint=None, repo_root=None):
    """Copy a learner checkpoint or explicitly labelled versioned diagnostic recovery.

    Recovery supplies the analogous guided v2 diagnostic route, not the reserved
    supervisor assessment answer. Existing destinations retain learner edits.
    """
    root=Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
    main=(root/'examples/fieldcare/app/main.py').read_text()
    main += '\nfrom app.diagnose_v2_routes import router as diagnose_v2_router\napp.include_router(diagnose_v2_router)\n'
    recovery={'app/main.py': main,
              'app/diagnose_v2_routes.py':(root/'examples/patterns/diagnose_v2_routes.py').read_text()}
    return prepare_checkpoint(destination, checkpoint=checkpoint, recovery_files=recovery,
                              repo_root=root, baseline_name='security-baseline.json')


def observe_security(project, *, caller_env, sequence, missing_env=None):
    """Separate in-process demo observations with a controlled clock and adapter spy.

    Each row: caller label / missing / wrong, path, optional payload, optional at
    (nondecreasing seconds). A fresh worker begins with clean counters. No real keys
    or network calls. No private reference sequence is bundled in this function.
    missing_env tests startup refusal instead. Suppresses app prints/errors.
    """
    config={'caller_env':dict(caller_env), 'sequence':sequence, 'missing_env':missing_env}
    env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','TMPDIR','SYSTEMROOT')}
    result=subprocess.run([sys.executable, str(Path(__file__).with_name('_security_probe.py')),
        str(Path(project).resolve()),json.dumps(config)], env=env, capture_output=True, text=True, timeout=40)
    if result.returncode:
        return {'evidence_kind':'in_process_demo', 'external_provider_calls':0,
                'error':'probe_failed: inspect source/imports and the supplied sequence; no application output retained.'}
    report = json.loads(result.stdout)
    from .edits import source_fingerprint
    report["source_fingerprint"] = source_fingerprint(project)
    from .notebook import revision
    report['source_revision'] = revision(project)
    report['selection'] = json.loads(json.dumps({'caller_env':caller_env,'sequence':sequence}))
    return report


def review_security(project, *, caller_env, allowance, sequence, predictions,
                    observed, http_rows, inherited):
    """Public evidence checks, not a grade or a supplied experiment/implementation.

    Verify route coverage/configuration separately; retain the learner's chosen
    timeline and compare it against first-admission window accounting.
    """
    from math import ceil
    from .notebook import revision, preserved
    checks=preserved(project,inherited,mutable=('app/security_settings.py',))
    rows=observed.get('rows',[])
    checks['policy']=observed.get('configuration')=={'caller_env':caller_env,'allowance':allowance,'window_seconds':60}
    checks['predictions']=bool(rows) and predictions==[r['status'] for r in rows]
    checks['sequence_complete']=len(rows)==len(sequence)>0
    checks['observations_current']=observed.get('source_revision')==revision(project) and observed.get('selection')=={'caller_env':caller_env,'sequence':sequence}
    buckets={}; renewal=False; isolated=False; accounting=True
    admitted_paths={}; pooled=False; awaiting_expiry=set(); staggered=False
    for step,row in zip(sequence,rows):
        caller=step['caller']; now=row['at']; status=row['status']
        if caller not in caller_env:
            accounting &= status==401 and row['adapter_calls']==0
            continue
        start,count=buckets.get(caller,(now,0))
        if now-start>=60:
            renewal |= count>=allowance and status==200
            if status==200:
                awaiting_expiry.update(other for other,(t,n) in buckets.items() if other!=caller and n>0 and now-t<60)
            awaiting_expiry.discard(caller)
            start,count=now,0
            admitted_paths[caller]=set()
        if count>=allowance:
            pooled |= len(admitted_paths.get(caller,set()))>=2
            staggered |= caller in awaiting_expiry and status==429
            accounting &= status==429 and row['adapter_calls']==0 and row['retry_after']==str(max(1,ceil(60-(now-start))))
        else:
            accounting &= status in (200,422)
            expected_calls=int(status==200 and row.get('response_status')=='ready')
            accounting &= row['adapter_calls']==expected_calls
            isolated |= status==200 and any(other!=caller and n>=allowance and now-t<60 for other,(t,n) in buckets.items())
            admitted_paths.setdefault(caller,set()).add(row['path'])
            count+=1
        buckets[caller]=(start,count)
    checks['window_accounting']=bool(rows) and bool(accounting)
    checks['timeline_coverage']=({401,422,429} <= {r['status'] for r in rows}
        and {r['caller'] for r in rows if r['status']==200} >= set(caller_env)
        and {'missing','wrong'} <= {r['caller'] for r in rows if r['status']==401}
        and len({r['path'] for r in rows if r['status']==200})>=2 and renewal and isolated)
    checks['cross_route_pooling']=bool(pooled)
    checks['caller_specific_renewal']=bool(staggered)
    # Each path gets its own elapsed window in this separate worker.
    paths=observed.get('routes',[])
    coverage=observe_security(project,caller_env=caller_env,sequence=[
        {'caller':caller,'path':path,'at':i*60}
        for i,path in enumerate(paths) for caller in ('missing','wrong',*caller_env)])
    checks['route_coverage']=bool(paths) and len(coverage.get('rows',[]))==len(paths)*(len(caller_env)+2) and all(
        row['status']==(200 if row['caller'] in caller_env else 401)
        and row['adapter_calls']==int(row['caller'] in caller_env)
        and (row['caller'] not in caller_env or row.get('response_fields')==['answer','citations','mode','status']) for row in coverage.get('rows',[]))
    checks['inherited_routes']=set(inherited['inherited_paths'])<=set(paths)
    checks['public_routes']=coverage.get('public')=={'/health':200,'/docs':200,'/openapi.json':200}
    missing=[]
    for label,name in caller_env.items():
        refused=observe_security(project,caller_env=caller_env,sequence=[],missing_env=name)
        restored=observe_security(project,caller_env=caller_env,sequence=[{'caller':label,'path':paths[0]}]) if paths else {}
        restored_rows=restored.get('rows',[])
        missing.append({'missing_name':name,'startup':refused.get('startup'),
                        'recovered_status':restored_rows[0]['status'] if restored_rows else None,
                        'recovered_adapter_calls':restored_rows[0]['adapter_calls'] if restored_rows else None})
    checks['missing_configuration']=all(row['startup']=='refused_missing_or_invalid_caller_configuration' for row in missing)
    checks['configuration_recovery']=all(row['recovered_status']==200 and row['recovered_adapter_calls']==1 for row in missing)
    # These HTTP requests use complete supported fixtures and a fresh actual server.
    counts={}; expected=[]; http_isolated=False
    for row in http_rows:
        caller=row['caller']; n=counts.get(caller,0)
        expected.append(401 if caller not in caller_env else 429 if n>=allowance else 200)
        http_isolated |= caller in caller_env and row['status']==200 and any(
            other!=caller and used>=allowance for other,used in counts.items())
        if caller in caller_env and n<allowance:counts[caller]=n+1
    checks['actual_http']=bool(http_rows) and http_isolated and [r['status'] for r in http_rows]==expected and 429 in expected and all(r.get('retry_after') for r in http_rows if r['status']==429)
    return {'passed':all(checks.values()),'checks':checks,'source_revision':revision(project),
            'selection':json.loads(json.dumps({'caller_env':caller_env,'sequence':sequence,'predictions':predictions,
                         'http_callers':[r['caller'] for r in http_rows],'http_path':http_rows[0]['path'] if http_rows else ''})),
            'coverage':coverage,'missing_configuration':missing,
            'observations':observed,'actual_http':http_rows,'external_provider_calls':0}


def configuration_template_ok(text, caller_env):
    """Accept exactly the required names with the taught nonfunctional placeholder.

    This checks a submission template, not actual secrets or runtime configuration.
    Values are never returned or included in an error message.
    """
    if not isinstance(text,str):return False
    names=[]
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith('#'):continue
        name,separator,value=line.partition('=')
        if not separator or value.strip()!='<set-in-runtime>':return False
        names.append(name.strip())
    return len(names)==len(set(names)) and set(names)==set(caller_env.values())
