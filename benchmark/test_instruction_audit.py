from benchmark.instruction_audit import audit_instruction_documents


def test_duplicate_instruction_is_detected():
    findings = audit_instruction_documents({
        "AGENTS.md": "The agent must keep receipts.",
        "CLAUDE.md": "The agent must keep receipts.",
    })
    assert [(f.kind, f.document) for f in findings] == [("duplicate", "CLAUDE.md")]


def test_explicit_must_and_must_not_conflict_is_detected():
    findings = audit_instruction_documents({
        "a.md": "The agent must use worktrees.",
        "b.md": "The agent must not use worktrees.",
    })
    assert {f.kind for f in findings} == {"conflict"}


def test_stale_terms_are_explicit_findings():
    findings = audit_instruction_documents(
        {"a.md": "Use legacy-router for this path."},
        deprecated_terms=["legacy-router"],
    )
    assert findings[0].kind == "stale_term"
