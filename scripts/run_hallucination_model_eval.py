#!/usr/bin/env python3
"""Paired, auditable OpenAI Responses API test. Never invent model outputs."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from datetime import datetime, timezone
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "guides/why-does-chatgpt-make-things-up/research/model-eval"
QUESTIONS = STUDY / "questions.json"
API = "https://api.openai.com/v1/responses"
INSTRUCTIONS = (
    "You are answering a real user's factual question. Answer in 1-4 plain-language "
    "sentences. Say when you cannot verify a detail. Never invent a citation, quotation, "
    "exact date, or source. Distinguish verified facts from speculation. Where you use "
    "a genuine web source, identify it. You may abstain rather than make an unsupported "
    "guess. Do not mention any evaluation or test."
)
FIELDS = [
    "id", "arm", "status", "reviewed_by", "reviewed_utc",
    "supporting_primary_url", "exact_passage_or_location",
    "citation_check", "notes",
]
LABELS = {"not_reviewed", "correct", "incorrect", "abstained", "mixed_or_unclear"}
CITATIONS = {"not_checked", "supported", "unsupported", "no_reference"}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def questions():
    raw = QUESTIONS.read_bytes()
    dataset = json.loads(raw)
    items = dataset["cases"]
    if dataset["status"] != "PREREGISTERED_NOT_RUN" or len(items) != 12:
        raise ValueError("Study questions must be pre-registered and contain 12 cases")
    if len({r["id"] for r in items}) != len(items):
        raise ValueError("Duplicate case ID")
    for item in items:
        if not re.fullmatch(r"E\d{2}", item["id"]):
            raise ValueError("Invalid case ID")
        if not item["primary_url"].startswith("https://"):
            raise ValueError("Reviewer needs a primary source")
        if not item["question"].strip() or not item["expected"].strip():
            raise ValueError("Incomplete registration")
    return dataset, hashlib.sha256(raw).hexdigest()


def payload(model, text, arm):
    p = {
        "model": model,
        "instructions": INSTRUCTIONS,
        "input": text,
        "max_output_tokens": 550,
        "store": False,
    }
    if arm == "with_web":
        p["tools"] = [{"type": "web_search", "search_context_size": "medium"}]
        p["tool_choice"] = "required"
    return p


def post(api_key, p):
    body = json.dumps(p).encode("utf-8")
    req = request.Request(API, data=body, headers={
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }, method="POST")
    begin = time.monotonic()
    try:
        with request.urlopen(req, timeout=130) as response:
            raw = response.read(4_000_000)
    except error.HTTPError as exc:
        # Do not log potentially sensitive response bodies.
        raise RuntimeError("API request failed: HTTP " + str(exc.code)) from None
    except error.URLError as exc:
        raise RuntimeError("API connection failed: " + str(exc.reason)) from None
    elapsed = round(time.monotonic() - begin, 3)
    result = json.loads(raw)
    if not isinstance(result, dict) or "output" not in result:
        raise ValueError("Unexpected API response; cannot store a valid output")
    return result, elapsed


def output_text(response):
    parts = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for fragment in item.get("content", []):
            if fragment.get("type") == "output_text":
                parts.append(fragment.get("text", ""))
    return "\n".join(parts).strip()


def tool_calls(response):
    return [x for x in response.get("output", []) if x.get("type") == "web_search_call"]


def run(model, max_cases, dry_run, acknowledge):
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", model):
        raise ValueError("Unsafe model name")
    dataset, digest = questions()
    selected = dataset["cases"][:max_cases]
    if dry_run:
        print(json.dumps({
            "status": "DRY_RUN_ONLY_NO_API_CALLS",
            "model": model,
            "questions": len(selected),
            "pairs": len(selected),
            "requests": 2 * len(selected),
            "arms": dataset["arms"],
            "sha256_questions": digest,
            "sample_baseline": payload(model, selected[0]["question"], "no_web"),
            "sample_web_tool": payload(model, selected[0]["question"], "with_web"),
        }, indent=2))
        return
    if not acknowledge:
        raise ValueError("API usage incurs charges; pass --acknowledge-api-costs to execute")
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set; no model requests were made")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = STUDY / "runs" / stamp
    out.mkdir(parents=True, exist_ok=False)
    manifest = {
        "state": "running", "created_utc": now(), "model_requested": model,
        "preregistered_questions_sha256": digest, "questions_selected": len(selected),
        "requested_responses": 2 * len(selected),
        "instructions": INSTRUCTIONS, "api": API, "runs": [],
    }
    write_json(out / "manifest.json", manifest)
    try:
        for number, case in enumerate(selected):
            # Counterbalanced arm ordering to reduce systematic order confounding.
            order = ["no_web", "with_web"] if number % 2 == 0 else ["with_web", "no_web"]
            pair_models = []
            for arm in order:
                name = case["id"] + "__" + arm + ".json"
                exact_request = payload(model, case["question"], arm)
                # Store the exact nonsecret JSON request BEFORE the API invocation.
                write_json(out / "requests" / name, exact_request)
                answer, elapsed = post(api_key, exact_request)
                write_json(out / "responses" / name, answer)
                calls = tool_calls(answer)
                record = {
                    "id": case["id"], "arm": arm,
                    "request_file": "requests/" + name,
                    "response_file": "responses/" + name,
                    "response_id": answer.get("id"),
                    "status": answer.get("status"),
                    "resolved_model": answer.get("model"),
                    "web_search_calls": len(calls),
                    "web_search_actions": [x.get("action", {}) for x in calls],
                    "output_characters": len(output_text(answer)),
                    "duration_seconds": elapsed,
                    "captured_utc": now(),
                    "usage": answer.get("usage"),
                }
                manifest["runs"].append(record)
                write_json(out / "manifest.json", manifest)
                print(case["id"], arm, "model=", record["resolved_model"],
                      "search_calls=", len(calls), "chars=", record["output_characters"], flush=True)
                if answer.get("status") != "completed" or not output_text(answer):
                    raise RuntimeError("Incomplete/empty model output: " + name)
                if arm == "with_web" and not calls:
                    raise RuntimeError("Search arm did not call web_search: " + name)
                if arm == "no_web" and calls:
                    raise RuntimeError("No-web arm unexpectedly used search: " + name)
                pair_models.append(record["resolved_model"])
                time.sleep(1)
            if not all(pair_models) or pair_models[0] != pair_models[1]:
                raise RuntimeError("Model version differs across arms for " + case["id"])
        manifest["state"] = "captured_pending_human_review"
        manifest["completed_utc"] = now()
        write_json(out / "manifest.json", manifest)
        with (out / "reviews.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for case in selected:
                for arm in ("no_web", "with_web"):
                    writer.writerow({
                        "id": case["id"], "arm": arm, "status": "not_reviewed",
                        "reviewed_by": "", "reviewed_utc": "",
                        "supporting_primary_url": case["primary_url"],
                        "exact_passage_or_location": "", "citation_check": "not_checked",
                        "notes": "",
                    })
        print("Raw responses captured. Human review REQUIRED before any conclusions:", out)
    except Exception as exc:
        manifest["state"] = "failed_or_partial_no_valid_conclusions"
        manifest["error_type"] = type(exc).__name__
        manifest["error"] = str(exc)
        manifest["stopped_utc"] = now()
        write_json(out / "manifest.json", manifest)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="gpt-4.1-mini")
    parser.add_argument("--max-cases", type=int, default=12)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--acknowledge-api-costs", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.max_cases <= 12:
        parser.error("--max-cases must be between 1 and 12")
    try:
        run(args.model, args.max_cases, args.dry_run, args.acknowledge_api_costs)
    except (ValueError, RuntimeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
