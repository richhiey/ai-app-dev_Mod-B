"""Isolated FieldCare route contract probe; never calls an external provider.

Private implementation for ``fieldcare.inspect_route_bindings``. This is a
learning check for trusted local code, not a sandbox for hostile Python.
"""
import contextlib
import importlib
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch

sys.dont_write_bytecode = True

_REQUEST_SCHEMA = {
    'additionalProperties': False,
    'properties': {
        'question': {'maxLength': 2000, 'minLength': 1, 'title': 'Question', 'type': 'string'},
        'equipment_id': {'anyOf': [{'maxLength': 64, 'minLength': 1, 'type': 'string'}, {'type': 'null'}],
                         'default': None, 'title': 'Equipment Id'},
    },
    'required': ['question'], 'title': 'DiagnosticRequest', 'type': 'object',
}
_RESPONSE_SCHEMA = {
    'additionalProperties': False,
    'properties': {
        'answer': {'minLength': 1, 'title': 'Answer', 'type': 'string'},
        'status': {'enum': ['ready', 'needs_clarification'], 'title': 'Status', 'type': 'string'},
        'citations': {'items': {'type': 'string'}, 'title': 'Citations', 'type': 'array'},
        'mode': {'enum': ['demo', 'live'], 'title': 'Mode', 'type': 'string'},
    },
    'required': ['answer', 'status', 'citations', 'mode'],
    'title': 'DiagnosticResponse', 'type': 'object',
}
_CASES = {
    'valid': {'question': 'What filter and airflow checks are documented for this equipment?',
              'equipment_id': 'EQ-FC-1002'},
    'invalid': {'equipment_id': 'EQ-FC-1002'},
    'incomplete': {'question': 'The unit runs hot after service.'},
}
_MOCK_ANSWER = 'MOCK: route wiring checked; generated wording has not been evaluated.'


def _blocked(*args, **kwargs):
    raise RuntimeError('Network access is disabled in this probe.')


def inspect(root: Path, routes: dict[str, str]) -> dict:
    report = {'evidence_kind': 'in_process_mocked_provider', 'passed': False,
              'external_provider_calls': 0, 'errors': [], 'routes': []}
    sys.path.insert(0, str(root))
    # Import logs and exceptions from learner code must not leak secrets into
    # the notebook. All returned errors below are fixed, actionable messages.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), \
            patch.dict(os.environ, {'FIELDCARE_MODE': 'live', 'OPENROUTER_MODEL': 'mock/model',
                                    'OPENROUTER_API_KEY': 'synthetic-not-a-real-key'}, clear=True), \
            patch.object(socket.socket, 'connect', side_effect=_blocked), \
            patch.object(socket.socket, 'connect_ex', side_effect=_blocked), \
            patch.object(socket, 'create_connection', side_effect=_blocked):
        try:
            import httpx
            from fastapi.routing import APIRoute
            from fastapi.testclient import TestClient
            app = importlib.import_module('app.main').app
            model = importlib.import_module('app.model')
            service = importlib.import_module('app.service')
            schemas = importlib.import_module('app.schemas')
            baseline = importlib.import_module('app.routes').SYSTEM_PROMPT
            openapi = app.openapi()
        except Exception:
            report['errors'].append('app_import_failed: check Python syntax, app.main and the shared scaffold imports.')
            return report

        for path, module_name in routes.items():
            row = {'path': path, 'module': module_name, 'registered': False,
                   'request_schema_ok': False, 'response_schema_ok': False,
                   'distinct_from_baseline': None, 'prompt_binding_ok': False,
                   'cases': [], 'errors': [], 'passed': False}
            report['routes'].append(row)
            try:
                module = importlib.import_module(module_name)
                prompt = getattr(module, 'SYSTEM_PROMPT', None)
            except Exception:
                row['errors'].append('module_import_failed: check the module name, file and Python syntax.')
                continue
            row['distinct_from_baseline'] = None if path == '/v1/diagnose' else bool(
                isinstance(prompt, str) and prompt.strip() and prompt != baseline)
            # Inspect the public module router; newer FastAPI versions defer
            # flattening included routers on app.routes. OpenAPI and the
            # endpoint observed during requests establish actual registration.
            registered = [route for route in getattr(getattr(module, 'router', None), 'routes', [])
                          if isinstance(route, APIRoute) and route.path == path and 'POST' in route.methods]
            operation = openapi.get('paths', {}).get(path, {}).get('post', {})
            row['registered'] = bool(operation) and len(registered) == 1 and registered[0].endpoint.__module__ == module_name
            if not row['registered']:
                row['errors'].append('route_registration_failed: register exactly one POST route from the supplied module.')
            if len(registered) == 1:
                route = registered[0]
                row['request_schema_ok'] = bool(route.body_field is not None
                    and route.body_field.field_info.annotation is schemas.DiagnosticRequest
                    and schemas.DiagnosticRequest.model_json_schema() == _REQUEST_SCHEMA
                    and schemas.DiagnosticRequest.model_config.get('str_strip_whitespace') is True
                    and operation.get('requestBody', {}).get('content', {}).get('application/json', {}).get('schema', {}).get('$ref') == '#/components/schemas/DiagnosticRequest')
                row['response_schema_ok'] = bool(route.response_model is schemas.DiagnosticResponse
                    and schemas.DiagnosticResponse.model_json_schema() == _RESPONSE_SCHEMA
                    and operation.get('responses', {}).get('200', {}).get('content', {}).get('application/json', {}).get('schema', {}).get('$ref') == '#/components/schemas/DiagnosticResponse')
            if not row['request_schema_ok'] or not row['response_schema_ok']:
                row['errors'].append('schema_contract_failed: retain DiagnosticRequest and DiagnosticResponse unchanged.')
            if row['distinct_from_baseline'] is False:
                row['errors'].append('prompt_not_distinct: give the new route its own nonempty SYSTEM_PROMPT.')

            posted = []
            endpoints = []
            async def observed_app(scope, receive, send):
                await app(scope, receive, send)
                if scope['type'] == 'http':
                    endpoints.append(getattr(scope.get('endpoint'), '__module__', None))
            def fake_post(url, *, headers, json, timeout):
                posted.append({'prompt': json.get('messages', [{}])[0].get('content'),
                               'boundary_ok': url == 'https://openrouter.ai/api/v1/chat/completions'
                               and json.get('model') == 'mock/model'})
                return httpx.Response(200, request=httpx.Request('POST', str(url)), json={
                    'choices': [{'finish_reason': 'stop', 'message': {'content': _MOCK_ANSWER}}]})

            try:
                with patch.object(model.httpx, 'post', side_effect=fake_post) as provider, \
                        patch.object(service, 'generate_answer', wraps=model.generate_answer) as adapter, \
                        TestClient(observed_app, raise_server_exceptions=False) as client:
                    for name, payload in _CASES.items():
                        before_model, before_provider = adapter.call_count, provider.call_count
                        before_posts = len(posted)
                        response = client.post(path, json=payload)
                        if not endpoints or endpoints[-1] != module_name:
                            row['registered'] = False
                        model_calls, provider_calls = adapter.call_count - before_model, provider.call_count - before_provider
                        expected_status = 422 if name == 'invalid' else 200
                        expected_calls = 1 if name == 'valid' else 0
                        case = {'case': name, 'status_code': response.status_code,
                                'model_calls': model_calls, 'provider_calls': provider_calls,
                                'passed': response.status_code == expected_status
                                and model_calls == expected_calls and provider_calls == expected_calls}
                        if name == 'valid':
                            row['prompt_binding_ok'] = bool(isinstance(prompt, str) and prompt.strip()
                                and len(posted) == before_posts + 1 and posted[-1]['prompt'] == prompt
                                and posted[-1]['boundary_ok'])
                        if name != 'invalid':
                            try:
                                body = response.json()
                                schemas.DiagnosticResponse.model_validate(body)
                                case['passed'] = case['passed'] and body['mode'] == 'live' and (
                                    body['status'] == 'ready' and body['answer'] == _MOCK_ANSWER
                                    if name == 'valid' else body['status'] == 'needs_clarification')
                            except Exception:
                                case['passed'] = False
                        row['cases'].append(case)
            except Exception:
                row['errors'].append('request_probe_failed: check lifespan, route and service code using the notebook demo run.')
            if not row['registered'] and not any(error.startswith('route_registration_failed:') for error in row['errors']):
                row['errors'].append('route_registration_failed: the requested path reached a different module.')
            if not row['prompt_binding_ok']:
                row['errors'].append('prompt_binding_failed: pass this module’s SYSTEM_PROMPT to the shared model path.')
            if len(row['cases']) != 3 or not all(case['passed'] for case in row['cases']):
                row['errors'].append('request_behavior_failed: compare statuses and model/provider counts with the three required cases.')
            row['passed'] = not row['errors']
    report['passed'] = bool(report['routes']) and not report['errors'] and all(row['passed'] for row in report['routes'])
    return report


if __name__ == '__main__':
    try:
        # A fresh interpreter can otherwise read a same-timestamp .pyc left
        # by a running demo after a quick learner edit. Never read those caches.
        with tempfile.TemporaryDirectory(prefix='module-b-probe-cache-') as cache:
            sys.pycache_prefix = cache
            result = inspect(Path(sys.argv[1]), json.loads(sys.argv[2]))
    except Exception:
        result = {'evidence_kind': 'in_process_mocked_provider', 'passed': False,
                  'external_provider_calls': 0, 'routes': [],
                  'errors': ['probe_failed: check the selected workspace and shared source version.']}
    print(json.dumps(result))
