import pytest

from backend.intelligence.authority import (
    ClaimField,
    FieldAuthority,
    evaluate_authority,
    independent_sources,
)
from backend.intelligence.lineage import SourceLineage, origin_fingerprint


@pytest.mark.parametrize(
    ("field", "authority"),
    [
        (ClaimField.SPECIFICATION, FieldAuthority.MANUFACTURER_DECLARATION),
        (ClaimField.MEASUREMENT, FieldAuthority.INDEPENDENT_MEASUREMENT),
        (ClaimField.PRICE, FieldAuthority.RETAILER_CURRENT_STATE),
        (ClaimField.STOCK, FieldAuthority.RETAILER_CURRENT_STATE),
        (ClaimField.WARRANTY, FieldAuthority.MANUFACTURER_POLICY),
        (ClaimField.SERVICE, FieldAuthority.COMMUNITY_EXPERIENCE),
        (ClaimField.EXPERIENCE, FieldAuthority.COMMUNITY_EXPERIENCE),
    ],
)
def test_allowed_field_authority(field, authority):
    decision = evaluate_authority(field, authority)
    assert decision.accepted


def test_manufacturer_declaration_cannot_be_used_as_independent_measurement():
    decision = evaluate_authority(ClaimField.MEASUREMENT, FieldAuthority.MANUFACTURER_DECLARATION)
    assert decision.accepted is False
    assert "not permitted" in decision.reason


def test_price_cannot_be_qualified_from_community_experience():
    decision = evaluate_authority(ClaimField.PRICE, FieldAuthority.COMMUNITY_EXPERIENCE)
    assert decision.accepted is False


def test_unknown_field_or_authority_rejected():
    with pytest.raises(ValueError):
        evaluate_authority("not-a-field", FieldAuthority.RETAILER_CURRENT_STATE)
    with pytest.raises(ValueError):
        evaluate_authority(ClaimField.PRICE, "not-an-authority")


def test_independence_rejects_same_origin_even_with_different_sources():
    origin = origin_fingerprint("manufacturer.example/catalog")
    first = SourceLineage("source-1", "retailer-a", origin_fingerprint=origin)
    second = SourceLineage("source-2", "retailer-b", origin_fingerprint=origin)
    assert independent_sources(first, second) is False


def test_independence_accepts_different_origins():
    first = SourceLineage("source-1", "retailer-a", origin_fingerprint=origin_fingerprint("a.example"))
    second = SourceLineage("source-2", "retailer-b", origin_fingerprint=origin_fingerprint("b.example"))
    assert independent_sources(first, second) is True


def test_republisher_is_not_independent_of_parent():
    origin = origin_fingerprint("manufacturer.example")
    parent = SourceLineage("source-1", "manufacturer", origin_fingerprint=origin)
    republished = SourceLineage(
        "source-2",
        "retailer",
        parent_source_id="source-1",
        republisher_of="source-1",
        lineage_type="republished",
        origin_fingerprint=origin,
    )
    assert independent_sources(parent, republished) is False
