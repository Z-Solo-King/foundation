from backend.sources.model import Source, SourceType
from backend.sources.policy import SourcePolicy, evaluate_source


def test_source_policy():
    source = Source(
        url="https://example.com",
        source_type=SourceType.WEB,
        title="Example",
    )
    policy = SourcePolicy()

    assert evaluate_source(source, policy) is True
