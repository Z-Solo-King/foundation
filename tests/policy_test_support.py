from backend.admission import AdmissionPolicy, AdmissionRoute
from backend.sources.access_policy import AccessClass, DisclosureClass, RetentionClass, SourceAccessPolicy
from backend.intelligence.authority import ClaimField, FieldAuthority


def admission_policy(**overrides):
    values = {
        "version": "public-admission/v1",
        "window_seconds": 60,
        "max_requests_per_subject": 30,
        "max_requests_global": 300,
        "max_concurrent_per_subject": 22,
        "max_concurrent_global": 22,
        "retry_after_seconds": 5,
        "protected_routes": (AdmissionRoute.CHAT, AdmissionRoute.RESEARCH, AdmissionRoute.STREAM),
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
    ClaimField.SPECIFICATION: {FieldAuthority.MANUFACTURER_DECLARATION, FieldAuthority.INDEPENDENT_MEASUREMENT},
    ClaimField.MEASUREMENT: {FieldAuthority.INDEPENDENT_MEASUREMENT},
    ClaimField.PRICE: {FieldAuthority.RETAILER_CURRENT_STATE},
    ClaimField.STOCK: {FieldAuthority.RETAILER_CURRENT_STATE},
    ClaimField.WARRANTY: {FieldAuthority.MANUFACTURER_POLICY, FieldAuthority.RETAILER_CURRENT_STATE},
    ClaimField.SERVICE: {FieldAuthority.MANUFACTURER_POLICY, FieldAuthority.COMMUNITY_EXPERIENCE},
    ClaimField.EXPERIENCE: {FieldAuthority.COMMUNITY_EXPERIENCE},
}


def private_policy_envelope():
    return {
        "schema": "protected-policy-envelope/v1",
        "policy_digest": "test-policy-digest",
        "admission": {
            "version": "public-admission/v1",
            "window_seconds": 60,
            "max_requests_per_subject": 30,
            "max_requests_global": 300,
            "max_concurrent_per_subject": 22,
            "max_concurrent_global": 22,
            "retry_after_seconds": 5,
            "protected_routes": ["chat", "research", "stream"],
        },
        "research_planning": {
            "base_source_families": ["web_search", "retailers", "oem"],
            "category_required_source_families": {
                "buying_guide": ["amazon", "flipkart", "reddit", "retailers", "oem"],
                "best_product": ["amazon", "flipkart", "reddit", "retailers", "professional_reviews"],
            },
            "keyword_groups": {
                "reddit": ["reddit", "subreddit"],
                "amazon": ["amazon", "buyer reviews"],
                "flipkart": ["flipkart"],
                "youtube": ["youtube", "video review"],
                "social_media": ["twitter", "instagram", "facebook"],
                "social_communities": ["community", "forum"],
                "chinese_communities": ["chinese", "bilibili", "zhihu", "baidu tieba", "douban", "ptt"],
                "teardown_evidence": ["teardown", "pcb", "revision"],
                "professional_reviews": ["professional review", "reviewers"],
                "search_trends": ["trending", "trend"],
                "price_stock": ["price", "stock", "availability", "current"],
            },
            "temporal_terms": ["old vs new", "latest", "recent", "revision", "2024", "2025", "2026"],
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
