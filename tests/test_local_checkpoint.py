"""A local checkpoint must validate before changing its fresh runner clone."""
import hashlib
from pathlib import Path
import shutil
import zipfile

import pytest
from module_b.local_checkpoint import LOCAL_POLICY, restore_local_checkpoint
from module_b.workspace import export_workspace

ROOT = Path(__file__).resolve().parents[1]


def fixture_export(tmp_path):
    source, clone = tmp_path / "source", tmp_path / "clone"
    for target in (source, clone):
        shutil.copytree(ROOT / "service", target / "service", ignore=shutil.ignore_patterns("__pycache__"))
        for name in ("pyproject.toml", "requirements.lock"):
            shutil.copy2(ROOT / name, target / name)
    (source / "service/fieldcare/student_route.py").write_text("# Learner-authored route\n")
    (source / ".env").write_text("DO_NOT_EXPORT=private\n")
    archive = export_workspace(source, tmp_path / "local.zip", policy=LOCAL_POLICY)
    return archive, clone


def test_restore_source_digest_and_refuse_repeat(tmp_path):
    archive, clone = fixture_export(tmp_path)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    record = restore_local_checkpoint(archive, clone, digest)
    assert (clone / "service/fieldcare/student_route.py").read_text() == "# Learner-authored route\n"
    assert not (clone / ".env").exists()
    assert record["archive_sha256"] == digest
    with pytest.raises(FileExistsError):
        restore_local_checkpoint(archive, clone, digest)


def test_wrong_digest_changes_nothing(tmp_path):
    archive, clone = fixture_export(tmp_path)
    with pytest.raises(ValueError, match="SHA-256"):
        restore_local_checkpoint(archive, clone, "0" * 64)
    assert not (clone / "service/fieldcare/student_route.py").exists()


def test_dependency_mismatch_changes_nothing(tmp_path):
    archive, clone = fixture_export(tmp_path)
    (clone / "requirements.lock").write_text("different dependencies\n")
    with pytest.raises(ValueError, match="Dependency metadata"):
        restore_local_checkpoint(archive, clone, hashlib.sha256(archive.read_bytes()).hexdigest())
    assert not (clone / "service/fieldcare/student_route.py").exists()


@pytest.mark.parametrize("name", ["../escape.py", ".env", "service/fieldcare/main.py"])
def test_unsafe_private_or_duplicate_member_changes_nothing(tmp_path, name):
    archive, clone = fixture_export(tmp_path)
    with zipfile.ZipFile(archive, "a") as package:
        package.writestr(name, "bad member\n")
    before = (clone / "service/fieldcare/main.py").read_bytes()
    with pytest.raises(ValueError):
        restore_local_checkpoint(archive, clone, hashlib.sha256(archive.read_bytes()).hexdigest())
    assert (clone / "service/fieldcare/main.py").read_bytes() == before
    assert not (clone / "service/fieldcare/student_route.py").exists()


def test_public_marked_export_restores(tmp_path, monkeypatch):
    from tools import checkpoint

    # Exercise the public exporter, not a hand-built approximation of its ZIP.
    source = tmp_path / "public-source"
    shutil.copytree(ROOT / "service", source / "service", ignore=shutil.ignore_patterns("__pycache__"))
    for name in ("pyproject.toml", "requirements.lock"):
        shutil.copy2(ROOT / name, source / name)
    clone = tmp_path / "clone"
    shutil.copytree(source, clone)
    monkeypatch.setattr(checkpoint, "ROOT", source)
    archive = checkpoint.export(tmp_path / "marked.zip")
    with zipfile.ZipFile(archive) as package:
        assert package.namelist().count(".module-b-workspace.json") == 1
    restored = restore_local_checkpoint(archive, clone, hashlib.sha256(archive.read_bytes()).hexdigest())
    assert "service/fieldcare/main.py" in restored["files"]


@pytest.mark.parametrize("arguments", [["export", "new.zip"], ["new.zip"]])
def test_export_cli_accepts_explicit_and_original_spelling(tmp_path, monkeypatch, arguments):
    import sys
    from tools import checkpoint

    called = []
    monkeypatch.setattr(sys, "argv", ["checkpoint", *arguments])
    monkeypatch.setattr(checkpoint, "export", lambda path: called.append(path) or path)
    checkpoint.main()
    assert called == [Path("new.zip")]
