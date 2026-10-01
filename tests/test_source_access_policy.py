import pytest
from datetime import datetime,timezone
from backend.sources.access_policy import *

TTL={RetentionClass.NONE:0,RetentionClass.EPHEMERAL:0,RetentionClass.SHORT:86400,RetentionClass.STANDARD:604800,RetentionClass.UNKNOWN:None}
def p(**o):
    v=dict(policy_version=SOURCE_ACCESS_POLICY_VERSION,access_class=AccessClass.PUBLIC,acquisition_method="http_get",requires_authentication=False,robots_restriction=False,retention_class=RetentionClass.SHORT,raw_content_allowed=False,disclosure_class=DisclosureClass.PUBLIC_SAFE,revalidation_required=True,revalidation_after_seconds=None);v.update(o);return SourceAccessPolicy(**v)
def test_contract_and_public_safe_default():
    x=p();x.validate();d=decide_source_access(x,requested_disclosure=DisclosureClass.PUBLIC_SAFE,request_authenticated=False,restricted_research=True);assert d.allowed and d.revalidate
def test_auth_and_restricted_guards():
    with pytest.raises(ValueError): p(access_class=AccessClass.UNKNOWN).validate()
    with pytest.raises(ValueError): p(retention_class=RetentionClass.UNKNOWN).validate()
    with pytest.raises(ValueError): p(access_class=AccessClass.AUTHENTICATED,requires_authentication=False).validate()
    auth=p(access_class=AccessClass.AUTHENTICATED,requires_authentication=True,disclosure_class=DisclosureClass.PRIVATE_ONLY)
    assert not decide_source_access(auth,requested_disclosure=DisclosureClass.PUBLIC_SAFE,request_authenticated=False,restricted_research=True).allowed
    restricted=p(access_class=AccessClass.RESTRICTED,disclosure_class=DisclosureClass.PRIVATE_ONLY)
    assert not decide_source_access(restricted,requested_disclosure=DisclosureClass.METADATA_ONLY,request_authenticated=True,restricted_research=False).allowed
def test_generic_retention_and_conflict():
    observed=datetime(2026,9,18,tzinfo=timezone.utc);x=p()
    assert retention_seconds(x,TTL)==86400
    assert expires_at(observed,x,TTL).isoformat().startswith("2026-09-19")
    assert revalidation_due(observed,x,default_revalidation_seconds=86400).isoformat().startswith("2026-09-19")
    restricted=p(access_class=AccessClass.RESTRICTED,disclosure_class=DisclosureClass.PRIVATE_ONLY)
    ranks={AccessClass.RESTRICTED:4,AccessClass.AUTHENTICATED:3,AccessClass.PUBLIC:2,AccessClass.UNKNOWN:0},{DisclosureClass.FORBIDDEN:4,DisclosureClass.PRIVATE_ONLY:3,DisclosureClass.METADATA_ONLY:2,DisclosureClass.PUBLIC_SAFE:1},{RetentionClass.NONE:4,RetentionClass.EPHEMERAL:3,RetentionClass.SHORT:2,RetentionClass.STANDARD:1,RetentionClass.UNKNOWN:0}
    assert resolve_source_policy_conflict([x,restricted],access_rank=ranks[0],disclosure_rank=ranks[1],retention_rank=ranks[2]).access_class is AccessClass.RESTRICTED
def test_fail_closed_edges():
    with pytest.raises(ValueError): p(policy_version="v0").validate()
    with pytest.raises(ValueError): p(acquisition_method=" ").validate()
    with pytest.raises(ValueError): p(revalidation_after_seconds=-1).validate()
    with pytest.raises(ValueError): expires_at(datetime(2026,9,18),p(),TTL)
    with pytest.raises(ValueError): revalidation_due(datetime(2026,9,18),p())
