"""Public authority contract and generic evaluator; rule tables remain private Operations policy."""
from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from .lineage import SourceLineage,is_independent
class FieldAuthority(StrEnum):
    MANUFACTURER_DECLARATION="manufacturer_declaration"; INDEPENDENT_MEASUREMENT="independent_measurement"; RETAILER_CURRENT_STATE="retailer_current_state"; MANUFACTURER_POLICY="manufacturer_policy"; COMMUNITY_EXPERIENCE="community_experience"
class ClaimField(StrEnum):
    SPECIFICATION="specification"; MEASUREMENT="measurement"; PRICE="price"; STOCK="stock"; WARRANTY="warranty"; SERVICE="service"; EXPERIENCE="experience"
@dataclass(frozen=True)
class AuthorityDecision:
    accepted:bool; field:ClaimField; authority:FieldAuthority; reason:str
def evaluate_authority(field,authority,*,allowed_authorities):
    f=ClaimField(field); a=FieldAuthority(authority)
    allowed={FieldAuthority(v) for v in allowed_authorities.get(f,allowed_authorities.get(f.value,set()))}
    ok=a in allowed
    return AuthorityDecision(ok,f,a,"allowed field authority" if ok else "authority is not permitted for this field")
def independent_sources(first:SourceLineage,second:SourceLineage)->bool: return is_independent(first,second)
