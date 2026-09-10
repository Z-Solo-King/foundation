from backend.execution.acquisition import DEFAULT_METHODS, reserve_acquisition
from backend.execution.pipeline import attach_observation, start_run
from backend.execution.providers import ProviderCapability, ProviderRegistry
from backend.execution.resources import ResourceBudget
from backend.intelligence.certificates import create_certificate, verify_certificate
from backend.intelligence.claims import Claim
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.integrity import sha256_text
from backend.intelligence.lineage import SourceLineage, is_independent
from backend.intelligence.observations import EvidenceSpan, Observation
from backend.intelligence.planning import create_plan
from backend.intelligence.sources import Source, SourcePolicy, SourceType


def test_plan():
    plan = create_plan(ResearchContract(question="test"))
    assert "discover_sources" in plan.stages
    assert plan.source_budget == 20


def test_source_and_acquisition():
    source = Source("s1", "https://example.com", SourceType.WEB)
    budget = ResourceBudget(requests=2)
    method = reserve_acquisition(source, SourcePolicy(), budget)
    assert method.name == "direct_http"
    assert budget.remaining()["requests"] == 1
    assert len(DEFAULT_METHODS) == 5


def test_evidence_certificate_and_integrity():
    obs = Observation.create(
        "obs1", "s1", "https://example.com", "The system stores evidence."
    )
    span = EvidenceSpan("obs1", 18, 26)
    cert = create_certificate(obs, span)
    assert cert.span_text == "evidence"
    assert cert.content_hash == sha256_text(obs.content)
    assert verify_certificate(obs, cert)


def test_independence():
    first = SourceLineage("s1", "family-a")
    second = SourceLineage("s2", "family-a")
    third = SourceLineage("s3", "family-b")
    assert not is_independent(first, second)
    assert is_independent(first, third)


def test_provider_registry():
    registry = ProviderRegistry()
    registry.register(ProviderCapability("provider-a", "search", priority=20))
    registry.register(ProviderCapability("provider-b", "search", priority=10))
    assert registry.best("search").provider == "provider-b"


def test_run_pipeline():
    run = start_run(ResearchContract(question="test"))
    budget = ResourceBudget(evidence_items=1)
    obs = Observation.create("o1", "s1", "https://example.com", "content")
    run = attach_observation(run, obs, budget)
    assert len(run.observations) == 1
    claim = Claim.create("c1", "A test claim.")
    assert claim.text == "A test claim."
