from __future__ import annotations

import re
from pathlib import Path

WORKFLOW_ROOT = Path(__file__).parents[1] / ".github" / "workflows"
SHA_REF = re.compile(r"^[0-9a-f]{40}$")


CANONICAL_OPERATIONS_REPOSITORY = "Z-Solo-King/operations"
CANONICAL_OPERATIONS_REF = "cf28a28cb40de527aff1cd87f96e103669635f70"


def _workflow_texts() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(WORKFLOW_ROOT.glob("*.y*ml"))
    }


def test_all_third_party_actions_are_sha_pinned():
    violations = []
    for name, text in _workflow_texts().items():
        for line_no, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if not stripped.startswith("uses:"):
                continue
            ref = stripped.split("@", 1)[-1].split("#", 1)[0].strip()
            action = stripped.split("uses:", 1)[1].split("@", 1)[0].strip()
            if action.startswith("./") or action.startswith("docker://"):
                continue
            if not SHA_REF.fullmatch(ref):
                violations.append(f"{name}:{line_no}:{action}@{ref}")
    assert not violations, "Unpinned third-party GitHub Actions:\n" + "\n".join(violations)


def test_production_deployment_has_one_owner():
    texts = _workflow_texts()
    deployers = [name for name, text in texts.items() if "pywrangler deploy" in text]
    assert deployers == ["codeql.yml"], deployers

    forbidden = re.compile(r"(?i)(workers\s+build|deploy\s+hook|deploy_hook|workers-builds)")
    violations = [
        f"{name}:{line_no}:{line.strip()}"
        for name, text in texts.items()
        for line_no, line in enumerate(text.splitlines(), 1)
        if forbidden.search(line)
    ]
    assert not violations, "Competing Cloudflare deployment references:\n" + "\n".join(violations)


def test_canonical_operations_production_pin_is_single_and_current():
    codeql = _workflow_texts()["codeql.yml"]
    assert f"OPERATIONS_REPOSITORY: {CANONICAL_OPERATIONS_REPOSITORY}" in codeql
    assert f"OPERATIONS_REF: {CANONICAL_OPERATIONS_REF}" in codeql
    assert codeql.count(CANONICAL_OPERATIONS_REF) == 2
    assert "bb1d8c33e926a9752de86492e9d35f26a5f2824c" not in codeql
    assert "OPERATIONS_REF:" not in codeql.split("jobs:", 1)[1]
    assert 'git clone --no-checkout "https://github.com/${OPERATIONS_REPOSITORY}.git"' in codeql
    assert '"github:${OPERATIONS_REF}"' in codeql


def test_operations_checkout_uses_dedicated_github_credential():
    codeql = _workflow_texts()["codeql.yml"]
    assert "OPERATIONS_READ_TOKEN: ${{ secrets.OPERATIONS_READ_TOKEN }}" in codeql
    assert "BACKUP_GITHUB_TOKEN" not in codeql
    assert "B2_APPLICATION_KEY" in codeql
    assert "OPERATIONS_READ_TOKEN" in codeql
    assert "api.github.com/repos/${OPERATIONS_REPOSITORY}" in codeql
    assert "OPERATIONS_READ_TOKEN cannot access the expected private Operations repository." in codeql


def test_required_ci_contract_supports_merge_group():
    texts = _workflow_texts()
    codeql = texts["codeql.yml"]
    frontend = texts["frontend-ui.yml"]
    assert "merge_group:" in codeql
    assert "types: [checks_requested]" in codeql
    assert "name: Public tests" in codeql
    assert "name: Analyze python" in codeql
    assert "npm test" in codeql
    assert "merge_group:" in frontend
