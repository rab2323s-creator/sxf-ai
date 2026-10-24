#!/usr/bin/env python3
"""Review gate for externally captured local GPU measurements.

Converts a local candidate into one draft registry entry only after verifying
all required evidence. Does NOT change the public registry by itself.
"""
import argparse
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/"data/local-llm-catalog.json"
REGISTRY=ROOT/"data/local-llm-benchmarks.json"

def inspect(candidate,catalog):
    assert candidate["schemaVersion"]==1 and candidate["kind"]=="local-measurement-candidate"
    assert candidate["publicationStatus"]=="review-required"
    assert candidate["repetitions"]>=3 and candidate["warmupCount"]>=1
    model=next((m for m in catalog["models"] if m["id"]==candidate["modelId"]),None)
    assert model is not None and model["format"]=="Ollama" and model["tag"]==candidate["modelTag"]
    assert candidate["runtime"]=="Ollama" and isinstance(candidate["runtimeVersion"],str) and candidate["runtimeVersion"]
    assert isinstance(candidate["contextTokens"],int) and candidate["contextTokens"]>=128
    assert candidate["concurrency"]==1
    assert candidate["workload"] in model["workloads"]
    if candidate["workload"]=="vision":
        assert isinstance(candidate.get("inputImageSha256"),str) and len(candidate["inputImageSha256"])==64
        assert type(candidate.get("inputImageBytes")) is int and candidate["inputImageBytes"]>=64
    else:
        assert candidate.get("inputImageSha256") is None
    gpu=candidate["gpu"]
    assert isinstance(gpu["name"],str) and gpu["name"] and isinstance(gpu["uuid"],str) and gpu["uuid"]
    assert type(gpu["totalMiB"]) is int and gpu["totalMiB"]>=1024
    runs=candidate["runRecords"]
    assert len(runs)==candidate["repetitions"]+candidate["warmupCount"]
    assert sum(bool(r["warmup"]) for r in runs)==candidate["warmupCount"]
    live=[r for r in runs if not r["warmup"]]
    for r in live:
        assert type(r["completionTokens"]) is int and r["completionTokens"]>0
        assert type(r["generationDurationNs"]) is int and r["generationDurationNs"]>0
        assert type(r["observedPeakGpuUsedMiB"]) is int and r["observedPeakGpuUsedMiB"]>=0
        actual=r["completionTokens"]*1e9/r["generationDurationNs"]
        assert math.isfinite(actual) and actual>0
        assert abs(actual-r["tokensPerSecond"])<0.001
    return model, live

def main():
    p=argparse.ArgumentParser()
    p.add_argument("candidate",type=Path)
    p.add_argument("--evidence-url",required=True,help="Immutable accessible measurement report URL, human-reviewed")
    p.add_argument("--output",type=Path,required=True,help="A draft entry (NOT the public registry)")
    args=p.parse_args()
    if not args.evidence_url.startswith("https://"):raise ValueError("Evidence must use HTTPS")
    candidate=json.loads(args.candidate.read_text())
    catalog=json.loads(CATALOG.read_text())
    model,live=inspect(candidate,catalog)
    # Conservative: publish each trial rather than a misleading invented aggregate.
    records=[]
    for r in live:
        records.append({"modelId":model["id"],"gpu":candidate["gpu"]["name"],"runtime":candidate["runtime"]+" "+candidate["runtimeVersion"],"quantization":model["tag"],"measuredAt":candidate["measuredAt"][:10],"sourceUrl":args.evidence_url,"tokensPerSecond":r["tokensPerSecond"],"contextTokens":candidate["contextTokens"],"concurrency":1,"evidenceType":"measured","measurementScope":"generation-only Ollama API eval_count/eval_duration","reviewStatus":"draft-not-published"})
    if args.output.exists():raise FileExistsError("Do not overwrite an existing review artifact")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({"schemaVersion":1,"publicationStatus":"draft-not-published","measurements":records},indent=2)+"\n")
    print(f"PASS: {len(records)} evidence-backed trial records prepared, not published")
if __name__=="__main__":main()
