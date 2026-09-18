from datetime import datetime, timedelta, timezone
from decimal import Decimal
import asyncio

import pytest


def test_artifact_execution_all_states_and_serialization():
    from backend.artifacts.contract import (
        ArtifactExecutionState,
        ArtifactKind,
        ArtifactSafety,
        ArtifactValidation,
        authorize_artifact_execution,
        create_artifact,
    )

    with pytest.raises(ValueError, match="target_scope"):
        authorize_artifact_execution(create_artifact(
            b"x", kind=ArtifactKind.TEXT, media_type="text/plain",
            parser_version="p", owner_scope="o", validation=ArtifactValidation.VALID
        ), target_scope=" ")
    blocked = create_artifact(
        b"x", kind=ArtifactKind.TEXT, media_type="text/plain",
        parser_version="p", owner_scope="o", safety=ArtifactSafety.BLOCKED,
        validation=ArtifactValidation.VALID,
    )
    decision = authorize_artifact_execution(blocked, target_scope="o")
    assert decision.state is ArtifactExecutionState.BLOCKED
    assert decision.to_dict()["schema_version"] == "artifact-execution/v1"

    malformed = create_artifact(
        b"x", kind=ArtifactKind.TEXT, media_type="text/plain",
        parser_version="p", owner_scope="o", validation=ArtifactValidation.UNSUPPORTED,
    )
    assert authorize_artifact_execution(malformed, target_scope="o").state is ArtifactExecutionState.BLOCKED

    private = create_artifact(
        b"x", kind=ArtifactKind.TEXT, media_type="text/plain",
        parser_version="p", owner_scope="owner", safety=ArtifactSafety.PRIVATE,
        validation=ArtifactValidation.VALID,
    )
    assert authorize_artifact_execution(private, target_scope="other").state is ArtifactExecutionState.REQUIRES_AUTHORIZATION
    assert authorize_artifact_execution(private, target_scope="other", explicit_authorization=True).state is ArtifactExecutionState.AUTHORIZED


def test_evaluation_corpus_contract_rejects_invalid_cases_and_manifests():
    from backend.evaluation_corpus import CORPUS_SCHEMA, CorpusManifest, EvaluationCase

    base = dict(
        case_id="c", case_class="facts", population="p",
        expected_invariants=("x",), oracle_provenance="o",
    )
    for field in ("case_id", "case_class", "population", "oracle_provenance"):
        bad = dict(base, **{field: ""})
        with pytest.raises(ValueError, match=field):
            EvaluationCase(**bad).validate()
    with pytest.raises(ValueError, match="expected_invariants"):
        EvaluationCase(**dict(base, expected_invariants=())).validate()
    with pytest.raises(ValueError, match="replay_mode"):
        EvaluationCase(**dict(base, replay_mode="other")).validate()

    case = EvaluationCase(**base)
    assert len(case.fingerprint) == 64
    with pytest.raises(ValueError, match="unsupported corpus schema"):
        CorpusManifest("wrong", (case,)).validate()
    with pytest.raises(ValueError, match="at least one"):
        CorpusManifest(CORPUS_SCHEMA, ()).validate()
    with pytest.raises(ValueError, match="leakage_check_version"):
        CorpusManifest(CORPUS_SCHEMA, (case,), leakage_check_version=" ").validate()

    duplicate_fp_case = EvaluationCase(**dict(base, case_id="d"))
    duplicate_fp_manifest = CorpusManifest(CORPUS_SCHEMA, (case, duplicate_fp_case))
    with pytest.raises(ValueError, match="duplicate case fingerprint"):
        duplicate_fp_manifest.validate()


def test_measurement_comparability_validation_and_all_terminal_states():
    from backend.intelligence.comparability import (
        ComparabilityResult,
        ComparabilityState,
        Measurement,
        MeasurementContext,
        classify_comparability,
        normalize_measurement,
    )

    with pytest.raises(ValueError, match="entity"):
        MeasurementContext("", provenance_id="p").validate()
    with pytest.raises(ValueError, match="sample_size"):
        MeasurementContext("e", provenance_id="p", sample_size=0).validate()
    with pytest.raises(ValueError, match="replication_count"):
        MeasurementContext("e", provenance_id="p", replication_count=0).validate()
    with pytest.raises(ValueError, match="uncertainty_high"):
        MeasurementContext(
            "e", provenance_id="p",
            uncertainty_low=Decimal("2"), uncertainty_high=Decimal("1")
        ).validate()
    with pytest.raises(ValueError, match="schema"):
        ComparabilityResult(ComparabilityState.UNKNOWN, (), schema_version="wrong").validate()
    assert normalize_measurement(Decimal("1"), None) is None
    assert normalize_measurement(Decimal("1"), "not-a-unit") is None

    a = Measurement(Decimal("1"), MeasurementContext("cpu", provenance_id="a", unit="s"))
    b = Measurement(Decimal("2"), MeasurementContext("gpu", provenance_id="b", unit="s"))
    assert classify_comparability(a, b).state is ComparabilityState.UNCOMPARABLE

    c = Measurement(Decimal("1"), MeasurementContext("cpu", provenance_id="c", unit="s", variant="v1"))
    d = Measurement(Decimal("1"), MeasurementContext("cpu", provenance_id="d", unit="s", variant="v2"))
    assert classify_comparability(c, d).state is ComparabilityState.UNCOMPARABLE

    e = Measurement(Decimal("1"), MeasurementContext("cpu", provenance_id="e", unit="s"))
    f = Measurement(Decimal("1"), MeasurementContext("cpu", provenance_id="f", unit="g"))
    assert classify_comparability(e, f).state is ComparabilityState.UNCOMPARABLE

    g = Measurement(Decimal("1"), MeasurementContext("cpu", provenance_id="g", unit=None))
    h = Measurement(Decimal("1"), MeasurementContext("cpu", provenance_id="h", unit=None))
    assert classify_comparability(g, h).state is ComparabilityState.UNKNOWN


def test_freshness_validation_edge_cases():
    from backend.intelligence.freshness import (
        EvidenceTime,
        FreshnessRequirement,
        FreshnessState,
        TimestampQuality,
        classify_freshness,
    )
    now = datetime(2026, 9, 18, tzinfo=timezone.utc)

    with pytest.raises(ValueError, match="unsupported freshness policy"):
        FreshnessRequirement(policy_version="wrong").validate()
    with pytest.raises(ValueError, match="as_of"):
        FreshnessRequirement(as_of=datetime(2026, 9, 18)).validate()

    with pytest.raises(ValueError, match="observed_at"):
        EvidenceTime(observed_at=datetime(2026, 9, 18))
    with pytest.raises(ValueError, match="effective_to"):
        EvidenceTime(
            effective_from=now,
            effective_to=now - timedelta(minutes=1),
        )
    with pytest.raises(ValueError, match="missing timestamp quality"):
        EvidenceTime(
            published_at=now,
            timestamp_quality=TimestampQuality.MISSING,
        )
    with pytest.raises(ValueError, match="revision_id"):
        EvidenceTime(revision_id=" ")

    future = EvidenceTime(published_at=now + timedelta(hours=1))
    assert classify_freshness(
        future, FreshnessRequirement(allow_future=True, max_age=timedelta(hours=2)), now=now
    ) is FreshnessState.FRESH

    historical = EvidenceTime(published_at=now + timedelta(hours=1))
    assert classify_freshness(
        historical, FreshnessRequirement(historical=True), now=now
    ) is FreshnessState.FRESH

    unbounded = EvidenceTime(published_at=now - timedelta(days=5))
    assert classify_freshness(
        unbounded, FreshnessRequirement(max_age=None), now=now
    ) is FreshnessState.FRESH


def test_language_contract_validation_edges():
    from backend.intelligence.language import (
        ClaimLanguageAlignment,
        LanguageNormalization,
        LanguageSpan,
        TranslationArtifact,
        build_normalization,
        normalize_language_tag,
        normalize_text,
    )

    with pytest.raises(ValueError, match="language tag"):
        normalize_language_tag("!")
    with pytest.raises(TypeError):
        normalize_text(123)

    with pytest.raises(ValueError, match="span_id"):
        LanguageSpan("", "en", 500, "a", "a" * 64).validate()
    with pytest.raises(ValueError, match="confidence"):
        LanguageSpan("s", "en", 1001, "a", "a" * 64).validate()
    with pytest.raises(ValueError, match="SHA-256"):
        LanguageSpan("s", "en", 500, "a", "bad").validate()

    good = TranslationArtifact(
        translation_id="t",
        source_span_ids=("s",),
        source_language="en",
        target_language="hi",
        method="m",
        version="v",
        derived_fingerprint="a" * 64,
        preserves_qualifiers=True,
        preserves_negation=True,
        preserves_units=True,
    )
    with pytest.raises(ValueError, match="method"):
        TranslationArtifact(
            translation_id="t", source_span_ids=("s",), source_language="en", target_language="hi",
            method="", version="v", derived_fingerprint="a" * 64,
            preserves_qualifiers=True, preserves_negation=True, preserves_units=True,
        ).validate()
    with pytest.raises(ValueError, match="cross language"):
        TranslationArtifact(
            translation_id="t", source_span_ids=("s",), source_language="en", target_language="en",
            method="m", version="v", derived_fingerprint="a" * 64,
            preserves_qualifiers=True, preserves_negation=True, preserves_units=True,
        ).validate()
    with pytest.raises(ValueError, match="derived"):
        TranslationArtifact(
            translation_id="t", source_span_ids=("s",), source_language="en", target_language="hi",
            method="m", version="v", derived_fingerprint="a" * 64,
            preserves_qualifiers=True, preserves_negation=True, preserves_units=True,
            translation_provenance="source",
        ).validate()

    with pytest.raises(ValueError, match="alignment status"):
        ClaimLanguageAlignment("a","s","t","tr","en","hi","bad",True).validate()
    with pytest.raises(ValueError, match="source_claim"):
        ClaimLanguageAlignment("a","","t","tr","en","hi","unknown",True).validate()

    with pytest.raises(ValueError, match="source_span_ids"):
        LanguageNormalization((), "en", "x", "m", "v", "a" * 64).validate()
    with pytest.raises(ValueError, match="normalized_text"):
        LanguageNormalization(("s",), "en", " ", "m", "v", "a" * 64).validate()
    with pytest.raises(ValueError, match="derived metadata"):
        LanguageNormalization(("s",), "en", "x", "m", "v", "a" * 64, derived=False).validate()

    result = build_normalization(" x ", source_span_ids=("s",), source_language="en")
    assert result.normalized_text == "x"
    assert good.derived_fingerprint == "a" * 64


def test_quality_scorecard_validation_edges():
    from backend.quality_scorecard import QualityMeasurement, QualityScorecard, build_scorecard

    with pytest.raises(ValueError, match="dimension"):
        QualityMeasurement("bogus", 1, "w", "p", "e").validate()
    with pytest.raises(ValueError, match="unavailable"):
        QualityMeasurement("correctness", 1, "w", "p", "e", available=False).validate()
    with pytest.raises(ValueError, match="missing available"):
        QualityMeasurement("correctness", None, "w", "p", "e").validate()
    with pytest.raises(ValueError, match="baseline"):
        QualityMeasurement("correctness", 1, "w", "p", "e", baseline=-1).validate()

    with pytest.raises(ValueError, match="schema"):
        QualityScorecard((), schema_version="wrong").validate()

    scorecard = build_scorecard((
        QualityMeasurement("correctness", 1, "w", "p", "e", critical=True),
        QualityMeasurement("latency", None, "w", "p", "e", critical=True, available=False, reason="unknown"),
    ))
    assert scorecard.critical_missing_dimensions == ("latency",)
    with pytest.raises(ValueError, match="SHA-256"):
        scorecard.receipt_metadata(corpus_fingerprint="bad")


def test_typed_contradiction_remaining_edges():
    from backend.intelligence.contradiction import TypedClaim, _numeric_conflict, bounded_typed_candidate_pairs

    a = TypedClaim("a","e","p",1,"numeric",unit="kg",tolerance=Decimal("-1"))
    b = TypedClaim("b","e","p",2,"numeric",unit="kg")
    with pytest.raises(ValueError, match="tolerance"):
        _numeric_conflict(a,b)

    v1 = TypedClaim("a","e","p",1,"numeric",unit="kg",version="v1")
    v2 = TypedClaim("b","e","p",1,"numeric",unit="kg",version="v2")
    assert bounded_typed_candidate_pairs([v1,v2]) == ()


@pytest.mark.asyncio
async def test_worker_observation_helper_coverage():
    from backend.worker_research import _load_observations, _public_run

    class Bound:
        def __init__(self, value):
            self.value = value
        def bind(self, *args):
            return self
        async def all(self):
            class Result:
                results = [{"observation_id": "1"}]
            return Result()

    class DB:
        def prepare(self, query):
            return Bound(query)

    class Env:
        DB = DB()

    rows = await _load_observations(Env(), "run", 5)
    assert rows == [{"observation_id": "1"}]
    assert _public_run({"status": "done"}, "run")["run_id"] == "run"
