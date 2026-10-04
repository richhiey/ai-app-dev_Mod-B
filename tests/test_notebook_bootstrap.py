"""Check that every learner notebook installs the published Module B source."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALL_NOTEBOOKS = sorted((ROOT / "notebooks").rglob("*.ipynb"))
# Sprint 4 uses a separate UI notebook format; these bootstrap checks cover 1–3.
NOTEBOOKS = [p for p in ALL_NOTEBOOKS if p.parent.name in {"sprint_1", "sprint_2", "sprint_3"}]


def setup_source(file):
    notebook = json.loads(file.read_text())
    return "".join(next(cell["source"] for cell in notebook["cells"] if cell["id"] == "setup"))


def test_sprints_1_to_3_notebooks_install_published_source_and_real_provider():
    assert len(ALL_NOTEBOOKS) == 8
    assert len(NOTEBOOKS) == 6
    sources = [setup_source(file) for file in NOTEBOOKS]
    repositories = {re.search(r'^REPOSITORY = "([^"]+)"', source, re.M).group(1) for source in sources}
    assert repositories == {"https://github.com/richhiey/ai-app-dev_Mod-B.git"}
    for source in sources:
        assert '"clone", "--depth", "1", "--branch", "main", REPOSITORY, str(REPO)' in source
        assert "SOURCE_REVISION" not in source
        assert '"checkout"' not in source
        assert '"install", "-q", "-e", str(REPO)' in source
        assert 'str(REPO / "requirements.lock")' in source
        assert "require_openrouter_key(prompt=True)" in source or "campus_bootstrap.py" in source
        assert "files.upload" not in source


def test_notebooks_are_clean_and_have_one_setup_and_export_per_sprint():
    expected = {
        "sprint_1_service_foundations.ipynb",
        "sprint_1_live_workshops.ipynb",
        "sprint_2_secure_service.ipynb",
        "sprint_2_live_workshops.ipynb",
        "sprint_3_observable_service.ipynb",
        "sprint_3_live_workshops.ipynb",
    }
    assert {path.name for path in NOTEBOOKS} == expected
    for file in NOTEBOOKS:
        notebook = json.loads(file.read_text())
        cells = notebook["cells"]
        assert len({cell["id"] for cell in cells}) == len(cells)
        assert sum(cell["id"] == "setup" for cell in cells) == 1
        assert sum(cell["id"] == "save-checkpoint" for cell in cells) == 1
        for cell in cells:
            if cell["cell_type"] == "code":
                assert cell["execution_count"] is None
                assert cell["outputs"] == []
                compile("".join(cell["source"]), cell["id"], "exec")
                source = "".join(cell["source"])
                assert "write_source" not in source
                assert "register_source" not in source
                assert "trace_paths" not in source


def test_campus_setup_recovers_stale_import_and_failed_client_preserving_project(tmp_path):
    """An old package and failed TestClient must not prevent retrying setup."""
    import subprocess
    import sys
    old = tmp_path / "old-source/module_b"
    old.mkdir(parents=True)
    (old / "__init__.py").write_text("STALE = True\n")
    source = f"""
from pathlib import Path
import os, sys, runpy
os.environ["OPENROUTER_API_KEY"] = "synthetic-test-not-a-key"
sys.path.insert(0, {str(old.parent)!r})
import module_b
assert module_b.STALE
prepare = runpy.run_path({str(ROOT / 'src/module_b/campus_bootstrap.py')!r})["prepare_campus"]
base = Path({str(tmp_path)!r})
# Failed TestClient has no exit_stack; it must not have __exit__ called.
class FailedClient:
    def close(self): self.closed = True
    def __exit__(self, *args): raise AssertionError("half-started client")
failed = FailedClient()
previous = {{"client": failed}}
demo, project = prepare(repo={str(ROOT)!r}, base=base, sprint=2, project=base/'project', previous=previous)
assert failed.closed and previous['client'] is None
(project/'app/my_work.py').write_text('# keep this')
second, same_project = prepare(repo={str(ROOT)!r}, base=base, sprint=2, project=project)
assert second != demo and demo.exists()
assert same_project == project and (project/'app/my_work.py').read_text() == '# keep this'
from module_b.workspace import prepare_example
assert prepare_example.__module__ == 'module_b.workspace'
"""
    result = subprocess.run([sys.executable, "-c", source], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
