from datetime import datetime, timezone
import pytest
from backend.sources.access_policy import (
    SOURCE_ACCESS_POLICY_VERSION, AccessClass, DisclosureClass, RetentionClass,
    SourceAccessPolicy, SourceAccessDecision, decide_source_access,
    expires_at, revalidation_due, retention_seconds, resolve_source_policy_conflict,
)

def policy(**overrides):
    values=dict(policy_version=SOURCE_ACCESS_POLICY_VERSION,access_class=AccessClass.PUBLIC,acquisition_method="http_get",
        requires_authentication=False,robots_restriction=False,retention_class=RetentionClass.SHORT,
        raw_content_allowed=False,disclosure_class=DisclosureClass.PUBLIC_SAFE,revalidation_required=True,
        revalidation_after_seconds=None)
    values.update(overrides)
    return SourceAccessPolicy(**values)

TTL={RetentionClass.NONE:0,RetentionClass.EPHEMERAL:0,RetentionClass.SHORT:86400,RetentionClass.STANDARD:604800,RetentionClass.UNKNOWN:None}
RANKS=(
 {AccessClass.RESTRICTED:4,AccessClass.AUTHENTICATED:3,AccessClass.PUBLIC:2,AccessClass.UNKNOWN:0},
 {DisclosureClass.FORBIDDEN:4,DisclosureClass.PRIVATE_ONLY:3,DisclosureClass.METADATA_ONLY:2,DisclosureClass.PUBLIC_SAFE:1},
 {RetentionClass.NONE:4,RetentionClass.EPHEMERAL:3,RetentionClass.SHORT:2,RetentionClass.STANDARD:1,RetentionClass.UNKNOWN:0},
)

def test_source_access_policy_is_versioned_and_deterministic():
    value=policy(); value.validate()
    d=decide_source_access(value,requested_disclosure=DisclosureClass.PUBLIC_SAFE,request_authenticated=False,restricted_research=True)
    assert d.allowed and d.policy_version==SOURCE_ACCESS_POLICY_VERSION

def test_restricted_and_authenticated_sources_fail_closed():
    with pytest.raises(ValueError): policy(access_class=AccessClass.UNKNOWN).validate()
    with pytest.raises(ValueError): policy(retention_class=RetentionClass.UNKNOWN).validate()
    with pytest.raises(ValueError): policy(access_class=AccessClass.AUTHENTICATED,requires_authentication=False).validate()
    auth=policy(access_class=AccessClass.AUTHENTICATED,requires_authentication=True,disclosure_class=DisclosureClass.PRIVATE_ONLY)
    assert not decide_source_access(auth,requested_disclosure=DisclosureClass.PUBLIC_SAFE,request_authenticated=False,restricted_research=True).allowed
    restricted=policy(access_class=AccessClass.RESTRICTED,disclosure_class=DisclosureClass.PRIVATE_ONLY)
    assert not decide_source_access(restricted,requested_disclosure=DisclosureClass.METADATA_ONLY,request_authenticated=True,restricted_research=False).allowed

def test_retention_and_disclosure_guards():
    with pytest.raises(ValueError): policy(disclosure_class=DisclosureClass.PUBLIC_SAFE,raw_content_allowed=True).validate()
    with pytest.raises(ValueError): policy(retention_class=RetentionClass.NONE,raw_content_allowed=True).validate()

def test_validation_edges_and_decision_invariants():
    with pytest.raises(ValueError,match="unsupported"): policy(policy_version="v0").validate()
    with pytest.raises(ValueError,match="acquisition"): policy(acquisition_method=" ").validate()
    with pytest.raises(ValueError,match="boolean"): policy(requires_authentication=1).validate()
    with pytest.raises(ValueError,match="boolean"): policy(robots_restriction=1).validate()
    with pytest.raises(ValueError,match="raw content"): policy(retention_class=RetentionClass.NONE,raw_content_allowed=True).validate()
    with pytest.raises(ValueError,match="reason"): SourceAccessDecision(False," ",RetentionClass.SHORT,DisclosureClass.PRIVATE_ONLY,True).validate()
    with pytest.raises(ValueError,match="standard retention"): SourceAccessDecision(False,"blocked",RetentionClass.STANDARD,DisclosureClass.PRIVATE_ONLY,True).validate()

def test_retention_expiry_revalidation_and_conflict_resolution():
    observed=datetime(2026,9,18,tzinfo=timezone.utc); value=policy()
    assert retention_seconds(value,TTL)==86400
    assert expires_at(observed,value,TTL).isoformat().startswith("2026-09-19")
    assert revalidation_due(observed,value,86400).isoformat().startswith("2026-09-19")
    custom=policy(revalidation_after_seconds=3600)
    assert revalidation_due(observed,custom,86400).isoformat().startswith("2026-09-18T01")
    restricted=policy(access_class=AccessClass.RESTRICTED,disclosure_class=DisclosureClass.PRIVATE_ONLY)
    assert resolve_source_policy_conflict([value,restricted],access_rank=RANKS[0],disclosure_rank=RANKS[1],retention_rank=RANKS[2]).access_class is AccessClass.RESTRICTED
    assert resolve_source_policy_conflict([value,value],access_rank=RANKS[0],disclosure_rank=RANKS[1],retention_rank=RANKS[2]) is value
    with pytest.raises(ValueError): expires_at(datetime(2026,9,18),value,TTL)
