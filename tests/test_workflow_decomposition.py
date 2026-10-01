from pathlib import Path
import re
import yaml

ROOT=Path(__file__).parents[1]

def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def test_hybrid_language_root_delegates_to_four_reusable_lanes():
    path=ROOT/".github/workflows/hybrid-language-pilots.yml"
    text=path.read_text(encoding="utf-8")
    data=load(path)
    assert "workflow_dispatch:" in text
    assert "operations_ref:" in text
    for name in (
        "hybrid-language-pilots-rust-core.yml",
        "hybrid-language-pilots-rust-bench.yml",
        "hybrid-language-pilots-typescript.yml",
        "hybrid-language-pilots-tooling.yml",
    ):
        assert f"./.github/workflows/{name}" in text
    assert len(text.splitlines()) < 150

def test_hybrid_language_reusable_workflows_are_self_contained():
    for path in ROOT.glob(".github/workflows/hybrid-language-pilots-*.yml"):
        if path.name == "hybrid-language-pilots.yml":
            continue
        text=path.read_text(encoding="utf-8")
        data=load(path)
        assert "workflow_call:" in text
        assert "operations_ref:" in text
        assert "needs.resolve_operations_ref" not in text
        assert "needs.resolve_operations_ref" not in text
        assert len(text.splitlines()) < 550

def test_nightly_research_is_lifecycle_decomposed():
    root=ROOT/".github/workflows/nightly-multi-agent-research-v3.yml"
    text=root.read_text(encoding="utf-8")
    assert "./.github/workflows/nightly-research-execution.yml" in text
    assert "./.github/workflows/nightly-research-migration-review.yml" in text
    assert "./.github/workflows/nightly-research-diagnosis.yml" in text
    assert "final-gate:" in text
    for name in ("nightly-research-execution.yml","nightly-research-migration-review.yml","nightly-research-diagnosis.yml"):
        child=ROOT/".github/workflows"/name
        assert "workflow_call:" in child.read_text(encoding="utf-8")

def test_nightly_diagnosis_uses_parent_result_inputs_not_nested_needs():
    path=ROOT/".github/workflows/nightly-research-diagnosis.yml"
    text=path.read_text(encoding="utf-8")
    assert "needs.research" not in text
    assert "needs.migration_review" not in text
    assert "inputs.research_result" in text
    assert "inputs.migration_result" in text

def test_production_release_entrypoint_is_a_compatibility_facade():
    path=ROOT/"scripts/production_release.sh"
    text=path.read_text(encoding="utf-8")
    assert "source" in text
    assert len(text.splitlines()) < 40
    assert (ROOT/"scripts/release/production_release_preflight.sh").exists()
    assert (ROOT/"scripts/release/production_release_deploy_acceptance.sh").exists()
