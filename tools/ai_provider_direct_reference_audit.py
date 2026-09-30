#!/usr/bin/env python3
"""Fail-closed public audit for direct external AI-provider coupling."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROVIDER_MARKERS = (
    "api.groq.com",
    "generativelanguage.googleapis.com",
    "integrate.api.nvidia.com",
    "api.cohere.ai",
    "router.huggingface.co",
    "openrouter.ai/api/v1",
    "GROQ_API_KEY",
    "GEMINI_API_KEY",
    "NVIDIA_NIM_API_KEY",
    "COHERE_API_KEY",
    "HF_TOKEN",
    "OPENROUTER_API_KEY",
)

ALLOWED_RELATIVE_PATHS = {
    "tools/woocommerce_v175_plugin_fingerprint_22.py",
    "tools/provider_fleet_ai_adapter.py",
    "tools/ai_provider_direct_reference_audit.py",
}

SCAN_SUFFIXES = {".py", ".mjs", ".js", ".ts", ".tsx", ".yml", ".yaml", ".toml"}


def direct_provider_references() -> list[tuple[str, str]]:
    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative in ALLOWED_RELATIVE_PATHS or relative.startswith("tests/") or relative.startswith(".git/"):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for marker in PROVIDER_MARKERS:
            if marker in text:
                offenders.append((relative, marker))
    return sorted(set(offenders))


def main() -> int:
    offenders = direct_provider_references()
    if offenders:
        for path, marker in offenders:
            print(f"AI_PROVIDER_DIRECT_REFERENCE {path} {marker}")
        return 1
    print("Foundation AI provider direct-reference audit: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
