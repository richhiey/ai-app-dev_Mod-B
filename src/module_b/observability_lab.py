"""Workspace, collection and review mechanics for the cumulative Sprint 3 notebook."""
import ast
import json
import os
from pathlib import Path
import time
from .checkpoints import prepare_checkpoint
from .edits import write_source
from .notebook import revision, preserved
from .runtime import ServiceProcess
from .security_lab import runtime_keys


def prepare_observable_workspace(destination, *,checkpoint=None,repo_root=None):
    root=Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
    main=(root/'examples/fieldcare/app/main.py').read_text()
    main+='\nfrom app.diagnose_v2_routes import router as v2_router\napp.include_router(v2_router)\n'
    main+='\nfrom module_b.security import SecurityMiddleware, protected_post_paths\nfrom app.security_settings import CALLER_ENV, POLICY\napp.add_middleware(SecurityMiddleware,caller_env=CALLER_ENV,protected_paths=protected_post_paths(app),policy=POLICY)\n'
    recovery={'app/main.py':main,'app/diagnose_v2_routes.py':(root/'examples/patterns/diagnose_v2_routes.py').read_text(),
        'app/security_settings.py':"from module_b.security import LimitPolicy\nCALLER_ENV={'operations':'FIELDCARE_OPERATIONS_KEY','weekend_partner':'FIELDCARE_WEEKEND_PARTNER_KEY'}\nPOLICY=LimitPolicy(allowance=4,window_seconds=60)\n"}
    return prepare_checkpoint(destination,checkpoint=checkpoint,recovery_files=recovery,repo_root=root,baseline_name='observability-baseline.json')


def insert_before_security(project,registration):
    """Keep imported source unchanged; register additions before static path inventory."""
    path=Path(project)/'app/main.py';source=path.read_text()
    if registration in source:return
    tree=ast.parse(source)
    nodes=[n for n in tree.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
        and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='add_middleware'
        and n.value.args and isinstance(n.value.args[0],ast.Name) and n.value.args[0].id=='SecurityMiddleware']
    if len(nodes)!=1:raise ValueError('Expected one visible SecurityMiddleware attachment; review your main.py before adding routes.')
    lines=source.splitlines(keepends=True);lines.insert(nodes[0].lineno-1,registration+'\n')
    write_source(project,'app/main.py',''.join(lines),expected=source)


def save_guided_file(project,name,source):
    """Worked starter written once; reruns preserve student changes."""
    path=Path(project)/name
    if not path.exists():
        if name.endswith('.py'):write_source(project,name,source)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source)
    return path


def read_callers(project):
    # Config is learner-controlled executable source, same trust as starting service.
    namespace={};exec((Path(project)/'app/security_settings.py').read_text(),namespace)
    return namespace['CALLER_ENV']


def service(project,log_path,*,mode='fixture'):
    callers=read_callers(project);keys=runtime_keys(callers)
    env={**keys,'FIELDCARE_MODE':'demo','FIELDCARE_STREAM_MODE':mode,'FIELDCARE_LOG_PATH':str(Path(log_path).resolve()),
         'OPENROUTER_API_KEY':os.environ.get('OPENROUTER_API_KEY') if mode=='live' else None,
         'OPENROUTER_MODEL':os.environ.get('OPENROUTER_MODEL') if mode=='live' else None}
    return ServiceProcess(project_dir=project,env=env),{label:keys[name] for label,name in callers.items()}


def collect_stream(response,started):
    """Measure actual local HTTP delivery; server time and client time are separate."""
    events=[];first=None;terminal=False;protocol_ok=True
    for line in response.iter_lines():
        if not line:continue
        event=json.loads(line)
        if terminal:protocol_ok=False
        events.append(event)
        if event.get('type')=='delta' and first is None:first=(time.perf_counter()-started)*1000
        if event.get('type') in ('complete','error'):terminal=True
    return {'status_code':response.status_code,'request_id':response.headers.get('x-request-id'),
            'first_content_ms':first,'completion_ms':(time.perf_counter()-started)*1000,
            'event_types':[e.get('type') for e in events],
            'completed':protocol_ok and bool(events) and events[-1].get('type')=='complete',
            'evidence_kind':'actual_local_http_transport_fixture','events':events}


def read_logs(path,*,expected=0):
    """Bounded wait for final ASGI cleanup, without printing raw process output."""
    deadline=time.monotonic()+2
    while True:
        rows=[json.loads(line) for line in Path(path).read_text().splitlines() if line] if Path(path).exists() else []
        if len(rows)>=expected or time.monotonic()>=deadline:return rows
        time.sleep(.02)


def review_checkpoint(project,*,inherited,observations,eval_before,eval_after,selected,companion,notes):
    """Readiness evidence, not a grade; written judgments still need instructor review."""
    from .evaluation import design_revision
    current=revision(project)
    checks=preserved(project,inherited)
    checks['observations_current']=observations.get('source_revision')==current
    checks['incremental_progress']=observations.get('progress_observed') is True
    checks['buffered_delivery']=observations.get('buffered_matches') is True
    checks['terminal_correlation']=observations.get('terminal_records_match') is True
    checks['cancellation_and_recovery']=observations.get('cancellation_observed') is True and observations.get('recovery_complete') is True
    checks['invalid_input']=observations.get('invalid_status')==422
    checks['route_inventory']=observations.get('documented_routes_in_inventory') is True
    checks['normal_and_interrupted']=observations.get('normal_complete') is True and observations.get('interrupted_failed') is True
    from .observability import FIELDS
    checks['required_log_fields']=bool(observations.get('logs')) and all(set(FIELDS)<=set(row) for row in observations.get('logs',[]))
    checks['private_markers_absent']=observations.get('marker_absent') is True and observations.get('safe_metadata_present') is True
    checks['retained_routes']=bool(observations.get('retained_routes')) and all(s==200 for s in observations.get('retained_routes',{}).values())
    checks['selected_observed']=observations.get('selection')=={'case_id':selected,'companion':companion}
    checks['guards_retained']=observations.get('unauthorized_status')==401 and observations.get('limited_status')==429
    checks['eval_selection']=bool(selected and companion and selected!=companion)
    checks['eval_same_config']=eval_after.get('design_revision')==design_revision(Path(project)/'data/pipeline_design.json')==observations.get('design_revision')
    expected={selected,companion}
    checks['eval_cases_rerun']=all({r['eval_id'] for r in report.get('rows',[])}==expected for report in (eval_before,eval_after)) and bool(selected)
    return {'structural_ready':all(checks.values()),'written_evidence_present':all(isinstance(notes.get(k),str) and bool(notes[k].strip()) for k in ('stream_decision','log_fields','privacy','eval_reason','result')),
        'checks':checks,'source_revision':current,'instructor_review':'pending'}


def registered_routes(project, log_path):
    """Inventory actual registrations, including operations omitted from OpenAPI."""
    import subprocess
    import sys
    env={k:v for k,v in os.environ.items() if k in ('PATH','HOME','TMPDIR','SYSTEMROOT')}
    env.update(runtime_keys(read_callers(project)))
    env.update(FIELDCARE_MODE='demo',FIELDCARE_STREAM_MODE='fixture',FIELDCARE_LOG_PATH=str(log_path))
    result=subprocess.run([sys.executable,str(Path(__file__).with_name('_route_inventory.py')),
        str(Path(project).resolve())],env=env,capture_output=True,text=True,timeout=30)
    if result.returncode:raise ValueError('Route inspection failed; check source/imports. No process output retained.')
    return json.loads(result.stdout)


def probe_checkpoint(project, *,case_id,marker,companion):
    """Actual HTTP observations with inherited policy and labelled experiment boundaries.

    Quota/isolation stays in one uninterrupted worker. Other delivery observations
    use separate workers so an inherited two-admission policy is not overwritten.
    No restart establishes timed renewal, and no marker/response text is exported.
    """
    import tempfile
    import httpx
    from .data import load_fixture
    namespace={};exec((Path(project)/'app/security_settings.py').read_text(),namespace)
    policy=namespace['POLICY']
    if policy is None or not 1<=policy.allowance<=20 or policy.window_seconds<30:
        raise ValueError('This bounded probe needs 1–20 admissions and a window of at least 30 seconds; keep your policy and design a separate probe otherwise.')
    with tempfile.TemporaryDirectory(prefix='fieldcare-observation-') as folder:
        root=Path(folder);log=root/'quota.jsonl';server,keys=service(project,log)
        paths=registered_routes(project,log)
        replay_paths=['/v1/fieldcare-stream','/v1/fieldcare-buffered','/v1/fieldcare-evidence']
        body={'case_id':case_id,'question':marker}
        with server,httpx.Client(base_url=server.base_url,trust_env=False,timeout=20) as client:
            headers={'X-API-Key':next(iter(keys.values()))}
            documented={path for path,methods in client.get('/openapi.json').json()['paths'].items() if 'post' in methods}
            guard_statuses={path:client.post(path,json={},headers={'X-API-Key':marker}).status_code for path in paths}
            missing_statuses={path:client.post(path,json={}).status_code for path in paths}
            admitted=[client.post(replay_paths[i%3],json=body,headers=headers).status_code for i in range(policy.allowance)]
            limited_statuses={path:client.post(path,json=body,headers=headers).status_code for path in replay_paths}
            other={'X-API-Key':list(keys.values())[1]}
            isolated=client.post('/v1/fieldcare-evidence',json={'case_id':case_id},headers=other).status_code
            count=len(paths)*2+policy.allowance+len(replay_paths)+1
            quota_rows=read_logs(log,expected=count)
        rows=list(quota_rows);expected_records=count
        # Each named delivery experiment has fresh capacity. It is not quota evidence.
        delivery={};retained={};design=None;buffered_events=[];cancelled_id=None;invalid_status=None
        scenarios=['normal','interrupted','buffered','cancelled','recovery','invalid','evidence']
        scenarios += ['retained:'+path for path in paths if path not in replay_paths]
        for name in scenarios:
            target=root/('delivery-'+str(len(delivery))+'.jsonl');server,keys=service(project,target)
            with server,httpx.Client(base_url=server.base_url,trust_env=False,timeout=20) as client:
                headers={'X-API-Key':next(iter(keys.values()))}
                if name in ('normal','interrupted','recovery'):
                    start=time.perf_counter()
                    payload={**body,**({'fault':'interrupt'} if name=='interrupted' else {})}
                    with client.stream('POST','/v1/fieldcare-stream',json=payload,headers=headers) as response:
                        delivery[name]=collect_stream(response,start)
                elif name=='buffered':
                    response=client.post('/v1/fieldcare-buffered',json=body,headers=headers)
                    buffered_events=response.json().get('events',[]) if response.status_code==200 else []
                    delivery[name]={'status_code':response.status_code}
                elif name=='cancelled':
                    with client.stream('POST','/v1/fieldcare-stream',json=body,headers=headers) as response:
                        cancelled_id=response.headers.get('x-request-id')
                        for line in response.iter_lines():
                            if line:break
                    delivery[name]={'request_id':cancelled_id}
                elif name=='invalid':
                    response=client.post('/v1/fieldcare-stream',json={'case_id':case_id,'unexpected':{'secret':marker}},headers=headers)
                    invalid_status=response.status_code;delivery[name]={'status_code':invalid_status}
                elif name=='evidence':
                    response=client.post('/v1/fieldcare-evidence',json={'case_id':case_id},headers=headers)
                    design=response.json().get('design_revision');delivery[name]={'status_code':response.status_code}
                else:
                    path=name.split(':',1)[1]
                    retained[path]=client.post(path,json=load_fixture(project,'valid-request'),headers=headers).status_code
                    delivery[name]={'status_code':retained[path]}
                rows.extend(read_logs(target,expected=1));expected_records+=1
        normal=delivery['normal'];interrupted=delivery['interrupted'];recovery=delivery['recovery']
        buffered_ok=(delivery['buffered']['status_code']==200 and bool(buffered_events)
            and [e.get('type') for e in buffered_events]==normal['event_types']
            and buffered_events[-1].get('type')=='complete'
            and [e.get('text') for e in buffered_events]==[e.get('text') for e in normal['events']])
        safe_present=len(rows)==expected_records and len({r.get('request_id') for r in rows})==len(rows) and all(
            r.get('request_id') and r.get('route') and r.get('outcome') and r.get('latency_ms') is not None for r in rows)
        by_id={r.get('request_id'):r for r in rows}
        normal_record=by_id.get(normal['request_id'],{});failed_record=by_id.get(interrupted['request_id'],{})
        return {'source_revision':revision(project),'design_revision':design,
            'selection':{'case_id':case_id,'companion':companion},
            'evidence_kind':'actual_local_http_transport_fixture',
            'experiments':{'quota_and_isolation_records':len(quota_rows),'separate_delivery_workers':len(scenarios),
                'inherited_allowance':policy.allowance,'window_seconds':policy.window_seconds,'renewal_tested':False},
            'admitted_statuses':admitted,'isolated_status':isolated,
            'normal_complete':normal['completed'],
            'progress_observed':normal['first_content_ms'] is not None and normal['completion_ms']-normal['first_content_ms']>=40,
            'buffered_matches':buffered_ok,
            'interrupted_failed':not interrupted['completed'] and interrupted['event_types']==['delta','error'],
            'terminal_records_match':normal_record.get('outcome')=='completed' and failed_record.get('outcome')=='failed' and failed_record.get('error_category')=='provider_interrupted',
            'cancellation_observed':by_id.get(cancelled_id,{}).get('outcome')=='cancelled',
            'recovery_complete':recovery['completed'],
            'marker_absent':all(marker not in path.read_text() for path in root.glob('*.jsonl')),
            'safe_metadata_present':safe_present,'documented_routes_in_inventory':documented<=set(paths),
            'unauthorized_status':401 if all(s==401 for s in [*guard_statuses.values(),*missing_statuses.values()]) else None,
            'limited_status':429 if all(s==429 for s in limited_statuses.values()) and all(s==200 for s in admitted) and isolated==200 else None,
            'invalid_status':invalid_status,'retained_routes':retained,'guard_statuses':guard_statuses,
            'missing_statuses':missing_statuses,'limited_statuses':limited_statuses,'logs':rows,
            'first_content_ms':normal['first_content_ms'],'completion_ms':normal['completion_ms']}
