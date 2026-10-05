"""Validate a local source export and overlay it on a fresh course clone.

The caller owns the fresh clone. Existing learner workspaces are never targets.
Archive validation reuses the workspace restore boundary; it does not execute code.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from module_b.workspace import WorkspacePolicy, restore_workspace

LOCAL_POLICY = WorkspacePolicy(
    directory_suffixes={
        "service/fieldcare": (".py",),
        "service/data": (".json",),
        "clients": (".py",),
        "evidence": (".md", ".json"),
    },
    root_files=("requirements.lock", "pyproject.toml"),
)


def restore_local_checkpoint(archive, fresh_clone, expected_sha256):
    """Overlay one verified local export; refuse reuse or dependency mismatch."""
    archive, root = Path(archive), Path(fresh_clone).resolve()
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != expected_sha256.strip().lower():
        raise ValueError("Archive SHA-256 differs from the value recorded locally.")
    marker = root / ".local-checkpoint-restored.json"
    if marker.exists():
        raise FileExistsError("This clone already has a checkpoint. Create a fresh clone.")
    if not (root / "service/fieldcare/main.py").is_file():
        raise ValueError("Expected a fresh local-service course clone.")
    # Earlier local exports had no marker. Add one only when absent; existing
    # markers and entry metadata still pass the common archive validation.
    converted = io.BytesIO()
    with zipfile.ZipFile(archive) as source:
        entries = source.infolist()
        if len(entries) > 1999 or sum(x.file_size for x in entries) > 19 * 1024 * 1024:
            raise ValueError("Checkpoint exceeds the permitted archive size.")
        with zipfile.ZipFile(converted, "w") as target:
            for entry in entries:
                target.writestr(entry, source.read(entry))
            if ".module-b-workspace.json" not in source.namelist():
                target.writestr(".module-b-workspace.json", json.dumps({
                    "schema_version": 1,
                    "source_project": "ms-app-dev-module-b",
                    "source_version": "local-campus-export",
                    "example": "fieldcare",
                }))
    with tempfile.TemporaryDirectory() as temporary:
        temporary = Path(temporary)
        checked_zip = temporary / "checked.zip"
        checked_zip.write_bytes(converted.getvalue())
        overlay = restore_workspace(checked_zip, temporary / "overlay", policy=LOCAL_POLICY)
        for relative in ("service/fieldcare/main.py", "service/fieldcare/schemas.py",
                         "service/data/equipment_records.json", "service/data/service_docs.json",
                         "pyproject.toml", "requirements.lock"):
            if not (overlay / relative).is_file():
                raise ValueError(f"Local export is missing required file: {relative}")
        for name in ("pyproject.toml", "requirements.lock"):
            if (overlay / name).read_bytes() != (root / name).read_bytes():
                raise ValueError("Dependency metadata differs from main; resolve the course-source mismatch before running.")
        files = sorted(p for p in overlay.rglob("*") if p.is_file() and p.name != ".module-b-workspace.json")
        # Validate every target before changing this new clone.
        for source in files:
            destination = root / source.relative_to(overlay)
            if destination.is_symlink() or any(p.is_symlink() for p in destination.parents if p != root.parent):
                raise ValueError("Checkpoint destination contains a symbolic link.")
        for source in files:
            destination = root / source.relative_to(overlay)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        record = {"archive_sha256": digest, "files": [p.relative_to(overlay).as_posix() for p in files]}
        marker.write_text(json.dumps(record, indent=2) + "\n")
    return record
