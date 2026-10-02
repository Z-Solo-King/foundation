#!/usr/bin/env node
/** Repository hygiene and uniform-format gate. */
import fs from "node:fs";
import path from "node:path";
import fnmatch from "node:module";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const CONTRACT_REL="docs/REPOSITORY_HYGIENE_FORMAT_CONTRACT.json";
const TEXT_EXTENSIONS=new Set([".bash",".cjs",".conf",".css",".cfg",".fish",".html",".ini",".json",".jsonc",".mjs",".md",".properties",".ps1",".py",".scss",".sh",".sql",".svg",".toml",".ts",".tsx",".txt",".xml",".yaml",".yml"]);
const FORMATTER_EXTENSIONS=new Set([".cjs",".json",".jsonc",".js",".mjs",".md",".py",".ts",".tsx",".yaml",".yml"]);
const FORBIDDEN_TRACKED=["**/__pycache__/**","*.coverage","*.pyc","*.pyo",".pytest_cache/**","coverage.xml","htmlcov/**","node_modules/**",".DS_Store"];
const DATE_NAME_RE=/(?:19|20)\d{2}[-_]\d{2}[-_]\d{2}/;
const TAB_RE=/^\t+/;
function sh(root,args){const r=spawnSync("git",args,{cwd:root,encoding:"utf8",stdio:["ignore","pipe","pipe"]});if(r.status!==0)throw new Error(String(r.stderr||"git failed"));return String(r.stdout||"").split(/\r?\n/).filter(Boolean);}
function tracked(root){return spawnSync("git",["ls-files","-z"],{cwd:root,encoding:"buffer"}).stdout.toString().split("\0").filter(Boolean);}
function globMatch(pat,value){
  pat=pat.replaceAll("\\","/"); value=value.replaceAll("\\","/");
  if(pat.endsWith("/**")) return value.startsWith(pat.slice(0,-3));
  let s="^"; for(let i=0;i<pat.length;i++){const ch=pat[i];if(ch==="*"&&pat[i+1]==="*"){i++;s+=".*";}else if(ch==="*"){s+="[^/]*";}else if("?+.^$()[]{}|".includes(ch))s+="\\"+ch;else s+=ch;} return new RegExp(s+"$").test(value);
}
function select(root,allFiles,base){const files=tracked(root);if(allFiles)return [files,false];if(base){const set=new Set(files);return [sh(root,["diff","--name-only",base+"...HEAD"]).filter(p=>set.has(p)),true];}return [files,false];}
function isText(p){return TEXT_EXTENSIONS.has(path.extname(p).toLowerCase())||["AGENTS.md","Caddyfile","Containerfile","Dockerfile","GNUmakefile","Makefile","README.md"].includes(path.basename(p));}
function isFormatter(p){return FORMATTER_EXTENSIONS.has(path.extname(p).toLowerCase());}
function forbidden(p){const n=p.replaceAll("\\","/");return FORBIDDEN_TRACKED.some(x=>globMatch(x,n));}
function checkBytes(full,rel){
  const raw=fs.readFileSync(full), issues=[]; if(raw.includes(0))return[{rule:"binary-control",path:rel,severity:"error"}];
  let text; try{text=raw.toString("utf8");if(Buffer.from(text,"utf8").length!==raw.length)throw new Error();}catch{return[{rule:"utf8",path:rel,severity:"error"}];}
  if(text.includes("\r\n")||text.includes("\r"))issues.push({rule:"lf-only",path:rel,severity:"error"});
  if(raw.length&&!raw.subarray(-1).equals(Buffer.from("\n")))issues.push({rule:"final-newline",path:rel,severity:"error"});
  if(text.split("\n").some(line=>/[ \t]+$/.test(line)))issues.push({rule:"trailing-whitespace",path:rel,severity:"error"});
  const name=path.basename(rel),ext=path.extname(rel).toLowerCase(); if(name!=="Makefile"&&name!=="GNUmakefile"&&ext!==".mk"&&text.split("\n").some(line=>TAB_RE.test(line)))issues.push({rule:"tab-indentation",path:rel,severity:"error"});
  return issues;
}
function checkMarkdownName(rel){const p=path.parse(rel);if(p.ext.toLowerCase()!==".md")return[];const normalized=rel.replaceAll("\\","/");const allowed=["docs/history/","docs/HISTORY/","docs/feed-lab/","docs/runtime/"];return DATE_NAME_RE.test(p.base)&&!allowed.some(x=>normalized.startsWith(x))?[{rule:"date-named-canonical-doc",path:rel,severity:"error"}]:[];}
function checkSize(full,rel,changedMode){const ext=path.extname(rel).toLowerCase();if(!new Set([".py",".js",".mjs",".cjs",".ts",".tsx"]).has(ext))return[];const text=fs.readFileSync(full,"utf8").replace(/\r?\n/g,"\n");const lines=text.split("\n").slice(0,-1);if(lines.length<=1000&&fs.statSync(full).size<=50000)return[];return[{rule:"critical-source-size",path:rel,severity:changedMode?"error":"warning"}];}
function buildReport(root,selected,changedMode){const violations=[],counts={files_checked:0,files_with_errors:0,warnings:0};for(const rel of selected){const full=path.join(root,rel);if(!fs.statSync(full,{throwIfNoEntry:false})?.isFile())continue;counts.files_checked++;if(isText(rel))violations.push(...checkBytes(full,rel));if(forbidden(rel))violations.push({rule:"tracked-artifact",path:rel,severity:"error"});violations.push(...checkMarkdownName(rel));violations.push(...checkSize(full,rel,changedMode));}counts.files_with_errors=new Set(violations.filter(x=>x.severity==="error").map(x=>x.path)).size;counts.warnings=violations.filter(x=>x.severity==="warning").length;return{schema_version:"repository-hygiene-report/v1",repository:path.basename(root),mode:changedMode?"changed":"all",files:counts,violations,passed:!violations.some(x=>x.severity==="error")};}
function formatter(root,selected){const py=selected.filter(p=>path.extname(p)===".py"),pre=selected.filter(p=>[".js",".mjs",".cjs",".ts",".tsx",".json",".jsonc",".md",".yml",".yaml"].includes(path.extname(p).toLowerCase())),md=selected.filter(p=>path.extname(p).toLowerCase()===".md");const cmds=[];if(py){cmds.push([["ruff","format","--check",...py],"ruff-format"],[["ruff","check",...py],"ruff-lint"]);}if(pre.length)cmds.push([["npx","--yes","prettier@3.9.9","--check",...pre],"prettier"]);if(md.length)cmds.push([["npx","--yes","markdownlint-cli2@0.23.3",...md],"markdownlint"]);const failures=[];for(const [cmd,rule] of cmds){const r=spawnSync(cmd[0],cmd.slice(1),{cwd:root,encoding:"utf8",stdio:["ignore","pipe","pipe"]});if(r.status)failures.push({rule,severity:"error",path:"<formatter>",exit_code:r.status,output:(r.stdout||"")+(r.stderr||"").slice(-2000)});}return failures;}
if(fileURLToPath(import.meta.url)===process.argv[1]){
  const a=Object.fromEntries(process.argv.slice(2).reduce((acc,v,i,arr)=>{if(v.startsWith("--"))acc.push([v.slice(2),arr[i+1]??""]);return acc;},[])); const root=path.resolve(a.root??".");
  const contract=path.join(root,CONTRACT_REL);if(!fs.existsSync(contract))throw new Error("missing hygiene contract: "+CONTRACT_REL);JSON.parse(fs.readFileSync(contract,"utf8"));
  const [files,changedMode]=select(root,a.all==="true",a["changed-from"]);const report=buildReport(root,files,changedMode);
  if(a["format-check"]==="true"){report.violations.push(...formatter(root,files.filter(isFormatter)));report.passed=report.passed&&!report.violations.some(x=>x.severity==="error");}
  if(a.report){fs.mkdirSync(path.dirname(path.resolve(a.report)),{recursive:true});fs.writeFileSync(path.resolve(a.report),JSON.stringify(report,null,2)+"\n");}
  console.log(a["summary-only"]==="true"?JSON.stringify({...report.files,passed:report.passed},null,2):JSON.stringify(report,null,2));
  process.exitCode=(report.passed||a.strict!=="true")?0:1;
}
