import asyncio
import sys
from datetime import datetime, timedelta, timezone

import pytest


def test_entailment_adjudication_rejects_ambiguous():
    from backend.evaluation.entailment import EntailmentResult, EntailmentStatus, adjudicate_ambiguous
    result = EntailmentResult(EntailmentStatus.AMBIGUOUS, 0.7, "ambiguous")
    rejected = adjudicate_ambiguous(result, False)
    assert rejected.status == EntailmentStatus.UNSUPPORTED
    assert adjudicate_ambiguous(EntailmentResult(EntailmentStatus.SUPPORTED, 1.0, "ok"), False).status == EntailmentStatus.SUPPORTED


def test_evaluation_harness_production_failure_and_success():
    from backend.evaluation.harness import BenchmarkCase, EvaluationCategory, EvaluationHarness, EvaluationResult
    harness = EvaluationHarness()
    for i in range(150):
        harness.register_case(BenchmarkCase(f"case-{i}", EvaluationCategory.RETRIEVAL, "d", "q", "a"))
    ready, reason = harness.production_readiness()
    assert ready is False and "only 0 cases" in reason

    balanced = EvaluationHarness()
    categories = list(EvaluationCategory)
    for i in range(150):
        cat = categories[i % len(categories)]
        balanced.register_case(BenchmarkCase(f"case-{i}", cat, "d", "q", "a"))
        balanced.record_result(f"case-{i}", EvaluationResult(f"case-{i}", True))
    ready, reason = balanced.production_readiness()
    assert ready is True and reason == "production gate passed"

    failing = EvaluationHarness()
    for i in range(150):
        cat = categories[i % len(categories)]
        failing.register_case(BenchmarkCase(f"case-{i}", cat, "d", "q", "a"))
        failing.record_result(f"case-{i}", EvaluationResult(f"case-{i}", i != 0))
    ready, reason = failing.production_readiness()
    assert ready is False and "pass rate" in reason


def test_acquisition_no_enabled_method(monkeypatch):
    import backend.execution.acquisition as acquisition
    from backend.intelligence.sources import Source, SourcePolicy
    disabled = tuple(acquisition.AcquisitionMethod(m.name, m.priority, False) for m in acquisition.DEFAULT_METHODS)
    monkeypatch.setattr(acquisition, "DEFAULT_METHODS", disabled)
    source = Source("s", "https://example.com", "family", "example.com")
    with pytest.raises(RuntimeError, match="no acquisition method available"):
        acquisition.choose_method(source, SourcePolicy())


def test_engine_invalid_transitions():
    from backend.execution.engine import create_run, transition_research
    from backend.intelligence.contracts import ResearchContract, ResearchPlan
    contract = ResearchContract(question="q")
    plan = ResearchPlan(question="q", stages=(), source_budget=1, evidence_budget=1)
    run = create_run("r", contract, plan)
    with pytest.raises(ValueError, match="invalid run status"):
        transition_research(run, "bogus")
    with pytest.raises(ValueError, match="invalid or unsupported"):
        transition_research(run, "completed")


def test_worker_boundary_remaining_guards(monkeypatch):
    from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator
    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {}, "p")
    expired_result = WorkerResult(task.task_id, task.nonce, "failure", None, None, 1, "worker", datetime.now(timezone.utc))
    expired_task = task.__class__(task.task_id, task.nonce, task.schema_version, task.task_type, task.input_hash, task.provenance, task.created_at, datetime.now(timezone.utc) - timedelta(hours=2), task.metadata)
    ok, reason = validator.validate_result(expired_task, expired_result, None)
    assert ok is False and "expired" in reason
    bad_order = task.__class__(task.task_id, task.nonce, task.schema_version, task.task_type, task.input_hash, task.provenance, datetime.now(timezone.utc), datetime.now(timezone.utc) - timedelta(hours=1), task.metadata)
    assert validator.validate_task(bad_order)[0] is False
    future = validator.create_task("fetch", {}, "p")
    future_result = WorkerResult(future.task_id, future.nonce, "failure", None, None, 1, "worker", datetime.now(timezone.utc) + timedelta(minutes=6))
    ok, reason = validator.validate_result(future, future_result, None)
    assert ok is False and "timestamp" in reason
    missing_success = validator.create_task("fetch", {}, "p")
    missing_result = WorkerResult(missing_success.task_id, missing_success.nonce, "success", None, None, 1, "worker", datetime.now(timezone.utc))
    ok, reason = validator.validate_result(missing_success, missing_result, None)
    assert ok is False and "output data" in reason
    monkeypatch.setattr(validator, "MAX_OUTPUT_SIZE_MB", 0)
    oversized = validator.create_task("fetch", {}, "p")
    payload = {"x": 1}
    import hashlib, json
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
    oversized_result = WorkerResult(oversized.task_id, oversized.nonce, "success", digest, payload, 1, "worker", datetime.now(timezone.utc))
    ok, reason = validator.validate_result(oversized, oversized_result, payload)
    assert ok is False and "exceeds" in reason
    assert validator.sample_validate(WorkerResult("t", "n", "failure", None, None, 1, "w", datetime.now(timezone.utc)), {})[0] is False
    assert validator.sample_validate(WorkerResult("t", "n", "success", "h", {}, 1, "w", datetime.now(timezone.utc)), {"error": "x"})[0] is False


def test_typed_contradiction_date_boolean_and_text_edges():
    from backend.intelligence.contradiction import TypedClaim, detect_typed_contradiction
    def c(cid, value, value_type, **kwargs):
        return TypedClaim(cid, "E", "P", value, value_type, unit=kwargs.get("unit", "u"), qualifier=kwargs.get("qualifier", "q"), valid_from=kwargs.get("valid_from"), valid_until=kwargs.get("valid_until"))
    assert detect_typed_contradiction(c("a", "2024-01-01", "date"), c("b", "2024-01-02", "date")) is not None
    assert detect_typed_contradiction(c("a", True, "boolean"), c("b", False, "boolean")) is not None
    assert detect_typed_contradiction(c("a", "x", "text", unit="a"), c("b", "y", "text", unit="b")) is None
    assert detect_typed_contradiction(c("a", "x", "text", qualifier="q1"), c("b", "x", "text", qualifier="q2")) is not None


def test_lineage_constructor_guards():
    from backend.intelligence.lineage import SourceLineage
    with pytest.raises(ValueError, match="origin_fingerprint"):
        SourceLineage("s", "f", lineage_type="republished")
    with pytest.raises(ValueError, match="identify its origin"):
        SourceLineage("s", "f", lineage_type="republished", origin_fingerprint="fp")


def test_observation_create_all_positional_forms():
    from backend.intelligence.observations import Observation
    one = Observation.create("o1", "https://e", "body")
    two = Observation.create("o2", "sid", "https://e", "body")
    three = Observation.create("o3", "sid", "https://e", "body", datetime.now(timezone.utc))
    assert one.content == two.content == three.content == "body"
    with pytest.raises(TypeError):
        Observation.create("o4", "a", "b", "c", "d", "e")


def test_verifier_final_branch_matrix():
    from backend.intelligence.certificates import create_certificate
    from backend.intelligence.claims import Claim
    from backend.intelligence.lineage import SourceLineage
    from backend.intelligence.observations import EvidenceSpan, Observation
    from backend.intelligence.verifier import ClaimStatus, EvidenceVerifier, VerificationResult
    result = VerificationResult("c", ClaimStatus.UNKNOWN)
    assert result.verified_at.tzinfo is not None
    obs1 = Observation.create("o1", "s1", "https://a", "claim text")
    obs2 = Observation.create("o2", "s2", "https://b", "claim text")
    cert1 = create_certificate(obs1, EvidenceSpan("o1", 0, 10))
    cert2 = create_certificate(obs2, EvidenceSpan("o2", 0, 10))
    claim = Claim.create("c", "claim text")
    verifier = EvidenceVerifier(semantic_strict=True)
    verified = verifier.verify_claim(claim, (cert1, cert2), {"o1": obs1, "o2": obs2}, {"s1": SourceLineage("s1", "f1", origin_fingerprint="o1"), "s2": SourceLineage("s2", "f2", origin_fingerprint="o2")}, ())
    assert verified.status in {ClaimStatus.CORROBORATED, ClaimStatus.SUPPORTED}
    same_origin = verifier.verify_claim(claim, (cert1, cert2), {"o1": obs1, "o2": obs2}, {"s1": SourceLineage("s1", "f1", origin_fingerprint="same"), "s2": SourceLineage("s2", "f2", origin_fingerprint="same")}, ())
    assert same_origin.independent_corroboration_count == 1
    inaccessible = verifier.verify_claim(claim, (cert1,), {}, {}, ())
    assert inaccessible.status == ClaimStatus.INACCESSIBLE


def test_http_runtime_error_and_redirect_exhaustion(monkeypatch):
    import backend.sources.http as http
    monkeypatch.delitem(sys.modules, "workers", raising=False)
    with pytest.raises(RuntimeError, match="Cloudflare Workers runtime"):
        http._workers_fetch()
    class Response:
        status = 302
        headers = {"location": "https://example.com/next"}
        async def arrayBuffer(self):
            return b""
    async def fetcher(_url, _opts):
        return Response()
    with pytest.raises(RuntimeError, match="too many redirects"):
        asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher))
