from benchmark.evaluation_corpus import ApprovalStatus, LeakageClass, ReplayMode, detect_corpus_collisions
from benchmark.evaluation_corpus_report import load_fixture, render_corpus_report


def test_fixture_covers_required_corpus_classes():
    manifest = load_fixture()
    categories = {case.category for case in manifest.cases}
    required = {
        "deterministic factual",
        "multi-source research",
        "contradictory evidence",
        "stale/current temporal",
        "multilingual research",
        "citation precision",
        "source-family duplication",
        "adversarial retrieved content",
        "incomplete partial execution",
        "provider/source failure",
        "large evidence/long-running research",
    }
    assert required <= categories
    assert all(case.replay_mode is ReplayMode.SNAPSHOT for case in manifest.cases)
    assert all(case.leakage_class is LeakageClass.CLEAN for case in manifest.cases)
    assert manifest.approval_status is ApprovalStatus.UNAPPROVED


def test_fixture_has_no_duplicate_inputs_or_oracles():
    manifest = load_fixture()
    assert detect_corpus_collisions(manifest) == ()


def test_report_keeps_repository_fixture_distinct_from_approved_evidence():
    report = render_corpus_report()
    assert report["evidence_tier"] == "repository_only"
    assert report["approval_status"] == "unapproved"
    assert report["promotion_allowed"] is False
    assert report["oracle_validation_metadata"]["registry_version"] == "oracle-registry-v1"
    assert report["replay"]["all_cases_snapshot_bound"] is True
    assert report["replay"]["digest"]
