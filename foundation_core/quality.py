"""Deterministic plausibility checks over observed product facts."""
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from typing import Any

from .field_routing import route_field
from .normalization import normalize_specs


@dataclass(frozen=True)
class PlausibilitySignal:
    code: str
    severity: str
    field: str
    message: str
    action: str = "cross_check"


_NUM = re.compile(r"\d+(?:\.\d+)?")
_RULES_CACHE: tuple[Mapping[str, Any], ...] | None = None


def _num(value: object) -> float | None:
    match = _NUM.search(str(value or ""))
    return float(match.group(0)) if match else None


def _rules() -> tuple[Mapping[str, Any], ...]:
    global _RULES_CACHE
    if _RULES_CACHE is None:
        raw = resources.files("foundation_core").joinpath("quality_rules.json").read_text(encoding="utf-8")
        payload = json.loads(raw)
        if not isinstance(payload, dict) or not isinstance(payload.get("rules"), list):
            raise ValueError("quality_rules.json must contain a rules list")
        _RULES_CACHE = tuple(item for item in payload["rules"] if isinstance(item, Mapping))
    return _RULES_CACHE


def _matches(rule: Mapping[str, Any], *, category: str, panel: str, price: float, refresh: float | None, size: float | None) -> bool:
    when = rule.get("when")
    if not isinstance(when, Mapping):
        return False
    categories = when.get("category_contains", ())
    if categories and not any(str(token).casefold() in category for token in categories):
        return False
    panel_contains = when.get("panel_contains")
    if panel_contains and str(panel_contains).casefold() not in panel:
        return False
    if "price_lt" in when and not price < float(when["price_lt"]):
        return False
    if "refresh_gte" in when:
        if refresh is None or not refresh >= float(when["refresh_gte"]):
            return False
    if "size_gte" in when:
        if size is None or not size >= float(when["size_gte"]):
            return False
    return True


def evaluate_price_spec_plausibility(raw: Mapping[str, object]) -> tuple[PlausibilitySignal, ...]:
    """Evaluate versioned, data-defined plausibility rules without changing observed values."""
    price = _num(raw.get("price"))
    if price is None:
        routed_price = route_field(raw, "price")
        price = _num(routed_price.value) if routed_price is not None else None
    if price is None:
        return ()

    specs = normalize_specs(raw.get("specs"))
    category_field = route_field(raw, "category")
    title_field = route_field(raw, "title")
    category = " ".join(
        str(value or "").lower()
        for value in (
            category_field.value if category_field is not None else None,
            raw.get("product_type"),
            title_field.value if title_field is not None else None,
        )
    )
    panel = str(specs.get("panel") or specs.get("panel_type") or "").lower()
    refresh = _num(specs.get("refresh_rate") or specs.get("hz"))
    size = _num(specs.get("screen_size") or specs.get("display_size"))

    signals: list[PlausibilitySignal] = []
    for rule in _rules():
        if not _matches(rule, category=category, panel=panel, price=price, refresh=refresh, size=size):
            continue
        signals.append(
            PlausibilitySignal(
                str(rule["code"]),
                str(rule["severity"]),
                str(rule["field"]),
                str(rule["message"]),
                str(rule.get("action", "cross_check")),
            )
        )
    return tuple(signals)
