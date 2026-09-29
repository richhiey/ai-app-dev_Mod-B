from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
import pytest
from module_b.security import ConfigurationError, FixedWindowLimiter, LimitPolicy, SecurityMiddleware, load_callers, protected_post_paths
from module_b.security_lab import prepare_security_workspace, observe_security

CALLERS={'dispatch':'FIELDCARE_DISPATCH_KEY','partner':'FIELDCARE_PARTNER_KEY'}

@pytest.fixture
def secured(monkeypatch):
    monkeypatch.setenv('FIELDCARE_DISPATCH_KEY','test-dispatch-not-live')
    monkeypatch.setenv('FIELDCARE_PARTNER_KEY','test-partner-not-live')
    clock=[0.0]; calls=[]; app=FastAPI()
    class Body(BaseModel):
        question:str
    @app.post('/v1/diagnose')
    @app.post('/v2/diagnose')
    def post(body:Body):
        calls.append(1)
        return {'answer':'fixture'}
    @app.get('/health')
    def health():return {'status':'ok'}
    app.add_middleware(SecurityMiddleware,caller_env=CALLERS,protected_paths=protected_post_paths(app),policy=LimitPolicy(2,60),clock=lambda:clock[0])
    with TestClient(app) as client:
        yield client,clock,calls

def call(client,caller='dispatch',path='/v1/diagnose',payload=None):
    headers={} if caller is None else {'X-API-Key':f'test-{caller}-not-live'}
    return client.post(path,json=payload if payload is not None else {'question':'q'},headers=headers)

def test_auth_before_work_and_no_secret_echo(secured):
    c,_,calls=secured
    for who in (None,'wrong'):
        response=call(c,who)
        assert response.status_code==401
        assert 'test-' not in response.text
    assert calls==[]
    assert call(c).status_code==200
    assert call(c).status_code==200
    assert call(c).status_code==429
    assert len(calls)==2

def test_isolation_shared_versions_and_exact_renewal(secured):
    c,t,calls=secured
    assert call(c).status_code==200
    assert call(c,path='/v2/diagnose').status_code==200
    assert call(c).status_code==429
    t[0]=10
    assert call(c,'partner').status_code==200
    t[0]=59.2
    response=call(c)
    assert response.status_code==429 and response.headers['retry-after']=='1'
    t[0]=60
    assert call(c).status_code==200
    assert call(c,'partner').status_code==200
    assert call(c,'partner').status_code==429  # its window has NOT renewed
    t[0]=70
    assert call(c,'partner').status_code==200

def test_invalid_body_counts_and_duplicate_keys_reject(secured):
    c,_,calls=secured
    assert c.post('/v1/diagnose',json={},headers=[('X-API-Key','test-dispatch-not-live'),('X-API-Key','test-dispatch-not-live')]).status_code==401
    assert call(c,payload={}).status_code==422
    assert call(c).status_code==200
    assert call(c).status_code==429
    assert len(calls)==1
    assert c.get('/health').status_code==200
    assert c.get('/openapi.json').status_code==200
    assert call(c,path='/not-a-route').status_code==404

@pytest.mark.parametrize('env',[{}, {'FIELDCARE_DISPATCH_KEY':'<set-in-runtime>','FIELDCARE_PARTNER_KEY':'x'}, {'FIELDCARE_DISPATCH_KEY':'same','FIELDCARE_PARTNER_KEY':'same'}])
def test_fail_closed_configuration(env):
    with pytest.raises(ConfigurationError):load_callers(CALLERS,env)

@pytest.mark.parametrize('allowance,window',[(0,60),(True,60),(1,0),(1,float('nan')),(1,True)])
def test_policy_validation(allowance,window):
    with pytest.raises(ValueError):LimitPolicy(allowance,window)

def test_concurrent_burst_is_atomic():
    limiter=FixedWindowLimiter(LimitPolicy(3,60),lambda:0)
    with ThreadPoolExecutor(max_workers=16) as pool:
        results=list(pool.map(lambda _:limiter.admit('dispatch')[0],range(100)))
    assert sum(results)==3

def test_workspace_probe_missing_configuration_and_carryover(tmp_path):
    project,baseline=prepare_security_workspace(tmp_path/'service')
    original=(project/'app/main.py').read_text()
    (project/'app/main.py').write_text(original+"\nfrom module_b.security import SecurityMiddleware, LimitPolicy, protected_post_paths\napp.add_middleware(SecurityMiddleware, caller_env="+repr(CALLERS)+", protected_paths=protected_post_paths(app), policy=LimitPolicy(2,60))\n")
    sequence=[{'caller':who,'path':path,'at':at} for who,path,at in [('missing','/v1/diagnose',0),('dispatch','/v1/diagnose',0),('dispatch','/v2/diagnose',0),('dispatch','/v1/diagnose',0),('partner','/v2/diagnose',0),('dispatch','/v1/diagnose',60)]]
    report=observe_security(project,caller_env=CALLERS,sequence=sequence)
    assert [r['status'] for r in report['rows']]==[401,200,200,429,200,200],report
    assert [r['adapter_calls'] for r in report['rows']]==[0,1,1,0,1,1]
    assert observe_security(project,caller_env=CALLERS,sequence=[],missing_env='FIELDCARE_PARTNER_KEY')['startup']=='refused_missing_or_invalid_caller_configuration'
    same,_=prepare_security_workspace(project)
    assert (same/'app/main.py').read_text()!=original

def test_cumulative_security_checkpoint_preserves_prior_baseline(tmp_path):
    first,before=prepare_security_workspace(tmp_path/'auth')
    (first/'app/security_settings.py').write_text('# learner edit\n')
    second,current=prepare_security_workspace(tmp_path/'limits',checkpoint=first)
    assert current['provenance']=='learner checkpoint copied; original retained'
    assert (second/'app/security_settings.py').read_text()=='# learner edit\n'
    assert (second/'fixtures/security-baseline.inherited-1.json').is_file()
    assert (first/'fixtures/security-baseline.json').is_file()
    assert not (first/'fixtures/security-baseline.inherited-1.json').exists()

def test_inventory_includes_hidden_nested_prefixed_routes():
    from fastapi import APIRouter
    app=FastAPI(); router=APIRouter(); nested=APIRouter()
    @nested.post('/hidden',include_in_schema=False)
    def hidden(): return {}
    router.include_router(nested,prefix='/tools')
    app.include_router(router,prefix='/v1')
    assert protected_post_paths(app)==('/v1/tools/hidden',)


def test_review_tracks_source_experiment_and_preservation(tmp_path):
    from pathlib import Path
    from module_b.notebook import baseline, fresh, register_source
    from module_b.security_lab import review_security
    import json
    root=Path(__file__).resolve().parents[1]
    project,_=prepare_security_workspace(tmp_path/'service',repo_root=root)
    incoming=baseline(project,'incoming',['/v1/diagnose','/v2/diagnose'])
    ref=json.loads((root/'instructor/sprint_2/05_per_key_limits/reference.json').read_text())
    (project/'app/security_settings.py').write_text(ref['settings_source'])
    register_source(project,'\nfrom module_b.security import SecurityMiddleware, protected_post_paths\nfrom app.security_settings import CALLER_ENV, POLICY\napp.add_middleware(SecurityMiddleware, caller_env=CALLER_ENV, protected_paths=protected_post_paths(app), policy=POLICY)\n')
    observed=observe_security(project,caller_env=ref['caller_env'],sequence=ref['sequence'])
    # Actual HTTP behavior is separately exercised by complete notebook execution.
    http_rows=[{'caller':caller,'path':'/v1/diagnose','status':status,'retry_after':'60' if status==429 else None} for caller,status in zip(ref['http_callers'],ref['expected_http'])]
    def review():
        return review_security(project,caller_env=ref['caller_env'],allowance=3,sequence=ref['sequence'],predictions=ref['expected_statuses'],observed=observed,http_rows=http_rows,inherited=incoming)
    result=review()
    assert result['passed'],result['checks']
    assert all(r['recovered_status']==200 for r in result['missing_configuration'])
    one_caller_http=review_security(project,caller_env=CALLERS,allowance=3,sequence=ref['sequence'],
        predictions=ref['expected_statuses'],observed=observed,
        http_rows=[r for r in http_rows if r['caller']=='dispatch'],inherited=incoming)
    assert not one_caller_http['checks']['actual_http']
    # Evidence must demonstrate pooling for one caller, not merely visit two paths.
    same_path=[dict(step,path='/v1/diagnose') for step in ref['sequence']]
    same_observed=observe_security(project,caller_env=CALLERS,sequence=same_path)
    same_review=review_security(project,caller_env=CALLERS,allowance=3,sequence=same_path,
        predictions=[r['status'] for r in same_observed['rows']],observed=same_observed,
        http_rows=http_rows,inherited=incoming)
    assert not same_review['checks']['cross_route_pooling']
    # Starting both callers together cannot establish caller-specific renewal.
    simultaneous=[dict(step,at=0 if step['at']<60 else 60) for step in ref['sequence']]
    simultaneous_observed=observe_security(project,caller_env=CALLERS,sequence=simultaneous)
    simultaneous_review=review_security(project,caller_env=CALLERS,allowance=3,sequence=simultaneous,
        predictions=[r['status'] for r in simultaneous_observed['rows']],observed=simultaneous_observed,
        http_rows=http_rows,inherited=incoming)
    assert not simultaneous_review['checks']['caller_specific_renewal']
    selection=result['selection']
    assert fresh(result,project,selection)
    ref['sequence'][0]['at']=0.5
    assert result['selection']['sequence'][0]['at']==0  # Snapshot, not a mutable alias.
    assert not review()['checks']['observations_current']
    ref['sequence'][0]['at']=0
    data=next((project/'data').glob('*.json')); data.write_text(data.read_text()+'\n')
    assert not fresh(result,project,selection)
    changed=review()
    assert not changed['passed']
    assert not changed['checks']['data_preserved']
    assert not changed['checks']['observations_current']


@pytest.mark.parametrize('text,expected',[
    ('FIELDCARE_DISPATCH_KEY=<set-in-runtime>\nFIELDCARE_PARTNER_KEY=<set-in-runtime>',True),
    ('FIELDCARE_DISPATCH_KEY=<set-in-runtime>',False),
    ('FIELDCARE_DISPATCH_KEY=example-value\nFIELDCARE_PARTNER_KEY=<set-in-runtime>',False),
    ('FIELDCARE_DISPATCH_KEY=<set-in-runtime>\nFIELDCARE_DISPATCH_KEY=<set-in-runtime>\nFIELDCARE_PARTNER_KEY=<set-in-runtime>',False),
    ('',False),
])
def test_configuration_template_requires_names_and_nonfunctional_placeholders(text,expected):
    from module_b.security_lab import configuration_template_ok
    assert configuration_template_ok(text,CALLERS) is expected
