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


def test_source_policy_validation_edges_and_decision_invariants():
    with pytest.raises(ValueError, match="unsupported"):
        SourceAccessPolicy(policy_version="v0").validate()
    with pytest.raises(ValueError, match="acquisition"):
        SourceAccessPolicy(acquisition_method=" ").validate()
    with pytest.raises(ValueError, match="boolean"):
        SourceAccessPolicy(requires_authentication=1).validate()
    with pytest.raises(ValueError, match="boolean"):
        SourceAccessPolicy(robots_restriction=1).validate()
    with pytest.raises(ValueError, match="raw content"):
        SourceAccessPolicy(retention_class=RetentionClass.NONE, raw_content_allowed=True).validate()
    auth = SourceAccessPolicy(
        access_class=AccessClass.AUTHENTICATED,
        requires_authentication=True,
        disclosure_class=DisclosureClass.PRIVATE_ONLY,
    )
    assert decide_source_access(
        auth,
        requested_disclosure=DisclosureClass.METADATA_ONLY,
        request_authenticated=False,
    ).allowed is False
    from backend.sources.access_policy import SourceAccessDecision
    with pytest.raises(ValueError, match="reason"):
        SourceAccessDecision(False, " ", RetentionClass.SHORT, DisclosureClass.PRIVATE_ONLY, True).validate()
    with pytest.raises(ValueError, match="standard retention"):
        SourceAccessDecision(False, "blocked", RetentionClass.STANDARD, DisclosureClass.PRIVATE_ONLY, True).validate()


def test_retention_none_guard_is_reached_for_non_public_disclosure():
    with pytest.raises(ValueError, match="retention is none"):
        SourceAccessPolicy(
            retention_class=RetentionClass.NONE,
            raw_content_allowed=True,
            disclosure_class=DisclosureClass.METADATA_ONLY,
        ).validate()


def test_retention_expiry_revalidation_and_conflict_resolution_are_deterministic():
    from datetime import datetime, timezone
    from backend.sources.access_policy import expires_at, revalidation_due, resolve_source_policy_conflict, retention_seconds
    observed = datetime(2026, 9, 18, tzinfo=timezone.utc)
    policy = SourceAccessPolicy(retention_class=RetentionClass.SHORT, revalidation_required=True)
    assert retention_seconds(policy) == 86_400
    assert expires_at(observed, policy).isoformat().startswith("2026-09-19")
    assert revalidation_due(observed, policy).isoformat().startswith("2026-09-19")
    restricted = SourceAccessPolicy(access_class=AccessClass.RESTRICTED, disclosure_class=DisclosureClass.PRIVATE_ONLY)
    assert resolve_source_policy_conflict((policy, restricted)).access_class is AccessClass.RESTRICTED


def test_source_policy_expiry_rejects_naive_time_and_unknown_retention():
    from datetime import datetime
    from backend.sources.access_policy import expires_at
    with pytest.raises(ValueError, match="timezone-aware"):
        expires_at(datetime(2026, 9, 18), SourceAccessPolicy())
    with pytest.raises(ValueError, match="unknown"):
        expires_at(datetime(2026, 9, 18, tzinfo=__import__("datetime").timezone.utc), SourceAccessPolicy(retention_class=RetentionClass.UNKNOWN))
