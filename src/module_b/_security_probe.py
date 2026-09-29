"""Isolated local teaching observations, not a sandbox for untrusted Python."""
import contextlib
import io
import json
import os
from pathlib import Path
import secrets
import socket
import sys
from unittest.mock import patch
from fastapi.testclient import TestClient
from module_b.security import ConfigurationError

project=Path(sys.argv[1]); config=json.loads(sys.argv[2])
sys.path.insert(0,str(project))
os.environ['FIELDCARE_MODE']='demo'
os.environ.pop('OPENROUTER_API_KEY',None)
os.environ.pop('OPENROUTER_MODEL',None)
keys={label:secrets.token_urlsafe(32) for label in config['caller_env']}
for label,name in config['caller_env'].items(): os.environ[name]=keys[label]
if config.get('missing_env'): os.environ.pop(config['missing_env'],None)
clock=[0.0]
report={'evidence_kind':'in_process_demo','external_provider_calls':0,'rows':[]}
def no_network(*args,**kwargs): raise RuntimeError('External network disabled in demo probe.')
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), patch.object(socket.socket,'connect',no_network), patch.object(socket,'create_connection',no_network), patch('module_b.security.service_clock',side_effect=lambda:clock[0]):
    try:
        from app.main import app
        import app.service as service
        from module_b.security import protected_post_paths
        report['routes']=list(protected_post_paths(app))
        try:
            from app.security_settings import CALLER_ENV, POLICY
            report['configuration']={'caller_env':CALLER_ENV, 'allowance':POLICY.allowance if POLICY else None,
                                     'window_seconds':POLICY.window_seconds if POLICY else None}
        except ModuleNotFoundError as error:
            if error.name != 'app.security_settings':raise
            report['configuration']=None  # Older examples can attach configuration directly.
        fixture=json.loads((project/'fixtures/valid-request.json').read_text())
        original=service.generate_answer
        with patch.object(service,'generate_answer',wraps=original) as adapter, TestClient(app,raise_server_exceptions=False) as client:
            for step in config['sequence']:
                next_time=float(step.get('at',clock[0]))
                if next_time < clock[0]: raise ValueError('Timeline must be nondecreasing.')
                clock[0]=next_time
                caller=step['caller']; path=step['path']
                headers={} if caller=='missing' else {'X-API-Key':keys.get(caller,'invalid-local-probe')}
                before=adapter.call_count
                response=client.post(path,json=step.get('payload',fixture),headers=headers)
                report['rows'].append({'at':clock[0],'caller':caller,'path':path,
                    'status':response.status_code,'adapter_calls':adapter.call_count-before,
                    'retry_after':response.headers.get('retry-after'),
                    'response_status':response.json().get('status') if response.status_code==200 else None,
                    'response_fields':sorted(response.json()) if response.headers.get('content-type','').startswith('application/json') and isinstance(response.json(),dict) else []})
            report['public']={p:client.get(p).status_code for p in ('/health','/docs','/openapi.json')}
            report['startup']='ready'
    except ConfigurationError:
        report['startup']='refused_missing_or_invalid_caller_configuration'
print(json.dumps(report))
