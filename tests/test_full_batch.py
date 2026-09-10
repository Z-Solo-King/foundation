from backend.artifacts.manifest import create_manifest
from backend.execution.adaptive import choose_strategy
from backend.execution.capability import CapabilityState, CapabilityRegistry
from backend.execution.research_run import create_run, transition
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.planning import create_plan
from backend.intelligence.contradiction import detect_contradiction
from backend.intelligence.evidence_graph import EvidenceGraph, EvidenceLink, Relation
from backend.intelligence.snapshots import ClaimSnapshot, changed
from backend.intelligence.sources import Source, SourcePolicy, SourceType, evaluate_source
from backend.intelligence.observations import Observation, EvidenceSpan
from backend.intelligence.certificates import create_certificate, verify_certificate


def test_plan():
    plan = create_plan(ResearchContract("test"))
    assert "discover_sources" in plan.stages


def test_source():
    source = Source("s1", "https://example.com", SourceType.WEB)
    assert evaluate_source(source, SourcePolicy())


def test_graph():
    graph = EvidenceGraph().add(
        EvidenceLink("c1", "e1", Relation.SUPPORTS)
    )
    assert graph.for_claim("c1")


def test_contradiction():
    assert detect_contradiction("system enabled", "system disabled")


def test_snapshot():
    first = ClaimSnapshot.create("s1", "c1", "one")
    second = ClaimSnapshot.create("s2", "c1", "two")
    assert changed(first, second)


def test_capability():
    registry = CapabilityRegistry()
    registry.register(
        CapabilityState("browser", True, True, 10, 9)
    )
    assert registry.usable("browser")


def test_adaptive():
    assert choose_strategy(False).name == "direct_http"


def test_run():
    run = create_run("r1", ResearchContract("test"))
    assert transition(run, "running").status == "running"


def test_certificate():
    observation = Observation.create(
        "o1",
        "s1",
        "https://example.com",
        "The system stores evidence.",
    )
    certificate = create_certificate(
        observation,
        EvidenceSpan("o1", 18, 26),
    )
    assert certificate.span_text == "evidence"
    assert verify_certificate(observation, certificate)


def test_artifact():
    manifest = create_manifest(
        "a1",
        "x.txt",
        "txt",
        b"hello",
        "run:r1",
    )
    assert len(manifest.content_hash) == 64
