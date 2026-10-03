"""Prepare a disposable, local-only workspace for the Sprint 2 secret exercise."""

import json
import re
import subprocess
from pathlib import Path

_SENTINEL = ".module-b-synthetic-secret-workshop"


def _root(folder: str | Path) -> Path:
    root = Path(folder).resolve()
    if not (root / _SENTINEL).is_file():
        raise ValueError("Use only a folder created by prepare_secret_workshop.")
    return root


def git_fixture(folder: str | Path, *args: str) -> str:
    """Run an explicit Git command only inside the marked practice repository."""
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=Synthetic lesson fixture",
            "-c",
            "user.email=lesson@example.invalid",
            *args,
        ],
        cwd=_root(folder),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def prepare_secret_workshop(
    folder: str | Path, *, marker: str, repo_root: str | Path | None = None
) -> Path:
    """Create unsafe starter files and one synthetic .env commit; preserve edits."""
    if not re.fullmatch(r"SYNTHETIC_[A-Z0-9_]{3,80}_NOT_A_CREDENTIAL", marker):
        raise ValueError("Use an explicitly nonfunctional synthetic marker.")

    root = Path(folder).resolve()
    if root.exists():
        if json.loads((_root(root) / _SENTINEL).read_text())["marker"] != marker:
            raise ValueError("This fixture already belongs to another marker.")
        return root

    root.mkdir(parents=True)
    (root / _SENTINEL).write_text(json.dumps({"marker": marker}) + "\n")
    repository = Path(repo_root) if repo_root else Path(__file__).resolve().parents[2]
    patterns = repository / "examples" / "patterns" / "secret_workshop"
    for name in ("log", "prompt"):
        (root / f"{name}_policy.py").write_text((patterns / f"{name}_unsafe.py").read_text())

    git_fixture(root, "init", "-q")
    (root / ".env").write_text(f"FAKE_MARKER={marker}\n")
    git_fixture(root, "add", ".env")
    git_fixture(root, "commit", "-qm", "Add a synthetic marker for the lesson")
    (root / "local.key").write_text(marker + "\n")
    return root
