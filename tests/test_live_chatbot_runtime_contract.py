import ast
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _source():
    return (ROOT / "worker.py").read_text(encoding="utf-8")


def test_chat_headers_backend_token_contract_is_present():
    source = _source()
    tree = ast.parse(source)
    names = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert "_chat_headers" in names
    assert "_anonymous_chat_enabled" in names
    assert "_public_chat_subject" in names
    assert 'CHAT_BACKEND_TOKEN' in source
    assert 'headers = _chat_headers(request, env)' in source


def test_anonymous_chat_routes_are_admission_controlled():
    source = _source()
    assert 'if not anonymous and not _authorized(request, self.env):' in source
    assert 'AdmissionRoute.CHAT' in source
    assert 'AdmissionRoute.STREAM' in source
    assert '_public_chat_subject(request) if anonymous' in source


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
