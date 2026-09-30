from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLEET = ROOT / "docs" / "AI_PROVIDER_FLEET_2026-09-30.json"


def load_fleet() -> dict:
    return json.loads(FLEET.read_text(encoding="utf-8"))


def test_public_provider_fleet_has_exact_shared_eight_family_set() -> None:
    data = load_fleet()
    expected = {
        "openrouter_free",
        "groq",
        "gemini",
        "cerebras",
        "nvidia_nim",
        "cohere_free",
        "huggingface_free",
        "siliconflow",
    }
    assert set(data["supported_external_providers"]) == expected
    assert set(data["external_providers"]) == expected
    assert len(expected) == 8
    assert data["native_runtime_provider"] == "cloudflare_workers_ai"


def test_public_provider_fleet_has_all_nine_task_families() -> None:
    assert set(load_fleet()["task_families"]) == {
        "chatbot",
        "research",
        "search_synthesis",
        "extraction_assist",
        "audit_assist",
        "scan_triage",
        "action_plan",
        "workflow_assist",
        "cloudflare_diagnostic",
    }


def test_public_provider_fleet_remains_strict_zero_cost() -> None:
    invariants = load_fleet()["zero_cost_invariants"]
    assert invariants == {
        "max_daily_cost_usd": 0,
        "paid_fallback_allowed": False,
        "unknown_pricing_allowed": False,
        "auto_recharge_allowed": False,
        "auto_upgrade_allowed": False,
    }


def test_cerebras_is_supported_but_not_asserted_as_configured() -> None:
    data = load_fleet()
    assert "cerebras" in data["supported_external_providers"]
    assert "cerebras" not in data["currently_configured_external_providers"]
    assert "mistral" in data["conditional_candidates"]
