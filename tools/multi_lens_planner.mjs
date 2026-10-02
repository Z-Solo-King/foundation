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

  // Weighted evidence value is deliberately bounded and numerically stable.
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


function adaptiveExecutionPolicy(input, defaults) {
  const policy = input.execution_policy && typeof input.execution_policy === "object"
    ? input.execution_policy
    : (defaults.execution_policy && typeof defaults.execution_policy === "object" ? defaults.execution_policy : {});
  const mode = String(policy.mode || "static");
  const adaptive = mode === "adaptive";
  const rawLevels = Array.isArray(policy.lane_levels) ? policy.lane_levels : [0, 2, 4, 6, 8];
  const laneLevels = [...new Set(rawLevels.map((x) => Math.max(0, Math.floor(Number(x) || 0))))]
    .filter((x) => x >= 0 && x <= 32)
    .sort((a, b) => a - b);
  const ambiguity = clamp(policy.ambiguity ?? 0);
  const evidenceGain = clamp(policy.evidence_gain ?? 0);
  const tokenBudget = Math.max(0, Math.floor(Number(policy.token_budget) || 0));
  const tokensPerLane = Math.max(1, Math.floor(Number(policy.tokens_per_lane) || 256));
  const requestedMax = Math.max(1, Number(input.max_lanes ?? defaults.max_lanes) || 6);
  if (!adaptive) {
    return {
      mode: "static",
      ambiguity,
      evidence_gain: evidenceGain,
      token_budget: tokenBudget,
      tokens_per_lane: tokensPerLane,
      candidate_lane_cap: Math.max(0, Math.floor(requestedMax)),
      lane_cap_reason: "static-planner-budget",
      stop: policy.stop && typeof policy.stop === "object" ? policy.stop : {},
    };
  }
  let desired;
  if (ambiguity < 0.35 || evidenceGain < 0.35) desired = 0;
  else if (ambiguity >= 0.80 && evidenceGain >= 0.70) desired = 6;
  else if (ambiguity >= 0.60 || evidenceGain >= 0.60) desired = 4;
  else desired = 2;
  const availableByTokenBudget = tokenBudget > 0 ? Math.floor(tokenBudget / tokensPerLane) : 0;
  const effective = Math.min(requestedMax, desired, availableByTokenBudget);
  const snapped = laneLevels.filter((x) => x <= effective).pop() ?? 0;
  let reason = "adaptive-evidence-and-budget";
  if (tokenBudget <= 0) reason = "adaptive-token-budget-zero";
  else if (snapped === 0) reason = "adaptive-signal-or-budget-insufficient";
  return {
    mode: "adaptive",
    ambiguity,
    evidence_gain: evidenceGain,
    token_budget: tokenBudget,
    tokens_per_lane: tokensPerLane,
    candidate_lane_cap: snapped,
    lane_cap_reason: reason,
    stop: policy.stop && typeof policy.stop === "object" ? policy.stop : {},
  };
}

function plan(input) {
  const defaults = input.target_defaults && typeof input.target_defaults === "object"
    ? input.target_defaults
    : {};
  const execution = adaptiveExecutionPolicy(input, defaults);
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
  const requestedRequiredIds = new Set(Array.isArray(input.required_ids) ? input.required_ids : []);
  const requiredFamilies = new Set(Array.isArray(input.required_families) ? input.required_families : []);
  const disabledIds = new Set(Array.isArray(input.disabled_ids) ? input.disabled_ids : []);

  const rows = [];
  const byId = new Map();
  const errors = [];

  for (const lane of lanes) {
    if (!lane || typeof lane.id !== "string" || !lane.family) continue;
    if (disabledIds.has(lane.id) || lane.enabled === false) {
      if (lane.required === true || requestedRequiredIds.has(lane.id) || requiredFamilies.has(lane.family)) {
        errors.push({
          code: "disabled_required_lane",
          lane_id: lane.id,
          message: "a required lane is disabled and cannot satisfy the schedule",
        });
      }
      continue;
    }

    if (byId.has(lane.id)) {
      errors.push({
        code: "duplicate_lane_id",
        lane_id: lane.id,
        message: "duplicate lane IDs are not schedulable",
      });
      continue;
    }

    const scored = scoreLane(lane, target, history, new Set());
    const row = {
      id: lane.id,
      family: lane.family,
      required: lane.required === true,
      depends_on: Array.isArray(lane.depends_on) ? [...new Set(lane.depends_on.filter(Boolean))] : [],
      exclusive_group: lane.exclusive_group || null,
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

    rows.push(row);
    byId.set(row.id, row);
  }

  for (const id of requestedRequiredIds) {
    if (!byId.has(id)) {
      errors.push({
        code: "unknown_required_lane",
        lane_id: id,
        message: "required lane is missing or disabled",
      });
    }
  }

  const requiredIds = new Set(requestedRequiredIds);
  for (const row of rows) {
    if (row.required || requiredFamilies.has(row.family)) requiredIds.add(row.id);
  }

  // Required dependency closure: a required lane pulls its prerequisites into the required set.
  const closureQueue = [...requiredIds];
  while (closureQueue.length) {
    const id = closureQueue.shift();
    const row = byId.get(id);
    if (!row) continue;

    for (const dependencyId of row.depends_on) {
      if (!byId.has(dependencyId)) {
        errors.push({
          code: "missing_dependency",
          lane_id: id,
          dependency_id: dependencyId,
          message: "required lane dependency is missing or disabled",
        });
        continue;
      }
      if (!requiredIds.has(dependencyId)) {
        requiredIds.add(dependencyId);
        closureQueue.push(dependencyId);
      }
    }
  }

  const mandatory = rows.filter((row) => requiredIds.has(row.id));
  const candidates = rows.filter((row) => !requiredIds.has(row.id));

  const selected = [];
  const skipped = [];
  const families = new Set();
  const exclusiveGroups = new Set();

  let cost = 0;
  let latency = 0;
  let quota = 0;
  let adaptiveSelected = 0;

  function canFit(row, selection = "adaptive") {
    const candidateCapacity = selection === "required"
      ? Number.POSITIVE_INFINITY
      : execution.candidate_lane_cap;
    return (
      selected.length < target.max_lanes &&
      adaptiveSelected < candidateCapacity &&
      cost + row.estimated.cost <= target.cost_budget &&
      latency + row.estimated.latency <= target.latency_budget &&
      quota + row.estimated.quota <= target.quota_budget
    );
  }

  function dependenciesSatisfied(row) {
    return row.depends_on.every((id) => selected.some((x) => x.id === id));
  }

  function conflicts(row) {
    return row.exclusive_group && exclusiveGroups.has(row.exclusive_group);
  }

  function commit(row, selection) {
    const dependencyBatches = row.depends_on
      .map((id) => selected.find((x) => x.id === id)?.batch)
      .filter((value) => Number.isInteger(value));

    const batch = dependencyBatches.length ? Math.max(...dependencyBatches) + 1 : 0;
    const materialized = { ...row, selection, required: requiredIds.has(row.id), batch };
    selected.push(materialized);
    if (selection !== "required") adaptiveSelected += 1;
    families.add(row.family);
    if (row.exclusive_group) exclusiveGroups.add(row.exclusive_group);
    cost += row.estimated.cost;
    latency += row.estimated.latency;
    quota += row.estimated.quota;
  }

  // Resolve required lanes in dependency order. Cycles are explicit infeasibility.
  const pendingMandatory = new Set(mandatory.map((row) => row.id));
  while (pendingMandatory.size) {
    let progress = false;

    for (const row of mandatory) {
      if (!pendingMandatory.has(row.id)) continue;
      if (!dependenciesSatisfied(row)) continue;
      pendingMandatory.delete(row.id);
      progress = true;

      if (conflicts(row)) {
        skipped.push({
          ...row,
          selection: "required-but-blocked",
          skip_reason: "exclusive_group_conflict",
        });
        errors.push({
          code: "required_exclusive_conflict",
          lane_id: row.id,
          exclusive_group: row.exclusive_group,
          message: "two required lanes cannot occupy the same exclusive group",
        });
        continue;
      }

      if (!canFit(row, "required")) {
        skipped.push({
          ...row,
          selection: "required-but-blocked",
          skip_reason: "budget_or_lane_limit",
        });
        errors.push({
          code: "required_budget_conflict",
          lane_id: row.id,
          message: "required lanes do not fit the declared execution budget",
        });
        continue;
      }

      commit(row, "required");
    }

    if (!progress) {
      for (const id of pendingMandatory) {
        const row = byId.get(id);
        if (row) {
          skipped.push({
            ...row,
            selection: "required-but-blocked",
            skip_reason: "dependency_cycle",
          });
        }
        errors.push({
          code: "dependency_cycle",
          lane_id: id,
          message: "required dependency graph could not be resolved",
        });
      }
      pendingMandatory.clear();
    }
  }

  // Once required constraints are feasible, choose adaptive candidates.
  if (errors.length === 0) {
    candidates.sort((a, b) => b.score - a.score || a.id.localeCompare(b.id));

    // Dependency-aware candidate selection: defer unresolved dependencies instead
    // of incorrectly converting them into permanent skips just because a
    // dependency sorts later in the score order.
    const pending = new Set(candidates.map((row) => row.id));
    let progress = true;

    while (pending.size && progress) {
      progress = false;

      for (const row of candidates) {
        if (!pending.has(row.id)) continue;
        if (!dependenciesSatisfied(row)) continue;

        pending.delete(row.id);
        progress = true;

        if (conflicts(row)) {
          skipped.push({
            ...row,
            selection: "candidate",
            skip_reason: "exclusive_group_conflict",
          });
          continue;
        }

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

        if (
          sameFamily &&
          weakestSelected &&
          diversityAdjusted < weakestSelected.score * 1.03
        ) {
          skipped.push({
            ...row,
            selection: "candidate",
            skip_reason: "diversity_penalty",
          });
          continue;
        }

        commit(row, "adaptive");
      }
    }

    // Anything still pending has an unavailable dependency (including a
    // dependency that was skipped by conflict/budget rules) or a cycle.
    for (const row of candidates) {
      if (!pending.has(row.id)) continue;
      pending.delete(row.id);
      skipped.push({
        ...row,
        selection: "candidate",
        skip_reason: "missing_dependency",
      });
    }
  } else {
    for (const row of candidates) {
      skipped.push({
        ...row,
        selection: "candidate",
        skip_reason: "required_constraints_infeasible",
      });
    }
  }

  // Record disabled/invalid input explicitly.
  for (const lane of lanes) {
    if (!lane || !lane.id || !lane.family) continue;
    if (selected.some((x) => x.id === lane.id) || skipped.some((x) => x.id === lane.id)) continue;

    if (disabledIds.has(lane.id) || lane.enabled === false) {
      skipped.push({
        id: lane.id,
        family: lane.family,
        selection: "candidate",
        skip_reason: "disabled",
      });
    } else {
      skipped.push({
        id: lane.id,
        family: lane.family,
        selection: "candidate",
        skip_reason: "invalid_or_duplicate",
      });
    }
  }

  return {
    schema: "multi-lens-plan/v1",
    authority: "scheduling_only",
    feasible: errors.length === 0,
    errors,
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
    execution_policy: {
      mode: execution.mode,
      candidate_lane_cap: execution.candidate_lane_cap,
      lane_cap_reason: execution.lane_cap_reason,
      ambiguity: execution.ambiguity,
      evidence_gain: execution.evidence_gain,
      token_budget: execution.token_budget,
      tokens_per_lane: execution.tokens_per_lane,
      declared_stop: {
        mode: "evidence_gain",
        required_families: [...requiredFamilies].sort(),
        minimum_novel_evidence_gain: Number(execution.stop.minimum_novel_evidence_gain ?? 0.05),
        no_novel_rounds_before_stop: Math.max(1, Math.floor(Number(execution.stop.no_novel_rounds_before_stop) || 1)),
        required_constraints_must_complete: true,
        preserve_skipped_reasons: true,
      },
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
