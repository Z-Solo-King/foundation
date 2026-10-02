import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export function clamp(value, min = 0, max = 1) {
  return Math.min(max, Math.max(min, Number.isFinite(value) ? value : min));
}

export function positive(value, fallback = 0) {
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

export function stableJson(value) {
  if (Array.isArray(value)) return '[' + value.map(stableJson).join(',') + ']';
  if (value && typeof value === 'object') return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + stableJson(value[key])).join(',') + '}';
  return JSON.stringify(value);
}

export function sha256(value) {
  return crypto.createHash('sha256').update(Buffer.isBuffer(value) ? value : String(value)).digest('hex');
}

export function digestObject(value) {
  return sha256(stableJson(value));
}

export function fingerprintObject(value, size = 16) {
  return digestObject(value).slice(0, size);
}

export function walkFiles(root, {skip = new Set()} = {}) {
  const files = [];
  const stack = [root];
  while (stack.length) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, {withFileTypes:true})) {
      if (skip.has(entry.name)) continue;
      const full = path.join(current, entry.name);
      if (entry.isDirectory()) stack.push(full);
      else if (entry.isFile()) files.push(path.relative(root, full).replaceAll(path.sep, '/'));
    }
  }
  return files.sort();
}

export function readText(root, rel, max = 1_000_000) {
  try {
    return fs.readFileSync(path.join(root, rel)).subarray(0, max).toString('utf8');
  } catch {
    return '';
  }
}

function resolvePath(root, rel) {
  return root instanceof URL ? new URL(rel, root) : path.join(root, rel);
}

export function exists(root, rel) {
  return fs.existsSync(resolvePath(root, rel));
}

export function parseTime(value) {
  if (typeof value !== 'string' || !value.trim()) return null;
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function freshnessScore(observedAt, maxAgeMs, now = new Date()) {
  const when = parseTime(observedAt);
  if (!when || !(maxAgeMs > 0)) return 0;
  const age = Math.max(0, now.getTime() - when.getTime());
  if (age <= maxAgeMs) return 1;
  return clamp(maxAgeMs / age);
}
