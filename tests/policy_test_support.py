from backend.admission import AdmissionPolicy, AdmissionRoute
from backend.sources.access_policy import AccessClass, DisclosureClass, RetentionClass, SourceAccessPolicy
from backend.intelligence.authority import ClaimField, FieldAuthority


def admission_policy(**overrides):
    values = {
        "version": "public-admission/v1",
        "window_seconds": 11,
        "max_requests_per_subject": 7,
        "max_requests_global": 70,
        "max_concurrent_per_subject": 3,
        "max_concurrent_global": 4,
        "retry_after_seconds": 2,
        "protected_routes": (AdmissionRoute.RESEARCH,),
    }
    values.update(overrides)
    return AdmissionPolicy(**values)


def source_policy(**overrides):
    values = {
        "policy_version": "source-access/v1",
        "access_class": AccessClass.PUBLIC,
        "acquisition_method": "http_get",
        "requires_authentication": False,
        "robots_restriction": False,
        "retention_class": RetentionClass.SHORT,
        "raw_content_allowed": False,
        "disclosure_class": DisclosureClass.PUBLIC_SAFE,
        "revalidation_required": True,
        "revalidation_after_seconds": None,
    }
    values.update(overrides)
    return SourceAccessPolicy(**values)


AUTHORITY_RULES = {
    ClaimField.SPECIFICATION: {FieldAuthority.MANUFACTURER_DECLARATION},
    ClaimField.PRICE: {FieldAuthority.RETAILER_CURRENT_STATE},
}


def private_policy_envelope():
    return {
        "schema": "protected-policy-envelope/v1",
        "policy_digest": "synthetic-policy-digest",
        "admission": {
            "version": "public-admission/v1",
            "window_seconds": 11,
            "max_requests_per_subject": 7,
            "max_requests_global": 70,
            "max_concurrent_per_subject": 3,
            "max_concurrent_global": 4,
            "retry_after_seconds": 2,
            "protected_routes": ["research"],
        },
        "research_planning": {
            "base_source_families": ["synthetic_web"],
            "category_required_source_families": {
                "synthetic_category": ["source_a", "source_b"],
            },
            "keyword_groups": {
                "synthetic_family": ["synthetic", "fixture"],
            },
            "temporal_terms": ["latest", "recent"],
            "quick_stages": ["define_question", "discover_sources", "collect_observations", "verify_evidence", "synthesize_answer"],
            "standard_stages": ["define_question", "assess_constraints", "discover_sources", "collect_observations", "map_evidence", "verify_evidence", "check_independence", "synthesize_answer"],
        },
        "source_access": {},
        "claim_authority": {},
    }


class PolicyBinding:
    async def fetch(self, request):
        class Response:
            status = 200
            async def json(self):
                return private_policy_envelope()
        return Response()


def policy_binding():
    return PolicyBinding()
