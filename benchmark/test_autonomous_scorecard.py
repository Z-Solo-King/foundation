from __future__ import annotations

import json

from benchmark.autonomous_scorecard import build_scorecard, render_markdown


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_scorecard_aggregates_shards_and_separates_contract_from_acquisition(tmp_path) -> None:
    write_json(
        tmp_path / "shard-0" / "benchmark-summary.json",
        {
            "schema": "autonomous-public-benchmark-summary/v8",
            "run_id": "run-1",
            "shard": 0,
            "selected_targets": 2,
            "cycles": 3,
            "total_observations": 0,
            "status_counts": {"ok": 5, "blocked": 1, "error": 0, "empty": 0, "resource_limited": 0},
            "http_status_counts": {"200": 5, "403": 1},
            "diagnostic_counts": {"attempts-1": 6},
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
            "schema": "autonomous-public-benchmark-summary/v8",
            "run_id": "run-1",
            "shard": 1,
            "selected_targets": 1,
            "cycles": 2,
            "status_counts": {"ok": 4, "blocked": 0, "error": 1, "empty": 0, "resource_limited": 0},
            "http_status_counts": {"200": 4},
            "diagnostic_counts": {"attempts-1": 5},
            "targets_with_failures": [],
        },
    )
    write_json(
        tmp_path / "autonomous-chatbot-query-benchmark" / "chatbot-query-benchmark.json",
        {"schema": "chatbot-research-query-benchmark/v4", "queries": 3, "passed": 3, "failed": 0, "pass_rate": 1.0},
    )

    scorecard = build_scorecard(tmp_path)

    assert scorecard["status"] == {
        "overall": "WARN",
        "execution": "PASS",
        "research_contract": "PASS",
        "acquisition_clean": "FAIL",
    }
    assert scorecard["selected_targets"] == 3
    assert scorecard["total_observations"] == 11
    assert scorecard["acquisition"]["usable_observation_rate"] == 0.818182
    assert scorecard["acquisition"]["blocked_rate"] == 0.090909
    assert scorecard["acquisition"]["error_rate"] == 0.090909
    assert scorecard["research_contract"]["pass_rate"] == 1.0
    assert scorecard["targets_with_failures"][0]["url"] == "https://blocked.example/"
    assert "latency percentiles" in " ".join(scorecard["measurement_gaps"])

    markdown = render_markdown(scorecard)
    assert "Overall: **WARN**" in markdown
    assert "Research contract: **PASS** (3/3 passed)" in markdown
    assert "Acquisition clean: **FAIL**" in markdown


def test_scorecard_rejects_missing_summary(tmp_path) -> None:
    try:
        build_scorecard(tmp_path)
    except ValueError as exc:
        assert "no benchmark-summary.json" in str(exc)
    else:
        raise AssertionError("expected missing-summary failure")
