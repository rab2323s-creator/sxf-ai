#!/usr/bin/env python3
"""Build the public local-LLM catalog from an explicit reviewed Hugging Face allowlist.

Fail closed: never replace a valid snapshot with missing/uncertain source data.
No model-quality, compatibility or throughput measurements are inferred.
"""
import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "data/local-llm-sources.json"
OUTPUT = ROOT / "data/local-llm-catalog.json"
RE_QUANT = re.compile(r"(?:^|[-_.])(IQ4_XS|Q[234568]_[A-Z0-9_]+|UD-Q[345]_[A-Z0-9_]+)(?:[.-]|$)", re.I)

def load(path):
    return json.loads(path.read_text(encoding="utf-8"))

def fetch_tree(repo, revision="main"):
    parts = repo.split("/")
    if len(parts) != 2 or not all(re.fullmatch(r"[\w.-]+", x) for x in parts):
        raise ValueError("Untrusted repository identifier")
    url = "https://huggingface.co/api/models/" + quote(repo, safe="/") + "/tree/" + quote(revision, safe="") + "?recursive=true&expand=false"
    req = urllib.request.Request(url, headers={"User-Agent":"SXF-local-catalog/2.0", "Accept":"application/json"})
    with urllib.request.urlopen(req, timeout=25) as response:
        entries = json.load(response)
    if not isinstance(entries, list):
        raise ValueError("Invalid Hugging Face tree response")
    return entries

def variants(entry, items, allowed, checked):
    published = []
    repo = entry["repo"]
    for item in items:
        filename = item.get("path", "")
        size = item.get("size")
        if not isinstance(filename, str) or "/" in filename or not filename.lower().endswith(".gguf"):
            continue
        if not isinstance(size, int) or isinstance(size, bool) or size < 1_000_000 or size > 500_000_000_000:
            continue
        if re.search(r"-\d{5}-of-\d{5}\.gguf$", filename, re.I) or re.search(r"mmproj|vision-encoder", filename, re.I):
            continue
        matches = RE_QUANT.findall(filename)
        quant = matches[-1].upper() if matches else None
        if quant not in allowed:
            continue
        published.append({
            "id":"hf:"+repo+"/"+filename,
            "family":entry["name"],
            "name":entry["name"]+" "+quant,
            "format":"GGUF", "tag":None, "quantization":quant,
            "sizeBytes":size, "sizeGb":round(size/1_000_000_000, 3),
            "sizeEvidence":"hub-file-bytes", "sourceType":"huggingface-repository",
            "sourceUrl":"https://huggingface.co/"+repo+"/blob/"+entry.get("revision","main")+"/"+quote(filename),
            "repository":repo, "filename":filename, "checkedAt":checked,
            "workloads":entry["workloads"], "license":entry["license"],
            "licenseEvidence":"curated-repository-classification; check model card",
            "note":"Exact Hub file bytes; not measured VRAM. Review additional assets and runtime support before installation.",
            "performance":None, "sxfUrl":entry.get("sxfUrl"),
            "extraAssets":("vision" in entry["workloads"])
        })
    return sorted(published,key=lambda x:(x["family"],x["quantization"],x["filename"]))

def build(old, config, fetch=fetch_tree, *, minimum_success=1):
    allowed=set(config["allowedQuantizations"])
    accepted=[x for x in old["models"] if x["format"]=="Ollama"]
    succeeded=0; failed=[]
    existing={m["id"]:m for m in old["models"] if m["format"]=="GGUF"}
    updated={}
    checked=datetime.now(timezone.utc).date().isoformat()
    for entry in config["repositories"]:
        try:
            tree=fetch(entry["repo"],entry.get("revision","main"))
            found=variants(entry,tree,allowed,checked)
            if not found:
                raise ValueError("No approved, unsharded GGUF files with byte sizes")
            succeeded+=1
            for m in found: updated[m["id"]]=m
        except Exception as exc:
            failed.append({"repository":entry["repo"],"reason":str(exc)[:150]})
            for key,m in existing.items():
                if m.get("repository")==entry["repo"]: updated[key]=m
    if succeeded<minimum_success:
        raise ValueError("No repositories verified: refusing to overwrite the previous catalog")
    limit=int(config["maxPublished"])
    combined=accepted+sorted(updated.values(),key=lambda x:(x["family"].lower(),x["id"]))
    if len(combined)>limit: combined=combined[:limit]
    return {
        "schemaVersion":2, "generatedAt":checked,
        "methodology":"Ollama tag sizes are curated rounded publisher snapshots; GGUF bytes are fetched from the Hub tree API. Memory fit is a planning heuristic, never a hardware measurement.",
        "countPolicy":"An entry denotes an artifact/tag, not a distinct model family. Sharded or multimodal auxiliary files are excluded from the simple one-file catalog.",
        "verification":{"successfulRepositories":succeeded,"failedRepositories":failed},
        "models":combined
    }

def validate(catalog):
    ids=set()
    for m in catalog["models"]:
        assert m["id"] not in ids, "Duplicate artifact"
        ids.add(m["id"])
        assert m["sizeGb"]>0 and m["sourceUrl"].startswith("https://"), m["id"]
        assert m["workloads"] and set(m["workloads"])<= {"coding","chat","vision"}
        if m["format"]=="GGUF":
            assert isinstance(m["sizeBytes"],int) and m["sizeEvidence"]=="hub-file-bytes"
        assert m.get("performance") is None, "Unknown throughput must not be fabricated"

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--check",action="store_true")
    args=cli.parse_args()
    old=load(OUTPUT); config=load(SOURCES)
    validate(old)
    if args.check:
        print("PASS: local catalog records",len(old["models"]))
        return
    new=build(old,config)
    validate(new)
    if len(new["models"])<len(old["models"]):
        raise ValueError("Refusing catalog shrinkage")
    OUTPUT.write_text(json.dumps(new,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Verified {new['verification']['successfulRepositories']} repositories; {len(new['models'])} total artifacts; {len(new['verification']['failedRepositories'])} repositories unavailable")

if __name__=="__main__":
    main()
