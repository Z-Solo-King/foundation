#!/usr/bin/env node
/**
 * Deterministic autonomous-research scorecard aggregator.
 * Report-only: it never authorizes provider, runtime, policy, or promotion changes.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

export const STATUS_KEYS = ["ok", "empty", "blocked", "resource_limited", "error"];
export const EVIDENCE_ORDER = new Map([
  ["deterministic_contract", 0],
  ["simulated_provider", 1],
  ["live_source_acquisition", 2],
  ["live_provider", 3],
  ["integration_runtime", 4],
  ["production", 5],
]);

function readJson(file) {
  const value = JSON.parse(fs.readFileSync(file, "utf8"));
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("expected object in " + file);
  }
  return value;
}

export function ratio(numerator, denominator) {
  return denominator ? Number((numerator / denominator).toFixed(6)) : null;
}

export function weightedAverage(values) {
  const totalWeight = values.reduce((sum, item) => sum + item[1], 0);
  return totalWeight
    ? Number((values.reduce((sum, item) => sum + item[0] * item[1], 0) / totalWeight).toFixed(3))
    : null;
}

export function collectSummaryFiles(root) {
  const found = [];
  const visit = dir => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) visit(full);
      else if (entry.isFile() && (entry.name === "benchmark-summary.json" || /^summary-.*\.json$/.test(entry.name))) found.push(full);
    }
  };
  visit(root);
  return [...new Set(found.map(file => path.resolve(file)))].sort();
}

export function tierRank(value) {
  return EVIDENCE_ORDER.get(String(value || "").trim().toLowerCase()) ?? -1;
}

export function targetHealth(observations, failures, statusCounts, httpStatusCounts) {
  if (observations <= 0) return ["unknown", "collect_more_observations"];
  const failureRate = failures / observations;
  const blocked = Number(statusCounts.blocked || 0);
  const limited = Number(statusCounts.resource_limited || 0);
  const errors = Number(statusCounts.error || 0);
  if (blocked / observations >= 0.95) return ["blocked", "quarantine_until_manual_recheck"];
  if (limited / observations >= 0.95) return ["rate_limited", "exponential_backoff_and_quarantine"];
  if (errors / observations >= 0.95 && Object.keys(httpStatusCounts).length === 0) return ["transport_error", "investigate_dns_tls_or_network_path"];
  if (failureRate === 0) return ["healthy", "retain_normal_sampling"];
  if (failureRate >= 0.5) return ["degraded", "retain_for_targeted_recheck"];
  return ["intermittent", "retain_with_failure_aware_retry"];
}

export function buildScorecard(root) {
  const summaryPaths = collectSummaryFiles(root);
  if (!summaryPaths.length) throw new Error("no benchmark summary files found under " + root);

  const statusCounts = Object.create(null);
  const httpCounts = Object.create(null);
  const diagnosticCounts = Object.create(null);
  const targets = new Map();
  let selectedTargets = 0;
  let cycles = 0;
  const runIds = new Set();
  const shards = [];
  const measurementGaps = new Set();
  const measurementRows = [];
  const componentTiers = new Set();

  const bump = (target, key, delta) => {
    target[key] = target[key] || Object.create(null);
    target[key][delta[0]] = Number(target[key][delta[0]] || 0) + Number(delta[1] || 0);
  };
  const mergeCounts = (into, source) => {
    for (const [key, value] of Object.entries(source || {})) into[key] = Number(into[key] || 0) + Number(value || 0);
  };

  for (const file of summaryPaths) {
    const row = readJson(file);
    if (!String(row.schema || "").startsWith("autonomous-public-benchmark-summary/")) continue;

    const evidence = row.evidence;
    if (evidence && typeof evidence === "object" && typeof evidence.tier === "string") {
      if (EVIDENCE_ORDER.has(evidence.tier)) componentTiers.add(evidence.tier);
      else measurementGaps.add("benchmark artifact declares unsupported evidence tier: " + evidence.tier);
    } else {
      componentTiers.add("legacy_untyped");
      measurementGaps.add("one or more acquisition artifacts predate the explicit evidence-tier contract");
    }

    const runId = String(row.run_id || "");
    if (runId) runIds.add(runId);
    if (Number.isInteger(row.shard)) shards.push(row.shard);
    selectedTargets += Number(row.selected_targets || row.selected || 0);
    cycles += Number(row.cycles || 0);
    mergeCounts(statusCounts, row.status_counts);
    mergeCounts(httpCounts, row.http_status_counts);
    mergeCounts(diagnosticCounts, row.diagnostic_counts);

    if (row.measurement && typeof row.measurement === "object") measurementRows.push(row.measurement);
    else measurementGaps.add("sanitized benchmark summary does not expose structural or latency measurements");

    for (const target of Array.isArray(row.targets_with_failures) ? row.targets_with_failures : []) {
      if (!target || typeof target !== "object") continue;
      const url = String(target.url || "");
      const entry = targets.get(url) || {
        url,
        observations: 0,
        failures: 0,
        statusCounts: Object.create(null),
        httpStatusCounts: Object.create(null),
        diagnostics: Object.create(null),
      };
      entry.observations += Number(target.observations || 0);
      entry.failures += Number(target.failures || 0);
      mergeCounts(entry.statusCounts, target.status_counts);
      mergeCounts(entry.httpStatusCounts, target.http_status_counts);
      mergeCounts(entry.diagnostics, target.diagnostics);
      targets.set(url, entry);
    }
  }

  const measurementObservations = measurementRows.reduce((sum, row) => sum + Number(row.observations || 0), 0);
  const productCandidates = measurementRows.reduce((sum, row) => sum + Number(row.product_candidates_total || 0), 0);
  const jsonldBlocks = measurementRows.reduce((sum, row) => sum + Number(row.jsonld_blocks_total || 0), 0);
  const productObservations = measurementRows.reduce((sum, row) => sum + Number(row.observations_with_product_candidates || 0), 0);
  const jsonldObservations = measurementRows.reduce((sum, row) => sum + Number(row.observations_with_jsonld || 0), 0);
  const latencyMeans = [];
  const p95Values = [];

  for (const row of measurementRows) {
    const latency = row.elapsed_ms;
    if (!latency || typeof latency !== "object") continue;
    if (typeof latency.median === "number" && Number(row.observations || 0)) latencyMeans.push([Number(latency.median), Number(row.observations)]);
    if (typeof latency.p95 === "number") p95Values.push(Number(latency.p95));
  }

  if (!measurementRows.length) {
    measurementGaps.add("sanitized benchmark artifacts do not expose latency measurements");
    measurementGaps.add("sanitized benchmark artifacts do not expose product-candidate counts");
    measurementGaps.add("sanitized benchmark artifacts do not expose JSON-LD counts");
  }
  if (measurementRows.length && measurementRows.every(row => !row.field_level_correctness_oracle)) {
    measurementGaps.add("no oracle-backed product-field recall/precision score is present in this run");
  }
  measurementGaps.add("product-candidate and JSON-LD counts are structural hints, not correctness judgments");
  measurementGaps.add("live benchmark validates transport/content structure, not field-level product correctness");

  const totalObservations = Object.values(statusCounts).reduce((sum, value) => sum + Number(value || 0), 0);
  const ok = Number(statusCounts.ok || 0);
  const empty = Number(statusCounts.empty || 0);
  const blocked = Number(statusCounts.blocked || 0);
  const resourceLimited = Number(statusCounts.resource_limited || 0);
  const errors = Number(statusCounts.error || 0);
  const operationalFailures = blocked + resourceLimited;
  const cleanFailures = empty + blocked + resourceLimited + errors;

  let queryResult = null;
  const queryPaths = [];
  const visitQuery = dir => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) visitQuery(full);
      else if (entry.isFile() && entry.name === "chatbot-query-benchmark.json") queryPaths.push(full);
    }
  };
  visitQuery(root);
  queryPaths.sort();
  if (queryPaths.length) queryResult = readJson(queryPaths[0]);

  const queryTotal = Number(queryResult?.queries || 0);
  const queryPassed = Number(queryResult?.passed || 0);
  const queryFailed = Number(queryResult?.failed || 0);
  const corpusCoverage = queryResult?.corpus_coverage && typeof queryResult.corpus_coverage === "object" ? queryResult.corpus_coverage : {};
  const querySchema = String(queryResult?.schema || "");
  const queryEvidence = queryResult?.evidence;
  let queryTier = null;

  if (queryEvidence && typeof queryEvidence === "object" && typeof queryEvidence.tier === "string") {
    if (EVIDENCE_ORDER.has(queryEvidence.tier)) {
      queryTier = queryEvidence.tier;
      componentTiers.add(queryTier);
    } else {
      measurementGaps.add("query benchmark declares unsupported evidence tier: " + queryEvidence.tier);
    }
  } else {
    componentTiers.add("legacy_untyped");
    measurementGaps.add("deep-query benchmark artifact predates the explicit evidence-tier contract");
  }

  if (!queryResult) measurementGaps.add("deep-query benchmark artifact was not published with this run");
  else if (!querySchema.startsWith("chatbot-research-query-benchmark/")) measurementGaps.add("deep-query benchmark artifact uses an unexpected schema");

  const shardExpected = [...new Set(shards)].sort((a,b) => a-b);
  const executionPass = totalObservations > 0 && shardExpected.length > 0;
  const contractStatus = queryResult && queryTotal > 0 && queryFailed === 0 && queryPassed === queryTotal ? "PASS" : "FAIL";
  const acquisitionCleanStatus = cleanFailures === 0 ? "PASS" : "FAIL";
  const overallStatus = executionPass && contractStatus === "PASS" && acquisitionCleanStatus === "PASS" ? "PASS" : "WARN";

  const typedTiers = [...componentTiers].filter(tier => tier !== "legacy_untyped").sort((a,b) => tierRank(a)-tierRank(b));
  const minimumTier = typedTiers.length ? typedTiers[0] : "legacy_untyped";

  const targetRows = [...targets.values()].map(entry => {
    const [healthClass, recommendedAction] = targetHealth(entry.observations, entry.failures, entry.statusCounts, entry.httpStatusCounts);
    return {
      url: entry.url,
      observations: entry.observations,
      failures: entry.failures,
      failure_rate: ratio(entry.failures, entry.observations),
      status_counts: Object.fromEntries(Object.entries(entry.statusCounts).sort()),
      http_status_counts: Object.fromEntries(Object.entries(entry.httpStatusCounts).sort()),
      diagnostics: Object.fromEntries(Object.entries(entry.diagnostics).sort()),
      health_class: healthClass,
      recommended_action: recommendedAction,
    };
  }).sort((a,b) => Number(b.failure_rate || 0)-Number(a.failure_rate || 0) || a.url.localeCompare(b.url));

  return {
    schema: "autonomous-research-scorecard/v3",
    run_ids: [...runIds].sort(),
    shards: shardExpected,
    selected_targets: selectedTargets,
    cycles,
    total_observations: totalObservations,
    evidence: {
      component_tiers: [...componentTiers].sort(),
      minimum_tier: minimumTier,
      research_contract_tier: queryTier,
      live_provider_claim_allowed: false,
      integration_runtime_claim_allowed: false,
      production_readiness_claim_allowed: false,
      field_level_correctness_oracle: false,
      rule: "Aggregate scorecards cannot claim a stronger tier than their individual artifacts; transport/structural signals remain distinct from correctness and production readiness.",
    },
    status: {
      overall: overallStatus,
      execution: executionPass ? "PASS" : "FAIL",
      research_contract: contractStatus,
      acquisition_clean: acquisitionCleanStatus,
    },
    research_contract: {
      schema: querySchema || null,
      queries: queryTotal,
      passed: queryPassed,
      failed: queryFailed,
      pass_rate: ratio(queryPassed, queryTotal),
      project_query_count: Number(corpusCoverage.project_query_count || 0),
      project_query_rate: corpusCoverage.project_query_rate ?? null,
      category_count: Number(corpusCoverage.category_count || 0),
      source_family_count: Number(corpusCoverage.source_family_count || 0),
      temporal_modes: corpusCoverage.temporal_modes && typeof corpusCoverage.temporal_modes === "object" ? corpusCoverage.temporal_modes : {},
    },
    acquisition: {
      usable_observation_rate: ratio(ok, totalObservations),
      operational_failure_rate: ratio(operationalFailures, totalObservations),
      error_rate: ratio(errors, totalObservations),
      empty_rate: ratio(empty, totalObservations),
      blocked_rate: ratio(blocked, totalObservations),
      resource_limited_rate: ratio(resourceLimited, totalObservations),
      clean_failure_rate: ratio(cleanFailures, totalObservations),
      status_counts: Object.fromEntries(Object.entries(statusCounts).sort()),
      http_status_counts: Object.fromEntries(Object.entries(httpCounts).sort()),
      diagnostic_counts: Object.fromEntries(Object.entries(diagnosticCounts).sort()),
      health_class_counts: Object.fromEntries([...targetRows].reduce((map, item) => { map[item.health_class] = Number(map[item.health_class] || 0) + 1; return map; }, new Map())),
    },
    structural_signals: {
      observations_measured: measurementObservations,
      observations_with_product_candidates: productObservations,
      product_candidate_observation_rate: ratio(productObservations, measurementObservations),
      product_candidates_total: productCandidates,
      observations_with_jsonld: jsonldObservations,
      jsonld_observation_rate: ratio(jsonldObservations, measurementObservations),
      jsonld_blocks_total: jsonldBlocks,
      weighted_median_latency_ms: weightedAverage(latencyMeans),
      max_shard_p95_latency_ms: p95Values.length ? Math.max(...p95Values) : null,
      evidence_scope: measurementRows.length ? "transport_and_structural_signals_only" : "transport_only",
      field_level_correctness_oracle: false,
    },
    targets_with_failures: targetRows,
    measurement_gaps: [...measurementGaps].sort(),
  };
}

export function renderMarkdown(scorecard) {
  const status = scorecard.status;
  const contract = scorecard.research_contract;
  const acquisition = scorecard.acquisition;
  const structural = scorecard.structural_signals;
  const evidence = scorecard.evidence;
  const lines = [
    "# Autonomous Research Scorecard",
    "",
    "Overall: **" + status.overall + "**",
    "Execution: **" + status.execution + "**",
    "Research contract: **" + status.research_contract + "** (" + contract.passed + "/" + contract.queries + " passed)",
    "Acquisition clean: **" + status.acquisition_clean + "**",
    "",
    "## Evidence tier",
    "",
    "- Minimum aggregate tier: " + evidence.minimum_tier,
    "- Component tiers: " + evidence.component_tiers.join(", "),
    "- Live-provider claim allowed: False",
    "- Integration-runtime claim allowed: False",
    "- Production-readiness claim allowed: False",
    "- Field-level correctness oracle: False",
    "",
    "## Research contract coverage",
    "",
    "- Project queries: " + contract.project_query_count + " (" + contract.project_query_rate + ")",
    "- Query categories: " + contract.category_count,
    "- Source families: " + contract.source_family_count,
    "- Temporal modes: " + JSON.stringify(contract.temporal_modes),
    "",
    "## Acquisition performance",
    "",
    "- Targets selected: " + scorecard.selected_targets,
    "- Cycles: " + scorecard.cycles,
    "- Observations: " + scorecard.total_observations,
    "- Usable observation rate: " + acquisition.usable_observation_rate,
    "- Operational failure rate: " + acquisition.operational_failure_rate,
    "- Error rate: " + acquisition.error_rate,
    "- Blocked rate: " + acquisition.blocked_rate,
    "- Resource-limited rate: " + acquisition.resource_limited_rate,
    "- Empty rate: " + acquisition.empty_rate,
    "",
    "## Structural acquisition signals",
    "",
    "- Measured observations: " + structural.observations_measured,
    "- Product-candidate observation rate: " + structural.product_candidate_observation_rate,
    "- Product-candidate hints: " + structural.product_candidates_total,
    "- JSON-LD observation rate: " + structural.jsonld_observation_rate,
    "- JSON-LD blocks: " + structural.jsonld_blocks_total,
    "- Weighted median latency (shard medians): " + structural.weighted_median_latency_ms + " ms",
    "- Maximum shard-local p95 latency: " + structural.max_shard_p95_latency_ms + " ms",
    "- Evidence scope: " + structural.evidence_scope,
    "",
    "## Measurement gaps",
    "",
  ];
  lines.push(...scorecard.measurement_gaps.map(gap => "- " + gap));
  lines.push("", "## Targets with failures", "");
  if (scorecard.targets_with_failures.length) {
    lines.push("| Target | Observations | Failures | Failure rate | HTTP statuses |", "|---|---:|---:|---:|---|");
    for (const target of scorecard.targets_with_failures) {
      const http = Object.entries(target.http_status_counts).map(([k,v]) => k + ":" + v).join(", ") || "-";
      lines.push("| " + target.url + " | " + target.observations + " | " + target.failures + " | " + target.failure_rate + " | " + http + " |");
    }
  } else {
    lines.push("No target-level failures were recorded.");
  }
  return lines.join("\n") + "\n";
}

export function main(argv = process.argv.slice(2)) {
  const args = Object.fromEntries(argv.reduce((acc, value, i, all) => {
    if (value.startsWith("--")) acc.push([value.slice(2), all[i + 1] || ""]);
    return acc;
  }, []));
  if (!args.root || !args["json-output"] || !args["markdown-output"]) throw new Error("--root, --json-output and --markdown-output are required");
  const scorecard = buildScorecard(path.resolve(args.root));
  const jsonOutput = path.resolve(args["json-output"]);
  const markdownOutput = path.resolve(args["markdown-output"]);
  fs.mkdirSync(path.dirname(jsonOutput), {recursive:true});
  fs.mkdirSync(path.dirname(markdownOutput), {recursive:true});
  fs.writeFileSync(jsonOutput, JSON.stringify(scorecard, null, 2) + "\n", "utf8");
  fs.writeFileSync(markdownOutput, renderMarkdown(scorecard), "utf8");
  process.stdout.write(JSON.stringify(scorecard, null, 2) + "\n");
  return 0;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  try { main(); } catch (error) { process.stderr.write(String(error?.message || error) + "\n"); process.exitCode = 1; }
}
