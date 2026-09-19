from __future__ import annotations

import json
from pathlib import Path

from benchmark.research_artifact_validator import (
    _find_named_artifacts,
    _nightly_artifact_errors,
    _scorecard_evidence_boundary_errors,
    validate_repository,
)


ROOT = Path(__file__).resolve().parents[1]


def _copy_catalog_tree(destination: Path) -> None:
    catalog = json.loads((ROOT / "benchmark/research_artifact_catalog.json").read_text(encoding="utf-8"))
    for row in catalog["artifacts"]:
        relative = row["path"]
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def test_repository_research_artifact_contract_is_valid() -> None:
    report = validate_repository(ROOT)
    assert report["valid"] is True, report["errors"]
    assert not report["errors"]


def test_validator_rejects_project_query_without_github() -> None:
    corpus_path = ROOT / "benchmark/chatbot-query-corpus.json"
    original = json.loads(corpus_path.read_text(encoding="utf-8"))
    try:
        broken = json.loads(json.dumps(original))
        for row in broken["queries"]:
            if row.get("category") == "project_status":
                row["required_sources"] = ["reddit"]
                break
        corpus_path.write_text(json.dumps(broken), encoding="utf-8")
        report = validate_repository(ROOT)
        assert report["valid"] is False
        assert any("without github source family" in error for error in report["errors"])
    finally:
        corpus_path.write_text(json.dumps(original, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_scorecard_discovery_finds_nested_runtime_output(tmp_path) -> None:
    _copy_catalog_tree(tmp_path)
    scorecard_path = tmp_path / ".runtime" / "scorecard" / "research-scorecard.json"
    scorecard_path.parent.mkdir(parents=True, exist_ok=True)
    scorecard_path.write_text(json.dumps({"schema": "autonomous-research-scorecard/v2"}), encoding="utf-8")
    assert _find_named_artifacts(tmp_path, "research-scorecard.json") == [scorecard_path]


def test_scorecard_policy_rejects_false_field_level_correctness_claim() -> None:
    scorecard = {
        "schema": "autonomous-research-scorecard/v2",
        "structural_signals": {
            "field_level_correctness_oracle": True,
            "evidence_scope": "field_level_correctness",
        },
    }
    errors = _scorecard_evidence_boundary_errors(scorecard)
    assert any("field-level correctness" in error for error in errors)


def _write_valid_nightly_bundle(root: Path) -> None:
    artifact_dir = root / ".runtime" / "artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    run_id = "nightly-test-run"
    operations_revision = "operations-test-revision"
    statuses = []
    for lane in range(3):
        programs = [f"lane{lane}-slot{slot}" for slot in range(8)]
        status = {
            "schema": "nightly-research-lane-status/v1",
            "run_id": run_id,
            "lane": lane,
            "mode": "live",
            "state": "live_research_executed",
            "preflight": "success",
            "runner": "success",
            "validation": "success",
            "program_count": 8,
            "programs": programs,
            "operations_revision": operations_revision,
        }
        statuses.append(status)
        (artifact_dir / f"nightly-lane-{lane}-status.json").write_text(
            json.dumps(status), encoding="utf-8"
        )

    (artifact_dir / "nightly-diagnosis.json").write_text(
        json.dumps(
            {
                "schema": "nightly-research-diagnosis/v1",
                "run_id": run_id,
                "aggregate_state": "live_research_executed",
                "research_job_result": "success",
                "lanes": statuses,
                "operations_revision": operations_revision,
                "real_research_findings_allowed": True,
                "historical_dry_run_findings_are_real_research": False,
                "evidence_rule": "LLM output is candidate-only until deterministic acquisition/evidence receipt qualification.",
            }
        ),
        encoding="utf-8",
    )
    (artifact_dir / "nightly-project-improvement.json").write_text(
        json.dumps(
            {
                "schema": "project-improvement-research/v1",
                "research_mode": "project_improvement",
                "program_count": 24,
                "project_snapshot": {"revision": "foundation-test-revision"},
                "evidence_policy": {
                    "llm_findings": "candidate_only_until_acquisition_receipt"
                },
            }
        ),
        encoding="utf-8",
    )
    (artifact_dir / "nightly-baseline.json").write_text(
        json.dumps(
            {
                "schema": "project-improvement-baseline/v1",
                "available": True,
                "decision": "STABLE",
                "current_research_id": "current-research",
                "previous_research_id": "previous-research",
                "current_revision": "foundation-test-revision",
                "previous_revision": "foundation-previous-revision",
            }
        ),
        encoding="utf-8",
    )


def test_nightly_artifact_bundle_accepts_coherent_complete_run(tmp_path) -> None:
    _copy_catalog_tree(tmp_path)
    _write_valid_nightly_bundle(tmp_path)
    assert _nightly_artifact_errors(tmp_path) == []


def test_nightly_artifact_bundle_rejects_cross_run_lane_mix(tmp_path) -> None:
    _copy_catalog_tree(tmp_path)
    _write_valid_nightly_bundle(tmp_path)
    lane_one = tmp_path / ".runtime" / "artifacts" / "nightly-lane-1-status.json"
    payload = json.loads(lane_one.read_text(encoding="utf-8"))
    payload["run_id"] = "different-run"
    lane_one.write_text(json.dumps(payload), encoding="utf-8")
    errors = _nightly_artifact_errors(tmp_path)
    assert any("share one non-empty run_id" in error for error in errors)


def test_nightly_artifact_bundle_rejects_missing_lane(tmp_path) -> None:
    _copy_catalog_tree(tmp_path)
    _write_valid_nightly_bundle(tmp_path)
    (tmp_path / ".runtime" / "artifacts" / "nightly-lane-2-status.json").unlink()
    errors = _nightly_artifact_errors(tmp_path)
    assert any("missing lane status: lane 2" in error for error in errors)
