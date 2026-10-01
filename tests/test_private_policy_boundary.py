from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from backend.admission import AdmissionPolicy, AdmissionRoute
from backend.intelligence.planning import create_plan
from backend.intelligence.contracts import ResearchContract
from backend.sources.access_policy import (
    AccessClass,
    DisclosureClass,
    RetentionClass,
    SourceAccessPolicy,
    SourceAccessDecision,
    expires_at,
    revalidation_due,
    retention_seconds,
    resolve_source_policy_conflict,
)
from tests.policy_test_support import admission_policy, source_policy, private_policy_envelope


def _planning_policy(**overrides):
    value = {
        "base_source_families": ["synthetic_web"],
        "category_required_source_families": {"synthetic": ["source_a"]},
        "keyword_groups": {"source_b": ["token-b"]},
        "temporal_terms": ["latest"],
        "quick_stages": ["define_question", "discover_sources", "collect_observations", "verify_evidence", "synthesize_answer"],
        "standard_stages": ["define_question", "assess_constraints", "discover_sources", "collect_observations", "map_evidence", "verify_evidence", "check_independence", "synthesize_answer"],
    }
    value.update(overrides)
    return value


def test_admission_policy_envelope_rejects_missing_fields():
    with pytest.raises(ValueError, match="invalid private admission policy envelope"):
        AdmissionPolicy.from_mapping({})


def test_admission_policy_rejects_empty_protected_routes():
    policy = admission_policy(protected_routes=())
    with pytest.raises(ValueError, match="protected_routes"):
        policy.validate()


def test_planning_policy_handles_non_mapping_category_and_keyword_values():
    contract = ResearchContract(question="token-b latest")
    policy = _planning_policy(category_required_source_families=[], keyword_groups=[])
    plan = create_plan(contract, planning_policy=policy)
    assert plan.metadata["required_source_families"] == "synthetic_web"


def test_planning_policy_handles_mapping_values_with_wrong_sequence_types():
    contract = ResearchContract(question="latest")
    policy = _planning_policy(
        category_required_source_families={"synthetic": "not-a-sequence"},
        keyword_groups={"source_a": "not-a-sequence"},
    )
    plan = create_plan(contract, planning_policy=policy)
    assert plan.metadata["temporal_reconciliation"] == "true"


def test_source_access_validation_fail_closed_edges():
    with pytest.raises(ValueError, match="unsupported"):
        source_policy(policy_version="v0").validate()
    with pytest.raises(ValueError, match="acquisition"):
        source_policy(acquisition_method=" ").validate()
    with pytest.raises(ValueError, match="boolean"):
        source_policy(requires_authentication=1).validate()
    with pytest.raises(ValueError, match="boolean"):
        source_policy(robots_restriction=1).validate()
    with pytest.raises(ValueError, match="unknown"):
        source_policy(access_class=AccessClass.UNKNOWN).validate()
    with pytest.raises(ValueError, match="unknown"):
        source_policy(retention_class=RetentionClass.UNKNOWN).validate()
    with pytest.raises(ValueError, match="authenticated"):
        source_policy(access_class=AccessClass.AUTHENTICATED, requires_authentication=False).validate()
    with pytest.raises(ValueError, match="public-safe"):
        source_policy(access_class=AccessClass.RESTRICTED, disclosure_class=DisclosureClass.PUBLIC_SAFE).validate()
    with pytest.raises(ValueError, match="raw content"):
        source_policy(disclosure_class=DisclosureClass.PUBLIC_SAFE, raw_content_allowed=True).validate()
    with pytest.raises(ValueError, match="retention is none"):
        source_policy(retention_class=RetentionClass.NONE, raw_content_allowed=True, disclosure_class=DisclosureClass.METADATA_ONLY).validate()


def test_source_access_error_and_policy_resolution_branches():
    policy = source_policy()
    with pytest.raises(ValueError, match="reason"):
        SourceAccessDecision(False, " ", RetentionClass.SHORT, DisclosureClass.PRIVATE_ONLY, True).validate()
    with pytest.raises(ValueError, match="standard retention"):
        SourceAccessDecision(False, "blocked", RetentionClass.STANDARD, DisclosureClass.PRIVATE_ONLY, True).validate()
    with pytest.raises(ValueError, match="retention policy"):
        retention_seconds(policy, {})
    observed = datetime(2026, 9, 18, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="timezone-aware"):
        expires_at(observed.replace(tzinfo=None), policy, {RetentionClass.SHORT: 86400})
    assert expires_at(observed, policy, {RetentionClass.SHORT: None}) is None
    with pytest.raises(ValueError, match="timezone-aware"):
        revalidation_due(observed.replace(tzinfo=None), policy, 86400)
    with pytest.raises(ValueError, match="unavailable"):
        revalidation_due(observed, source_policy(revalidation_after_seconds=None), None)
    with pytest.raises(ValueError, match="at least one"):
        resolve_source_policy_conflict(
            (),
            access_rank={},
            disclosure_rank={},
            retention_rank={},
        )


@pytest.mark.asyncio
async def test_private_policy_envelope_requires_operations_binding():
    import worker

    with pytest.raises(RuntimeError, match="unavailable"):
        await worker._private_policy_envelope(SimpleNamespace(), SimpleNamespace(headers={}))


@pytest.mark.asyncio
async def test_private_policy_envelope_accepts_valid_authenticated_envelope():
    import worker

    class Ops:
        async def fetch(self, request):
            class Response:
                status = 200

                async def json(self):
                    return private_policy_envelope()

            return Response()

    request = SimpleNamespace(headers={"Authorization": "Bearer synthetic"})
    body = await worker._private_policy_envelope(SimpleNamespace(OPERATIONS=Ops()), request)
    assert body["schema"] == "protected-policy-envelope/v1"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body",
    [
        {"schema": "wrong", "policy_digest": "synthetic"},
        {"schema": "protected-policy-envelope/v1", "policy_digest": ""},
    ],
)
async def test_private_policy_envelope_rejects_invalid_payloads(body):
    import worker

    class Ops:
        async def fetch(self, request):
            class Response:
                status = 200

                async def json(self):
                    return body

            return Response()

    with pytest.raises(RuntimeError):
        await worker._private_policy_envelope(SimpleNamespace(OPERATIONS=Ops()), SimpleNamespace(headers={}))


@pytest.mark.asyncio
async def test_private_policy_envelope_rejects_non_200_response():
    import worker

    class Ops:
        async def fetch(self, request):
            class Response:
                status = 503

                async def json(self):
                    return {"schema": "protected-policy-envelope/v1", "policy_digest": "synthetic"}

            return Response()

    with pytest.raises(RuntimeError, match="invalid"):
        await worker._private_policy_envelope(SimpleNamespace(OPERATIONS=Ops()), SimpleNamespace(headers={}))


@pytest.mark.asyncio
async def test_public_admit_fails_closed_when_private_policy_lookup_fails(monkeypatch):
    import worker

    async def broken(*args, **kwargs):
        raise RuntimeError("synthetic outage")

    monkeypatch.setattr(worker, "_private_policy_envelope", broken)
    env = SimpleNamespace(DB=object(), ENVIRONMENT="production")
    decision, lease = await worker._public_admit(env, AdmissionRoute.RESEARCH, "subject", "event", SimpleNamespace(headers={}))
    assert not decision.allowed
    assert decision.outcome.value == "authority_unavailable"
    assert lease is None


@pytest.mark.asyncio
async def test_public_admit_fails_closed_on_missing_policy_payload():
    import worker

    env = SimpleNamespace(DB=object(), ENVIRONMENT="production")
    decision, lease = await worker._public_admit(
        env,
        AdmissionRoute.RESEARCH,
        "subject",
        "event",
        SimpleNamespace(headers={}),
        policy_envelope={"schema": "protected-policy-envelope/v1", "policy_digest": "synthetic"},
    )
    assert not decision.allowed
    assert decision.outcome.value == "authority_unavailable"
    assert lease is None


@pytest.mark.asyncio
async def test_public_admit_fails_closed_on_malformed_admission_policy():
    import worker

    env = SimpleNamespace(DB=object(), ENVIRONMENT="production")
    decision, lease = await worker._public_admit(
        env,
        AdmissionRoute.RESEARCH,
        "subject",
        "event",
        SimpleNamespace(headers={}),
        policy_envelope={"admission": {"bad": True}, "schema": "protected-policy-envelope/v1", "policy_digest": "synthetic"},
    )
    assert not decision.allowed
    assert decision.outcome.value == "authority_unavailable"
    assert lease is None


def test_source_policy_short_circuit_branches_are_both_exercised():
    # Cover the second operand of compound validation guards.
    with pytest.raises(ValueError, match="source access flags"):
        source_policy(robots_restriction=1).validate()
    with pytest.raises(ValueError, match="unknown"):
        source_policy(retention_class=RetentionClass.UNKNOWN).validate()
    with pytest.raises(ValueError, match="authenticated"):
        source_policy(access_class=AccessClass.AUTHENTICATED, requires_authentication=False).validate()
    with pytest.raises(ValueError, match="public-safe"):
        source_policy(access_class=AccessClass.AUTHENTICATED, requires_authentication=True, disclosure_class=DisclosureClass.PUBLIC_SAFE).validate()

    # Exercise the false branch of the raw-content guard and the second operand
    # of the retention guard without relying on production values.
    public_with_raw_forbidden = source_policy(disclosure_class=DisclosureClass.METADATA_ONLY, raw_content_allowed=False)
    public_with_raw_forbidden.validate()
    with pytest.raises(ValueError, match="retention is none"):
        source_policy(
            disclosure_class=DisclosureClass.METADATA_ONLY,
            retention_class=RetentionClass.NONE,
            raw_content_allowed=True,
        ).validate()

    # A non-empty override still leaves the validation branch false.
    source_policy(revalidation_after_seconds=1).validate()

    # The requested default is the second operand that can reject when the
    # policy-specific override is absent.
    with pytest.raises(ValueError, match="unavailable"):
        revalidation_due(datetime(2026, 9, 18, tzinfo=timezone.utc), source_policy(), -1)

    assert resolve_source_policy_conflict(
        (source_policy(),),
        access_rank={AccessClass.PUBLIC: 1},
        disclosure_rank={DisclosureClass.PUBLIC_SAFE: 1},
        retention_rank={RetentionClass.SHORT: 1},
    ) is not None
