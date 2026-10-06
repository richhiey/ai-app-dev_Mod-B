import io
import json
import time

import pytest
import requests
from module_b.live_observer import hosted_settings, observe_response, transport_failure


def response(body, *, status=200, content_type='application/x-ndjson', headers=None):
    r=requests.Response();r.status_code=status
    r.headers.update({'Content-Type':content_type,'X-Request-ID':'same-run',**(headers or {})})
    r.raw=io.BytesIO(body.encode())
    return r


def events(*rows):
    return ''.join(json.dumps(row)+'\n' for row in rows)


def test_small_real_stream_preserves_fixture_provenance_and_stops_on_terminal():
    r=response(events({'type':'metadata','mode':'fixture','request_id':'same-run'},
                      {'type':'delta','text':'FIXTURE ONLY'}, {'type':'complete','request_id':'same-run'})+'malformed after terminal')
    seen=[];record=observe_response(r,label='fixture',emit=seen.append)
    assert record['mode']=='fixture' and record['terminal_event']=='complete'
    assert record['delta_count']==1 and record['first_content_ms'] is not None
    assert record['failure'] is None and 'FIXTURE ONLY' in seen
    assert 'FIXTURE ONLY' not in json.dumps(record)


@pytest.mark.parametrize('tail,expected', [('', 'incomplete_stream'),
    (events({'type':'error','request_id':'same-run'}),'service_error_event'),
    ('not-json\n','JSONDecodeError'), ('[]\n','ValueError')])
def test_partial_content_does_not_become_success(tail,expected):
    r=response(events({'type':'delta','text':'partial'})+tail)
    record=observe_response(r,label='partial',emit=lambda _:None)
    assert record['delta_count']==1 and record['failure']==expected
    assert record['terminal_event']!='complete'


def test_mismatched_request_ids_cannot_form_an_evidence_chain():
    r=response(events({'type':'metadata','request_id':'other-run'},{'type':'complete'}))
    record=observe_response(r,label='wrong id',emit=lambda _:None)
    assert record['failure']=='ValueError' and record['terminal_event'] is None


def test_rate_limit_preserves_retry_without_echoing_body():
    r=response('{"detail":"private-value"}',status=429,content_type='application/json',headers={'Retry-After':'12'})
    seen=[];record=observe_response(r,label='limited',emit=seen.append)
    assert record['http_status']==429 and record['retry_after']=='12'
    assert 'private-value' not in json.dumps([seen,record])


def test_json_clarification_is_not_stream_completion():
    r=response(json.dumps({'status':'needs_clarification','answer':'Need context','mode':'live'}),content_type='application/json')
    record=observe_response(r,label='clarification',emit=lambda _:None)
    assert record['application_status']=='needs_clarification'
    assert record['terminal_event'] is None and record['delta_count']==0


@pytest.mark.parametrize('body,ctype', [('[]','application/json'),('<html>login</html>','text/html'),('x'*65537,'application/x-ndjson')])
def test_invalid_response_shapes_are_reported(body,ctype):
    record=observe_response(response(body,content_type=ctype),label='invalid',emit=lambda _:None)
    assert record['failure']=='ValueError'


def test_duration_and_transport_failures_do_not_expose_raw_error():
    record=observe_response(response(events({'type':'delta','text':'late'})),label='late',started=time.monotonic()-2,max_seconds=1,emit=lambda _:None)
    assert record['failure']=='TimeoutError'
    record=transport_failure('offline',requests.ConnectionError('private URL detail'))
    assert record['failure']=='ConnectionError' and 'private' not in json.dumps(record)


@pytest.mark.parametrize('origin',['http://example.com','https://localhost','https://127.0.0.1','https://u:p@example.com','https://example.com/path','https://example.com?key=private'])
def test_caller_setup_rejects_inappropriate_origins(monkeypatch,origin):
    monkeypatch.setenv('FIELDCARE_SERVICE_URL',origin);monkeypatch.setenv('FIELDCARE_CALLER_KEY','synthetic')
    with pytest.raises(ValueError):hosted_settings()


def test_local_jupyter_settings_use_private_environment(monkeypatch):
    monkeypatch.setenv('FIELDCARE_SERVICE_URL','https://course.example/');monkeypatch.setenv('FIELDCARE_CALLER_KEY','synthetic')
    assert hosted_settings()==('https://course.example','synthetic')
