from benchmark.nightly.coverage_contract import assess_execution


def test_coverage_contract_does_not_claim_unexecuted_jobs():
    result = assess_execution([{"case_id": "acquisition_html", "status": "completed"}])
    assert result["execution_claim"] == "partial"
    assert "assistant_ecosystem" in result["missing_classes"]


def test_coverage_contract_accepts_all_nineteen_completed_cases():
    cases = ["acquisition_html","api_xhr","identity_variants","contradiction_specs","price_stock","pagination_sitemap","images","blocking","multilingual","review_poisoning","freshness","comparison","missing_data","prompt_injection","repository_repair","vcs_comparison","assistant_ecosystem","agent_scaling","self_audit"]
    result = assess_execution([{"case_id": case, "status": "completed"} for case in cases])
    assert result["missing_classes"] == []
    assert result["execution_claim"] == "complete"
