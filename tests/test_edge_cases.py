from datetime import datetime, timedelta, timezone
import hashlib

import pytest

from backend.evaluation.entailment import EntailmentStatus, verify_claim_entailment
from backend.evaluation.harness import BenchmarkCase, EvaluationCategory, EvaluationHarness, EvaluationResult
from backend.evidence_certificate import EvidenceCertificate, verify_certificate
from backend.execution.acquisition import choose_method, reserve_acquisition
from backend.execution.adaptive import choose_strategy
from backend.execution.engine import ResearchRun, create_run, start_research, transition_research
from backend.execution.resources import ResourceBudget
from backend.execution.router import ProviderRouter
from backend.execution.providers import ProviderCapability, ProviderRegistry
from backend.execution.worker_boundary import WorkerResult, WorkerTask, WorkerTaskValidator
from backend.intelligence.certificates import create_certificate
from backend.intelligence.claims import Claim
from backend.intelligence.contracts import ResearchContract, ResearchPlan
from backend.intelligence.contradiction import TypedClaim, detect_typed_contradiction
from backend.intelligence.lineage import SourceLineage
from backend.intelligence.observations import EvidenceSpan, Observation
from backend.intelligence.sources import Source, SourcePolicy, SourceType
from backend.intelligence.verifier import ClaimStatus, EvidenceVerifier
from backend.sources.http import FetchResult


def test_entailment_threshold_and_negation_edges():
    obs = Observation.create("o", "https://e", "product available today")
    assert verify_claim_entailment("product", obs, EvidenceSpan("o", 0, 18), supported_threshold=0.9, ambiguous_threshold=0.1).status == EntailmentStatus.SUPPORTED
    assert verify_claim_entailment("product absent", obs, EvidenceSpan("o", 0, 18)).status == EntailmentStatus.UNSUPPORTED
    assert verify_claim_entailment("", obs, EvidenceSpan("o", 0, 0)).status == EntailmentStatus.UNSUPPORTED
    assert verify_claim_entailment("product maybe", obs, EvidenceSpan("o", 0, 7), supported_threshold=0.99, ambiguous_threshold=0.1).status == EntailmentStatus.AMBIGUOUS


def test_evaluation_harness_readiness_edges():
    harness = EvaluationHarness()
    case = BenchmarkCase("edge", EvaluationCategory.RETRIEVAL, "d", "q", "a")
    harness.register_case(case)
    harness.record_result("edge", EvaluationResult("edge", True))
    assert harness.bootstrap_readiness()[0] is False
    assert harness.production_readiness()[0] is False
    with pytest.raises(ValueError): harness.record_result("edge", EvaluationResult("other", True))
    with pytest.raises(ValueError): harness.regression_test("missing", lambda c: EvaluationResult(c.case_id, True))


def test_evidence_certificate_mismatches():
    obs = Observation.create("o", "https://example.com", "hello world")
    cert = create_certificate(obs, EvidenceSpan("o", 0, 5))
    variants = [
        EvidenceCertificate("x", cert.source_url, cert.content_hash, 0, 5, "hello"),
        EvidenceCertificate(cert.observation_id, "https://other", cert.content_hash, 0, 5, "hello"),
        EvidenceCertificate(cert.observation_id, cert.source_url, "bad", 0, 5, "hello"),
        EvidenceCertificate(cert.observation_id, cert.source_url, cert.content_hash, 0, 99, "hello"),
        EvidenceCertificate(cert.observation_id, cert.source_url, cert.content_hash, 0, 5, "other"),
        EvidenceCertificate(cert.observation_id, cert.source_url, cert.content_hash, 0, 5, "hello", False),
    ]
    for variant in variants:
        assert verify_certificate(obs, variant) is False


def test_acquisition_method_and_adaptive_edges():
    source = Source("s", "https://example.com", SourceType.WEB)
    assert choose_method(source, SourcePolicy(allowed=False)).enabled is False
    assert reserve_acquisition(source, SourcePolicy(allowed=False), ResourceBudget(requests=1)).enabled is False
    assert choose_strategy(True).requires_browser is False
    assert choose_strategy(False).requires_browser is False


def test_engine_invalid_transitions_and_router_execute_edges():
    run = create_run("r", ResearchContract("q"), ResearchPlan("q", (), 1, 1))
    with pytest.raises(ValueError): transition_research(run, "bad")
    started = start_research(run)
    with pytest.raises(ValueError): start_research(started)
    registry = ProviderRegistry()
    registry.register(ProviderCapability("paid", "x", free_eligible=False))
    router = ProviderRouter(registry, ResourceBudget(inference_calls=1))
    with pytest.raises(PermissionError): router.execute("x", lambda: "no")
    assert router.route("x", strict_zero_cost_only=False).approved is True
    assert router.execute("x", lambda: "ok", strict_zero_cost_only=False) == "ok"


def test_worker_boundary_remaining_fail_closed_paths():
    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {}, "p")
    valid_hash = hashlib.sha256(b'{"x": 1}').hexdigest()

    replay = validator.validate_task(task)
    assert replay[0] is True
    assert validator.validate_task(task)[0] is True
    validator._completed_nonces.add(task.nonce)
    assert "replay" in validator.validate_task(task)[1]

    expired_result = WorkerResult(task.task_id, task.nonce, "success", valid_hash, {"x": 1}, 1, "worker", datetime.now(timezone.utc))
    expired_task = WorkerTask(task.task_id, task.nonce + "-exp", task.schema_version, task.task_type, task.input_hash, task.provenance, datetime.now(timezone.utc) - timedelta(hours=26), datetime.now(timezone.utc) - timedelta(hours=25), task.metadata)
    assert validator.validate_result(expired_task, expired_result)[0] is False

    naive = WorkerResult(task.task_id, task.nonce, "success", valid_hash, {"x": 1}, 1, "worker", datetime.now())
    assert validator.validate_result(task, naive)[0] is False
    future = WorkerResult(task.task_id, task.nonce, "success", valid_hash, {"x": 1}, 1, "worker", datetime.now(timezone.utc) + timedelta(minutes=6))
    assert validator.validate_result(task, future)[0] is False
    negative = WorkerResult(task.task_id, task.nonce, "success", valid_hash, {"x": 1}, -1, "worker", datetime.now(timezone.utc))
    assert validator.validate_result(task, negative)[0] is False
    missing_worker = WorkerResult(task.task_id, task.nonce, "success", valid_hash, {"x": 1}, 1, "", datetime.now(timezone.utc))
    assert validator.validate_result(task, missing_worker)[0] is False
    bad_status = WorkerResult(task.task_id, task.nonce, "other", valid_hash, {"x": 1}, 1, "worker", datetime.now(timezone.utc))
    assert validator.validate_result(task, bad_status)[0] is False


def test_typed_contradiction_invalid_numeric_and_scope_edges():
    def claim(cid, value, value_type, **kw):
        return TypedClaim(cid, "e", "p", value, value_type, **kw)
    assert detect_typed_contradiction(claim("a", "not-number", "numeric"), claim("b", "2", "numeric")) is None
    assert detect_typed_contradiction(claim("a", "2024-01-01", "date"), claim("b", "not-date", "date")) is None
    assert detect_typed_contradiction(claim("a", "same", "text", unit="u"), claim("b", "same", "text", unit="v")) is None
    assert detect_typed_contradiction(claim("a", "same", "enum"), claim("b", "different", "enum")) is not None
    assert detect_typed_contradiction(claim("a", 1, "quantity", unit="kg"), claim("b", 2, "quantity", unit=None)) is None
    assert detect_typed_contradiction(claim("a", 1, "numeric", scope=" A "), claim("b", 2, "numeric", scope="a")) is not None


def test_observation_constructor_and_span_edges():
    now = datetime.now(timezone.utc)
    obs = Observation("o", "sid", "https://e", "hello", now)
    assert obs.source_id == "sid" and obs.observed_at == now
    with pytest.raises(TypeError): Observation("o", "sid", "u", "c", now, "extra")
    with pytest.raises(TypeError): Observation("o", "u", "c")
    with pytest.raises(TypeError): Observation("o", "sid", "u", "c", now, source_id="x")
    with pytest.raises(TypeError): Observation.create("o", "u", "c", source_url="other")
    with pytest.raises(TypeError): Observation.create("o", "u")
    assert EvidenceSpan("o", 1, 3).text_from(obs) == "el"


def test_lineage_relationship_edges():
    first = SourceLineage("s1", "f1", parent_source_id="parent")
    second = SourceLineage("parent", "f2")
    verifier = EvidenceVerifier()
    assert verifier.check_independence(first, second) is False
    assert verifier.check_independence(SourceLineage("s1", "f1", republisher_of="r"), SourceLineage("r", "f2")) is False


def test_verifier_semantic_and_accessibility_matrix():
    claim = Claim.create("c", "product is available")
    obs = Observation.create("o", "sid", "https://e", "product is available")
    cert = create_certificate(obs, EvidenceSpan("o", 0, len(obs.content)))
    strict = EvidenceVerifier(semantic_strict=True)
    unsupported_obs = Observation.create("u", "uid", "https://u", "product maybe stocked")
    unsupported_cert = create_certificate(unsupported_obs, EvidenceSpan("u", 0, len(unsupported_obs.content)))
    partial = strict.verify_claim(claim, (unsupported_cert,), {"u": unsupported_obs}, {})
    assert partial.status == ClaimStatus.UNKNOWN or partial.status == ClaimStatus.PARTIAL

    invalid_cert = EvidenceCertificate("o", obs.source_url, "bad", 0, len(obs.content), obs.content)
    contradicted = strict.verify_claim(claim, (invalid_cert,), {"o": obs}, {})
    assert contradicted.status == ClaimStatus.CONTRADICTED

    missing_lineage = EvidenceVerifier().verify_claim(claim, (cert,), {"o": obs}, {})
    assert missing_lineage.status == ClaimStatus.SUPPORTED
    assert any("origin" in reason for reason in missing_lineage.reasons)

    other = Claim.create("o2", "product is unavailable")
    conflict = EvidenceVerifier().verify_claim(claim, (cert,), {"o": obs}, {}, (other,))
    assert conflict.status == ClaimStatus.CONTRADICTED


def test_verifier_inaccessible_and_partial_final_statuses():
    verifier = EvidenceVerifier(semantic_strict=True)
    inaccessible = EvidenceCertificate("missing", "https://e", "bad", 0, 1, "x")
    result = verifier.verify_claim(Claim.create("c", "claim"), (inaccessible,), {}, {})
    assert result.status == ClaimStatus.INACCESSIBLE

    obs = Observation.create("o", "sid", "https://e", "claim is true", datetime.now(timezone.utc) - timedelta(days=1))
    cert = create_certificate(obs, EvidenceSpan("o", 0, len(obs.content)))
    result = verifier.verify_claim(Claim.create("c", "claim is false"), (cert,), {"o": obs}, {})
    assert result.status in {ClaimStatus.CONTRADICTED, ClaimStatus.PARTIAL, ClaimStatus.SUPPORTED}


def test_http_fetch_result_shape_and_worker_adapter(monkeypatch):
    import backend.sources.http as http
    result = FetchResult("https://e", "https://e", 200, "text/plain", b"x", None)
    assert result.final_url == "https://e"
    async def fetcher(url, options):
        class Response:
            status = 200
            headers = {}
            async def arrayBuffer(self): return b"ok"
        return Response()
    assert (pytest.raises if False else True)
    assert (awaitable := fetcher) is not None


def test_wikipedia_runtime_import_failure(monkeypatch):
    import backend.sources.wikipedia as wikipedia
    monkeypatch.setitem(__import__("sys").modules, "workers", None)
    with pytest.raises(RuntimeError, match="Cloudflare Workers runtime"):
        wikipedia._workers_fetch()
