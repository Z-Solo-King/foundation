const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const same=(a,b)=>{try{return new URL(a).hostname.replace(/^www\./,'')===new URL(b).hostname.replace(/^www\./,'')}catch{return false}};
const json=(x,n=200)=>new Response(JSON.stringify(x),{status:n,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});
let seq=0;
function cdp(ws,method,params={},timeout=45000,sessionId=""){
  return new Promise((resolve,reject)=>{
    const id=++seq; let done=false;
    const finish=()=>{if(done)return;done=true;clearTimeout(timer);ws.removeEventListener("message",onMessage);ws.removeEventListener("close",onClose)};
    const timer=setTimeout(()=>{finish();reject(new Error("CDP timeout: "+method))},timeout);
    const onClose=()=>{finish();reject(new Error("CDP socket closed: "+method))};
    const onMessage=e=>{try{
      const m=JSON.parse(typeof e.data==="string"?e.data:new TextDecoder().decode(e.data));
      if(m.id!==id)return; finish();
      if(m.error)reject(new Error(m.error.message||("CDP "+method+" failed"))); else resolve(m.result||{});
    }catch(err){finish();reject(err)}};
    ws.addEventListener("message",onMessage);ws.addEventListener("close",onClose);
    try{ws.send(JSON.stringify(sessionId?{id,method,params,sessionId}:{id,method,params}))}catch(err){finish();reject(err)}
  });
}
async function evalJson(ws,code,sessionId){
  const wrapped="(async()=>{const __v=await ("+code+");return JSON.stringify(__v);})()";
  const r=await cdp(ws,"Runtime.evaluate",{expression:wrapped,awaitPromise:true,returnByValue:true,generatePreview:false},45000,sessionId);
  const v=r.result?.value;
  if(typeof v!=="string")throw new Error("Runtime.evaluate returned no serializable string value");
  return JSON.parse(v);
}
function blockedText(s){return /just a moment|cf-chl-|cf-browser-verification|cf-mitigated|turnstile|captcha|access denied|attention required|checking your browser|verify you are human/i.test(String(s||""))}
function nativeText(s){
  try{
    const t=String(s||"");
    if(blockedText(t)||!/^\s*(?:<\?xml[^>]*>\s*)?<rss\b/i.test(t))return false;
    const d=new DOMParser().parseFromString(t,"application/xml");
    if(!d||d.getElementsByTagName("parsererror").length||String(d.documentElement?.localName||"").toLowerCase()!=="rss")return false;
    const ns="http://base.google.com/ns/1.0";
    for(const item of [...d.getElementsByTagName("*")].filter(n=>(n.localName||"").toLowerCase()==="item")){
      const f=n=>{const a=[...item.getElementsByTagNameNS(ns,n)];return a.length?String(a[0].textContent||"").trim():""};
      if(f("id")&&f("title")&&f("link")&&f("price")&&f("availability"))return true;
    }
    return false;
  }catch{return false}
}
export default {async fetch(req,env){
  try{
    const u=new URL(req.url);let input={};
    if(req.method==="POST"){try{input=await req.json()}catch{}}
    const root=String(input.root||u.searchParams.get("root")||u.searchParams.get("u")||"").trim().replace(/\/$/,"");
    if(!/^https?:\/\//i.test(root))return json({success:false,error:"missing_root"},400);
    const raw=Array.isArray(input.targets)?input.targets:[];
    const targets=[...new Set(raw.map(x=>String(x||"").trim()).filter(Boolean))]
      .map(x=>{try{return new URL(x,root).href}catch{return null}})
      .filter(x=>x&&same(x,root)).slice(0,180);
    if(!targets.length)return json({success:false,error:"no_targets"},400);
    const session=await env.BROWSER.launch();
    const wsres=await session.webSocket.fetch("https://browser-binding.invalid",{headers:{Upgrade:"websocket"}});
    if(!wsres.webSocket)throw new Error("Browser binding did not return a WebSocket");
    const ws=wsres.webSocket;ws.accept();
    let targetId="",sessionId="";
    try{
      const created=await cdp(ws,"Target.createTarget",{url:"about:blank"},45000);
      targetId=String(created.targetId||"");if(!targetId)throw new Error("Target.createTarget returned no targetId");
      const attached=await cdp(ws,"Target.attachToTarget",{targetId,flatten:true},45000);
      sessionId=String(attached.sessionId||"");if(!sessionId)throw new Error("Target.attachToTarget returned no sessionId");
      await cdp(ws,"Page.enable",{},45000,sessionId);
      await cdp(ws,"Runtime.enable",{},45000,sessionId);
      await cdp(ws,"Network.enable",{},45000,sessionId);
      await cdp(ws,"Page.navigate",{url:root},45000,sessionId);
      let page={href:root,title:"",readyState:"",challenge:false,body_len:0};
      const until=Date.now()+30000;
      while(Date.now()<until){
        await sleep(1200);
        try{
          page=await evalJson(ws,"(()=>({href:location.href,title:document.title||'',readyState:document.readyState,challenge:"+blockedText.toString()+".test(document.documentElement?.outerHTML||''),body_len:(document.body?.innerText||'').length}))()",sessionId);
        }catch{}
        if(page.readyState==="complete"&&!page.challenge&&page.body_len>100)break;
      }
      const bodyCode="(async()=>{"+
        "const targets="+JSON.stringify(targets)+",root="+JSON.stringify(root)+",same="+same.toString()+",bad="+blockedText.toString()+",nat="+nativeText.toString()+";"+
        "const out=[];let hit=null;"+
        "for(const x of targets){try{const ac=new AbortController(),tm=setTimeout(()=>ac.abort(),7000);"+
        "const r=await fetch(x,{credentials:'include',redirect:'follow',signal:ac.signal,headers:{accept:'application/xml,application/rss+xml,text/xml,text/plain,*/*'}});"+
        "clearTimeout(tm);const t=await r.text();const rec={url:x,status:r.status,final:r.url,ct:r.headers.get('content-type')||'',len:t.length,challenge:bad(t),native:nat(t)};out.push(rec);"+
        "if(rec.native&&same(r.url,root)){hit={url:r.url,status:r.status,ct:rec.ct,len:t.length,method:'browser_session'};break}}catch(e){out.push({url:x,status:0,error:String(e?.name||e)})}}"+
        "return {hit,statuses:out,resources:(performance.getEntriesByType('resource')||[]).map(e=>e.name).filter(x=>same(x,root)&&(/\\.xml(?:\\.gz)?(?:$|[?#])/i.test(x)||/google|merchant|shopping|product-feed|woocommerce_gpf|woo-feed|wppfm/i.test(x))).slice(0,160)}})()";
      const result=await evalJson(ws,bodyCode,sessionId);
      let cookie_names=[];
      try{const ck=await cdp(ws,"Network.getAllCookies",{},45000,sessionId);cookie_names=[...new Set((ck.cookies||[]).filter(c=>c&&c.name).map(c=>String(c.name)))].slice(0,120)}catch{}
      return json({success:true,root,page,result:result||{},cookie_names,has_cf_clearance:cookie_names.includes("cf_clearance")});
    }finally{
      try{if(targetId)await cdp(ws,"Target.closeTarget",{targetId},15000)}catch{}
      try{ws.close()}catch{}
      try{await env.BROWSER.closeSession(session.sessionId)}catch{}
    }
  }catch(e){return json({success:false,error:String(e&&e.stack||e)},500)}
}};