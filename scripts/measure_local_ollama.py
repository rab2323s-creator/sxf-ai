#!/usr/bin/env python3
"""Local-only Ollama + NVIDIA measurement capture; no synthetic measurements.

Runs exclusively against 127.0.0.1. Produces a review artifact, NOT public data.
For GPU memory sampling, nvidia-smi must exist and must name exactly one GPU.
"""
import argparse
import base64
import hashlib
import datetime as dt
import json
import os
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

API="http://127.0.0.1:11434"
CATALOG=Path(__file__).resolve().parents[1]/"data/local-llm-catalog.json"

def request(path,payload=None):
    data=None if payload is None else json.dumps(payload).encode()
    req=urllib.request.Request(API+path,data=data,headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=600) as resp:return json.load(resp)

def gpu_sample():
    output=subprocess.check_output(["nvidia-smi","--query-gpu=name,uuid,memory.total,memory.used","--format=csv,noheader,nounits"],text=True,timeout=8)
    lines=[x.strip() for x in output.splitlines() if x.strip()]
    if len(lines)!=1:raise RuntimeError("Exactly one NVIDIA GPU required; no ambiguous multi-GPU accounting")
    pieces=[x.strip() for x in lines[0].split(",")]
    if len(pieces)!=4:raise RuntimeError("Unexpected nvidia-smi CSV")
    return {"name":pieces[0],"uuid":pieces[1],"totalMiB":int(pieces[2]),"usedMiB":int(pieces[3])}

def run(args):
    catalog=json.loads(CATALOG.read_text())
    matches=[m for m in catalog["models"] if m["id"]==args.model_id and m["format"]=="Ollama" and m.get("tag")]
    if len(matches)!=1:raise ValueError("Use an exact allowlisted Ollama tag ID from the local catalog")
    model=matches[0]
    if args.image and "vision" not in model["workloads"]:
        raise ValueError("Vision runs require a source-listed vision-capable Ollama tag")
    image_bytes=None
    image_sha256=None
    if args.image:
        image_bytes=Path(args.image).read_bytes()
        if not (64<=len(image_bytes)<=8_000_000):
            raise ValueError("Image fixture must be 64 bytes to 8 MB")
        if not (image_bytes.startswith(bytes.fromhex("89504e470d0a1a0a")) or image_bytes.startswith(bytes.fromhex("ffd8ff"))):
            raise ValueError("Image fixture must be PNG or JPEG")
        image_sha256=hashlib.sha256(image_bytes).hexdigest()
    if args.context not in (4096,8192,16384,32768):raise ValueError("Invalid context")
    if args.repeats<3:raise ValueError("Minimum three measured trials required")
    baseline=gpu_sample()
    # Read actual installed version and explicit model availability before measuring.
    version=request("/api/version")
    tags=request("/api/tags")
    installed={m.get("name") for m in tags.get("models",[])}
    if not any(t.split(":")[0]==model["tag"].split(":")[0] and t.split(":")[-1]==model["tag"].split(":")[-1] for t in installed):
        raise RuntimeError("Exact model tag is not listed locally; pull it manually after license review")
    runs=[]
    prompt="Describe the main visible objects in the image." if image_bytes else "Explain the difference between GPU VRAM and system RAM in three paragraphs."
    for i in range(args.repeats+1):
        peak=[baseline["usedMiB"]];fail=[None];stop=threading.Event()
        def poll():
            while not stop.wait(0.20):
                try:peak.append(gpu_sample()["usedMiB"])
                except Exception as e:fail[0]=str(e);stop.set()
        watcher=threading.Thread(target=poll,daemon=True)
        watcher.start()
        started=time.monotonic()
        try:
            ans=request("/api/generate",{"model":model["tag"],"prompt":prompt,"images":[base64.b64encode(image_bytes).decode("ascii")] if image_bytes else [],"think":False,"stream":False,"keep_alive":"5m","options":{"num_ctx":args.context,"temperature":0,"num_predict":192}})
            wall=time.monotonic()-started
        finally:
            stop.set();watcher.join(timeout=3)
        if fail[0]:raise RuntimeError("GPU memory telemetry failed: "+fail[0])
        if ans.get("done") is not True or type(ans.get("eval_count")) is not int or type(ans.get("eval_duration")) is not int or ans["eval_count"]<=0 or ans["eval_duration"]<=0:raise RuntimeError("Incomplete Ollama generation metrics")
        if not isinstance(ans.get("response"),str) or not ans["response"].strip():raise RuntimeError("Empty generated output; possible thinking-only answer. Requested think=false, but the model/runtime may ignore it. Reasoning chars="+str(len(ans.get("thinking") or ""))+", done_reason="+str(ans.get("done_reason"))+"; refusing to publish this run.")
        record={"trial":i,"warmup":i==0,"wallSeconds":round(wall,3),"completionTokens":ans["eval_count"],"generationDurationNs":ans["eval_duration"],"tokensPerSecond":round(ans["eval_count"]*1e9/ans["eval_duration"],4),"observedPeakGpuUsedMiB":max(peak),"observedGpuUsedDeltaMiB":max(peak)-baseline["usedMiB"],"telemetrySampleIntervalMs":200}
        runs.append(record)
    measured=[r for r in runs if not r["warmup"]]
    if len(measured)<3 or min(r["tokensPerSecond"] for r in measured)<=0:raise RuntimeError("Incomplete repeats")
    out={"schemaVersion":1,"kind":"local-measurement-candidate","publicationStatus":"review-required","measuredAt":dt.datetime.now(dt.timezone.utc).isoformat(),"modelId":model["id"],"modelTag":model["tag"],"quantization":"unknown-ollama-publisher-tag","runtime":"Ollama","runtimeVersion":version.get("version"),"gpu":baseline,"workload":"vision" if image_bytes else "chat","inputImageSha256":image_sha256,"inputImageBytes":len(image_bytes) if image_bytes else None,"contextTokens":args.context,"requestedOutputTokens":192,"requestedThink":False,"concurrency":1,"warmupCount":1,"repetitions":args.repeats,"runRecords":runs,"notes":"GPU total used memory sampled every 200ms, not exact allocation to model. Measured peak is sample-limited; GPU may contain other processes. Requested think=false; disablement may not be honored by every model/runtime. A vision run sends a real image payload but does not establish output correctness. CPU offload is not independently confirmed. Do not publish as full-GPU compatibility without runtime residency evidence."}
    output=Path(args.output)
    if output.exists():raise FileExistsError("Refusing to overwrite a measurement artifact")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(out,indent=2)+"\n")
    print("Measurement candidate saved for human review:",output)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--model-id",required=True)
    p.add_argument("--image",help="Local PNG/JPEG fixture for vision Ollama benchmark")
    p.add_argument("--context",type=int,default=4096)
    p.add_argument("--repeats",type=int,default=3)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    run(a)
