"""Execute the exact notebooks in an isolated fresh checkout and Python environment.

No Colab/GitHub upload, provider credentials, or global kernelspec installation.
Also reruns notebooks in the same workspace to catch destructive setup/reset bugs.
"""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def run(args, *, cwd=None, env=None, timeout=240):
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout.strip()


def main(reference_config=None):
    report = {"verified_at": datetime.now(timezone.utc).isoformat(), "scope": "Local Linux/macOS Jupyter execution; not hosted Colab", "provider_calls": 0, "platform": sys.platform, "notebooks": []}
    with tempfile.TemporaryDirectory(prefix="module-b-notebook-review-") as temporary:
        temp = Path(temporary)
        checkout = temp / "ai-app-dev_Mod-B"
        shutil.copytree(ROOT, checkout, ignore=shutil.ignore_patterns('.git','.venv','__pycache__','*.egg-info','work','artifacts','.pytest_cache','node_modules','.env','.env.local','.env.production'))
        environment = temp / "python"
        print("Creating fresh environment and installing shared source...", flush=True)
        run([sys.executable,'-m','venv',str(environment)])
        python = environment / 'bin/python'
        run([str(python),'-m','pip','install','-q','-e',f'{checkout}[dev]','-c',str(checkout/'requirements.lock')])
        report['python'] = run([str(python),'--version'])
        report['pip_check'] = run([str(python),'-m','pip','check'])
        report['shared_tests'] = run([str(python),'-m','pytest','-o','addopts=','-q','--junitxml',str(temp/'shared-tests.xml')],cwd=checkout)
        report['shared_junit_cases'] = sum(int(suite.get('tests', 0)) for suite in ET.parse(temp/'shared-tests.xml').getroot().iter('testsuite'))
        summary = re.search(r"(\d+) passed", report['shared_tests'])
        if summary:
            report['shared_test_count'] = int(summary[1])
            subtests = re.search(r'(\d+) subtests passed', report['shared_tests'])
            report['shared_subtests'] = int(subtests[1]) if subtests else 0
        print("Shared tests passed; checking examples with test suites...", flush=True)
        report['example_tests'] = []
        for example in sorted((checkout/'examples').iterdir()):
            if (example/'tests').is_dir():
                junit = temp / f'{example.name}-tests.xml'
                result = run([str(python),'-m','pytest','-o','addopts=','-q','tests','--junitxml',str(junit)],cwd=example)
                count = sum(int(suite.get('tests', 0)) for suite in ET.parse(junit).getroot().iter('testsuite'))
                report['example_tests'].append({'example':example.name,'tests':count,'output':result})
        worker = checkout / 'scripts/execute_notebooks.py'
        env = dict(os.environ)
        for key in ['OPENROUTER_API_KEY','OPENROUTER_MODEL','FIELDCARE_MODE','FIELDCARE_DIAGNOSE_V2_MODEL','FIELDCARE_HANDOVER_V2_MODEL','MODULE_B_REPO','MODULE_B_REPO_URL','MODULE_B_REPO_REF']:
            env.pop(key,None)
        print("Executing discovered Colab notebooks twice in fresh Jupyter kernels...", flush=True)
        code_cells = sum(sum(cell['cell_type'] == 'code' for cell in json.loads(path.read_text())['cells'])
                         for path in (checkout/'notebooks').rglob('*.ipynb'))
        # Two passes; retain the 90-second per-cell bound while allowing the
        # module to grow without an unrelated four-minute aggregate cutoff.
        worker_timeout = 120 + 4 * code_cells * 90
        command=[str(python),str(worker),str(checkout),str(temp)]
        if reference_config is not None:command.append(str(reference_config))
        print(run(command,env=env,timeout=worker_timeout),flush=True)
        report['notebooks'] = json.loads((temp/'notebook-results.json').read_text())
    report['limitations'] = ['Hosted Colab was not opened or tested.','No live provider call; demo plus mocked-boundary verification only.','Generated-answer quality remains pending; no demo or mocked observation substitutes for it.']
    (ROOT/'docs/local-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Local verification recorded in docs/local-verification.json',flush=True)


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--reference-config',type=Path,help='Private cell edits outside the learner source package.')
    args=parser.parse_args()
    main(args.reference_config.resolve() if args.reference_config else None)
