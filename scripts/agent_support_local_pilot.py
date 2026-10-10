#!/usr/bin/env python3
"""Run an independently recorded, zero-vendor-API-fee local model experiment.

Requires a llama.cpp OpenAI-compatible server listening on 127.0.0.1.
This measures a local LLM making policy recommendations, NOT a production tool-using agent.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from agent_support_pilot import load, decide_oracle, extract, question, SYSTEM

SEEDS = [1103, 2207, 3301]
CATEGORIES = ("refund", "damage", "shipping", "cancel", "privacy", "warranty")
ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "agent-support-pilot-cases.json"


def check_local_url(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "http" or parts.hostname not in ("127.0.0.1", "localhost"):
        raise ValueError("Only localhost http endpoints allowed; this experiment must make no paid API calls")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("Invalid endpoint")
    return url.rstrip("/")


def request_local(url, model, text, seed, timeout):
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": text}],
        "temperature": 0,
        "seed": seed,
        "max_tokens": 160,
        "stream": False
    }
    req = urllib.request.Request(url + "/v1/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as res:
        response = json.load(res)
    content = response["choices"][0]["message"]["content"]
    return content, response.get("usage", {})


def evaluate(url, model, repeats=3, timeout=75, model_sha256="", engine_commit=""):
    url = check_local_url(url)
    data, policies = load()
    for case in data["cases"]:
        if decide_oracle(case) != case["expected_decision"]:
            raise ValueError("Preregistered rubric mismatch: " + case["id"])
    if repeats < 1 or repeats > 3:
        raise ValueError("Repeat count must be between 1 and 3")
    rows = []
    start = time.monotonic()
    for run_index, seed in enumerate(SEEDS[:repeats], start=1):
        for case in data["cases"]:
            begin = time.monotonic()
            raw, usage, error = "", {}, None
            try:
                raw, usage = request_local(url, model, question(case, policies), seed, timeout)
                prediction = extract(raw)
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
                    ValueError, KeyError, TypeError, IndexError) as exc:
                prediction = None
                error = type(exc).__name__ + ": " + str(exc)[:160]
            duration = time.monotonic() - begin
            rows.append({
                "run": run_index, "seed": seed, "case_id": case["id"], "category": case["category"],
                "expected": case["expected_decision"], "predicted": prediction,
                "correct": prediction == case["expected_decision"],
                "latency_seconds": round(duration, 3),
                "input_tokens": int(usage.get("prompt_tokens") or 0),
                "output_tokens": int(usage.get("completion_tokens") or 0),
                "response_text": raw[:1500],
                "error": error
            })
            print(f"run {run_index}/{repeats}: {case['id']} "
                  f"{'PASS' if rows[-1]['correct'] else 'FAIL'} ({duration:.1f}s)", flush=True)
    accuracy = []
    for i in range(1, repeats+1):
        subset = [r for r in rows if r["run"] == i]
        accuracy.append({
            "run": i,
            "correct": sum(r["correct"] for r in subset),
            "attempts": len(subset),
            "accuracy": round(sum(r["correct"] for r in subset)/len(subset), 4)
        })
    category = {}
    for name in CATEGORIES:
        cases = [r for r in rows if r["category"] == name]
        category[name] = {"correct": sum(r["correct"] for r in cases), "attempts": len(cases)}
    durations = [r["latency_seconds"] for r in rows]
    report = {
        "schema_version": "1.0",
        "evidence_type": "MEASURED LOCAL MODEL INFERENCE ON AUTHOR-CREATED SYNTHETIC SUPPORT CASES",
        "not_a_production_agent_benchmark": True,
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "model": model,
        "model_file_sha256": model_sha256,
        "llama_cpp_commit": engine_commit,
        "dataset_sha256": hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
        "dataset_name": data["dataset_name"], "dataset_version": data["dataset_version"],
        "preregistered_cases": len(data["cases"]),
        "repetitions": repeats,
        "seeds": SEEDS[:repeats],
        "setting": {"temperature": 0, "max_tokens": 160, "one_attempt_per_case": True,
                    "ground_truth": "Pre-registered deterministic policy labels"},
        "overall": {
            "attempts": len(rows),
            "correct": sum(r["correct"] for r in rows),
            "exact_match": round(sum(r["correct"] for r in rows)/len(rows), 4),
            "invalid_or_request_failures": sum(r["predicted"] is None for r in rows),
            "median_latency_seconds": round(statistics.median(durations), 3),
            "p95_latency_seconds": round(sorted(durations)[max(0, int(len(durations)*.95)-1)], 3),
            "wall_seconds": round(time.monotonic()-start, 3),
            "prompt_tokens": sum(r["input_tokens"] for r in rows),
            "completion_tokens": sum(r["output_tokens"] for r in rows),
            "provider_api_fees_usd": 0,
            "hardware_energy_cost_measured": False
        },
        "runs": accuracy, "per_category": category, "rows": rows,
        "limitations": [
            "All 24 cases are author-written synthetic examples; there are no real customer interactions.",
            "Local Qwen model supplies proposed support decisions, with no live tool execution.",
            "Exact-match rubric cannot measure full explanation quality or actual business value.",
            "No manual labor baseline, staffing saving or enterprise ROI is measured.",
            "Zero provider API fees does not imply zero hardware, electric power or engineering costs.",
            "This benchmark is not a representative production failure estimate or statistical confidence interval."
        ]
    }
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--server", default="http://127.0.0.1:8087")
    p.add_argument("--model", default="sxf-local-qwen3-4b")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--timeout", type=int, default=75)
    p.add_argument("--model-sha256", default="")
    p.add_argument("--engine-commit", default="")
    p.add_argument("--output", type=pathlib.Path, required=True)
    args = p.parse_args()
    try:
        report = evaluate(args.server, args.model, args.repeats, args.timeout,
                          args.model_sha256, args.engine_commit)
    except ValueError as ex:
        print(str(ex), file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"overall": report["overall"], "runs": report["runs"]}, indent=2))
    print("Results stored in:", args.output)
    # Tests can be negative; success means the evaluation ran, not that the model was accurate.
    return 0

if __name__ == "__main__":
    sys.exit(main())
