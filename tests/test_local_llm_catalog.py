#!/usr/bin/env python3
"""Offline, deterministic regression tests for the GGUF ingestion gate."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from update_local_llm_catalog import build, validate, variants, load

def main():
 old=load(ROOT/"data/local-llm-catalog.json")
 config=load(ROOT/"data/local-llm-sources.json")
 validate(old)
 old={"schemaVersion":2,"models":[m for m in old["models"] if m["format"]=="Ollama"]}
 assert len(old["models"])>=13
 entry={"repo":"Example/Repo","name":"Sample 8B","workloads":["chat"],"license":"unknown"}
 rows=[{"path":"Sample-8B-Q4_K_M.gguf","size":5_123_456_789},
       {"path":"Sample-8B-Q8_0.gguf","size":8_234_567_890},
       {"path":"Sample-8B-00001-of-00002.gguf","size":1234567890},
       {"path":"mmproj-Sample-Q4_K_M.gguf","size":1234567890},
       {"path":"Sample-Q4_K_M.gguf","size":None}]
 found=variants(entry,rows,{"Q4_K_M","Q8_0"},"2026-10-24")
 assert len(found)==2, found
 assert found[0]["sizeEvidence"]=="hub-file-bytes"
 assert abs(found[0]["sizeGb"]-5.123)<0.01 or abs(found[1]["sizeGb"]-5.123)<0.01
 def mock(repo,revision):return rows
 tiny={"maxPublished":200,"allowedQuantizations":["Q4_K_M","Q8_0"],"repositories":[entry]}
 updated=build(old,tiny,mock)
 validate(updated)
 assert len(updated["models"])==len(old["models"])+2
 assert updated["verification"]["successfulRepositories"]==1
 def fail(repo,revision):raise OSError("upstream unavailable")
 try:build(old,tiny,fail)
 except ValueError:pass
 else:raise AssertionError("Updater must fail closed with no upstream data")
 print("PASS: only exact, unsharded source-file bytes admitted; failures leave last snapshot intact")

if __name__=="__main__":main()
