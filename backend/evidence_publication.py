"""Public publication boundary for signed, lineage-bound evidence packages."""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

SCHEMA = "evidence-package/v1"


def _canonical(package: dict[str, Any]) -> bytes:
    unsigned = {key: value for key, value in package.items() if key not in {"signature", "content_digest"}}
    return json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def package_digest(package: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(package)).hexdigest()


def package_signature(package: dict[str, Any], secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), _canonical(package), hashlib.sha256).hexdigest()


def verify_package(package: object, *, secret: str, run_id: str, observed_ids: set[str]) -> tuple[bool, str]:
    if not secret.strip():
        return False, "evidence package signing secret is not configured"
    if not isinstance(package, dict):
        return False, "evidence package must be a JSON object"
    if package.get("schema") != SCHEMA:
        return False, "unsupported evidence package schema"
    if package.get("run_id") != run_id:
        return False, "evidence package run_id does not match requested research run"
    digest = package.get("content_digest")
    signature = package.get("signature")
    if not isinstance(digest, str) or not hmac.compare_digest(digest, package_digest(package)):
        return False, "evidence package digest verification failed"
    if not isinstance(signature, str) or not hmac.compare_digest(signature, package_signature(package, secret)):
        return False, "evidence package signature verification failed"
    lineage = package.get("lineage")
    if not isinstance(lineage, dict):
        return False, "evidence package lineage is required"
    observation_ids = lineage.get("observation_ids")
    if not isinstance(observation_ids, list) or not observation_ids or not all(isinstance(item, str) for item in observation_ids):
        return False, "evidence package lineage must contain observation_ids"
    if not set(observation_ids).issubset(observed_ids):
        return False, "evidence package references observations outside the research run"
    claims = package.get("claims")
    if not isinstance(claims, list) or not claims:
        return False, "evidence package must contain claims"
    for claim in claims:
        if not isinstance(claim, dict) or not isinstance(claim.get("claim"), str) or not claim["claim"].strip():
            return False, "evidence package contains an invalid claim"
        evidence_ids = claim.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not evidence_ids or not set(evidence_ids).issubset(set(observation_ids)):
            return False, "every claim must be lineage-bound to package observations"
    return True, "verified"
