#!/usr/bin/env python3
"""Fail-closed source inventory for shortlisted multimodal GGUF artifacts.

Only verifies Hugging Face tree file existence and byte sizes.
Never claims a model/projector pair is compatible or that inference ran.
"""
import argparse
import json
import urllib.request
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/"data/local-llm-runtime-audit.json"
CATALOG=ROOT/"data/local-llm-catalog.json"

def verify(audit, catalog):
    ids={m["id"]:m for m in catalog["models"]}
    assert audit["schemaVersion"]==1
    assert len(audit["models"])==len({m["modelId"] for m in audit["models"]})
    for row in audit["models"]:
        assert row["modelId"] in ids
        model=ids[row["modelId"]]
        assert "vision" in model["workloads"]
        assert row["repository"]==model["repository"]
        assert row["compatibilityStatus"]=="untested"
        assert row["visionInferenceStatus"]=="untested"
        p=row["projectorCandidate"]
        assert p["inventoryStatus"] in {"listed-not-byte-verified","hub-byte-verified","not-found"}
        if p["inventoryStatus"]=="hub-byte-verified":
            assert type(p["sizeBytes"]) is int and p["sizeBytes"]>100_000
        else:
            assert p["sizeBytes"] is None

def fetch(repo):
    url="https://huggingface.co/api/models/"+quote(repo,safe="/")+"/tree/main?recursive=true&expand=false"
    with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"SXF-runtime-source-audit/1.0"}),timeout=25) as r:
        result=json.load(r)
    if not isinstance(result,list): raise ValueError("Invalid Hub tree")
    return result

def refresh(audit, fetcher=fetch):
    # Resolve all repositories BEFORE changing anything; intermittent upstream errors fail the entire update.
    tree={repo:fetcher(repo) for repo in sorted({r["repository"] for r in audit["models"]})}
    out=json.loads(json.dumps(audit))
    for row in out["models"]:
        p=row["projectorCandidate"]
        found=[f for f in tree[row["repository"]] if f.get("path")==p["filename"] and f.get("type")=="file"]
        if not found:
            p["inventoryStatus"]="not-found";p["sizeBytes"]=None
        else:
            size=found[0].get("size")
            if type(size) is not int or size<100_000:raise ValueError("Hub file has no verified size: "+row["repository"]+"/"+p["filename"])
            p["inventoryStatus"]="hub-byte-verified";p["sizeBytes"]=size
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--refresh",action="store_true")
    args=ap.parse_args()
    audit=json.loads(AUDIT.read_text())
    catalog=json.loads(CATALOG.read_text())
    verify(audit,catalog)
    if args.refresh:
        new=refresh(audit)
        verify(new,catalog)
        AUDIT.write_text(json.dumps(new,indent=2)+"\n")
    print("PASS: projector source inventory; compatibility and vision inference remain untested")
if __name__=="__main__":main()
