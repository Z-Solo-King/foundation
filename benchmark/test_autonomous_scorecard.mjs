import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { buildScorecard, renderMarkdown } from "./autonomous_scorecard.mjs";

const TIER = {
  DETERMINISTIC_CONTRACT: "deterministic_contract",
  LIVE_SOURCE_ACQUISITION: "live_source_acquisition",
};

function writeJson(root, relative, payload) {
  const file = path.join(root, relative);
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(payload), "utf8");
}

test("scorecard aggregates shards and keeps contract separate from acquisition", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "scorecard-"));
  try {
    writeJson(root, "shard-0/benchmark-summary.json", {
      schema: "autonomous-public-benchmark-summary/v10",
      run_id: "run-1",
      shard: 0,
      selected_targets: 2,
      cycles: 3,
      evidence: { tier: TIER.LIVE_SOURCE_ACQUISITION },
      status_counts: { ok: 5, blocked: 1, error: 0, empty: 0, resource_limited: 0 },
      http_status_counts: { "200": 5, "403": 1 },
      diagnostic_counts: { "attempts-1": 6 },
      measurement: {
        observations: 6,
        elapsed_ms: { min: 20, median: 30, p95: 50, max: 60 },
        product_candidates_total: 10,
        jsonld_blocks_total: 4,
        observations_with_product_candidates: 5,
        observations_with_jsonld: 2,
        field_level_correctness_oracle: false,
      },
      targets_with_failures: [{
        url: "https://blocked.example/",
        observations: 1,
        failures: 1,
        status_counts: { ok: 0, blocked: 1 },
        http_status_counts: { "403": 1 },
        diagnostics: { "attempts-1": 1 },
      }],
    });
    writeJson(root, "shard-1/benchmark-summary.json", {
      schema: "autonomous-public-benchmark-summary/v10",
      run_id: "run-1",
      shard: 1,
      selected_targets: 1,
      cycles: 2,
      evidence: { tier: TIER.LIVE_SOURCE_ACQUISITION },
      status_counts: { ok: 4, blocked: 0, error: 1, empty: 0, resource_limited: 0 },
      http_status_counts: { "200": 4 },
      diagnostic_counts: { "attempts-1": 5 },
      measurement: {
        observations: 5,
        elapsed_ms: { min: 10, median: 40, p95: 90, max: 100 },
        product_candidates_total: 8,
        jsonld_blocks_total: 3,
        observations_with_product_candidates: 4,
        observations_with_jsonld: 3,
        field_level_correctness_oracle: false,
      },
      targets_with_failures: [],
    });
    writeJson(root, "autonomous-chatbot-query-benchmark/chatbot-query-benchmark.json", {
      schema: "chatbot-research-query-benchmark/v6",
      queries: 14,
      passed: 14,
      failed: 0,
      evidence: { tier: TIER.DETERMINISTIC_CONTRACT },
      corpus_coverage: {
        project_query_count: 11,
        project_query_rate: 0.7857,
        category_count: 14,
        source_family_count: 14,
        temporal_modes: { current: 13, old_vs_new: 1 },
      },
    });

    const scorecard = buildScorecard(root);
    assert.deepEqual(scorecard.status, {
      overall: "WARN",
      execution: "PASS",
      research_contract: "PASS",
      acquisition_clean: "FAIL",
    });
    assert.equal(scorecard.evidence.minimum_tier, TIER.DETERMINISTIC_CONTRACT);
    assert.deepEqual(new Set(scorecard.evidence.component_tiers), new Set([
      TIER.DETERMINISTIC_CONTRACT,
      TIER.LIVE_SOURCE_ACQUISITION,
    ]));
    assert.equal(scorecard.evidence.live_provider_claim_allowed, false);
    assert.equal(scorecard.evidence.integration_runtime_claim_allowed, false);
    assert.equal(scorecard.evidence.production_readiness_claim_allowed, false);
    assert.equal(scorecard.selected_targets, 3);
    assert.equal(scorecard.total_observations, 11);
    assert.equal(scorecard.acquisition.usable_observation_rate, 0.818182);
    assert.equal(scorecard.acquisition.blocked_rate, 0.090909);
    assert.equal(scorecard.acquisition.error_rate, 0.090909);
    assert.equal(scorecard.research_contract.pass_rate, 1);
    assert.equal(scorecard.research_contract.project_query_count, 11);
    assert.equal(scorecard.structural_signals.observations_measured, 11);
    assert.equal(scorecard.structural_signals.product_candidates_total, 18);
    assert.equal(scorecard.structural_signals.jsonld_blocks_total, 7);
    assert.equal(scorecard.structural_signals.field_level_correctness_oracle, false);
    assert.equal(scorecard.targets_with_failures[0].health_class, "blocked");
    assert.equal(scorecard.targets_with_failures[0].recommended_action, "quarantine_until_manual_recheck");
    const markdown = renderMarkdown(scorecard);
    assert.match(markdown, /Overall: \*\*WARN\*\*/);
    assert.match(markdown, /Research contract: \*\*PASS\*\* \(14\/14 passed\)/);
    assert.match(markdown, /Acquisition clean: \*\*FAIL\*\*/);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test("missing summaries fail closed", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "scorecard-empty-"));
  try {
    assert.throws(() => buildScorecard(root), /no benchmark summary files found/);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});
