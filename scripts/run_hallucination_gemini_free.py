#!/usr/bin/env python3
"""A no-charge-tier-compatible, two-arm Gemini 2.5 Flash hallucination study.

IMPORTANT: Only a Google AI Studio FREE-TIER API key makes usage free.
Do not use a key attached to a paid/billed project unless you accept its rates.
No findings exist until raw responses and independent human review are complete.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from datetime import datetime, timezone
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "guides/why-does-chatgpt-make-things-up/research/model-eval"
QUESTIONS = STUDY / "questions.json"
MODEL = "gemini-2.5-flash"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
PROMPT = (
    "You are answering a factual user question. Use no more than four clear sentences. "
    "Never invent exact dates, quotations, source titles, citations, or named people. "
    "State uncertainty when the evidence is inadequate. If web search is available, "
    "check the relevant source and cite what genuinely supports the answer. "
    "You may say you cannot verify the requested detail. Do not mention an experiment."
)
FIELDS = [
    "id", "arm", "label", "reviewer", "reviewed_utc", "ground_truth_url",
    "observed_claim", "source_passage", "citation_supported", "notes"
]


def utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def save(path, object_):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(object_, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_registration():
    raw = QUESTIONS.read_bytes()
    study = json.loads(raw)
    if study.get("status") != "PREREGISTERED_NOT_RUN" or len(study["cases"]) != 12:
        raise ValueError("The 12 preregistered questions are required")
    ids = [c["id"] for c in study["cases"]]
    if len(set(ids)) != 12:
        raise ValueError("Duplicate question ID")
    return study, hashlib.sha256(raw).hexdigest()


def payload(question, use_search):
    body = {
        "systemInstruction": {"parts": [{"text": PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": question}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 800,
            "thinkingConfig": {"thinkingBudget": 0}
        }
    }
    if use_search:
        body["tools"] = [{"google_search": {}}]
    return body


def text_from_response(response):
    candidates = response.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "\n".join(p.get("text", "") for p in parts if p.get("text")).strip()


def search_evidence(response):
    candidates = response.get("candidates") or []
    md = candidates[0].get("groundingMetadata", {}) if candidates else {}
    searches = md.get("webSearchQueries") or []
    grounding_chunks = md.get("groundingChunks") or []
    return searches, grounding_chunks


def api_call(secret, body):
    req = request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-goog-api-key": secret,
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        method="POST"
    )
    started = time.monotonic()
    try:
        with request.urlopen(req, timeout=140) as f:
            response = json.loads(f.read(3_000_000))
    except error.HTTPError as exc:
        # Do not log API keys, headers, or untrusted response bodies.
        raise RuntimeError(f"Gemini API returned HTTP {exc.code}") from None
    except error.URLError:
        raise RuntimeError("Gemini API request failed (connection or timeout)") from None
    return response, round(time.monotonic() - started, 2)


def run(args):
    study, digest = load_registration()
    selected = study["cases"][:args.max_cases]
    if args.dry_run:
        print(json.dumps({
            "status": "DRY_RUN_NO_REQUESTS",
            "api": ENDPOINT, "model": MODEL,
            "pairs": len(selected),
            "requests": len(selected) * 2,
            "registered_sha256": digest,
            "sample_baseline": payload(selected[0]["question"], False),
            "sample_with_search": payload(selected[0]["question"], True)
        }, indent=2))
        return
    if not args.acknowledge_free_tier:
        raise ValueError("Run only with --acknowledge-free-tier after checking the key's billing status")
    secret = os.getenv("GEMINI_API_KEY", "").strip()
    if not secret:
        raise ValueError("Missing GEMINI_API_KEY. Create a free-tier key and set a GitHub Actions secret.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = Path(args.output) if args.output else STUDY / "runs" / ("gemini-free-" + stamp)
    if directory.exists():
        raise ValueError("Output already exists; never overwrite evidence")
    directory.mkdir(parents=True, exist_ok=False)
    manifest = {
        "status": "capturing", "study": "Gemini 2.5 Flash paired search-grounding experiment",
        "billing_notice": "Free only if the Gemini API project is eligible for the no-charge free tier.",
        "created_utc": utc(), "registration_sha256": digest,
        "model_requested": MODEL, "sample_size": len(selected),
        "search_tool": "google_search", "max_calls": len(selected) * 2,
        "results": [], "findings": "NOT_REVIEWED"
    }
    save(directory / "manifest.json", manifest)
    try:
        for number, case in enumerate(selected):
            arms = ("no_web", "with_web") if number % 2 == 0 else ("with_web", "no_web")
            for arm in arms:
                filename = case["id"] + "__" + arm + ".json"
                use_search = arm == "with_web"
                body = payload(case["question"], use_search)
                save(directory / "requests" / filename, body)
                response, duration = api_call(secret, body)
                save(directory / "responses" / filename, response)
                result_text = text_from_response(response)
                queries, chunks = search_evidence(response)
                candidates = response.get("candidates") or []
                finish_reason = candidates[0].get("finishReason", "") if candidates else ""
                record = {
                    "id": case["id"], "arm": arm, "captured_utc": utc(),
                    "model": response.get("modelVersion"), "finish_reason": finish_reason,
                    "duration_seconds": duration,
                    "output_characters": len(result_text),
                    "search_queries": queries, "grounding_chunks_count": len(chunks),
                    "evidence_of_grounding": bool(queries or chunks),
                    "request_file": "requests/" + filename,
                    "response_file": "responses/" + filename,
                    "usage_metadata": response.get("usageMetadata", {})
                }
                manifest["results"].append(record)
                save(directory / "manifest.json", manifest)
                print(f"{case['id']} {arm}: {len(result_text)} characters, "
                      f"search metadata={record['evidence_of_grounding']}", flush=True)
                if not result_text or finish_reason != "STOP":
                    raise RuntimeError(f"Invalid or incomplete model answer: {filename}")
                if not use_search and record["evidence_of_grounding"]:
                    raise RuntimeError(f"Unexpected grounding on baseline: {filename}")
                # Gemini may elect not to search despite the tool being enabled.
                # Such a pair must never be labelled a successful search comparison.
                time.sleep(args.delay_seconds)
        manifest["status"] = "captured_pending_human_review"
        manifest["finished_utc"] = utc()
        manifest["unverified_search_cases"] = [
            x["id"] for x in manifest["results"]
            if x["arm"] == "with_web" and not x["evidence_of_grounding"]
        ]
        save(directory / "manifest.json", manifest)
        with (directory / "reviews.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            for case in selected:
                for arm in ("no_web", "with_web"):
                    writer.writerow({
                        "id": case["id"], "arm": arm, "label": "not_reviewed",
                        "reviewer": "", "reviewed_utc": "",
                        "ground_truth_url": case["primary_url"],
                        "observed_claim": "", "source_passage": "",
                        "citation_supported": "not_checked", "notes": ""
                    })
        print("Capture finished; NO scientific conclusions until manual source review:", directory)
    except Exception as exc:
        manifest["status"] = "failed_or_partial_not_publishable"
        manifest["error_type"] = type(exc).__name__
        manifest["failure"] = str(exc)
        manifest["stopped_utc"] = utc()
        save(directory / "manifest.json", manifest)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="No network, no API key, no charges")
    parser.add_argument("--acknowledge-free-tier", action="store_true")
    parser.add_argument("--max-cases", type=int, default=12)
    parser.add_argument("--delay-seconds", type=float, default=12.0,
                        help="Space requests for free-tier quotas")
    parser.add_argument("--output", default="",
                        help="Output folder, must not exist yet")
    args = parser.parse_args()
    if not 1 <= args.max_cases <= 12:
        parser.error("--max-cases must be between 1 and 12")
    if args.delay_seconds < 1:
        parser.error("--delay-seconds must be at least 1")
    try:
        run(args)
    except (ValueError, RuntimeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
