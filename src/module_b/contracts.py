"""Reusable contract observations for trusted course ASGI workspaces.

The defaults describe FieldCare's supplied service seam. Override the dotted
adapter location and route binding to reuse the same observations elsewhere.
This is a structural rehearsal, never an answer-quality evaluator.
"""
from collections.abc import Mapping
import json
from pathlib import Path
import re
import subprocess
import sys


def inspect_contract(project: Path, *, route: str, route_module: str,
                     max_length: int, accepted_payload: Mapping,
                     incomplete_payload: Mapping, input_field: str = 'question',
                     adapter_module: str = 'app.service',
                     adapter_name: str = 'generate_answer',
                     service_name: str = 'run_diagnosis',
                     expected_output_model: str = 'app.schemas.DiagnosticResponse',
                     expected_input_model: str | None = None,
                     output_examples: Mapping | None = None) -> dict:
    """Observe input/output validation in a fresh, credential-free interpreter.

    ``route_module`` exposes ``router`` and a synchronous callable named by
    ``service_name``. Its original callable runs before a temporary malformed
    result is injected; project files never change. ``adapter_module`` exposes
    the model adapter used by that callable. The demo profile blocks network
    sockets and strips inherited credentials. Counts are adapter invocations,
    NOT external model calls or cost measurements. Configure this explicitly
    for compatible future examples; arbitrary ASGI architectures need their
    own adapter seam. ``expected_output_model`` names the supplied output class that the route
    must preserve. Optional example bodies are checked only for shape. When expected_input_model
    is supplied, require the same validation schema (ignoring documentation annotations and
    replacing input_field maxLength with max_length) and the same model_config.
    This preserves requiredness, extra-field policy, trimming and other constraints.
    """
    project = Path(project).resolve()
    if not project.is_dir():
        raise ValueError('Choose an existing workspace.')
    if not isinstance(route, str) or not re.fullmatch(r'/[A-Za-z0-9_/-]+', route):
        raise ValueError('Supply an absolute route without query strings.')
    for name in (route_module, adapter_module, expected_output_model, *([expected_input_model] if expected_input_model is not None else [])):
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+', name):
            raise ValueError('Supply dotted module names.')
    for name in (input_field, adapter_name, service_name):
        if not isinstance(name, str) or not name.isidentifier():
            raise ValueError('Supply valid field/function names.')
    if isinstance(max_length, bool) or not isinstance(max_length, int) or max_length < 1:
        raise ValueError('max_length must be a positive integer.')
    if not isinstance(accepted_payload.get(input_field), str) or not accepted_payload[input_field].strip():
        raise ValueError('The accepted example needs nonempty text in input_field.')
    config = dict(route=route, route_module=route_module, max_length=max_length,
                  accepted_payload=dict(accepted_payload), incomplete_payload=dict(incomplete_payload),
                  input_field=input_field, adapter_module=adapter_module,
                  adapter_name=adapter_name, service_name=service_name,
                  expected_output_model=expected_output_model, expected_input_model=expected_input_model,
                  output_examples=dict(output_examples or {}))
    worker = Path(__file__).with_name('_contract_probe.py')
    try:
        result = subprocess.run([sys.executable, str(worker), str(project), json.dumps(config)],
                                capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise ValueError('worker failed')
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, ValueError):
        return {'passed': False, 'evidence_kind': 'in_process_demo', 'external_provider_calls': 0,
                'cases': [], 'errors': ['probe_failed: check the workspace, imports and service seam.']}
