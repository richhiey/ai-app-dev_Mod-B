"""Transport and UI regression checks. Install examples/streamlit/requirements.txt for UI checks."""
import json
from pathlib import Path
import sys

import httpx
import pytest

UI = Path(__file__).resolve().parents[1] / 'examples/streamlit'
sys.path.insert(0, str(UI))
import fieldcare_client as fc


def fake_transport(monkeypatch, handler):
    original = httpx.Client
    monkeypatch.setattr(fc.httpx, 'Client', lambda **kwargs: original(transport=httpx.MockTransport(handler), **kwargs))


def test_client_stream_contract_and_private_header(monkeypatch):
    def respond(request):
        assert str(request.url) == 'http://127.0.0.1:8001/v1/diagnose-stream'
        assert request.headers['x-api-key'] == 'test-only'
        assert json.loads(request.content) == {'question': 'A question'}
        events = [{'type':'metadata','mode':'fixture','citations':[]}, {'type':'delta','text':'one'}, {'type':'complete'}]
        return httpx.Response(200, headers={'content-type':'application/x-ndjson','x-request-id':'request-1'},
                              text='\n'.join(json.dumps(e) for e in events))
    fake_transport(monkeypatch, respond)
    events=list(fc.stream_diagnosis(fc.make_input(' A question ', ' '), base_url='http://127.0.0.1:8001', caller_key='test-only'))
    assert events[0]['request_id']=='request-1'
    assert events[-1]['type']=='complete'


@pytest.mark.parametrize('url',['https://example.com','http://127.0.0.1@evil.test','http://localhost/other','http://127.0.0.1:8001?x=y'])
def test_client_rejects_nonlocal_or_nonorigin_targets(url):
    with pytest.raises(fc.FieldCareError):
        list(fc.stream_diagnosis({'question':'q'},base_url=url,caller_key='test-only'))


def test_clarification_and_retry_after_are_preserved(monkeypatch):
    fake_transport(monkeypatch, lambda _: httpx.Response(200, headers={'x-request-id':'clarify-1'},
                   json={'status':'needs_clarification','answer':'Which equipment?','citations':[],'mode':'live'}))
    event=list(fc.stream_diagnosis({'question':'q'},base_url='http://localhost:8001',caller_key='test-only'))[0]
    assert event['type']=='response' and event['request_id']=='clarify-1'
    monkeypatch.undo()
    fake_transport(monkeypatch, lambda _: httpx.Response(429,headers={'retry-after':'42','x-request-id':'limit-1'},text='PRIVATE BODY'))
    with pytest.raises(fc.FieldCareError) as raised:
        list(fc.stream_diagnosis({'question':'q'},base_url='http://localhost:8001',caller_key='test-only'))
    assert raised.value.retry_after==42 and raised.value.request_id=='limit-1'
    assert 'PRIVATE' not in str(raised.value)


@pytest.mark.parametrize('text',['{"type":"delta","text":"partial"}\n','not-json\n'])
def test_broken_stream_never_completes(monkeypatch,text):
    fake_transport(monkeypatch, lambda _: httpx.Response(200,headers={'content-type':'application/x-ndjson'},text=text))
    with pytest.raises(fc.FieldCareError):
        list(fc.stream_diagnosis({'question':'q'},base_url='http://localhost:8001',caller_key='test-only'))


def app_test():
    pytest.importorskip('streamlit')
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(UI/'app_reference.py'),default_timeout=15).run()


def send(app, question="Which filter and airflow checks are documented?"):
    return app.chat_input[0].set_value(question).run()


def test_ui_demo_chat_history_clarification_failure_and_rerun():
    app = app_test()
    assert not app.exception
    send(app, '   ')
    assert 'Enter a question' in app.error[0].value
    assert app.session_state.turns == []
    app.text_input[0].set_value('EQ-FC-1002')
    send(app)
    saved = app.session_state.turns[0]['result'].copy()
    assert saved['status'] == 'Complete' and saved['request_id'] == 'demo-001'
    assert len(app.chat_message) == 2
    app.checkbox[0].check().run()
    assert app.session_state.turns[0]['result'] == saved
    app.text_input[0].set_value('')
    send(app)
    assert app.session_state.turns[-1]['result']['status'] == 'Needs clarification'
    app.selectbox[0].set_value('Unavailable').run()
    send(app)
    failed = app.session_state.turns[-1]['result']
    assert failed['status'] == 'Error' and failed['answer'] == '' and failed['request_id'] == ''
    assert app.session_state.turns[0]['result'] == saved
    assert len(app.chat_message) == 6
    app.selectbox[0].set_value('Interrupted').run()
    app.text_input[0].set_value('EQ-FC-1002')
    send(app)
    assert app.session_state.turns[-1]['result']['status'] == 'Error'
    assert app.session_state.turns[-1]['result']['answer'].startswith('MOCK ONLY')
    assert any('Incomplete' in warning.value for warning in app.warning)
    assert not app.exception


def test_ui_real_client_called_only_on_submit_or_explicit_retry(monkeypatch):
    calls = []
    def stream(payload, **settings):
        calls.append(payload)
        if len(calls) == 1:
            raise fc.FieldCareError('Try again', request_id='failed-1', retry_after=1)
        yield {'type':'metadata','mode':'fixture','request_id':'http-2','citations':[]}
        yield {'type':'delta','text':'FIXTURE ONLY'}
        yield {'type':'complete'}
    monkeypatch.setattr(fc,'stream_diagnosis',stream)
    monkeypatch.setattr(fc,'load_settings',lambda:('http://localhost:8001','test-only'))
    app = app_test()
    app.radio[0].set_value('Local service').run()
    assert calls == []
    app.text_input[0].set_value('EQ-FC-1002')
    send(app, 'question')
    assert len(calls) == 1
    assert app.session_state.turns[-1]['result']['request_id'] == 'failed-1'
    app.checkbox[0].check().run()
    app.text_input[0].set_value('DIFFERENT').run()
    assert len(calls) == 1
    next(b for b in app.button if b.label == 'Retry this message').click().run()
    assert len(calls) == 2 and calls[1] == calls[0]
    assert app.session_state.turns[-1]['result']['mode'] == 'fixture'
    assert app.session_state.turns[-1]['retry']
    assert len(app.session_state.turns) == 2
    next(b for b in app.button if b.label == 'New chat').click().run()
    assert app.session_state.turns == [] and len(calls) == 2
    assert not app.exception


@pytest.mark.parametrize('usage, expected_tokens, expected_model', [
    (None, None, None),
    ({'type': 'usage', 'tokens': None, 'model': None}, None, None),
    ({'type': 'usage', 'tokens': 0, 'model': 'reported-test-model'}, 0, 'reported-test-model'),
    ({'type': 'usage', 'tokens': 17, 'model': 'reported-test-model'}, 17, 'reported-test-model'),
    ({'type': 'usage', 'tokens': True, 'model': 123}, None, None),
])
def test_ui_observations_preserve_missing_and_zero_usage(monkeypatch, usage, expected_tokens, expected_model):
    calls = []
    def stream(payload, **settings):
        calls.append(payload)
        yield {'type': 'metadata', 'mode': 'live', 'request_id': 'observed-1', 'citations': ['DOC-1']}
        yield {'type': 'delta', 'text': 'One '}
        yield {'type': 'delta', 'text': 'reply'}
        if usage is not None:
            yield usage
        yield {'type': 'complete'}
    monkeypatch.setattr(fc, 'stream_diagnosis', stream)
    monkeypatch.setattr(fc, 'load_settings', lambda: ('http://localhost:8000', 'test-only'))
    app = app_test()
    app.radio[0].set_value('Local service').run()
    assert calls == []  # Displaying configured settings is not a service request.
    assert any('Configured target: http://localhost:8000/v1/diagnose-stream' in c.value for c in app.caption)
    send(app)
    result = app.session_state.turns[0]['result']
    assert result['status'] == 'Complete'
    assert result['tokens'] == expected_tokens and result['model'] == expected_model
    assert result['chunks'] == 2 and result['answer'] == 'One reply'
    assert 0 <= result['first_text_ms'] <= result['elapsed_ms']
    assert result['citations'] == ['DOC-1'] and result['request_id'] == 'observed-1'
    assert result['target'] == 'http://localhost:8000/v1/diagnose-stream'
    assert result['events'] == ['metadata', 'delta'] + (['usage'] if usage is not None else []) + ['complete']
    visible = app.table[0].value.set_index('Signal')['Observed'].to_dict()
    assert visible['Reported total tokens'] == ('Not reported' if expected_tokens is None else str(expected_tokens))
    assert visible['Reported model'] == (expected_model or 'Not reported')
    app.checkbox[0].check().run()
    assert len(calls) == 1 and app.session_state.turns[0]['result'] == result
    assert not app.exception


def test_ui_error_after_success_has_fresh_telemetry_and_partial_failure_is_not_complete(monkeypatch):
    calls = []
    def stream(payload, **settings):
        calls.append(payload)
        if len(calls) == 2:
            raise fc.FieldCareError('Unauthorized caller.', status_code=401, request_id='auth-2')
        yield {'type': 'metadata', 'mode': 'live', 'request_id': 'stream-' + str(len(calls)), 'citations': ['DOC-1']}
        yield {'type': 'delta', 'text': 'partial' if len(calls) == 3 else 'complete'}
        if len(calls) == 3:
            yield {'type': 'error', 'request_id': 'stream-3', 'category': 'provider_interrupted'}
        else:
            yield {'type': 'usage', 'tokens': 17, 'model': 'reported-test-model'}
            yield {'type': 'complete'}
    monkeypatch.setattr(fc, 'stream_diagnosis', stream)
    monkeypatch.setattr(fc, 'load_settings', lambda: ('http://localhost:8000', 'test-only'))
    app = app_test()
    app.radio[0].set_value('Local service').run()
    send(app)
    successful = app.session_state.turns[0]['result'].copy()
    send(app)
    rejected = app.session_state.turns[1]['result']
    assert rejected['status'] == 'Error' and rejected['http_status'] == 401
    assert rejected['request_id'] == 'auth-2' and rejected['answer'] == '' and rejected['citations'] == []
    assert rejected['tokens'] is None and rejected['model'] is None and rejected['first_text_ms'] is None
    assert rejected['events'] == [] and rejected['chunks'] == 0
    send(app)
    partial = app.session_state.turns[2]['result']
    assert partial['status'] == 'Error' and partial['answer'] == 'partial'
    assert partial['events'] == ['metadata', 'delta', 'error'] and partial['chunks'] == 1
    assert partial['request_id'] == 'stream-3' and partial['tokens'] is None
    assert any('Incomplete response' in warning.value for warning in app.warning)
    assert app.session_state.turns[0]['result'] == successful
    assert len(calls) == 3 and not app.exception
