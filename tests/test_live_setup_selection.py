"""Execute the shipped Live bootstrap selector across two distinct source clones."""
import ast
import json
from pathlib import Path
import subprocess
import sys

import pytest


NOTEBOOKS = (
    "notebooks/sprint_1/sprint_1_live_workshops.ipynb",
    "notebooks/sprint_2/sprint_2_live_workshops.ipynb",
    "notebooks/sprint_3/sprint_3_live_workshops.ipynb",
    "notebooks/sprint_4/sprint_4_fieldcare_live.ipynb",
)


def _repository():
    # Works both as a standalone planning test and merged into repository tests/.
    for parent in Path(__file__).resolve().parents:
        for candidate in (parent, parent / "shared/ai-app-dev_Mod-B"):
            if (candidate / NOTEBOOKS[0]).is_file():
                return candidate
    raise AssertionError("Could not locate the delivered Live notebooks")


def _selection_and_import(notebook):
    data = json.loads(notebook.read_text())
    setup = next(cell for cell in data["cells"] if cell.get("id") == "setup")
    source = "".join(setup["source"])
    lines = source.splitlines()
    start = next((i for i, line in enumerate(lines)
                  if line.startswith("previous_helper_path =")), None)
    assert start is not None, f"Missing helper-selection block in {notebook.name}"
    helper = next(node for node in ast.parse(source).body
                  if isinstance(node, ast.ImportFrom)
                  and node.module in ("module_b.live", "module_b.live_observer")
                  and node.lineno > start)
    # Include the actual helper import, not a reconstructed equivalent.
    return "\n".join(lines[start:helper.end_lineno]), helper.module, [a.name for a in helper.names]


@pytest.mark.parametrize("relative", NOTEBOOKS)
def test_live_setup_reselects_helpers_from_latest_clone(tmp_path, relative):
    selection, module, names = _selection_and_import(_repository() / relative)
    clones = []
    for marker in ("first-clone", "second-clone"):
        clone = tmp_path / marker
        package = clone / "src/module_b"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text(f"MARKER = {marker!r}\n")
        (package / "bootstrap_probe.py").write_text(f"MARKER = {marker!r}\n")
        helper_source = (f"MARKER = {marker!r}\nfrom . import bootstrap_probe\n"
                         + "\n".join(f"{name} = MARKER" for name in names) + "\n")
        (package / (module.rsplit(".", 1)[1] + ".py")).write_text(helper_source)
        clones.append(str(clone))
    script = f'''
import importlib
from pathlib import Path
import sys

selection = {selection!r}
clones = {clones!r}
namespace = {{"Path": Path, "sys": sys, "importlib": importlib}}
for index, clone in enumerate(clones):
    namespace["REPO"] = Path(clone)
    exec(selection, namespace)
    loaded = importlib.import_module({module!r})
    expected = Path(clone) / "src"
    assert Path(loaded.__file__).resolve().is_relative_to(expected.resolve())
    assert loaded.MARKER == Path(clone).name
    assert loaded.bootstrap_probe.MARKER == Path(clone).name
    assert importlib.import_module("module_b").MARKER == Path(clone).name
    for name in {names!r}:
        assert namespace[name] == Path(clone).name
    assert sys.path.count(str(expected)) == 1
    if index:
        assert str(Path(clones[0]) / "src") not in sys.path
        assert namespace["LIVE_HELPER_PATH"] == str(expected)
print("Both helper module and its cached package/dependency use the second clone.")
'''
    result = subprocess.run([sys.executable, "-c", script], text=True,
                            capture_output=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
