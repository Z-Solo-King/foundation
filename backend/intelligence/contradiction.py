from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import NamedTuple


@dataclass(frozen=True)
class Contradiction:
    claim_a: str
    claim_b: str
    reason: str
    predicate: str | None = None


@dataclass(frozen=True)
class TypedClaim:
    claim_id: str
    entity: str
    predicate: str
    value: object
    value_type: str
    scope: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    unit: str | None = None
    qualifier: str | None = None
    version: str | None = None
    tolerance: Decimal = Decimal("0")
    negated: bool = False


class NormalizedQuantity(NamedTuple):
    value: Decimal
    dimension: str
    unit: str


_UNIT_FACTORS: dict[str, tuple[str, Decimal]] = {
    "mg": ("mass", Decimal("0.000001")),
    "g": ("mass", Decimal("0.001")),
    "kg": ("mass", Decimal("1")),
    "lb": ("mass", Decimal("0.45359237")),
    "mm": ("length", Decimal("0.001")),
    "cm": ("length", Decimal("0.01")),
    "m": ("length", Decimal("1")),
    "in": ("length", Decimal("0.0254")),
    "inch": ("length", Decimal("0.0254")),
    "ml": ("volume", Decimal("0.001")),
    "l": ("volume", Decimal("1")),
}


def _numeric(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def normalize_quantity(value: object, unit: str | None) -> NormalizedQuantity | None:
    number = _numeric(value)
    if number is None or not unit:
        return None
    key = unit.strip().casefold()
    spec = _UNIT_FACTORS.get(key)
    if spec is None:
        return None
    dimension, factor = spec
    return NormalizedQuantity(number * factor, dimension, key)


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _scopes_overlap(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return True
    return left.strip().casefold() == right.strip().casefold()


def _validity_overlap(left: TypedClaim, right: TypedClaim) -> bool:
    if left.valid_until and right.valid_from and left.valid_until < right.valid_from:
        return False
    if right.valid_until and left.valid_from and right.valid_until < left.valid_from:
        return False
    return True


def _numeric_conflict(left: TypedClaim, right: TypedClaim) -> bool:
    if left.tolerance < 0 or right.tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    a = normalize_quantity(left.value, left.unit) if left.unit else None
    b = normalize_quantity(right.value, right.unit) if right.unit else None
    if a and b:
        if a.dimension != b.dimension:
            return False
        tolerance = max(left.tolerance, right.tolerance)
        return abs(a.value - b.value) > tolerance
    raw_a, raw_b = _numeric(left.value), _numeric(right.value)
    if raw_a is None or raw_b is None or left.unit != right.unit:
        return False
    return abs(raw_a - raw_b) > max(left.tolerance, right.tolerance)


def detect_typed_contradiction(left: TypedClaim, right: TypedClaim) -> Contradiction | None:
    if left.entity.strip().casefold() != right.entity.strip().casefold():
        return None
    if left.predicate.strip().casefold() != right.predicate.strip().casefold():
        return None
    if left.version and right.version and left.version != right.version:
        return None
    if not _scopes_overlap(left.scope, right.scope) or not _validity_overlap(left, right):
        return None
    if left.negated != right.negated:
        return Contradiction(left.claim_id, right.claim_id, "explicit negation conflict", left.predicate)

    if left.value_type == right.value_type == "numeric":
        if _numeric_conflict(left, right):
            return Contradiction(left.claim_id, right.claim_id, "numeric values differ beyond tolerance", left.predicate)

    if left.value_type == right.value_type == "date":
        a, b = _as_date(left.value), _as_date(right.value)
        if a is not None and b is not None and a != b:
            return Contradiction(left.claim_id, right.claim_id, "dates differ", left.predicate)

    if left.value_type in {"enum", "boolean"} and right.value_type == left.value_type:
        if str(left.value).strip().casefold() != str(right.value).strip().casefold():
            return Contradiction(left.claim_id, right.claim_id, "mutually exclusive categorical values", left.predicate)

    if left.value_type == right.value_type == "quantity" and _numeric_conflict(left, right):
        return Contradiction(left.claim_id, right.claim_id, "normalized quantities differ", left.predicate)

    if left.value_type == right.value_type == "text":
        a = str(left.value).strip().casefold()
        b = str(right.value).strip().casefold()
        if left.qualifier != right.qualifier:
            # Commercial qualifiers such as starts_at and exact are different
            # claims unless a stronger predicate explicitly declares them exclusive.
            return None
        if a and b and a != b:
            return Contradiction(left.claim_id, right.claim_id, "typed text predicates differ", left.predicate)

    return None


def detect_contradiction(claim_a: str, claim_b: str):
    a = claim_a.strip().lower()
    b = claim_b.strip().lower()

    if not a or not b or a == b:
        return None

    for positive, negative in (
        ("true", "false"),
        ("yes", "no"),
        ("enabled", "disabled"),
        ("available", "unavailable"),
    ):
        if positive in a.split() and negative in b.split():
            return Contradiction(claim_a, claim_b, f"opposing marker: {positive}/{negative}")
        if negative in a.split() and positive in b.split():
            return Contradiction(claim_a, claim_b, f"opposing marker: {positive}/{negative}")

    if a.startswith("not ") and a[4:] == b:
        return Contradiction(claim_a, claim_b, "explicit negation")
    if b.startswith("not ") and b[4:] == a:
        return Contradiction(claim_a, claim_b, "explicit negation")

    return None


def _candidate_bucket_key(claim: TypedClaim) -> tuple[str, str, str, str, str]:
    start = claim.valid_from.date().isoformat() if claim.valid_from else "*"
    return (
        claim.entity.strip().casefold(),
        claim.predicate.strip().casefold(),
        (claim.scope or "*").strip().casefold() or "*",
        (claim.version or "*").strip().casefold() or "*",
        start,
    )


def bucket_typed_claims(
    claims: tuple[TypedClaim, ...] | list[TypedClaim],
) -> dict[tuple[str, str, str, str, str], tuple[TypedClaim, ...]]:
    """Group compatible contradiction candidates deterministically."""
    buckets: dict[tuple[str, str, str, str, str], list[TypedClaim]] = {}
    for claim in claims:
        if not isinstance(claim, TypedClaim):
            raise TypeError("claims must contain TypedClaim values")
        key = _candidate_bucket_key(claim)
        buckets.setdefault(key, []).append(claim)
    return {
        key: tuple(sorted(values, key=lambda item: item.claim_id))
        for key, values in sorted(buckets.items(), key=lambda item: item[0])
    }


def bounded_typed_candidate_pairs(
    claims: tuple[TypedClaim, ...] | list[TypedClaim],
    *,
    max_pairs: int = 1_000,
) -> tuple[tuple[TypedClaim, TypedClaim], ...]:
    """Produce source-order-invariant, bounded candidate pairs."""
    if max_pairs < 1:
        raise ValueError("max_pairs must be positive")
    pairs: list[tuple[TypedClaim, TypedClaim]] = []
    for values in bucket_typed_claims(claims).values():
        for index, left in enumerate(values):
            for right in values[index + 1:]:
                if _validity_overlap(left, right):
                    pairs.append((left, right))
                    if len(pairs) >= max_pairs:
                        return tuple(pairs)
    return tuple(pairs)
