#!/usr/bin/env node
"use strict";

/**
 * Deterministic, non-authoritative multi-lens planner.
 *
 * It chooses evidence/execution lanes; it never decides acceptance or policy.
 * Usage:
 *   node tools/multi_lens_planner.mjs < input.json
 */

function clamp(value, min = 0, max = 1) {
  return Math.min(max, Math.max(min, Number.isFinite(value) ? value : min));
}

function positive(value, fallback = 0) {
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function scoreLane(lane, target, history, selectedFamilies) {
  const h = history[lane.id] || {};
  const runs = Math.max(0, Number(h.runs) || 0);

  const coverage = clamp(lane.coverage_gain);
  const failure = clamp(lane.failure_detection);
  const confidence = clamp(lane.confidence_gain);
  const freshness = clamp(lane.freshness_need ?? target.freshness_need);
  const baseYield = runs > 0 ? clamp(h.novel_finding_rate) : clamp(lane.prior_yield ?? 0.5);

  const exploration = Math.min(
    0.35,
    Math.sqrt(Math.log1p(Math.max(1, target.total_verified_lanes || 1)) / (runs + 1)) / 3,
  );

  const novelty = clamp(baseYield + exploration);
  const learningQuality = runs > 0 ? clamp(h.evidence_acceptance_rate ?? 0.5) : 0.5;

  const rawBenefit =
    0.23 * coverage +
    0.18 * failure +
    0.14 * confidence +
    0.12 * freshness +
    0.18 * novelty +
    0.15 * learningQuality;

  const cost = positive(lane.execution_cost, 1);
  const latency = positive(lane.latency_cost, 1);
  const quota = positive(lane.quota_cost, 0);
  const budgetPenalty =
    0.45 * clamp(cost / Math.max(1, target.cost_budget)) +
    0.35 * clamp(latency / Math.max(1, target.latency_budget)) +
    0.20 * clamp(quota / Math.max(1, target.quota_budget));

  const familyPenalty = selectedFamilies.has(lane.family)
    ? clamp(lane.same_family_penalty ?? 0.08)
    : 0;

  return {
    score: rawBenefit / (1 + budgetPenalty + familyPenalty),
    components: {
      rawBenefit,
      budgetPenalty,
      familyPenalty,
      exploration,
      novelty,
    },
    runs,
  };
}

function plan(input) {
  const defaults = input.target_defaults && typeof input.target_defaults === "object"
    ? input.target_defaults
    : {};
  const target = {
    max_lanes: Math.max(1, Number(input.max_lanes ?? defaults.max_lanes) || 6),
    cost_budget: Math.max(1, Number(input.cost_budget ?? defaults.cost_budget) || 6),
    latency_budget: Math.max(1, Number(input.latency_budget ?? defaults.latency_budget) || 120),
    quota_budget: Math.max(1, Number(input.quota_budget ?? defaults.quota_budget) || 100),
    freshness_need: clamp(input.freshness_need ?? defaults.freshness_need ?? 0.5),
    total_verified_lanes: Math.max(
      1,
      Number(input.total_verified_lanes ?? defaults.total_verified_lanes) || 1,
    ),
  };

  const lanes = Array.isArray(input.lanes) ? input.lanes : [];
  const history = input.history && typeof input.history === "object" ? input.history : {};

  const mandatory = [];
  const candidates = [];

  for (const lane of lanes) {
    if (!lane || typeof lane.id !== "string" || !lane.family) continue;
    if (lane.enabled === false) continue;

    const scored = scoreLane(lane, target, history, new Set());
    const row = {
      id: lane.id,
      family: lane.family,
      required: lane.required === true,
      score: scored.score,
      components: scored.components,
      runs: scored.runs,
      reason: lane.reason || "",
      estimated: {
        cost: positive(lane.execution_cost, 1),
        latency: positive(lane.latency_cost, 1),
        quota: positive(lane.quota_cost, 0),
      },
    };

    if (lane.required === true) mandatory.push(row);
    else candidates.push(row);
  }

  const selected = [];
  const skipped = [];
  const families = new Set();
  let cost = 0;
  let latency = 0;
  let quota = 0;

  function canFit(row) {
    return (
      selected.length < target.max_lanes &&
      cost + row.estimated.cost <= target.cost_budget &&
      latency + row.estimated.latency <= target.latency_budget &&
      quota + row.estimated.quota <= target.quota_budget
    );
  }

  for (const row of mandatory) {
    if (canFit(row)) {
      selected.push({ ...row, selection: "required" });
      families.add(row.family);
      cost += row.estimated.cost;
      latency += row.estimated.latency;
      quota += row.estimated.quota;
    } else {
      skipped.push({
        ...row,
        selection: "required-but-blocked",
        skip_reason: "budget_or_lane_limit",
      });
    }
  }

  candidates.sort((a, b) => b.score - a.score || a.id.localeCompare(b.id));

  for (const row of candidates) {
    if (selected.some((x) => x.id === row.id)) continue;
    if (!canFit(row)) {
      skipped.push({
        ...row,
        selection: "candidate",
        skip_reason: "budget_or_lane_limit",
      });
      continue;
    }

    const sameFamily = families.has(row.family);
    const diversityAdjusted = sameFamily ? row.score * 0.90 : row.score * 1.05;
    const weakestSelected = selected
      .filter((x) => x.selection !== "required")
      .sort((a, b) => a.score - b.score)[0];

    if (sameFamily && weakestSelected && diversityAdjusted < weakestSelected.score * 1.03) {
      skipped.push({
        ...row,
        selection: "candidate",
        skip_reason: "diversity_penalty",
      });
      continue;
    }

    selected.push({ ...row, selection: "adaptive" });
    families.add(row.family);
    cost += row.estimated.cost;
    latency += row.estimated.latency;
    quota += row.estimated.quota;
  }

  for (const row of lanes) {
    if (
      row &&
      row.id &&
      !selected.some((x) => x.id === row.id) &&
      !skipped.some((x) => x.id === row.id)
    ) {
      skipped.push({
        id: row.id,
        family: row.family,
        selection: "candidate",
        skip_reason: "disabled_or_invalid",
      });
    }
  }

  return {
    schema: "multi-lens-plan/v1",
    authority: "scheduling_only",
    target: input.target || null,
    constraints: target,
    selected,
    skipped,
    totals: {
      lanes: selected.length,
      families: families.size,
      cost,
      latency,
      quota,
    },
  };
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString("utf8");
}

const raw = await readStdin();
if (!raw.trim()) {
  console.error("expected JSON input on stdin");
  process.exit(2);
}

let input;
try {
  input = JSON.parse(raw);
} catch {
  console.error("invalid JSON input");
  process.exit(2);
}

process.stdout.write(JSON.stringify(plan(input), null, 2) + "\n");
