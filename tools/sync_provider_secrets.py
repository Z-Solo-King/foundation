#!/usr/bin/env python3
"""sync_provider_secrets.py

Fans out one JSON blob (PROVIDER_KEYS_JSON) of free-tier LLM provider
credentials to:
  - Foundation GitHub Actions secrets, as RESEARCH_<PROVIDER>_* (consumed by
    .github/workflows/nightly-multi-agent-research-v2.yml, which checks out
    the pinned Operations revision via the OPERATIONS_APP_ID GitHub App --
    Operations itself never runs GitHub Actions).
  - Cloudflare Worker secrets on research-intelligence-engine-private, as
    CHAT_<PROVIDER>_* (consumed by the live chatbot).

Also computes and pushes the priority-ordered provider list:
  - RESEARCH_LLM_PROVIDERS (Foundation GitHub secret)
  - CHAT_LLM_PROVIDERS      (Cloudflare secret)

Run this from a Foundation Actions workflow (Operations cannot run Actions).
"""
from __future__ import annotations
import base64, json, os, sys, urllib.request, urllib.error
try:
    from nacl import encoding, public
except ImportError:
    os.system(f"{sys.executable} -m pip install pynacl --break-system-packages -q")
    from nacl import encoding, public

GH_OWNER = "Z-Solo-King"
GH_REPO = "foundation"  # secrets target -- Operations has no Actions runtime
CF_SCRIPT_NAME = "research-intelligence-engine-private"
KNOWN_PROVIDERS = {
    "groq": "GROQ", "gemini": "GEMINI", "cerebras": "CEREBRAS",
    "cloudflare_workers_ai": "CLOUDFLARE_WORKERS_AI", "openrouter_free": "OPENROUTER",
    "siliconflow": "SILICONFLOW", "mistral_free": "MISTRAL",
}

def gh_request(method, path, token, body=None):
    url = f"https://api.github.com{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(req) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}

def gh_set_secret(owner, repo, token, name, value):
    pub_key = gh_request("GET", f"/repos/{owner}/{repo}/actions/secrets/public-key", token)
    key = public.PublicKey(pub_key["key"].encode(), encoding.Base64Encoder())
    encrypted = base64.b64encode(public.SealedBox(key).encrypt(value.encode())).decode()
    gh_request("PUT", f"/repos/{owner}/{repo}/actions/secrets/{name}", token,
               {"encrypted_value": encrypted, "key_id": pub_key["key_id"]})
    print(f"  [github/{repo}] set {name}")

def cf_set_secret(account_id, script_name, api_token, name, value):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/workers/scripts/{script_name}/secrets"
    body = json.dumps({"name": name, "text": value, "type": "secret_text"}).encode()
    req = urllib.request.Request(url, data=body, method="PUT", headers={
        "Authorization": f"Bearer {api_token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        print(f"  [cloudflare] {'set' if result.get('success') else 'FAILED'} {name}")

def main():
    gh_token = os.environ["GH_ADMIN_TOKEN"]
    cf_token = os.environ["CF_API_TOKEN"]
    cf_account = os.environ["CF_ACCOUNT_ID"]
    providers_json = json.loads(os.environ["PROVIDER_KEYS_JSON"])
    configured_order = []
    for provider_key, creds in providers_json.items():
        if provider_key not in KNOWN_PROVIDERS:
            print(f"WARNING: '{provider_key}' unknown provider, skipping.", file=sys.stderr)
            continue
        prefix = KNOWN_PROVIDERS[provider_key]
        endpoint, api_key, model = creds.get("endpoint", ""), creds.get("api_key", ""), creds.get("model", "")
        if not (endpoint and api_key and model):
            print(f"WARNING: '{provider_key}' missing fields, skipping.", file=sys.stderr)
            continue
        print(f"Syncing provider: {provider_key}")
        gh_set_secret(GH_OWNER, GH_REPO, gh_token, f"RESEARCH_{prefix}_ENDPOINT", endpoint)
        gh_set_secret(GH_OWNER, GH_REPO, gh_token, f"RESEARCH_{prefix}_API_KEY", api_key)
        gh_set_secret(GH_OWNER, GH_REPO, gh_token, f"RESEARCH_{prefix}_MODEL", model)
        cf_set_secret(cf_account, CF_SCRIPT_NAME, cf_token, f"CHAT_{prefix}_ENDPOINT", endpoint)
        cf_set_secret(cf_account, CF_SCRIPT_NAME, cf_token, f"CHAT_{prefix}_API_KEY", api_key)
        cf_set_secret(cf_account, CF_SCRIPT_NAME, cf_token, f"CHAT_{prefix}_MODEL", model)
        configured_order.append(provider_key)
    if not configured_order:
        print("No valid providers found.", file=sys.stderr)
        sys.exit(1)
    provider_list = ",".join(configured_order)
    print(f"Priority order: {provider_list}")
    gh_set_secret(GH_OWNER, GH_REPO, gh_token, "RESEARCH_LLM_PROVIDERS", provider_list)
    cf_set_secret(cf_account, CF_SCRIPT_NAME, cf_token, "CHAT_LLM_PROVIDERS", provider_list)
    print(f"\nDone. {len(configured_order)} provider(s) synced.")

if __name__ == "__main__":
    main()
