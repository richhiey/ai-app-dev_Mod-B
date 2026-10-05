"""Check that every learner notebook installs the published Module B source."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALL_NOTEBOOKS = sorted((ROOT / "notebooks").rglob("*.ipynb"))
# Campus development after Sprint 1 uses the local repository, so Sprint 2–4 have no Campus notebooks.
NOTEBOOKS = [p for p in ALL_NOTEBOOKS if p.parent.name in {"sprint_1", "sprint_2", "sprint_3"}]


def setup_source(file):
    notebook = json.loads(file.read_text())
    return "".join(next(cell["source"] for cell in notebook["cells"] if cell["id"] == "setup"))


def test_sprints_1_to_3_notebooks_install_published_source_and_real_provider():
    assert len(ALL_NOTEBOOKS) == 5
    assert len(NOTEBOOKS) == 4
    sources = [
        "\n".join("".join(cell["source"]) for cell in json.loads(file.read_text())["cells"] if cell["cell_type"] == "code")
        for file in NOTEBOOKS
    ]
    setups = [setup_source(file) for file in NOTEBOOKS]
    assert all("https://github.com/richhiey/ai-app-dev_Mod-B.git" in source for source in sources)
    for setup, source in zip(setups, sources):
        assert '"git", "clone"' in setup
        assert '"--branch", "main"' in setup
        assert "SOURCE_REVISION" not in source
        assert '"checkout"' not in source
        assert '"install", "-e", str(REPO)' in source or '"install", "-q", "-e", str(REPO)' in source
        assert 'str(REPO / "requirements.lock")' in source
        assert "require_openrouter_key(prompt=True)" in source or "getpass(" in source

    checkpoint = next(source for file, source in zip(NOTEBOOKS, sources) if file.name == "sprint_1_service_foundations.ipynb")
    assert "files.upload" in checkpoint
    assert "WorkspacePolicy" in checkpoint
    assert "restore_workspace" in checkpoint
    for file, source in zip(NOTEBOOKS, sources):
        if file.name != "sprint_1_service_foundations.ipynb":
            assert "files.upload" not in source


def test_notebooks_are_clean_and_have_one_setup_and_export_per_sprint():
    expected = {
        "sprint_1_service_foundations.ipynb",
        "sprint_1_live_workshops.ipynb",
        "sprint_2_live_workshops.ipynb",
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
