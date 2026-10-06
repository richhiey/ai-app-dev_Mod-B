"""Check that every learner notebook installs the published Module B source."""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALL_NOTEBOOKS = sorted((ROOT / "notebooks").rglob("*.ipynb"))
# Campus development after Sprint 1 uses the local repository, so Sprint 2–4 have no Campus notebooks.
NOTEBOOKS = [p for p in ALL_NOTEBOOKS if p.parent.name in {"sprint_1", "sprint_2", "sprint_3"}]


def setup_source(file):
    notebook = json.loads(file.read_text())
    setup_id = "checkpoint-01" if file.name == "sprint_1_service_foundations.ipynb" else "setup"
    return "".join(next(cell["source"] for cell in notebook["cells"] if cell["id"] == setup_id))


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
        # Recording rev-parse HEAD is provenance; only checkout/pinning is forbidden.
        assert '"checkout"' not in source
        assert '"install", "-e", str(REPO)' in source or '"install", "-q", "-e", str(REPO)' in source
        assert 'str(REPO / "requirements.lock")' in source
        assert "require_openrouter_key(prompt=True)" in source or "getpass(" in source

    checkpoint = next(source for file, source in zip(NOTEBOOKS, sources) if file.name == "sprint_1_service_foundations.ipynb")
    assert "ARCHIVE.is_file()" in checkpoint
    assert "restore_local_checkpoint(ARCHIVE, REPO, ARCHIVE_SHA256)" in checkpoint
    assert "hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()" in checkpoint
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
    for file in (p for p in ALL_NOTEBOOKS if p.name != "sprint_4_fieldcare_campus.ipynb"):
        notebook = json.loads(file.read_text())
        cells = notebook["cells"]
        assert len({cell["id"] for cell in cells}) == len(cells)
        campus_checkpoint = file.name == "sprint_1_service_foundations.ipynb"
        setup_id = "checkpoint-01" if campus_checkpoint else "setup"
        save_id = "checkpoint-07" if campus_checkpoint else "save-checkpoint"
        assert sum(cell["id"] == setup_id for cell in cells) == 1
        assert sum(cell["id"] == save_id for cell in cells) == 1
        for cell in cells:
            if cell["cell_type"] == "code":
                assert cell["execution_count"] is None
                assert cell["outputs"] == []
                compile("".join(cell["source"]), cell["id"], "exec")
                source = "".join(cell["source"])
                assert "write_source" not in source
                assert "register_source" not in source
                assert "trace_paths" not in source


def test_checkpoint_selects_fresh_helpers_without_editable_hooks_and_on_rerun(tmp_path):
    source = setup_source(ROOT / "notebooks/sprint_1/sprint_1_service_foundations.ipynb")
    # Run the import selection itself in a separate interpreter. Neither fake
    # clone is installed; rerunning must discard the first clone's module cache.
    selection = source[source.index("previous_helper_path ="):source.index("restored =")]
    clones = []
    for name in ("first", "second"):
        clone = tmp_path / name
        package = clone / "src/module_b"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("")
        (package / "local_checkpoint.py").write_text("def restore_local_checkpoint(*args): return __file__\n")
        clones.append(clone)
    script = "import importlib, sys; from pathlib import Path\n"
    for clone in clones:
        script += f"REPO = Path({str(clone)!r})\n" + selection
        script += "assert Path(restore_local_checkpoint()).is_relative_to(REPO)\n"
    subprocess.run([sys.executable, "-S", "-c", script], check=True)


def test_checkpoint_model_is_passed_to_both_child_process_environments(tmp_path, monkeypatch):
    import getpass
    import os
    import httpx
    from module_b import runtime
    from module_b.openrouter import CHAT_MODELS, DEFAULT_CHAT_MODEL

    notebook = json.loads((ROOT / "notebooks/sprint_1/sprint_1_service_foundations.ipynb").read_text())
    source = "".join(next(c["source"] for c in notebook["cells"] if c["id"] == "checkpoint-05"))
    model = sorted(CHAT_MODELS - {DEFAULT_CHAT_MODEL})[0]
    received = {}
    monkeypatch.setattr(getpass, "getpass", lambda prompt: "synthetic-test-key")
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: received.update(preparation=dict(kw["env"])))

    class ProcessDouble:
        base_url = "http://checkpoint.invalid"
        def __init__(self, **kwargs):
            received["service"] = dict(kwargs["env"])
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    class ClientDouble:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, path, json):
            received.setdefault("paths", []).append(path)
            return httpx.Response(200, json={"test_double": True})

    monkeypatch.setattr(runtime, "ServiceProcess", ProcessDouble)
    monkeypatch.setattr(httpx, "Client", ClientDouble)
    namespace = {"REPO": tmp_path, "CHECKPOINT_MODEL": model, "os": os, "sys": sys,
                 "subprocess": subprocess, "ServiceProcess": ProcessDouble,
                 "httpx": httpx, "json": json, "observations": []}
    exec(source.replace("RUN_GENERATION = False", "RUN_GENERATION = True"), namespace)
    assert received["preparation"]["OPENROUTER_MODEL"] == model
    assert received["service"]["OPENROUTER_MODEL"] == model
    assert received["paths"] == ["/v1/diagnose", "/v2/diagnose"]
    assert namespace["generation_attempted"]
    assert namespace["provider_key"] == ""
    assert "OPENROUTER_API_KEY" not in namespace["generation_env"]
