"""Public authority contract; concrete field-to-authority rules are supplied by private policy."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping
from .lineage import SourceLineage,is_independent
class FieldAuthority(StrEnum):
    MANUFACTURER_DECLARATION="manufacturer_declaration"; INDEPENDENT_MEASUREMENT="independent_measurement"; RETAILER_CURRENT_STATE="retailer_current_state"; MANUFACTURER_POLICY="manufacturer_policy"; COMMUNITY_EXPERIENCE="community_experience"
class ClaimField(StrEnum):
    SPECIFICATION="specification"; MEASUREMENT="measurement"; PRICE="price"; STOCK="stock"; WARRANTY="warranty"; SERVICE="service"; EXPERIENCE="experience"
@dataclass(frozen=True)
class AuthorityDecision:
    accepted: bool; field: ClaimField; authority: FieldAuthority; reason: str
def evaluate_authority(field: ClaimField|str, authority: FieldAuthority|str, *, allowed_authorities: Mapping[ClaimField|str, set[FieldAuthority|str]|frozenset[FieldAuthority|str]])->AuthorityDecision:
    f=ClaimField(field); a=FieldAuthority(authority); raw=allowed_authorities.get(f,allowed_authorities.get(f.value,()))
    allowed=a in {FieldAuthority(v) for v in raw}
    return AuthorityDecision(allowed,f,a,"allowed field authority" if allowed else "authority is not permitted for this field")
def independent_sources(first: SourceLineage, second: SourceLineage)->bool: return is_independent(first,second)
__all__=["AuthorityDecision","ClaimField","FieldAuthority","evaluate_authority","independent_sources"]
