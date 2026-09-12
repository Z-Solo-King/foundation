"""Bound public repository context for reliable AI-assisted maintenance."""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROD_BYTES, TEST_BYTES = 30_000, 45_000
PROD_FUNCTION, TEST_FUNCTION, PROD_CLASS = 75, 110, 180
SKIP = {".git", ".venv", "__pycache__"}


def _span(node: ast.AST) -> int:
    return max(0, getattr(node, "end_lineno", 0) - getattr(node, "lineno", 0) + 1)


def main() -> int:
    failures: list[str] = []
    for root in (ROOT / "backend", ROOT / "tests"):
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if any(part in SKIP for part in path.parts):
                continue
            relative = path.relative_to(ROOT).as_posix()
            is_test = relative.startswith("tests/")
            limit = TEST_BYTES if is_test else PROD_BYTES
            if path.stat().st_size > limit:
                failures.append(f"module {relative}: {path.stat().st_size} > {limit}")
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
            except (OSError, SyntaxError) as exc:
                failures.append(f"parse {relative}: {exc}")
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    function_limit = TEST_FUNCTION if is_test else PROD_FUNCTION
                    if _span(node) > function_limit:
                        failures.append(f"function {relative}:{node.name}: {_span(node)} > {function_limit}")
                elif isinstance(node, ast.ClassDef) and not is_test and _span(node) > PROD_CLASS:
                    failures.append(f"class {relative}:{node.name}: {_span(node)} > {PROD_CLASS}")
    for failure in failures:
        print(f"FAIL {failure}")
    if failures:
        return 1
    print("PASS foundation context budget")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
