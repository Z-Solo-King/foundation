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


def test_versioned_source_policy_fails_closed_on_unknown_or_conflicting_state():
    from backend.intelligence.sources import AccessState, DisclosureState, evaluate_source_policy

    source = Source("source-2", "https://example.org", SourceType.WEB)
    unknown = evaluate_source_policy(source, SourcePolicy(access=AccessState.UNKNOWN))
    assert not unknown.allowed
    assert unknown.policy_revision == "source-policy/v1"

    conflict = evaluate_source_policy(
        source,
        SourcePolicy(access=AccessState.RESTRICTED, disclosure=DisclosureState.PUBLIC),
    )
    assert not conflict.allowed


def test_versioned_source_policy_allows_authenticated_metadata_only_access():
    from backend.intelligence.sources import AccessState, evaluate_source_policy

    source = Source("source-3", "https://private.example", SourceType.WEB)
    decision = evaluate_source_policy(
        source,
        SourcePolicy(access=AccessState.AUTHENTICATED, retain_content=False),
    )
    assert decision.allowed
    assert "metadata-only" in decision.reason


def test_source_policy_rejects_invalid_retention_and_revision():
    with pytest.raises(ValueError, match="revision"):
        SourcePolicy(revision="").validate()
    with pytest.raises(ValueError, match="retention"):
        SourcePolicy(retention_seconds=-1).validate()
