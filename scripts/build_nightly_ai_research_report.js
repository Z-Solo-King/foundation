#!/usr/bin/env node
const fs=require("fs"), path=require("path");
const root=path.join(process.cwd(),".runtime","nightly-ai-research");
const dirs=fs.existsSync(root)?fs.readdirSync(root,{withFileTypes:true}).filter(x=>x.isDirectory()&&x.name.startsWith("nightly-ai-research-")).map(x=>path.join(root,x.name)).filter(x=>fs.existsSync(path.join(x,"metadata.json"))):[];
const jobs=dirs.map(d=>JSON.parse(fs.readFileSync(path.join(d,"metadata.json"),"utf8")));
const ids=new Set(jobs.map(x=>x.job_id)); const missing=[]; for(let i=1;i<=20;i++){const id=String(i).padStart(2,"0"); if(!ids.has(id)) missing.push(id);}
const invalid=jobs.filter(x=>!Object.values(x.source_status||{}).some(v=>v===200)).map(x=>x.job_id);
const targets=[...new Set(jobs.flatMap(x=>x.target_issues||[]))].sort();
const report={schema:"nightly-ai-research-report/v1",generated_at:new Date().toISOString(),expected_jobs:20,jobs,missing_jobs:missing,invalid_jobs:invalid,benchmark_targets:targets};
fs.writeFileSync(path.join(root,"nightly_ai_research_report.json"),JSON.stringify(report,null,2)+"\n");
fs.writeFileSync(path.join(root,"benchmark_improvement_candidates.json"),JSON.stringify({schema:"nightly-ai-research-improvement-candidates/v1",generated_at:report.generated_at,evidence_class:"research-signal",benchmark_targets:targets,jobs:jobs.map(x=>({job_id:x.job_id,topic:x.topic,target_issues:x.target_issues,focus:x.research_focus}))},null,2)+"\n");
fs.writeFileSync(path.join(root,"nightly_ai_research_report.md"),["Nightly AI research — 20-job synthesis","","Job packets: "+jobs.length+"/20","Missing packets: "+(missing.length?missing.join(", "):"none"),"Zero-source packets: "+(invalid.length?invalid.join(", "):"none"),"Benchmark targets: "+targets.join(", "),"","Research-signal evidence only; runtime and production certification remain separate."].join("\n")+"\n");
if(jobs.length!==20||missing.length||invalid.length) process.exitCode=1;
