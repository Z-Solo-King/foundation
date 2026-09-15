from foundation_core.product_identity import identity_matches


def test_exact_sku_match_is_accepted():
    result = identity_matches(
        {"sku": "ABC-123", "brand": "Acme"},
        {"sku": "ABC-123", "brand": "Acme", "title": "Widget"},
    )
    assert result.accepted
    assert "sku" in result.matched_fields


def test_exact_gtin_match_is_accepted():
    result = identity_matches({"gtin": "8901234567890"}, {"gtin13": "8901234567890"})
    assert result.accepted
    assert "gtin" in result.matched_fields


def test_conflicting_strong_identifier_rejects_candidate():
    result = identity_matches({"sku": "A", "brand": "Acme"}, {"sku": "B", "brand": "Acme"})
    assert not result.accepted
    assert result.conflicts == ("sku",)


def test_url_trailing_slash_normalization_is_accepted():
    result = identity_matches(
        {"url": "https://example.com/product/widget/"},
        {"url": "https://example.com/product/widget"},
    )
    assert result.accepted
    assert "url" in result.matched_fields


def test_relative_url_is_normalized_without_inventing_origin():
    result = identity_matches({"url": "/product/widget/"}, {"url": "/product/widget"})
    assert result.accepted


def test_identity_mapping_value_is_supported():
    result = identity_matches(
        {"brand": {"name": "Acme"}, "sku": {"value": "ABC-123"}},
        {"brand": "Acme", "sku": "ABC-123"},
    )
    assert result.accepted


def test_brand_and_title_exact_match_is_accepted_without_strong_id():
    result = identity_matches(
        {"brand": "Acme", "title": "Widget 16GB"},
        {"brand": "ACME", "name": "Widget 16GB"},
    )
    assert result.accepted


def test_related_product_with_only_a_similar_title_is_rejected():
    result = identity_matches(
        {"brand": "Acme", "title": "Widget Pro 16GB"},
        {"brand": "Acme", "title": "Widget Pro 8GB"},
    )
    assert not result.accepted


def test_missing_identity_does_not_become_a_match():
    result = identity_matches({"title": "Widget"}, {"description": "Widget"})
    assert not result.accepted


def test_variant_id_mismatch_is_rejected():
    result = identity_matches(
        {"sku": "ABC", "variant_id": "black-16gb"},
        {"sku": "ABC", "variant_id": "white-16gb"},
    )
    assert not result.accepted
    assert "variant_id" in result.conflicts


def test_matching_variant_dimensions_are_preserved():
    dimensions = {
        "region": "IN",
        "storage": "1TB",
        "color": "black",
        "cpu": "Core Ultra 7",
        "gpu": "RTX 5070",
        "display_size": "16",
        "seller": "Acme Retail",
        "condition": "new",
        "bundle_type": "single",
    }
    result = identity_matches(
        {"sku": "ABC", **dimensions},
        {"sku": "ABC", **dimensions},
    )
    assert result.accepted
    assert all(field in result.matched_fields for field in dimensions)


def test_region_mismatch_rejects_exact_sku_candidate():
    result = identity_matches(
        {"sku": "ABC", "region": "IN"},
        {"sku": "ABC", "region": "US"},
    )
    assert not result.accepted
    assert "region" in result.conflicts


def test_storage_mismatch_rejects_exact_sku_candidate():
    result = identity_matches(
        {"sku": "ABC", "storage": "1TB"},
        {"sku": "ABC", "storage": "512GB"},
    )
    assert not result.accepted
    assert "storage" in result.conflicts


def test_display_and_compute_variant_mismatch_rejects_candidate():
    result = identity_matches(
        {
            "sku": "ABC",
            "color": "black",
            "cpu": "Core Ultra 7",
            "gpu": "RTX 5070",
            "display_size": "16",
        },
        {
            "sku": "ABC",
            "color": "white",
            "cpu": "Core Ultra 5",
            "gpu": "RTX 5060",
            "display_size": "14",
        },
    )
    assert not result.accepted
    assert set(result.conflicts) == {"color", "cpu", "gpu", "display_size"}


def test_seller_condition_and_bundle_mismatch_rejects_candidate():
    result = identity_matches(
        {
            "sku": "ABC",
            "seller": "Acme Retail",
            "condition": "new",
            "bundle_type": "single",
        },
        {
            "sku": "ABC",
            "seller": "Other Retail",
            "condition": "renewed",
            "bundle_type": "bundle",
        },
    )
    assert not result.accepted
    assert set(result.conflicts) == {"seller", "condition", "bundle_type"}
