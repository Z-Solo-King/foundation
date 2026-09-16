#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.github.com/app/installations?per_page=100"
EXPECTED_ACCOUNT = "Z-Solo-King"


def main() -> int:
    jwt = os.environ.get("OPERATIONS_APP_JWT")
    if not jwt:
        print("Missing OPERATIONS_APP_JWT", file=sys.stderr)
        return 1
    req = urllib.request.Request(
        API,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {jwt}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "foundation-production-release",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            installations = json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            payload = json.loads(body)
            print(json.dumps({k: payload.get(k) for k in ("message", "errors", "documentation_url")}))
        except json.JSONDecodeError:
            print(f"GitHub App installation discovery failed: HTTP {exc.code}")
        return 1
    matches = [item for item in installations if (item.get("account") or {}).get("login") == EXPECTED_ACCOUNT]
    if len(matches) != 1:
        print(f"Expected exactly one GitHub App installation for {EXPECTED_ACCOUNT}; found {len(matches)}")
        return 1
    installation_id = matches[0].get("id")
    if not isinstance(installation_id, int) or installation_id <= 0:
        print("Resolved GitHub App installation has an invalid id")
        return 1
    print(installation_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
