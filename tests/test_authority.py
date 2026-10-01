import pytest
from backend.intelligence.authority import *
from backend.intelligence.lineage import SourceLineage,origin_fingerprint
RULES={
 ClaimField.SPECIFICATION:{FieldAuthority.MANUFACTURER_DECLARATION,FieldAuthority.INDEPENDENT_MEASUREMENT},
 ClaimField.MEASUREMENT:{FieldAuthority.INDEPENDENT_MEASUREMENT},
 ClaimField.PRICE:{FieldAuthority.RETAILER_CURRENT_STATE},
 ClaimField.STOCK:{FieldAuthority.RETAILER_CURRENT_STATE},
 ClaimField.WARRANTY:{FieldAuthority.MANUFACTURER_POLICY,FieldAuthority.RETAILER_CURRENT_STATE},
 ClaimField.SERVICE:{FieldAuthority.MANUFACTURER_POLICY,FieldAuthority.COMMUNITY_EXPERIENCE},
 ClaimField.EXPERIENCE:{FieldAuthority.COMMUNITY_EXPERIENCE},
}
def test_generic_evaluator_accepts_supplied_rules():
    assert evaluate_authority(ClaimField.PRICE,FieldAuthority.RETAILER_CURRENT_STATE,allowed_authorities=RULES).accepted
    assert not evaluate_authority(ClaimField.PRICE,FieldAuthority.COMMUNITY_EXPERIENCE,allowed_authorities=RULES).accepted
def test_invalid_values_fail_closed():
    with pytest.raises(ValueError): evaluate_authority("bad",FieldAuthority.PRICE if False else FieldAuthority.RETAILER_CURRENT_STATE,allowed_authorities=RULES)
    with pytest.raises(ValueError): evaluate_authority(ClaimField.PRICE,"bad",allowed_authorities=RULES)
def test_independence_remains_generic():
    origin=origin_fingerprint("manufacturer.example")
    a=SourceLineage("a","one",origin_fingerprint=origin);b=SourceLineage("b","two",origin_fingerprint=origin)
    assert not independent_sources(a,b)
