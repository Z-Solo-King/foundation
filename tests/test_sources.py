import pytest

from backend.intelligence.sources import Source, SourcePolicy, SourceType, evaluate_source


def test_source_policy():
    source = Source(
        source_id="source-1",
        url="https://example.com",
        source_type=SourceType.WEB,
        title="Example",
    )
    policy = SourcePolicy()

    assert evaluate_source(source, policy) is True


def test_source_policy_validation_edges_and_decision_branches():
    source = Source("s", "https://example.com", SourceType.WEB)
    with pytest.raises(ValueError, match="revision"):
        SourcePolicy(revision="").validate()
    with pytest.raises(ValueError, match="max_requests"):
        SourcePolicy(max_requests=0).validate()
    with pytest.raises(ValueError, match="retention_seconds"):
        SourcePolicy(retention_seconds=-1).validate()
    with pytest.raises(ValueError, match="revalidate_after_seconds"):
        SourcePolicy(revalidate_after_seconds=-1).validate()
    with pytest.raises(ValueError, match="access/disclosure"):
        SourcePolicy(access="bad").validate()

    assert not __import__("backend.intelligence.sources", fromlist=["evaluate_source_policy"]).evaluate_source_policy(
        source, SourcePolicy(allowed=False)
    ).allowed
    from backend.intelligence.sources import AccessState, DisclosureState, evaluate_source_policy
    assert not evaluate_source_policy(source, SourcePolicy(access=AccessState.UNKNOWN)).allowed
    assert not evaluate_source_policy(source, SourcePolicy(disclosure=DisclosureState.UNKNOWN)).allowed
    assert not evaluate_source_policy(
        source,
        SourcePolicy(access=AccessState.RESTRICTED, disclosure=DisclosureState.PUBLIC),
    ).allowed
    decision = evaluate_source_policy(
        source,
        SourcePolicy(access=AccessState.AUTHENTICATED, retain_content=False),
    )
    assert decision.allowed and "metadata-only" in decision.reason

    class UnvalidatedPolicy:
        allowed = True
        max_requests = 0
        revision = "source-policy/v1"
        access = AccessState.PUBLIC
        disclosure = DisclosureState.PUBLIC
        retain_content = False
        def validate(self):
            return None

    exhausted = evaluate_source_policy(source, UnvalidatedPolicy())
    assert exhausted.allowed is False
    assert "budget" in exhausted.reason
