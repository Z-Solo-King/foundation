from datetime import datetime, timedelta, timezone
import hashlib

import pytest

from backend.evaluation.entailment import EntailmentStatus, verify_claim_entailment
from backend.evaluation.harness import BenchmarkCase, EvaluationCategory, EvaluationHarness, EvaluationResult
from backend.evidence_certificate import EvidenceCertificate as PublicCertificate, verify_certificate as verify_public_certificate
from backend.execution.acquisition import choose_method, reserve_acquisition
from backend.execution.adaptive import choose_strategy
from backend.execution.engine import create_run, start_research, transition_research, complete_research
from backend.execution.resources import ResourceBudget
from backend.execution.router import ProviderRouter
from backend.execution.providers import ProviderCapability, ProviderRegistry
from backend.execution.worker_boundary import WorkerResult, WorkerTask, WorkerTaskValidator
from backend.intelligence.certificates import EvidenceCertificate, create_certificate, verify_certificate
from backend.intelligence.claims import Claim
from backend.intelligence.contracts import ResearchContract, ResearchPlan
from backend.intelligence.contradiction import TypedClaim, detect_typed_contradiction, detect_contradiction
from backend.intelligence.lineage import SourceLineage, is_independent
from backend.intelligence.observations import EvidenceSpan, Observation
from backend.intelligence.sources import Source, SourcePolicy, SourceType, canonical_source_url
from backend.intelligence.verifier import ClaimStatus, EvidenceVerifier


def test_entailment_threshold_and_negation_edges():
    obs = Observation.create("o", "https://e", "product available today")
    assert verify_claim_entailment("product", obs, EvidenceSpan("o", 0, 18), supported_threshold=0.9, ambiguous_threshold=0.1).status == EntailmentStatus.SUPPORTED
    assert verify_claim_entailment("product absent", obs, EvidenceSpan("o", 0, 18)).status == EntailmentStatus.UNSUPPORTED
    assert verify_claim_entailment("", obs, EvidenceSpan("o", 0, 0)).status == EntailmentStatus.UNSUPPORTED
    assert verify_claim_entailment("product maybe", obs, EvidenceSpan("o", 0, 7), supported_threshold=0.99, ambiguous_threshold=0.1).status == EntailmentStatus.AMBIGUOUS
    assert verify_claim_entailment("unrelated", obs, EvidenceSpan("o", 0, 18), supported_threshold=0.9, ambiguous_threshold=0.8).status == EntailmentStatus.UNSUPPORTED


def test_evaluation_harness_readiness_edges():
    harness = EvaluationHarness()
    case = BenchmarkCase("edge", EvaluationCategory.RETRIEVAL, "d", "q", "a")
    harness.register_case(case)
    assert harness.bootstrap_readiness()[0] is False
    assert harness.production_readiness()[0] is False
    with pytest.raises(ValueError): harness.regression_test("missing", lambda c: EvaluationResult(c.case_id, True))
    for i in range(10):
        cid = f"prod-{i}"; harness.register_case(BenchmarkCase(cid, EvaluationCategory.SECURITY, "d", "q", "a")); harness.record_result(cid, EvaluationResult(cid, False))
    assert harness.production_readiness()[0] is False


def test_public_evidence_certificate_mismatches():
    obs = Observation.create("o", "https://example.com", "hello world")
    cert = PublicCertificate("o", obs.source_url, hashlib.sha256(obs.content.encode()).hexdigest(), 0, 5, "hello")
    assert verify_public_certificate(obs, cert) is True
    assert verify_public_certificate(obs, PublicCertificate("x", cert.source_url, cert.content_hash, 0, 5, "hello")) is False
    assert verify_public_certificate(obs, PublicCertificate(cert.observation_id, "https://other", cert.content_hash, 0, 5, "hello")) is False
    assert verify_public_certificate(obs, PublicCertificate(cert.observation_id, cert.source_url, "bad", 0, 5, "hello")) is False
    with pytest.raises(ValueError): verify_public_certificate(obs, PublicCertificate(cert.observation_id, cert.source_url, cert.content_hash, 0, 99, "hello"))
    assert verify_public_certificate(obs, PublicCertificate(cert.observation_id, cert.source_url, cert.content_hash, 0, 5, "other")) is False
    assert verify_public_certificate(obs, PublicCertificate(cert.observation_id, cert.source_url, cert.content_hash, 0, 5, "hello", False)) is False


def test_intelligence_certificate_mismatches():
    obs = Observation.create("o", "sid", "https://example.com", "hello world")
    cert = create_certificate(obs, EvidenceSpan("o", 0, 5))
    assert verify_certificate(obs, cert) is True
    assert verify_certificate(obs, EvidenceCertificate("x", cert.source_id, cert.source_url, cert.content_hash, 0, 5, "hello", True)) is False
    assert verify_certificate(obs, EvidenceCertificate(cert.observation_id, "other", cert.source_url, cert.content_hash, 0, 5, "hello", True)) is False
    assert verify_certificate(obs, EvidenceCertificate(cert.observation_id, cert.source_id, "https://other", cert.content_hash, 0, 5, "hello", True)) is False
    assert verify_certificate(obs, EvidenceCertificate(cert.observation_id, cert.source_id, cert.source_url, "bad", 0, 5, "hello", True)) is False
    assert verify_certificate(obs, EvidenceCertificate(cert.observation_id, cert.source_id, cert.source_url, cert.content_hash, 0, 99, "hello", True)) is False
    assert verify_certificate(obs, EvidenceCertificate(cert.observation_id, cert.source_id, cert.source_url, cert.content_hash, 0, 5, "other", True)) is False
    assert verify_certificate(obs, EvidenceCertificate(cert.observation_id, cert.source_id, cert.source_url, cert.content_hash, 0, 5, "hello", False)) is False


def test_acquisition_method_and_adaptive_edges(monkeypatch):
    from backend.execution import acquisition, adaptive
    source = Source("s", "https://example.com", SourceType.WEB)
    with pytest.raises(PermissionError): choose_method(source, SourcePolicy(allowed=False))
    with pytest.raises(PermissionError): reserve_acquisition(source, SourcePolicy(allowed=False), ResourceBudget(requests=1))
    monkeypatch.setattr(acquisition, "DEFAULT_METHODS", ())
    with pytest.raises(RuntimeError): choose_method(source, SourcePolicy())
    monkeypatch.setattr(adaptive, "DEFAULT_STRATEGIES", ())
    with pytest.raises(RuntimeError): choose_strategy(True)
    assert choose_strategy.__name__ == "choose_strategy"


def test_engine_invalid_transitions_and_router_execute_edges():
    from backend.execution import synthesis
    run = create_run("r", ResearchContract("q"), ResearchPlan("q", (), 1, 1))
    with pytest.raises(ValueError): transition_research(run, "bad")
    started = start_research(run)
    with pytest.raises(ValueError): start_research(started)
    assert complete_research(started, True).status == "completed"
    registry = ProviderRegistry()
    registry.register(ProviderCapability("paid", "x", free_eligible=False))
    registry.register(ProviderCapability("free", "extraction", free_eligible=True))
    router = ProviderRouter(registry, ResourceBudget(inference_calls=1))
    with pytest.raises(PermissionError): router.execute("x", lambda: "no")
    assert router.route("x", strict_zero_cost_only=False).approved is True
    assert router.route("extraction").approved is True
    assert router.execute("x", lambda: "ok", strict_zero_cost_only=False, consume_inference=False) == "ok"
    obs = type("O", (), {"observation_id":"present","source_url":"https://e"})()
    cert = type("C", (), {"observation_id":"missing"})()
    claim = Claim.create("c", "claim")
    result = type("R", (), {"supporting_evidence":(cert,)})()
    fake_run = type("Run", (), {"verified_claims":((claim,result),),"observations":(obs,)})()
    synthesized = synthesis.ResearchSynthesizer().synthesize(fake_run)
    assert synthesized is not None


def test_worker_boundary_remaining_fail_closed_paths():
    validator = WorkerTaskValidator()
    def fresh_task(): return validator.create_task("fetch", {}, "p")
    task = fresh_task(); valid_hash = hashlib.sha256(b'{"x": 1}').hexdigest()
    validator._completed_nonces.add(task.nonce); assert "replay" in validator.validate_task(task)[1]
    active_task = fresh_task(); validator._active_tasks[active_task.nonce] = "different-task"; assert "another task" in validator.validate_task(active_task)[1]
    expired_task = fresh_task(); expired_task = WorkerTask(expired_task.task_id, expired_task.nonce, expired_task.schema_version, expired_task.task_type, expired_task.input_hash, expired_task.provenance, datetime.now(timezone.utc) - timedelta(hours=26), datetime.now(timezone.utc) - timedelta(hours=25), expired_task.metadata)
    expired_result = WorkerResult(expired_task.task_id, expired_task.nonce, "success", valid_hash, {"x": 1}, 1, "worker", datetime.now(timezone.utc)); assert validator.validate_result(expired_task, expired_result, {"x": 1})[0] is False
    naive_task = fresh_task(); naive = WorkerResult(naive_task.task_id, naive_task.nonce, "success", valid_hash, {"x": 1}, 1, "worker", datetime.now()); assert validator.validate_result(naive_task, naive, {"x": 1})[0] is False
    future_task = fresh_task(); future = WorkerResult(future_task.task_id, future_task.nonce, "success", valid_hash, {"x": 1}, 1, "worker", datetime.now(timezone.utc) + timedelta(minutes=6)); assert validator.validate_result(future_task, future, {"x": 1})[0] is False
    negative_task = fresh_task(); negative = WorkerResult(negative_task.task_id, negative_task.nonce, "success", valid_hash, {"x": 1}, -1, "worker", datetime.now(timezone.utc)); assert validator.validate_result(negative_task, negative, {"x": 1})[0] is False
    missing_worker_task = fresh_task(); missing_worker = WorkerResult(missing_worker_task.task_id, missing_worker_task.nonce, "success", valid_hash, {"x": 1}, 1, "", datetime.now(timezone.utc)); assert validator.validate_result(missing_worker_task, missing_worker, {"x": 1})[0] is False
    bad_status_task = fresh_task(); bad_status = WorkerResult(bad_status_task.task_id, bad_status_task.nonce, "other", valid_hash, {"x": 1}, 1, "worker", datetime.now(timezone.utc)); assert validator.validate_result(bad_status_task, bad_status, {"x": 1})[0] is False
    huge_task = fresh_task(); huge_result = WorkerResult(huge_task.task_id, huge_task.nonce, "success", hashlib.sha256(("x"*3000000).encode()).hexdigest(), {"x":"a"*3000000}, 1, "worker", datetime.now(timezone.utc)); assert validator.validate_result(huge_task, huge_result, {"x":"a"*3000000})[0] is False


def test_typed_contradiction_invalid_numeric_and_scope_edges():
    def claim(cid, value, value_type, **kw): return TypedClaim(cid, "e", "p", value, value_type, **kw)
    assert detect_typed_contradiction(claim("a", "not-number", "numeric"), claim("b", "2", "numeric")) is None
    assert detect_typed_contradiction(claim("a", "2024-01-01", "date"), claim("b", "not-date", "date")) is None
    assert detect_typed_contradiction(claim("a", "same", "text", unit="u"), claim("b", "same", "text", unit="v")) is None
    assert detect_typed_contradiction(claim("a", "same", "text", unit="u"), claim("b", "different", "text", unit="u")) is not None
    assert detect_typed_contradiction(claim("a", "same", "enum"), claim("b", "different", "enum")) is not None
    assert detect_typed_contradiction(claim("a", 1, "quantity", unit="kg"), claim("b", 2, "quantity", unit="kg")) is not None
    assert detect_typed_contradiction(claim("a", 1, "quantity", unit="kg"), claim("b", 2, "quantity", unit=None)) is None
    assert detect_typed_contradiction(claim("a", 1, "numeric", scope=" A "), claim("b", 2, "numeric", scope="a")) is not None
    assert detect_contradiction("not available", "available") is not None
    assert detect_contradiction("available", "not available") is not None


def test_observation_constructor_and_span_edges():
    now = datetime.now(timezone.utc)
    obs = Observation("o", "sid", "https://e", "hello", now)
    defaulted = Observation("o2", "sid", "https://e", "hello", None)
    assert obs.source_id == "sid" and obs.observed_at == now and defaulted.observed_at.tzinfo is not None
    with pytest.raises(TypeError): Observation("o", "sid", "u", "c", now, "extra")
    with pytest.raises(TypeError): Observation("o", "u", "c")
    with pytest.raises(TypeError): Observation("o", "sid", "u", "c", now, source_id="x")
    with pytest.raises(TypeError): Observation.create("o", "u", "c", source_url="other")
    with pytest.raises(TypeError): Observation.create("o", "u")
    assert EvidenceSpan("o", 1, 3).text_from(obs) == "el"


def test_lineage_relationship_edges():
    verifier = EvidenceVerifier()
    with pytest.raises(ValueError): SourceLineage("s", "f", lineage_type="republished").validate()
    with pytest.raises(ValueError): SourceLineage("s", "f", lineage_type="republished", origin_fingerprint="fp").validate()
    assert verifier.check_independence(SourceLineage("s1", "f1", parent_source_id="parent"), SourceLineage("parent", "f2")) is False
    assert verifier.check_independence(SourceLineage("s1", "f1", republisher_of="r"), SourceLineage("r", "f2")) is False
    assert is_independent(SourceLineage("a","f1"), SourceLineage("b","f2")) is True
    assert is_independent(SourceLineage("a","f1"), SourceLineage("a","f2")) is False


def test_verifier_semantic_and_accessibility_matrix():
    claim = Claim.create("c", "product is available")
    obs = Observation.create("o", "sid", "https://e", "product is available")
    cert = create_certificate(obs, EvidenceSpan("o", 0, len(obs.content)))
    strict = EvidenceVerifier(semantic_strict=True)
    unsupported_obs = Observation.create("u", "uid", "https://u", "product maybe stocked")
    unsupported_cert = create_certificate(unsupported_obs, EvidenceSpan("u", 0, len(unsupported_obs.content)))
    assert strict.verify_claim(claim, (unsupported_cert,), {"u": unsupported_obs}, {}).status == ClaimStatus.UNKNOWN
    invalid_cert = EvidenceCertificate("o", obs.source_id, obs.source_url, "bad", 0, len(obs.content), obs.content, True)
    assert strict.verify_claim(claim, (invalid_cert,), {"o": obs}, {}).status == ClaimStatus.CONTRADICTED
    missing_lineage = EvidenceVerifier().verify_claim(claim, (cert,), {"o": obs}, {})
    assert missing_lineage.status == ClaimStatus.SUPPORTED and any("origin" in reason for reason in missing_lineage.reasons)
    other = Claim.create("o2", "product is unavailable")
    assert EvidenceVerifier().verify_claim(claim, (cert,), {"o": obs}, {}, (other,)).status == ClaimStatus.CONTRADICTED
    same_id = Claim.create("c", "something else")
    assert EvidenceVerifier().verify_claim(claim, (cert,), {"o": obs}, {}, (same_id,)).status == ClaimStatus.SUPPORTED
    assert canonical_source_url("https://example.com:8080/a") == "https://example.com:8080/a"


def test_verifier_inaccessible_and_stale_partial_paths():
    verifier = EvidenceVerifier(semantic_strict=True)
    inaccessible = EvidenceCertificate("missing", "sid", "https://e", "bad", 0, 1, "x", True)
    assert verifier.verify_claim(Claim.create("c", "claim"), (inaccessible,), {}, {}).status == ClaimStatus.INACCESSIBLE
    obs = Observation.create("o", "sid", "https://e", "claim true", datetime.now(timezone.utc) - timedelta(days=31))
    cert = create_certificate(obs, EvidenceSpan("o", 0, len(obs.content)))
    assert verifier.verify_claim(Claim.create("c", "claim true"), (cert,), {"o": obs}, {}).status == ClaimStatus.STALE


def test_wikipedia_runtime_import_failure(monkeypatch):
    import backend.sources.wikipedia as wikipedia
    monkeypatch.setitem(__import__("sys").modules, "workers", None)
    with pytest.raises(RuntimeError, match="Cloudflare Workers runtime"):
        wikipedia._workers_fetch()


def test_public_api_and_synthesis_edge_paths(monkeypatch):
    from backend.api.main import submit_research
    from backend.api.models import ResearchRequest
    assert submit_research(ResearchRequest("q", max_sources=0)).ok is False
    from backend.execution.synthesis import ResearchSynthesizer
    claim = Claim.create("c", "claim")
    cert = EvidenceCertificate("missing", "sid", "https://e", "hash", 0, 1, "x", True)
    result = type("R", (), {"supporting_evidence":(cert,)})()
    run = type("Run", (), {"verified_claims":((claim,result),),"observations":()})()
    assert ResearchSynthesizer().synthesize(run).evidence_chain == ()


def test_worker_default_success_run_payload(monkeypatch):
    import worker
    class Req:
        def __init__(self): self.method="GET"; self.url="https://x/api/v1/research/r1"; self.headers={"Authorization":"Bearer secret"}
        async def json(self): return None
    class Statement:
        def bind(self,*args): return self
        async def first(self): return {"run_id":"r1","status":"running"}
        async def all(self): return [{"observation_id":"o1"}]
    class DB:
        def prepare(self,sql): return Statement()
    env = type("Env", (), {"DB":DB(),"ARTIFACTS":None,"ENVIRONMENT":"production","AUTH_TOKEN":"secret","CONTROL_PLANE":None})()
    entry = worker.Default(); entry.env = env
    response = __import__("asyncio").run(entry.fetch(Req()))
    assert response
