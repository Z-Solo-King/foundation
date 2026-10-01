import fs from 'node:fs';

export function validateOperationsGuard({ repository, mainBranch, workflowsPresent, approvedSha }) {
  if (!repository || repository.private !== true) throw new Error('Operations repository must remain private');
  if (repository.default_branch !== 'main') throw new Error('Operations default branch must remain main');
  if (!mainBranch || mainBranch.name !== 'main') throw new Error('Operations main branch lookup failed');
  if (!/^[0-9a-f]{40}$/.test(mainBranch.sha || '')) throw new Error('Operations main SHA is invalid');
  if (workflowsPresent) throw new Error('Private Operations must not contain .github/workflows');
  if (!/^[0-9a-f]{40}$/.test(approvedSha || '')) throw new Error('approved Operations SHA is invalid');

  return {
    schema: 'operations-main-integrity-receipt/v1',
    repository: repository.full_name,
    private: repository.private === true,
    default_branch: repository.default_branch,
    observed_main_sha: mainBranch.sha,
    approved_sha: approvedSha,
    status: mainBranch.sha === approvedSha ? 'APPROVED' : 'DRIFT',
  };
}

if (process.argv[1]?.endsWith('validate_operations_main_guard.mjs')) {
  const payload = JSON.parse(fs.readFileSync(process.argv[2] || 0, 'utf8'));
  const receipt = validateOperationsGuard(payload);
  process.stdout.write(JSON.stringify(receipt, null, 2) + '\n');
  if (receipt.status === 'DRIFT') process.exitCode = 2;
}
