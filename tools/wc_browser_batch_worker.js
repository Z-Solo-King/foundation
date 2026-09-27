const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const same=(a,b)=>{try{return new URL(a).hostname.replace(/^www\./,"")===new URL(b).hostname.replace(/^www\./,"")}catch{return false}};
const json=(x,n=200)=>new Response(JSON.stringify(x),{status:n,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});
const badRx=/just a moment|cf-chl-|cf-browser-verification|cf-mitigated|turnstile|captcha|access denied|attention required|checking your browser|verify you are human/i;
const nativeText=t=>{try{
 const s=String(t||"");if(badRx.test(s)||!/^\s*(?:<\?xml[^>]*>\s*)?<rss\b/i.test(s))return false;
 const d=new DOMParser().parseFromString(s,"application/xml");
 if(!d||d.getElementsByTagName("parsererror").length||String(d.documentElement?.localName||"").toLowerCase()!=="rss")return false;
 const ns="http://base.google.com/ns/1.0";
 for(const item of [...d.getElementsByTagName("*")].filter(n=>(n.localName||"").toLowerCase()==="item")){
   const f=n=>String([...item.getElementsByTagNameNS(ns,n)][0]?.textContent||"").trim();
   if(f("id")&&f("title")&&f("link")&&f("price")&&f("availability"))return true;
 }
 return false;
}catch{return false}};
let cid=0;
function cdp(ws,method,params={},timeout=45000){return new Promise((resolve,reject)=>{
 const id=++cid;let done=false;
 const finish=()=>{if(done)return;done=true;clearTimeout(timer);ws.removeEventListener("message",onMessage);ws.removeEventListener("close",onClose)};
 const timer=setTimeout(()=>{finish();reject(new Error("CDP timeout: "+method))},timeout);
 const onClose=()=>{finish();reject(new Error("CDP socket closed: "+method))};
 const onMessage=e=>{try{const m=JSON.parse(typeof e.data==="string"?e.data:new TextDecoder().decode(e.data));if(m.id!==id)return;finish();if(m.error)reject(new Error(m.error.message||("CDP "+method+" failed")));else resolve(m.result||{})}catch(err){finish();reject(err)}};
 ws.addEventListener("message",onMessage);ws.addEventListener("close",onClose);
 try{ws.send(JSON.stringify({id,method,params}))}catch(err){finish();reject(err)}
})}
async function evalJson(ws,code,timeout=45000){
 const wrapped="(async()=>JSON.stringify(await ("+code+")))()";
 const r=await cdp(ws,"Runtime.evaluate",{expression:wrapped,awaitPromise:true,returnByValue:true,generatePreview:false},timeout);
 const v=r.result?.value;
 if(typeof v!=="string")throw new Error("Runtime.evaluate did not return string");
 return JSON.parse(v);
}
export default {async fetch(req,env){
 try{
  const u=new URL(req.url);let input={};if(req.method==="POST"){try{input=await req.json()}catch{}}
  const root=String(input.root||u.searchParams.get("root")||u.searchParams.get("u")||"").trim().replace(/\/$/,"");
  const debug=String(input.debug||u.searchParams.get("debug")||"")==="1";
  const raw=Array.isArray(input.targets)?input.targets:[];
  const targets=[...new Set(raw.map(x=>String(x||"").trim()).filter(Boolean))].map(x=>{try{return new URL(x,root).href}catch{return null}}).filter(x=>x&&same(x,root)).slice(0,180);
  if(!/^https?:\/\//i.test(root)||!targets.length)return json({success:false,error:"missing_root_or_targets"},400);
  const session=await env.BROWSER.launch();const wr=await session.webSocket.fetch("https://browser-binding.invalid",{headers:{Upgrade:"websocket"}});
  if(!wr.webSocket)throw new Error("Browser Run did not return a WebSocket");
  const ws=wr.webSocket;ws.accept();
  try{
   let version=null; if(debug){try{version=await cdp(ws,"Browser.getVersion")}catch(e){version={error:String(e)}}}
   await cdp(ws,"Page.enable");await cdp(ws,"Runtime.enable");await cdp(ws,"Network.enable");
   const nav=await cdp(ws,"Page.navigate",{url:root});
   let page={href:root,title:"",readyState:"",challenge:false,body_len:0};let eval_error="";
   const deadline=Date.now()+30000;
   while(Date.now()<deadline){
    await sleep(1000);
    try{page=await evalJson(ws,"(()=>({href:location.href,title:document.title||'',readyState:document.readyState,challenge:"+badRx.toString()+".test(document.documentElement?.outerHTML||''),body_len:(document.body?.innerText||'').length}))()")}catch(e){eval_error=String(e?.message||e)}
    if(page.readyState==="complete"&&!page.challenge)break;
   }
   if(debug)return json({success:true,root,version,nav,page,eval_error});
   let resultRows=[];let hit=null;
   for(let i=0;i<targets.length;i+=8){
    const batch=targets.slice(i,i+8);
    const code="(async()=>{const ts="+JSON.stringify(batch)+",root="+JSON.stringify(root)+",same="+same.toString()+",bad="+badRx.toString()+",native="+nativeText.toString()+";const out=[];for(const x of ts){try{const ac=new AbortController(),tm=setTimeout(()=>ac.abort(),7000);const r=await fetch(x,{credentials:'include',redirect:'follow',signal:ac.signal,headers:{accept:'application/xml,application/rss+xml,text/xml,text/plain,*/*'}});const t=await r.text();clearTimeout(tm);out.push({url:x,status:r.status,final:r.url,ct:r.headers.get('content-type')||'',len:t.length,challenge:bad.test(t),native:native(t)})}catch(e){out.push({url:x,status:0,error:String(e?.name||e)})}}return out})()";
    try{const rows=await evalJson(ws,code,65000);for(const rec of rows){resultRows.push(rec);if(rec.native&&same(rec.final,root)){hit={url:rec.final,status:rec.status,ct:rec.ct,len:rec.len,method:"browser_session"};break}}}catch(e){for(const x of batch)resultRows.push({url:x,status:0,error:String(e?.name||e)})}
    if(hit)break;
   }
   let cookie_names=[];try{const ck=await cdp(ws,"Network.getAllCookies");cookie_names=[...new Set((ck.cookies||[]).filter(c=>c&&c.name).map(c=>String(c.name)))].slice(0,120)}catch{}
   return json({success:true,root,page,result:{hit,statuses:resultRows},cookie_names,has_cf_clearance:cookie_names.includes("cf_clearance")});
  }finally{try{ws.close()}catch{}try{await env.BROWSER.closeSession(session.sessionId)}catch{}}
 }catch(e){return json({success:false,error:String(e&&e.stack||e)},500)}
}};