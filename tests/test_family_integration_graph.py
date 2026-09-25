import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
GRAPH = ROOT / "docs" / "FAMILY_INTEGRATION_GRAPH.json"


def test_family_integration_graph_is_complete_and_closed():
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))

    assert graph["schema"] == "family-integration-graph/v1"
    assert graph["status"] == "CURRENT"

    nodes = {node["id"]: node for node in graph["nodes"]}
    assert len(nodes) >= 14
    assert {"foundation.docs", "foundation.ai_map", "foundation.research",
            "foundation.benchmark", "foundation.edge", "foundation.ui",
            "foundation.persistence", "operations.extractor_mapper",
            "operations.chatbot", "operations.resource",
            "operations.governance", "operations.runtime",
            "family.ci", "family.observability"} <= nodes.keys()

    for edge in graph["edges"]:
        assert edge["from"] in nodes
        assert edge["to"] in nodes
        assert edge["contract"].strip()

    materials = graph["material_registry"]
    assert len(materials) == 20
    assert all(isinstance(value, list) and value for value in materials.values())

    material_ids = set(materials)
    probes = graph["benchmark_probes"]
    assert len(probes) >= 10
    for probe in probes:
        assert probe["materials"]
        assert set(probe["materials"]) <= material_ids
        assert probe["targets"]
        for target in probe["targets"]:
            repo, number = target.rsplit("#", 1)
            assert repo in {"foundation", "operations"}
            assert number.isdigit()

    assert graph["loops"]["research_learning"][0] == "research signal"
    assert graph["loops"]["failure_correction"][0] == "bounded worker"
    assert graph["loops"]["family_sync"][0] == "source change"
    assert graph["loops"]["resource"][0] == "request"
    assert graph["loops"]["chat_research"][0] == "UI intent"


def test_family_integration_graph_does_not_create_forbidden_authorities():
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    forbidden = " ".join(graph["non_goals"]).lower()
    assert "no second resource ledger" in forbidden
    assert "no private operations policy copied into foundation" in forbidden
    assert "no ui transport state treated as execution truth" in forbidden
