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


def detect_typed_contradiction(left: TypedClaim, right: TypedClaim) -> Contradiction | None:
    if left.entity != right.entity or left.predicate != right.predicate:
        return None
    if left.version and right.version and left.version != right.version:
        return None
    if not _scopes_overlap(left.scope, right.scope) or not _validity_overlap(left, right):
        return None

    if left.value_type == right.value_type == "numeric":
        a, b = _numeric(left.value), _numeric(right.value)
        if a is not None and b is not None and left.unit == right.unit and a != b:
            return Contradiction(left.claim_id, right.claim_id, "numeric values differ", left.predicate)

    if left.value_type == right.value_type == "date":
        a, b = _as_date(left.value), _as_date(right.value)
        if a is not None and b is not None and a != b:
            return Contradiction(left.claim_id, right.claim_id, "dates differ", left.predicate)

    if left.value_type in {"enum", "boolean"} and right.value_type == left.value_type:
        if str(left.value).strip().lower() != str(right.value).strip().lower():
            return Contradiction(left.claim_id, right.claim_id, "mutually exclusive categorical values", left.predicate)

    if left.value_type == right.value_type == "quantity":
        a, b = _numeric(left.value), _numeric(right.value)
        if a is not None and b is not None and left.unit and left.unit == right.unit and a != b:
            return Contradiction(left.claim_id, right.claim_id, "normalized quantities differ", left.predicate)

    if left.value_type == right.value_type == "text":
        a = str(left.value).strip().lower()
        b = str(right.value).strip().lower()
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
