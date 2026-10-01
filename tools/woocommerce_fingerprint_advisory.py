"""Bounded external-AI advisory adapter.

AI output remains advisory evidence classification and never becomes native-feed
verification or extraction authority.
"""
#!/usr/bin/env python3
from __future__ import annotations

"""
WooCommerce V175-derived plugin fingerprint + native Google-feed recovery harness.

The attached extract_universal_V175.py is the source/design authority for:
- clearance-aware browser recovery
- persistent-cookie semantics
- browser/XHR discovery
- transport/provenance separation
- bounded recovery budgets
- public-only acquisition

V175 source SHA-256: 33d651b329c20372db40026c0626a3227408096beb910c1d1069266af5cc1b15

This focused harness deliberately does NOT import the 1.5 MB monolith at runtime.
It preserves the V175 evidence contracts while enforcing the repository acceptance boundary:
- Chromium + Firefox/Gecko + WebKit clean browser passes
- public API/XHR discovery without clearance-cookie replay
- optional Cloudflare Browser Run and Browserless adapters
- passive robots/sitemap + historical index discovery
- plugin fingerprint normalization with provenance-aware confidence
- plugin-specific native Google XML candidate generation
- strict payload validation

Important: challenge/clearance encounters are diagnostic only. No clearance cookies, CAPTCHA state,
or anti-bot bypass state are replayed or admitted into native-feed verification.
"""

import asyncio
import gzip
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlsplit, quote

import httpx


async def ai_advisory(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Use the six configured external AI APIs as bounded advisory fallbacks.

    The advisory output can classify evidence or suggest candidate feed hypotheses.
    It never verifies a feed, bypasses access controls, or changes extraction authority.
    """
    provider_specs = [
        ("openrouter_free", "https://openrouter.ai/api/v1/chat/completions", "openrouter/free", "OPENROUTER"),
        ("groq", "https://api.groq.com/openai/v1/chat/completions", "openai/gpt-oss-120b", "GROQ"),
        ("gemini", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-3.8-flash", "GEMINI"),
        ("nvidia_nim", "https://integrate.api.nvidia.com/v1/chat/completions", "deepseek-ai/deepseek-v4.1-flash", "NVIDIA_NIM"),
        ("cohere_free", "https://api.cohere.ai/compatibility/v1/chat/completions", "command-a-plus-05-2026", "COHERE"),
        ("huggingface_free", "https://router.huggingface.co/v1/chat/completions", "openai/gpt-oss-120b", "HUGGINGFACE"),
    ]

    try:
        raw_config = json.loads(os.getenv("PROVIDER_KEYS_JSON", "{}") or "{}")
    except json.JSONDecodeError:
        raw_config = {}
    if not isinstance(raw_config, dict):
        raw_config = {}

    explicit_keys = {
        "nvidia_nim": os.getenv("NVIDIA_NIM_API_KEY", "").strip(),
        "cohere_free": os.getenv("COHERE_API_KEY", "").strip(),
        "huggingface_free": os.getenv("HF_TOKEN", "").strip(),
    }

    prompt = {
        "task": "Classify WooCommerce plugin evidence. Return JSON {family,confidence,why}. Advisory only; never invent verification.",
        "evidence": {
            "plugin_asset_slugs": evidence.get("plugin_asset_slugs", []),
            "namespaces": evidence.get("namespaces", []),
            "xhr_urls": evidence.get("xhr_urls", [])[:80],
            "http_api_namespaces": evidence.get("http_api_namespaces", []),
        },
    }

    outcomes: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=25) as client:
        for provider, endpoint, default_model, config_name in provider_specs:
            config = raw_config.get(provider) if isinstance(raw_config.get(provider), dict) else {}
            key = explicit_keys.get(provider, str(config.get("api_key") or "").strip())
            if not key:
                outcomes.append({"provider": provider, "outcome": "unconfigured"})
                continue

            model = str(config.get("model") or default_model).strip() or default_model
            if provider in {"nvidia_nim", "cohere_free", "huggingface_free"}:
                model = default_model

            started = time.monotonic()
            try:
                r = await client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "temperature": 0,
                        "max_tokens": 256,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": "Return only JSON. Advisory classification only; never claim feed existence or successful web access."},
                            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                        ],
                    },
                )
                latency_ms = max(0, int((time.monotonic() - started) * 1000))
                if r.status_code < 200 or r.status_code >= 300:
                    failure = "rate_limited" if r.status_code == 429 else "request_failed"
                    outcomes.append({"provider": provider, "outcome": failure, "status": r.status_code, "latency_ms": latency_ms})
                    continue

                body = r.json()
                content = body.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                result = json.loads(content)
                outcomes.append({"provider": provider, "outcome": "success", "status": r.status_code, "latency_ms": latency_ms})
                return {
                    "enabled": True,
                    "provider": provider,
                    "model": model,
                    "status": r.status_code,
                    "latency_ms": latency_ms,
                    "result": result,
                    "outcomes": outcomes,
                }
            except Exception as exc:
                outcomes.append({
                    "provider": provider,
                    "outcome": "temporary",
                    "latency_ms": max(0, int((time.monotonic() - started) * 1000)),
                    "error": type(exc).__name__,
                })

    return {
        "enabled": bool(outcomes),
        "provider": None,
        "model": None,
        "status": None,
        "latency_ms": None,
        "result": {},
        "outcomes": outcomes,
        "reason": "all_active_ai_providers_unavailable",
    }




# Backward-compatible name for existing callers/tests.
groq_advisory = ai_advisory


