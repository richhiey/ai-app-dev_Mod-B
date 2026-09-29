"""Prepare editable example copies and export selected learner work.

Setup never resets an existing workspace. To start again, choose a new destination.
Exports omit common credential/configuration files, but this is NOT a secret scanner:
Python source or permitted JSON may contain secrets a learner has inserted. Review
files before sharing the ZIP.
"""
from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tomllib
from types import MappingProxyType
from typing import Any
import zipfile

_PROJECT_NAME = "ms-app-dev-module-b"
_MARKER = ".module-b-workspace.json"
_MARKER_SCHEMA = 1
_EXCLUDED = {
    ".git", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".ipynb_checkpoints", ".cache", "node_modules", ".next", ".nuxt",
}
_SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx", ".p8")
_MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
_MAX_ARCHIVE_FILES = 2000


def _excluded_component(name: str) -> bool:
    lowered = name.lower()
    return (
        lowered in _EXCLUDED
        or (lowered == ".env" or lowered.startswith(".env.")) and lowered != ".env.example"
        or lowered.endswith(_SECRET_SUFFIXES)
        or lowered in {"id_rsa", "id_ed25519", "id_ecdsa", "id_dsa"}
    )


def _safe_parts(name: str) -> tuple[str, ...] | None:
    if not isinstance(name, str) or "\\" in name or "\x00" in name or ":" in name:
        return None
    parts = tuple(name.split("/"))
    if any(part in ("", ".", "..") or _excluded_component(part) for part in parts):
        return None
    return parts


@dataclass(frozen=True)
class WorkspacePolicy:
    """An explicit, immutable checkpoint allowlist owned by the calling notebook.

    ``directory_suffixes`` maps relative directories to allowed filename suffixes
    anywhere below them. For example, ``{"src": (".py",), "web": (".ts", ".css")}``.
    Supplying this mapping replaces, rather than extends, the default directories.
    ``root_files`` names exact files at the workspace root. Inputs are defensively
    copied; wildcard/path traversal rules are not accepted. Private/cache path
    exclusions always win, even over an explicit suffix or root-file allowance.
    Pass the SAME trusted policy to export and restore; archives cannot supply it.
    """

    directory_suffixes: Mapping[str, Collection[str]] = field(default_factory=lambda: {
        "app": (".py",), "data": (".json",), "fixtures": (".json",),
    })
    root_files: Collection[str] = ("trace-record.md",)

    def __post_init__(self) -> None:
        if not isinstance(self.directory_suffixes, Mapping):
            raise ValueError("directory_suffixes must map relative directories to suffix collections.")
        directories: dict[str, frozenset[str]] = {}
        for directory, suffixes in self.directory_suffixes.items():
            parts = _safe_parts(directory)
            if parts is None or _MARKER in parts or any(re.search(r"[*?\[\]]", part) for part in parts):
                raise ValueError(f"Policy directory must be a safe explicit relative path: {directory!r}")
            if isinstance(suffixes, (str, bytes)) or not isinstance(suffixes, Collection) or not suffixes:
                raise ValueError("Each policy directory needs a nonempty collection of suffixes.")
            if any(not isinstance(suffix, str) or re.fullmatch(r"\.[A-Za-z0-9][A-Za-z0-9._-]*", suffix) is None for suffix in suffixes):
                raise ValueError("Policy suffixes must be explicit extensions such as '.py' or '.jsonl'.")
            directories[directory] = frozenset(suffixes)
        if isinstance(self.root_files, (str, bytes)) or not isinstance(self.root_files, Collection):
            raise ValueError("root_files must be a collection of explicit filenames.")
        roots: set[str] = set()
        for name in self.root_files:
            # Validate syntax separately from exclusion: an explicit private file
            # still remains excluded rather than weakening the global boundary.
            if (
                not isinstance(name, str) or name in ("", ".", "..", _MARKER)
                or any(character in name for character in "/\\\x00:*?[]")
            ):
                raise ValueError(f"Policy root file must be an explicit filename: {name!r}")
            roots.add(name)
        object.__setattr__(self, "directory_suffixes", MappingProxyType(directories))
        object.__setattr__(self, "root_files", frozenset(roots))


DEFAULT_POLICY = WorkspacePolicy()


def _validated_marker(marker: Any, name: str | None = None) -> dict[str, Any]:
    """Validate and retain only the four non-content provenance fields."""
    if not (
        isinstance(marker, dict)
        and type(marker.get("schema_version")) is int
        and marker["schema_version"] == _MARKER_SCHEMA
        and marker.get("source_project") == _PROJECT_NAME
        and isinstance(marker.get("example"), str)
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", marker["example"])
        and (name is None or marker["example"] == name)
        and isinstance(marker.get("source_version"), str)
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]{0,127}", marker["source_version"])
    ):
        raise ValueError("Invalid Module B workspace manifest.")
    return {key: marker[key] for key in ("schema_version", "source_project", "source_version", "example")}


def _repository_root(repo_root: str | Path | None) -> tuple[Path, str]:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[2]
    root = root.expanduser().resolve()
    try:
        with (root / "pyproject.toml").open("rb") as stream:
            project = tomllib.load(stream)["project"]
        if project.get("name") != _PROJECT_NAME:
            raise ValueError("Unexpected project name")
        version = project["version"]
        if not isinstance(version, str) or not version.strip():
            raise ValueError("Missing project version")
    except (OSError, KeyError, ValueError, TypeError) as exc:
        raise ValueError(f"{root} is not a versioned {_PROJECT_NAME} repository.") from exc
    return root, version


def _workspace_marker(path: Path, name: str | None = None) -> dict[str, Any]:
    marker_path = path / _MARKER
    if marker_path.is_symlink():
        raise FileExistsError(f"Refusing a workspace with a symbolic-link marker: {path}")
    try:
        return _validated_marker(json.loads(marker_path.read_text(encoding="utf-8")), name)
    except (OSError, ValueError, TypeError):
        raise FileExistsError(
            f"{path} already exists without a matching workspace marker. "
            "Choose a new destination; existing files were not changed."
        ) from None


def prepare_example(
    name: str = "fieldcare",
    destination: str | Path = Path("work/fieldcare"),
    *,
    repo_root: str | Path | None = None,
) -> Path:
    """Copy a packaged example once; retain every edit on subsequent calls.

    ``repo_root`` defaults to the checkout containing this module. The example
    is copied into ``destination``, relative to the current directory unless an
    absolute path is supplied. A matching marker permits reuse; it does not
    cause an update when the source version changes. Use a NEW path for a reset
    or another checkpoint. Private environment/key files and known dependency/cache
    directories are omitted (``.env.example`` is retained). Other data and build
    directories are not guessed away from arbitrary gitignore rules. Symbolic
    links in the remaining packaged example are rejected.
    """
    if not isinstance(name, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name) is None:
        raise ValueError("Example name must be a single directory name (letters, digits, '_' or '-').")
    root, version = _repository_root(repo_root)
    raw_destination = Path(destination).expanduser()
    if raw_destination.is_symlink():
        raise FileExistsError(f"Refusing a symbolic-link workspace: {raw_destination}")
    target = raw_destination.resolve()
    if target.exists():
        if not target.is_dir():
            raise FileExistsError(f"Workspace destination is not a directory: {target}")
        _workspace_marker(target, name)
        return target

    source = root / "examples" / name
    if source.is_symlink() or not source.is_dir():
        raise FileNotFoundError(f"Packaged example not found as a real directory: {source}")
    if source.resolve().parent != (root / "examples").resolve():
        raise ValueError("Packaged example must be inside the repository's examples directory.")
    if target == source or source in target.parents:
        raise ValueError("Choose a workspace outside its packaged example directory.")

    # Prune ignored directories before descending; node_modules can be huge and
    # often contains links that are irrelevant to an editable teaching copy.
    entries: list[Path] = []
    for directory, directories, files in os.walk(source, followlinks=False):
        current = Path(directory)
        directories[:] = sorted(entry_name for entry_name in directories if not _excluded_component(entry_name))
        for entry_name in [*directories, *sorted(files)]:
            if _excluded_component(entry_name):
                continue
            entry = current / entry_name
            if entry.is_symlink():
                raise ValueError("Packaged examples must not contain symbolic links outside excluded paths.")
            entries.append(entry)
    if (source / _MARKER).exists():
        raise ValueError("Packaged example already contains a workspace marker.")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents copying into another process's newly-created folder.
    target.mkdir()
    for entry in entries:
        relative = entry.relative_to(source)
        copied = target / relative
        if entry.is_dir():
            copied.mkdir(parents=True, exist_ok=True)
        elif entry.is_file():
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(entry, copied)
    marker = {
        "schema_version": _MARKER_SCHEMA,
        "source_project": _PROJECT_NAME,
        "source_version": version,
        "example": name,
    }
    # A partial failed copy has no ownership marker, so it is never silently reused.
    with (target / _MARKER).open("x", encoding="utf-8") as stream:
        json.dump(marker, stream, indent=2)
        stream.write("\n")
    return target


def export_workspace(
    project: str | Path, destination: str | Path, *, policy: WorkspacePolicy = DEFAULT_POLICY,
) -> Path:
    """Write a new ZIP using the caller's explicit checkpoint policy.

    The default allows ``app/**/*.py``, ``data/**/*.json``, ``fixtures/**/*.json``
    and root ``trace-record.md``. Pass another WorkspacePolicy for other components,
    and supply that same policy on restore. A valid marker is exported as a canonical
    four-field manifest; extra marker fields are never copied. An existing invalid
    marker is rejected. Unmarked projects export without a manifest and cannot be
    restored by ``restore_workspace``. Symbolic links and private/cache directories
    are skipped. Existing output files are NEVER overwritten. This allowlist is
    not a guarantee of secret-free content: inspect Python, JSON and notes before
    sharing them. User edits to allowed files are exported as they are.
    """
    if not isinstance(policy, WorkspacePolicy):
        raise TypeError("policy must be a WorkspacePolicy supplied by the caller.")
    raw_project = Path(project).expanduser()
    if raw_project.is_symlink() or not raw_project.is_dir():
        raise ValueError("Project must be a real workspace directory, not a symbolic link.")
    root = raw_project.resolve()
    manifest = None
    if (root / _MARKER).exists() or (root / _MARKER).is_symlink():
        manifest = (json.dumps(_workspace_marker(root), indent=2) + "\n").encode("utf-8")
    output = Path(destination).expanduser()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Export destination already exists: {output}")
    output = output.absolute()
    selected: list[tuple[Path, str]] = []
    for directory, directories, files in os.walk(root, followlinks=False):
        current = Path(directory)
        directories[:] = sorted(
            name for name in directories
            if not _excluded_component(name) and not (current / name).is_symlink()
            and any(
                folder == (current / name).relative_to(root).as_posix()
                or folder.startswith((current / name).relative_to(root).as_posix() + "/")
                or (current / name).relative_to(root).as_posix().startswith(folder + "/")
                for folder in policy.directory_suffixes
            )
        )
        for name in sorted(files):
            path = current / name
            relative = path.relative_to(root).as_posix()
            if relative == _MARKER or path.is_symlink() or not path.is_file():
                continue
            if _allowed_member(relative, policy):
                selected.append((path, relative))
    if len(selected) + (manifest is not None) > _MAX_ARCHIVE_FILES:
        raise ValueError("Workspace export exceeds the 2,000-file limit (including the manifest).")
    if sum(path.stat().st_size for path, _ in selected) + len(manifest or b"") > _MAX_ARCHIVE_BYTES:
        raise ValueError("Workspace export exceeds the 20 MiB uncompressed size limit.")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive mode is the final collision check, including concurrent creation.
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        if manifest is not None:
            archive.writestr(_MARKER, manifest)
        for path, relative in sorted(selected, key=lambda item: item[1]):
            archive.write(path, arcname=relative)
    return output.resolve()


def _allowed_member(name: str, policy: WorkspacePolicy = DEFAULT_POLICY) -> bool:
    parts = _safe_parts(name)
    if parts is None:
        return False
    if name == _MARKER or (len(parts) == 1 and name in policy.root_files):
        return True
    return any(
        name.startswith(directory + "/") and any(parts[-1].endswith(suffix) for suffix in suffixes)
        for directory, suffixes in policy.directory_suffixes.items()
    )


def restore_workspace(
    archive: str | Path, destination: str | Path, *, policy: WorkspacePolicy = DEFAULT_POLICY,
) -> Path:
    """Restore an exported, marked workspace to a NEW directory without execution.

    All ZIP entries and their contents are validated before creating the target.
    Only the caller-trusted policy and a valid manifest are accepted; the archive
    cannot expand permitted paths or suffixes. Supply the same policy used for export.
    Traversal,
    absolute/backslash paths, duplicate names, symlinks, special files and more
    than 20 MiB of uncompressed content are rejected. The result can be passed to
    ``prepare_example`` with the manifest's example name without resetting edits.
    This validates paths and provenance format, not code safety or secret-free
    contents. Review restored code before running it. No file is overwritten.
    """
    if not isinstance(policy, WorkspacePolicy):
        raise TypeError("policy must be a WorkspacePolicy supplied by the caller.")
    raw_target = Path(destination).expanduser()
    if raw_target.exists() or raw_target.is_symlink():
        raise FileExistsError(f"Restore destination already exists: {raw_target}. Choose a new path.")
    target = raw_target.resolve()
    payloads: dict[str, bytes] = {}
    try:
        with zipfile.ZipFile(Path(archive).expanduser()) as package:
            members = package.infolist()
            if len(members) > _MAX_ARCHIVE_FILES or sum(info.file_size for info in members) > _MAX_ARCHIVE_BYTES:
                raise ValueError("Archive exceeds the 20 MiB or 2,000-file restore limit.")
            names: set[str] = set()
            for info in members:
                file_type = stat.S_IFMT(info.external_attr >> 16)
                if (
                    not _allowed_member(info.filename, policy)
                    or info.filename in names
                    or info.is_dir()
                    or file_type not in (0, stat.S_IFREG)
                    or info.flag_bits & 1
                ):
                    raise ValueError(f"Unsupported, duplicate or unsafe archive member: {info.filename!r}")
                names.add(info.filename)
            if _MARKER not in names:
                raise ValueError("Archive has no Module B workspace manifest; use a marked workspace export.")
            for name in names:
                parts = name.split("/")
                if any("/".join(parts[:end]) in names for end in range(1, len(parts))):
                    raise ValueError("Archive uses the same path as both a file and a directory.")
            # Fully read/check CRC before creating anything. Bound reads even if
            # malformed metadata disagrees with the decompressor's output size.
            total = 0
            for info in members:
                with package.open(info) as stream:
                    content = stream.read(_MAX_ARCHIVE_BYTES - total + 1)
                total += len(content)
                if total > _MAX_ARCHIVE_BYTES or len(content) != info.file_size:
                    raise ValueError("Archive contents exceed the size limit or disagree with their declared size.")
                payloads[info.filename] = content
            marker = _validated_marker(json.loads(payloads[_MARKER].decode("utf-8")))
            payloads[_MARKER] = (json.dumps(marker, indent=2) + "\n").encode("utf-8")
    except (zipfile.BadZipFile, UnicodeError, json.JSONDecodeError, NotImplementedError, RuntimeError) as exc:
        raise ValueError("Invalid or unsupported workspace archive.") from exc

    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir()  # Exclusive: a concurrent destination also causes refusal.
    # Write marker last, so interrupted restores are not mistaken for complete workspaces.
    for name in sorted(payloads, key=lambda name: (name == _MARKER, name)):
        output = target / name
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as stream:
            stream.write(payloads[name])
    return target
