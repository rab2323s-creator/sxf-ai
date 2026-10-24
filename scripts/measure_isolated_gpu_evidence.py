#!/usr/bin/env python3
"""Isolated GPU evidence capture; no guessed benchmarks or website publishing.

Requires exactly one NVIDIA GPU and local Ollama. Measures Ollama API generation
throughput while recording image answers, loaded model metadata and GPU-wide
memory telemetry. GPU-wide memory is never equated with model-only VRAM.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import threading
import time
import urllib.request
import zlib

API = "http://127.0.0.1:11434"
TRIALS = (
    ("qwen3:8b", "chat", "qwen3-8b"),
    ("qwen3-vl:4b", "vision", "qwen3-vl-4b"),
)


def api(path, payload=None):
    raw = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(API + path, data=raw, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=600) as response:
        return json.load(response)


def gpu():
    raw = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=name,uuid,memory.total,memory.used,driver_version",
         "--format=csv,noheader,nounits"], text=True, timeout=12
    )
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    if len(lines) != 1:
        raise RuntimeError("Exactly one NVIDIA GPU must be assigned.")
    parts = [part.strip() for part in lines[0].split(",")]
    if len(parts) != 5:
        raise RuntimeError("Unexpected nvidia-smi output: " + raw[:200])
    return {"name": parts[0], "gpuUuidSha256": hashlib.sha256(parts[1].encode()).hexdigest(),
            "totalMiB": int(parts[2]), "usedMiB": int(parts[3]),
            "driverVersion": parts[4]}


def png_fixture():
    width = height = 128
    pixels = b"".join(
        b"\x00" + b"".join(
            bytes((238, 42, 42)) if 24 <= x < 104 and 24 <= y < 104 else bytes((36, 77, 208))
            for x in range(width))
        for y in range(height)
    )
    def chunk(kind, data):
        return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack("!2I5B", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(pixels)) + chunk(b"IEND", b""))


def resident_models():
    models = api("/api/ps").get("models")
    if not isinstance(models, list):
        raise RuntimeError("Ollama /api/ps did not return a models array.")
    return models


def unload_all():
    for item in resident_models():
        name = item.get("name") or item.get("model")
        if not name:
            raise RuntimeError("Cannot safely unload a resident Ollama model without a name.")
        print("Unloading prior resident model:", name, flush=True)
        api("/api/generate", {"model": name, "keep_alive": 0, "stream": False})
    for _ in range(60):
        if not resident_models():
            time.sleep(2)  # Allow GPU driver to finish releasing the previous model.
            if not resident_models():
                return
        time.sleep(1)
    raise RuntimeError("Could not clear previous Ollama model residency; no baseline recorded.")


def capture_generation(payload):
    samples = [gpu()["usedMiB"]]
    errors = []
    stop = threading.Event()
    def sample():
        while not stop.wait(0.20):
            try:
                samples.append(gpu()["usedMiB"])
            except Exception as exc:
                errors.append(str(exc))
                stop.set()
    thread = threading.Thread(target=sample, daemon=True)
    thread.start()
    start = time.monotonic()
    try:
        response = api("/api/generate", payload)
        wall = time.monotonic() - start
    finally:
        stop.set()
        thread.join(timeout=5)
    samples.append(gpu()["usedMiB"])
    if errors:
        raise RuntimeError("GPU monitoring interrupted: " + errors[0])
    if (response.get("done") is not True or type(response.get("eval_count")) is not int
            or type(response.get("eval_duration")) is not int
            or response["eval_count"] <= 0 or response["eval_duration"] <= 0):
        raise RuntimeError("Incomplete Ollama measured token metrics.")
    answer = response.get("response")
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("Empty answer; cannot verify vision quality or text generation.")
    return response, wall, max(samples), len(samples)


def run(output_dir, ollama_bin, *, context=4096, repeats=3):
    if not shutil.which("nvidia-smi"):
        raise RuntimeError("No NVIDIA GPU in Colab. This is a hardware allocation issue, not an SXF code error.")
    if context != 4096 or repeats < 3:
        raise ValueError("This review procedure uses context=4096 and at least 3 measured runs.")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.glob("*.json")):
        raise FileExistsError("Evidence files already exist. Use a fresh output directory; never overwrite a capture.")
    base_device = gpu()
    runtime_version = api("/api/version").get("version")
    if not runtime_version:
        raise RuntimeError("Ollama server version unavailable.")

    image_bytes = png_fixture()
    image_file = output_dir / "vision-square.png"
    image_file.write_bytes(image_bytes)
    digest = hashlib.sha256(image_bytes).hexdigest()

    report_paths = []
    for tag, workload, stem in TRIALS:
        unload_all()
        baseline = gpu()
        if baseline["gpuUuidSha256"] != base_device["gpuUuidSha256"]:
            raise RuntimeError("GPU changed during the benchmark.")
        print("Clean Ollama baseline for", tag, ":", baseline["usedMiB"], "MiB GPU-wide", flush=True)
        subprocess.run([ollama_bin, "pull", tag], check=True)
        tags = [t for t in api("/api/tags").get("models", [])
                if (t.get("name") or t.get("model")) == tag]
        if len(tags) != 1 or not isinstance(tags[0].get("digest"), str):
            raise RuntimeError("Installed tag/digest cannot be uniquely verified: " + tag)
        info = tags[0]
        prompt = ("Describe the main visible shapes and colors in this image." if workload == "vision"
                  else "Explain how GPU VRAM differs from system RAM in three short paragraphs.")
        payload = {
            "model": tag, "prompt": prompt, "stream": False, "think": False,
            "keep_alive": "20m", "options": {
                "num_ctx": context, "num_predict": 192, "temperature": 0
            }
        }
        if workload == "vision":
            payload["images"] = [base64.b64encode(image_bytes).decode("ascii")]

        records = []
        model_ps = None
        for i in range(repeats + 1):
            response, wall, device_peak, samples = capture_generation(payload)
            ps = resident_models()
            if len(ps) != 1 or (ps[0].get("name") or ps[0].get("model")) != tag:
                raise RuntimeError("Another model is resident or requested model not resident. Not isolated.")
            model_ps = ps[0]
            record = {
                "trial": i, "warmup": i == 0, "wallSeconds": round(wall, 4),
                "completionTokens": response["eval_count"],
                "generationDurationNs": response["eval_duration"],
                "tokensPerSecond": round(response["eval_count"] * 1e9 / response["eval_duration"], 4),
                "promptTokens": response.get("prompt_eval_count"),
                "promptDurationNs": response.get("prompt_eval_duration"),
                "loadDurationNs": response.get("load_duration"),
                "totalDurationNs": response.get("total_duration"),
                "doneReason": response.get("done_reason"),
                "answer": response["response"], "answerSha256": hashlib.sha256(response["response"].encode()).hexdigest(),
                "gpuWideObservedPeakUsedMiB": device_peak,
                "gpuWideObservedIncreaseOverBaselineMiB": max(0, device_peak - baseline["usedMiB"]),
                "gpuSamples": samples, "gpuSampleIntervalMs": 200,
                "psReportedSizeBytes": model_ps.get("size"), "psReportedGpuResidentBytes": model_ps.get("size_vram"),
            }
            records.append(record)
            print(tag, "warmup" if i == 0 else "trial " + str(i),
                  "tokens/s =", record["tokensPerSecond"], flush=True)
        report = {
            "schemaVersion": 2, "kind": "sxf-isolated-gpu-evidence",
            "publicationStatus": "review-required-not-published",
            "measuredAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            "gpu": baseline, "runtime": "Ollama", "runtimeVersion": runtime_version,
            "modelId": "ollama:" + tag, "modelTag": tag, "modelDigest": info["digest"],
            "modelSizeBytes": info.get("size"),
            "reportedQuantization": (info.get("details") or {}).get("quantization_level"),
            "workload": workload, "prompt": prompt, "contextTokens": context,
            "requestedOutputTokens": 192, "requestedThink": False, "concurrency": 1,
            "warmupCount": 1, "repetitions": repeats,
            "imageSha256": digest if workload == "vision" else None,
            "imageBytes": len(image_bytes) if workload == "vision" else None,
            "expectedImageDescription": "A centered red square on a blue background." if workload == "vision" else None,
            "visionAnswerReview": "manual-check-required" if workload == "vision" else None,
            "gpuBaselineAfterUnloadingOthers": baseline,
            "gpuAfterLastInference": gpu(),
            "ollamaPsAfterInference": model_ps,
            "runRecords": records,
            "limits": "Whole-GPU 200ms samples are NOT model-exclusive VRAM or verified true peaks. /api/ps size_vram is Ollama-reported, not independent full residency proof. Generation-only tok/s excludes prefill/loading. Answers are retained for review; an answer does not alone prove vision accuracy. Physical GPU origin not independently attested."
        }
        path = output_dir / (stem + "-isolated.json")
        if path.exists():
            raise FileExistsError("Would overwrite evidence " + str(path))
        path.write_text(json.dumps(report, indent=2) + "\n")
        report_paths.append(path)
        # Unload NOW, so subsequent model is not contaminated by this one.
        unload_all()

    return [*report_paths, image_file]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ollama-bin", required=True)
    parser.add_argument("--context", type=int, default=4096)
    parser.add_argument("--repeats", type=int, default=3)
    options = parser.parse_args()
    paths = run(options.output_dir, options.ollama_bin, context=options.context, repeats=options.repeats)
    print("PASS: measured user-run evidence recorded for human review:", *(str(x) for x in paths), sep="\n")
