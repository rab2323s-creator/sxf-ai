#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_PATH = ROOT / "data" / "archive.json"
PRICING_PATH = ROOT / "data" / "model-pricing.json"
HISTORY_PATH = ROOT / "data" / "model-history.json"
CONFIG_PATH = ROOT / "data" / "ai-enrichment-config.json"
OUT_PATH = ROOT / "data" / "ai-enrichment-candidates.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_date(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value):
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def normalized(value):
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def signal_haystack(signal):
    return normalized(" ".join([
        signal.get("title", ""),
        signal.get("summary", ""),
        " ".join(signal.get("tags", [])),
    ]))


def explicit_model_match(signal, model):
    haystack = signal_haystack(signal)
    candidates = [model.get("model", ""), model.get("model_id", "")]
    aliases = model.get("aliases") or []
    if isinstance(aliases, list):
        candidates.extend(aliases)
    return any(normalized(candidate) and normalized(candidate) in haystack for candidate in candidates)


def family_model_match(signal, model):
    family = normalized(model.get("family", ""))
    return bool(family and family in signal_haystack(signal))


def active_price(model, on_date):
    periods = model.get("pricing", {}).get("standard", [])
    for period in periods:
        start = period.get("start")
        end = period.get("end")
        if start and on_date >= start and (end is None or on_date <= end):
            return period
    return periods[-1] if periods else None


def history_for_model(model_id, history, limit=5):
    rows = [event for event in history.get("events", []) if event.get("model_id") == model_id]
    rows.sort(key=lambda event: event.get("sequence", 0), reverse=True)
    return rows[:limit]


def enrichment_priority(item):
    score = int(item.get("seo_quality_score", 0)) + int(item.get("signal_score", 0))
    title = item.get("title", "")
    category = item.get("category", "")
    if category == "Models":
        score += 35
    elif category in {"Research", "Open Source"}:
        score += 15
    if re.search(r"\bintroducing\b|\brelease(?:d|s)?\b|\blaunch(?:ed|es)?\b|\bpricing\b|\bavailable\b", title, re.I):
        score += 20
    if re.search(r"\bGPT[- ]?\d|\bClaude\b|\bGemini\b|\bLlama\b|\bGrok\b", title, re.I):
        score += 20
    return score


def select_candidates(archive_items, config, now):
    cutoff = now - timedelta(days=int(config["candidate_max_age_days"]))
    rows = []
    for item in archive_items:
        if not item.get("seo_eligible"):
            continue
        if item.get("category") not in set(config["allowed_categories"]):
            continue
        published = parse_date(item.get("published"))
        if published is None or published < cutoff:
            continue
        if int(item.get("seo_quality_score", 0)) < int(config["min_seo_quality_score"]):
            continue
        if int(item.get("signal_score", 0)) < int(config["min_signal_score"]):
            continue
        rows.append((enrichment_priority(item), published, item))
    rows.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [item for _score, _published, item in rows[: int(config["candidate_limit"])]]


def build_evidence_pack(item, pricing, history):
    published = parse_date(item.get("published"))
    published_date = published.date().isoformat() if published else datetime.now(timezone.utc).date().isoformat()
    matched_models = []
    source_urls = [item.get("url")]

    all_models = pricing.get("models", [])
    explicit_models = [model for model in all_models if explicit_model_match(item, model)]
    evidence_models = explicit_models or [model for model in all_models if family_model_match(item, model)]

    for model in evidence_models:
        price = active_price(model, published_date)
        provenance = model.get("provenance", {})
        evidence = provenance.get("evidence", {})
        official_sources = [url for url in model.get("official_sources", []) if url]
        source_urls.extend(official_sources)
        source_urls.extend([url for url in evidence.values() if isinstance(url, str) and url])
        matched_models.append({
            "model_id": model.get("model_id"),
            "provider": model.get("provider"),
            "family": model.get("family"),
            "model": model.get("model"),
            "context_window": model.get("context_window"),
            "max_output": model.get("max_output"),
            "knowledge_cutoff": model.get("knowledge_cutoff"),
            "reasoning": model.get("reasoning"),
            "modalities": model.get("modalities"),
            "positioning": model.get("positioning"),
            "pricing_standard": price,
            "pricing_long_context": model.get("pricing", {}).get("long_context"),
            "verified_at": provenance.get("verified_at"),
            "official_sources": official_sources,
            "history": history_for_model(model.get("model_id"), history),
        })

    evidence = {
        "signal": {
            "title": item.get("title"),
            "url": item.get("url"),
            "signal_url": item.get("signal_url"),
            "source": item.get("source"),
            "published": item.get("published"),
            "category": item.get("category"),
            "tags": item.get("tags", []),
            "summary": item.get("summary", ""),
            "signal_score": item.get("signal_score", 0),
            "seo_quality_score": item.get("seo_quality_score", 0),
            "seo_quality_factors": item.get("seo_quality_factors", []),
        },
        "models": matched_models,
        "source_urls": sorted(set(url for url in source_urls if url)),
    }
    return evidence


def proposed_structure(evidence):
    has_model = bool(evidence["models"])
    sections = [
        "intro",
        "what_changed",
        "why_it_matters",
        "key_facts",
    ]
    if has_model:
        sections += ["pricing_or_capability_impact", "before_vs_after"]
    sections += ["who_should_care", "what_to_verify", "faq", "sources"]
    return {
        "route_policy": "preserve-existing-signal-route",
        "seo_title_max_chars": 60,
        "meta_description_max_chars": 160,
        "h1_policy": "clear-descriptive-no-hype",
        "required_sections": sections,
        "fact_policy": "evidence-only",
        "unknown_policy": "use unknown or omit; never infer unsupported facts",
        "internal_link_policy": "links must come from existing SXF routes only",
    }


def main():
    config = load_json(CONFIG_PATH)
    if config.get("mode") != "dry-run":
        raise RuntimeError("Step 1 must remain in dry-run mode")
    if config.get("publish_mode") != "manual-review":
        raise RuntimeError("Step 1 must require manual review")

    now = datetime.now(timezone.utc)
    archive = load_json(ARCHIVE_PATH)
    pricing = load_json(PRICING_PATH)
    history = load_json(HISTORY_PATH)
    candidates = select_candidates(archive.get("items", []), config, now)

    rows = []
    for rank, item in enumerate(candidates, start=1):
        evidence = build_evidence_pack(item, pricing, history)
        rows.append({
            "rank": rank,
            "signal_slug": item.get("signal_slug"),
            "signal_url": item.get("signal_url"),
            "title": item.get("title"),
            "source": item.get("source"),
            "category": item.get("category"),
            "published": item.get("published"),
            "priority_score": enrichment_priority(item),
            "evidence_hash": sha256_json(evidence),
            "evidence": evidence,
            "requested_output": proposed_structure(evidence),
            "generation_status": "not-called",
            "index_decision": "unchanged",
        })

    snapshot = {
        "candidate_slugs": [row["signal_slug"] for row in rows],
        "evidence_hashes": [row["evidence_hash"] for row in rows],
        "config_version": config["version"],
    }
    payload = {
        "version": config["version"],
        "mode": config["mode"],
        "snapshot_hash": sha256_json(snapshot),
        "candidate_count": len(rows),
        "candidate_limit": config["candidate_limit"],
        "budget_guard": {
            "monthly_budget_eur": config["monthly_budget_eur"],
            "monthly_page_limit": config["monthly_page_limit"],
            "per_page_input_token_cap": config["per_page_input_token_cap"],
            "per_page_output_token_cap": config["per_page_output_token_cap"],
            "writer_model": config["writer_model"],
            "validator_model": config["validator_model"],
        },
        "candidates": rows,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"AI enrichment dry-run: {len(rows)} candidates written to {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
