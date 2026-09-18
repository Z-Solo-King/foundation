import asyncio
from pathlib import Path
from types import SimpleNamespace


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


def test_dashboard_proxy_fails_closed_without_binding():
    import worker
    class Request: headers = {}
    payload, status = asyncio.run(worker._operations_dashboard(SimpleNamespace(), Request()))
    assert status == 503
    assert payload["error"] == "dashboard_backend_unavailable"


def test_dashboard_proxy_forwards_auth_and_returns_payload():
    import worker
    class Response:
        status = 200
        async def json(self): return {"ok": True, "schema": "heroic-ai-ops-dashboard/v1", "status": "ok"}
    class Binding:
        def __init__(self): self.calls = []
        async def fetch(self, request): self.calls.append(request); return Response()
    class Request: headers = {"Authorization": "Bearer dashboard"}
    binding = Binding()
    payload, status = asyncio.run(worker._operations_dashboard(SimpleNamespace(OPERATIONS=binding), Request()))
    assert status == 200
    assert payload["schema"] == "heroic-ai-ops-dashboard/v1"
    request = binding.calls[0]
    assert request.url == "https://private/v1/dashboard"
    assert request.method == "GET"
    assert request.headers.get("Authorization") == "Bearer dashboard"


def test_dashboard_proxy_rejects_invalid_private_response():
    import worker
    class Response:
        status = 200
        async def json(self): return ["invalid"]
    class Binding:
        async def fetch(self, request): return Response()
    class Request: headers = {}
    payload, status = asyncio.run(worker._operations_dashboard(SimpleNamespace(OPERATIONS=Binding()), Request()))
    assert status == 503
    assert payload["error"] == "invalid_private_dashboard_response"


def test_dashboard_proxy_handles_binding_error():
    import worker
    class Binding:
        async def fetch(self, request): raise RuntimeError("binding unavailable")
    class Request: headers = {}
    payload, status = asyncio.run(worker._operations_dashboard(SimpleNamespace(OPERATIONS=Binding()), Request()))
    assert status == 503
    assert payload["error"] == "dashboard_backend_unavailable"


def test_public_worker_dashboard_route_requires_auth_and_proxies():
    import worker
    class Request:
        def __init__(self, headers):
            self.method = "GET"; self.url = "https://example/api/v1/dashboard"; self.headers = headers
    class Response:
        status = 200
        async def json(self): return {"ok": True, "status": "ok"}
    class Binding:
        async def fetch(self, url, options): return Response()
    unauthorized = worker.Default(); unauthorized.env = SimpleNamespace(AUTH_TOKEN="secret", OPERATIONS=Binding())
    response = asyncio.run(unauthorized.fetch(Request({}))); assert response.status == 401
    authorized = worker.Default(); authorized.env = SimpleNamespace(ENVIRONMENT="development", AUTH_TOKEN=None, LOCAL_DEVELOPMENT_AUTH_BYPASS="true", OPERATIONS=Binding())
    response = asyncio.run(authorized.fetch(Request({}))); assert response.status == 200
