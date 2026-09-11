from datetime import datetime, timedelta, timezone
import types

import pytest


def test_entailment_ai_positive_and_negative_adjudication():
    from backend.evaluation.entailment import EntailmentResult, EntailmentStatus, adjudicate_ambiguous, verify_claim_entailment
    from backend.intelligence.observations import EvidenceSpan, Observation
    result = adjudicate_ambiguous(EntailmentResult(EntailmentStatus.AMBIGUOUS, 0.7, "ambiguous"), True)
    assert result.status == EntailmentStatus.SUPPORTED
    rejected = adjudicate_ambiguous(EntailmentResult(EntailmentStatus.AMBIGUOUS, 0.7, "ambiguous"), False)
    assert rejected.status == EntailmentStatus.UNSUPPORTED
    obs = Observation.create("lex", "s", "https://e", "a b c d e f x")
    lexical = verify_claim_entailment("a b c d e f g", obs, EvidenceSpan("lex", 0, len(obs.content)))
    assert lexical.status == EntailmentStatus.SUPPORTED


def test_engine_invalid_lifecycle_branches():
    from backend.execution.engine import complete_research, create_run, start_research
    from backend.intelligence.contracts import ResearchContract, ResearchPlan
    contract = ResearchContract(question="q")
    plan = ResearchPlan(question="q", stages=(), source_budget=1, evidence_budget=1)
    planned = create_run("r", contract, plan)
    with pytest.raises(ValueError):
        start_research(planned.__class__(planned.run_id, planned.contract, planned.plan, "completed"))
    running = start_research(planned)
    assert complete_research(running, success=False).status == "failed"
    with pytest.raises(ValueError):
        complete_research(planned)


def test_worker_task_and_result_validation_all_remaining_rejections(monkeypatch):
    from backend.execution.worker_boundary import WorkerTask, WorkerResult, WorkerTaskValidator
    validator = WorkerTaskValidator()
    base = validator.create_task("fetch", {}, "p")
    assert validator.validate_task(WorkerTask("", base.nonce, base.schema_version, base.task_type, base.input_hash, base.provenance, base.created_at, base.expires_at, {}))[0] is False
    assert validator.validate_task(WorkerTask(base.task_id, base.nonce, "2.0", base.task_type, base.input_hash, base.provenance, base.created_at, base.expires_at, {}))[0] is False
    assert validator.validate_task(WorkerTask(base.task_id, base.nonce, base.schema_version, "unknown", base.input_hash, base.provenance, base.created_at, base.expires_at, {}))[0] is False
    huge = {"x": "a" * 17000}
    with pytest.raises(ValueError, match="metadata exceeds"):
        validator.create_task("fetch", {}, "p", huge)
    active = validator.create_task("fetch", {}, "p")
    assert validator.validate_task(active)[0] is True
    conflicting = WorkerTask(active.task_id + "2", active.nonce, active.schema_version, active.task_type, active.input_hash, active.provenance, active.created_at, active.expires_at, active.metadata)
    assert validator.validate_task(conflicting)[0] is False
    completed = validator.create_task("fetch", {}, "p")
    validator.validate_task(completed)
    validator._completed_nonces.add(completed.nonce)
    assert validator.validate_task(completed)[0] is False
    expired = WorkerTask(base.task_id + "x", "nonce-expired", base.schema_version, base.task_type, base.input_hash, base.provenance, base.created_at, datetime.now(timezone.utc) - timedelta(hours=1), base.metadata)
    assert validator.validate_task(expired)[0] is False
    good = validator.create_task("fetch", {"x": 1}, "p")
    now = datetime.now(timezone.utc)
    result = WorkerResult(good.task_id, good.nonce, "bogus", None, None, 1, "worker", now)
    assert validator.validate_result(good, result, None)[0] is False
    for status in ("failure", "timeout", "invalid"):
        task = validator.create_task("fetch", {status: 1}, "p")
        result = WorkerResult(task.task_id, task.nonce, status, None, None, 1, "worker", now)
        ok, reason = validator.validate_result(task, result, None)
        assert ok is True and reason == "valid"


def test_worker_concurrent_replay_guards():
    from backend.execution.worker_boundary import WorkerTaskValidator, WorkerResult
    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {}, "p")

    class RaceLock:
        def __enter__(self):
            validator._completed_nonces.add(task.nonce)
        def __exit__(self, *_):
            return False

    validator._completed_nonces.clear()
    validator._lock = RaceLock()
    assert validator.validate_task(task)[0] is False

    validator = WorkerTaskValidator()
    result_task = validator.create_task("fetch", {}, "p")
    validator._completed_nonces.add(result_task.nonce)
    result = WorkerResult(result_task.task_id, result_task.nonce, "failure", None, None, 1, "worker", datetime.now(timezone.utc))
    assert validator.validate_result(result_task, result, None)[0] is False


def test_worker_result_rejects_invalid_timestamp_and_execution_time():
    from backend.execution.worker_boundary import WorkerResult, WorkerTaskValidator
    validator = WorkerTaskValidator()
    task = validator.create_task("fetch", {}, "p")
    now = datetime.now(timezone.utc)
    naive = WorkerResult(task.task_id, task.nonce, "failure", None, None, 1, "worker", now.replace(tzinfo=None))
    assert validator.validate_result(task, naive, None)[0] is False
    future = WorkerResult(task.task_id, task.nonce, "failure", None, None, 1, "worker", now + timedelta(minutes=6))
    assert validator.validate_result(task, future, None)[0] is False
    negative = WorkerResult(task.task_id, task.nonce, "failure", None, None, -1, "worker", now)
    assert validator.validate_result(task, negative, None)[0] is False
    missing_worker = WorkerResult(task.task_id, task.nonce, "failure", None, None, 1, "worker", now).copy(worker_id="") if False else WorkerResult(task.task_id, task.nonce, "failure", None, None, 1, "", now)
    assert validator.validate_result(task, missing_worker, None)[0] is False


def test_typed_contradiction_entity_predicate_and_version_guards():
    from backend.intelligence.contradiction import TypedClaim, detect_typed_contradiction
    base = TypedClaim("a", "E", "P", "x", "text")
    assert detect_typed_contradiction(base, TypedClaim("b", "F", "P", "x", "text")) is None
    assert detect_typed_contradiction(base, TypedClaim("c", "E", "Q", "x", "text")) is None
    assert detect_typed_contradiction(TypedClaim("d", "E", "P", "x", "text", version="1"), TypedClaim("e", "E", "P", "y", "text", version="2")) is None
    a = TypedClaim("aa", "E", "P", "x", "unknown", unit=None, qualifier=None)
    b = TypedClaim("bb", "E", "P", "y", "unknown", unit=None, qualifier=None)
    assert detect_typed_contradiction(a, b) is None
    left = TypedClaim("left", "E", "P", 1, "numeric", valid_until=datetime(2026, 1, 1, tzinfo=timezone.utc), unit="kg")
    right = TypedClaim("right", "E", "P", 2, "numeric", valid_from=datetime(2026, 2, 1, tzinfo=timezone.utc), unit="kg")
    assert detect_typed_contradiction(left, right) is None
    quantity = TypedClaim("q", "E", "P", 1, "quantity", unit=None)
    quantity2 = TypedClaim("q2", "E", "P", 2, "quantity", unit=None)
    assert detect_typed_contradiction(quantity, quantity2) is None
    enum_a = TypedClaim("ea", "E", "P", "same", "enum", unit=None)
    enum_b = TypedClaim("eb", "E", "P", "same", "enum", unit=None)
    assert detect_typed_contradiction(enum_a, enum_b) is None
    text_a = TypedClaim("t1", "E", "P", "a", "text", unit="kg", qualifier="x")
    text_b = TypedClaim("t2", "E", "P", "b", "text", unit="lb", qualifier="x")
    assert detect_typed_contradiction(text_a, text_b) is None


def test_lineage_validation_guards():
    from backend.intelligence.lineage import SourceLineage
    with pytest.raises(ValueError):
        SourceLineage("s", "f", lineage_type="bogus").validate()
    with pytest.raises(ValueError):
        SourceLineage("s", "f", lineage_type="republished").validate()


def test_observation_invalid_span_order_and_creation():
    from backend.intelligence.observations import EvidenceSpan, Observation
    obs = Observation.create("o", "sid", "https://e", "abc")
    with pytest.raises(ValueError):
        EvidenceSpan("o", 3, 2).text_from(obs)
    with pytest.raises(ValueError):
        EvidenceSpan("wrong", 0, 1).text_from(obs)
    with pytest.raises(TypeError):
        Observation("o1", "sid", None, "text", datetime.now(timezone.utc))
    with pytest.raises(TypeError):
        Observation("o2", "sid", "https://e", None, datetime.now(timezone.utc))


def test_verifier_inaccessible_semantic_and_explicit_timestamp_paths():
    from backend.intelligence.claims import Claim
    from backend.intelligence.certificates import create_certificate
    from backend.intelligence.observations import EvidenceSpan, Observation
    from backend.intelligence.verifier import ClaimStatus, EvidenceVerifier, VerificationResult
    claim = Claim.create("c", "text")
    obs = Observation.create("o", "s", "https://e", "other")
    cert = create_certificate(obs, EvidenceSpan("o", 0, 5))
    verifier = EvidenceVerifier(semantic_strict=True)
    result = verifier.verify_claim(claim, (cert,), {"o": obs}, {}, ())
    assert result.status in {ClaimStatus.PARTIAL, ClaimStatus.UNKNOWN, ClaimStatus.INACCESSIBLE}
    explicit = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert VerificationResult("v", ClaimStatus.UNKNOWN, verified_at=explicit).verified_at == explicit


def test_http_runtime_export_and_redirect_without_location(monkeypatch):
    import backend.sources.http as http
    monkeypatch.setitem(__import__('sys').modules, "workers", types.SimpleNamespace(fetch=lambda *_args, **_kwargs: object()))
    assert http._workers_fetch() is not None
    monkeypatch.delitem(__import__('sys').modules, "workers", raising=False)
    with pytest.raises(RuntimeError):
        http._workers_fetch()
    class Response:
        status = 302
        headers = {}
        async def arrayBuffer(self):
            return b""
    async def fetcher(_url, _opts):
        return Response()
    import asyncio
    with pytest.raises(RuntimeError, match="redirect"):
        asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher))
