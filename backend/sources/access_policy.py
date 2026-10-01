from __future__ import annotations
from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping

SOURCE_ACCESS_POLICY_VERSION = "source-access/v1"

class AccessClass(StrEnum):
    PUBLIC="public"; AUTHENTICATED="authenticated"; RESTRICTED="restricted"; UNKNOWN="unknown"
class RetentionClass(StrEnum):
    EPHEMERAL="ephemeral"; SHORT="short"; STANDARD="standard"; NONE="none"; UNKNOWN="unknown"
class DisclosureClass(StrEnum):
    PUBLIC_SAFE="public_safe"; METADATA_ONLY="metadata_only"; PRIVATE_ONLY="private_only"; FORBIDDEN="forbidden"

@dataclass(frozen=True)
class SourceAccessPolicy:
    policy_version: str
    access_class: AccessClass
    acquisition_method: str
    requires_authentication: bool
    robots_restriction: bool
    retention_class: RetentionClass
    raw_content_allowed: bool
    disclosure_class: DisclosureClass
    revalidation_required: bool
    revalidation_after_seconds: int | None

    def validate(self)->None:
        if self.policy_version != SOURCE_ACCESS_POLICY_VERSION: raise ValueError("unsupported source access policy version")
        if not self.acquisition_method.strip(): raise ValueError("acquisition_method is required")
        if not isinstance(self.requires_authentication,bool) or not isinstance(self.robots_restriction,bool): raise ValueError("source access flags must be boolean")
        if self.access_class is AccessClass.UNKNOWN or self.retention_class is RetentionClass.UNKNOWN: raise ValueError("unknown source access or retention class must fail closed")
        if self.access_class is AccessClass.AUTHENTICATED and not self.requires_authentication: raise ValueError("authenticated access class requires authentication")
        if self.access_class in {AccessClass.RESTRICTED,AccessClass.AUTHENTICATED} and self.disclosure_class is DisclosureClass.PUBLIC_SAFE: raise ValueError("restricted/authenticated content cannot be public-safe by default")
        if self.disclosure_class is DisclosureClass.PUBLIC_SAFE and self.raw_content_allowed: raise ValueError("public-safe disclosure cannot retain unrestricted raw content")
        if self.retention_class is RetentionClass.NONE and self.raw_content_allowed: raise ValueError("raw content cannot be retained when retention is none")
        if self.revalidation_after_seconds is not None and self.revalidation_after_seconds < 0: raise ValueError("revalidation_after_seconds must be non-negative")

@dataclass(frozen=True)
class SourceAccessDecision:
    allowed: bool
    reason: str
    retention_class: RetentionClass
    disclosure_class: DisclosureClass
    revalidate: bool
    policy_version: str=SOURCE_ACCESS_POLICY_VERSION
    def validate(self)->None:
        if not self.reason.strip(): raise ValueError("decision reason is required")
        if not self.allowed and self.retention_class is RetentionClass.STANDARD: raise ValueError("rejected sources cannot receive standard retention")

def decide_source_access(policy: SourceAccessPolicy, *, requested_disclosure: DisclosureClass, request_authenticated: bool, restricted_research: bool)->SourceAccessDecision:
    policy.validate()
    if requested_disclosure is DisclosureClass.PUBLIC_SAFE and policy.disclosure_class is not DisclosureClass.PUBLIC_SAFE:
        decision=SourceAccessDecision(False,"policy does not permit public disclosure",policy.retention_class,policy.disclosure_class,policy.revalidation_required)
    elif policy.requires_authentication and not request_authenticated:
        decision=SourceAccessDecision(False,"source authentication is required",policy.retention_class,policy.disclosure_class,policy.revalidation_required)
    elif policy.access_class is AccessClass.RESTRICTED and not restricted_research:
        decision=SourceAccessDecision(False,"restricted source requires governed research context",policy.retention_class,policy.disclosure_class,True)
    elif policy.robots_restriction:
        decision=SourceAccessDecision(False,"source acquisition is restricted by policy",policy.retention_class,policy.disclosure_class,True)
    else:
        decision=SourceAccessDecision(True,"source acquisition allowed by policy",policy.retention_class,policy.disclosure_class,policy.revalidation_required)
    decision.validate(); return decision

def retention_seconds(policy: SourceAccessPolicy, retention_ttl_seconds: Mapping[RetentionClass,int|None])->int|None:
    policy.validate()
    if policy.retention_class not in retention_ttl_seconds: raise ValueError("retention policy value is unavailable")
    return retention_ttl_seconds[policy.retention_class]

def expires_at(observed_at, policy: SourceAccessPolicy, retention_ttl_seconds: Mapping[RetentionClass,int|None]):
    from datetime import timedelta,timezone
    policy.validate()
    if observed_at.tzinfo is None: raise ValueError("observed_at must be timezone-aware")
    seconds=retention_seconds(policy,retention_ttl_seconds)
    if seconds is None: return None
    return observed_at.astimezone(timezone.utc)+timedelta(seconds=seconds)

def revalidation_due(observed_at, policy: SourceAccessPolicy, default_revalidation_seconds: int|None):
    from datetime import timedelta,timezone
    policy.validate()
    if observed_at.tzinfo is None: raise ValueError("observed_at must be timezone-aware")
    if not policy.revalidation_required: return None
    seconds=policy.revalidation_after_seconds if policy.revalidation_after_seconds is not None else default_revalidation_seconds
    if seconds is None or seconds < 0: raise ValueError("revalidation policy value is unavailable")
    return observed_at.astimezone(timezone.utc)+timedelta(seconds=seconds)

def resolve_source_policy_conflict(policies, *, access_rank: Mapping[AccessClass,int], disclosure_rank: Mapping[DisclosureClass,int], retention_rank: Mapping[RetentionClass,int])->SourceAccessPolicy:
    if not policies: raise ValueError("at least one source policy is required")
    for policy in policies: policy.validate()
    if all(policy==policies[0] for policy in policies[1:]): return policies[0]
    return max(policies,key=lambda policy:(access_rank.get(policy.access_class,-1),disclosure_rank.get(policy.disclosure_class,-1),retention_rank.get(policy.retention_class,-1),int(policy.requires_authentication),int(policy.robots_restriction),int(not policy.raw_content_allowed)))
