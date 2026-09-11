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
