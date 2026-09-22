from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact source marker, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


worker = ROOT / "worker.py"
replace_once(
    worker,
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
    backend_token = str(
        getattr(env, "CHAT_BACKEND_TOKEN", "")
        or getattr(env, "AUTH_TOKEN", "")
        or ""
    ).strip()
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
    "public chat auth helpers",
)
replace_once(
    worker,
    "    headers = _chat_headers(request)\n",
    "    headers = _chat_headers(request, env)\n",
    "backend credential forwarding",
)
replace_once(
    worker,
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
    worker,
    '            subject = authenticated_subject_fingerprint(request) or "development-local"\n'
    '            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex\n'
    '            decision, lease = await _public_admit(self.env, AdmissionRoute.STREAM, subject, event_id)\n',
    '            subject = _public_chat_subject(request) if anonymous else (authenticated_subject_fingerprint(request) or "development-local")\n'
    '            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex\n'
    '            decision, lease = await _public_admit(self.env, AdmissionRoute.STREAM, subject, event_id)\n',
    "anonymous stream subject",
)
replace_once(
    worker,
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
    worker,
    '            subject = authenticated_subject_fingerprint(request) or "development-local"\n'
    '            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex\n'
    '            decision, lease = await _public_admit(self.env, AdmissionRoute.CHAT, subject, event_id)\n',
    '            subject = _public_chat_subject(request) if anonymous else (authenticated_subject_fingerprint(request) or "development-local")\n'
    '            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex\n'
    '            decision, lease = await _public_admit(self.env, AdmissionRoute.CHAT, subject, event_id)\n',
    "anonymous chat subject",
)

public_wrangler = ROOT / "wrangler.toml"
text = public_wrangler.read_text(encoding="utf-8")
if 'PUBLIC_CHAT_ANONYMOUS = "true"' not in text:
    marker = 'STRICT_ZERO_COST_ONLY = "true"\n'
    if marker not in text:
        raise SystemExit("public wrangler policy marker missing")
    public_wrangler.write_text(text.replace(marker, marker + 'PUBLIC_CHAT_ANONYMOUS = "true"\n', 1), encoding="utf-8")

release = ROOT / "scripts" / "production_release.sh"
text = release.read_text(encoding="utf-8")
if 'PUBLIC_CHAT_ANONYMOUS = "true"' not in text:
    marker = """  'STRICT_ZERO_COST_ONLY = "true"' \\
"""
    if marker not in text:
        raise SystemExit("production public-vars marker missing")
    text = text.replace(marker, marker + """  'PUBLIC_CHAT_ANONYMOUS = "true"' \\
""", 1)

if 'wrangler.chatbot.production.generated.toml' not in text:
    marker = '# Only the canonical private Operations deployment now follows the public asset smoke.\n'
    if marker not in text:
        raise SystemExit("production Operations marker missing")
    overlay = r'''# Only the canonical private Operations deployment now follows the public asset smoke.
# Operations remains workflow-free; Foundation materializes the approved chatbot
# AI binding/provider configuration in the canonical production release.
npx --yes wrangler@4.131.1 d1 execute research-intelligence --remote \
  --file="$RUNNER_TEMP/operations/docs/RESOURCE_GOVERNANCE_D1_SCHEMA.sql" \
  --config="$RUNNER_TEMP/operations/wrangler.toml"
secret_file="$RUNNER_TEMP/operations-secrets.env"
printf 'AUTH_TOKEN=%s\n' "$AUTH_TOKEN" > "$secret_file"

operations_wrangle="$RUNNER_TEMP/operations/wrangler.chatbot.production.generated.toml"
python - "$RUNNER_TEMP/operations/wrangler.toml" "$operations_wrangle" <<'PY'
from pathlib import Path
import sys
src, dst = map(Path, sys.argv[1:])
text = src.read_text(encoding="utf-8")
if "[ai]" not in text:
    text = text.replace(
        "preview_urls = false\n",
        "preview_urls = false\n\n[ai]\nbinding = \"AI\"\n",
        1,
    )
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
grep -q '^CHAT_MODERATION_MODE = "observe"$' "$operations_wrangle"
(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config "$operations_wrangle" --secrets-file "$secret_file" --message "github:$OPERATIONS_REF" --tag "github:$OPERATIONS_REF")
# Fail closed unless the active Cloudflare Operations deployment points to the
# version carrying the exact canonical GitHub provenance annotation.
'''
    text = text.replace(marker, overlay, 1)
release.write_text(text, encoding="utf-8")

composer = ROOT / "frontend" / "composer.js"
text = composer.read_text(encoding="utf-8")
composer.write_text(
    text.replace(
        "Chat uses the authenticated Heroic AI backend and canonical Operations routing.",
        "Chat uses the public governed Heroic AI endpoint; a session token is only needed for protected operational features.",
        1,
    ),
    encoding="utf-8",
)

app = ROOT / "frontend" / "app.js"
replace_once(
    app,
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
    "SSE decoder cleanup",
)

ux = ROOT / "frontend" / "ux_enhancements.js"
text = ux.read_text(encoding="utf-8")
if "window.fetch = (input, init = {}) => {" in text:
    start = text.index("  window.fetch = (input, init = {}) => {")
    end = text.index("  function updateLastAssistant", start)
    text = text[:start] + text[end:]
text = text.replace("  let activeController = null;\n", "", 1)
text = text.replace("  const originalFetch = window.fetch.bind(window);\n", "", 1)
text = text.replace(
    """  async function enhancedSubmitChat(text, chatId) {
    stopRequested = false;
    activeController = new AbortController();
    try {
""",
    """  async function enhancedSubmitChat(text, chatId) {
    stopRequested = false;
    try {
""",
    1,
)
text = text.replace(
    "This backend requires a session token. Open Settings to enter one, or enable Guest test mode to try Heroic AI locally without credentials.",
    "Public chat does not require a session token. Protected operational views still do.",
    1,
)
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
    "button.hidden = !Boolean(activeController) || !api.state.submitting;",
    "button.hidden = !api.state.submitting;",
    1,
)
ux.write_text(text, encoding="utf-8")

checks = [
    ("worker.py", "def _anonymous_chat_enabled(env):"),
    ("worker.py", "def _public_chat_subject(request):"),
    ("worker.py", "if not anonymous and not _authorized(request, self.env):"),
    ("worker.py", "headers = _chat_headers(request, env)"),
    ("wrangler.toml", 'PUBLIC_CHAT_ANONYMOUS = "true"'),
    ("scripts/production_release.sh", 'CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"'),
    ("scripts/production_release.sh", 'CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"'),
    ("scripts/production_release.sh", 'binding = "AI"'),
    ("frontend/ux_enhancements.js", "api.cancelActiveChat?.()"),
    ("frontend/ux_enhancements.js", "Public chat does not require a session token."),
]
for rel, needle in checks:
    if needle not in (ROOT / rel).read_text(encoding="utf-8"):
        raise SystemExit(f"post-patch contract missing: {rel}: {needle}")

print("live chatbot source synchronization: PASS")
