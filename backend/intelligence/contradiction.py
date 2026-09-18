from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


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
    tolerance: Decimal | None = None
    negated: bool = False


_UNIT_FACTORS = {
    "ms": ("time", Decimal("1")),
    "s": ("time", Decimal("1000")),
    "us": ("time", Decimal("0.001")),
    "g": ("mass", Decimal("1")),
    "kg": ("mass", Decimal("1000")),
    "mg": ("mass", Decimal("0.001")),
    "bytes": ("bytes", Decimal("1")),
    "kb": ("bytes", Decimal("1024")),
    "mb": ("bytes", Decimal("1048576")),
}


def _numeric(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


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
    return left.strip().lower() == right.strip().lower()


def _validity_overlap(left: TypedClaim, right: TypedClaim) -> bool:
    if left.valid_until and right.valid_from and left.valid_until < right.valid_from:
        return False
    if right.valid_until and left.valid_from and right.valid_until < left.valid_from:
        return False
    return True


def _normalize_quantity(value: object, unit: str | None) -> tuple[str, Decimal] | None:
    numeric = _numeric(value)
    if numeric is None:
        return None
    if not unit:
        return ("unknown", numeric)
    spec = _UNIT_FACTORS.get(unit.strip().casefold())
    if spec is None:
        return (f"unknown:{unit.strip().casefold()}", numeric)
    dimension, factor = spec
    return dimension, numeric * factor


def _normalized_tolerance(claim: TypedClaim) -> Decimal:
    tolerance = claim.tolerance or Decimal("0")
    if not claim.unit:
        return tolerance
    spec = _UNIT_FACTORS.get(claim.unit.strip().casefold())
    if spec is None:
        return tolerance
    return tolerance * spec[1]


def _numeric_pair(left: TypedClaim, right: TypedClaim) -> tuple[Decimal, Decimal] | None:
    a = _normalize_quantity(left.value, left.unit)
    b = _normalize_quantity(right.value, right.unit)
    if a is not None and b is not None and a[0] == b[0]:
        return a[1], b[1]
    if (left.unit or "") .strip().casefold() == (right.unit or "").strip().casefold():
        raw_a, raw_b = _numeric(left.value), _numeric(right.value)
        if raw_a is not None and raw_b is not None:
            return raw_a, raw_b
    return None


def detect_typed_contradiction(left: TypedClaim, right: TypedClaim) -> Contradiction | None:
    if left.entity != right.entity or left.predicate != right.predicate:
        return None
    if left.version and right.version and left.version != right.version:
        return None
    if not _scopes_overlap(left.scope, right.scope) or not _validity_overlap(left, right):
        return None

    if left.value_type == right.value_type == "numeric":
        pair = _numeric_pair(left, right)
        if pair is not None:
            tolerance = max(_normalized_tolerance(left), _normalized_tolerance(right))
            if abs(pair[0] - pair[1]) > tolerance:
                return Contradiction(left.claim_id, right.claim_id, "numeric values differ beyond tolerance", left.predicate)

    if left.value_type == right.value_type == "date":
        a, b = _as_date(left.value), _as_date(right.value)
        if a is not None and b is not None and a != b:
            return Contradiction(left.claim_id, right.claim_id, "dates differ", left.predicate)

    if left.value_type in {"enum", "boolean"} and right.value_type == left.value_type:
        if str(left.value).strip().lower() != str(right.value).strip().lower():
            return Contradiction(left.claim_id, right.claim_id, "mutually exclusive categorical values", left.predicate)

    if left.value_type == right.value_type == "quantity":
        if left.unit and right.unit:
            pair = _numeric_pair(left, right)
            if pair is not None:
                tolerance = max(left.tolerance or Decimal("0"), right.tolerance or Decimal("0"))
                if abs(pair[0] - pair[1]) > tolerance:
                    return Contradiction(left.claim_id, right.claim_id, "normalized quantities differ", left.predicate)

    if left.value_type == right.value_type == "text":
        a = str(left.value).strip().lower()
        b = str(right.value).strip().lower()
        if left.negated != right.negated:
            return Contradiction(left.claim_id, right.claim_id, "explicit negation differs", left.predicate)
        if left.qualifier != right.qualifier:
            return Contradiction(left.claim_id, right.claim_id, "commercial qualifiers differ", left.predicate)
        if left.unit == right.unit and a and b and a != b:
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


def _candidate_bucket_key(claim: TypedClaim) -> tuple[str, str, str]:
    return (
        claim.entity.strip().casefold(),
        claim.predicate.strip().casefold(),
        (claim.scope or "*").strip().casefold() or "*",
    )


def bucket_typed_claims(
    claims: tuple[TypedClaim, ...] | list[TypedClaim],
) -> dict[tuple[str, str, str], tuple[TypedClaim, ...]]:
    """Group compatible contradiction candidates deterministically."""
    buckets: dict[tuple[str, str, str], list[TypedClaim]] = {}
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
