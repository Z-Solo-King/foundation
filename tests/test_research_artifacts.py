from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_research_artifact_catalog_is_structured_and_truthful() -> None:
    catalog = _load("benchmark/research_artifact_catalog.json")
    assert catalog["schema"] == "research-artifact-catalog/v1"
    artifacts = {row["path"]: row for row in catalog["artifacts"]}
    required = {
        "benchmark/chatbot-query-corpus.json",
        "benchmark/chatbot_query_benchmark.py",
        "benchmark/public_chatbot_runner.py",
        "benchmark/research_artifact_validator.py",
        "benchmark/multi_agent/baseline.py",
        "benchmark/nightly/NIGHTLY_RESEARCH_PLAN.json",
        "benchmark/nightly/research-ledger.schema.json",
        "benchmark/nightly/research_ledger.py",
        "benchmark/autonomous_scorecard.mjs",
    }
    assert required <= artifacts.keys()
    for path, row in artifacts.items():
        assert (ROOT / path).exists(), path
        assert isinstance(row["reusable_evidence"], bool)
        assert row["research_value"] in {"High", "Medium", "Low"}
    assert len(catalog["reusable_evidence_rules"]) >= 6


def test_project_research_corpus_has_broad_project_coverage() -> None:
    corpus = _load("benchmark/chatbot-query-corpus.json")
    assert corpus["schema"] == "chatbot-research-query-corpus/v3"
    queries = corpus["queries"]
    assert len(queries) >= 25
    categories = {row["category"] for row in queries}
    project_categories = {
        "project_architecture",
        "project_status",
        "research_artifacts",
        "extraction_quality",
        "regression_analysis",
        "ci_health",
        "source_novelty",
        "evidence_quality",
        "research_efficiency",
        "frontend_research",
        "acceptance",
        "nightly_artifact_integrity",
    }
    assert project_categories <= categories
    project_rows = [row for row in queries if row["category"] in project_categories]
    project_category_counts = {
        category: sum(1 for row in project_rows if row["category"] == category)
        for category in project_categories
    }
        category: sum(1 for row in project_rows if row["category"] == category)
        for category in project_categories
    }
    assert all(count >= 1 for count in project_category_counts.values())
    assert len(project_rows) >= len(project_categories)
    assert all("github" in row["required_sources"] for row in project_rows)
    assert any(row["temporal"] == "old_vs_new" for row in project_rows)


def test_project_queries_cover_the_research_artifacts_themselves() -> None:
    corpus = _load("benchmark/chatbot-query-corpus.json")
    queries = {row["id"]: row["query"].lower() for row in corpus["queries"]}
    assert "scorecards" in queries["project-research-artifacts"]
    assert "nightly research plans" in queries["project-research-artifacts"]
    assert "scorecards" in queries["project-research-artifacts"]







        candidates.update(
            path for path in runtime_dir.rglob(filename) if path.is_file()
        )























    errors.extend(
        f"nightly artifact bundle missing lane status: lane {lane}"
        for lane in missing_lanes
    )



    statuses = [
        _load(discovered_lane_paths[lane]) for lane in range(NIGHTLY_LANE_COUNT)
    ]










        errors.append(
            f"nightly lane statuses must share one valid mode: {sorted(modes)}"
        )

    operations_revisions = {
        str(item.get("operations_revision", "")) for item in statuses
    }

        errors.append(
            "nightly lane statuses must share one non-empty Operations revision"
        )









            errors.append(
                f"nightly lane {lane} must report exactly 8 programs, got {program_count}"
            )

        expected = {
            f"lane{lane}-slot{slot}" for slot in range(NIGHTLY_PROGRAMS_PER_LANE)
        }

            errors.append(
                f"nightly lane {lane} program IDs do not exactly match the 8-slot contract"
            )







            errors.append(
                f"unsupported nightly diagnosis schema: {diagnosis.get('schema')!r}"
            )




            "lane_specific_failure"
            if "lane_failure" in lane_state_set
            else "blocked_before_execution"
            if "blocked_before_execution" in lane_state_set
            else "dry_run"
            if lane_state_set == {"dry_run"}
            else "live_research_executed"
            if lane_state_set == {"live_research_executed"}
            else "partial_or_mixed"







        should_allow = expected_aggregate == "live_research_executed" and modes == {
            "live"
        }

            errors.append(
                "nightly diagnosis real_research_findings_allowed violates execution/evidence boundary"
            )

            errors.append(
                "nightly diagnosis must mark dry-run findings as non-research"
            )





            errors.append(
                "nightly diagnosis blockers must use the bounded blocker vocabulary"
            )

            errors.append(
                "nightly diagnosis blockers must be unique and bounded to 8 entries"
            )





            errors.append(
                f"unsupported project-improvement schema: {project.get('schema')!r}"
            )

            errors.append(
                "nightly project-improvement artifact must declare research_mode=project_improvement"
            )

            errors.append(
                "nightly project-improvement artifact must contain all 24 programs"
            )

            errors.append(
                "nightly project-improvement artifact must carry a project revision"
            )

        if (
            evidence_policy.get("llm_findings")
            != "candidate_only_until_acquisition_receipt"
        ):
            errors.append(
                "nightly project-improvement artifact violates the LLM evidence policy"
            )
        if "live_research_executed" not in {
            str(item.get("state")) for item in statuses
        }:
            errors.append(
                "nightly project-improvement artifact requires live research lane execution"
            )





            errors.append(
                f"unsupported nightly baseline schema: {baseline.get('schema')!r}"
            )
        if baseline.get("decision") not in {
            "NO_BASELINE",
            "IMPROVED",
            "REGRESSED",
            "STABLE",
        }:
            errors.append(
                f"invalid nightly baseline decision: {baseline.get('decision')!r}"
            )

            for field in (
                "current_research_id",
                "previous_research_id",
                "current_revision",
                "previous_revision",
            ):























    artifacts = {
        str(row.get("path")): row
        for row in catalog.get("artifacts", [])
        if isinstance(row, dict)
    }

    errors.extend(
        f"catalog missing required artifact: {path}" for path in missing_catalog_entries
    )

























        row
        for row in queries




    errors.extend(
        f"missing project research category: {category}"
        for category in missing_categories
    )



            errors.append(
                f"project query without github source family: {row.get('id')}"
            )




        warnings.append(
            "multiple project categories are not represented by distinct queries"
        )









            warnings.append(
                f"benchmark artifact reports {failed} failed query contracts"
            )


            errors.append(
                "benchmark artifact reports incomplete project-query coverage"
            )

























    parser = argparse.ArgumentParser(
        description="Validate the research artifact/evidence boundary."
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="also fail when benchmark artifacts report query failures",
    )











    raise SystemExit(main())









    project_category_counts = {
        category: sum(1 for row in project_rows if row["category"] == category)
        for category in project_categories
    }






    assert "scorecards" in queries["project-research-artifacts"]
