import fs from "node:fs/promises";

const t=process.env.TARGET;
const UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/153 Safari/537.36";

async function req(url,opt={}) {
  return await fetch(url,{redirect:"follow",...opt,headers:{"user-agent":UA,"accept":"*/*",...(opt.headers||{})}});
}
async function text(url,opt={}) { const r=await req(url,opt); return {r,text:await r.text()}; }
async function show(label,r) {
  const s=await r.text();
  console.log(JSON.stringify({label,url:r.url,status:r.status,contentType:r.headers.get("content-type")||"",bytes:s.length,sample:s.slice(0,12000)}));
  return s;
}

if(t==="Acer"){
  const h=await text("https://store.acer.com/en-in/",{headers:{accept:"text/html"}});
  console.log(JSON.stringify({label:"home",status:h.r.status,url:h.r.url,contentType:h.r.headers.get("content-type")||"",bytes:h.text.length,sample:h.text.slice(0,800)}));
  const q="query($search:String,$pageSize:Int=20,$currentPage:Int=1){products(search:$search,pageSize:$pageSize,currentPage:$currentPage){total_count page_info{current_page page_size total_pages} items{sku name url_key}}}";
  try{
    const g=await req("https://store.acer.com/en-in/graphql",{method:"POST",headers:{"content-type":"application/json","accept":"application/json","store":"default","origin":"https://store.acer.com","referer":"https://store.acer.com/en-in/"},body:JSON.stringify({query:q,variables:{search:"laptop",pageSize:50,currentPage:1}})});
    const s=await show("graphql",g);
    if(g.status===200) console.log("PRODUCT_DATA_MATCH="+(/"products"\s*:/.test(s) ? "1":"0"));
  }catch(e){console.log(JSON.stringify({label:"graphql-error",error:String(e) }))}
}else if(t==="ASUS"){
  const u="https://odinapi.asus.com/recent-data/apiv2/SearchResult?SystemCode=asus&WebsiteCode=in&SearchKey=laptop&SearchType=products&SearchPDLine=&SearchPDLine2=&PDLineFilter=&TopicFilter=&CateFilter=&PageSize=20&Pages=1&LocalFlag=0&siteID=www&sitelang=";
  const s=await show("odin-search",await req(u,{headers:{accept:"application/json",referer:"https://www.asus.com/in/"} }));
  const m=s.match(/"ProductID"\s*:\s*"([^"]+)"/i)||s.match(/"PartNo"\s*:\s*"([^"]+)"/i);
  console.log(JSON.stringify({label:"first-id",id:m?.[1]||null}));
  for(const id of [...new Set([m?.[1],"R_90NR0NR2-M002Y0","90NR0NR2-M002Y0"].filter(Boolean))]){
    for(const extra of ["","&SystemCode=asus&WebsiteCode=in","&SystemCode=asus&WebsiteCode=asus"]){
      const url="https://odinapi.asus.com/recent-data/apiv2/GetPrice?ProductId="+encodeURIComponent(id)+extra;
      console.log("PRICE_URL="+url);
      try{
        const r=await req(url,{headers:{accept:"application/json",referer:"https://www.asus.com/in/"}});
        console.log(JSON.stringify({label:"odin-price",id,url,status:r.status,contentType:r.headers.get("content-type")||"",sample:(await r.text()).slice(0,5000)}));
      }catch(e){console.log(JSON.stringify({label:"odin-price-error",id,url,error:String(e)}))}
    }
  }
}else if(t==="Dell"){
  const p=await req("https://www.dellstore.com/rest/V1/products?searchCriteria%5BpageSize%5D=50&searchCriteria%5BcurrentPage%5D=1",{headers:{accept:"application/json",referer:"https://www.dellstore.com/"}});
  const ps=await show("products",p);
  let sku="580-AEKD"; try{const j=JSON.parse(ps);sku=j.items?.[0]?.sku||sku}catch{}
  const stock=await req("https://www.dellstore.com/rest/V1/stockStatuses/"+encodeURIComponent(sku),{headers:{accept:"application/json",referer:"https://www.dellstore.com/"}});
  await show("stock",stock);
}else if(t==="Flipkart"){
  const r=await req("https://www.flipkart.com/laptops/pr?sid=6bo,b5g",{headers:{accept:"text/html"}});
  const s=await show("raw-html",r);
  const markers=["__INITIAL_STATE__","INITIAL_STATE","finalPrice","productId","pricing"];
  const contexts={};
  for(const k of markers){
    const idx=s.indexOf(k);
    contexts[k]={idx,snippet:idx>=0?s.slice(Math.max(0,idx-2500),idx+9000):null};
  }
  console.log(JSON.stringify({label:"state-contexts",contexts}));
}
await fs.writeFile("retailer-final-contract.txt","done");
