from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_production_release_delegates_operations_cloudflare_deploy_to_governed_helper():
    release = (ROOT / "scripts" / "production_release.sh").read_text(encoding="utf-8")
    helper = (ROOT / "scripts" / "deploy_operations_chatbot_config.sh").read_text(encoding="utf-8")
    assert 'deploy_operations_chatbot_config.sh' in release
    assert 'binding = "AI"' in helper
    assert 'CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"' in helper
    assert 'CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/meta/llama-3.1-8b-instruct-fast"' in helper
    assert 'CHAT_PROVIDER_RUNTIME_STATE' in helper
    assert 'workers_ai_neurons": 9000' in helper
    assert 'GET Operations settings -> HTTP' in helper


def test_production_chat_boundary_remains_authenticated():
    worker = (ROOT / "worker.py").read_text(encoding="utf-8")
    assert 'if not _authorized(request, self.env):' in worker
    assert 'path.endswith("/api/v1/chat")' in worker
    assert 'path.endswith("/api/v1/chat/stream")' in worker


def test_frontend_uses_canonical_chat_cancellation():
    ux = (ROOT / "frontend" / "ux_enhancements.js").read_text(encoding="utf-8")
    assert "window.fetch =" not in ux
    assert "api.cancelActiveChat?.()" in ux
