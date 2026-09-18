"""Reporting contract for the versioned evaluation-corpus fixture.

The report explicitly separates repository-only fixture validation from approved
real-source/oracle evidence. It never promotes an unapproved corpus.
"""

from __future__ import annotations

import json
from pathlib import Path

from benchmark.evaluation_corpus import ApprovalStatus, EvaluationCase, EvaluationCorpusManifest, LeakageClass, ReplayMode


MANIFEST_PATH = Path(__file__).with_name("evaluation_corpus_fixture.json")


def load_fixture() -> EvaluationCorpusManifest:
    raw = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    cases = tuple(
        EvaluationCase(
            case_id=item["case_id"],
            corpus_id=item["corpus_id"],
            corpus_version=item["corpus_version"],
            category=item["category"],
            population=item["population"],
            source_family=item["source_family"],
            input_digest=item["input_digest"],
            expected_invariants=tuple(item["expected_invariants"]),
            oracle_ref=item.get("oracle_ref"),
            snapshot_ref=item.get("snapshot_ref"),
            replay_mode=ReplayMode(item.get("replay_mode", "deterministic")),
            leakage_class=LeakageClass(item.get("leakage_class", "clean")),
        )
        for item in raw["cases"]
    )
    manifest = EvaluationCorpusManifest(
        corpus_id=raw["corpus_id"],
        corpus_version=raw["corpus_version"],
        owner=raw["owner"],
        approval_status=ApprovalStatus(raw["approval_status"]),
        cases=cases,
        oracle_registry_version=raw["oracle_registry_version"],
        provenance_revision=raw["provenance_revision"],
        approval_receipt_ref=raw.get("approval_receipt_ref"),
    )
    manifest.validate()
    return manifest


def render_corpus_report() -> dict[str, object]:
    manifest = load_fixture()
    return {
        "schema": "evaluation-corpus-report/v1",
        "corpus_id": manifest.corpus_id,
        "corpus_version": manifest.corpus_version,
        "case_count": len(manifest.cases),
        "approval_status": manifest.approval_status.value,
        "evidence_tier": "repository_only",
        "oracle_validation_metadata": {
            "registry_version": manifest.oracle_registry_version,
            "receipt_present": manifest.approval_receipt_ref is not None,
        },
        "replay": {
            "all_cases_snapshot_bound": all(case.snapshot_ref for case in manifest.cases),
            "digest": manifest.digest(),
        },
        "promotion_allowed": False,
        "promotion_authority": "external_evaluation_promotion_authority",
    }


if __name__ == "__main__":
    print(json.dumps(render_corpus_report(), indent=2, sort_keys=True))
