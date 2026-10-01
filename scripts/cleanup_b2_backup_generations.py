#!/usr/bin/env python3
"""Delete stale Backblaze B2 repository-backup object versions after verification."""
from __future__ import annotations
import argparse, json, subprocess, tempfile
from pathlib import Path
from typing import Iterable

PREFIX = "repository-backup/"
DELETE_BATCH_SIZE = 1000

def _aws_json(*args: str) -> dict:
    result = subprocess.run(["aws","s3api",*args,"--output","json"],check=True,capture_output=True,text=True)
    return json.loads(result.stdout or "{}")

def load_keep_keys(keep_file: Path) -> set[str]:
    keys=set()
    for line in keep_file.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        fields=line.split("\t")
        if not fields or not fields[0].startswith(PREFIX):
            raise SystemExit("backup keep-file contains a key outside the repository-backup/ prefix")
        keys.add(fields[0])
    if not keys: raise SystemExit("backup keep-file is empty")
    return keys

def deletion_plan(payload: dict, keep_keys: set[str]) -> list[dict[str,str]]:
    deletions=[]
    for field in ("Versions","DeleteMarkers"):
        for row in payload.get(field,[]) or []:
            key=str(row.get("Key") or ""); version_id=str(row.get("VersionId") or "")
            if not key.startswith(PREFIX) or not version_id: continue
            if key in keep_keys and row.get("IsLatest") is True: continue
            deletions.append({"Key":key,"VersionId":version_id})
    return deletions

def list_all_versions(bucket: str, endpoint: str) -> dict[str,list[dict[str,object]]]:
    versions=[]; markers=[]; key_marker=""; version_id_marker=""
    while True:
        args=["list-object-versions","--bucket",bucket,"--prefix",PREFIX,"--endpoint-url",endpoint]
        if key_marker: args.extend(["--key-marker",key_marker])
        if version_id_marker: args.extend(["--version-id-marker",version_id_marker])
        payload=_aws_json(*args)
        versions.extend(row for row in (payload.get("Versions",[]) or []) if isinstance(row,dict))
        markers.extend(row for row in (payload.get("DeleteMarkers",[]) or []) if isinstance(row,dict))
        if not payload.get("IsTruncated"):
            return {"Versions":versions,"DeleteMarkers":markers}
        next_key=str(payload.get("NextKeyMarker") or "")
        next_version=str(payload.get("NextVersionIdMarker") or "")
        if not next_key or not next_version:
            raise SystemExit("B2 version listing reported truncation without complete continuation markers")
        key_marker, version_id_marker = next_key, next_version

def delete_versions(bucket: str, endpoint: str, deletions: Iterable[dict[str,str]]) -> None:
    items=list(deletions)
    for start in range(0,len(items),DELETE_BATCH_SIZE):
        batch=items[start:start+DELETE_BATCH_SIZE]
        with tempfile.NamedTemporaryFile("w",encoding="utf-8",delete=False,suffix=".json") as handle:
            json.dump({"Objects":batch,"Quiet":True},handle); path=handle.name
        try:
            _aws_json("delete-objects","--bucket",bucket,"--endpoint-url",endpoint,"--delete",f"file://{path}")
        finally:
            Path(path).unlink(missing_ok=True)

def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--bucket",required=True); parser.add_argument("--endpoint",required=True); parser.add_argument("--keep-file",required=True)
    args=parser.parse_args()
    keep_keys=load_keep_keys(Path(args.keep_file))
    payload=list_all_versions(args.bucket,args.endpoint)
    deletions=deletion_plan(payload,keep_keys)
    delete_versions(args.bucket,args.endpoint,deletions)
    listed=len(payload["Versions"])+len(payload["DeleteMarkers"])
    print(f"B2 retention cleanup: kept_current_keys={len(keep_keys)} listed_versions={listed} deleted_versions={len(deletions)} prefix={PREFIX}")
    return 0

if __name__=="__main__": raise SystemExit(main())
