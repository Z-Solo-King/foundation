        return {"ok": False, "error": "chat_backend_unavailable", "status": "unavailable"}, 503
    headers = _chat_headers(request)
    private_payload = dict(payload)
    # research_agent is private Operations capability; public ChatRequest stays closed.
    # Only an authenticated research-proof header may promote it at this boundary.
    if (
        request.headers.get("X-Heroic-Research-Proof") == "1"
        and _authorized(request, env)
        and private_payload.get("operation") == "knowledge"
    ):
        private_payload["research_agent"] = True
    try:
        upstream = await operations.fetch(
            _service_request(
                "https://chat/v1/chat",
                method="POST",
                headers=headers,
                body=json.dumps(private_payload),
                signal=getattr(request, "signal", None),
            )
        )
        body = await upstream.json()
        if not isinstance(body, dict):
            return {"ok": False, "error": "invalid_private_chat_response"}, 503
        include_provider = request.headers.get("X-Heroic-Research-Proof") == "1" and _authorized(request, env)
        return _public_chat_body(body, include_provider=include_provider), upstream.status
    except Exception as exc:
        return {"ok": False, "error": "chat_backend_unavailable"}, 503

