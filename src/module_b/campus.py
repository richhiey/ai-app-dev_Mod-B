"""Notebook housekeeping only: preserve source, read completed logs, save work.

Teaching implementations are ordinary files in examples/fieldcare/app.
No helper generates or patches Python source.
"""
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import tempfile
import time
import zipfile

from .workspace import prepare_example, restore_workspace, export_workspace, WorkspacePolicy

CAMPUS_POLICY = WorkspacePolicy(
    directory_suffixes={"app": (".py",), "data": (".json",), "fixtures": (".json",)},
    root_files=("trace-record.md",),
)


def prepare_project(repo, destination, checkpoint=""):
    """Prepare supplied source or restore a selected checkpoint into a NEW path.

    Legacy Campus exports omitted the manifest. Validate their paths and sizes
    with the same restore policy after adding a provenance marker in memory.
    Existing destinations are preserved; an explicit restore never overwrites one.
    """
    if not checkpoint:
        return prepare_example(destination=destination, repo_root=repo)
    archive = Path(checkpoint).expanduser()
    if not archive.is_file():
        raise FileNotFoundError("Checkpoint not found. Upload it or leave CHECKPOINT empty.")
    if Path(destination).exists():
        raise FileExistsError("Checkpoint destination exists. Choose a new PROJECT path; your work was preserved.")
    with zipfile.ZipFile(archive) as source:
        if ".module-b-workspace.json" in source.namelist():
            return restore_workspace(archive, destination, policy=CAMPUS_POLICY)
        infos = source.infolist()
        if len(infos) > 1999 or sum(i.file_size for i in infos) > 19 * 1024 * 1024:
            raise ValueError("Legacy checkpoint is too large.")
        # Preserve ZIP entry metadata so restore_workspace can reject symlinks,
        # duplicate names, traversal, private files and unsupported file types.
        converted = io.BytesIO()
        with zipfile.ZipFile(converted, "w") as target:
            for info in infos:
                target.writestr(info, source.read(info))
            target.writestr(".module-b-workspace.json", json.dumps({
                "schema_version": 1, "source_project": "ms-app-dev-module-b",
                "source_version": "legacy-campus-export", "example": "fieldcare",
            }))
    with tempfile.TemporaryDirectory() as temporary:
        migrated = Path(temporary) / "checkpoint.zip"
        migrated.write_bytes(converted.getvalue())
        return restore_workspace(migrated, destination, policy=CAMPUS_POLICY)


def read_request_records(path, request_ids, timeout=3):
    """Wait briefly for terminal middleware writes; return only this run's IDs."""
    wanted = set(request_ids)
    deadline = time.monotonic() + timeout
    while True:
        records = []
        if Path(path).exists():
            for line in Path(path).read_text().splitlines():
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue  # A final append can be in flight.
                if record.get("request_id") in wanted:
                    records.append(record)
        if wanted <= {r["request_id"] for r in records}:
            return records
        if time.monotonic() >= deadline:
            raise RuntimeError("A matching terminal log is missing; finish the request and retry this cell.")
        time.sleep(0.05)


def save_checkpoint(project, directory, sprint):
    """Export only learner source/data, never demo logs or runtime credentials."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return export_workspace(project, Path(directory) / f"sprint-{sprint}-campus-checkpoint-{stamp}.zip",
                            policy=CAMPUS_POLICY)
