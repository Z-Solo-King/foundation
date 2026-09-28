from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_PUBLIC_FILES = {
    "INSTALL.ps1",
    "README.txt",
    "README_BATCH.txt",
    "PHASE_0_CONSOLIDATION_AUDIT.md",
}


def test_private_bundle_files_are_absent():
    for name in FORBIDDEN_PUBLIC_FILES:
        assert not (ROOT / name).exists(), f"private/internal file leaked: {name}"


def test_public_deployment_is_standalone_and_uses_safe_placeholders():
    text = (ROOT / "wrangler.toml").read_text(encoding="utf-8")
    assert "REPLACE_WITH_D1_DATABASE_ID" in text
    assert "REPLACE_WITH_PUBLIC_DATABASE_NAME" in text
    assert "B2_BUCKET = \"REPLACE_WITH_B2_BUCKET\"" in text
    assert "B2_ENDPOINT = \"REPLACE_WITH_B2_ENDPOINT\"" in text
    assert "[[services]]" not in text
    assert "CONTROL_PLANE" not in text
    assert "REPLACE_WITH_PRIVATE_CONTROL_PLANE_SERVICE" not in text
    assert "[[r2_buckets]]" not in text
    assert "ARTIFACTS" not in text
    assert "research-intelligence-engine-private" not in text


def test_public_docs_do_not_name_private_service():
    for path in (ROOT / "README.md", ROOT / "DEPLOYMENT.md"):
        text = path.read_text(encoding="utf-8")
        assert "research-intelligence-engine-private" not in text


def test_live_feed_recovery_assets_are_not_public():
    forbidden = (
        "tools/woocommerce_google_feed_ai_agents_1247.mjs",
        "tools/woocommerce_google_feed_rescue_fast.mjs",
        "tools/custom_api_google_feed_recovery_1249.mjs",
        "tools/custom_api_google_feed_browser_probe_1249.mjs",
        "data/feed_lab/custom_api_google_feed_registry_2026-09-27.json",
        ".github/workflows/woocommerce-google-feed-recovery-1247.yml",
        ".github/workflows/custom-api-google-feed-recovery-1249-live.yml",
    )
    for path in forbidden:
        assert not (ROOT / path).exists(), f"live target asset leaked: {path}"


def test_public_operational_docs_use_redacted_runtime_markers():
    for path in (
        ROOT / "docs" / "CURRENT_LIVE_AUDIT_2026-09-25_R2.md",
        ROOT / "docs" / "CURRENT_LIVE_AUDIT_2026-09-25_R3.md",
        ROOT / "docs" / "WORKER_IDENTITY_2026-09-25.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "heroic-ai.dev" not in text
        assert "Super Administrator - All Privileges" not in text
        assert "research-intelligence" not in text
