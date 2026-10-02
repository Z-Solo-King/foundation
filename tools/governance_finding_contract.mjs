import { createHash } from 'node:crypto';

const EVIDENCE_ORDER = Object.freeze({ L0: 0, L1: 1, L2: 2, L3: 3, L4: 4 });
const SEVERITY_TO_EVIDENCE = Object.freeze({ info: 'L1', attention: 'L2', warning: 'L2', error: 'L2', critical: 'L2' });
const SEVERITY_TO_RISK = Object.freeze({ info: 'low', attention: 'medium', warning: 'high', error: 'high', critical: 'critical' });
const MUTATION_BY_SEVERITY = Object.freeze({ info: 'none', attention: 'review', warning: 'review', error: 'bounded', critical: 'blocked_until_verified' });

export function stableDedupeKey(finding) {
  const basis = [
    String(finding.code ?? ''),
    String(finding.lane ?? ''),
    String(finding.category ?? ''),
    ...(Array.isArray(finding.paths) ? finding.paths.slice().sort() : []),
  ].join('|');
  return createHash('sha256').update(basis).digest('hex').slice(0, 20);
}

export function normalizeFinding(finding) {
  if (!finding || typeof finding !== 'object') throw new Error('finding must be an object');
  const severity = String(finding.severity ?? 'info');
  const evidenceLevel = EVIDENCE_ORDER[finding.evidence_level] !== undefined
    ? finding.evidence_level
    : SEVERITY_TO_EVIDENCE[severity] ?? 'L1';
  const riskClass = SEVERITY_TO_RISK[severity] ?? 'medium';
  return {
    ...finding,
    risk_class: riskClass,
    evidence_level: evidenceLevel,
    evidence_sufficiency: evidenceLevel === 'L4' ? 'production' : evidenceLevel === 'L3' ? 'execution' : evidenceLevel === 'L2' ? 'repository' : 'source',
    mutation_policy: MUTATION_BY_SEVERITY[severity] ?? 'review',
    dedupe_key: String(finding.dedupe_key || stableDedupeKey(finding)),
    requires_fresh_runtime_evidence: Boolean(
      finding.requires_fresh_runtime_evidence
      ?? ['critical'].includes(severity)
      ?? false,
    ),
  };
}

export function reconcileFindings(reports) {
  const byKey = new Map();
  for (const report of reports ?? []) {
    for (const finding of report?.findings ?? []) {
      const item = normalizeFinding(finding);
      const existing = byKey.get(item.dedupe_key);
      if (!existing || EVIDENCE_ORDER[item.evidence_level] > EVIDENCE_ORDER[existing.evidence_level]) {
        byKey.set(item.dedupe_key, item);
      }
    }
  }
  return [...byKey.values()].sort((a, b) => {
    const risk = { critical: 0, high: 1, medium: 2, low: 3 };
    return (risk[a.risk_class] - risk[b.risk_class])
      || String(a.lane).localeCompare(String(b.lane))
      || String(a.code).localeCompare(String(b.code));
  });
}

export function buildAdaptivePriority(findings, lanes) {
  const material = new Set(
    (findings ?? [])
      .filter((f) => f.risk_class === 'critical' || f.risk_class === 'high')
      .map((f) => f.lane),
  );
  return [...(lanes ?? [])]
    .map((lane) => {
      let score = Number(lane.prior_yield ?? 0);
      if (material.has(lane.family) || material.has(lane.id)) score += 1.5;
      return { ...lane, priority_score: Number(score.toFixed(3)) };
    })
    .sort((a, b) => b.priority_score - a.priority_score);
}
