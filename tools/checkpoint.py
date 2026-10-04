"""Export reviewed source or unpack a Sprint 1 archive into a NEW folder."""

import argparse
from pathlib import Path
from module_b.campus import prepare_project
from module_b.workspace import WorkspacePolicy, export_workspace

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    unpack = commands.add_parser("unpack")
    unpack.add_argument("archive", type=Path)
    unpack.add_argument("destination", type=Path)
    export = commands.add_parser("export")
    export.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.command == "unpack":
        result = prepare_project(ROOT, args.destination, args.archive)
        print("Restored without executing source:", result)
        print(
            "Compare your route files with service/fieldcare; follow docs/local-development.md."
        )
    else:
        policy = WorkspacePolicy(
            directory_suffixes={
                "service/fieldcare": (".py",),
                "service/data": (".json",),
                "clients": (".py",),
                "evidence": (".md", ".json"),
            },
            root_files=("requirements.lock", "pyproject.toml"),
        )
        print(
            "Source archive:", export_workspace(ROOT, args.destination, policy=policy)
        )
        print(
            "Review Python, JSON and notes for secrets before submitting. This is not a secret scanner."
        )


if __name__ == "__main__":
    main()
