from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks = {
    "anonymous flag": 'PUBLIC_CHAT_ANONYMOUS = "true"' in (ROOT/"wrangler.toml").read_text(),
    "anonymous helper": "def _anonymous_chat_enabled(env):" in (ROOT/"worker.py").read_text(),
    "backend header": "headers = _chat_headers(request, env)" in (ROOT/"worker.py").read_text(),
    "provider": 'CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"' in (ROOT/"scripts/production_release.sh").read_text(),
    "AI model": 'CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"' in (ROOT/"scripts/production_release.sh").read_text(),
    "AI binding": 'binding = "AI"' in (ROOT/"scripts/production_release.sh").read_text(),
    "canonical cancellation": "api.cancelActiveChat?.()" in (ROOT/"frontend/ux_enhancements.js").read_text(),
    "no fetch monkeypatch": "window.fetch = (input, init = {})" not in (ROOT/"frontend/ux_enhancements.js").read_text(),
}
failed=[name for name,ok in checks.items() if not ok]
if failed: raise SystemExit("verification failed: "+", ".join(failed))
print(checks)
