#!/usr/bin/env node
/** Validate code-to-document synchronization maps. */
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"..");
const MAP_REL="docs/CODE_DOCUMENTATION_SYNC_MAP.json";
function git(root,args){const r=spawnSync("git",args,{cwd:root,encoding:"utf8",stdio:["ignore","pipe","pipe"]});if(r.status!==0)throw new Error(String(r.stderr||"git failed"));return String(r.stdout||"").split(/\r?\n/).filter(Boolean);}
function tracked(root){return spawnSync("git",["ls-files","-z"],{cwd:root,encoding:"buffer"}).stdout.toString().split("\0").filter(Boolean);}
function changed(root,base){return git(root,["diff","--name-only",base+"...HEAD"]);}
function globToRegex(pattern){
  let p=pattern.replaceAll("\\","/");
  if(p.endsWith("/**")) return {prefix:p.slice(0,-3)};
  let out="^";
  for(let i=0;i<p.length;i++){
    const ch=p[i];
    if(ch==="*"&&p[i+1]==="*"){i++;out+=".*";}
    else if(ch==="*"){out+="[^/]*";}
    else if("?+.^$()[]{}|".includes(ch)) out+="\\"+ch;
    else if(ch==="/") out+="/";
    else out+=ch;
  }
  return {regex:new RegExp(out+"$")};
}
export function matches(p,pattern){
  p=p.replaceAll("\\","/"); const g=globToRegex(pattern.replaceAll("\\","/"));
  return g.prefix!==undefined?p.startsWith(g.prefix):g.regex.test(p);
}
export function validate(root,changedPaths=null,strict=false){
  const trackedFiles=tracked(root), trackedSet=new Set(trackedFiles);
  const data=JSON.parse(fs.readFileSync(path.join(root,MAP_REL),"utf8"));
  if(data.schema_version!=="code-doc-sync/v1") throw new Error("unsupported code-doc-sync schema");
  if(!Array.isArray(data.groups)) throw new Error("groups must be a list");
  const issues=[],seen=new Set(),rows=[];
  for(const group of data.groups){
    const gid=String(group.id??"");
    if(!gid||seen.has(gid)){issues.push({rule:"unique-group-id",group:gid,severity:"error"});continue;}
    seen.add(gid);
    const codePaths=group.code_paths||[],docs=group.docs||[];
    if(!codePaths.length||!docs.length){issues.push({rule:"nonempty-group",group:gid,severity:"error"});continue;}
    const missing=docs.filter(d=>!trackedSet.has(d)); if(missing.length) issues.push({rule:"mapped-document-missing",group:gid,paths:missing,severity:"error"});
    const matched=trackedFiles.filter(p=>codePaths.some(pat=>matches(p,pat)));
    if(!matched.length) issues.push({rule:"code-pattern-no-match",group:gid,severity:"error"});
    const cp=changedPaths??new Set(), changedCode=[...cp].filter(p=>codePaths.some(pat=>matches(p,pat))), changedDocs=[...cp].filter(p=>docs.includes(p));
    let require=group.require_doc_update===undefined?true:group.require_doc_update;
    if(typeof require!=="boolean"){issues.push({rule:"boolean-require-doc-update",group:gid,severity:"error"});require=true;}
    const exemption=String(group.sync_exemption_reason??"").trim();
    if(require===false&&!exemption) issues.push({rule:"sync-exemption-reason-required",group:gid,severity:"error"});
    if(require&&changedCode.length&&!changedDocs.length) issues.push({rule:"code-change-missing-documentation",group:gid,changed_code_count:changedCode.length,severity:"error"});
    rows.push({id:gid,matched_code_count:matched.length,changed_code_count:changedCode.length,changed_doc_count:changedDocs.length,require_doc_update:require,has_sync_exemption:Boolean(exemption)});
  }
  return {schema_version:"code-doc-sync-report/v1",repository:path.basename(root),groups:rows,issues,passed:!issues.some(x=>x.severity==="error"),strict};
}
if(fileURLToPath(import.meta.url)===process.argv[1]){
  const valueFlags=new Set(["root","changed-from","report"]);
  const boolFlags=new Set(["all","strict","summary-only"]);
  const a={};
  for(let i=2;i<process.argv.length;i++){
    const token=process.argv[i];
    if(!token.startsWith("--")) continue;
    const key=token.slice(2);
    if(boolFlags.has(key)) a[key]=true;
    else if(valueFlags.has(key)) a[key]=process.argv[++i]??"";
    else a[key]=process.argv[++i]??"";
  }
  const root=path.resolve(a.root??"."); let changedPaths=null; if(a["changed-from"]&&!a.all) changedPaths=new Set(changed(root,a["changed-from"]));
  const report=validate(root,changedPaths,Boolean(a.strict));
  if(a.report){fs.mkdirSync(path.dirname(path.resolve(a.report)),{recursive:true});fs.writeFileSync(path.resolve(a.report),JSON.stringify(report,null,2)+"\n");}
  if(a["summary-only"]) console.log(JSON.stringify({groups:report.groups.length,issues:report.issues.length,passed:report.passed},null,2));
  else console.log(JSON.stringify(report,null,2));
  process.exitCode=(report.passed||!a.strict)?0:1;
}
