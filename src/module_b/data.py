"""Data readers independent of any service, schema or provider."""
from pathlib import Path
import json
import re
from typing import TypeAlias

from module_b._files import project_file

JSONValue: TypeAlias = str | int | float | bool | None | list['JSONValue'] | dict[str, 'JSONValue']


def load_json(project: str | Path, path: str | Path) -> JSONValue:
    """Read a project-relative JSON value: object, list or scalar, unchanged."""
    if Path(path).suffix != '.json':
        raise ValueError('load_json requires a .json file.')
    return json.loads(project_file(project, path).read_text(encoding='utf-8'))


def load_jsonl(project: str | Path, path: str | Path) -> list[JSONValue]:
    """Read JSON Lines records, skipping blank lines; never execute or echo data."""
    if Path(path).suffix != '.jsonl':
        raise ValueError('load_jsonl requires a .jsonl file.')
    records = []
    with project_file(project, path).open(encoding='utf-8') as stream:
        for number, line in enumerate(stream, start=1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    raise ValueError(f'Invalid JSON on line {number} of {path}.') from None
    return records


def load_fixture(project: str | Path, name: str, *, directory: str | Path = 'fixtures') -> JSONValue:
    """Convenience reader for named fixtures; no assumption about their JSON shape."""
    if not isinstance(name, str) or not re.fullmatch(r'[a-zA-Z0-9_-]+', name):
        raise ValueError('Use a fixture name without an extension or path separators.')
    return load_json(project, Path(directory) / f'{name}.json')
