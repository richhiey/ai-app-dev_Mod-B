"""Shared, non-executing file resolution for notebook inspection/loaders."""
from collections.abc import Sequence
from pathlib import Path

_BLOCKED = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', '.ipynb_checkpoints', 'node_modules'}


def project_file(project: str | Path, path: str | Path, *, roots: Sequence[str] | None = None) -> Path:
    """Resolve a project-relative file without traversing links or private folders."""
    raw = Path(project).expanduser()
    if raw.is_symlink() or not raw.is_dir():
        raise ValueError('Project must be a real directory, not a symbolic link.')
    root = raw.resolve()
    text = str(path)
    relative = Path(path)
    if not text or '\\' in text or ':' in text or relative.is_absolute() or '..' in relative.parts:
        raise ValueError('Use a project-relative path without traversal or backslashes.')
    if any(part.lower() in _BLOCKED or (part.lower().startswith('.env') and part.lower() != '.env.example') or part.lower().endswith(('.pem', '.key', '.p12', '.pfx', '.p8')) for part in relative.parts):
        raise ValueError('Private configuration, credential and cache paths cannot be inspected.')
    if roots is not None:
        if isinstance(roots, str) or not roots:
            raise ValueError('roots must be a nonempty sequence of relative directories.')
        allowed = []
        for item in roots:
            directory = Path(item)
            if directory.is_absolute() or '..' in directory.parts or '\\' in str(item) or ':' in str(item):
                raise ValueError('Inspection roots must stay inside the project.')
            allowed.append(directory)
        if not any(relative.is_relative_to(directory) for directory in allowed):
            raise ValueError('Source path is outside the configured inspection roots.')
    candidate = root
    for part in relative.parts:
        candidate /= part
        if candidate.is_symlink():
            raise ValueError('File paths must not pass through symbolic links.')
    if not candidate.resolve().is_relative_to(root):
        raise ValueError('File path escapes the project directory.')
    if not candidate.is_file():
        raise FileNotFoundError(f'Project file not found: {relative}')
    return candidate
