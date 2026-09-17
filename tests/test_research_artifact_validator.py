from __future__ import annotations

import json
from pathlib import Path

from benchmark.research_artifact_validator import validate_repository


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


def test_validator_rejects_false_field_level_correctness_claim(tmp_path) -> None:
    _copy_catalog_tree(tmp_path)
    (tmp_path / ".runtime").mkdir()
    (tmp_path / ".runtime/research-scorecard.json").write_text(
        json.dumps(
            {
                "schema": "autonomous-research-scorecard/v2",
                "structural_signals": {
                    "field_level_correctness_oracle": True,
                    "evidence_scope": "field_level_correctness",
                },
            }
        ),
        encoding="utf-8",
    )
    report = validate_repository(tmp_path)
    assert report["valid"] is False
    assert any("field-level correctness" in error for error in report["errors"])
