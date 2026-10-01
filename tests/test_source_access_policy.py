import pytest

from tests.policy_test_support import source_policy

from backend.sources.access_policy import (
    SOURCE_ACCESS_POLICY_VERSION,
    AccessClass,
    DisclosureClass,
    RetentionClass,
    SourceAccessPolicy,
    decide_source_access,
)


TTL = {RetentionClass.NONE: 0, RetentionClass.EPHEMERAL: 0, RetentionClass.SHORT: 86_400, RetentionClass.STANDARD: 7 * 86_400, RetentionClass.UNKNOWN: None}
RANKS = ({AccessClass.RESTRICTED: 4, AccessClass.AUTHENTICATED: 3, AccessClass.PUBLIC: 2, AccessClass.UNKNOWN: 0}, {DisclosureClass.FORBIDDEN: 4, DisclosureClass.PRIVATE_ONLY: 3, DisclosureClass.METADATA_ONLY: 2, DisclosureClass.PUBLIC_SAFE: 1}, {RetentionClass.NONE: 4, RetentionClass.EPHEMERAL: 3, RetentionClass.SHORT: 2, RetentionClass.STANDARD: 1, RetentionClass.UNKNOWN: 0})


def test_source_access_policy_is_versioned_and_deterministic():
    policy = source_policy()
    policy.validate()
    decision = decide_source_access(
        policy,
        requested_disclosure=DisclosureClass.PUBLIC_SAFE,
        request_authenticated=False,
        restricted_research=True,
    )
    assert decision.allowed is True
    assert decision.policy_version == SOURCE_ACCESS_POLICY_VERSION
    assert decision.revalidate is True


def test_restricted_and_authenticated_sources_fail_closed_for_public_disclosure():
    with pytest.raises(ValueError):
        source_policy(access_class=AccessClass.UNKNOWN).validate()
    with pytest.raises(ValueError):
        source_policy(retention_class=RetentionClass.UNKNOWN).validate()
    with pytest.raises(ValueError):
        source_policy(access_class=AccessClass.AUTHENTICATED, requires_authentication=False).validate()
    with pytest.raises(ValueError):
        source_policy(access_class=AccessClass.RESTRICTED, disclosure_class=DisclosureClass.PUBLIC_SAFE).validate()
    auth = source_policy(
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
        restricted_research=True,
    ).allowed is True


def test_retention_and_disclosure_flags_fail_closed():
    with pytest.raises(ValueError):
        source_policy(disclosure_class=DisclosureClass.PUBLIC_SAFE, raw_content_allowed=True).validate()
    with pytest.raises(ValueError):
        source_policy(retention_class=RetentionClass.NONE, raw_content_allowed=True).validate()
    robots = source_policy(robots_restriction=True)
    assert decide_source_access(
        robots,
        requested_disclosure=DisclosureClass.PUBLIC_SAFE,
        request_authenticated=False,
    ).allowed is False
    restricted = source_policy(
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
        source_policy(policy_version="v0").validate()
    with pytest.raises(ValueError, match="acquisition"):
        source_policy(acquisition_method=" ").validate()
    with pytest.raises(ValueError, match="boolean"):
        source_policy(requires_authentication=1).validate()
    with pytest.raises(ValueError, match="boolean"):
        source_policy(robots_restriction=1).validate()
    with pytest.raises(ValueError, match="raw content"):
        source_policy(retention_class=RetentionClass.NONE, raw_content_allowed=True).validate()
    auth = source_policy(
        access_class=AccessClass.AUTHENTICATED,
        requires_authentication=True,
        disclosure_class=DisclosureClass.PRIVATE_ONLY,
    )
    assert decide_source_access(
        auth,
        requested_disclosure=DisclosureClass.METADATA_ONLY,
        request_authenticated=False,
        restricted_research=True,
    ).allowed is False
    from backend.sources.access_policy import SourceAccessDecision
    with pytest.raises(ValueError, match="reason"):
        SourceAccessDecision(False, " ", RetentionClass.SHORT, DisclosureClass.PRIVATE_ONLY, True).validate()
    with pytest.raises(ValueError, match="standard retention"):
        SourceAccessDecision(False, "blocked", RetentionClass.STANDARD, DisclosureClass.PRIVATE_ONLY, True).validate()


def test_retention_none_guard_is_reached_for_non_public_disclosure():
    with pytest.raises(ValueError, match="retention is none"):
        source_policy(
            retention_class=RetentionClass.NONE,
            raw_content_allowed=True,
            disclosure_class=DisclosureClass.METADATA_ONLY,
        ).validate()


def test_retention_expiry_revalidation_and_conflict_resolution_are_deterministic():
    from datetime import datetime, timezone
    from backend.sources.access_policy import (
        expires_at,
        revalidation_due,
        resolve_source_policy_conflict,
        retention_seconds,
    )
    observed = datetime(2026, 9, 18, tzinfo=timezone.utc)
    policy = source_policy(retention_class=RetentionClass.SHORT, revalidation_required=True)
    assert retention_seconds(policy, TTL) == 86_400
    assert retention_seconds(source_policy(retention_class=RetentionClass.NONE), TTL) == 0
    assert retention_seconds(source_policy(retention_class=RetentionClass.EPHEMERAL), TTL) == 0
    assert retention_seconds(source_policy(retention_class=RetentionClass.STANDARD), TTL) == 7 * 86_400
    assert expires_at(observed, policy, TTL).isoformat().startswith("2026-09-19")
    assert revalidation_due(observed, policy, 86400).isoformat().startswith("2026-09-19")
    custom = source_policy(revalidation_after_seconds=3600)
    assert revalidation_due(observed, custom, 86400).isoformat().startswith("2026-09-18T01")
    assert revalidation_due(observed, source_policy(revalidation_required=False), 86_400) is None
    restricted = source_policy(
        access_class=AccessClass.RESTRICTED,
        disclosure_class=DisclosureClass.PRIVATE_ONLY,
    )
    assert resolve_source_policy_conflict((policy, restricted), access_rank=RANKS[0], disclosure_rank=RANKS[1], retention_rank=RANKS[2]).access_class is AccessClass.RESTRICTED
    assert resolve_source_policy_conflict((policy, policy), access_rank=RANKS[0], disclosure_rank=RANKS[1], retention_rank=RANKS[2]) is policy


def test_source_policy_expiry_rejects_naive_time_and_unknown_retention():
    from datetime import datetime, timezone
    from backend.sources.access_policy import expires_at, resolve_source_policy_conflict
    with pytest.raises(ValueError, match="revalidation_after_seconds"):
        source_policy(revalidation_after_seconds=-1).validate()
    with pytest.raises(ValueError, match="timezone-aware"):
        expires_at(datetime(2026, 9, 18), source_policy(), TTL)
    from backend.sources.access_policy import revalidation_due
    with pytest.raises(ValueError, match="timezone-aware"):
        revalidation_due(datetime(2026, 9, 18), source_policy(), 86_400)
    with pytest.raises(ValueError, match="unknown"):
        expires_at(datetime(2026, 9, 18, tzinfo=timezone.utc), source_policy(retention_class=RetentionClass.UNKNOWN), TTL)
    with pytest.raises(ValueError, match="at least one"):
        resolve_source_policy_conflict((), access_rank=RANKS[0], disclosure_rank=RANKS[1], retention_rank=RANKS[2])
