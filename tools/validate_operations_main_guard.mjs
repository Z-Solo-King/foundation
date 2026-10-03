import fs from 'node:fs';

export function validateOperationsGuard({repository, mainBranch, comparison, workflowsPresent, approvedSha}) {
  if (!repository || repository.private !== true) throw new Error('Operations repository must remain private');
  if (repository.default_branch !== 'main') throw new Error('Operations default branch must remain main');
  if (!mainBranch || mainBranch.name !== 'main') throw new Error('Operations main branch lookup failed');
  const mainSha = mainBranch?.commit?.sha || '';
  if (!/^[0-9a-f]{40}$/.test(mainSha)) throw new Error('Operations main SHA is invalid');
  if (workflowsPresent) throw new Error('Private Operations must not contain .github/workflows');
  if (!/^[0-9a-f]{40}$/.test(approvedSha || '')) throw new Error('approved Operations SHA is invalid');
  if (!comparison || !['ahead','identical'].includes(comparison.status)) throw new Error('approved Operations SHA is not an ancestor of main');
  if (comparison.base_commit?.sha && comparison.base_commit.sha !== approvedSha) throw new Error('comparison base does not match approved Operations SHA');
  if (comparison.head_commit?.sha && comparison.head_commit.sha !== mainSha) throw new Error('comparison head does not match Operations main SHA');
  return {schema:'operations-main-integrity-receipt/v2',repository:'Z-Solo-King/operations',private:true,default_branch:'main',workflows_present:false,approved_lineage_verified:true,status:'APPROVED_LINEAGE'};
}

if (process.argv[1]?.endsWith('validate_operations_main_guard.mjs')) {
  const payload=JSON.parse(fs.readFileSync(process.argv[2] || 0,'utf8'));
  const receipt=validateOperationsGuard(payload);
  process.stdout.write(JSON.stringify(receipt,null,2)+'\n');
  if (receipt.status!=='APPROVED_LINEAGE') process.exitCode=2;
}
