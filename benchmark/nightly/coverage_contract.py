"""Deterministic nightly coverage accounting; never an execution claim."""
from __future__ import annotations

REQUIRED_CLASSES = frozenset({"acquisition_html","api_xhr","identity_variants","contradiction_specs","price_stock","pagination_sitemap","images","blocking","multilingual","review_poisoning","freshness","comparison","missing_data","prompt_injection","repository_repair","vcs_comparison","assistant_ecosystem","agent_scaling","self_audit"})


def assess_execution(records: list[dict[str, object]]) -> dict[str, object]:
    observed={str(r.get("case_id")) for r in records if r.get("case_id")}
    completed=sum(str(r.get("status"))=="completed" for r in records)
    return {"required_classes":sorted(REQUIRED_CLASSES),"observed_classes":sorted(observed),"missing_classes":sorted(REQUIRED_CLASSES-observed),"records":len(records),"completed":completed,"execution_claim":"complete" if REQUIRED_CLASSES<=observed and completed>=19 else "partial"}
