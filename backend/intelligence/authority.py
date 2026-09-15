from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .lineage import SourceLineage, is_independent


class FieldAuthority(StrEnum):
    MANUFACTURER_DECLARATION = "manufacturer_declaration"
    INDEPENDENT_MEASUREMENT = "independent_measurement"
    RETAILER_CURRENT_STATE = "retailer_current_state"
    MANUFACTURER_POLICY = "manufacturer_policy"
    COMMUNITY_EXPERIENCE = "community_experience"


class ClaimField(StrEnum):
    SPECIFICATION = "specification"
    MEASUREMENT = "measurement"
    PRICE = "price"
    STOCK = "stock"
    WARRANTY = "warranty"
    SERVICE = "service"
    EXPERIENCE = "experience"


_ALLOWED = {
    ClaimField.SPECIFICATION: frozenset({FieldAuthority.MANUFACTURER_DECLARATION, FieldAuthority.INDEPENDENT_MEASUREMENT}),
    ClaimField.MEASUREMENT: frozenset({FieldAuthority.INDEPENDENT_MEASUREMENT}),
    ClaimField.PRICE: frozenset({FieldAuthority.RETAILER_CURRENT_STATE}),
    ClaimField.STOCK: frozenset({FieldAuthority.RETAILER_CURRENT_STATE}),
    ClaimField.WARRANTY: frozenset({FieldAuthority.MANUFACTURER_POLICY, FieldAuthority.RETAILER_CURRENT_STATE}),
    ClaimField.SERVICE: frozenset({FieldAuthority.MANUFACTURER_POLICY, FieldAuthority.COMMUNITY_EXPERIENCE}),
    ClaimField.EXPERIENCE: frozenset({FieldAuthority.COMMUNITY_EXPERIENCE}),
}


@dataclass(frozen=True)
class AuthorityDecision:
    accepted: bool
    field: ClaimField
    authority: FieldAuthority
    reason: str


def evaluate_authority(field: ClaimField | str, authority: FieldAuthority | str) -> AuthorityDecision:
    field_value = ClaimField(field)
    authority_value = FieldAuthority(authority)
    allowed = authority_value in _ALLOWED[field_value]
    return AuthorityDecision(allowed, field_value, authority_value, "allowed field authority" if allowed else "authority is not permitted for this field")


def independent_sources(first: SourceLineage, second: SourceLineage) -> bool:
    return is_independent(first, second)


__all__ = ["AuthorityDecision", "ClaimField", "FieldAuthority", "evaluate_authority", "independent_sources"]
