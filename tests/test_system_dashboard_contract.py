from pathlib import Path


def test_dashboard_route_is_read_only_and_proxied():
    source = Path("worker.py").read_text(encoding="utf-8")
    assert 'path.endswith("/api/v1/dashboard")' in source
    assert 'await _operations_dashboard(self.env, request)' in source
    assert 'request.method == "GET"' in source


def test_dashboard_ui_is_present():
    html = Path("frontend/index.html").read_text(encoding="utf-8")
    js = Path("frontend/dashboard.js").read_text(encoding="utf-8")
    css = Path("frontend/dashboard.css").read_text(encoding="utf-8")
    assert 'data-action="open-system-dashboard"' in html
    assert 'api/v1/dashboard' in js
    assert 'system-dashboard' in css


def test_dashboard_does_not_store_provider_secrets_in_frontend():
    js = Path("frontend/dashboard.js").read_text(encoding="utf-8")
    html = Path("frontend/index.html").read_text(encoding="utf-8")
    forbidden = {"GITHUB_DASHBOARD_TOKEN", "CLOUDFLARE_DASHBOARD_TOKEN", "B2_DASHBOARD_APPLICATION_KEY"}
    assert not any(secret in js or secret in html for secret in forbidden)
