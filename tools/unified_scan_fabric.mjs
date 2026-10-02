import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

export const LENSES = Object.freeze([
  {id:'typescript-breadth', language:'typescript', role:'breadth', objective:'complete fast inventory, partitioning, metadata and workflow/config checks'},
  {id:'rust-quality', language:'rust', role:'quality', objective:'deep deterministic source-quality, normalization and resource-sensitive checks'},
  {id:'go-fanout', language:'go', role:'fanout', objective:'bounded concurrent probes and differential runtime checks'},
  {id:'security', language:'language-neutral', role:'adversarial', objective:'secrets, trust boundaries, unsafe mutation and injection paths'},
  {id:'cloudflare-runtime', language:'external', role:'runtime', objective:'live Workers, Pages, D1, deployment and schedule evidence'},
  {id:'policy-reconciler', language:'language-neutral', role:'reconcile', objective:'ownership, duplicate authority, drift and evidence lineage'}
]);

const IGNORED = new Set(['.git','node_modules','.venv','__pycache__','target','dist','build']);

export function inventory(root) {
  const rows = [];
  const stack = [root];
  while (stack.length) {
    const dir = stack.pop();
    for (const entry of fs.readdirSync(dir,{withFileTypes:true})) {
      if (IGNORED.has(entry.name)) continue;
      const full = path.join(dir,entry.name);
      if (entry.isDirectory()) stack.push(full);
      else {
        const rel = path.relative(root,full).replaceAll(path.sep,'/');
        const stat = fs.statSync(full);
        const hash = crypto.createHash('sha256').update(fs.readFileSync(full)).digest('hex');
        rows.push({path:rel,bytes:stat.size,sha256:hash,extension:path.extname(rel).toLowerCase()});
      }
    }
  }
  return rows.sort((a,b)=>a.path.localeCompare(b.path));
}

export function disposition(file) {
  const source = new Set(['.py','.js','.mjs','.cjs','.ts','.tsx','.rs','.go','.php','.java','.kt','.swift','.rb','.cs','.cpp','.c','.h','.hpp','.sh']);
  if (source.has(file.extension)) return 'SCANNED';
  if (['.json','.yml','.yaml','.toml','.md','.txt','.lock'].includes(file.extension)) return 'DELEGATED';
  return 'NOT_APPLICABLE';
}

export function buildPlan(files, {changedPaths=[]}={}) {
  const changed = new Set(changedPaths);
  const rows = files.map(file => {
    const d = disposition(file);
    const risk = changed.has(file.path) || /(^|\/)(.github|private|security|auth|worker|runtime|polyglot|extractor_mapper)(\/|$)/i.test(file.path);
    return {
      path:file.path,status:d,priority:risk?'deep':'standard',
      lenses:risk ? LENSES.map(x=>x.id) : ['typescript-breadth','policy-reconciler']
    };
  });
  return {schema_version:'unified-scan-fabric/v1',total:rows.length,covered:rows.length,rows};
}

export function reconcile(findings) {
  const groups = new Map();
  for (const f of findings) {
    const key = f.invariant || f.id || f.message;
    if (!groups.has(key)) groups.set(key,[]);
    groups.get(key).push(f);
  }
  return [...groups.entries()].map(([key,rows]) => ({
    key,observations:rows.length,
    sources:[...new Set(rows.map(x=>x.source))].sort(),
    corroborated:new Set(rows.map(x=>x.source)).size > 1,
    disagreements:rows.filter(x=>x.disposition==='disputed').length
  }));
}

export function assertComplete(plan) {
  if (plan.total !== plan.covered) throw new Error('coverage_incomplete');
  for (const row of plan.rows) if (!row.path || !row.status) throw new Error('invalid_disposition');
  return true;
}