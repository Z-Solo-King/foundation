from __future__ import annotations

from tools.cross_system_equivalence import (
    architecture,
    pair_declarations,
    pair_features,
    pair_policies,
)


def _map(repo: str, policies: dict, features: list[dict], flows=None):
    return {
        "schema_version": "ai-project-map/v2",
        "repository": repo,
        "policy_catalog": policies,
        "feature_domains": features,
        "connection_model": {
            "node_types": ["repository", "feature", "function"],
            "edge_types": ["contains", "calls"],
        },
        "combined_architecture": {"flow": flows or []},
        "function_metrics": {"canonical_surface_declarations": 3},
    }


def test_policy_pairs_distinguish_exact_and_scope_missing():
    result = pair_policies(
        _map("foundation", {"P001": "one owner"}, []),
        _map("operations", {"P001": "one owner", "P016": "strict $0 / no paid fallback"}, []),
    )
    states = {item["id"]: item["state"] for item in result["rows"]}
    assert states == {"P001": "exact", "P016": "operations_only_scope"}


def test_feature_pairing_detects_cross_family_overlap():
    left = [{"id": "FND.mapper", "usage": "deterministic product mapping",
             "key": ["map_product", "normalize"], "surfaces": ["foundation_core"],
             "policy_logic": "normalize before mapping", "policies": ["P001", "P005"]}]
    right = [{"id": "OPS.extractor_mapper", "usage": "bounded product mapping",
              "key": ["map_product", "normalize"], "surfaces": ["extractor_mapper"],
              "policy_logic": "deterministic mapping", "policies": ["P001", "P005", "P020"]}]
    result = pair_features(_map("foundation", {"P001": "one owner"}, left),
                           _map("operations", {"P001": "one owner"}, right))
    assert result["overlaps"]
    assert result["cartesian_pairs"] == 1


def test_architecture_pairing_reports_shared_and_unique_flows():
    result = architecture(
        _map("foundation", {}, [], ["a -> b"]),
        _map("operations", {}, [], ["a -> b", "x -> y"]),
    )
    assert result["flows"]["shared"] == ["a -> b"]


def test_declaration_pairing_is_deterministic():
    left = {"declarations": [{"name": "map_product", "path": "foundation_core/product_mapping.py"}]}
    right = {"declarations": [{"name": "map_product", "path": "extractor_mapper/fast_engine.py"}]}
    result = pair_declarations(left, right)
    assert result["shared_names"] == ["map_product"]
    assert result["same_name_pairs"][0]["name"] == "map_product"
