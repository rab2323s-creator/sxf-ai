#!/usr/bin/env python3
"""Audit SXF provider-published Standard token prices against third-party feeds.

Discovery only. This script NEVER edits the official SXF model catalog. An
OpenRouter price applies to OpenRouter; a LiteLLM price is third-party
metadata. Differences request human review of the provider's official page.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data/model-pricing.json"
OUTPUT = ROOT / "data/pricing-source-audit.json"
OPENROUTER = "https://openrouter.ai/api/v1/models"
LITELLM = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
MAX_BODY_BYTES = 18 * 1024 * 1024

# Exact provider/model identity only. No substring or fuzzy price matches.
OPENROUTER_PREFIX = {
    "OpenAI": "openai", "Anthropic": "anthropic", "Google": "google",
    "xAI": "x-ai", "DeepSeek": "deepseek", "Mistral AI": "mistralai",
    "Cohere": "cohere", "Meta": "meta-llama",
}
LITELLM_PROVIDER = {
    "OpenAI": {"openai"}, "Anthropic": {"anthropic"},
    "Google": {"gemini"}, "xAI": {"xai"},
    "DeepSeek": {"deepseek"}, "Mistral AI": {"mistral"},
    "Cohere": {"cohere"},
}


def money(value):
    """Parse nonnegative finite decimal amounts; never silently coerce."""
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return result if result.is_finite() and result >= 0 else None


def fetch_json(url, token=None):
    headers = {"User-Agent": "SXF-AI-Pricing-Audit/1.0", "Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(url, headers=headers)
    with urlopen(req, timeout=25) as reply:
        data = reply.read(MAX_BODY_BYTES + 1)
        if len(data) > MAX_BODY_BYTES:
            raise ValueError("Upstream response exceeded maximum size")
        return json.loads(data)


def active_price(model, day):
    if model.get("pricing_status") != "official-paid":
        return None
    if model.get("pricing_basis", {}).get("meter") != "tokens":
        return None
    # Tiered rates cannot be compared with a simple per-token listing.
    if model.get("pricing", {}).get("tiered"):
        return None
    periods = model.get("pricing", {}).get("standard", [])
    matches = [p for p in periods if p.get("start", "9999") <= day and
               (p.get("end") is None or day <= p["end"])]
    if len(matches) != 1:
        return None
    p = matches[0]
    amounts = {"input": money(p.get("input")), "output": money(p.get("output"))}
    return amounts if all(v is not None for v in amounts.values()) else None


def comparable_observation(current, observed):
    # No tolerance for meaningful differences; $0.000001 / 1m tokens
    # merely absorbs conversion precision in provider/third-party datasets.
    delta = Decimal("0.000001")
    return ("matches" if all(abs(current[k] - observed[k]) <= delta
                             for k in ("input", "output")) else "review_difference")


def compare_catalog(catalog, router, litellm, day, errors=None):
    errors = errors or {}
    router_models = {}
    if isinstance(router, dict) and isinstance(router.get("data"), list):
        router_models = {m.get("id"): m for m in router["data"]
                         if isinstance(m, dict) and isinstance(m.get("id"), str)}
    third_models = litellm if isinstance(litellm, dict) else {}
    report = []
    for model in catalog.get("models", []):
        model_id = model.get("model_id", "")
        provider = model.get("provider", "")
        base = active_price(model, day)
        item = {
            "model_id": model_id, "model": model.get("model"), "provider": provider,
            "official_status": model.get("pricing_status"),
            "official_verified_at": model.get("provenance", {}).get("verified_at"),
            "official_pricing_url": model.get("provenance", {}).get("evidence", {}).get("pricing"),
            "scope": "Provider-published Standard API",
            "official_usd_per_million_tokens": (
                {k: str(v) for k, v in base.items()} if base is not None else None
            ),
            "observations": [],
        }
        if base is None:
            item["audit_status"] = "not_comparable"
            report.append(item)
            continue
        source_ids = OPENROUTER_PREFIX.get(provider)
        if source_ids and router is not None:
            entry = router_models.get(source_ids + "/" + model_id)
            p = entry.get("pricing", {}) if isinstance(entry, dict) else {}
            inp, out = money(p.get("prompt")), money(p.get("completion"))
            if inp is not None and out is not None:
                rates = {"input": inp * 1_000_000, "output": out * 1_000_000}
                item["observations"].append({
                    "source": "OpenRouter", "source_type": "third_party_platform_price",
                    "url": OPENROUTER, "model_key": entry["id"],
                    "usd_per_million_tokens": {k: str(v) for k, v in rates.items()},
                    "comparison": comparable_observation(base, rates),
                })
        allowed = LITELLM_PROVIDER.get(provider, set())
        if allowed and litellm is not None:
            # An unprefixed key is eligible ONLY if litellm_provider matches
            # the exact expected vendor; a prefixed key must also agree.
            for key in (model_id, next(iter(sorted(allowed))) + "/" + model_id):
                entry = third_models.get(key)
                if not isinstance(entry, dict) or entry.get("litellm_provider") not in allowed:
                    continue
                inp = money(entry.get("input_cost_per_token"))
                out = money(entry.get("output_cost_per_token"))
                if inp is None or out is None:
                    continue
                rates = {"input": inp * 1_000_000, "output": out * 1_000_000}
                item["observations"].append({
                    "source": "LiteLLM", "source_type": "third_party_registry",
                    "url": LITELLM, "model_key": key,
                    "source_link": entry.get("source"),
                    "usd_per_million_tokens": {k: str(v) for k, v in rates.items()},
                    "comparison": comparable_observation(base, rates),
                })
                break
        if any(x["comparison"] == "review_difference" for x in item["observations"]):
            item["audit_status"] = "review_difference"
        elif item["observations"]:
            item["audit_status"] = "cross_checked_third_party"
        else:
            item["audit_status"] = "not_found_in_third_party_feeds"
        report.append(item)

    counts = {}
    for item in report:
        counts[item["audit_status"]] = counts.get(item["audit_status"], 0) + 1
    return {
        "schema_version": "1.0",
        "disclaimer": ("Third-party API observations are NOT official direct-provider "
                       "prices. Differences do not automatically imply an SXF error. "
                       "Official pricing requires confirmation at primary sources."),
        "as_of_utc_date": day,
        "catalog_source_verified": catalog.get("source_verified"),
        "sources": [
            {"name": "OpenRouter", "url": OPENROUTER, "available": router is not None,
             "error": errors.get("OpenRouter")},
            {"name": "LiteLLM", "url": LITELLM, "available": litellm is not None,
             "error": errors.get("LiteLLM")},
        ],
        "summary": {"models": len(report), "statuses": counts},
        "models": report,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--router-fixture", type=Path)
    parser.add_argument("--litellm-fixture", type=Path)
    args = parser.parse_args()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    errors = {}
    feeds = {}
    for name, url, fixture, key in [
        ("OpenRouter", OPENROUTER, args.router_fixture, os.environ.get("OPENROUTER_API_KEY")),
        ("LiteLLM", LITELLM, args.litellm_fixture, None),
    ]:
        try:
            feeds[name] = (json.loads(fixture.read_text(encoding="utf-8")) if fixture
                           else fetch_json(url, key))
        except (HTTPError, URLError, OSError, ValueError) as exc:
            feeds[name] = None
            errors[name] = type(exc).__name__ + ": " + str(exc)[:180]
            print(name + " unavailable: " + errors[name], file=sys.stderr)
    if all(value is None for value in feeds.values()):
        print("No pricing feeds were retrieved; existing audit left untouched.", file=sys.stderr)
        return 1
    now = datetime.now(timezone.utc)
    report = compare_catalog(catalog, feeds["OpenRouter"], feeds["LiteLLM"],
                             now.date().isoformat(), errors)
    report["checked_at_utc"] = now.isoformat(timespec="seconds")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print("Pricing audit:", report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
