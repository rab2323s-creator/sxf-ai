#!/usr/bin/env python3
"""Offline evidence regression tests; synthetic fixtures are never public results."""
import copy
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import audit_local_vision_sources as vision
from review_local_gpu_measurement import inspect
from measure_local_ollama import gpu_sample
catalog=json.loads((ROOT/"data/local-llm-catalog.json").read_text())
audit=json.loads((ROOT/"data/local-llm-runtime-audit.json").read_text())
vision.verify(audit,catalog)
def sample(repo):
 return [{"path":"mmproj-F16.gguf","type":"file","size":123456789},{"path":"mmproj-model-f16.gguf","type":"file","size":87654321}]
verified=vision.refresh(audit,sample)
vision.verify(verified,catalog)
assert all(x["projectorCandidate"]["inventoryStatus"]=="hub-byte-verified" for x in verified["models"])
assert all(x["compatibilityStatus"]=="untested" for x in verified["models"])
try:vision.refresh(audit,lambda repo:(_ for _ in ()).throw(OSError("unavailable")))
except OSError:pass
else:raise AssertionError("Inventory must fail closed on source outage")
model=next(m for m in catalog["models"] if m["id"]=="ollama:qwen3:8b")
trial={"trial":1,"warmup":False,"completionTokens":32,"generationDurationNs":2_000_000_000,"tokensPerSecond":16.0,"observedPeakGpuUsedMiB":5000,"observedGpuUsedDeltaMiB":200,"wallSeconds":2.4,"telemetrySampleIntervalMs":200}
candidate={"schemaVersion":1,"kind":"local-measurement-candidate","publicationStatus":"review-required","repetitions":3,"warmupCount":1,"modelId":model["id"],"modelTag":model["tag"],"runtime":"Ollama","runtimeVersion":"synthetic-test","workload":"chat","inputImageSha256":None,"contextTokens":4096,"concurrency":1,"gpu":{"name":"Synthetic GPU - NOT REAL","uuid":"SYNTHETIC","totalMiB":8192},"runRecords":[dict(trial,trial=0,warmup=True)]+[dict(trial,trial=i+1) for i in range(3)]}
inspect(candidate,catalog)
bad=copy.deepcopy(candidate);bad["runRecords"][1]["tokensPerSecond"]=99
try:inspect(bad,catalog)
except AssertionError:pass
else:raise AssertionError("Fabricated throughput accepted")
bad=copy.deepcopy(candidate);bad["runRecords"]=bad["runRecords"][:2]
try:inspect(bad,catalog)
except AssertionError:pass
else:raise AssertionError("Incomplete repetitions accepted")
registry=json.loads((ROOT/"data/local-llm-benchmarks.json").read_text())
assert registry["measurements"]==[], "Unreviewed measurements appeared in public data"
print("PASS: source-only vision inventory, fail-closed source requests, measurement math and empty public benchmark registry")
