import fs from 'node:fs';

export const SANCTIONED_WORKFLOWS = Object.freeze([
  'custom-website-product-feed-1249.yml',
]);

export function validateOperationsGuard({repository, mainBranch, workflowsPresent, workflowEntries = [], approvedSha}) {
  if (!repository || repository.private !== true) throw new Error('Operations repository must remain private');
  if (repository.default_branch !== 'main') throw new Error('Operations default branch must remain main');
  if (!mainBranch || mainBranch.name !== 'main') throw new Error('Operations main branch lookup failed');
  const mainSha = mainBranch?.sha || mainBranch?.commit?.sha || '';
  if (!/^[0-9a-f]{40}$/.test(mainSha)) throw new Error('Operations main SHA is invalid');

  const entries = Array.isArray(workflowEntries)
    ? workflowEntries.filter((value) => typeof value === 'string' && value.trim())
    : [];
  if (workflowsPresent && entries.length === 0) {
    throw new Error('Private Operations workflow inventory is present but entries were not supplied');
  }
  const unauthorized = entries.filter((name) => !SANCTIONED_WORKFLOWS.includes(name));
  if (unauthorized.length > 0) {
    throw new Error(`Private Operations contains unauthorized workflows: ${unauthorized.join(', ')}`);
  }

  if (!/^[0-9a-f]{40}$/.test(approvedSha || '')) throw new Error('approved Operations SHA is invalid');
  return {
    schema:'operations-main-integrity-receipt/v1',
    repository:repository.full_name,
    private:true,
    default_branch:repository.default_branch,
    observed_main_sha:mainSha,
    approved_sha:approvedSha,
    workflows: entries,
    status:mainSha===approvedSha?'APPROVED':'DRIFT'
  };
}

if (process.argv[1]?.endsWith('validate_operations_main_guard.mjs')) {
  const payload=JSON.parse(fs.readFileSync(process.argv[2] || 0,'utf8'));
  const receipt=validateOperationsGuard(payload);
  process.stdout.write(JSON.stringify(receipt,null,2)+'\n');
  if (receipt.status==='DRIFT') process.exitCode=2;
}
