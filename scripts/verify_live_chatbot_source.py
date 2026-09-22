from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
checks = {
    "anonymous chat flag": 'PUBLIC_CHAT_ANONYMOUS = "true"' in (ROOT/"wrangler.toml").read_text(),
    "anonymous chat helper": "def _anonymous_chat_enabled(env):" in (ROOT/"worker.py").read_text(),
    "backend token forwarding": "headers = _chat_headers(request, env)" in (ROOT/"worker.py").read_text(),
    "AI provider in release": 'CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"' in (ROOT/"scripts/production_release.sh").read_text(),
    "AI binding in release": 'binding = "AI"' in (ROOT/"scripts/production_release.sh").read_text(),
    "UI stop uses canonical canceller": "api.cancelActiveChat?.()" in (ROOT/"frontend/ux_enhancements.js").read_text(),
    "UI no global fetch override": "window.fetch = (input, init = {})" not in (ROOT/"frontend/ux_enhancements.js").read_text(),
}
failed=[name for name,ok in checks.items() if not ok]
print(checks)
if failed: raise SystemExit("verification failed: "+", ".join(failed))
