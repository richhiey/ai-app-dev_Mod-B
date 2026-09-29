import asyncio
import json
from pathlib import Path
import time
import uuid
import httpx
import pytest
from module_b.observability import safe_record, FIELDS
from module_b.observability_lab import (prepare_observable_workspace,save_guided_file,insert_before_security,
    service,collect_stream,read_logs)
from module_b.notebook import register_source, preserved
from module_b.evaluation import module_a, evaluate_selected, design_revision
from module_b.streaming import provider_events, StreamFailure
ROOT=Path(__file__).resolve().parents[1]
PATTERN=ROOT/'examples/patterns/sprint_3'

@pytest.fixture
def workspace(tmp_path):
    project,base=prepare_observable_workspace(tmp_path/'app',repo_root=ROOT)
    for name in ['stream_routes.py','log_settings.py']:
        save_guided_file(project,'app/'+name,(PATTERN/name).read_text())
    save_guided_file(project,'data/pipeline_design.json',json.dumps(module_a.default_pipeline_design(),indent=2))
    insert_before_security(project,'\nfrom app.stream_routes import router as stream_router\napp.include_router(stream_router)\n')
    register_source(project,(PATTERN/'attachment.py.txt').read_text())
    assert all(preserved(project,base).values())
    return project


def test_allowlist_discards_unknown_nested_and_false_numeric_values():
    marker='SYNTHETIC-private@example.invalid'
    row=safe_record({'request_id':str(uuid.uuid4()),'prompt':marker,'error':{'secret':marker},
        'model':marker,'tokens':True,'latency_ms':float('nan'),'route':'/'+marker,'error_category':marker},routes=['/safe'])
    assert marker not in json.dumps(row)
    assert row['tokens'] is None and row['model'] is None
    assert row['route']=='unmatched' and row['error_category']=='internal_error'


def test_http_stream_logs_guards_and_eval_share_config(workspace,tmp_path):
    log=tmp_path/'events.jsonl';server,keys=service(workspace,log)
    with server, httpx.Client(base_url=server.base_url,trust_env=False) as client:
        h={'X-API-Key':next(iter(keys.values()))};body={'case_id':'EVAL-FC-005'}
        rejected=client.post('/v1/fieldcare-stream',json=body)
        assert rejected.status_code==401
        start=time.perf_counter()
        buffered=client.post('/v1/fieldcare-buffered',json=body,headers=h)
        assert buffered.status_code==200
        buffered_ms=(time.perf_counter()-start)*1000
        start=time.perf_counter()
        with client.stream('POST','/v1/fieldcare-stream',json=body,headers=h) as response:
            streamed=collect_stream(response,start)
        assert streamed['completed'] and streamed['first_content_ms']<streamed['completion_ms']
        assert streamed['first_content_ms']<buffered_ms
        assert [e.get('text') for e in streamed['events']]==[e.get('text') for e in buffered.json()['events']]
        with client.stream('POST','/v1/fieldcare-stream',json={**body,'fault':'interrupt'},headers=h) as response:
            interrupted=collect_stream(response,time.perf_counter())
        assert not interrupted['completed'] and interrupted['event_types']==['delta','error']
        evidence=client.post('/v1/fieldcare-evidence',json=body,headers=h).json()
        assert evidence['design_revision']==design_revision(workspace/'data/pipeline_design.json')
        assert client.post('/v1/fieldcare-stream',json=body,headers=h).status_code==429
        rows=read_logs(log,expected=6)
        assert len(rows)==6 and len({r['request_id'] for r in rows})==6
        assert rows[3]['outcome']=='failed' and rows[3]['status_code']==200
        assert rows[0]['source']=='none' and rows[-1]['source']=='none'
        assert all(r['tokens'] is None for r in rows)
        assert set(rows[2])==set(FIELDS)
    evals=evaluate_selected(workspace/'data/pipeline_design.json',['EVAL-FC-005','EVAL-FC-003'])
    assert evals['design_revision']==evidence['design_revision']
    assert all(r['pipeline_pass'] for r in evals['rows'])


def test_cancellation_privacy_and_restart_preserve_source(workspace,tmp_path):
    marker='SYNTHETIC-NAME-private@example.invalid'
    log=tmp_path/'events.jsonl';server,keys=service(workspace,log)
    with server,httpx.Client(base_url=server.base_url,trust_env=False) as client:
        h={'X-API-Key':next(iter(keys.values()))}
        assert client.post('/v1/fieldcare-stream?note='+marker,json={'secret':{'value':marker}},headers=h).status_code==422
        assert client.post('/v1/fieldcare-stream',json={'question':marker},headers={'X-API-Key':marker}).status_code==401
        with client.stream('POST','/v1/fieldcare-stream',json={'case_id':'EVAL-FC-006','question':marker},headers=h) as r:
            for line in r.iter_lines():
                if line:break
        rows=read_logs(log,expected=3)
        assert len(rows)==3
        assert rows[-1]['outcome']=='cancelled'
        assert marker not in log.read_text()
        assert all(r['request_id'] and r['route'] for r in rows)
    source=(workspace/'app/stream_routes.py').read_text()+'\n# learner edit\n'
    (workspace/'app/stream_routes.py').write_text(source)
    assert save_guided_file(workspace,'app/stream_routes.py','replacement').read_text()==source


@pytest.mark.parametrize('ending,valid',[
    ('data: {"choices":[{"delta":{},"finish_reason":"stop"}],"model":"approved","usage":{"total_tokens":17}}\n\ndata: [DONE]\n\n',True),
    ('',False),('data: {"error":{"message":"SYNTHETIC-PRIVATE"}}\n\n',False),
    ('data: {"choices":[{"finish_reason":"length"}]}\n\ndata: [DONE]\n\n',False)])
def test_provider_adapter_mock_usage_and_safe_failure(monkeypatch,ending,valid):
    monkeypatch.setenv('OPENROUTER_API_KEY','SYNTHETIC-KEY');monkeypatch.setenv('OPENROUTER_MODEL','approved')
    payload=': comment\n\ndata: {"choices":[{"delta":{"content":"hello"}}]}\n\n'+ending
    def respond(request):
        assert json.loads(request.content)['stream'] is True
        return httpx.Response(200,text=payload)
    async def run():return [event async for event in provider_events({},transport=httpx.MockTransport(respond))]
    if valid:assert asyncio.run(run())[-1]=={'type':'usage','model':'approved','tokens':17}
    else:
        with pytest.raises(StreamFailure) as caught:asyncio.run(run())
        assert 'SYNTHETIC' not in str(caught.value)


def test_original_evaluator_detects_actual_config_regression(workspace):
    path=workspace/'data/pipeline_design.json';design=json.loads(path.read_text())
    before=evaluate_selected(path,['EVAL-FC-005','EVAL-FC-003'])
    design['response_policy']['ask_before_model_specific_guidance_when_ids_missing']=False
    path.write_text(json.dumps(design))
    after=evaluate_selected(path,['EVAL-FC-005','EVAL-FC-003'])
    assert before['rows'][0]['pipeline_pass']
    assert not after['rows'][0]['pipeline_pass']
    assert after['rows'][1]['pipeline_pass']
    assert after['design_revision']!=before['design_revision']


def test_running_pipeline_reports_loaded_revision_not_later_file(workspace,tmp_path):
    log=tmp_path/'events.jsonl';server,keys=service(workspace,log)
    original=design_revision(workspace/'data/pipeline_design.json')
    with server,httpx.Client(base_url=server.base_url,trust_env=False) as client:
        path=workspace/'data/pipeline_design.json';path.write_text(path.read_text()+'\n')
        response=client.post('/v1/fieldcare-evidence',json={'case_id':'EVAL-FC-005'},
            headers={'X-API-Key':next(iter(keys.values()))}).json()
        assert response['design_revision']==original
        assert response['design_revision']!=design_revision(path)


def test_provider_multiline_and_missing_usage(monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY','SYNTHETIC-KEY');monkeypatch.setenv('OPENROUTER_MODEL','approved')
    payload=': keepalive\n\ndata: {"choices":\ndata: [{"delta":{"content":"hello"},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n'
    async def run():
        return [e async for e in provider_events({},transport=httpx.MockTransport(lambda req:httpx.Response(200,text=payload)))]
    assert asyncio.run(run())==[{'type':'delta','text':'hello'}]


def test_vendor_hashes_and_evaluator_functions():
    import hashlib
    vendor=ROOT/'src/module_b/_module_a'
    provenance=json.loads((vendor/'provenance.json').read_text())
    for name,digest in provenance['files'].items():
        assert hashlib.sha256((vendor/name).read_bytes()).hexdigest()==digest,name
    assert 'Compare one actual pipeline run' in module_a.evaluate_case.__doc__


def test_checkpoint_checks_hidden_routes_buffering_and_terminal_evidence(workspace):
    from module_b.observability_lab import probe_checkpoint
    source=(workspace/'app/stream_routes.py').read_text()
    # Hide a real replay operation from documentation: it must still be inventoried.
    (workspace/'app/stream_routes.py').write_text(source.replace("@router.post('/v1/fieldcare-buffered')", "@router.post('/v1/fieldcare-buffered',include_in_schema=False)"))
    report=probe_checkpoint(workspace,case_id='EVAL-FC-006',companion='EVAL-FC-003',marker='SYNTHETIC-CHECK-PRIVATE')
    assert report['guard_statuses']['/v1/fieldcare-buffered']==401
    assert report['missing_statuses']['/v1/fieldcare-buffered']==401
    assert all(s==429 for s in report['limited_statuses'].values())
    for key in ['progress_observed','buffered_matches','terminal_records_match','cancellation_observed','recovery_complete','safe_metadata_present','marker_absent']:
        assert report[key],key
    assert report['invalid_status']==422


def test_checkpoint_detects_broken_buffered_consumer(workspace):
    from module_b.observability_lab import probe_checkpoint
    source=(workspace/'app/stream_routes.py').read_text()
    (workspace/'app/stream_routes.py').write_text(source.replace("return {'events':[event async for event in events(body,request)]}","return {'events': []}"))
    report=probe_checkpoint(workspace,case_id='EVAL-FC-006',companion='EVAL-FC-003',marker='SYNTHETIC-BUFFER-PRIVATE')
    assert report['normal_complete']
    assert not report['buffered_matches']


@pytest.mark.parametrize('field',['progress_observed','buffered_matches','terminal_records_match','cancellation_observed','recovery_complete','documented_routes_in_inventory'])
def test_readiness_rejects_missing_delivery_evidence(workspace,field):
    from module_b.observability_lab import review_checkpoint
    from module_b.notebook import baseline,revision
    from module_b.observability import FIELDS
    base=baseline(workspace,'review-entry',[])
    evaluation=evaluate_selected(workspace/'data/pipeline_design.json',['EVAL-FC-006','EVAL-FC-003'])
    observation={'source_revision':revision(workspace),'design_revision':evaluation['design_revision'],
      'normal_complete':True,'interrupted_failed':True,'marker_absent':True,'safe_metadata_present':True,
      'retained_routes':{'/v1/diagnose':200},'selection':{'case_id':'EVAL-FC-006','companion':'EVAL-FC-003'},
      'unauthorized_status':401,'limited_status':429,'invalid_status':422,'logs':[dict.fromkeys(FIELDS)]}
    for flag in ['progress_observed','buffered_matches','terminal_records_match','cancellation_observed','recovery_complete','documented_routes_in_inventory']:observation[flag]=True
    args=dict(inherited=base,observations=observation,eval_before=evaluation,eval_after=evaluation,selected='EVAL-FC-006',companion='EVAL-FC-003',notes={})
    assert review_checkpoint(workspace,**args)['structural_ready']
    observation[field]=False
    assert not review_checkpoint(workspace,**args)['structural_ready']


def test_checkpoint_preserves_two_admission_incoming_policy(workspace):
    from module_b.observability_lab import probe_checkpoint
    path=workspace/'app/security_settings.py'
    source=path.read_text().replace('allowance=4','allowance=2');path.write_text(source)
    report=probe_checkpoint(workspace,case_id='EVAL-FC-005',companion='EVAL-FC-003',marker='SYNTHETIC-TWO-ALLOWANCE')
    assert path.read_text()==source
    assert report['admitted_statuses']==[200,200]
    assert report['isolated_status']==200 and report['limited_status']==429
    assert report['normal_complete'] and report['interrupted_failed'] and report['buffered_matches']
    assert report['experiments']['renewal_tested'] is False
