"""Small file and checkpoint utilities shared by Sprint 2 and Sprint 3 notebooks."""

from datetime import datetime, timezone
from html import escape
import ast
import hashlib
import json
from pathlib import Path
import re

from .edits import content_fingerprint, preserves_statements, write_source
from .workspace import export_workspace


def revision(project: str | Path) -> str:
    """Fingerprint application Python and JSON data files."""
    return content_fingerprint(project, directories=("app", "data"), suffixes=(".py", ".json"))


def table(rows: list[dict], columns: list[str] | None = None) -> None:
    """Display selected observation fields as a small escaped HTML table."""
    if not rows:
        print("No observations yet.")
        return

    from IPython.display import HTML, display

    columns = columns or list(rows[0])
    header = "".join(f"<th>{escape(str(column))}</th>" for column in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{escape(str(row.get(column, '')))}</td>" for column in columns) + "</tr>"
        for row in rows
    )
    display(HTML(f"<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"))


def apply_student_edits(project: str | Path, edits: dict[str, str]) -> None:
    """Write only explicit learner source files under app/."""
    root = Path(project).resolve()
    for name, source in edits.items():
        relative = Path(name)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or len(relative.parts) < 2
            or relative.parts[0] != "app"
            or relative.suffix != ".py"
        ):
            raise ValueError("Learner edits must use relative app/*.py paths.")

        target = root
        for part in relative.parts:
            target /= part
            if target.is_symlink():
                raise ValueError("Learner edits cannot follow symbolic links.")
        ast.parse(source, filename=name)

    for name, source in edits.items():
        path = root / name
        expected = path.read_text() if path.is_file() else None
        write_source(root, name, source, expected=expected)

    if edits:
        print("Saved:", ", ".join(edits))
    else:
        print("No source changes supplied.")


def register_source(project: str | Path, registration: str) -> None:
    """Append one visible route-registration block to app/main.py."""
    root = Path(project)
    path = root / "app/main.py"
    source = path.read_text()
    if registration not in source:
        write_source(root, "app/main.py", source + registration, expected=source)


def baseline(project: str | Path, name: str, paths: list[str]) -> dict:
    """Record inherited source and data once for a later-sprint checkpoint."""
    if re.fullmatch(r"[a-z0-9-]+", name) is None:
        raise ValueError("Use a lowercase stage name with letters, digits, and hyphens.")

    root = Path(project)
    record_path = root / "fixtures" / f"{name}-baseline.json"
    if record_path.is_file():
        return json.loads(record_path.read_text())

    record = {
        "inherited_paths": list(paths),
        "inherited_source": {
            path.relative_to(root).as_posix(): path.read_text()
            for path in sorted((root / "app").rglob("*.py"))
        },
        "inherited_data_sha256": {
            path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((root / "data").rglob("*.json"))
        },
    }
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record_path.write_text(json.dumps(record, indent=2) + "\n")
    return record


def preserved(project: str | Path, inherited: dict, *, mutable: tuple[str, ...] = ()) -> dict[str, bool]:
    """Check inherited files and confirm app/main.py retains its original statements."""
    root = Path(project)
    source_preserved = all(
        (root / name).is_file() and (root / name).read_text() == source
        for name, source in inherited["inherited_source"].items()
        if name not in {"app/main.py", *mutable}
    )
    registration_preserved = preserves_statements(
        inherited["inherited_source"]["app/main.py"],
        (root / "app/main.py").read_text(),
    )
    data_preserved = all(
        (root / name).is_file()
        and hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
        for name, digest in inherited["inherited_data_sha256"].items()
    )
    return {
        "source_preserved": source_preserved,
        "registration_preserved": registration_preserved,
        "data_preserved": data_preserved,
    }


def fresh(report: dict, project: str | Path, selection: dict | None = None) -> bool:
    """Check that saved observations still match their source and task selection."""
    return report.get("source_revision") == revision(project) and (
        selection is None or report.get("selection") == selection
    )


def export_progress(
    project: str | Path,
    destination: str | Path,
    *,
    sprint: int,
    evidence: dict,
    notes: dict,
    readiness: dict,
) -> Path:
    """Save one checkpoint ZIP with its current evidence record."""
    root = Path(project)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    record = {
        "sprint": sprint,
        "saved_at": stamp,
        "source_revision": revision(root),
        "readiness": readiness,
        "observations": evidence,
        "notes": notes,
        "instructor_review": "pending",
    }
    fixture_dir = root / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    (fixture_dir / f"sprint-{sprint}-progress.json").write_text(json.dumps(record, indent=2) + "\n")

    archive = export_workspace(root, Path(destination) / f"sprint-{sprint}-checkpoint-{stamp}.zip")
    print("Download the source checkpoint:", archive)
    return archive
