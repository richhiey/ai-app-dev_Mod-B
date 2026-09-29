# Extending the shared core

The reusable layer manages files, processes and notebook evidence. Business rules, provider configuration and teaching operations belong in examples or explicit case-specific helpers. The core is an ASGI/Python notebook toolkit, not a plugin framework or a completed implementation of later sprints.

## Run another service

`ServiceProcess` has no knowledge of FieldCare or OpenRouter. Select an import path, factory flag, environment and readiness policy:

```python
import httpx
from module_b.runtime import ServiceProcess

with ServiceProcess(
    "catalog.api:create_app",
    project_dir=project,
    factory=True,
    env={"CATALOG_MODE": "fixture", "OLD_SETTING": None},
    inherit_env=False,
    health_path="/ready",
    health_status=204,
) as service:
    response = httpx.get(f"{service.base_url}/items")
```

This illustrative import path must exist in your example. The tests exercise a second, independent ASGI factory with an authenticated `/ready` route and HTTP 204. `health_headers` can supply that endpoint's required headers; they are private and are not included in diagnostic messages. Keep any actual keys in runtime configuration.

With `inherit_env=True` (the default), supplied values override inherited settings and `None` removes a named setting. With `False`, only explicit settings are passed; supply any OS settings your particular app requires. Uvicorn process-control variables are always stripped so inherited settings cannot change the helper's owned process or load a hidden env file.

FieldCare notebooks use `module_b.fieldcare.demo_service(project)` to explicitly select demo mode and remove its provider credentials. Live or other provider configurations use the generic runner with explicit settings. This keeps application policy out of the core.

## Inspect another layout

```python
from module_b.source import source_excerpt, source_text

print(source_excerpt(project, "src/catalog/api.py", "create_app", roots=("src",)))
print(source_text(project, "web/client.ts", roots=("web",), suffixes=(".ts",)))
```

The existing `app/` default remains compatible. Python definitions are selected with AST inspection, including decorators; no inspected code runs. Other languages are displayed as whole text files under explicit roots/extensions. Symlinks, traversal and private/cache paths are refused.

## Read different data shapes

```python
from module_b.data import load_fixture, load_json, load_jsonl

cases = load_fixture(project, "batch", directory="cases")
settings = load_json(project, "config/public-settings.json")
events = load_jsonl(project, "events/sanitized.jsonl")
```

JSON readers preserve objects, arrays and scalar values; they do not assume the diagnostic request schema. JSONL parsing reports a bad line number without echoing its payload. Loading records is not an evaluation framework or a redaction guarantee. The future evaluation lesson must still invoke the authentic Module A evaluator.

## Preserve new component types

The default checkpoint policy retains the original app/data/fixture formats. Adding a UI or another source layout requires an explicit policy so files are not silently omitted:

```python
from module_b.workspace import WorkspacePolicy, export_workspace, restore_workspace

policy = WorkspacePolicy(
    directory_suffixes={
        "app": (".py",),
        "src": (".py",),
        "data": (".json", ".csv"),
        "fixtures": (".json",),
        "web": (".ts", ".tsx", ".js", ".css", ".html"),
        "events": (".jsonl",),
    },
    root_files=("trace-record.md", "package.json", "README.md"),
)
archive = export_workspace(project, "my-new-checkpoint.zip", policy=policy)
restored = restore_workspace(archive, "work/restored-project", policy=policy)
```

A supplied directory mapping replaces the defaults; list every directory you need. The immutable policy is author-owned. **Use the same trusted policy for export and restore**; an archive cannot grant itself additional file access. The original four-field workspace manifest remains compatible. Old checkpoints still restore under the default policy.

Common secret/cache paths remain excluded even when an extension is allowed. `.env.example` can remain in prepared examples; real `.env` variants, key files and dependency caches are omitted. Explicitly review permitted source/data before sharing—an allowlist cannot detect a credential pasted into code. Export and restore both enforce 20 MiB / 2,000-member limits and never overwrite an existing destination.

## Add a course component

1. Create a teaching example or extend the relevant verified service checkpoint. Keep actual route/configuration/HTTP operations visible to learners.
2. Add a focused module under `src/module_b` only for reusable infrastructure. A case-specific probe stays named and scoped to its example.
3. Write behavioural tests using another example or layout where generality is claimed. Avoid proving reuse only with FieldCare.
4. Add a Colab notebook that imports shared helpers. Verify it from a fresh local environment and preserve learner edits on repeated setup.
5. Run `scripts/verify_notebooks.py`. It discovers notebooks across sprint folders and examples with `tests/`; output evidence preserves the notebook directory structure to avoid filename collisions.
6. Create a new verified checkpoint. Keep earlier tags unchanged; revise the current notebooks' bootstrap reference when intentionally upgrading them.

Auth, quotas, streaming, sanitized events and UI connectors can each be added through these extension points. Their educational implementation remains incremental; this review does not claim they already exist.
