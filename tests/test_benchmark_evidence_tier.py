import json

import pytest

from benchmark import chatbot_query_benchmark, public_chatbot_runner
from benchmark.evidence_tier import EvidenceTier, parse_evidence_tier


def test_evidence_tiers_are_ordered_and_expose_claim_policy():
    deterministic = parse_evidence_tier("deterministic_contract")
    source = parse_evidence_tier("live_source_acquisition")
    live = parse_evidence_tier("live_provider")
    production = parse_evidence_tier("production")

    assert deterministic.rank < source.rank < live.rank < production.rank
    assert deterministic.provider_execution == "not_live"
    assert source.source_acquisition == "live"
    assert source.provider_execution == "not_live"
    assert live.provider_execution == "live"
    assert production.production_execution is True
    assert deterministic.allows("contract_coverage") is True
    assert source.allows("live_source_acquisition") is True
    assert source.allows("live_provider") is False
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
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["evidence"]["tier"] == EvidenceTier.DETERMINISTIC_CONTRACT.value
    assert payload["evidence"]["production_readiness_claim_allowed"] is False


def test_public_acquisition_summary_labels_live_source_evidence(tmp_path):
    targets = tmp_path / "targets.json"
    output = tmp_path / "out"
    targets.write_text('{"targets":["https://example.com/"]}', encoding="utf-8")
    assert public_chatbot_runner.run(str(targets), str(output), "evidence-tier-test", shards=1, shard=0, workers=1, duration_minutes=0) == 0
    summary = json.loads((output / "evidence-tier-test" / "summary-0.json").read_text(encoding="utf-8"))
    assert summary["evidence"]["tier"] == EvidenceTier.LIVE_SOURCE_ACQUISITION.value
    assert summary["evidence"]["claim_policy"]["live_provider"] is False
    assert summary["evidence"]["production_readiness_claim_allowed"] is False
    assert summary["measurement"]["field_level_correctness_oracle"] is False
