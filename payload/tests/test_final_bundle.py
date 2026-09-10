from backend.api import health_response
from backend.artifacts.manifest import create_manifest
from backend.execution.acquisition import reserve_acquisition
from backend.execution.capability import CapabilityRegistry, CapabilityState
from backend.execution.providers import ProviderCapability, ProviderRegistry
from backend.execution.research_run import create_run, transition
from backend.execution.resources import ResourceBudget
from backend.intelligence.certificates import create_certificate, verify_certificate
from backend.intelligence.claims import Claim
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.contradiction import detect_contradiction
from backend.intelligence.evidence_graph import EvidenceGraph, EvidenceLink, Relation
from backend.intelligence.lineage import SourceLineage, is_independent
from backend.intelligence.observations import EvidenceSpan, Observation
from backend.intelligence.planning import create_plan
from backend.intelligence.snapshots import ClaimSnapshot, changed
from backend.intelligence.sources import Source, SourcePolicy, SourceType


def test_health():
    assert health_response()["status"] == "ok"


def test_plan():
    plan = create_plan(ResearchContract("test"))
    assert "verify_evidence" in plan.stages


def test_source_budget():
    source = Source("s1", "https://example.com", SourceType.WEB)
    budget = ResourceBudget(requests=2)
    method = reserve_acquisition(source, SourcePolicy(), budget)
    assert method.name == "direct_http"
    assert budget.requests == 1


def test_certificate():
    observation = Observation.create(
        "o1", "s1", "https://example.com", "The system stores evidence."
    )
    cert = create_certificate(observation, EvidenceSpan("o1", 18, 26))
    assert cert.span_text == "evidence"
    assert verify_certificate(observation, cert)


def test_lineage():
    assert not is_independent(
        SourceLineage("s1", "family-a"),
        SourceLineage("s2", "family-a"),
    )
    assert is_independent(
        SourceLineage("s1", "family-a"),
        SourceLineage("s2", "family-b"),
    )


def test_graph_and_contradiction():
    graph = EvidenceGraph().add(
        EvidenceLink("c1", "e1", Relation.SUPPORTS)
    )
    assert graph.for_claim("c1")
    assert detect_contradiction("system enabled", "system disabled")


def test_snapshot():
    first = ClaimSnapshot.create("s1", "c1", "one")
    second = ClaimSnapshot.create("s2", "c1", "two")
    assert changed(first, second)


def test_capability_registry():
    registry = CapabilityRegistry()
    registry.register(CapabilityState("browser", True, True, 10, 9))
    assert registry.usable("browser")


def test_provider_registry():
    registry = ProviderRegistry()
    registry.register(ProviderCapability("a", "search", priority=20))
    registry.register(ProviderCapability("b", "search", priority=10))
    assert registry.best("search").provider == "b"


def test_research_run():
    run = create_run("r1", ResearchContract("test"))
    assert transition(run, "running").status == "running"


def test_claim():
    assert Claim.create("c1", "A valid claim.").text == "A valid claim."


def test_artifact():
    manifest = create_manifest("a1", "result.txt", "txt", b"hello", "run:r1")
    assert len(manifest.content_hash) == 64
