"""Export a small, reviewable source checkpoint for the Sprint 1 assessment."""

import argparse
import json
from pathlib import Path
import shutil
import tempfile
import tomllib

from module_b.workspace import WorkspacePolicy, export_workspace

ROOT = Path(__file__).resolve().parents[1]
POLICY = WorkspacePolicy(
    directory_suffixes={
        "service/fieldcare": (".py",),
        "service/data": (".json",),
        "clients": (".py",),
        "evidence": (".md", ".json"),
    },
    root_files=("requirements.lock", "pyproject.toml"),
)


def export(destination: Path) -> Path:
    """Stage only allowed learner files, then create a marked secure archive."""
    with (ROOT / "pyproject.toml").open("rb") as stream:
        version = tomllib.load(stream)["project"]["version"]

    with tempfile.TemporaryDirectory(prefix="fieldcare-checkpoint-") as temporary:
        stage = Path(temporary) / "fieldcare"
        stage.mkdir()
        for directory, suffixes in POLICY.directory_suffixes.items():
            source = ROOT / directory
            if not source.is_dir():
                continue
            for path in source.rglob("*"):
                if path.is_symlink() or not path.is_file() or path.suffix not in suffixes:
                    continue
                relative = path.relative_to(ROOT)
                target = stage / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        for name in POLICY.root_files:
            source = ROOT / name
            if source.is_file() and not source.is_symlink():
                shutil.copy2(source, stage / name)

        marker = {
            "schema_version": 1,
            "source_project": "ms-app-dev-module-b",
            "source_version": version,
            "example": "fieldcare",
        }
        (stage / ".module-b-workspace.json").write_text(
            json.dumps(marker, indent=2) + "\n", encoding="utf-8"
        )
        return export_workspace(stage, destination, policy=POLICY)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="a new ZIP path, for example artifacts/sprint-1-checkpoint.zip")
    args = parser.parse_args()
    archive = export(args.destination)
    print("Checkpoint source archive:", archive)
    print("Review the included source and evidence for accidental secrets before uploading it to the assessment notebook.")


if __name__ == "__main__":
    main()
