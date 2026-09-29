"""Small guarded source edits shared by teaching notebooks.

Callers keep the source/diff visible. This module owns collision and path checks,
not route generation. It does not import or execute learner files.
"""
from pathlib import Path


def write_source(project, relative, source, *, expected=None):
    """Create source once, or replace exactly the supplied previous text.

    Identical reruns are no-ops. Unexpected existing content is never overwritten.
    Only relative .py files are accepted; symlinks/traversal are refused. The
    caller supplies a trusted, real workspace. This is not a concurrent editor.
    """
    root = Path(project)
    path = Path(relative)
    if root.is_symlink() or not root.is_dir() or path.is_absolute() or '..' in path.parts or path.suffix != '.py':
        raise ValueError('Choose a real workspace and a relative Python source file.')
    target = root
    for part in path.parts:
        target /= part
        if target.is_symlink():
            raise ValueError('Source edits cannot follow symbolic links.')
    if not isinstance(source, str) or expected is not None and not isinstance(expected, str):
        raise TypeError('source and expected must be text.')
    if target.exists():
        actual = target.read_text()
        if actual == source:
            return target
        if expected is None or actual != expected:
            raise FileExistsError('Source has changed. Preserve your edit and use a fresh workspace or review the expected text.')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source)
    return target


def content_fingerprint(project, *, directories=('app',), suffixes=('.py',)):
    """Hash selected workspace content paths/bytes without importing source.

    Select data directories/extensions explicitly when they affect observed
    behavior. Symlinks are refused. Cache directories are skipped. This is an
    evidence freshness check, not a secret scanner or tamper-proof signature.
    """
    import hashlib
    import os
    root = Path(project)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Choose a real workspace directory.')
    if isinstance(directories, str) or not directories or isinstance(suffixes, str) or not suffixes:
        raise ValueError('Supply directory and extension collections.')
    digest = hashlib.sha256()
    files = set()
    for directory in directories:
        relative = Path(directory)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Choose relative content directories.')
        target = root
        for part in relative.parts:
            target /= part
            if target.is_symlink():
                raise ValueError('Content fingerprints cannot follow symbolic links.')
        if not target.is_dir():
            raise ValueError('Content directory does not exist.')
        for folder, children, names in os.walk(target, followlinks=False):
            children[:] = sorted(name for name in children if name != '__pycache__')
            if any((Path(folder)/name).is_symlink() for name in children):
                raise ValueError('Content fingerprints cannot follow symbolic links.')
            for name in names:
                path = Path(folder)/name
                if path.suffix in suffixes:
                    if path.is_symlink():
                        raise ValueError('Content fingerprints cannot follow symbolic links.')
                    files.add(path)
    for path in sorted(files):
        name = path.relative_to(root).as_posix().encode()
        content = path.read_bytes()
        digest.update(len(name).to_bytes(8,'big') + name + len(content).to_bytes(8,'big') + content)
    return digest.hexdigest()


def source_fingerprint(project, *, directory='app'):
    """Hash Python source using the established single-directory interface."""
    return content_fingerprint(project, directories=(directory,), suffixes=('.py',))


def preserves_statements(original, current):
    """True when every original top-level Python statement remains in order.

    Additional imports and registration statements may be inserted. Existing
    assignments/calls cannot be replaced or reordered. This is a source-change
    observation, not a proof that added code has no runtime side effects.
    """
    import ast
    try:
        before = [ast.dump(node, include_attributes=False) for node in ast.parse(original).body]
        after = iter(ast.dump(node, include_attributes=False) for node in ast.parse(current).body)
        return all(any(item == statement for item in after) for statement in before)
    except (SyntaxError, TypeError):
        return False
