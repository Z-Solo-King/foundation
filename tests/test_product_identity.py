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
