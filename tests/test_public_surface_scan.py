from tools.public_surface_scan import scan_metadata, scan_text

def test_public_docs_reject_private_runtime_identity():
    findings, _ = scan_text("docs/CURRENT_SOURCE_OF_TRUTH.md", "legacy research-intelligence-engine-private Worker")
    assert findings

def test_public_docs_warn_on_architecture_repo_reference():
    findings, warnings = scan_text("docs/CURRENT_SOURCE_OF_TRUTH.md", "protected repository Z-Solo-King/operations")
    assert not findings
    assert warnings

def test_pr_metadata_rejects_private_revision_and_domain():
    findings, _ = scan_metadata({"title":"fix", "body":"heroic-ai.dev github:0123456789abcdef0123456789abcdef01234567", "commits":[]})
    assert len(findings) >= 2

def test_current_safe_reference_passes():
    findings, _ = scan_text("CHATGPT.md", "Foundation and Operations share project context")
    assert not findings
