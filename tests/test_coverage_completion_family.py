import asyncio
import hashlib
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest


def test_resource_budget_all_paths():
    from backend.execution.resources import ResourceBudget, ResourceError
    budget = ResourceBudget(requests=2, evidence_items=2, ai_calls=3, inference_calls=2)
    assert budget.inference_remaining == 2
    assert budget.remaining()["inference_calls"] == 2
    budget.consume_requests(); budget.consume_evidence(); budget.consume_ai_calls(); budget.consume_inference()
    with pytest.raises(ValueError): ResourceBudget(inference_calls=-1)
    with pytest.raises(ValueError): budget.consume("requests", -1)
    with pytest.raises(ValueError): budget.consume("missing")
    budget.requests = None
    with pytest.raises(ValueError): budget.consume("requests")
    budget.requests = 0
    with pytest.raises(ResourceError): budget.consume_requests()


def test_contradiction_typed_and_legacy_all_markers():
    from backend.intelligence.contradiction import TypedClaim, detect_contradiction, detect_typed_contradiction
    assert detect_contradiction("", "x") is None
    assert detect_contradiction("same", "same") is None
    for pos, neg in (("true", "false"), ("yes", "no"), ("enabled", "disabled"), ("available", "unavailable")):
        assert detect_contradiction(pos, neg) is not None
        assert detect_contradiction(neg, pos) is not None
    assert detect_contradiction("not available", "available") is not None
    assert detect_contradiction("available", "not available") is not None
    base = dict(entity="E", predicate="P", scope=None, valid_from=None, valid_until=None, unit="u", qualifier="q", version=None)
    def claim(cid, value, value_type, **changes):
        data = dict(base); data.update(changes)
        return TypedClaim(cid, data.pop("entity"), data.pop("predicate"), value, value_type, **data)
    assert detect_typed_contradiction(claim("a", 1, "numeric"), claim("b", 2, "numeric")) is not None
    assert detect_typed_contradiction(claim("a", "2024-01-01", "date"), claim("b", date(2024,1,2), "date")) is not None
    assert detect_typed_contradiction(claim("a", "yes", "boolean"), claim("b", "no", "boolean")) is not None
    assert detect_typed_contradiction(claim("a", 1, "quantity"), claim("b", 2, "quantity")) is not None
    assert detect_typed_contradiction(claim("a", "alpha", "text"), claim("b", "beta", "text")) is not None
    assert detect_typed_contradiction(claim("a", "alpha", "text", qualifier="x"), claim("b", "alpha", "text", qualifier="y")) is not None
    assert detect_typed_contradiction(claim("a", 1, "numeric", unit="kg"), claim("b", 2, "numeric", unit="lb")) is None
    assert detect_typed_contradiction(claim("a", 1, "numeric", scope="a"), claim("b", 2, "numeric", scope="b")) is None
    assert detect_typed_contradiction(claim("a", 1, "numeric", valid_until=datetime(2024,1,1)), claim("b", 2, "numeric", valid_from=datetime(2024,1,2))) is None
    assert detect_typed_contradiction(claim("a", 1, "numeric", version="v1"), claim("b", 2, "numeric", version="v2")) is None


def test_worker_boundary_fail_closed_all_branches():
    from backend.execution.worker_boundary import WorkerResult, WorkerTask, WorkerTaskValidator
    validator = WorkerTaskValidator()
    with pytest.raises(ValueError): validator.create_task("", {}, "p")
    with pytest.raises(ValueError): validator.create_task("fetch", {}, "")
    with pytest.raises(ValueError): validator.create_task("fetch", {}, "p", {"x":"a"*20000})
    task = validator.create_task("fetch", {"a":1}, "p", {"m":1})
    assert validator.validate_task(task)[0]
    expired = WorkerTask(task.task_id, task.nonce+"e", task.schema_version, task.task_type, task.input_hash, task.provenance, task.created_at, datetime.now(timezone.utc)-timedelta(hours=1), task.metadata)
    assert validator.validate_task(expired)[0] is False
    malformed = WorkerTask("", "", task.schema_version, task.task_type, task.input_hash, "", task.created_at, task.expires_at, task.metadata)
    assert "required" in validator.validate_task(malformed)[1]
    now = datetime.now(timezone.utc)
    backwards = WorkerTask(task.task_id, "nonce-b", task.schema_version, task.task_type, task.input_hash, task.provenance, now + timedelta(hours=2), now + timedelta(hours=1), task.metadata)
    assert "precedes" in validator.validate_task(backwards)[1]
    bad_schema = WorkerTask(task.task_id, "nonce-s", "2", task.task_type, task.input_hash, task.provenance, task.created_at, task.expires_at, task.metadata)
    assert validator.validate_task(bad_schema)[0] is False
    bad_type = WorkerTask(task.task_id, "nonce-t", task.schema_version, "x", task.input_hash, task.provenance, task.created_at, task.expires_at, task.metadata)
    assert validator.validate_task(bad_type)[0] is False
    huge_meta = WorkerTask(task.task_id, "nonce-m", task.schema_version, task.task_type, task.input_hash, task.provenance, task.created_at, task.expires_at, {"x":"a"*20000})
    assert validator.validate_task(huge_meta)[0] is False
    other = WorkerTask(task.task_id+"2", task.nonce, task.schema_version, task.task_type, task.input_hash, task.provenance, task.created_at, task.expires_at, task.metadata)
    assert "another task" in validator.validate_task(other)[1]

    def result(status="success", **kw):
        return WorkerResult(task.task_id, task.nonce, status, kw.get("output_hash"), kw.get("output_data"), kw.get("execution_time_ms", 1), kw.get("worker_id", "worker"), kw.get("completed_at", datetime.now(timezone.utc)))
    h = hashlib.sha256(b'{"x": 1}').hexdigest()
    assert validator.validate_result(task, result(output_hash=h), {"x":1})[0] is True
    task2 = validator.create_task("fetch", {}, "p")
    for r in (
        result("success", output_hash=h),
        WorkerResult("x", task2.nonce, "success", h, {"x":1}, 1, "worker", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, "bad", "success", h, {"x":1}, 1, "worker", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, task2.nonce, "weird", h, {"x":1}, 1, "worker", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, task2.nonce, "success", None, None, 1, "worker", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, task2.nonce, "success", "bad", {"x":1}, 1, "worker", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, task2.nonce, "success", h, {"x":1}, -1, "worker", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, task2.nonce, "success", h, {"x":1}, 1, "", datetime.now(timezone.utc)),
        WorkerResult(task2.task_id, task2.nonce, "success", h, {"x":1}, 1, "worker", datetime.now(timezone.utc)+timedelta(minutes=6)),
    ):
        validator.validate_result(task2, r, r.output_data)
    assert validator.sample_validate(result("failure"), {})[0] is False
    assert validator.sample_validate(result("success"), [1])[0] is False
    assert validator.sample_validate(result("success"), {"error":"x"})[0] is False
    assert validator.sample_validate(result("success"), {"error":"x","status":"error"})[0] is True


def test_worker_http_entrypoint_all_paths():
    import worker
    class Req:
        def __init__(self, method, url, payload=None, headers=None): self.method, self.url, self._payload, self.headers = method, url, payload, headers or {}
        async def json(self): return self._payload
    class DBStatement:
        def __init__(self, first=None, all_rows=None): self.first_value, self.all_rows = first, all_rows or []
        def bind(self,*args): return self
        async def run(self): return {"success":True}
        async def first(self): return self.first_value
        async def all(self): return self.all_rows
    class DB:
        def prepare(self, sql): return DBStatement()
    class Art:
        async def put(self,*args,**kwargs): pass
    env = SimpleNamespace(DB=DB(), ARTIFACTS=Art(), ENVIRONMENT="development", AUTH_TOKEN=None, CONTROL_PLANE=None)
    entry = worker.Default(); entry.env = env
    assert asyncio.run(entry.fetch(Req("GET", "https://x/health")))
    assert asyncio.run(entry.fetch(Req("GET", "https://x/readiness")))
    assert asyncio.run(entry.fetch(Req("GET", "https://x/nope")))
    assert asyncio.run(entry.fetch(Req("GET", "https://x/api/v1/research/r")))
    assert asyncio.run(entry.fetch(Req("POST", "https://x/api/v1/research", [])))
    assert asyncio.run(entry.fetch(Req("POST", "https://x/api/v1/research", {"question":"q"})))


def test_api_models_capabilities_and_serialization(monkeypatch):
    from backend.api.main import api_response_to_json, submit_research
    from backend.api.models import APIResponse, ResearchRequest
    from backend.capabilities.model import Capability
    from backend.capabilities.registry import CapabilityRegistry
    assert Capability("x").remaining_today is None and Capability("x").usable() is True
    assert Capability("x", enabled=False).usable() is False
    assert Capability("x", daily_limit=2, used_today=3).remaining_today == 0
    assert Capability("x", free_eligible=False).usable() is False
    with pytest.raises(ValueError): ResearchRequest("").validate()
    with pytest.raises(ValueError): ResearchRequest("q", max_sources=0).validate()
    with pytest.raises(ValueError): ResearchRequest("q", max_evidence_items=0).validate()
    with pytest.raises(ValueError): ResearchRequest("q", strict_zero_cost_only=False).validate()
    with pytest.raises(ValueError): ResearchRequest("q", max_sources=1, source_urls=("a","b")).validate()
    reg = CapabilityRegistry(); reg.register(Capability("a")); assert reg.get("a") and reg.usable("a") and reg.usable("missing") is False
    assert len(reg.all()) == 1 and reg.snapshot() == (reg.get("a"),)
    assert api_response_to_json(APIResponse(False, error="bad")) == '{"ok": false, "error": "bad"}'
    assert "run_id" in api_response_to_json(APIResponse(True, run_id="r", metadata={"x":1}))
    assert submit_research(ResearchRequest("q", strict_zero_cost_only=False)).ok is False
    class Broken:
        def validate(self): raise ValueError("bad")
    assert submit_research(Broken()).ok is False
    from backend.api import main as api_main
    monkeypatch.setattr(api_main, "start_run", lambda contract: (_ for _ in ()).throw(RuntimeError("boom")))
    assert "Internal error" in submit_research(ResearchRequest("q")).error


def test_entailment_harness_and_claim_validation():
    from backend.evaluation.entailment import EntailmentStatus, adjudicate_ambiguous, verify_claim_entailment
    from backend.evaluation.harness import EvaluationCategory, EvaluationHarness, BenchmarkCase, EvaluationResult
    from backend.intelligence.claims import Claim
    from backend.intelligence.contracts import ResearchContract
    from backend.intelligence.observations import Observation, EvidenceSpan
    obs = Observation.create("o", "https://e", "The product is available now.")
    assert verify_claim_entailment("", obs, EvidenceSpan("o",0,3)).status == EntailmentStatus.UNSUPPORTED
    assert verify_claim_entailment("available", obs, EvidenceSpan("o",0,5)).status == EntailmentStatus.UNSUPPORTED
    amb = verify_claim_entailment("product available", Observation.create("o2","https://e","product maybe available elsewhere"), EvidenceSpan("o2",0,32), supported_threshold=1.1)
    assert amb.status == EntailmentStatus.AMBIGUOUS
    assert adjudicate_ambiguous(amb, True).accepted is True and adjudicate_ambiguous(amb, False).accepted is False
    assert adjudicate_ambiguous(verify_claim_entailment("available", obs, EvidenceSpan("o",0,31)), True).status != EntailmentStatus.AMBIGUOUS
    with pytest.raises(ValueError): Claim.create("c", "")
    assert Claim.create("c", "text").text == "text"
    with pytest.raises(ValueError): ResearchContract("").validate()
    with pytest.raises(ValueError): ResearchContract("q", max_sources=0).validate()
    with pytest.raises(ValueError): ResearchContract("q", max_evidence_items=0).validate()
    h = EvaluationHarness(); h._bootstrap_target = 2; h._promotion_threshold = 0.5
    c1 = BenchmarkCase("1", EvaluationCategory.RETRIEVAL, "d", "q", "a")
    c2 = BenchmarkCase("2", EvaluationCategory.SECURITY, "d", "q", "a")
    h.register_case(c1); h.register_case(c2)
    with pytest.raises(ValueError): h.register_case(c1)
    with pytest.raises(ValueError): h.record_result("missing", EvaluationResult("missing", True))
    h.record_result("1", EvaluationResult("1", True)); h.record_result("2", EvaluationResult("2", False))
    assert h.summary_by_category()[str(EvaluationCategory.RETRIEVAL)]["pass_rate"] == 1.0
    assert h.bootstrap_readiness()[0] is True
    h.record_result("2", EvaluationResult("2", True)); assert h.bootstrap_readiness()[0] is True
    h._bootstrap_target = 3; assert h.bootstrap_readiness()[0] is False
    h._bootstrap_target = 2; h._promotion_threshold = 1.1; assert h.bootstrap_readiness()[0] is False
    h._production_target = 1; h._promotion_threshold = 0.0; assert h.production_readiness()[0] is False
    assert h.regression_test("1", lambda case: EvaluationResult(case.case_id, True)).passed is True
    with pytest.raises(ValueError): h.regression_test("x", lambda case: EvaluationResult("x", True))


def test_intelligence_certificates_observations_lineage_sources():
    from backend.intelligence.certificates import create_certificate as create_intel_certificate, verify_certificate as verify_intel_certificate
    from backend.intelligence.lineage import SourceLineage, origin_fingerprint, is_independent
    from backend.intelligence.observations import Observation, EvidenceSpan
    from backend.intelligence.sources import Source, SourcePolicy, SourceType, canonical_source_url, evaluate_source
    obs = Observation.create("o", "sid", "https://Example.com", "hello evidence")
    span = EvidenceSpan("o",0,5); cert = create_intel_certificate(obs, span)
    assert verify_intel_certificate(obs, cert) is True
    for bad in (
        cert.__class__(cert.observation_id, "other", cert.source_url, cert.content_hash, cert.span_start, cert.span_end, cert.span_text, True),
        cert.__class__(cert.observation_id, cert.source_id, "https://other", cert.content_hash, cert.span_start, cert.span_end, cert.span_text, True),
        cert.__class__(cert.observation_id, cert.source_id, cert.source_url, "bad", cert.span_start, cert.span_end, cert.span_text, True),
        cert.__class__(cert.observation_id, cert.source_id, cert.source_url, cert.content_hash, 0, 99, cert.span_text, True),
        cert.__class__(cert.observation_id, cert.source_id, cert.source_url, cert.content_hash, cert.span_start, cert.span_end, "other", True),
        cert.__class__(cert.observation_id, cert.source_id, cert.source_url, cert.content_hash, cert.span_start, cert.span_end, cert.span_text, False),
    ):
        assert verify_intel_certificate(obs, bad) is False
    with pytest.raises(TypeError): Observation("o", "sid", "u", "c", "bad", "extra")
    with pytest.raises(TypeError): Observation.create("o", "u", "c", "x", "y", "z")
    with pytest.raises(ValueError): EvidenceSpan("x",0,1).validate(obs)
    with pytest.raises(ValueError): EvidenceSpan("o",-1,1).validate(obs)
    with pytest.raises(ValueError): EvidenceSpan("o",5,4).validate(obs)
    with pytest.raises(ValueError): EvidenceSpan("o",0,99).validate(obs)
    with pytest.raises(ValueError): SourceLineage("","f").validate()
    with pytest.raises(ValueError): SourceLineage("s","f",lineage_type="bad").validate()
    with pytest.raises(ValueError): SourceLineage("s","f",lineage_type="republished").validate()
    rep = SourceLineage("s","f",parent_source_id="p",lineage_type="republished",origin_fingerprint="fp"); rep.validate(); assert rep.effective_origin == "fp"
    assert SourceLineage("s","f").effective_origin == "family:f"
    with pytest.raises(ValueError): origin_fingerprint("")
    assert origin_fingerprint("Example.COM") == origin_fingerprint(" example.com ")
    assert is_independent(SourceLineage("a","f1"), SourceLineage("b","f2")) is True
    with pytest.raises(ValueError): canonical_source_url("bad")
    assert canonical_source_url("https://EXAMPLE.com:443//a?utm_source=x&b=2") == "https://example.com/a?b=2"
    source = Source("s","https://example.com","web",family_id="f"); source.validate(); assert source.lineage("fp").origin_fingerprint == "fp"
    with pytest.raises(ValueError): Source("s","https://example.com",SourceType.WEB,lineage_type="bad").validate()
    with pytest.raises(ValueError): Source("s","https://example.com",SourceType.WEB,lineage_type="republished").validate()
    assert evaluate_source(source, SourcePolicy()) is True and evaluate_source(source, SourcePolicy(allowed=False)) is False and evaluate_source(source, SourcePolicy(max_requests=0)) is False


def test_execution_adaptive_engine_router_synthesis():
    from backend.execution.acquisition import choose_method, reserve_acquisition, simulate_acquire, create_lineage
    from backend.execution.adaptive import choose_strategy
    from backend.execution.engine import create_run, start_research, add_observation, add_claim, complete_research, transition_research, summarize_research
    from backend.execution.providers import ProviderCapability, ProviderRegistry
    from backend.execution.router import ProviderRouter
    from backend.execution.resources import ResourceBudget, ResourceError
    from backend.execution.synthesis import ResearchSynthesizer
    from backend.intelligence.claims import Claim
    from backend.intelligence.contracts import ResearchContract, ResearchPlan
    from backend.intelligence.observations import Observation
    from backend.intelligence.sources import Source, SourcePolicy, SourceType
    contract = ResearchContract("q"); plan = ResearchPlan("q", ("a",), 1, 1); run = create_run("r", contract, plan)
    with pytest.raises(ValueError): start_research(start_research(run))
    obs = Observation.create("o", "sid", "https://e", "evidence")
    budget = ResourceBudget(evidence_items=1, requests=1, inference_calls=2)
    run2 = add_observation(start_research(run), obs, budget); run2 = add_claim(run2, Claim.create("c","evidence")); assert len(run2.observations)==1 and len(run2.claims)==1
    assert transition_research(run, "planned") is run
    with pytest.raises(ValueError): transition_research(run, "bad")
    with pytest.raises(ValueError): transition_research(run2, "planned")
    assert complete_research(run2, False).status == "failed"
    assert summarize_research(run)["claims_verified"] == 0
    assert choose_strategy(True).requires_browser is False and choose_strategy(False).requires_browser is False
    source = Source("s","https://example.com",SourceType.WEB)
    method = choose_method(source, SourcePolicy()); assert method.enabled
    assert reserve_acquisition(source, SourcePolicy(), ResourceBudget(requests=1)).enabled
    assert simulate_acquire(source, method, "o2", "c").content == "c" and create_lineage(source,"f").lineage_type == "origin"
    reg = ProviderRegistry(); reg.register(ProviderCapability("p","x",enabled=False)); reg.register(ProviderCapability("free","x",priority=2)); reg.register(ProviderCapability("paid","x",free_eligible=False,priority=1)); reg.register(ProviderCapability("extract","extraction"))
    router = ProviderRouter(reg, ResourceBudget(inference_calls=1))
    assert router.route("missing").approved is False
    assert router.route("x").approved is True
    disabled = ProviderRegistry(); disabled.register(ProviderCapability("d","y",enabled=False)); assert ProviderRouter(disabled, ResourceBudget()).route("y").approved is False
    paid = ProviderRegistry(); paid.register(ProviderCapability("p","z",free_eligible=False)); assert ProviderRouter(paid, ResourceBudget()).route("z").approved is False
    exhausted = ProviderRouter(reg, ResourceBudget(inference_calls=0)); assert exhausted.route("extraction").approved is False
    class BrokenBudget:
        def remaining(self): raise ResourceError("broken")
        def consume_inference(self): pass
    assert ProviderRouter(reg, BrokenBudget()).route("extraction").approved is False
    assert ProviderRouter(reg, ResourceBudget(inference_calls=1)).execute("x", lambda: "ok") == "ok"
    with pytest.raises(PermissionError): ProviderRouter(reg, ResourceBudget()).execute("missing", lambda: "x")
    with pytest.raises(ResourceError): ProviderRouter(reg, ResourceBudget(inference_calls=0)).execute("extraction", lambda: "x")
    synth = ResearchSynthesizer(); result = synth.synthesize(run); assert result.confidence == "unknown"


def test_synthesis_status_matrix_and_entailment_negation():
    from backend.execution.engine import ResearchRun
    from backend.execution.synthesis import ResearchSynthesizer
    from backend.intelligence.contracts import ResearchContract, ResearchPlan
    from backend.intelligence.claims import Claim
    from backend.intelligence.verifier import VerificationResult, ClaimStatus
    from backend.intelligence.certificates import EvidenceCertificate
    from backend.intelligence.observations import Observation
    obs = Observation.create("o","sid","https://e","available evidence")
    cert = EvidenceCertificate("o","sid","https://e",hashlib.sha256(obs.content.encode()).hexdigest(),0,9,"available",True)
    def run(statuses):
        vals=[]
        for i,s in enumerate(statuses): vals.append((Claim.create(f"c{i}", f"claim {i}"), VerificationResult(f"c{i}",s,(cert,) if s in {ClaimStatus.CORROBORATED,ClaimStatus.SUPPORTED} else (),(),2 if s==ClaimStatus.CORROBORATED else 0,("reason",))))
        return ResearchRun("r",ResearchContract("q"),ResearchPlan("q",(),1,1),verified_claims=tuple(vals),observations=(obs,))
    for statuses, confidence in (((ClaimStatus.CORROBORATED,),"high"),((ClaimStatus.SUPPORTED,),"medium"),((ClaimStatus.PARTIAL,),"low"),((ClaimStatus.CONTRADICTED,),"unknown"),((ClaimStatus.SUPPORTED,ClaimStatus.CONTRADICTED),"low"),((ClaimStatus.UNKNOWN,),"unknown")):
        assert ResearchSynthesizer().synthesize(run(statuses)).confidence == confidence
    mixed = ResearchSynthesizer().synthesize(run((ClaimStatus.SUPPORTED,ClaimStatus.CONTRADICTED,ClaimStatus.UNKNOWN))); assert "Contradictory" in mixed.answer and "Unresolved" in mixed.answer


def test_source_transport_and_wikipedia_boundaries(monkeypatch):
    import backend.sources.http as http
    import backend.sources.wikipedia as wikipedia
    assert http._safe_host("example.com") is True and http._safe_host("127.0.0.1") is False
    with pytest.raises(RuntimeError):
        monkeypatch.setattr(http, "_workers_fetch", lambda: (_ for _ in ()).throw(RuntimeError("runtime")))
        asyncio.run(http.fetch_public_url("https://example.com"))
    class Resp:
        def __init__(self,status=200,headers=None,body=b"ok"): self.status=status; self.headers=headers or {}; self.body=body
        async def arrayBuffer(self): return self.body
        async def json(self): return {}
    async def fetcher(url, opts): return Resp()
    got = asyncio.run(http.fetch_public_url("https://example.com", fetcher=fetcher)); assert got.status == 200
    redirects = iter([Resp(302,{"location":"/x"}), Resp(200,{},b"x")])
    got = asyncio.run(http.fetch_public_url("https://example.com", fetcher=lambda u,o: _next_async(redirects))); assert got.final_url.endswith("/x")
    async def bad_redirect(u,o): return Resp(302,{})
    with pytest.raises(RuntimeError): asyncio.run(http.fetch_public_url("https://example.com", fetcher=bad_redirect))
    async def huge(u,o): return Resp(200,{},b"x"*(http.MAX_BYTES+1))
    with pytest.raises(RuntimeError): asyncio.run(http.fetch_public_url("https://example.com", fetcher=huge))
    async def _wiki(u,o): return Resp(200,{},b"")
    monkeypatch.setattr(wikipedia, "_workers_fetch", lambda: _wiki)
    assert asyncio.run(wikipedia._implementation("q",2,fetcher=_wiki)) == []


async def _next_async(iterator):
    return next(iterator)
