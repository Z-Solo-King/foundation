#!/usr/bin/env python3
"""Synchronize validated provider configuration to GitHub and Cloudflare.

This utility is intended to run from a Foundation-owned, explicitly
permissioned workflow. It never installs dependencies at runtime and never
prints secret values.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from typing import Any

try:
    from nacl import encoding, public
except ImportError as exc:  # pragma: no cover - exercised by workflow bootstrap
    raise SystemExit(
        "PyNaCl is required; install the pinned workflow dependency before running this tool"
    ) from exc

GH_OWNER = os.environ.get("GITHUB_OWNER", "Z-Solo-King")
GH_REPO = os.environ.get("GITHUB_REPOSITORY_NAME", "foundation")
CF_SCRIPT_NAME = os.environ.get(
    "CLOUDFLARE_SCRIPT_NAME", "research-intelligence-engine-private"
)
KNOWN_PROVIDERS = {
    "groq": "GROQ",
    "gemini": "GEMINI",
    "cerebras": "CEREBRAS",
    "cloudflare_workers_ai": "CLOUDFLARE_WORKERS_AI",
    "openrouter_free": "OPENROUTER",
    "siliconflow": "SILICONFLOW",
    "mistral_free": "MISTRAL",
}


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"required environment variable is missing: {name}")
    return value


def _provider_config(value: Any, provider: str) -> tuple[str, str, str]:
    if not isinstance(value, Mapping):
        raise ValueError(f"provider '{provider}' must be an object")
    endpoint = value.get("endpoint")
    api_key = value.get("api_key")
    model = value.get("model")
    if not all(isinstance(item, str) and item.strip() for item in (endpoint, api_key, model)):
        raise ValueError(f"provider '{provider}' requires non-empty endpoint, api_key and model")
    if not endpoint.startswith("https://"):
        raise ValueError(f"provider '{provider}' endpoint must use HTTPS")
    return endpoint.strip(), api_key.strip(), model.strip()


def _json_request(method: str, url: str, headers: Mapping[str, str], body: Any = None) -> Any:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers=dict(headers))
    try:
        with urllib.request.urlopen(request) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"remote request failed: HTTP {exc.code} {method} {url}") from exc
    return json.loads(raw) if raw else {}


def gh_request(method: str, path: str, token: str, body: Any = None) -> Any:
    return _json_request(
        method,
        f"https://api.github.com{path}",
        {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
        body,
    )


def gh_set_secret(owner: str, repo: str, token: str, name: str, value: str) -> None:
    public_key = gh_request(
        "GET", f"/repos/{owner}/{repo}/actions/secrets/public-key", token
    )
    key = public.PublicKey(public_key["key"].encode("ascii"), encoding.Base64Encoder())
    encrypted = base64.b64encode(public.SealedBox(key).encrypt(value.encode("utf-8"))).decode("ascii")
    gh_request(
        "PUT",
        f"/repos/{owner}/{repo}/actions/secrets/{name}",
        token,
        {"encrypted_value": encrypted, "key_id": public_key["key_id"]},
    )
    print(f"[github/{repo}] set {name}")


def cf_set_secret(account_id: str, script_name: str, api_token: str, name: str, value: str) -> None:
    encoded_name = urllib.parse.quote(name, safe="")
    result = _json_request(
        "PUT",
        f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{script_name}/secrets/{encoded_name}",
        {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        },
        {"name": name, "text": value, "type": "secret_text"},
    )
    if result.get("success") is not True:
        raise RuntimeError(f"Cloudflare rejected secret update: {name}")
    print(f"[cloudflare/{script_name}] set {name}")


def main() -> int:
    gh_token = _required_env("GH_ADMIN_TOKEN")
    cf_token = _required_env("CF_API_TOKEN")
    cf_account = _required_env("CF_ACCOUNT_ID")
    raw = _required_env("PROVIDER_KEYS_JSON")
    providers = json.loads(raw)
    if not isinstance(providers, Mapping):
        raise ValueError("PROVIDER_KEYS_JSON must contain an object")

    prepared: list[tuple[str, str, str, str, str]] = []
    for provider, config in providers.items():
        if provider not in KNOWN_PROVIDERS:
            raise ValueError(f"unknown provider: {provider}")
        endpoint, api_key, model = _provider_config(config, provider)
        prepared.append((provider, KNOWN_PROVIDERS[provider], endpoint, api_key, model))
    if not prepared:
        raise ValueError("at least one provider must be configured")

    configured_order = []
    for provider, prefix, endpoint, api_key, model in prepared:
        print(f"Synchronizing provider: {provider}")
        for suffix, value in (("ENDPOINT", endpoint), ("API_KEY", api_key), ("MODEL", model)):
            gh_set_secret(GH_OWNER, GH_REPO, gh_token, f"RESEARCH_{prefix}_{suffix}", value)
            cf_set_secret(cf_account, CF_SCRIPT_NAME, cf_token, f"CHAT_{prefix}_{suffix}", value)
        configured_order.append(provider)

    provider_list = ",".join(configured_order)
    gh_set_secret(GH_OWNER, GH_REPO, gh_token, "RESEARCH_LLM_PROVIDERS", provider_list)
    cf_set_secret(cf_account, CF_SCRIPT_NAME, cf_token, "CHAT_LLM_PROVIDERS", provider_list)
    print(f"Completed synchronization for {len(configured_order)} provider(s)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
