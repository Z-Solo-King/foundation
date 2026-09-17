from benchmark.multi_agent.baseline import compare
from benchmark.reproducibility import make_receipt


def reproducibility(**changes):
    value = {
        "repository": "Z-Solo-King/foundation",
        "revision": "rev-1",
        "artifact_id": "artifact-1",
        "suite": "nightly-project-improvement",
        "suite_version": "v1",
        "configuration": {"profile": "standard", "workers": 6},
        "evidence_tier": "deterministic_contract",
        "corpus_id": "project-research",
        "corpus_version": "v1",
        "execution_state": "completed",
        "workflow_id": "workflow-1",
        "workflow_run_id": "1",
        "generated_at": "2026-09-17T00:00:00Z",
    }
    value.update(changes)
    return make_receipt(**value)


def summary(**changes):
    value = {
        "schema": "project-improvement-research/v1",
        "research_id": "research-1",
        "execution_state": "completed",
        "status_counts": {"completed": 24},
        "program_count": 24,
        "programs": [{"measurement": {"useful_findings": 10}, "status": "completed"}],
        "improvement_signals": [],
        "project_snapshot": {"revision": "rev-1"},
        "reproducibility": reproducibility(),
    }
    value.update(changes)
    return value


def test_missing_reproducibility_metadata_does_not_create_a_baseline():
    current = summary(reproducibility=None)
    result = compare(current, summary())
    assert result["decision"] == "NO_BASELINE"
    assert result["available"] is False
    assert "reproducibility" in result["reason"]


def test_incompatible_baseline_is_not_compared():
    current = summary()
    previous = summary(reproducibility=reproducibility(corpus_version="v2"))
    result = compare(current, previous)
    assert result["decision"] == "NO_BASELINE"
    assert result["available"] is False
    assert any("corpus_version" in item for item in result["compatibility_errors"])


def test_compatible_baseline_can_produce_a_decision():
    current = summary(research_id="current", project_snapshot={"revision": "rev-2"})
    previous = summary(research_id="previous")
    result = compare(current, previous)
    assert result["available"] is True
    assert result["decision"] == "STABLE"
    assert result["reproducibility"]["evidence_tier"] == "deterministic_contract"
