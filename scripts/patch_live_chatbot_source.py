from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOLLAR = "$"


def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{label}: exact source marker not found once")
    path.write_text(text.replace(old, new), encoding="utf-8")


p = ROOT / "worker.py"
replace_once(p,
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
""","public chat auth helpers")
replace_once(p,'    headers = _chat_headers(request)\n','    headers = _chat_headers(request, env)\n',"backend credential forwarding")
replace_once(p,
"""        if request.method == "POST" and path.endswith("/api/v1/chat/stream"):
            if not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
""",
"""        if request.method == "POST" and path.endswith("/api/v1/chat/stream"):
            anonymous = _anonymous_chat_enabled(self.env)
            if not anonymous and not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
""","anonymous stream auth")
replace_once(p,
'            subject = authenticated_subject_fingerprint(request) or "development-local"\n            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex\n            decision, lease = await _public_admit(self.env, AdmissionRoute.STREAM, subject, event_id)\n',
'            subject = _public_chat_subject(request) if anonymous else (authenticated_subject_fingerprint(request) or "development-local")\n            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex\n            decision, lease = await _public_admit(self.env, AdmissionRoute.STREAM, subject, event_id)\n',"anonymous stream subject")
replace_once(p,
"""        if request.method == "POST" and path.endswith("/api/v1/chat"):
            if not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
""",
"""        if request.method == "POST" and path.endswith("/api/v1/chat"):
            anonymous = _anonymous_chat_enabled(self.env)
            if not anonymous and not _authorized(request, self.env):
                return _authenticated_json({"ok": False, "error": "unauthorized"}, status=401)
""","anonymous chat auth")
replace_once(p,
'            subject = authenticated_subject_fingerprint(request) or "development-local"\n            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex\n            decision, lease = await _public_admit(self.env, AdmissionRoute.CHAT, subject, event_id)\n',
'            subject = _public_chat_subject(request) if anonymous else (authenticated_subject_fingerprint(request) or "development-local")\n            event_id = request.headers.get("Idempotency-Key") or req.request_id or uuid.uuid4().hex\n            decision, lease = await _public_admit(self.env, AdmissionRoute.CHAT, subject, event_id)\n',"anonymous chat subject")

p = ROOT / "wrangler.toml"
text = p.read_text(encoding="utf-8")
if 'PUBLIC_CHAT_ANONYMOUS = "true"' not in text:
    text = text.replace('STRICT_ZERO_COST_ONLY = "true"\n','STRICT_ZERO_COST_ONLY = "true"\nPUBLIC_CHAT_ANONYMOUS = "true"\n',1)
p.write_text(text, encoding="utf-8")

p = ROOT / "scripts" / "production_release.sh"
text = p.read_text(encoding="utf-8")
if 'PUBLIC_CHAT_ANONYMOUS = "true"' not in text:
    text = text.replace('  \'STRICT_ZERO_COST_ONLY = "true"\' \\\n','  \'STRICT_ZERO_COST_ONLY = "true"\' \\\n  \'PUBLIC_CHAT_ANONYMOUS = "true"\' \\\n',1)
ops_ref = DOLLAR + "{OPERATIONS_REF}"
old = '(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config wrangler.toml --secrets-file "$secret_file" --message "github:' + ops_ref + '" --tag "github:' + ops_ref + '")'
new = r'''operations_wrangle="$RUNNER_TEMP/operations/wrangler.chatbot.production.generated.toml"
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
    text = text.replace(marker, marker + provider_lines, 1)
dst.write_text(text, encoding="utf-8")
PY
grep -q '^binding = "AI"$' "$operations_wrangle"
grep -q '^CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"$' "$operations_wrangle"
grep -q '^CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"$' "$operations_wrangle"
(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config "$operations_wrangle" --secrets-file "$secret_file" --message "github:OPSREF" --tag "github:OPSREF")'''.replace("github:OPSREF", "github:" + ops_ref)
replace_once(p,old,new,"Operations production chatbot overlay")
p.write_text(text,encoding="utf-8")

p = ROOT / "frontend" / "composer.js"
text = p.read_text(encoding="utf-8")
text = text.replace("Chat uses the authenticated Heroic AI backend and canonical Operations routing.","Chat uses the public governed Heroic AI endpoint; a session token is only needed for protected operational features.",1)
p.write_text(text,encoding="utf-8")

p = ROOT / "frontend" / "app.js"
text = p.read_text(encoding="utf-8")
replace_once(p,
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
""","SSE cleanup")
p.write_text(text,encoding="utf-8")

p = ROOT / "frontend" / "ux_enhancements.js"
text = p.read_text(encoding="utf-8")
replace_once(p,"""  let activeController = null;
  let stopRequested = false;
  const originalFetch = window.fetch.bind(window);
""","""  let stopRequested = false;
""","UX fetch controller")
start = text.find("  window.fetch = (input, init = {}) => {")
if start < 0: raise SystemExit("UX fetch override missing")
end = text.find("  function updateLastAssistant", start)
if end < 0: raise SystemExit("UX marker missing")
text = text[:start] + text[end:]
replace_once(p,"""  async function enhancedSubmitChat(text, chatId) {
    stopRequested = false;
    activeController = new AbortController();
    try {
      return await api.__originalSubmitChat(text, chatId);
    } catch (error) {
      if (stopRequested) submitGuidedMessage('Response stopped by you. The backend request was cancelled.');
      else if (/unauthorized|401/i.test(String(error?.message || error))) {
        submitGuidedMessage('This backend requires a session token. Open Settings to enter one, or enable Guest test mode to try Heroic AI locally without credentials.');
      }
      throw error;
    } finally {
      activeController = null;
    }
  }
""","""  async function enhancedSubmitChat(text, chatId) {
    stopRequested = false;
    try {
      return await api.__originalSubmitChat(text, chatId);
    } catch (error) {
      if (stopRequested) submitGuidedMessage('Response stopped by you. The backend request was cancelled.');
      else if (/unauthorized|401/i.test(String(error?.message || error))) {
        submitGuidedMessage('Public chat does not require a session token. The protected backend surface may still be unavailable; check Backend status and retry.');
      }
      throw error;
    }
  }
""","UX submit wrapper")
replace_once(p,"""    button.addEventListener('click', () => {
      if (!activeController) return;
      stopRequested = true;
      activeController.abort();
      button.hidden = true;
    });
""","""    button.addEventListener('click', () => {
      if (!api.state.submitting) return;
      stopRequested = true;
      api.cancelActiveChat?.();
      button.hidden = true;
    });
""","UX stop")
replace_once(p,"button.hidden = !Boolean(activeController) || !api.state.submitting;","button.hidden = !api.state.submitting;","UX stop visibility")
p.write_text(text.replace("This backend requires a session token. Open Settings to enter one, or enable Guest test mode to try Heroic AI locally without credentials.","Public chat does not require a session token. Protected operational views still do.",1),encoding="utf-8")

(ROOT / "tests" / "test_live_chatbot_contract.py").write_text("""from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_public_chat_is_explicitly_anon_admission_controlled():
    source = (ROOT / "worker.py").read_text(encoding="utf-8")
    assert "def _anonymous_chat_enabled(env):" in source
    assert "def _public_chat_subject(request):" in source
    assert "if not anonymous and not _authorized(request, self.env):" in source
    assert "AdmissionRoute.CHAT" in source
    assert "AdmissionRoute.STREAM" in source


def test_public_chat_forwards_backend_credential():
    source = (ROOT / "worker.py").read_text(encoding="utf-8")
    assert 'backend_token = str(getattr(env, "CHAT_BACKEND_TOKEN", "") or getattr(env, "AUTH_TOKEN", "") or "").strip()' in source
    assert "headers = _chat_headers(request, env)" in source


def test_production_chat_provider_and_public_mode_are_source_declared():
    public = (ROOT / "wrangler.toml").read_text(encoding="utf-8")
    release = (ROOT / "scripts" / "production_release.sh").read_text(encoding="utf-8")
    assert 'PUBLIC_CHAT_ANONYMOUS = "true"' in public
    assert 'PUBLIC_CHAT_ANONYMOUS = "true"' in release
    assert 'CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"' in release
    assert 'CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"' in release
    assert '[ai]' in release
    assert 'binding = "AI"' in release


def test_ui_stop_control_uses_the_canonical_chat_canceller():
    ux = (ROOT / "frontend" / "ux_enhancements.js").read_text(encoding="utf-8")
    assert "window.fetch =" not in ux
    assert "api.cancelActiveChat?.()" in ux
    assert "Public chat does not require a session token." in ux
""",encoding="utf-8")
print("live chatbot source synchronization: PASS")
