"""Passive public and historical index discovery adapter."""
#!/usr/bin/env python3
from __future__ import annotations

"""
WooCommerce V175-derived plugin fingerprint + native Google-feed recovery harness.

The attached extract_universal_V175.py is the source/design authority for:
- clearance-aware browser recovery
- persistent-cookie semantics
- browser/XHR discovery
- transport/provenance separation
- bounded recovery budgets
- public-only acquisition

V175 source SHA-256: 33d651b329c20372db40026c0626a3227408096beb910c1d1069266af5cc1b15

This focused harness deliberately does NOT import the 1.5 MB monolith at runtime.
It preserves the V175 evidence contracts while enforcing the repository acceptance boundary:
- Chromium + Firefox/Gecko + WebKit clean browser passes
- public API/XHR discovery without clearance-cookie replay
- optional Cloudflare Browser Run and Browserless adapters
- passive robots/sitemap + historical index discovery
- plugin fingerprint normalization with provenance-aware confidence
- plugin-specific native Google XML candidate generation
- strict payload validation

Important: challenge/clearance encounters are diagnostic only. No clearance cookies, CAPTCHA state,
or anti-bot bypass state are replayed or admitted into native-feed verification.
"""

import asyncio
import gzip
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlsplit, quote

import httpx


try:
    from .woocommerce_fingerprint_config import (
        PASSIVE_INDEX_ENABLED, WAYBACK_ENABLED, COMMONCRAWL_ENABLED,
        PLUGIN_FEED_DIRECTORIES,
    )
    from .woocommerce_fingerprint_discovery import (
        bare_host, same_host, discover_urls_from_xml_or_text,
        passive_sitemap_candidates, public_directory_feed_candidates,
    )
except ImportError:
    from woocommerce_fingerprint_config import (
        PASSIVE_INDEX_ENABLED, WAYBACK_ENABLED, COMMONCRAWL_ENABLED,
        PLUGIN_FEED_DIRECTORIES,
    )
    from woocommerce_fingerprint_discovery import (
        bare_host, same_host, discover_urls_from_xml_or_text,
        passive_sitemap_candidates, public_directory_feed_candidates,
    )

async def passive_public_discovery(root: str) -> Dict[str, Any]:
    if not PASSIVE_INDEX_ENABLED:
        return {"enabled": False, "urls": [], "historical": [], "errors": []}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; WooCommerceV175PassiveDiscovery/2026.09)", "Accept": "text/plain, application/xml, */*"}
    urls = set()
    historical = set()
    blobs = []
    errors = []
    probes = [
        "/robots.txt", "/wp-sitemap.xml", "/wp-sitemap.xml.gz", "/sitemap.xml", "/sitemap_index.xml",
        "/product-sitemap.xml", "/product-sitemap1.xml",
    ]
    directory_urls = set()
    directory_reports = []
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15) as client:
        for path in probes:
            u = urljoin(root + "/", path)
            try:
                r = await client.get(u)
                body = await r.aread()
                if r.status_code == 200:
                    txt = body.decode("utf-8", "ignore")[:600_000]
                    blobs.append(txt)
                    urls.update(discover_urls_from_xml_or_text(txt, root))
                    urls.update(passive_sitemap_candidates(txt, root))
            except Exception as e:
                errors.append({"url": u, "error": str(e)[:180]})

        # Public directory indexes are an important recovery path for plugins whose feed
        # filename is generated/randomized (e.g. CTX Feed and Product Feed PRO).
        async def inspect_directory(directory: str):
            u = urljoin(root + "/", directory.lstrip("/"))
            try:
                r = await client.get(u, timeout=8)
                body = await r.aread()
                text = body.decode("utf-8", "ignore")[:250_000]
                candidates = public_directory_feed_candidates(text, root, directory) if r.status_code == 200 else []
                return {
                    "directory": directory,
                    "status": r.status_code,
                    "candidate_urls": candidates,
                }
            except Exception as e:
                return {"directory": directory, "status": 0, "candidate_urls": [], "error": str(e)[:180]}

        directory_results = await asyncio.gather(*(inspect_directory(d) for d in PLUGIN_FEED_DIRECTORIES))
        for report in directory_results:
            directory_reports.append(report)
            directory_urls.update(report.get("candidate_urls") or [])
            urls.update(report.get("candidate_urls") or [])
        if WAYBACK_ENABLED:
            try:
                pattern = quote(bare_host(root) + "/*", safe="")
                filter_expr = quote(".*(feed|google|merchant|woo_feed|woocommerce_gpf|wpfm|webtoffee|adtribes|product-feed).*", safe="")
                api = f"https://web.archive.org/cdx/search/cdx?url={pattern}&output=json&fl=original,statuscode,mimetype&filter=statuscode:200&filter=urlkey:{filter_expr}&collapse=urlkey&limit=80"
                r = await client.get(api, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    rows = data[1:] if isinstance(data, list) and data and isinstance(data[0], list) else data
                    for row in rows or []:
                        if isinstance(row, list) and row:
                            u = str(row[0])
                            if same_host(u, root):
                                historical.add(u)
            except Exception as e:
                errors.append({"source": "wayback", "error": str(e)[:180]})
        if COMMONCRAWL_ENABLED:
            try:
                idx = await client.get("https://index.commoncrawl.org/collinfo.json", timeout=20)
                if idx.status_code == 200:
                    coll = idx.json()
                    index_id = str(coll[0].get("id")) if coll else ""
                    if index_id:
                        pattern = quote(bare_host(root) + "/*", safe="")
                        api = f"https://index.commoncrawl.org/{index_id}-index?url={pattern}&output=json&matchType=prefix&filter=status:200&filter=url:feed|google|merchant|woo_feed|woocommerce_gpf|wpfm|webtoffee|adtribes|product-feed&limit=80"
                        cr = await client.get(api, timeout=25)
                        if cr.status_code == 200:
                            for line in cr.text.splitlines():
                                try:
                                    row = json.loads(line)
                                    u = str(row.get("url", ""))
                                    if same_host(u, root):
                                        historical.add(u)
                                except Exception:
                                    continue
            except Exception as e:
                errors.append({"source": "commoncrawl", "error": str(e)[:180]})
    return {
        "enabled": True,
        "urls": sorted(urls)[:300],
        "historical": sorted(historical)[:300],
        "blobs": blobs[:20],
        "errors": errors,
        "directory_candidates": sorted(directory_urls)[:240],
        "directory_reports": directory_reports[:20],
    }


