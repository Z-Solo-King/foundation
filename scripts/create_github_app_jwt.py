#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import subprocess
import sys
import time

def b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

def main() -> int:
    if len(sys.argv) != 3:
        print("usage: create_github_app_jwt.py APP_ID PRIVATE_KEY_FILE", file=sys.stderr)
        return 2
    app_id, key_file = sys.argv[1:]
    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {"iat": now - 60, "exp": now + 540, "iss": app_id}
    unsigned = f"{b64url(json.dumps(header, separators=(",", ":")).encode())}.{b64url(json.dumps(payload, separators=(",", ":")).encode())}".encode()
    signed = subprocess.run(["openssl", "dgst", "-sha256", "-sign", key_file], input=unsigned, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    print(unsigned.decode() + "." + b64url(signed.stdout))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())