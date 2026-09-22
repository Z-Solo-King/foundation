from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOLLAR = "$"


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if text.count(old) != 1:
        raise SystemExit(f"{label}: source marker not found exactly once")
    path.write_text(text.replace(old, new), encoding="utf-8")


# Public Worker: anonymous chat admission + backend credential forwarding.
p = ROOT / "worker.py"
replace_once(
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
replace_once(
    p,
    """    headers = _chat_headers(request)
""",
    """    headers = _chat_headers(request, env)
""",
    "backend credential forwarding",
)
replace_once(
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
    "anonymous stream authorization",
)
replace_once(
    p,
    """            subject = authenticated_subject_fingerprint(request) or "development-local"
            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex
            decision, lease = await _public_admit(self.env, AdmissionRoute.STREAM, subject, event_id)
""",
    """            subject = _public_chat_subject(request) if anonymous else (authenticated_subject_fingerprint(request) or "development-local")
            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex
            decision, lease = await _public_admit(self.env, AdmissionRoute.STREAM, subject, event_id)
""",
    "anonymous stream subject",
)
replace_once(
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
    "anonymous chat authorization",
)
replace_once(
    p,
    """            subject = authenticated_subject_fingerprint(request) or "development-local"
            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex
            decision, lease = await _public_admit(self.env, AdmissionRoute.CHAT, subject, event_id)
""",
    """            subject = _public_chat_subject(request) if anonymous else (authenticated_subject_fingerprint(request) or "development-local")
            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex
            decision, lease = await _public_admit(self.env, AdmissionRoute.CHAT, subject, event_id)
""",
    "anonymous chat subject",
)

# Source-declare the public anonymous flag.
p = ROOT / "wrangler.toml"
text = p.read_text(encoding="utf-8")
if 'PUBLIC_CHAT_ANONYMOUS = "true"' not in text:
    text = text.replace(
        'STRICT_ZERO_COST_ONLY = "true"\n',
        'STRICT_ZERO_COST_ONLY = "true"\nPUBLIC_CHAT_ANONYMOUS = "true"\n',
        1,
    )
    p.write_text(text, encoding="utf-8")

# Canonical production release: keep the public flag and materialize the private AI
# binding/provider configuration into a generated Operations wrangler file.
p = ROOT / "scripts" / "production_release.sh"
text = p.read_text(encoding="utf-8")
if 'PUBLIC_CHAT_ANONYMOUS = "true"' not in text:
    text = text.replace(
        """  'STRICT_ZERO_COST_ONLY = "true"' \\
""",
        """  'STRICT_ZERO_COST_ONLY = "true"' \\
  'PUBLIC_CHAT_ANONYMOUS = "true"' \\
""",
        1,
    )
ops_ref = DOLLAR + "{OPERATIONS_REF}"
old_deploy = '(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config wrangler.toml --secrets-file "$secret_file" --message "github:' + ops_ref + '" --tag "github:' + ops_ref + '")'
if 'operations_wrangle="$RUNNER_TEMP/operations/wrangler.chatbot.production.generated.toml"' not in text:
    overlay_marker = '# Only the canonical private Operations deployment now follows the public asset smoke.\n'
    overlay = r'''operations_wrangle="$RUNNER_TEMP/operations/wrangler.chatbot.production.generated.toml"
python - "$RUNNER_TEMP/operations/wrangler.toml" "$operations_wrangle" <<'PY'
from pathlib import Path
import sys
src, dst = map(Path, sys.argv[1:])
text = src.read_text(encoding="utf-8")
if "[ai]" not in text:
    text = text.replace("preview_urls = false\n", "preview_urls = false\n\n[ai]\nbinding = \"AI\"\n", 1)
provider_lines = (
    'CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"\n'
    'CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"\n'
    'CHAT_MODERATION_MODE = "observe"\n'
)
if 'CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"' not in text:
    marker = 'STRICT_ZERO_COST_ONLY = "true"\n'
    if marker not in text:
        raise SystemExit("Operations wrangler vars marker missing")
    text = text.replace(marker, marker + provider_lines, 1)
dst.write_text(text, encoding="utf-8")
PY
grep -q '^binding = "AI"$' "$operations_wrangle"
grep -q '^CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"$' "$operations_wrangle"
grep -q '^CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"$' "$operations_wrangle"
'''
    if overlay_marker not in text:
        raise SystemExit("production release operations marker missing")
    text = text.replace(overlay_marker, overlay_marker + overlay, 1)
if old_deploy in text:
    new_deploy = '(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config "$operations_wrangle" --secrets-file "$secret_file" --message "github:' + ops_ref + '" --tag "github:' + ops_ref + '")'
    text = text.replace(old_deploy, new_deploy, 1)
p.write_text(text, encoding="utf-8")

# Frontend: use the original chat cancellation mechanism; do not monkey-patch fetch.
p = ROOT / "frontend" / "composer.js"
text = p.read_text(encoding="utf-8")
text = text.replace(
    "Chat uses the authenticated Heroic AI backend and canonical Operations routing.",
    "Chat uses the public governed Heroic AI endpoint; a session token is only needed for protected operational features.",
    1,
)
p.write_text(text, encoding="utf-8")

p = ROOT / "frontend" / "app.js"
replace_once(
    p,
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
    "SSE cleanup",
)

p = ROOT / "frontend" / "ux_enhancements.js"
text = p.read_text(encoding="utf-8")
if "window.fetch = (input, init = {})" in text:
    text = text.replace(
        """  let activeController = null;
  let stopRequested = false;
  const originalFetch = window.fetch.bind(window);
""",
        """  let stopRequested = false;
""",
        1,
    )
    start = text.find("  window.fetch = (input, init = {}) => {")
    end = text.find("  function updateLastAssistant", start)
    text = text[:start] + text[end:]
text = text.replace("button.hidden = !Boolean(activeController) || !api.state.submitting;", "button.hidden = !api.state.submitting;", 1)
text = text.replace(
    """    button.addEventListener('click', () => {
      if (!activeController) return;
      stopRequested = true;
      activeController.abort();
      button.hidden = true;
    });
""",
    """    button.addEventListener('click', () => {
      if (!api.state.submitting) return;
      stopRequested = true;
      api.cancelActiveChat?.();
      button.hidden = true;
    });
""",
    1,
)
text = text.replace(
    "This backend requires a session token. Open Settings to enter one, or enable Guest test mode to try Heroic AI locally without credentials.",
    "Public chat does not require a session token. Protected operational views still do.",
    1,
)
text = text.replace("activeController = new AbortController();\n", "", 1)
text = text.replace("    activeController = null;\n", "", 1)
p.write_text(text, encoding="utf-8")

print("live chatbot source synchronization: PASS")
