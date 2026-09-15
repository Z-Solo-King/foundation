
async def _get_run(env, run_id):
    return await get_run(env, run_id)


async def _operations_chat(env, payload, request):
    """Proxy Heroic AI chat only through the configured private service binding.

    The public Worker never exposes a private Worker URL to the browser. When the
    binding is absent, the contract fails closed instead of inventing a browser-local
    assistant response.
    """
    operations = getattr(env, "OPERATIONS", None)
    if operations is None:
        return {"ok": False, "error": "chat_backend_unavailable", "status": "unavailable"}, 503
    headers = {"Content-Type": "application/json"}
    token = _bearer_token(request)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    try:
        upstream = await operations.fetch(
            "https://chat/v1/chat",
            {
                "method": "POST",
                "headers": headers,
                "body": json.dumps(payload),
            },
        )
        body = await upstream.json()
        if not isinstance(body, dict):
            return {"ok": False, "error": "invalid_private_chat_response"}, 503
        return body, upstream.status
    except Exception:
        return {"ok": False, "error": "chat_backend_unavailable"}, 503
