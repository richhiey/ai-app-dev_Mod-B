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
        if "SOURCE_REVISION" in source:
            assert '"fetch", "--depth", "1", REPOSITORY, SOURCE_REVISION' in source
            assert 'actual_revision != SOURCE_REVISION' in source
        else:
            assert '"clone", "--depth", "1", "--branch", "main", REPOSITORY, str(REPO)' in source
        assert '"install", "-q", "-e", str(REPO)' in source
        assert 'str(REPO / "requirements.lock")' in source
        assert "require_openrouter_key(prompt=True)" in source
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


def test_campus_setup_recovers_stale_checkout_and_import_without_touching_project(tmp_path):
    """Reproduce reopening Colab with an old source folder AND cached module_b."""
    import subprocess
    import sys
    source = setup_source(ROOT / "notebooks/sprint_1/sprint_1_service_foundations.ipynb")
    source = source.split("from module_b.openrouter", 1)[0]
    source = re.sub(r'^BASE = .*$', f"BASE = Path({str(tmp_path)!r})", source, flags=re.M)
    source = re.sub(r'^REPOSITORY = .*$', f"REPOSITORY = {str(ROOT)!r}", source, flags=re.M)
    source = "\n".join(line for line in source.splitlines() if not line.startswith('subprocess.run([sys.executable, "-m", "pip"'))
    old = tmp_path / "ai-app-dev_Mod-B/src/module_b"
    old.mkdir(parents=True)
    (old / "__init__.py").write_text("STALE = True\n")
    project = tmp_path / "fieldcare-campus-project-1"
    project.mkdir()
    (project / "my-work.py").write_text("# keep my unfinished work\n")
    prelude = f"import sys; sys.path.insert(0, {str(old.parent)!r}); import module_b; assert module_b.STALE\n"
    checks = """
from module_b.workspace import prepare_example
from module_b.campus import prepare_project
assert (PROJECT / "my-work.py").read_text() == "# keep my unfinished work\\n"
assert (BASE / "ai-app-dev_Mod-B/src/module_b/__init__.py").read_text() == "STALE = True\\n"
assert prepare_example.__module__ == "module_b.workspace"
"""
    result = subprocess.run([sys.executable, "-c", prelude + source + "\n" + checks], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
