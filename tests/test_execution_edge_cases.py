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


def test_api_success_and_engine_lifecycle():
    from backend.api.main import submit_research
    from backend.api.models import ResearchRequest
    from backend.execution.engine import create_run, complete_research, transition_research
    from backend.intelligence.contracts import ResearchContract, ResearchPlan
    response = submit_research(ResearchRequest("q"))
    assert response.ok is True
    assert response.run_id
    assert submit_research(type("R", (), {"strict_zero_cost_only": False, "validate": lambda self: None})()).ok is False
    run = create_run("r", ResearchContract("q"), ResearchPlan("q", ("a",), 1, 1))
    running = transition_research(run, "running")
    assert running.status == "running"
    assert complete_research(running).status == "completed"
    assert complete_research(running, success=False).status == "failed"
    assert transition_research(running, "completed").status == "completed"
    assert transition_research(running, "failed").status == "failed"
    with pytest.raises(ValueError): transition_research(complete_research(running), "running")


def test_acquisition_and_strategy_no_available(monkeypatch):
    import backend.execution.acquisition as acquisition
    import backend.execution.adaptive as adaptive
    from backend.execution.adaptive import AcquisitionStrategy
    from backend.intelligence.sources import Source, SourcePolicy, SourceType
    source = Source("s", "https://example.com", SourceType.WEB)
    monkeypatch.setattr(acquisition, "DEFAULT_METHODS", ())
    with pytest.raises(RuntimeError): acquisition.choose_method(source, SourcePolicy())
    monkeypatch.setattr(adaptive, "DEFAULT_STRATEGIES", (AcquisitionStrategy("disabled", 1, enabled=False),))
    with pytest.raises(RuntimeError): adaptive.choose_strategy(False)


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
    run2 = add_observation(start_research(run), obs, budget); run2 = add_claim(run2, Claim.create("c", "evidence"))
    assert len(run2.observations) == 1 and len(run2.claims) == 1
    assert transition_research(run, "planned") is run
    with pytest.raises(ValueError): transition_research(run, "bad")
    with pytest.raises(ValueError): transition_research(run2, "planned")
    assert complete_research(run2, False).status == "failed"
    assert summarize_research(run)["claims_verified"] == 0
    assert choose_strategy(True).requires_browser is False and choose_strategy(False).requires_browser is False
    source = Source("s", "https://example.com", SourceType.WEB)
    method = choose_method(source, SourcePolicy()); assert method.enabled
    assert reserve_acquisition(source, SourcePolicy(), ResourceBudget(requests=1)).enabled
    assert simulate_acquire(source, method, "o2", "c").content == "c" and create_lineage(source, "f").lineage_type == "origin"
    reg = ProviderRegistry(); reg.register(ProviderCapability("p", "x", enabled=False)); reg.register(ProviderCapability("free", "x", priority=2)); reg.register(ProviderCapability("paid", "x", free_eligible=False, priority=1)); reg.register(ProviderCapability("extract", "extraction"))
    router = ProviderRouter(reg, ResourceBudget(inference_calls=1))
    assert router.route("missing").approved is False
    assert router.route("x").approved is True
    disabled = ProviderRegistry(); disabled.register(ProviderCapability("d", "y", enabled=False)); assert ProviderRouter(disabled, ResourceBudget()).route("y").approved is False
    paid = ProviderRegistry(); paid.register(ProviderCapability("p", "z", free_eligible=False)); assert ProviderRouter(paid, ResourceBudget()).route("z").approved is False
    exhausted = ProviderRouter(reg, ResourceBudget(inference_calls=0)); assert exhausted.route("extraction").approved is False
    class BrokenBudget:
        def remaining(self): raise ResourceError("broken")
        def consume_inference(self): pass
    assert ProviderRouter(reg, BrokenBudget()).route("extraction").approved is False
    assert ProviderRouter(reg, ResourceBudget(inference_calls=1)).execute("x", lambda: "ok") == "ok"
    with pytest.raises(PermissionError): ProviderRouter(reg, ResourceBudget()).execute("missing", lambda: "x")
    with pytest.raises(PermissionError): ProviderRouter(reg, ResourceBudget(inference_calls=0)).execute("extraction", lambda: "x")
    assert ResearchSynthesizer().synthesize(run).confidence == "unknown"


def test_engine_invalid_transitions():
    from backend.execution.engine import create_run, transition_research
    from backend.intelligence.contracts import ResearchContract, ResearchPlan
    run = create_run("r", ResearchContract(question="q"), ResearchPlan(question="q", stages=(), source_budget=1, evidence_budget=1))
    with pytest.raises(ValueError, match="invalid run status"): transition_research(run, "bogus")
    with pytest.raises(ValueError, match="invalid or unsupported"): transition_research(run, "completed")


def test_engine_invalid_lifecycle_branches():
    from backend.execution.engine import complete_research, create_run, start_research
    from backend.intelligence.contracts import ResearchContract, ResearchPlan
    planned = create_run("r", ResearchContract(question="q"), ResearchPlan(question="q", stages=(), source_budget=1, evidence_budget=1))
    with pytest.raises(ValueError): start_research(planned.__class__(planned.run_id, planned.contract, planned.plan, "completed"))
    running = start_research(planned)
    assert complete_research(running, success=False).status == "failed"
    with pytest.raises(ValueError): complete_research(planned)


def test_synthesis_status_matrix_and_entailment_negation():
    import hashlib
    from backend.execution.engine import ResearchRun
    from backend.execution.synthesis import ResearchSynthesizer
    from backend.intelligence.contracts import ResearchContract, ResearchPlan
    from backend.intelligence.claims import Claim
    from backend.intelligence.verifier import VerificationResult, ClaimStatus
    from backend.intelligence.certificates import EvidenceCertificate
    from backend.intelligence.observations import Observation
    obs = Observation.create("o", "sid", "https://e", "available evidence")
    cert = EvidenceCertificate("o", "sid", "https://e", hashlib.sha256(obs.content.encode()).hexdigest(), 0, 9, "available", True)
    def run(statuses):
        vals=[]
        for i,s in enumerate(statuses): vals.append((Claim.create(f"c{i}", f"claim {i}"), VerificationResult(f"c{i}", s, (cert,) if s in {ClaimStatus.CORROBORATED, ClaimStatus.SUPPORTED} else (), (), 2 if s==ClaimStatus.CORROBORATED else 0, ("reason",))))
        return ResearchRun("r", ResearchContract("q"), ResearchPlan("q", (), 1, 1), verified_claims=tuple(vals), observations=(obs,))
    for statuses, confidence in (((ClaimStatus.CORROBORATED,), "high"), ((ClaimStatus.SUPPORTED,), "medium"), ((ClaimStatus.PARTIAL,), "low"), ((ClaimStatus.CONTRADICTED,), "unknown"), ((ClaimStatus.SUPPORTED, ClaimStatus.CONTRADICTED), "low"), ((ClaimStatus.UNKNOWN,), "unknown")):
        assert ResearchSynthesizer().synthesize(run(statuses)).confidence == confidence
    mixed = ResearchSynthesizer().synthesize(run((ClaimStatus.SUPPORTED, ClaimStatus.CONTRADICTED, ClaimStatus.UNKNOWN)))
    assert "Unresolved aspects:" in mixed.answer
