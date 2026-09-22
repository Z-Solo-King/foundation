from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOLLAR = "$"


def ensure_replace(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one marker, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Public Worker anonymous governed chat.
p = ROOT / "worker.py"
ensure_replace(
    p,
    """def _chat_headers(request):
    headers = {"Content-Type": "application/json"}
    token = _bearer_token(request)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers
""",
    """def _chat_headers(request, env):
    headers = {"Content-Type": "application/json"}
    backend_token = str(getattr(env, "CHAT_BACKEND_TOKEN", "") or getattr(env, "AUTH_TOKEN", "") or "").strip()
    if backend_token:
        headers["Authorization"] = f"Bearer {backend_token}"
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    return headers


def _anonymous_chat_enabled(env):
    return str(getattr(env, "PUBLIC_CHAT_ANONYMOUS", "") or "").strip().casefold() == "true"


def _public_chat_subject(request):
    token_subject = authenticated_subject_fingerprint(request)
    if token_subject:
        return token_subject
    ip = str(request.headers.get("CF-Connecting-IP", "") or "anonymous").split(",", 1)[0].strip() or "anonymous"
    user_agent = str(request.headers.get("User-Agent", "") or "unknown")[:512]
    return hashlib.sha256(f"anonymous|{ip}|{user_agent}".encode("utf-8")).hexdigest()
""",
    "public chat helper",
)
ensure_replace(p, '    headers = _chat_headers(request)\n', '    headers = _chat_headers(request, env)\n', "private service credential forwarding")
ensure_replace(
    p,
    """        if request.method == "POST" and path.endswith("/api/v1/chat/stream"):
            if not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
""",
    """        if request.method == "POST" and path.endswith("/api/v1/chat/stream"):
            anonymous = _anonymous_chat_enabled(self.env)
            if not anonymous and not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
""",
    "anonymous stream route",
)
ensure_replace(
    p,
    '            subject = authenticated_subject_fingerprint(request) or "development-local"\n            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex\n            decision, lease = await _public_admit(self.env, AdmissionRoute.STREAM, subject, event_id)\n',
    '            subject = _public_chat_subject(request) if anonymous else (authenticated_subject_fingerprint(request) or "development-local")\n            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex\n            decision, lease = await _public_admit(self.env, AdmissionRoute.STREAM, subject, event_id)\n',
    "anonymous stream subject",
)
ensure_replace(
    p,
    """        if request.method == "POST" and path.endswith("/api/v1/chat"):
            if not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
""",
    """        if request.method == "POST" and path.endswith("/api/v1/chat"):
            anonymous = _anonymous_chat_enabled(self.env)
            if not anonymous and not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
""",
    "anonymous chat route",
)
ensure_replace(
    p,
    '            subject = authenticated_subject_fingerprint(request) or "development-local"\n            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex\n            decision, lease = await _public_admit(self.env, AdmissionRoute.CHAT, subject, event_id)\n',
    '            subject = _public_chat_subject(request) if anonymous else (authenticated_subject_fingerprint(request) or "development-local")\n            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex\n            decision, lease = await _public_admit(self.env, AdmissionRoute.CHAT, subject, event_id)\n',
    "anonymous chat subject",
)

# Public production config.
p = ROOT / "wrangler.toml"
ensure_replace(p, 'STRICT_ZERO_COST_ONLY = "true"\n', 'STRICT_ZERO_COST_ONLY = "true"\nPUBLIC_CHAT_ANONYMOUS = "true"\n', "public anonymous variable")

# Canonical Foundation deployment overlay for immutable Operations.
p = ROOT / "scripts" / "production_release.sh"
text = p.read_text(encoding="utf-8")
if 'PUBLIC_CHAT_ANONYMOUS = "true"' not in text:
    text = text.replace(
        '  \\'STRICT_ZERO_COST_ONLY = "true"\\' \\\\\\n',
        '  \\'STRICT_ZERO_COST_ONLY = "true"\\' \\\\\\n  \\'PUBLIC_CHAT_ANONYMOUS = "true"\\' \\\\\\n',
        1,
    )
if "wrangler.chatbot.production.generated.toml" not in text:
    ops_ref = DOLLAR + "{OPERATIONS_REF}"
    old_line = '(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config wrangler.toml --secrets-file "$secret_file" --message "github:' + ops_ref + '" --tag "github:' + ops_ref + '")'
    new_block = '''# Materialize the approved zero-cost chatbot configuration into the pinned private Operations tree.
operations_wrangle="$RUNNER_TEMP/operations/wrangler.chatbot.production.generated.toml"
python - "$RUNNER_TEMP/operations/wrangler.toml" "$operations_wrangle" "$RUNNER_TEMP/operations/worker.py" <<'PY'
from pathlib import Path
import sys
src, dst, worker = map(Path, sys.argv[1:])
text = src.read_text(encoding="utf-8")
if "[ai]" not in text:
    text = text.replace("preview_urls = false\\n", "preview_urls = false\\n\\n[ai]\\nbinding = \\"AI\\"\\n", 1)
provider_lines = (
    'CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"\\n'
    'CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"\\n'
    'CHAT_MODERATION_MODE = "observe"\\n'
)
if 'CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"' not in text:
    marker = 'STRICT_ZERO_COST_ONLY = "true"\\n'
    if marker not in text:
        raise SystemExit("Operations provider marker missing")
    text = text.replace(marker, marker + provider_lines, 1)
dst.write_text(text, encoding="utf-8")

ops = worker.read_text(encoding="utf-8")
if 'def _authorized_chat(request, env):' not in ops:
    ops = ops.replace('from urllib.parse import urlparse\\n', 'import hmac\\nfrom urllib.parse import urlparse\\n', 1)
    marker = 'from private.resource_governance_scheduler import reconcile_resource_governance\\n\\n\\nclass Default(WorkerEntrypoint):'
    replacement = 'from private.resource_governance_scheduler import reconcile_resource_governance\\n\\n\\ndef _authorized_chat(request, env):\\n    if authorized_request(request, env):\\n        return True\\n    expected = str(getattr(env, "CHAT_BACKEND_TOKEN", "") or "").strip()\\n    authorization = str(request.headers.get("Authorization", "") or "").strip()\\n    scheme, _, value = authorization.partition(" ")\\n    return bool(expected and scheme.casefold() == "bearer" and value and hmac.compare_digest(value.encode("utf-8"), expected.encode("utf-8")))\\n\\n\\nclass Default(WorkerEntrypoint):'
    if marker not in ops:
        raise SystemExit("Operations Worker marker missing")
    ops = ops.replace(marker, replacement, 1)
    route = '            if not authorized_request(request, self.env):\\n                return Response.json({"ok": False, "error": "unauthorized"}, status=401)'
    if route not in ops:
        raise SystemExit("Operations chat auth marker missing")
    ops = ops.replace(route, '            if not _authorized_chat(request, self.env):\\n                return Response.json({"ok": False, "error": "unauthorized"}, status=401)', 1)
    worker.write_text(ops, encoding="utf-8")
new_block = new_block.replace("github:OPSREF", "github:" + ops_ref)
if old_line not in text:
    raise SystemExit("Operations deploy command not found")
text = text.replace(old_line, new_block, 1)
p.write_text(text, encoding="utf-8")

# User-facing UI wording and safe SSE cleanup. Preserve the existing stop/AbortController implementation.
ensure_replace(ROOT / "frontend" / "composer.js",
               "Chat uses the authenticated Heroic AI backend and canonical Operations routing.",
               "Chat uses the public governed Heroic AI endpoint; a session token is only needed for protected operational features.",
               "composer chat wording")
ensure_replace(ROOT / "frontend" / "chat_view.js",
               "Session authentication is held only in session storage for this browser session.",
               "Protected operational features use a browser-session token; public chat does not require one.",
               "settings wording")
ensure_replace(ROOT / "frontend" / "ux_enhancements.js",
               "This backend requires a session token. Open Settings to enter one, or enable Guest test mode to try Heroic AI locally without credentials.",
               "Public chat does not require a session token. Protected operational views still do.",
               "auth error wording")
ensure_replace(ROOT / "frontend" / "app.js",
               """    buffer += decoder.decode();
    if (buffer.trim()) dispatch(buffer);
    if (signal) signal.removeEventListener('abort', onAbort);
""",
               """    try {
      buffer += decoder.decode();
      if (buffer.trim()) dispatch(buffer);
    } finally {
      if (signal) signal.removeEventListener('abort', onAbort);
    }
""",
               "SSE cleanup")

(ROOT / "tests" / "test_live_chatbot_contract.py").write_text(
"""from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_public_chat_uses_explicit_admission_flag():
    source = (ROOT / "worker.py").read_text(encoding="utf-8")
    assert "def _anonymous_chat_enabled(env):" in source
    assert "def _public_chat_subject(request):" in source
    assert "if not anonymous and not _authorized(request, self.env):" in source


def test_public_chat_uses_private_backend_credential():
    source = (ROOT / "worker.py").read_text(encoding="utf-8")
    assert "CHAT_BACKEND_TOKEN" in source
    assert "headers = _chat_headers(request, env)" in source


def test_release_contains_chatbot_provider_overlay():
    release = (ROOT / "scripts/production_release.sh").read_text(encoding="utf-8")
    assert 'PUBLIC_CHAT_ANONYMOUS = "true"' in release
    assert "wrangler.chatbot.production.generated.toml" in release
    assert 'CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"' in release
    assert 'CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"' in release
    assert 'binding = "AI"' in release
    assert 'def _authorized_chat(request, env):' in release


def test_ui_wording_matches_public_chat_capability():
    composer = (ROOT / "frontend/composer.js").read_text(encoding="utf-8")
    chat_view = (ROOT / "frontend/chat_view.js").read_text(encoding="utf-8")
    ux = (ROOT / "frontend/ux_enhancements.js").read_text(encoding="utf-8")
    assert "public governed Heroic AI endpoint" in composer
    assert "public chat does not require one." in chat_view
    assert "Public chat does not require a session token." in ux
""",
encoding="utf-8",
)
print("live chatbot source synchronization: PASS")
