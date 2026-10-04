"""Load fresh main source and prepare notebook workspaces without generating code.

Loaded with runpy from the freshly cloned checkout, so a previously imported
module_b package cannot intercept setup. Teaching operations remain in cells.
"""
import importlib
import os
from pathlib import Path
import sys
import uuid


def prepare_campus(*, repo, base, sprint, project, checkpoint="", previous=None):
    """Close old demo resources, refresh imports, and preserve learner files."""
    if sprint not in (1, 2, 3):
        raise ValueError("Campus sprint must be 1, 2, or 3.")
    repo, base = Path(repo).resolve(), Path(base).resolve()
    previous = {} if previous is None else previous
    # A TestClient whose __enter__ failed has no exit_stack. Do not invoke its
    # __exit__: that would hide the original problem behind a new AttributeError.
    old_client = previous.get("client")
    if old_client is not None:
        stack = getattr(old_client, "exit_stack", None)
        if stack is not None:
            stack.close()
        if hasattr(old_client, "close"):
            old_client.close()
        previous["client"] = None
    old_service = previous.get("service")
    if old_service is not None:
        old_service.stop()
        previous["service"] = None

    sys.path.insert(0, str(repo / "src"))
    loaded = sys.modules.get("module_b")
    stale = loaded is not None and Path(loaded.__file__).resolve().parent != repo / "src/module_b"
    for name in list(sys.modules):
        if name == "app" or name.startswith("app.") or (
            stale and (name == "module_b" or name.startswith("module_b."))
        ):
            del sys.modules[name]
    importlib.invalidate_caches()

    from module_b.campus import prepare_project
    from module_b.openrouter import DEFAULT_CHAT_MODEL, require_openrouter_key
    from module_b.workspace import prepare_example

    require_openrouter_key(prompt=True)
    os.environ.setdefault("OPENROUTER_MODEL", DEFAULT_CHAT_MODEL)
    os.environ["CAMPUS_SPRINT"] = str(sprint)
    project = prepare_project(repo, project, checkpoint)
    # Each setup gets a new demo/database path. No delete/reset is applied to a
    # previous folder, which may still hold notes or a native database handle.
    demo = prepare_example(
        destination=base / f"fieldcare-campus-demo-{sprint}-{uuid.uuid4().hex[:12]}",
        repo_root=repo,
    )
    os.chdir(demo)
    sys.path.insert(0, str(demo))
    print("Instructor source:", demo)
    print("Your project:", project)
    print("Project origin:", "imported checkpoint" if checkpoint else "supplied starter (not a completed assessment)")
    return demo, project
