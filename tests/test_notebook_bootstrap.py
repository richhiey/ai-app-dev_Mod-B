"""Check that every learner notebook uses the same real Module B source revision."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = sorted((ROOT / "notebooks").rglob("*.ipynb"))


def setup_source(file):
    notebook = json.loads(file.read_text())
    return "".join(next(cell["source"] for cell in notebook["cells"] if cell["id"] == "setup"))


def test_all_six_notebooks_bootstrap_the_same_reviewed_source_and_live_provider():
    assert len(NOTEBOOKS) == 6
    sources = [setup_source(file) for file in NOTEBOOKS]
    repositories = {re.search(r'^REPOSITORY = "([^"]+)"', source, re.M).group(1) for source in sources}
    revisions = {re.search(r'^REVISION = "([0-9a-f]{40})"', source, re.M).group(1) for source in sources}
    assert repositories == {"https://github.com/richhiey/ai-app-dev_Mod-B.git"}
    assert len(revisions) == 1
    for source in sources:
        assert '"checkout", REVISION' in source
        assert '"install"' in source and '"-e"' in source and 'str(REPO)' in source
        assert "require_openrouter_key(prompt=True)" in source
        assert "files.upload" not in source
