from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel
import pytest
from module_b.security import ConfigurationError, FixedWindowLimiter, LimitPolicy, SecurityMiddleware, load_callers, protected_post_paths

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



def test_inventory_includes_hidden_nested_prefixed_routes():
    from fastapi import APIRouter
    app=FastAPI(); router=APIRouter(); nested=APIRouter()
    @nested.post('/hidden',include_in_schema=False)
    def hidden(): return {}
    router.include_router(nested,prefix='/tools')
    app.include_router(router,prefix='/v1')
    assert protected_post_paths(app)==('/v1/tools/hidden',)
