"""Deterministic target-product identity checks.

Identity matching is conservative: exact strong identifiers can establish a match,
while contradictory identifiers reject a candidate. Missing identity never becomes
positive evidence merely because a candidate appears near the requested product.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class IdentityDecision:
    accepted: bool
    matched_fields: tuple[str, ...] = ()
    conflicts: tuple[str, ...] = ()
    reason: str = ""


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip().casefold()
    return text or None


def _url(value: object) -> str | None:
    text = _text(value)
    if not text:
        return None
    parsed = urlsplit(text)
    if not parsed.scheme or not parsed.netloc:
        return text.rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), parsed.query, ""))


def _field(record: Mapping[str, object], name: str) -> str | None:
    value = record.get(name)
    if isinstance(value, Mapping):
        value = value.get("id") or value.get("value") or value.get("name")
    return _text(value)


def _identity(record: Mapping[str, object]) -> dict[str, str | None]:
    return {
        "url": _url(record.get("url") or record.get("product_url") or record.get("canonical_url")),
        "sku": _field(record, "sku"),
        "mpn": _field(record, "mpn"),
        "gtin": _field(record, "gtin") or _field(record, "gtin13") or _field(record, "gtin14") or _field(record, "gtin12"),
        "brand": _field(record, "brand"),
        "variant_id": _field(record, "variant_id") or _field(record, "variant") or _field(record, "id"),
        "title": _field(record, "title") or _field(record, "name") or _field(record, "product_name"),
    }


def identity_matches(target: Mapping[str, object], candidate: Mapping[str, object]) -> IdentityDecision:
    expected = _identity(target)
    observed = _identity(candidate)
    strong = ("sku", "mpn", "gtin", "variant_id")
    matched: list[str] = []
    conflicts: list[str] = []

    for field in ("url", *strong, "brand"):
        expected_value = expected[field]
        observed_value = observed[field]
        if expected_value and observed_value:
            if expected_value == observed_value:
                matched.append(field)
            else:
                conflicts.append(field)

    if conflicts:
        return IdentityDecision(False, tuple(matched), tuple(conflicts), "identity conflict")

    strong_matches = [field for field in strong if field in matched]
    if strong_matches:
        return IdentityDecision(True, tuple(matched), (), "exact identity match")

    if "url" in matched:
        return IdentityDecision(True, tuple(matched), (), "canonical URL match")

    title = expected["title"]
    if title and observed["title"] == title and expected["brand"] and observed["brand"] == expected["brand"]:
        return IdentityDecision(True, tuple(matched) + ("brand", "title"), (), "exact brand and title match")

    return IdentityDecision(False, tuple(matched), (), "insufficient identity evidence")
