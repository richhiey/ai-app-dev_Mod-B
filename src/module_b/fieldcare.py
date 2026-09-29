"""Case-specific inspection helpers; no production service implementation here."""
from collections.abc import Mapping
import json
from pathlib import Path
import subprocess
import sys


def trace_paths(project: Path) -> list[dict]:
    """Run NEW isolated in-process requests, not counters from a running server.

    Wraps actual service/adapter functions in the selected workspace. Forbids
    external provider calls. A separate interpreter avoids cached app imports.
    """
    worker = Path(__file__).with_name("_fieldcare_probe.py")
    result = subprocess.run(
        [sys.executable, str(worker), str(Path(project).resolve())],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode:
        raise RuntimeError("Trace failed. Check the selected workspace against the starter; the probe expected the demo paths.")
    return json.loads(result.stdout)


def verify_prompt_binding(project: Path) -> str:
    """Inspect separate route prompt bindings with mocked provider HTTP only."""
    worker = Path(__file__).with_name("_configuration_probe.py")
    result = subprocess.run([sys.executable, str(worker), str(Path(project).resolve())],
                            capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise RuntimeError("Binding check failed. Check route registration and the distinct supplied prompts.")
    return result.stdout.strip()


def demo_service(project_dir: Path, **runtime_options):
    """Configure the generic runner for FieldCare's credential-free demo.

    Environment overrides are intentionally not accepted here. Use the generic
    ServiceProcess directly with explicit settings for provider-backed work.
    Other options (port, health policy, factory, etc.) pass through to the runner.
    """
    from module_b.runtime import ServiceProcess
    if 'env' in runtime_options:
        raise ValueError('demo_service owns its demo environment; use ServiceProcess for custom settings.')
    return ServiceProcess(project_dir=project_dir, env={
        'FIELDCARE_MODE': 'demo',
        'OPENROUTER_API_KEY': None,
        'OPENROUTER_MODEL': None,
    }, **runtime_options)


def inspect_route_bindings(project: Path, routes: Mapping[str, str]) -> dict:
    """Check arbitrary FieldCare route modules against the fixed C04 contract.

    ``routes`` maps POST paths to dotted Python modules, e.g. the original path
    to ``app.routes`` plus a learner-chosen extension. Runs a fresh interpreter,
    imports the app once, and exercises valid/invalid/incomplete requests with
    TestClient and a mocked provider. No prompt text, response body, inherited
    credentials or learner exception text is returned. This checks wiring and
    schemas, not the quality of generated answers or a running TCP server.

    The report includes ``passed``, safe ``errors`` and per-route ``cases`` with
    actual statuses and adapter/provider call counts. Failed learner work is a
    report, not an exception. Network sockets are blocked in the child process;
    this is a checker for trusted course code, not a hostile-code sandbox.
    """
    import re
    project = Path(project).resolve()
    if not project.is_dir():
        raise ValueError('Choose an existing service workspace directory.')
    if not isinstance(routes, Mapping) or not routes:
        raise ValueError('Supply at least one POST path mapped to a dotted module name.')
    for path, module in routes.items():
        if not isinstance(path, str) or not re.fullmatch(r'/[A-Za-z0-9_/{}/.-]+', path):
            raise ValueError('Route paths must be absolute HTTP paths without query strings.')
        if not isinstance(module, str) or not re.fullmatch(r'app(?:\.[A-Za-z_]\w*)+', module):
            raise ValueError('Route modules must be dotted Python names inside app.')
    worker = Path(__file__).with_name('_route_probe.py')
    try:
        result = subprocess.run([sys.executable, str(worker), str(project), json.dumps(dict(routes))],
                                capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise ValueError('worker failed')
        return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, ValueError):
        return {'evidence_kind': 'in_process_mocked_provider', 'passed': False,
                'external_provider_calls': 0, 'routes': [],
                'errors': ['probe_failed: check for a stalled app, syntax error or incompatible shared source version.']}
