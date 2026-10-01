from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_policy_modules_contain_contracts_not_concrete_policy_tables():
    checks = {
        ROOT / "backend/admission.py": ("max_requests_per_subject: int =", "max_concurrent_global: int =", "ADMISSION_POLICY ="),
        ROOT / "backend/intelligence/authority.py": ("_ALLOWED =",),
        ROOT / "backend/intelligence/planning.py": ("CATEGORY_REQUIRED_SOURCE_FAMILIES =", "keyword_groups = {"),
    }
    for path, forbidden in checks.items():
        source = path.read_text(encoding="utf-8")
        for marker in forbidden:
            assert marker not in source, f"protected policy marker leaked into {path}: {marker}"


def test_public_provider_execution_is_not_embedded():
    source = (ROOT / "tools/woocommerce_v175_transport.py").read_text(encoding="utf-8")
    forbidden = (
        "api.groq.com",
        "generativelanguage.googleapis.com",
        "openrouter.ai/api/v1",
        "integrate.api.nvidia.com",
        "api.cohere.ai",
        "router.huggingface.co",
    )
    assert not any(marker in source for marker in forbidden)


def test_paused_task_workflows_have_no_automatic_trigger():
    workflows = ROOT / ".github" / "workflows"
    paused = (
        "autonomous-benchmark.yml",
        "autonomous-engineering-supervisor.yml",
        "autonomous-scorecard.yml",
        "project-improvement-supervisor.yml",
        "live-ai-provider-crossfire.yml",
        "live-ai-agent-benchmark.yml",
        "nightly-ai-research-20jobs.yml",
        "fresh-control-plane-identity-acceptance.yml",
        "canonical-workflow-dispatch-acceptance.yml",
    )
    for name in paused:
        source = (workflows / name).read_text(encoding="utf-8")
        assert "workflow_dispatch:" in source
        assert "schedule:" not in source
        assert "
  push:" not in source
        assert "task workflow is paused" in source
