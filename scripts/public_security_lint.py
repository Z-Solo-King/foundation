"""Public-repository security and trust-boundary checks.

Purpose: detect public artifacts that accidentally expose private topology,
credential material, unsafe archive extraction, or direct network access from
deterministic planner-like modules. These checks are repository-local
complements to CodeQL and must remain safe to publish.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", "__pycache__", "archive"}
PROTECTED_PRIVATE_MARKERS = ()
FORBIDDEN_PRIVATE_MARKERS = (
    "private.chatbot",
    "resource_ledger",
    "promotion.py",
    "operations/",
    "extractor_mapper",
)
NETWORK_MODULES = {"requests", "httpx", "urllib", "aiohttp"}

@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    message: str
    def text(self) -> str:
        return f"{self.path}: {self.rule}: {self.message}"

def active_files(root: Path = ROOT) -> list[Path]:
    result = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if not path.is_file() or any(part in EXCLUDED for part in relative.parts):
            continue
        if path.suffix.lower() in {".py", ".js", ".mjs", ".html", ".yml", ".yaml", ".toml"}:
            result.append(path)
    return sorted(result)

def rel(path: Path, root: Path = ROOT) -> str:
    """Return a stable repo-relative path, or a readable external path for tests."""
    base = root.resolve()
    candidate = path if path.is_absolute() else base / path
    candidate = candidate.resolve()
    try:
        return str(candidate.relative_to(base)).replace("\\", "/")
    except ValueError:
        return candidate.as_posix()

def _is_test(relative: str) -> bool:
    return relative.startswith("tests/") or relative.endswith("_test.py") or "/tests/" in relative

def _is_policy_configuration(relative: str) -> bool:
    """Workflow configuration legitimately names secret variables and private jobs."""
    return relative.startswith(".github/workflows/")

def secret_findings(path: Path, source: str) -> list[Finding]:
    relative = rel(path)
    if _is_test(relative) or _is_policy_configuration(relative) or relative == "scripts/public_security_lint.py":
        return []
    findings = []
    for marker in PROTECTED_PRIVATE_MARKERS:
        if marker in source:
            findings.append(Finding(relative, "private-marker", f"public source contains protected marker {marker}"))
    if re.search(r"Authorization\s*[:=]\s*[`\"']Bearer\s+[A-Za-z0-9._-]{20,}", source):
        findings.append(Finding(relative, "credential-literal", "public source contains a hard-coded bearer credential"))
    if re.search(r"(?i)(?:api[_-]?key|access[_-]?key|secret|password|token)\s*[:=]\s*[\"'][A-Za-z0-9_./+=:-]{24,}[\"']", source):
        findings.append(Finding(relative, "credential-literal", "public source contains a hard-coded credential-like literal"))
    return findings

def private_reference_findings(path: Path, source: str) -> list[Finding]:
    relative = rel(path)
    if _is_test(relative) or relative.startswith("docs/") or relative == "scripts/public_security_lint.py" or _is_policy_configuration(relative):
        return []
    return [
        Finding(relative, "private-reference", f"public source contains private implementation marker {marker}")
        for marker in FORBIDDEN_PRIVATE_MARKERS
        if marker in source
    ]

def python_findings(path: Path, source: str) -> list[Finding]:
    relative = rel(path)
    try:
        tree = ast.parse(source, filename=relative)
    except SyntaxError as exc:
        return [Finding(relative, "syntax", str(exc))]
    findings = []
    is_test = _is_test(relative)
    planner_like = "planner" in Path(relative).parts or Path(relative).stem.endswith("planner")
    if not is_test:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "extractall":
                findings.append(Finding(relative, "unsafe-archive-extraction", "archive.extractall() requires reviewed path-safety handling"))
    if planner_like and not is_test:
        imported = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported |= any(alias.name.split(".")[0] in NETWORK_MODULES for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported |= node.module.split(".")[0] in NETWORK_MODULES
        if imported:
            findings.append(Finding(relative, "planner-network", "planner-like module imports a direct network client"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"urlopen", "fetch"}:
                findings.append(Finding(relative, "planner-network", f"planner-like module directly calls {node.func.id}()"))
    return findings

def lint_file(path: Path, root: Path = ROOT) -> list[Finding]:
    source = path.read_text(encoding="utf-8")
    findings = secret_findings(path, source)
    findings.extend(private_reference_findings(path, source))
    if path.suffix.lower() == ".py":
        findings.extend(python_findings(path, source))
    return findings

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    files = active_files()
    findings = [f for path in files for f in lint_file(path)]
    payload = {"schema_version": "public-security-lint/v1", "files_checked": len(files), "findings": [f.text() for f in findings], "total_findings": len(findings), "passed": not findings, "strict": args.strict}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 1 if args.strict and findings else 0

if __name__ == "__main__":
    raise SystemExit(main())
