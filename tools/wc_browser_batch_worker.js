export default {async fetch(req,env){
 let stage="start",session=null,ws=null;
 const json=(x,n=200)=>new Response(JSON.stringify(x),{status:n,headers:{"content-type":"application/json","cache-control":"no-store"}});
 try{
  stage="launch";
  session=await env.BROWSER.launch();
  const sid=session?.sessionId||null;
  stage="websocket_fetch";
  const r=await session.webSocket.fetch("https://browser-binding.invalid",{headers:{Upgrade:"websocket"}});
  if(!r.webSocket) throw new Error("no_websocket");
  ws=r.webSocket; ws.accept();
  stage="browser_get_version";
  const id=1;
  const version=await new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>reject(new Error("cdp_timeout")),20000);
    const onMessage=e=>{try{const m=JSON.parse(typeof e.data==="string"?e.data:new TextDecoder().decode(e.data));if(m.id!==id)return;clearTimeout(timer);ws.removeEventListener("message",onMessage);m.error?reject(new Error(m.error.message||"cdp_error")):resolve(m.result||{})}catch(err){clearTimeout(timer);ws.removeEventListener("message",onMessage);reject(err)}};
    ws.addEventListener("message",onMessage); ws.send(JSON.stringify({id,method:"Browser.getVersion",params:{}}));
  });
  stage="success";
  if(ws) try{ws.close()}catch{}
  let cleanup_error="";
  try{if(sid)await env.BROWSER.closeSession(sid)}catch(e){cleanup_error=String(e?.message||e)}
  return json({success:true,stage,session_id_present:!!sid,version,cleanup_error});
 }catch(e){
  const msg=String(e?.stack||e||"");
  try{if(ws)ws.close()}catch{}
  try{if(session?.sessionId)await env.BROWSER.closeSession(session.sessionId)}catch{}
  return json({success:false,stage,error:msg},500);
 }
}};