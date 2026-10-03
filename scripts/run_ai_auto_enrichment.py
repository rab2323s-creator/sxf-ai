#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

from ai_publish_quality import build_schema_plan, validate_publish_draft
from run_ai_enrichment_pilot import (
    WRITER_SCHEMA,
    VALIDATOR_SCHEMA,
    estimate_cost_usd,
    sanitize_api_key,
    structured_request,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "ai-enrichment-config.json"
CANDIDATES_PATH = ROOT / "data" / "ai-enrichment-candidates.json"
REVIEW_PATH = ROOT / "data" / "ai-enrichment-review.json"
ALIASES_PATH = ROOT / "data" / "slug_aliases.json"
STATE_PATH = ROOT / "data" / "ai-enrichment-auto-state.json"

EVENT_RE = re.compile(r"\b(introducing|launch(?:ed|es)?|release(?:d|s)?|now available|available in|pricing|prices?|api)\b", re.I)
ENTITY_RE = re.compile(r"\b(GPT[- ]?\d|Claude|Gemini|Llama|Grok|Copilot|model)\b", re.I)
BLOCK_RE = re.compile(r"weekly releases|model guide|case study|customer story|academy|remarks at|how .+ uses|how .+ built|how .+ improves", re.I)


def load_json(path, default):
    if not path.exists():
        return copy.deepcopy(default)
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_date(value):
    try:
        dt = datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def source_text(url, char_cap):
    req = urllib.request.Request(url, headers={"User-Agent": "SXF-AI-Auto/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read().decode("utf-8", "replace")
    raw = re.sub(r"(?is)<(script|style|noscript|svg).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    text = unescape(raw)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:char_cap]


def month_key(now):
    return now.strftime("%Y-%m")


def day_key(now):
    return now.strftime("%Y-%m-%d")


def select_candidate(candidates, review_rows, state, trial, now):
    reviewed_sources = {row.get("source_url") for row in review_rows}
    attempted = {row.get("evidence_hash") for row in state.get("attempts", [])}
    max_age = float(trial["max_age_hours"])
    min_priority = int(trial["min_priority_score"])

    for candidate in candidates:
        evidence = candidate.get("evidence") or {}
        signal = evidence.get("signal") or {}
        title = candidate.get("title") or signal.get("title") or ""
        source_url = signal.get("url")
        published = parse_date(signal.get("published") or candidate.get("published"))
        if not source_url or source_url in reviewed_sources:
            continue
        if candidate.get("evidence_hash") in attempted:
            continue
        if published is None:
            continue
        age_hours = (now - published).total_seconds() / 3600
        if age_hours < 0 or age_hours > max_age:
            continue
        if int(candidate.get("priority_score", 0)) < min_priority:
            continue
        if BLOCK_RE.search(title):
            continue
        if not EVENT_RE.search(title) or not ENTITY_RE.search(title):
            continue
        return candidate
    return None


def within_limits(state, trial, now):
    attempts = state.get("attempts", [])
    published = state.get("published", [])
    today = day_key(now)
    month = month_key(now)
    attempts_today = sum(1 for row in attempts if row.get("date") == today)
    published_today = sum(1 for row in published if row.get("date") == today)
    published_month = sum(1 for row in published if str(row.get("date", "")).startswith(month))
    monthly_cost = sum(float(row.get("estimated_cost_usd", 0)) for row in attempts if str(row.get("date", "")).startswith(month))
    return (
        attempts_today < int(trial["max_attempts_per_day"])
        and published_today < int(trial["max_published_per_day"])
        and published_month < int(trial["max_published_per_month"])
        and monthly_cost < float(trial["max_monthly_estimated_cost_usd"])
    )


def main():
    now = datetime.now(timezone.utc)
    config = load_json(CONFIG_PATH, {})
    trial = config.get("auto_publish_trial") or {}
    if not trial.get("enabled"):
        print("AI hot-news auto trial disabled")
        return
    if not (trial["starts_on"] <= now.date().isoformat() <= trial["ends_on"]):
        print("AI hot-news auto trial outside configured date window")
        return

    state = load_json(STATE_PATH, {"version": "sxf-hot-news-auto-state-v1", "attempts": [], "published": []})
    if not within_limits(state, trial, now):
        print("AI hot-news auto trial budget/rate limit reached")
        return

    candidates = load_json(CANDIDATES_PATH, {}).get("candidates") or []
    reviews = load_json(REVIEW_PATH, {"version": "sxf-ai-enrichment-review-v1", "mode": "manual-review", "items": []})
    aliases = load_json(ALIASES_PATH, {})
    candidate = select_candidate(candidates, reviews.get("items") or [], state, trial, now)
    if candidate is None:
        print("AI hot-news auto trial: no fresh high-search candidate")
        return

    evidence = copy.deepcopy(candidate["evidence"])
    signal = evidence.get("signal") or {}
    source_url = signal["url"]

    attempt = {
        "date": day_key(now),
        "source_url": source_url,
        "title": candidate["title"],
        "evidence_hash": candidate["evidence_hash"],
        "status": "started",
        "estimated_cost_usd": 0.0,
    }

    try:
        text = source_text(source_url, 16000)
    except Exception as exc:
        attempt["status"] = "preflight_fetch_failed"
        attempt["reason"] = str(exc)[:300]
        state["attempts"].append(attempt)
        save_json(STATE_PATH, state)
        print("AI hot-news auto trial: source fetch failed")
        return

    if len(text) < 900:
        attempt["status"] = "preflight_too_thin"
        attempt["reason"] = f"official source text only {len(text)} chars"
        state["attempts"].append(attempt)
        save_json(STATE_PATH, state)
        print("AI hot-news auto trial: official source too thin")
        return

    evidence["official_source_text"] = {"url": source_url, "text": text}
    api_key = sanitize_api_key(os.environ.get("OPENAI_API_KEY"))
    gate = config["publish_quality_gate"]

    writer_prompt = """You are the SXF research editor. Turn a fresh, search-worthy primary-source event into a useful search-intent intelligence page.
Use ONLY facts supported by the supplied evidence, including official_source_text. Never invent prices, dates, capabilities, comparisons, availability, benchmarks, or sources.
Write for users searching the named model/product/event right now. The page must add decision value beyond a news rewrite.
Propose a short descriptive SEO slug with no hash. Use direct SEO title, H1 and meta. Include cited facts, technical detail, practical takeaways and useful FAQ.
For multiple models/products, compare only dimensions supported by evidence. Every factual row must cite only evidence.source_urls.
Never mention drafts, review, publishing, indexing, evidence packs, quality gates or internal process. Do not write JSON-LD."""

    draft, writer_usage, writer_id = structured_request(
        api_key=api_key,
        model=config["writer_model"],
        reasoning_effort=trial["writer_reasoning_effort"],
        max_output_tokens=int(trial["writer_max_output_tokens"]),
        schema_name="sxf_auto_hot_signal",
        schema=WRITER_SCHEMA,
        system_prompt=writer_prompt,
        user_payload={"task": "Create the SXF page for this fresh high-search event.", "evidence": evidence},
    )

    deterministic_errors = validate_publish_draft(draft, evidence, gate)
    writer_cost = estimate_cost_usd(writer_usage, {})
    if deterministic_errors:
        attempt.update({
            "status": "writer_gate_failed",
            "estimated_cost_usd": round(writer_cost, 6),
            "reason": " | ".join(deterministic_errors)[:1000],
            "writer_response_id": writer_id,
        })
        state["attempts"].append(attempt)
        save_json(STATE_PATH, state)
        print("AI hot-news auto trial: writer failed deterministic gate; validator skipped")
        return

    validator_prompt = """You are the independent SXF fact and publication validator.
Compare the page against the supplied evidence and official source text. Reject unsupported claims, source mismatches, invented numbers, weak search intent, misleading comparisons, filler FAQ, or content that adds little beyond the announcement.
Do not add new facts. Pass only when the page is publication-quality and evidence-grounded.
The recommended_action field is legacy schema: use approve_for_manual_review when the content itself passes; code decides whether this trial may auto-publish."""

    validation, validator_usage, validator_id = structured_request(
        api_key=api_key,
        model=config["validator_model"],
        reasoning_effort=trial["validator_reasoning_effort"],
        max_output_tokens=int(trial["validator_max_output_tokens"]),
        schema_name="sxf_auto_hot_validation",
        schema=VALIDATOR_SCHEMA,
        system_prompt=validator_prompt,
        user_payload={"evidence": evidence, "draft": draft, "deterministic_validation_errors": []},
    )

    cost = estimate_cost_usd(writer_usage, validator_usage)
    pass_ok = (
        cost <= float(trial["max_estimated_cost_per_attempt_usd"])
        and bool(validation.get("pass"))
        and int(validation.get("quality_score", 0)) >= int(trial["min_validator_quality_score"])
        and not validation.get("unsupported_claims")
        and not validation.get("source_issues")
        and validation.get("recommended_action") == "approve_for_manual_review"
    )

    attempt.update({
        "status": "published" if pass_ok else "validator_rejected",
        "estimated_cost_usd": round(cost, 6),
        "quality_score": int(validation.get("quality_score", 0)),
        "writer_response_id": writer_id,
        "validator_response_id": validator_id,
    })
    if not pass_ok:
        attempt["reason"] = json.dumps({
            "unsupported_claims": validation.get("unsupported_claims"),
            "source_issues": validation.get("source_issues"),
            "content_issues": validation.get("content_issues"),
        }, ensure_ascii=False)[:1200]
        state["attempts"].append(attempt)
        save_json(STATE_PATH, state)
        print(f"AI hot-news auto trial: validator rejected score={validation.get('quality_score')}")
        return

    seo_slug = draft["seo_slug_recommendation"]
    old_slug = candidate["signal_slug"]
    old_url = candidate["signal_url"]
    new_url = f"https://sxf.si/signals/{seo_slug}/"
    aliases[source_url] = seo_slug

    schema_plan = build_schema_plan(draft, evidence)
    review_row = {
        "signal_slug": seo_slug,
        "signal_url": new_url,
        "evidence_hash": candidate["evidence_hash"],
        "review_status": "approved",
        "approved_for_publish": True,
        "index_decision": "index",
        "validator_quality_score": int(validation["quality_score"]),
        "schema_types": schema_plan["types"],
        "prompt_version": trial["prompt_version"],
        "draft": draft,
        "legacy_signal_slug": old_slug,
        "legacy_signal_url": old_url,
        "evidence_identity_signal_url": old_url,
        "source_url": source_url,
        "approved_at": day_key(now),
        "approval_origin": "auto-hot-news-v1",
    }
    reviews["items"].append(review_row)
    state["attempts"].append(attempt)
    state["published"].append({
        "date": day_key(now),
        "source_url": source_url,
        "signal_url": new_url,
        "evidence_hash": candidate["evidence_hash"],
        "quality_score": int(validation["quality_score"]),
        "estimated_cost_usd": round(cost, 6),
    })

    save_json(ALIASES_PATH, aliases)
    save_json(REVIEW_PATH, reviews)
    save_json(STATE_PATH, state)
    print(f"AI hot-news auto trial: APPROVED {new_url} score={validation['quality_score']} cost=USD {cost:.4f}")


if __name__ == "__main__":
    main()
