import pytest

from backend.sources.access_policy import (
    SOURCE_ACCESS_POLICY_VERSION,
    AccessClass,
    DisclosureClass,
    RetentionClass,
    SourceAccessPolicy,
    decide_source_access,
)


def test_source_access_policy_is_versioned_and_deterministic():
    policy = SourceAccessPolicy()
    policy.validate()
    decision = decide_source_access(
        policy,
        requested_disclosure=DisclosureClass.PUBLIC_SAFE,
        request_authenticated=False,
    )
    assert decision.allowed is True
    assert decision.policy_version == SOURCE_ACCESS_POLICY_VERSION
    assert decision.revalidate is True


def test_restricted_and_authenticated_sources_fail_closed_for_public_disclosure():
    with pytest.raises(ValueError):
        SourceAccessPolicy(access_class=AccessClass.UNKNOWN).validate()
    with pytest.raises(ValueError):
        SourceAccessPolicy(retention_class=RetentionClass.UNKNOWN).validate()
    with pytest.raises(ValueError):
        SourceAccessPolicy(access_class=AccessClass.AUTHENTICATED, requires_authentication=False).validate()
    with pytest.raises(ValueError):
        SourceAccessPolicy(access_class=AccessClass.RESTRICTED, disclosure_class=DisclosureClass.PUBLIC_SAFE).validate()
    auth = SourceAccessPolicy(
        access_class=AccessClass.AUTHENTICATED,
        requires_authentication=True,
        disclosure_class=DisclosureClass.PRIVATE_ONLY,
    )
    assert decide_source_access(
        auth,
        requested_disclosure=DisclosureClass.PUBLIC_SAFE,
        request_authenticated=False,
    ).allowed is False
    assert decide_source_access(
        auth,
        requested_disclosure=DisclosureClass.METADATA_ONLY,
        request_authenticated=True,
    ).allowed is True


def test_retention_and_disclosure_flags_fail_closed():
    with pytest.raises(ValueError):
        SourceAccessPolicy(disclosure_class=DisclosureClass.PUBLIC_SAFE, raw_content_allowed=True).validate()
    with pytest.raises(ValueError):
        SourceAccessPolicy(retention_class=RetentionClass.NONE, raw_content_allowed=True).validate()
    robots = SourceAccessPolicy(robots_restriction=True)
    assert decide_source_access(
        robots,
        requested_disclosure=DisclosureClass.PUBLIC_SAFE,
        request_authenticated=False,
    ).allowed is False
    restricted = SourceAccessPolicy(
        access_class=AccessClass.RESTRICTED,
        disclosure_class=DisclosureClass.PRIVATE_ONLY,
    )
    assert decide_source_access(
        restricted,
        requested_disclosure=DisclosureClass.METADATA_ONLY,
        request_authenticated=True,
        restricted_research=False,
    ).allowed is False
