"""
CI import-boundary check.

Scans every .py file under src/keel/ with the AST and asserts that none of them
import from the forbidden platform namespaces (app, backend).

This test must turn RED when keel code contains `import app.xxx` or
`from backend import yyy`, and GREEN when no such imports exist.
"""

import ast
import textwrap
from pathlib import Path

# Root of the keel source tree relative to this test file.
KEEL_SRC = Path(__file__).parent.parent / "src" / "keel"

# Top-level namespaces that keel must never depend on.
FORBIDDEN_PREFIXES: tuple[str, ...] = ("app", "backend")


def _collect_imports(path: Path) -> list[tuple[int, str]]:
    """Return (lineno, full_name) for every import in *path*."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                hits.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            hits.append((node.lineno, module))
    return hits


def _is_forbidden(name: str) -> bool:
    for prefix in FORBIDDEN_PREFIXES:
        if name == prefix or name.startswith(f"{prefix}."):
            return True
    return False


def test_no_platform_imports() -> None:
    """keel source must not import any forbidden platform namespace."""
    violations: list[str] = []

    py_files = sorted(KEEL_SRC.rglob("*.py"))
    assert py_files, f"No .py files found under {KEEL_SRC} — check the path."

    for py_file in py_files:
        for lineno, name in _collect_imports(py_file):
            if _is_forbidden(name):
                rel = py_file.relative_to(KEEL_SRC.parent.parent)
                violations.append(f"  {rel}:{lineno}  imports '{name}'")

    if violations:
        detail = "\n".join(violations)
        raise AssertionError(
            textwrap.dedent(f"""
                keel imports platform code — dependency boundary violated!

                Forbidden imports found:
                {detail}

                Fix: remove these imports from keel source.
                keel must only depend on stdlib and its declared pyproject.toml deps.
            """).strip()
        )
