from __future__ import annotations

import json

from benchmark.autonomous_scorecard import build_scorecard, render_markdown
from benchmark.evidence_tier import EvidenceTier


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_scorecard_aggregates_shards_and_separates_contract_from_acquisition(tmp_path) -> None:
    write_json(
        tmp_path / "shard-0" / "benchmark-summary.json",
        {
            "schema": "autonomous-public-benchmark-summary/v10",
            "run_id": "run-1",
            "shard": 0,
            "selected_targets": 2,
            "cycles": 3,
            "total_observations": 0,
            "evidence": {"tier": EvidenceTier.LIVE_SOURCE_ACQUISITION.value},
            "status_counts": {"ok": 5, "blocked": 1, "error": 0, "empty": 0, "resource_limited": 0},
            "http_status_counts": {"200": 5, "403": 1},
            "diagnostic_counts": {"attempts-1": 6},
            "measurement": {
                "observations": 6,
                "elapsed_ms": {"min": 20, "median": 30, "p95": 50, "max": 60},
                "product_candidates_total": 10,
                "jsonld_blocks_total": 4,
                "observations_with_product_candidates": 5,
                "observations_with_jsonld": 2,
                "field_level_correctness_oracle": False,
                "evidence_scope": "transport_and_structural_signals_only",
            },
            "targets_with_failures": [
                {
                    "url": "https://blocked.example/",
                    "observations": 1,
                    "failures": 1,
                    "status_counts": {"ok": 0, "blocked": 1},
                    "http_status_counts": {"403": 1},
                    "diagnostics": {"attempts-1": 1},
                }
            ],
        },
    )
    write_json(
        tmp_path / "shard-1" / "benchmark-summary.json",
        {
            "schema": "autonomous-public-benchmark-summary/v10",
            "run_id": "run-1",
            "shard": 1,
            "selected_targets": 1,
            "cycles": 2,
            "evidence": {"tier": EvidenceTier.LIVE_SOURCE_ACQUISITION.value},
            "status_counts": {"ok": 4, "blocked": 0, "error": 1, "empty": 0, "resource_limited": 0},
            "http_status_counts": {"200": 4},
            "diagnostic_counts": {"attempts-1": 5},
            "measurement": {
                "observations": 5,
                "elapsed_ms": {"min": 10, "median": 40, "p95": 90, "max": 100},
                "product_candidates_total": 8,
                "jsonld_blocks_total": 3,
                "observations_with_product_candidates": 4,
                "observations_with_jsonld": 3,
                "field_level_correctness_oracle": False,
                "evidence_scope": "transport_and_structural_signals_only",
            },
            "targets_with_failures": [],
        },
    )
    write_json(
        tmp_path / "autonomous-chatbot-query-benchmark" / "chatbot-query-benchmark.json",
        {
            "schema": "chatbot-research-query-benchmark/v6",
            "queries": 14,
            "passed": 14,
            "failed": 0,
            "pass_rate": 1.0,
            "evidence": {"tier": EvidenceTier.DETERMINISTIC_CONTRACT.value},
            "corpus_coverage": {
                "project_query_count": 11,
                "project_query_rate": 0.7857,
                "category_count": 14,
                "source_family_count": 14,
                "temporal_modes": {"current": 13, "old_vs_new": 1},
            },
        },
    )

    scorecard = build_scorecard(tmp_path)

    assert scorecard["status"] == {
        "overall": "WARN",
        "execution": "PASS",
        "research_contract": "PASS",
        "acquisition_clean": "FAIL",
    }
    assert scorecard["evidence"]["minimum_tier"] == EvidenceTier.DETERMINISTIC_CONTRACT.value
    assert set(scorecard["evidence"]["component_tiers"]) == {
        EvidenceTier.DETERMINISTIC_CONTRACT.value,
        EvidenceTier.LIVE_SOURCE_ACQUISITION.value,
    }
    assert scorecard["evidence"]["live_provider_claim_allowed"] is False
    assert scorecard["evidence"]["integration_runtime_claim_allowed"] is False
    assert scorecard["evidence"]["production_readiness_claim_allowed"] is False
    assert scorecard["selected_targets"] == 3
    assert scorecard["total_observations"] == 11
    assert scorecard["acquisition"]["usable_observation_rate"] == 0.818182
    assert scorecard["acquisition"]["blocked_rate"] == 0.090909
    assert scorecard["acquisition"]["error_rate"] == 0.090909
    assert scorecard["research_contract"]["pass_rate"] == 1.0
    assert scorecard["research_contract"]["project_query_count"] == 11
    assert scorecard["structural_signals"]["observations_measured"] == 11
    assert scorecard["structural_signals"]["product_candidates_total"] == 18
    assert scorecard["structural_signals"]["jsonld_blocks_total"] == 7
    assert scorecard["structural_signals"]["field_level_correctness_oracle"] is False
    assert scorecard["targets_with_failures"][0]["url"] == "https://blocked.example/"

    markdown = render_markdown(scorecard)
    assert "Overall: **WARN**" in markdown
    assert "Research contract: **PASS** (14/14 passed)" in markdown
    assert "Acquisition clean: **FAIL**" in markdown
    assert "Evidence tier" in markdown
    assert "Live-provider claim allowed: False" in markdown
    assert "Structural acquisition signals" in markdown


def test_scorecard_rejects_missing_summary(tmp_path) -> None:
    try:
        build_scorecard(tmp_path)
    except ValueError as exc:
        assert "no benchmark summary" in str(exc)
    else:
        raise AssertionError("expected missing-summary failure")
