"async def _public_admit(env, route, subject_fingerprint, event_id):
    db = getattr(env, "DB", None)
    environment = str(getattr(env, "ENVIRONMENT", "production") or "production").casefold()
    local_bypass = str(getattr(env, "LOCAL_DEVELOPMENT_AUTH_BYPASS", "") or "").casefold() == "true"
    if db is None:
        if environment == "development" and local_bypass:
            return AdmissionDecision(
                AdmissionOutcome.ACCEPTED,
                route,
                True,
                "explicit local development admission bypass",
            ), None
        return AdmissionDecision(
            AdmissionOutcome.AUTHORITY_UNAVAILABLE,
            route,
            False,
            "admission authority is unavailable for a protected resource-consuming route",
            AdmissionPolicy().retry_after_seconds,
        ), None
    store = D1AdmissionStore(db)
    return await store.acquire(
        subject_fingerprint=subject_fingerprint,
        route=route,
        policy=AdmissionPolicy(),
        event_id=event_id,
    )


def _admission_response(decision):
    if decision.allowed:
        return None
    status = (
        429
        if decision.outcome in {
            AdmissionOutcome.RATE_LIMITED,
            AdmissionOutcome.CONCURRENCY_LIMITED,
            AdmissionOutcome.DUPLICATE,
        }
        else 503
    )
    response = _authenticated_json(
        {
            "ok": False,
            "error": decision.reason,
            "admission": decision.outcome.value,
            "contract_version": decision.contract_version,
        },
        status=status,
    )
    if decision.retry_after_header:
        response.headers["Retry-After"] = decision.retry_after_header
    return response


