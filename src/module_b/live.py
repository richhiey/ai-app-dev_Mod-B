"""Isolated Live practice using the same source layout as local Campus.

No Campus source import, source rewriting, automatic provider work, or reset.
"""
from pathlib import Path
import json
import shutil
from module_b.workspace import export_workspace, restore_workspace, WorkspacePolicy


LIVE_POLICY = WorkspacePolicy(directory_suffixes={
    "service/fieldcare": (".py",), "service/data": (".json",),
    "evidence": (".md", ".json"), "evidence/ls07-policies": (".py",),
    "clients": (".py",)}, root_files=("requirements.lock", "pyproject.toml"))


def prepare_live_workspace(repo, destination):
    repo, destination = Path(repo).resolve(), Path(destination).resolve()
    if destination.exists():
        if not (destination / ".live-workspace.json").is_file():
            raise FileExistsError("Choose a new Live folder; existing work is preserved.")
        return destination
    destination.mkdir(parents=True)
    for folder in ("service", "clients", "evidence", "tools"):
        shutil.copytree(repo / folder, destination / folder,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for file in (repo / "examples/live").glob("*.py"):
        shutil.copy2(file, destination / "service/fieldcare" / file.name)
    for name in ("requirements.lock", "pyproject.toml"):
        shutil.copy2(repo / name, destination / name)
    (destination / ".live-workspace.json").write_text(json.dumps({"purpose": "public_live_practice"}))
    return destination


def export_live_workspace(project, destination):
    project = Path(project)
    marker = project / ".module-b-workspace.json"
    marker.write_text(json.dumps({"schema_version": 1,
        "source_project": "ms-app-dev-module-b", "source_version": "live-concept-practice",
        "example": "fieldcare"}))
    return export_workspace(project, destination, policy=LIVE_POLICY)


def restore_live_workspace(archive, destination):
    """Validate a learner's Live ZIP and restore to a new folder without execution.

    Campus checkpoints are separate. Credentials, indexes and process state must
    be prepared again; review restored Python files before starting the service.
    """
    project = restore_workspace(archive, destination, policy=LIVE_POLICY,
                                required_source_version="live-concept-practice")
    (project / ".live-workspace.json").write_text(json.dumps({"purpose": "public_live_practice"}))
    return project


def start_live_service(project, module, env, previous=None):
    from module_b.runtime import ServiceProcess
    if previous is not None:
        previous.stop()
    return ServiceProcess(f"fieldcare.{module}:app",
        project_dir=Path(project) / "service", env=env).start()
