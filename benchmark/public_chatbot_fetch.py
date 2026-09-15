"""HTTP fetch, HTML/JSON-LD classification and receipt construction for the public benchmark."""
from __future__ import annotations

import html.parser
import socket
import ssl
import time
from dataclasses import dataclass
from email.message import Message
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from collections import Counter
from urllib.parse import urlsplit

from .public_chatbot_targets import Target

USER_AGENT = "ResearchIntelligenceEngine-Benchmark/2026.09"
PRODUCT_HINTS = ("product", "itemprop=\"name\"", "productid", "sku", "add-to-cart", "price")
TRANSIENT_HTTP = {408, 425, 429, 500, 502, 503, 504}
MAX_ATTEMPTS = 2
REQUEST_TIMEOUT_SECONDS = 20.0
MAX_RESPONSE_BYTES = 2_000_000

class _ProductParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True); self.title_parts=[]; self.jsonld_blocks=[]; self._in_title=False; self._in_jsonld=False; self._jsonld_parts=[]
    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag.lower()=="title": self._in_title=True
        if tag.lower()=="script" and attr.get("type","").lower()=="application/ld+json": self._in_jsonld=True; self._jsonld_parts=[]
    def handle_endtag(self, tag):
        if tag.lower()=="title": self._in_title=False
        if tag.lower()=="script" and self._in_jsonld:
            self._in_jsonld=False; text="".join(self._jsonld_parts).strip()
            if text: self.jsonld_blocks.append(text)
    def handle_data(self, data):
        if self._in_title: self.title_parts.append(data)
        if self._in_jsonld: self._jsonld_parts.append(data)

@dataclass(frozen=True)
class Receipt:
    run_id: str; shard: int; shard_count: int; key: str; url: str; status: str; http_status: int
    elapsed_ms: int; bytes_read: int; pages_fetched: int; title: str; product_candidates: int
    jsonld_blocks: int; diagnostics: tuple[str, ...]; recorded_at: int

def classify(status: int, body: bytes, diagnostics: list[str]) -> tuple[str,int,str,int,int,int]:
    text=body.decode("utf-8",errors="ignore"); parser=_ProductParser()
    try: parser.feed(text)
    except Exception as exc: diagnostics.append(f"parser:{type(exc).__name__}")
    candidates=sum(text.lower().count(h) for h in PRODUCT_HINTS); jsonld=len(parser.jsonld_blocks); title=" ".join(" ".join(parser.title_parts).split())[:300]
    result="blocked" if status in {401,403} else "resource_limited" if status==429 else "error" if status>=400 else "empty" if not text.strip() else "ok" if candidates or jsonld else "empty"
    return result,len(body),title,candidates,jsonld,1

def retry_after(headers: Message | None) -> float:
    if headers is None: return 0.0
    try: return min(max(float(headers.get("Retry-After","0")),0.0),30.0)
    except (TypeError,ValueError): return 0.0

def fetch_target(target: Target, timeout: float=REQUEST_TIMEOUT_SECONDS) -> Receipt:
    started=time.perf_counter(); diagnostics=[]; last_status=0; last_body=b""; final_error=None
    for attempt in range(1,MAX_ATTEMPTS+1):
        try:
            request=Request(target.url,headers={"User-Agent":USER_AGENT,"Accept":"text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8","Accept-Language":"en-IN,en;q=0.8","Connection":"close"})
            with urlopen(request,timeout=timeout,context=ssl.create_default_context()) as response:
                last_status=int(getattr(response,"status",200)); last_body=response.read(MAX_RESPONSE_BYTES)
            if last_status in TRANSIENT_HTTP and attempt<MAX_ATTEMPTS: diagnostics.append(f"retry:http-{last_status}"); time.sleep(0.25*attempt); continue
            break
        except HTTPError as exc:
            last_status=int(exc.code)
            try:
                last_body=exc.read(MAX_RESPONSE_BYTES)
                if last_status in {429,503} and attempt<MAX_ATTEMPTS:
                    diagnostics.append(f"retry:http-{last_status}"); time.sleep(retry_after(exc.headers) or (0.5*attempt)); continue
            finally: exc.close()
            break
        except (TimeoutError,socket.timeout):
            final_error="timeout"; diagnostics.append(f"attempt-{attempt}:timeout")
            if attempt<MAX_ATTEMPTS: time.sleep(0.25*attempt); continue
        except (ssl.SSLError,ConnectionError,OSError) as exc:
            final_error=type(exc).__name__; diagnostics.append(f"attempt-{attempt}:{final_error}")
            if attempt<MAX_ATTEMPTS: time.sleep(0.25*attempt); continue
        except Exception as exc:
            final_error=type(exc).__name__; diagnostics.append(f"attempt-{attempt}:{final_error}"); break
    if last_status: result,size,title,candidates,jsonld,pages=classify(last_status,last_body,diagnostics)
    else: result,size,title,candidates,jsonld,pages=("resource_limited" if final_error=="timeout" else "error",len(last_body),"",0,0,0)
    diagnostics.append(f"attempts-{attempt}")
    return Receipt("",0,1,target.key,target.url,result,last_status,int((time.perf_counter()-started)*1000),size,pages,title,candidates,jsonld,tuple(diagnostics),int(time.time()))
