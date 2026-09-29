"""Display the learner's current application source without importing or running it."""
from __future__ import annotations

import ast
from pathlib import Path
from collections.abc import Sequence
from module_b._files import project_file


def source_excerpt(
    project: str | Path,
    path: str | Path,
    symbol: str | None = None,
    *,
    roots: Sequence[str] = ("app",),
) -> str:
    """Read current Python source; optionally select an AST definition.

    Existing notebooks default to app/. Pass roots=("src", "scripts") for another
    layout, or roots=(".",) to inspect project Python files. Traversal, private
    folders and symbolic links are refused. This never imports the code.
    Dotted symbols and decorators are supported. For UI/non-Python components,
    use source_text with explicitly selected roots and suffixes.
    """
    if Path(path).suffix != ".py":
        raise ValueError("source_excerpt requires a Python file; use source_text for other formats.")
    candidate = project_file(project, path, roots=roots)
    relative = Path(path)
    text = candidate.read_text(encoding="utf-8")
    if symbol is None:
        return text
    if not isinstance(symbol, str) or not symbol or any(not part.isidentifier() for part in symbol.split(".")):
        raise ValueError("Symbol must be a definition name or a dotted definition path.")
    scope = ast.parse(text, filename=str(relative)).body
    definition: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | None = None
    for name in symbol.split("."):
        matches = [node for node in scope if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name]
        if len(matches) != 1:
            raise ValueError(f"Expected one definition for {symbol!r} in {relative}; found {len(matches)} for {name!r}.")
        definition = matches[0]
        scope = definition.body
    assert definition is not None and definition.end_lineno is not None
    first_line = min([definition.lineno, *[decorator.lineno for decorator in definition.decorator_list]])
    return "".join(text.splitlines(keepends=True)[first_line - 1 : definition.end_lineno])


def source_text(
    project: str | Path,
    path: str | Path,
    *,
    roots: Sequence[str],
    suffixes: Sequence[str],
) -> str:
    """Read a complete explicitly allowed source file, including UI components.

    Example: source_text(project, "web/client.ts", roots=("web",), suffixes=(".ts",)).
    Only Python definitions have AST selection; this function returns plain text.
    """
    if isinstance(suffixes, str) or not suffixes or any(not s.startswith(".") or "/" in s or "\\" in s for s in suffixes):
        raise ValueError("suffixes must be an explicit sequence such as ('.ts', '.css').")
    if Path(path).suffix not in suffixes:
        raise ValueError("File type is not allowed by the inspection suffixes.")
    return project_file(project, path, roots=roots).read_text(encoding="utf-8")
