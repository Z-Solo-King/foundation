"""Static checks for GitHub Actions workflow hardening.

The checks are dependency-free so they run before installing project packages.
They deliberately fail closed on obvious unsafe workflow constructs rather than
attempting to replace GitHub's YAML validator.
"""
from __future__ import annotations

from pathlib import Path
import re

WORKFLOW_DIR = Path(".github/workflows")
SHA_RE = re.compile(r"@[0-9a-fA-F]{40}(?:\s+#.*)?$")
USES_RE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)\s*$")


def main() -> int:
    failures: list[str] = []
    workflow_files = sorted(WORKFLOW_DIR.glob("*.y*ml"))
    if not workflow_files:
        failures.append("no workflow files found")

    for path in workflow_files:
        text = path.read_text(encoding="utf-8")
        for line_no, raw in enumerate(text.splitlines(), 1):
            line = raw.rstrip()
            match = USES_RE.match(line)
            if match and not SHA_RE.search(match.group(1)):
                failures.append(
                    f"{path}:{line_no}: action reference is not pinned to a full 40-character commit SHA"
                )
        lowered = text.lower()
        if "pull_request_target:" in lowered:
            failures.append(f"{path}: pull_request_target is forbidden in the public project")
        if "permissions:\n" not in text:
            failures.append(f"{path}: workflow must declare explicit permissions")

    if failures:
        for failure in failures:
            print(failure)
        return 1

    print(f"GitHub workflow policy OK: {len(workflow_files)} workflows checked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
