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
PROTECTED_PRIVATE_MARKERS = ('__HEROIC_PRIVATE_RUNTIME_MARKER__',)
FORBIDDEN_PRIVATE_MARKERS = (
    "private.chatbot",
    "resource_ledger",
    "promotion.py",
    "operations/",
    "extractor_mapper",
)
NETWORK_MODULES = {"requests", "httpx", "urllib", "aiohttp"}
PRIVATE_IMPORT_PATTERN = re.compile(r"(?<![A-Za-z0-9_.-])(?:from|import)\s+private\.[A-Za-z0-9_.]+")
PRIVATE_PATH_PATTERN = re.compile(r"(?<![A-Za-z0-9_.-])operations/private/[A-Za-z0-9_./-]+")
PRIVATE_REVISION_PATTERN = re.compile(r"Z-Solo-King/operations@[0-9a-f]{40}")
WORKFLOW_PRIVATE_EXEC_PATTERN = re.compile(r"(?:python|python3|node|deno|go|cargo\s+run)[ \t]+(?:operations/private|.*/operations/private)")
SCAN_SUFFIXES = {".py", ".js", ".mjs", ".html", ".yml", ".yaml", ".toml", ".sh", ".json", ".md", ".txt", ".cfg", ".ini"}

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
        if path.suffix.lower() in SCAN_SUFFIXES:
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

def _is_workflow(relative: str) -> bool:
    return relative.startswith(".github/workflows/")


APPROVED_PRIVATE_EXECUTION_WORKFLOWS = frozenset({
    ".github/workflows/nightly-multi-agent-research-v3.yml",
    ".github/workflows/polyglot-migration-review.yml",
})

APPROVED_PRIVATE_BRIDGE_SCRIPTS = frozenset({
    "scripts/production_release.sh",
})


def _is_approved_private_bridge(relative: str) -> bool:
    return relative in APPROVED_PRIVATE_EXECUTION_WORKFLOWS or relative in APPROVED_PRIVATE_BRIDGE_SCRIPTS


def _is_public_safe_reference(relative: str) -> bool:
    return (
        relative.startswith("docs/")
        or _is_test(relative)
        or relative.startswith("benchmark/")
        or _is_workflow(relative)
        or _is_approved_private_bridge(relative)
    )


def secret_findings(path: Path, source: str, root: Path = ROOT) -> list[Finding]:
    relative = rel(path, root)
    if relative == "scripts/public_security_lint.py":
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

def private_reference_findings(path: Path, source: str, root: Path = ROOT) -> list[Finding]:
    relative = rel(path, root)
    if relative == "scripts/public_security_lint.py" or _is_public_safe_reference(relative):
        return []
    if PRIVATE_IMPORT_PATTERN.search(source) or PRIVATE_PATH_PATTERN.search(source):
        return [
            Finding(
                relative,
                "private-reference",
                "public runtime source contains a private implementation import/path",
            )
        ]
    return []


def workflow_private_execution_findings(path: Path, source: str, root: Path = ROOT) -> list[Finding]:
    relative = rel(path, root)
    if not _is_workflow(relative) or relative in APPROVED_PRIVATE_EXECUTION_WORKFLOWS:
        return []
    if WORKFLOW_PRIVATE_EXEC_PATTERN.search(source):
        return [
            Finding(
                relative,
                "workflow-private-execution",
                "public workflow directly executes private Operations code",
            )
        ]
    return []


def private_revision_findings(path: Path, source: str, root: Path = ROOT) -> list[Finding]:
    relative = rel(path, root)
    if relative == "scripts/public_security_lint.py" or _is_public_safe_reference(relative):
        return []
    if PRIVATE_REVISION_PATTERN.search(source):
        return [
            Finding(
                relative,
                "private-revision",
                "public runtime source embeds an immutable private Operations revision",
            )
        ]
    return []


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
    findings = secret_findings(path, source, root)
    findings.extend(private_reference_findings(path, source, root))
    findings.extend(workflow_private_execution_findings(path, source, root))
    findings.extend(private_revision_findings(path, source, root))
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
    return 1 if findings else 0

if __name__ == "__main__":
    raise SystemExit(main())
