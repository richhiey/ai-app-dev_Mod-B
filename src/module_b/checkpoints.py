"""Non-destructive checkpoint preparation shared by cumulative notebooks."""
from pathlib import Path
import json
import hashlib
import tempfile
from .workspace import prepare_example, export_workspace, restore_workspace
from .edits import write_source


def prepare_checkpoint(destination, *, checkpoint=None, recovery_files=None, repo_root=None,
                       baseline_name="checkpoint-baseline.json"):
    """Copy a checkpoint or explicitly supplied recovery overlay; preserve reruns.

    Recovery maps relative Python filenames to reviewed source strings. It is only
    used when checkpoint is None. A supplied missing checkpoint never silently
    falls back. Baselines snapshot inherited Python source and provenance before
    learner changes; they are teaching evidence, not tamper-proof grading records.
    An existing destination must have its saved baseline; no files are reset.
    """
    target = Path(destination).expanduser()
    if Path(baseline_name).name != baseline_name or not baseline_name.endswith('.json'):
        raise ValueError('Choose a plain JSON baseline filename.')
    baseline_path = target / 'fixtures' / baseline_name
    if target.exists():
        project = prepare_example(destination=target, repo_root=repo_root)
        if not baseline_path.is_file():
            raise FileExistsError('Existing checkpoint has no baseline; preserve it and choose a new destination.')
        return project, json.loads(baseline_path.read_text())
    if checkpoint is not None:
        source = Path(checkpoint).expanduser()
        if not source.exists():
            raise FileNotFoundError('Selected checkpoint does not exist; no recovery substitution was made.')
        if source.is_dir():
            with tempfile.TemporaryDirectory() as temporary:
                archive = export_workspace(source, Path(temporary) / 'checkpoint.zip')
                project = restore_workspace(archive, target)
        else:
            project = restore_workspace(source, target)
        provenance = 'learner checkpoint copied; original retained'
    else:
        if not recovery_files:
            raise ValueError('Select a checkpoint or explicitly supply recovery source.')
        project = prepare_example(destination=target, repo_root=repo_root)
        for relative, source in recovery_files.items():
            existing = project / relative
            write_source(project, relative, source, expected=existing.read_text() if existing.is_file() else None)
        provenance = 'supplied prerequisite recovery; not learner-created completion evidence'
    baseline = {'provenance': provenance,
                'inherited_data_sha256': {p.relative_to(project).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in sorted((project / 'data').rglob('*.json'))},
                'inherited_source': {p.relative_to(project).as_posix(): p.read_text()
                                     for p in sorted((project / 'app').rglob('*.py'))}}
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    # A cumulative checkpoint can already contain this stage's earlier baseline.
    # Preserve that imported record in the NEW copy before recording its new entry state.
    if baseline_path.exists():
        index = 1
        inherited = baseline_path.with_name(baseline_path.stem + f'.inherited-{index}.json')
        while inherited.exists():
            index += 1
            inherited = baseline_path.with_name(baseline_path.stem + f'.inherited-{index}.json')
        baseline_path.rename(inherited)
    with baseline_path.open('x') as stream:
        json.dump(baseline, stream, indent=2)
    return project, baseline
