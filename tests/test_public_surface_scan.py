from tools.public_surface_scan import public_paths, scan_metadata, scan_text


def test_public_docs_reject_private_runtime_identity():
    findings, _ = scan_text(
        "docs/CURRENT_SOURCE_OF_TRUTH.md",
        "legacy research-intelligence-engine-private Worker",
    )
    assert findings


def test_public_docs_warn_on_architecture_repo_reference():
    findings, warnings = scan_text(
        "docs/CURRENT_SOURCE_OF_TRUTH.md",
        "protected repository Z-Solo-King/operations",
    )
    assert not findings
    assert warnings


def test_pr_metadata_rejects_private_revision_and_domain():
    findings, _ = scan_metadata(
        {
            "title": "fix",
            "body": "heroic-ai.dev github:0123456789abcdef0123456789abcdef01234567",
            "commits": [],
        }
    )
    assert len(findings) >= 2


def test_recursive_public_inventory_includes_deep_docs():
    paths = public_paths()
    assert "docs/history/AI_CONTINUITY_ARCHIVE_2026-09-28.md" in paths
    assert "docs/FAMILY_SYNC_STATE_2026-09-25_R3.json" in paths
    assert len(paths) >= 100


def test_live_runtime_identifiers_are_blocked():
    samples = (
        ("docs/example.md", "Super Administrator - All Privileges"),
        ("docs/example.md", "https://private.example.workers.dev/api"),
        ("docs/example.md", "D1 identifier: 12345678-1234-1234-1234-123456789abc"),
        ("docs/example.md", "version ID: 12345678-1234-1234-1234-123456789abc"),
        ("docs/example.md", "Operations provenance 0123456789abcdef0123456789abcdef01234567"),
    )
    for path, value in samples:
        findings, _ = scan_text(path, value)
        assert findings, (path, value)


def test_forbidden_public_target_surface_is_detected():
    from tools.public_surface_scan import scan_path_rules

    findings = scan_path_rules("tools/custom_api_google_feed_recovery_1249.mjs")
    assert findings


def test_current_safe_reference_passes():
    findings, _ = scan_text("CHATGPT.md", "Foundation and Operations share project context")
    assert not findings
