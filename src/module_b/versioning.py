"""Isolated FieldCare version-binding observations for any compatible route pair."""
from collections.abc import Mapping
import json
from pathlib import Path
import re
import subprocess
import sys


def inspect_version_bindings(project, *, versions, changed_route, accepted_payload):
    """Exercise route-specific prompt/model settings at the mocked provider boundary.

    versions maps each POST path to {module, model_env}; compatible modules expose
    SYSTEM_PROMPT and MODEL_NAME and use the supplied FieldCare service/adapter.
    Distinct synthetic model identifiers are injected through the named environment
    settings before import. A second round changes ONLY changed_route's module
    constants in memory. Reports hashes, statuses and binding booleans, never source
    prompts, credentials or learner exception text. Files are untouched. Real TCP
    calls and generated-answer evaluation must be recorded separately.
    """
    project = Path(project).resolve()
    if not project.is_dir() or not isinstance(versions, Mapping) or len(versions) < 2:
        raise ValueError('Choose an existing workspace and at least two version bindings.')
    for path, spec in versions.items():
        if not isinstance(path, str) or not re.fullmatch(r'/[A-Za-z0-9_/-]+', path):
            raise ValueError('Version routes must be absolute paths without query strings.')
        if not isinstance(spec, Mapping) or set(spec) != {'module', 'model_env'}:
            raise ValueError('Each binding needs module and model_env.')
        if not isinstance(spec['module'], str) or not re.fullmatch(r'app(?:\.[A-Za-z_]\w*)+', spec['module']):
            raise ValueError('Choose a dotted module within app.')
        if not isinstance(spec['model_env'], str) or not re.fullmatch(r'[A-Z][A-Z0-9_]*', spec['model_env']):
            raise ValueError('Choose an explicit model environment name.')
    if changed_route not in versions or not isinstance(accepted_payload, Mapping):
        raise ValueError('Choose one supplied changed route and an accepted request mapping.')
    config = {'versions':dict(versions),'changed_route':changed_route,'payload':dict(accepted_payload)}
    try:
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('_version_probe.py')),
                                 str(project), json.dumps(config)], capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise ValueError('worker failed')
        return json.loads(result.stdout)
    except (ValueError, subprocess.TimeoutExpired):
        return {'passed':False,'evidence_kind':'in_process_mocked_provider','external_provider_calls':0,
                'rounds':[], 'errors':['probe_failed: check imports, route registration and shared source version.']}
