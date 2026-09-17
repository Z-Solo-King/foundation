import pytest

from benchmark.evidence_tier import EvidenceTier, parse_evidence_tier
from benchmark import chatbot_query_benchmark


def test_evidence_tiers_are_ordered_and_expose_claim_policy():
    deterministic = parse_evidence_tier("deterministic_contract")
    live = parse_evidence_tier("live_provider")
    production = parse_evidence_tier("production")

    assert deterministic.rank < live.rank < production.rank
    assert deterministic.provider_execution == "not_live"
    assert live.provider_execution == "live"
    assert production.production_execution is True
    assert deterministic.allows("contract_coverage") is True
    assert deterministic.allows("live_provider") is False
    assert production.allows("production") is True


def test_invalid_tier_is_rejected():
    with pytest.raises(ValueError, match="unsupported evidence tier"):
        parse_evidence_tier("imaginary")


def test_unknown_claim_is_rejected():
    with pytest.raises(ValueError, match="unknown benchmark claim class"):
        parse_evidence_tier(EvidenceTier.DETERMINISTIC_CONTRACT.value).allows("made_up")


def test_query_benchmark_refuses_stronger_tier_without_live_execution(tmp_path):
    corpus = tmp_path / "corpus.json"
    output = tmp_path / "benchmark.json"
    corpus.write_text(
        '{"queries":[{"id":"q1","query":"test","required_sources":[],"category":"project_status"}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="executes deterministic research-plan contracts only"):
        chatbot_query_benchmark.run(
            corpus,
            output,
            evidence_tier=EvidenceTier.LIVE_PROVIDER.value,
        )


def test_query_benchmark_serializes_deterministic_evidence_tier(tmp_path):
    corpus = tmp_path / "corpus.json"
    output = tmp_path / "benchmark.json"
    corpus.write_text(
        '{"queries":[{"id":"q1","query":"test","required_sources":[],"category":"project_status"}]}',
        encoding="utf-8",
    )
    assert chatbot_query_benchmark.run(corpus, output) == 0
    payload = __import__("json").loads(output.read_text(encoding="utf-8"))
    assert payload["evidence"]["tier"] == EvidenceTier.DETERMINISTIC_CONTRACT.value
    assert payload["evidence"]["production_readiness_claim_allowed"] is False
