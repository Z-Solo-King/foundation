from dataclasses import replace

import pytest

from backend.intelligence.service_limits import (
    LimitConfidence,
    RouteActivationGuard,
    ServiceLimitObservation,
    reconcile_limit,
    route_activation_allowed,
)


def observation(units=5, observed_at=100.0, confidence=LimitConfidence.VERIFIED):
    return ServiceLimitObservation("search-api", "search", observed_at, units, source="probe", observation_id="obs-1", confidence=confidence)


def test_route_activation_requires_fresh_verified_capacity():
    guard = RouteActivationGuard("search-api", "search", required_units=3, max_limit_age_seconds=10)
    assert route_activation_allowed(guard, observation(5, 100), now=105)
    assert not route_activation_allowed(guard, observation(2, 100), now=105)
    assert not route_activation_allowed(guard, observation(5, 100), now=120)
    assert not route_activation_allowed(guard, observation(5, 100, LimitConfidence.STALE), now=105)
    assert not route_activation_allowed(guard, None, now=105)
    assert not route_activation_allowed(guard, observation(5, 100), now=-1)


def test_route_activation_rejects_wrong_identity_unknown_capacity_and_bad_guard():
    guard = RouteActivationGuard("search-api", "search", required_units=1)
    assert not route_activation_allowed(guard, replace(observation(), service_id="other"), now=100)
    assert not route_activation_allowed(guard, replace(observation(), resource="browser"), now=100)
    assert not route_activation_allowed(guard, replace(observation(), available_units=None), now=100)
    with pytest.raises(ValueError): RouteActivationGuard("", "search").validate()
    with pytest.raises(ValueError): RouteActivationGuard("search-api", "search", required_units=0).validate()
    with pytest.raises(ValueError): ServiceLimitObservation("", "search", 1, 1, source="p", observation_id="o").validate()
    with pytest.raises(ValueError): replace(observation(), observed_at=-1).validate()
    with pytest.raises(ValueError): replace(observation(), reset_at=50).validate()
    with pytest.raises(ValueError): replace(observation(), confidence="verified").validate()


def test_freshness_guard_and_reconciliation():
    with pytest.raises(ValueError): observation().is_fresh(-1, 10)
    with pytest.raises(ValueError): observation().is_fresh(100, -1)
    assert reconcile_limit(None, observation()).available_units == 5
    previous = observation(5, 100)
    current = replace(previous, available_units=3, observation_id="obs-2")
    assert reconcile_limit(previous, current).confidence is LimitConfidence.VERIFIED
    same_time_conflict = replace(current, observed_at=100)
    contradictory = reconcile_limit(previous, same_time_conflict)
    assert contradictory.confidence is LimitConfidence.CONTRADICTORY
    with pytest.raises(ValueError): reconcile_limit(previous, replace(current, service_id="other"))