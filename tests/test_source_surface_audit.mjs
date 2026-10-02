import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { audit } from "../tools/source_surface_audit.mjs";

test("source-surface audit preserves severity thresholds", () => {
  const root=fs.mkdtempSync(path.join(os.tmpdir(),"surface-audit-"));
  const out=path.join(root,"out");
  try {
    fs.writeFileSync(path.join(root,"small.ts"), "export const x = 1;\n");
    fs.writeFileSync(path.join(root,"large.py"), "x=1\n".repeat(700));
    const result=audit([root],{criticalBytes:50000,criticalLines:1000,attentionBytes:25,attentionLines:500});
    assert.equal(result.schema,"source-surface-audit/v1");
    assert.equal(result.critical_code_count,0);
    assert.equal(result.attention_code_count,1);
    assert.equal(result.rows[0].path,"large.py");
  } finally {
    fs.rmSync(root,{recursive:true,force:true});
  }
});

test("governance Node ports exist and are standalone", () => {
  for(const file of [
    "tools/source_surface_audit.mjs",
    "tools/code_documentation_sync.mjs",
    "tools/repository_hygiene.mjs",
  ]){
    const content=fs.readFileSync(file,"utf8");
    assert.ok(content.includes('from "node:'));
    assert.ok(content.includes("process.exitCode"));
  }
});
