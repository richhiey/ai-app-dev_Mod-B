"""Private isolated contract probe. No project files or production routes change."""
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


def blocked(*args, **kwargs):
    raise RuntimeError('Network access is disabled in this observation.')


def validation_schema(schema):
    """Ignore schema documentation while preserving instance values verbatim."""
    if not isinstance(schema, dict):
        return schema
    annotations = {'title', 'description', 'examples', '$comment', 'deprecated'}
    maps = {'properties', 'patternProperties', '$defs', 'definitions', 'dependentSchemas'}
    singles = {'additionalProperties', 'unevaluatedProperties', 'propertyNames', 'items',
               'contains', 'not', 'if', 'then', 'else', 'additionalItems', 'unevaluatedItems', 'contentSchema'}
    arrays = {'allOf', 'anyOf', 'oneOf', 'prefixItems'}
    result = {}
    for name, value in schema.items():
        if name in annotations:
            continue
        if name in maps and isinstance(value, dict):
            result[name] = {key: validation_schema(item) for key, item in value.items()}
        elif name in singles:
            result[name] = [validation_schema(item) for item in value] if isinstance(value, list) else validation_schema(value)
        elif name in arrays and isinstance(value, list):
            result[name] = [validation_schema(item) for item in value]
        else:
            # default/const/enum contain data, not schemas. Never edit their keys.
            result[name] = value
    return result


def inspect(project, config):
    report = {'passed': False, 'evidence_kind': 'in_process_demo',
              'external_provider_calls': 0, 'cases': [], 'output_examples': {}, 'errors': []}
    sys.path.insert(0, str(project))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), \
            patch.dict(os.environ, {'FIELDCARE_MODE': 'demo'}, clear=True), \
            patch.object(socket.socket, 'connect', side_effect=blocked), \
            patch.object(socket.socket, 'connect_ex', side_effect=blocked), \
            patch.object(socket, 'create_connection', side_effect=blocked):
        try:
            from fastapi.testclient import TestClient
            from fastapi.exceptions import ResponseValidationError
            app = importlib.import_module('app.main').app
            module = importlib.import_module(config['route_module'])
            adapter_module = importlib.import_module(config['adapter_module'])
            routes = [r for r in module.router.routes
                      if r.path == config['route'] and 'POST' in r.methods]
            if len(routes) != 1 or config['route'] not in app.openapi()['paths']:
                raise ValueError('route not registered')
            route = routes[0]
            request_model = route.body_field.field_info.annotation
            response_model = route.response_model
            request_schema = request_model.model_json_schema()
            field = request_schema['properties'][config['input_field']]
            report['declared_max_length'] = field.get('maxLength')
            report['input_constraint_matches'] = field.get('maxLength') == config['max_length']
            report['input_schema'] = request_schema
            report['input_contract_matches'] = None
            if config.get('expected_input_model') is not None:
                input_module, input_name = config['expected_input_model'].rsplit('.', 1)
                expected_input = getattr(importlib.import_module(input_module), input_name)
                expected_schema = expected_input.model_json_schema()
                expected_schema.pop('title', None)
                expected_schema['properties'][config['input_field']]['maxLength'] = config['max_length']
                observed_schema = dict(request_schema)
                observed_schema.pop('title', None)
                observed_config = {k:v for k,v in request_model.model_config.items() if k not in {'title', 'json_schema_extra'}}
                expected_config = {k:v for k,v in expected_input.model_config.items() if k not in {'title', 'json_schema_extra'}}
                report['input_contract_matches'] = validation_schema(observed_schema) == validation_schema(expected_schema) and observed_config == expected_config
            report['output_schema'] = response_model.model_json_schema()
            output_module, output_name = config['expected_output_model'].rsplit('.', 1)
            expected_output = getattr(importlib.import_module(output_module), output_name)
            report['output_contract_matches'] = response_model.model_json_schema() == expected_output.model_json_schema()
            for name, body in config['output_examples'].items():
                try:
                    response_model.model_validate(body)
                    valid = True
                except Exception:
                    valid = False
                report['output_examples'][name] = {'schema_valid': valid, 'quality_evaluated': False}
            actual_service = getattr(module, config['service_name'])
            adapter = getattr(adapter_module, config['adapter_name'])
            accepted = config['accepted_payload']
            boundary = dict(accepted)
            text = accepted[config['input_field']]
            # Keep the meaningful supported query intact and pad with letters.
            boundary[config['input_field']] = (text + 'x' * config['max_length'])[:config['max_length']]
            oversized = dict(boundary)
            oversized[config['input_field']] += 'x'
            observed = []
            output_errors = []
            async def observed_app(scope, receive, send):
                try:
                    await app(scope, receive, send)
                except ResponseValidationError:
                    output_errors.append(True)
                    raise
                finally:
                    if scope['type'] == 'http':
                        observed.append(getattr(scope.get('endpoint'), '__module__', None))
            def malformed_after_service(*args, **kwargs):
                result = actual_service(*args, **kwargs)
                body = result.model_dump() if hasattr(result, 'model_dump') else dict(result)
                body['citations'] = 'DOC-FC-HX-001'  # INTENTIONALLY invalid array type.
                return body
            with patch.object(adapter_module, config['adapter_name'], wraps=adapter) as calls, \
                    TestClient(observed_app, raise_server_exceptions=False) as client:
                for name, payload, status, count, semantic in [
                    ('accepted', accepted, 200, 1, 'ready'),
                    ('at_limit', boundary, 200, 1, 'ready'),
                    ('over_limit', oversized, 422, 0, None),
                    ('missing_required_input', {k:v for k,v in accepted.items() if k != config['input_field']}, 422, 0, None),
                    ('missing_optional_context', config['incomplete_payload'], 200, 0, 'needs_clarification'),
                    ('malformed_output_after_service', accepted, 500, 1, None),
                ]:
                    before = calls.call_count
                    before_output_errors = len(output_errors)
                    context = patch.object(module, config['service_name'], side_effect=malformed_after_service) \
                        if name == 'malformed_output_after_service' else contextlib.nullcontext()
                    with context:
                        response = client.post(config['route'], json=payload)
                    row = {'case': name, 'status_code': response.status_code,
                           'adapter_calls': calls.call_count - before,
                           'external_provider_calls': 0,
                           'passed': response.status_code == status and calls.call_count - before == count
                                     and bool(observed) and observed[-1] == config['route_module']}
                    if name == 'malformed_output_after_service':
                        row['response_validation_detected'] = len(output_errors) == before_output_errors + 1
                        row['passed'] &= row['response_validation_detected']
                    if status == 200:
                        try:
                            body = response.json()
                            response_model.model_validate(body)
                            row['response_status'] = body.get('status')
                            row['passed'] &= body.get('status') == semantic and body.get('mode') == 'demo'
                        except Exception:
                            row['passed'] = False
                    report['cases'].append(row)
        except Exception:
            report['errors'].append('contract_observation_failed: check route registration, schemas and the configured service seam.')
    report['passed'] = not report['errors'] and report.get('input_constraint_matches', False) \
        and (config.get('expected_input_model') is None or report.get('input_contract_matches', False)) \
        and report.get('output_contract_matches', False) and len(report['cases']) == 6 and all(row['passed'] for row in report['cases'])
    return report


if __name__ == '__main__':
    try:
        with tempfile.TemporaryDirectory(prefix='module-b-contract-cache-') as cache:
            sys.pycache_prefix = cache
            result = inspect(Path(sys.argv[1]), json.loads(sys.argv[2]))
    except Exception:
        result = {'passed': False, 'evidence_kind': 'in_process_demo', 'external_provider_calls': 0,
                  'cases': [], 'errors': ['probe_failed: check the workspace and shared source version.']}
    print(json.dumps(result))
