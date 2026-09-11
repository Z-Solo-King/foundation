from backend.intelligence.observations import EvidenceSpan, Observation


def test_observation_and_evidence_span():
    observation = Observation.create(
        observation_id="obs-001",
        source_url="https://example.com",
        content="The system stores evidence.",
    )

    span = EvidenceSpan(
        observation_id="obs-001",
        start=18,
        end=26,
    )

    assert span.text_from(observation) == "evidence"
