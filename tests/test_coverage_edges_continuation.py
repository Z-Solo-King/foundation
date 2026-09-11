import asyncio
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest


def test_api_success_and_engine_lifecycle():
    from backend.api.main import submit_research
    from backend.api.models import ResearchRequest
    from backend.execution.engine import create_run, complete_research, transition_research
    from backend.intelligence.contracts import ResearchContract, ResearchPlan

    response = submit_research(ResearchRequest("q"))
    assert response.ok is True
    assert response.run_id
    assert submit_research(SimpleNamespace(strict_zero_cost_only=False, validate=lambda: None)).ok is False

    run = create_run("r", ResearchContract("q"), ResearchPlan("q", ("a",), 1, 1))
    running = transition_research(run, "running")
    assert running.status == "running"
    assert complete_research(running).status == "completed"
    assert complete_research(running, success=False).status == "failed"
    assert transition_research(running, "completed").status == "completed"
    assert transition_research(running, "failed").status == "failed"
    with pytest.raises(ValueError):
        transition_research(complete_research(running), "running")


def test_acquisition_and_strategy_no_available(monkeypatch):
    import backend.execution.acquisition as acquisition
    import backend.execution.adaptive as adaptive
    from backend.execution.acquisition import choose_method
    from backend.execution.adaptive import choose_strategy, AcquisitionStrategy
    from backend.intelligence.sources import Source, SourcePolicy, SourceType

    source = Source("s", "https://example.com", SourceType.WEB)
    monkeypatch.setattr(acquisition, "DEFAULT_METHODS", ())
    with pytest.raises(RuntimeError):
        choose_method(source, SourcePolicy())

    monkeypatch.setattr(
        adaptive,
        "DEFAULT_STRATEGIES",
        (AcquisitionStrategy("disabled", 1, enabled=False),),
    )
    with pytest.raises(RuntimeError):
        choose_strategy(False)


def test_router_remaining_gate_and_non_consuming_execute(monkeypatch):
    from backend.execution.providers import ProviderCapability, ProviderRegistry
    from backend.execution.resources import ResourceBudget
    from backend.execution.router import ProviderRouter

    registry = ProviderRegistry()
    paid = ProviderCapability("paid", "x", free_eligible=False)
    registry.register(paid)
    router = ProviderRouter(registry, ResourceBudget(inference_calls=1))
    assert router.route("x").approved is False
    assert router.route("x", strict_zero_cost_only=False).approved is True
    assert router.execute("x", lambda: "ok", consume_inference=False, strict_zero_cost_only=False) == "ok"

    monkeypatch.setattr(registry, "best", lambda capability, free_only=True: paid)
    denied = router.route("x")
    assert denied.approved is False and "not free-eligible" in denied.reason


def test_entailment_remaining_statuses():
    from backend.evaluation.entailment import EntailmentStatus, verify_claim_entailment
    from backend.intelligence.observations import EvidenceSpan, Observation

    obs = Observation.create("o", "https://e", "product is available now")
    assert verify_claim_entailment("product is available", obs, EvidenceSpan("o", 0, 24)).status == EntailmentStatus.SUPPORTED
    assert verify_claim_entailment("product available", obs, EvidenceSpan("o", 0, 24), supported_threshold=1.1).status == EntailmentStatus.AMBIGUOUS
    assert verify_claim_entailment("banana", obs, EvidenceSpan("o", 0, 24)).status == EntailmentStatus.UNSUPPORTED


def test_harness_production_success_and_observation_edges():
    from backend.evaluation.harness import EvaluationCategory, EvaluationHarness, BenchmarkCase, EvaluationResult
    from backend.intelligence.observations import Observation

    h = EvaluationHarness()
    h._promotion_threshold = 0.5
    for i in range(10):
        cid = f"retrieval-{i}"
        h.register_case(BenchmarkCase(cid, EvaluationCategory.RETRIEVAL, "d", "q", "a"))
        h.record_result(cid, EvaluationResult(cid, True))
    ok, reason = h.production_readiness()
    assert ok is True and reason == "production gate passed"
    obs = Observation.create("o", "https://e", "x")
    assert obs.observed_at.tzinfo is not None
    assert Observation("o2", "https://e", "x", datetime.now(timezone.utc)).content == "x"


def test_lineage_contradiction_and_observation_remaining_edges():
    from backend.intelligence.contradiction import TypedClaim, _as_date, _numeric, detect_contradiction, detect_typed_contradiction
    from backend.intelligence.lineage import SourceLineage

    assert _numeric("not-a-number") is None
    assert _as_date("not-a-date") is None
    assert _as_date(datetime(2024, 1, 2)).isoformat() == "2024-01-02"
    assert _as_date(date(2024, 1, 2)).isoformat() == "2024-01-02"
    assert detect_contradiction("something", "else") is None
    assert detect_contradiction("not available", "available") is not None
    assert detect_contradiction("available", "not available") is not None

    base = dict(entity="E", predicate="P", scope=None, valid_from=None, valid_until=None, unit="u", qualifier="q", version=None)
    def claim(cid, value, value_type, **changes):
        data = dict(base); data.update(changes)
        return TypedClaim(cid, data.pop("entity"), data.pop("predicate"), value, value_type, **data)

    assert detect_typed_contradiction(claim("a", "bad", "numeric"), claim("b", "other", "numeric")) is None
    assert detect_typed_contradiction(claim("a", "bad-date", "date"), claim("b", "also-bad", "date")) is None
    assert detect_typed_contradiction(claim("a", "one", "enum"), claim("b", "two", "enum")) is not None
    assert detect_typed_contradiction(claim("a", "same", "text", unit="a"), claim("b", "same", "text", unit="b")) is None
    assert detect_typed_contradiction(claim("a", "same", "text"), claim("b", "same", "text")) is None
    assert detect_typed_contradiction(claim("a", 1, "numeric", valid_until=datetime(2024, 1, 1)), claim("b", 2, "numeric", valid_from=datetime(2024, 1, 2))) is None
    assert detect_typed_contradiction(claim("a", 1, "numeric"), claim("b", 2, "other",)) is None
    with pytest.raises(ValueError):
        SourceLineage("s", "f", lineage_type="republished").validate()
    rep = SourceLineage("s", "f", lineage_type="republished", origin_fingerprint="fp", parent_source_id="p")
    rep.validate()


def test_http_host_and_wikipedia_runtime_paths(monkeypatch):
    import backend.sources.http as http
    import backend.sources.wikipedia as wikipedia

    assert http._safe_host("localhost") is False
    assert http._safe_host("1.1.1.1") is True
    assert http._safe_host("192.168.1.1") is False
    assert http._safe_host("not-an-ip.example") is True

    monkeypatch.setattr(http, "_workers_fetch", lambda: None)
    # Exercise the URL validator branches before any actual transport is attempted.
    with pytest.raises(ValueError): http.validate_url("ftp://example.com")
    with pytest.raises(ValueError): http.validate_url("https://user:pass@example.com")
    with pytest.raises(ValueError): http.validate_url("https://example.com:8443")
    with pytest.raises(ValueError): http.validate_url("http://localhost")

    monkeypatch.setattr(wikipedia, "_workers_fetch", lambda: (_ for _ in ()).throw(RuntimeError("runtime")))
    with pytest.raises(RuntimeError, match="Cloudflare Workers runtime"):
        asyncio.run(wikipedia._implementation("q", 1))


def test_worker_result_replay_and_size_guards():
    import hashlib
    import json
    from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator

    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {}, "p")
    output = {"x": 1}
    digest = hashlib.sha256(json.dumps(output, sort_keys=True, default=str).encode()).hexdigest()
    result = WorkerResult(task.task_id, task.nonce, "success", digest, output, 1, "worker", datetime.now(timezone.utc))
    assert validator.validate_result(task, result, output)[0] is True
    assert validator.validate_task(task)[0] is False

    expired = validator.create_task("fetch", {}, "p")
    expired_result = WorkerResult(expired.task_id, expired.nonce, "failure", None, None, 1, "worker", expired.expires_at + timedelta(hours=3))
    assert validator.validate_result(expired, expired_result, None)[0] is False

    future = validator.create_task("fetch", {}, "p")
    future_result = WorkerResult(future.task_id, future.nonce, "failure", None, None, 1, "worker", datetime.now(timezone.utc) + timedelta(minutes=6))
    assert validator.validate_result(future, future_result, None)[0] is False

    oversized = validator.create_task("fetch", {}, "p")
    huge = {"x": "a" * (validator.MAX_OUTPUT_SIZE_MB * 1024 * 1024 + 1)}
    huge_hash = hashlib.sha256(json.dumps(huge, sort_keys=True, default=str).encode()).hexdigest()
    huge_result = WorkerResult(oversized.task_id, oversized.nonce, "success", huge_hash, huge, 1, "worker", datetime.now(timezone.utc))
    assert validator.validate_result(oversized, huge_result, huge)[0] is False


def test_verifier_strict_and_inaccessible_paths():
    import hashlib
    from backend.intelligence.certificates import create_certificate
    from backend.intelligence.claims import Claim
    from backend.intelligence.observations import Observation, EvidenceSpan
    from backend.intelligence.lineage import SourceLineage
    from backend.intelligence.verifier import EvidenceVerifier, ClaimStatus

    obs = Observation.create("o", "sid", "https://e", "unrelated evidence")
    cert = create_certificate(obs, EvidenceSpan("o", 0, 19))
    claim = Claim.create("c", "banana")

    strict = EvidenceVerifier(semantic_strict=True)
    partial = strict.verify_claim(claim, (cert,), {"o": obs}, {"sid": SourceLineage("sid", "family")})
    assert partial.status == ClaimStatus.PARTIAL

    missing = strict.verify_claim(claim, (cert,), {}, {})
    assert missing.status == ClaimStatus.INACCESSIBLE
    assert "inaccessible" in " ".join(missing.reasons)

    contradicted = create_certificate(obs, EvidenceSpan("o", 0, 19))
    bad = contradicted.__class__(contradicted.observation_id, contradicted.source_id, contradicted.source_url, "bad", contradicted.span_start, contradicted.span_end, contradicted.span_text, True)
    bad_result = strict.verify_claim(claim, (bad,), {"o": obs}, {})
    assert bad_result.status == ClaimStatus.CONTRADICTED

    stale_obs = Observation.create("s", "sid", "https://e", "banana", datetime.now(timezone.utc) - timedelta(days=31))
    stale_cert = create_certificate(stale_obs, EvidenceSpan("s", 0, 6))
    stale_claim = Claim.create("stale", "banana")
    stale = strict.verify_claim(stale_claim, (stale_cert,), {"s": stale_obs}, {"sid": SourceLineage("sid", "family")})
    assert stale.status == ClaimStatus.STALE
