from tools.ai_provider_direct_reference_audit import ALLOWED_RELATIVE_PATHS, direct_provider_references


def test_public_ai_provider_audit_has_explicit_adapter_allowlist() -> None:
    assert "tools/woocommerce_v175_plugin_fingerprint_22.py" in ALLOWED_RELATIVE_PATHS


def test_public_ai_provider_audit_is_clean() -> None:
    assert direct_provider_references() == []
