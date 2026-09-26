import { mkdir, writeFile } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { createHash } from "node:crypto";

const exec = promisify(execFile);
const TARGETS = [
["Aarna Computers","https://aarnacomputers.com"],["Ads Store","https://adsstore.in"],["avikaretails","https://avikaretails.com"],["EZPZ Solutions","https://www.ezpzsolutions.in"],
["GamesNComps","https://gamesncomps.com"],["Geekbees","https://geekbees.in"],["hotshiftpc","https://hotshiftpc.com"],["itgadgetsonline","https://itgadgetsonline.com"],
["ithunt","https://ithunt.in"],["kccomputers","https://kccomputers.co.in"],["KRG KART","https://krgkart.com"],["Kryptronix Gaming","https://kryptronix.in"],
["NCL Computer","https://nclcomputer.com"],["networkitstore","https://networkitstore.in"],["nexusinfosys","https://www.mynexusinfosys.com"],["Only SDD","https://onlyssd.com"],
["PC Kumar Infotech","https://pckumar.in"],["PC Studio","https://www.pcstudio.in"],["PCHubShop","https://www.pchubshop.com"],["Prime ABGB","https://www.primeabgb.com"],
["quickincomputers","https://quickincomputers.com"],["SCL Gaming","https://sclgaming.in"],["solankienterprises","https://solankienterprises.com"],["Variety Infotech","https://varietyinfotech.com"],
["Viper PC","https://viperpc.in"],["AULA India","https://aulaindia.com"],["Cosmic Byte","https://www.thecosmicbyte.com"],["Meckeys","https://www.meckeys.com"],
["Moskeys","https://moskeys.com"],["Ninja Dog","https://ninjadog.in"],["StacksKB","https://stackskb.com"],["Theproaudio","https://www.theproaudio.com"]
];

const PATHS = [
"/?woocommerce_gpf=google","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000","/woocommerce_gpf/google",
"/index.php?action=woocommerce_gpf&woocommerce_gpf=google","/?woocommerce_gpf=googleinventory",
"/?feed=google","/?feed=google_shopping","/?feed=google_shopping_feed","/?feed=google-product-feed","/?product_feed=google",
"/google.xml","/google_feed.xml","/google_base.xml","/google-products.xml","/google-product-feed.xml","/google-shopping.xml",
"/google-shopping-feed.xml","/product-feed.xml","/products-feed.xml","/merchant-feed.xml","/feeds/google.xml","/feeds/google-products.xml",
"/feed/google.xml","/feed/google-shopping.xml","/feed/google-products.xml","/feed.xml","/rss.xml","/atom.xml",
"/wp-content/uploads/codesolz-feeds/google-products.xml","/wp-json/feedcraft-product-feed/v1/xml","/wp-json/feedcraft-product-feed/v1/json"
];

const start=Math.max(0,Number.parseInt(process.env.TARGET_START||"0",10)||0);
const count=Math.max(1,Number.parseInt(process.env.TARGET_COUNT||String(TARGETS.length),10)||TARGETS.length);
const selected=TARGETS.slice(start,start+count);
await mkdir("out/transport/feeds",{recursive:true});

function slug(s){return String(s).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"").slice(0,70)||"site";}
function challenge(status,text){const s=String(text||"").slice(0,12000).toLowerCase();return [403,429,430,451,503,520,521,522,523,524].includes(status)&&/just a moment|cf-chl|cloudflare|challenge-platform|cf-turnstile|captcha|verify you are human|access denied|request blocked|attention required|checking your browser/.test(s);}
function validate(xml,ct=""){const s=String(xml||"");const root=/^\s*(?:<\?xml[^>]*>\s*)?(?:<rss\b|<feed\b)/i.test(s);const g=/xmlns(?::[A-Za-z_][\w.-]*)?\s*=\s*["']http:\/\/base\.google\.com\/ns\/1\.0["']/i.test(s);const items=[...s.matchAll(/<(?:item|entry)\b[^>]*>([\s\S]*?)<\/(?:item|entry)>/gi)].map(m=>m[1]);let complete=0;for(const b of items){let n=0;for(const k of ["id","title","link","price"])n+=Number(new RegExp(`<(?:[A-Za-z_][\\w.-]*:)?${k}\\b[^>]*>`,"i").test(b));complete+=n;}const cov=complete/Math.max(1,items.length*4);return {qualifies:Boolean(root&&g&&items.length&&cov>=.75),item_count:items.length,required_field_coverage:Number(cov.toFixed(4)),content_type:ct};}

async function cmd(bin,args){
  try{
    const {stdout,stderr}=await exec(bin,args,{maxBuffer:70*1024*1024,timeout:12000,windowsHide:true});
    return {ok:true,stdout:String(stdout||""),stderr:String(stderr||""),exit:0};
  }catch(e){return {ok:false,stdout:String(e.stdout||""),stderr:String(e.stderr||e.message||""),exit:Number.isInteger(e.code)?e.code:-1};}
}

async function curl(url){
  const headFile="/tmp/curl-h-"+process.pid;
  const bodyFile="/tmp/curl-b-"+process.pid;
  const a=await cmd("curl",["-4","-L","--compressed","--max-time","10","--connect-timeout","5","-A","Mozilla/5.0 (compatible; WooCommerceGoogleTransport/1.0)","-H","Accept: application/xml, application/rss+xml, text/xml, text/html;q=0.8, */*;q=0.4","-D",headFile,"-o",bodyFile,"-sS","-w","%{http_code}\n%{url_effective}\n",url]);
  let body="";let headers="";try{body=await (await import("node:fs/promises")).readFile(bodyFile,"utf8");headers=await (await import("node:fs/promises")).readFile(headFile,"utf8");}catch{}
  const m=String(a.stdout).trim().split(/\n/);return {client:"curl4",status:Number(m[0]||0),finalUrl:m[1]||url,body,headers,bytes:body.length,error:a.ok?"":a.stderr};
}

async function wget(url){
  const out="/tmp/wget-b-"+process.pid;
  const a=await cmd("wget",["-q","-O",out,"--max-redirect","5","--timeout","10","--tries","1","--user-agent=Mozilla/5.0 (compatible; WooCommerceGoogleTransport/1.0)",url]);
  let body="";try{body=await (await import("node:fs/promises")).readFile(out,"utf8");}catch{}
  // wget does not expose final status consistently without extra parsing; classify successful body only.
  return {client:"wget",status:a.ok?200:0,finalUrl:url,body,headers:"",bytes:body.length,error:a.ok?"":a.stderr};
}

async function scan([name,base]){
  const probes=[];const feeds=[];
  let idx=0;
  const urls=PATHS.map(p=>new URL(p,base+"/").href);
  async function worker(){
    while(idx<urls.length){
      const url=urls[idx++];
      const variants=[];
      const c=await curl(url);variants.push(c);
      if(!(c.status===200&&c.body))variants.push(await wget(url));
      for(const r of variants){
        if(r.status===200&&r.body){
          const v=validate(r.body,r.headers);
          if(v.qualifies){
            const hash=createHash("sha256").update(r.body).digest("hex");
            const file=`out/transport/feeds/${slug(name)}-${hash.slice(0,12)}.xml`;
            await writeFile(file,r.body);
            feeds.push({url,finalUrl:r.finalUrl,client:r.client,file,sha256:hash,bytes:r.bytes,...v});
            probes.push({url,client:r.client,status:r.status,classification:"LIVE_VERIFIED",sha256:hash,...v});
            continue;
          }
        }
        if(r.status===401)probes.push({url,client:r.client,status:r.status,classification:"AUTH_REQUIRED"});
        else if(challenge(r.status,r.body))probes.push({url,client:r.client,status:r.status,classification:"BLOCKED_OR_CHALLENGED"});
        else if(r.status===403)probes.push({url,client:r.client,status:r.status,classification:"ACCESS_DENIED"});
        else if(r.status===429)probes.push({url,client:r.client,status:r.status,classification:"RATE_LIMITED"});
        else if(r.status)probes.push({url,client:r.client,status:r.status,classification:`HTTP_${r.status}`});
        else probes.push({url,client:r.client,classification:"ERROR",error:r.error});
      }
    }
  }
  await Promise.all(Array.from({length:8},worker));
  const counts={};for(const p of probes)counts[p.classification]=(counts[p.classification]||0)+1;
  return {name,base,feed_count:feeds.length,feeds,counts,probes};
}

const results=[];
for(const t of selected){const r=await scan(t);results.push(r);console.log(JSON.stringify({name:r.name,feeds:r.feeds.map(x=>({url:x.url,client:x.client})),counts:r.counts}));}
const all=results.flatMap(r=>r.feeds.map(f=>({brand:r.name,base:r.base,...f})));
await writeFile("out/transport/summary.json",JSON.stringify({generated_at:new Date().toISOString(),target_count:selected.length,live_verified_feeds:all.length,live_verified_sites:new Set(all.map(x=>x.brand)).size,sites:results.map(r=>({brand:r.name,feed_count:r.feed_count,feeds:r.feeds.map(f=>f.url),counts:r.counts}))},null,2)+"\n");
await writeFile("out/transport/audit.json",JSON.stringify({generated_at:new Date().toISOString(),targets:selected.length,results,feeds:all},null,2)+"\n");
