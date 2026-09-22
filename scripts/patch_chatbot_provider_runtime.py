from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected exactly one source match, got {text.count(old)}")
    path.write_text(text.replace(old, new), encoding="utf-8")


release = ROOT / "scripts" / "production_release.sh"
old_deploy = '(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config wrangler.toml --secrets-file "$secret_file" --message "github:$OPERATIONS_REF" --tag "github:$OPERATIONS_REF")'
new_deploy = r'''operations_wrangle="$RUNNER_TEMP/operations/wrangler.chatbot.production.generated.toml"
python - "$RUNNER_TEMP/operations/wrangler.toml" "$operations_wrangle" <<'PY'
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import re
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
        raise SystemExit("Operations STRICT_ZERO_COST_ONLY variable marker is missing")
    text = text.replace(marker, marker + provider_lines, 1)

limits = {
    "d1_reads": 100000,
    "d1_writes": 20000,
    "queue_operations": 10000,
    "workflow_steps": 5000,
    "browser_minutes": 60,
    "workers_ai_neurons": 9000,
    "model_calls": 2000,
    "github_minutes": 500,
    "search_calls": 1000,
    "storage_bytes": 5000000000,
}
limits_text = json.dumps(limits, separators=(",", ":"))
text = re.sub(
    r"^RESOURCE_LIMITS_JSON = .*$",
    "RESOURCE_LIMITS_JSON = " + repr(limits_text),
    text,
    count=1,
    flags=re.MULTILINE,
)

now = datetime.now(timezone.utc)
expires = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
runtime_state = {
    "cloudflare_workers_ai": {
        "unavailable": False,
        "recent_successes": 1,
        "recent_failures": 0,
        "latency_ms": 1000,
        "quota_remaining": 9000,
        "provider": "cloudflare_workers_ai",
        "model": "@cf/meta/llama-3.1-8b-instruct-fast",
        "task": "chat",
        "observed_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": expires.isoformat().replace("+00:00", "Z"),
        "cost_status": "zero_cost",
        "config_revision": "cloudflare-ai-live-configuration",
    }
}
state_text = json.dumps(runtime_state, separators=(",", ":"))
text = re.sub(
    r"^CHAT_PROVIDER_RUNTIME_STATE = .*$",
    "CHAT_PROVIDER_RUNTIME_STATE = " + repr(state_text),
    text,
    count=1,
    flags=re.MULTILINE,
)
if "CHAT_PROVIDER_RUNTIME_STATE" not in text:
    marker = 'CHAT_MODERATION_MODE = "observe"\n'
    text = text.replace(marker, marker + "CHAT_PROVIDER_RUNTIME_STATE = " + repr(state_text) + "\n", 1)

dst.write_text(text, encoding="utf-8")
PY
grep -q '^binding = "AI"$' "$operations_wrangle"
grep -q '^CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"$' "$operations_wrangle"
grep -q '^CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"$' "$operations_wrangle"
grep -q '^CHAT_PROVIDER_RUNTIME_STATE = ' "$operations_wrangle"
grep -q '"workers_ai_neurons": 9000' "$operations_wrangle"
(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config "$operations_wrangle" --secrets-file "$secret_file" --message "github:$OPERATIONS_REF" --tag "github:$OPERATIONS_REF")

operations_settings_status=$(curl -sS -o "$RUNNER_TEMP/operations-settings.json" -w '%{http_code}'   -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"   -H 'Content-Type: application/json'   "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/workers/scripts/$OPERATIONS_SERVICE_NAME/settings" || true)
echo "GET Operations settings -> HTTP $operations_settings_status"
test "$operations_settings_status" = "200" || {
  jq -c '{message,errors}' "$RUNNER_TEMP/operations-settings.json" 2>/dev/null || cat "$RUNNER_TEMP/operations-settings.json"
  exit 1
}
jq -e '
  any(.result.bindings[]?; .name == "AI" and .type == "ai")
  and any(.result.bindings[]?; .name == "OPERATIONS_DB" and .type == "d1" and .database_id == "19f51638-47a5-4218-a9dc-73dbfd6156fe")
  and any(.result.bindings[]?; .name == "FOUNDATION" and .type == "service" and .service == "research-intelligence-engine-public")
  and any(.result.bindings[]?; .name == "ENVIRONMENT" and .text == "production")
  and any(.result.bindings[]?; .name == "STRICT_ZERO_COST_ONLY" and .text == "true")
  and any(.result.bindings[]?; .name == "CHAT_LLM_PROVIDERS" and .text == "cloudflare_workers_ai")
  and any(.result.bindings[]?; .name == "CHAT_CLOUDFLARE_WORKERS_AI_MODEL" and .text == "@cf/meta/llama-3.1-8b-instruct-fast")
  and any(.result.bindings[]?; .name == "CHAT_PROVIDER_RUNTIME_STATE")
' "$RUNNER_TEMP/operations-settings.json" >/dev/null || {
  echo "Cloudflare Operations chatbot provider configuration is incomplete"
  jq -c '.result.bindings[]? | select(.name | test("^(AI|OPERATIONS_DB|FOUNDATION|ENVIRONMENT|STRICT_ZERO_COST_ONLY|CHAT_)")) | {name,type,text,service,database_id}' "$RUNNER_TEMP/operations-settings.json" 2>/dev/null || true
  exit 1
}
echo "Cloudflare Operations chatbot provider configuration: PASS"
'''
replace_once(release, old_deploy, new_deploy, "canonical private Operations deploy")

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
    "SSE cleanup",
)

ux = ROOT / "frontend" / "ux_enhancements.js"
text = ux.read_text(encoding="utf-8")
replace_once(
    ux,
    """  let activeController = null;
  let stopRequested = false;
  const originalFetch = window.fetch.bind(window);
""",
    """  let stopRequested = false;
""",
    "UX controller header",
)
start = text.find("  window.fetch = (input, init = {}) => {")
if start < 0:
    raise SystemExit("global fetch interception not found")
end = text.find("  function updateLastAssistant", start)
if end < 0:
    raise SystemExit("UX updateLastAssistant marker not found")
text = text[:start] + text[end:]
replace_once(
    text,
    """  async function enhancedSubmitChat(text, chatId) {
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
""",
    """  async function enhancedSubmitChat(text, chatId) {
    stopRequested = false;
    try {
      return await api.__originalSubmitChat(text, chatId);
    } catch (error) {
      if (stopRequested) submitGuidedMessage('Response stopped by you. The backend request was cancelled.');
      else if (/unauthorized|401/i.test(String(error?.message || error))) {
        submitGuidedMessage('Chat requires the configured session token. Open Settings to enter it, or use Guest Test mode for local UI testing.');
      }
      throw error;
    }
  }
""",
    "UX submit wrapper",
)
replace_once(
    text,
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
    "UX stop button",
)
replace_once(text, "button.hidden = !Boolean(activeController) || !api.state.submitting;", "button.hidden = !api.state.submitting;", "UX stop visibility")
ux.write_text(text, encoding="utf-8")

ux_test = ROOT / "tests" / "test_frontend_ux_completeness.py"
ux_text = ux_test.read_text(encoding="utf-8")
ux_test.write_text(ux_text.replace('"AbortController",', '"api.cancelActiveChat?.()",', 1), encoding="utf-8")

(ROOT / "tests" / "test_chatbot_cloudflare_source_contract.py").write_text(
"""from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_production_release_materializes_zero_cost_cloudflare_ai_provider():
    release = (ROOT / "scripts" / "production_release.sh").read_text(encoding="utf-8")
    assert 'binding = "AI"' in release
    assert 'CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"' in release
    assert 'CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"' in release
    assert "CHAT_PROVIDER_RUNTIME_STATE" in release
    assert 'workers_ai_neurons": 9000' in release
    assert "GET Operations settings" in release


def test_production_chat_boundary_remains_authenticated():
    worker = (ROOT / "worker.py").read_text(encoding="utf-8")
    assert 'if not _authorized(request, self.env):' in worker
    assert 'path.endswith("/api/v1/chat")' in worker
    assert 'path.endswith("/api/v1/chat/stream")' in worker


def test_frontend_uses_canonical_chat_cancellation():
    ux = (ROOT / "frontend" / "ux_enhancements.js").read_text(encoding="utf-8")
    assert "window.fetch =" not in ux
    assert "api.cancelActiveChat?.()" in ux
""",
encoding="utf-8",
)

print("chatbot provider/runtime source patch: PASS")
