"""Private isolated worker for inspect_version_bindings; trusted local course code only."""
import contextlib
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
from unittest.mock import patch


def blocked(*args, **kwargs):
    raise RuntimeError('Network disabled in binding observation.')


def inspect(root, config):
    report = {'passed':False, 'evidence_kind':'in_process_mocked_provider',
              'external_provider_calls':0, 'rounds':[], 'errors':[]}
    specs = config['versions']
    model_values = {path:f'mock/version-{index}' for index,path in enumerate(specs,1)}
    env = {'FIELDCARE_MODE':'live', 'OPENROUTER_MODEL':'mock/baseline',
           'OPENROUTER_API_KEY':'synthetic-not-a-real-key'}
    for path, spec in specs.items():
        env[spec['model_env']] = model_values[path]
    sys.path.insert(0, str(root))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), \
         patch.dict(os.environ, env, clear=True), \
         patch.object(socket.socket, 'connect', side_effect=blocked), \
         patch.object(socket.socket, 'connect_ex', side_effect=blocked), \
         patch.object(socket, 'create_connection', side_effect=blocked):
        try:
            import httpx
            from fastapi.testclient import TestClient
            app = importlib.import_module('app.main').app
            model = importlib.import_module('app.model')
            schema = importlib.import_module('app.schemas').DiagnosticResponse
            modules = {path:importlib.import_module(spec['module']) for path,spec in specs.items()}
            prompts = {path:module.SYSTEM_PROMPT for path,module in modules.items()}
            if any(not isinstance(value, str) or not value.strip() for value in prompts.values()):
                report['errors'].append('empty_prompt: each route requires a nonempty prompt.')
            if len({s['module'] for s in specs.values()}) != len(specs) or len({s['model_env'] for s in specs.values()}) != len(specs):
                report['errors'].append('shared_binding: use distinct route modules and model environment names.')
            observed = []
            def fake_post(url, *, headers, json, timeout):
                observed.append({'prompt':json['messages'][0]['content'], 'model':json['model'],
                                 'provider_url_ok':url == 'https://openrouter.ai/api/v1/chat/completions'})
                return httpx.Response(200, request=httpx.Request('POST',url), json={
                    'choices':[{'finish_reason':'stop','message':{'content':'MOCK: wiring observed; wording not evaluated.'}}]})
            for round_name in ('before_change', 'after_selected_route_change'):
                if round_name == 'after_selected_route_change':
                    changed = config['changed_route']
                    prompts[changed] += '\nSynthetic isolated v2-only observation change.'
                    model_values[changed] = 'mock/changed-version'
                    modules[changed].SYSTEM_PROMPT = prompts[changed]
                    modules[changed].MODEL_NAME = model_values[changed]
                rows = []
                with patch.object(model.httpx, 'post', side_effect=fake_post), TestClient(app,raise_server_exceptions=False) as client:
                    for path,spec in specs.items():
                        previous = len(observed)
                        response = client.post(path,json=config['payload'])
                        posts = observed[previous:]
                        body_valid = False
                        try:
                            body = schema.model_validate(response.json())
                            body_valid = body.mode == 'live' and body.status == 'ready'
                        except Exception:
                            pass
                        prompt_ok = len(posts)==1 and posts[0]['prompt']==prompts[path]
                        model_ok = len(posts)==1 and posts[0]['model']==model_values[path]
                        rows.append({'path':path,'module':spec['module'],'model_env':spec['model_env'],
                                     'status_code':response.status_code,'mock_provider_calls':len(posts),
                                     'prompt_binding_ok':prompt_ok,'model_binding_ok':model_ok,
                                     'observed_prompt_sha256':hashlib.sha256(posts[0]['prompt'].encode()).hexdigest() if len(posts)==1 else None,
                                     'observed_model':(posts[0]['model'] if model_ok else '<unexpected model binding>') if len(posts)==1 else None,
                                     'passed':response.status_code==200 and body_valid and prompt_ok and model_ok
                                              and posts[0]['provider_url_ok']})
                report['rounds'].append({'round':round_name,'routes':rows})
        except Exception:
            report['errors'].append('observation_failed: check route registration, module constants and service calls.')
    report['passed'] = not report['errors'] and len(report['rounds'])==2 and all(
        row['passed'] for group in report['rounds'] for row in group['routes'])
    return report


if __name__ == '__main__':
    try:
        with tempfile.TemporaryDirectory(prefix='module-b-version-cache-') as cache:
            sys.pycache_prefix = cache
            sys.dont_write_bytecode = True
            result = inspect(Path(sys.argv[1]),json.loads(sys.argv[2]))
    except Exception:
        result = {'passed':False,'evidence_kind':'in_process_mocked_provider','external_provider_calls':0,
                  'rounds':[], 'errors':['observation_failed: check workspace and route binding configuration.']}
    print(json.dumps(result))
