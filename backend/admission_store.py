"""D1-backed public admission state using the existing Foundation database."""
from __future__ import annotations

from dataclasses import dataclass
from time import time
from typing import Any

from backend.admission import (
    AdmissionDecision,
    AdmissionOutcome,
    AdmissionPolicy,
    AdmissionRoute,
    AdmissionSnapshot,
    decide_admission,
)


ROUTE_COST_UNITS = {
    AdmissionRoute.CHEAP_READ: 1,
    AdmissionRoute.CHAT: 2,
    AdmissionRoute.RESEARCH: 5,
    AdmissionRoute.STREAM: 3,
}


@dataclass(frozen=True)
class AdmissionLease:
    event_id: str
    subject_fingerprint: str
    route: AdmissionRoute
    window_start: int
    expires_at: int
    cost_units: int


class D1AdmissionStore:
    def __init__(self, db: Any):
        self.db = db

    async def _snapshot(self, *, window_start: int, subject_fingerprint: str, now: int) -> AdmissionSnapshot:
        row = await self.db.prepare(
            """SELECT
                 (SELECT COUNT(*) FROM public_admission_events
                    WHERE window_start = ? AND subject_fingerprint = ?) AS subject_requests,
                 (SELECT COUNT(*) FROM public_admission_events
                    WHERE window_start = ?) AS global_requests,
                 (SELECT COUNT(*) FROM public_admission_events
                    WHERE subject_fingerprint = ?
                      AND released_at IS NULL
                      AND lease_expires_at > ?) AS subject_concurrent,
                 (SELECT COUNT(*) FROM public_admission_events
                    WHERE released_at IS NULL
                      AND lease_expires_at > ?) AS global_concurrent"""
        ).bind(
            window_start, subject_fingerprint,
            window_start,
            subject_fingerprint, now,
            now,
        ).first()

        def field(name: str) -> int:
            return int(row.get(name, 0) or 0) if isinstance(row, dict) else int(getattr(row, name, 0) or 0)

        return AdmissionSnapshot(
            authority_available=True,
            subject_requests=field("subject_requests"),
            global_requests=field("global_requests"),
            subject_concurrent=field("subject_concurrent"),
            global_concurrent=field("global_concurrent"),
        )

    async def _insert_if_admissible(
        self,
        *,
        event_id: str,
        window_start: int,
        subject_fingerprint: str,
        route: AdmissionRoute,
        cost_units: int,
        expires_at: int,
        now: int,
        policy: AdmissionPolicy,
    ) -> bool:
        result = await self.db.prepare(
            """INSERT INTO public_admission_events
                 (event_id, window_start, subject_fingerprint, route,
                  cost_units, lease_expires_at, released_at)
               SELECT ?, ?, ?, ?, ?, ?, NULL
               WHERE
                 (SELECT COUNT(*) FROM public_admission_events
                    WHERE window_start = ? AND subject_fingerprint = ?) < ?
                 AND (SELECT COUNT(*) FROM public_admission_events
                    WHERE window_start = ?) < ?
                 AND (SELECT COUNT(*) FROM public_admission_events
                    WHERE subject_fingerprint = ?
                      AND released_at IS NULL
                      AND lease_expires_at > ?) < ?
                 AND (SELECT COUNT(*) FROM public_admission_events
                    WHERE released_at IS NULL
                      AND lease_expires_at > ?) < ?"""
        ).bind(
            event_id, window_start, subject_fingerprint, route.value,
            cost_units, expires_at,
            window_start, subject_fingerprint, policy.max_requests_per_subject,
            window_start, policy.max_requests_global,
            subject_fingerprint, now, policy.max_concurrent_per_subject,
            now, policy.max_concurrent_global,
        ).run()
        meta = result.get("meta", {}) if isinstance(result, dict) else getattr(result, "meta", {})
        return int(meta.get("changes", 0) or 0) == 1

    async def acquire(
        self,
        *,
        subject_fingerprint: str,
        route: AdmissionRoute,
        policy: AdmissionPolicy,
        event_id: str,
        now: int | None = None,
    ) -> tuple[AdmissionDecision, AdmissionLease | None]:
        self._validate_identity(subject_fingerprint, event_id)
        policy.validate()
        now = int(time()) if now is None else now
        if now < 0:
            raise ValueError("now must be non-negative")

        window_start = now - (now % policy.window_seconds)
        expires_at = now + policy.window_seconds
        cost_units = ROUTE_COST_UNITS[route]

        await self.db.prepare(
            "DELETE FROM public_admission_events WHERE window_start < ?"
        ).bind(window_start - policy.window_seconds).run()

        snapshot = await self._snapshot(
            window_start=window_start,
            subject_fingerprint=subject_fingerprint,
            now=now,
        )
        decision = decide_admission(
            policy=policy,
            snapshot=snapshot,
            subject_fingerprint=subject_fingerprint,
            route=route,
        )
        if not decision.allowed:
            return decision, None

        inserted = await self._insert_if_admissible(
            event_id=event_id,
            window_start=window_start,
            subject_fingerprint=subject_fingerprint,
            route=route,
            cost_units=cost_units,
            expires_at=expires_at,
            now=now,
            policy=policy,
        )
        if not inserted:
            return AdmissionDecision(
                AdmissionOutcome.CONCURRENCY_LIMITED,
                route,
                False,
                "admission state changed concurrently; retry",
                policy.retry_after_seconds,
            ), None

        return decision, AdmissionLease(
            event_id=event_id,
            subject_fingerprint=subject_fingerprint,
            route=route,
            window_start=window_start,
            expires_at=expires_at,
            cost_units=cost_units,
        )

    @staticmethod
    def _validate_identity(subject_fingerprint: str, event_id: str) -> None:
        if not subject_fingerprint.strip():
            raise ValueError("subject_fingerprint is required")
        if not event_id.strip():
            raise ValueError("event_id is required")

    async def release(self, lease: AdmissionLease | None) -> None:
        if lease is None:
            return
        await self.db.prepare(
            "UPDATE public_admission_events SET released_at = ? WHERE event_id = ? AND released_at IS NULL"
        ).bind(int(time()), lease.event_id).run()
