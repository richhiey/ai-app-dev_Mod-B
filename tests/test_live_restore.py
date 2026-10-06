"""A saved Live exercise must survive a new runtime without becoming Campus work."""
import json
from pathlib import Path
import zipfile

import httpx
import pytest

from module_b.live import export_live_workspace, prepare_live_workspace, restore_live_workspace
from module_b.runtime import ServiceProcess


ROOT = Path(__file__).resolve().parents[1]


def authored_workspace(tmp_path):
    project = prepare_live_workspace(ROOT, tmp_path / "original")
    (project / "service/fieldcare/checklist_schemas.py").write_text(
        "from fieldcare.schemas import DiagnosticRequest, DiagnosticResponse\n"
        "class ChecklistRequest(DiagnosticRequest):\n    pass\n"
        "class ChecklistResponse(DiagnosticResponse):\n    pass\n"
    )
    route = (ROOT / "examples/live/brief_routes.py").read_text()
    route = route.replace("from fieldcare.schemas import", "from fieldcare.checklist_schemas import")
    for original, changed in (("DiagnosticRequest", "ChecklistRequest"), ("DiagnosticResponse", "ChecklistResponse"),
                              ("BRIEF_PROMPT", "CHECKLIST_PROMPT"), ("brief_diagnose", "checklist_diagnose"),
                              ("/v1/diagnose-brief", "/v1/diagnose-checklist")):
        route = route.replace(original, changed)
    (project / "service/fieldcare/checklist_routes.py").write_text(route)
    registration = project / "service/fieldcare/live_extension.py"
    registration.write_text(registration.read_text() + "\nfrom fieldcare.checklist_routes import router as checklist_router\napp.include_router(checklist_router)\n")
    return project


def files_below(path):
    return {p.relative_to(path).as_posix(): p.read_bytes() for p in path.rglob("*") if p.is_file()}


def test_saved_authored_route_survives_fresh_runtime_and_setup(tmp_path):
    project = authored_workspace(tmp_path)
    policy = project / "evidence/ls07-policies/selected_policy.py"
    policy.parent.mkdir(parents=True)
    policy.write_text("SELECTED_POLICY = 'synthetic-review-fixture'\n")
    record = project / "evidence/ls07-checks.json"
    record.write_text(json.dumps({"synthetic": True, "statuses": [401, 422, 200]}))
    for name in (".env", ".git/config", "var/events.jsonl", "service/fieldcare/secret.key", "evidence/ls07-policies/private.pem"):
        p = project / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("PRIVATE-SYNTHETIC-SENTINEL\n")
    archive = export_live_workspace(project, tmp_path / "saved-live.zip")
    with zipfile.ZipFile(archive) as package:
        names = package.namelist()
        assert "evidence/ls07-policies/selected_policy.py" in names
        assert "evidence/ls07-checks.json" in names
        assert all(b"PRIVATE-SYNTHETIC-SENTINEL" not in package.read(name) for name in names)
    restored = restore_live_workspace(archive, tmp_path / "fresh-runtime")
    for name in ("checklist_schemas.py", "checklist_routes.py", "live_extension.py"):
        assert (restored / "service/fieldcare" / name).read_bytes() == (project / "service/fieldcare" / name).read_bytes()
    assert (restored / "evidence/ls07-policies/selected_policy.py").read_bytes() == policy.read_bytes()
    assert (restored / "evidence/ls07-checks.json").read_bytes() == record.read_bytes()
    before = files_below(restored)
    assert prepare_live_workspace(ROOT, restored) == restored
    assert files_below(restored) == before
    # Actual HTTP proves the retained registration still composes with the pilot.
    with ServiceProcess("fieldcare.live_versions:app", project_dir=restored / "service", env={"OPENROUTER_API_KEY": ""}) as service:
        with httpx.Client(base_url=service.base_url, timeout=15) as client:
            reply = client.post("/v1/diagnose-checklist", json={"question": "Which filter checks?"})
            assert reply.status_code == 200
            assert reply.json()["status"] == "needs_clarification"
            assert client.post("/v1/diagnose-checklist", json={}).status_code == 422
            assert client.post("/v1/diagnose", json={"question": "filter " + "x" * 693}).status_code == 200
            assert client.post("/v2/diagnose", json={"question": "filter " + "x" * 693}).status_code == 422


def test_campus_archive_rejected_before_creating_destination(tmp_path):
    project = authored_workspace(tmp_path)
    exported = export_live_workspace(project, tmp_path / "live.zip")
    campus = tmp_path / "campus.zip"
    with zipfile.ZipFile(exported) as source, zipfile.ZipFile(campus, "w") as target:
        for name in source.namelist():
            content = source.read(name)
            if name == ".module-b-workspace.json":
                manifest = json.loads(content)
                manifest["source_version"] = "local-campus-export"
                content = json.dumps(manifest).encode()
            target.writestr(name, content)
    destination = tmp_path / "must-not-exist"
    with pytest.raises(ValueError):
        restore_live_workspace(campus, destination)
    assert not destination.exists()


def test_existing_destination_is_never_modified(tmp_path):
    archive = export_live_workspace(authored_workspace(tmp_path), tmp_path / "live.zip")
    destination = tmp_path / "existing"
    destination.mkdir()
    (destination / "my-work.txt").write_text("Keep my work exactly.\n")
    before = files_below(destination)
    with pytest.raises(FileExistsError):
        restore_live_workspace(archive, destination)
    assert files_below(destination) == before


@pytest.mark.parametrize("bad_name", ["../escape.py", ".env", "evidence/ls07-policies/private.key"])
def test_unsafe_archive_rejected_without_partial_restore(tmp_path, bad_name):
    archive = export_live_workspace(authored_workspace(tmp_path), tmp_path / "live.zip")
    with zipfile.ZipFile(archive, "a") as package:
        package.writestr(bad_name, "PRIVATE-SYNTHETIC-SENTINEL")
    destination = tmp_path / "must-not-exist"
    with pytest.raises(ValueError):
        restore_live_workspace(archive, destination)
    assert not destination.exists()
