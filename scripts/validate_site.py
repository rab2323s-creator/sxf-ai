#!/usr/bin/env python3
from __future__ import annotations
import json
import re
import sys
import xml.etree.ElementTree as ET
import copy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://sxf.si"
AI_ENRICHMENT_CONFIG_PATH = ROOT / "data" / "ai-enrichment-config.json"
AI_ENRICHMENT_CANDIDATES_PATH = ROOT / "data" / "ai-enrichment-candidates.json"

EXPECTED_PRIMARY_NAV = [
    "/models/",
    "/compare/",
    "/tools/",
    "/research/",
    "/open-source/",
    "/guides/",
    "/superintelligence/",
    "/brief/",
    "/about/",
]

SHELL_PAGES = [
    ROOT / "index.html",
    ROOT / "about" / "index.html",
    ROOT / "models" / "index.html",
    ROOT / "models" / "pricing" / "index.html",
    ROOT / "tools" / "index.html",
    ROOT / "tools" / "ai-model-cost-calculator" / "index.html",
    ROOT / "research" / "index.html",
    ROOT / "open-source" / "index.html",
    ROOT / "guides" / "ai-agent-security" / "index.html",
    ROOT / "guides" / "how-to-build-ai-super-agent" / "index.html",
    ROOT / "guides" / "will-ai-take-over-the-world" / "index.html",
    ROOT / "guides" / "what-is-agentic-ai" / "index.html",
    ROOT / "guides" / "github-copilot-alternatives" / "index.html",
    ROOT / "guides" / "prompt-injection" / "index.html",
    ROOT / "guides" / "index.html",
    ROOT / "compare" / "index.html",
    ROOT / "superintelligence" / "index.html",
]

def fail(message):
    print(f"VALIDATION ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)

def local_path(url):
    path = urlparse(url).path
    if path == "/":
        return ROOT / "index.html"
    if path.endswith("/"):
        return ROOT / path.lstrip("/") / "index.html"
    return ROOT / path.lstrip("/")

def validate_jsonld(path, text):
    blocks = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.I | re.S)
    for raw in blocks:
        try:
            json.loads(raw)
        except Exception as exc:
            fail(f"{path}: invalid JSON-LD: {exc}")

def validate_html(path):
    text = path.read_text(encoding="utf-8")
    if path.name == "404.html":
        if "noindex" not in text.lower():
            fail("404.html must be noindex")
        return
    if not re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', text, re.I):
        fail(f"{path}: missing canonical")
    if "<main" not in text.lower():
        fail(f"{path}: missing main landmark")
    validate_jsonld(path, text)
    for href in re.findall(r'href=["\']([^"\']+)["\']', text, re.I):
        if href.startswith(("#","mailto:","tel:","javascript:")):
            continue
        if href.startswith(("http://","https://")):
            if not href.startswith(BASE):
                continue
            target = local_path(href)
        else:
            clean = href.split("#",1)[0].split("?",1)[0]
            if not clean:
                continue
            target = local_path(BASE + clean) if clean.startswith("/") else (path.parent / clean).resolve()
        if target.suffix in {".css",".js",".svg",".json",".webmanifest"}:
            if not target.exists():
                fail(f"{path}: missing internal asset {href}")
        elif href.endswith("/") or target.suffix == ".html":
            if not target.exists():
                fail(f"{path}: broken internal link {href}")

def extract_nav_hrefs(text):
    match = re.search(r'<nav[^>]+class=["\'][^"\']*top-nav[^"\']*["\'][^>]*>(.*?)</nav>', text, re.I | re.S)
    if not match:
        return []
    return re.findall(r'href=["\']([^"\']+)["\']', match.group(1), re.I)


def validate_site_shell():
    for path in SHELL_PAGES:
        if not path.exists():
            fail(f"site shell page missing: {path}")

        text = path.read_text(encoding="utf-8")
        nav_hrefs = extract_nav_hrefs(text)
        if nav_hrefs != EXPECTED_PRIMARY_NAV:
            fail(f"{path}: primary navigation drift: {nav_hrefs}")

        if text.count('<header class="site-header">') != 1:
            fail(f"{path}: expected exactly one site header")
        if text.count('<footer class="footer shell">') != 1:
            fail(f"{path}: expected exactly one site footer")
        if 'class="footer-main"' not in text:
            fail(f"{path}: premium footer missing")
        if "/compare/" not in text:
            fail(f"{path}: Compare link missing from shared shell")


def validate_section_counts(news):
    expected = {
        category: sum(1 for item in news["items"] if item.get("category") == category)
        for category in ("Models", "Tools", "Research", "Open Source")
    }
    paths = {
        "Models": ROOT / "models" / "index.html",
        "Tools": ROOT / "tools" / "index.html",
        "Research": ROOT / "research" / "index.html",
        "Open Source": ROOT / "open-source" / "index.html",
    }

    for category, path in paths.items():
        text = path.read_text(encoding="utf-8")
        match = re.search(r'<strong id=["\']sectionCount["\']>(\d+)</strong>', text, re.I)
        if not match:
            fail(f"{path}: missing sectionCount")
        actual = int(match.group(1))
        if actual != expected[category]:
            fail(f"{path}: sectionCount {actual} != {expected[category]} current {category} items")


def validate_model_history():
    from model_history import (
        build_initial_history,
        sync_history,
        validate_history_against_catalog,
        validate_history_structure,
    )

    catalog = json.loads((ROOT / "data" / "model-pricing.json").read_text(encoding="utf-8"))
    path = ROOT / "data" / "model-history.json"
    if not path.exists():
        fail("model-history.json is missing")
    history = json.loads(path.read_text(encoding="utf-8"))

    try:
        validate_history_against_catalog(catalog, history)
    except RuntimeError as exc:
        fail(f"model history invalid: {exc}")

    initial_event_count = sum(
        1 for event in history["events"]
        if event.get("type") in {"baseline", "model_added"}
    )
    if initial_event_count != len(catalog["models"]):
        fail(
            f"model history initial-event count {initial_event_count} "
            f"!= {len(catalog['models'])} catalog models"
        )

    # Regression: factual changes require a newer verified_at.
    stale_catalog = copy.deepcopy(catalog)
    stale_catalog["models"][0]["context_window"] += 1
    try:
        sync_history(stale_catalog, history)
    except RuntimeError as exc:
        if "require a newer provenance verified_at" not in str(exc):
            fail(f"model history stale-verification regression raised wrong error: {exc}")
    else:
        fail("model history accepted a factual change without a newer verification date")

    # Regression: deleting a tracked model is forbidden.
    removed_catalog = copy.deepcopy(catalog)
    removed_catalog["models"] = removed_catalog["models"][1:]
    try:
        sync_history(removed_catalog, history)
    except RuntimeError as exc:
        if "cannot be deleted" not in str(exc):
            fail(f"model history deletion regression raised wrong error: {exc}")
    else:
        fail("model history accepted deletion of a tracked model")

    # Regression: tampering with an old event must break the hash chain.
    tampered = copy.deepcopy(history)
    tampered["events"][0]["snapshot"]["context_window"] = 1
    try:
        validate_history_structure(tampered)
    except RuntimeError as exc:
        if "hash mismatch" not in str(exc):
            fail(f"model history tamper regression raised wrong error: {exc}")
    else:
        fail("model history accepted a tampered historical event")

    # Regression: a valid newer verified change creates one deterministic event.
    changed_catalog = copy.deepcopy(catalog)
    target = changed_catalog["models"][0]
    target["context_window"] += 1
    target["provenance"]["verified_at"] = "2026-09-28"
    changed_catalog["source_verified"] = "2026-09-28"
    updated, events = sync_history(changed_catalog, history)
    if len(events) != 1:
        fail(f"model history change regression created {len(events)} events instead of 1")
    event = events[0]
    if event.get("type") != "model_changed" or event.get("model_id") != target["model_id"]:
        fail("model history change regression created the wrong event")
    if [change.get("field") for change in event.get("changes", [])] != ["context_window"]:
        fail("model history change regression did not isolate the changed field")
    if event["changes"][0].get("change_type") != "context_change":
        fail("model history change regression classified the field incorrectly")
    try:
        validate_history_against_catalog(changed_catalog, updated)
    except RuntimeError as exc:
        fail(f"model history valid-change regression did not replay: {exc}")


def validate_model_pricing_catalog():
    path = ROOT / "data" / "model-pricing.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.4":
        fail(f"model-pricing.json schema_version drift: {data.get('schema_version')!r}")

    policy = data.get("verification_policy")
    if not isinstance(policy, dict) or policy.get("standard") != "Primary-source verification":
        fail("model-pricing.json verification policy missing or invalid")

    pricing_statuses = set(data.get("pricing_statuses", []))
    expected_pricing_statuses = {
        "official-paid", "free-preview", "partner-priced", "not-published", "self-hosted"
    }
    if pricing_statuses != expected_pricing_statuses:
        fail(f"model-pricing.json pricing statuses drift: {sorted(pricing_statuses)}")

    calculator_policy = data.get("calculator_policy")
    if not isinstance(calculator_policy, dict):
        fail("model-pricing.json calculator policy missing")
    if calculator_policy.get("eligible_statuses") != ["official-paid"]:
        fail("model-pricing.json calculator eligible statuses drift")

    models = data.get("models")
    if not isinstance(models, list) or not models:
        fail("model-pricing.json must contain a non-empty models array")

    required_ids = {
        "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
        "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
        "claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5",
        "claude-haiku-4-5-20251001", "gemini-3.8-flash", "grok-4.7",
        "grok-4.6", "grok-4.3", "gemini-3.7-flash",
        "llama-4-scout", "llama-4-maverick",
    }
    ids = [model.get("model_id") for model in models]
    if len(ids) != len(set(ids)):
        fail("model-pricing.json contains duplicate model IDs")
    missing = required_ids - set(ids)
    if missing:
        fail(f"model-pricing.json missing required models: {sorted(missing)}")

    aliases = {}
    names = set()
    verified = data.get("source_verified")
    try:
        verified_date = datetime.fromisoformat(verified).date()
    except Exception:
        fail(f"model-pricing.json has invalid source_verified date: {verified!r}")

    for model in models:
        model_id = model.get("model_id")
        name = model.get("model")
        if not name or name in names:
            fail(f"model-pricing.json has missing or duplicate model name: {name!r}")
        names.add(name)

        if not model.get("provider"):
            fail(f"{model_id}: missing provider")
        if not isinstance(model.get("context_window"), int) or model["context_window"] <= 0:
            fail(f"{model_id}: invalid context_window")
        max_output = model.get("max_output")
        if max_output not in {None, "unlimited"} and (not isinstance(max_output, int) or max_output <= 0):
            fail(f"{model_id}: invalid max_output")
        if not model.get("sxf_url", "").startswith("/"):
            fail(f"{model_id}: invalid sxf_url")
        if not local_path(BASE + model["sxf_url"]).exists():
            fail(f"{model_id}: sxf_url target does not exist: {model['sxf_url']}")

        sources = model.get("official_sources")
        if not isinstance(sources, list) or not sources or any(not url.startswith("https://") for url in sources):
            fail(f"{model_id}: official_sources must contain HTTPS URLs")

        provenance = model.get("provenance")
        if not isinstance(provenance, dict):
            fail(f"{model_id}: missing provenance")
        if provenance.get("verification_method") != "manual primary-source verification":
            fail(f"{model_id}: invalid verification_method")
        model_verified = provenance.get("verified_at")
        try:
            model_verified_date = datetime.fromisoformat(model_verified).date()
        except Exception:
            fail(f"{model_id}: invalid provenance verified_at {model_verified!r}")
        if model_verified_date > verified_date:
            fail(f"{model_id}: provenance verified_at {model_verified!r} is newer than catalog source_verified {verified!r}")
        evidence = provenance.get("evidence")
        required_evidence = {
            "model_identity", "context_window", "max_output",
            "knowledge_cutoff", "reasoning", "modalities", "pricing",
        }
        if not isinstance(evidence, dict):
            fail(f"{model_id}: provenance evidence missing")
        missing_evidence = required_evidence - set(evidence)
        if missing_evidence:
            fail(f"{model_id}: missing provenance evidence: {sorted(missing_evidence)}")
        for field, url in evidence.items():
            if field in required_evidence and url not in sources:
                fail(f"{model_id}: evidence for {field} is not an official source: {url!r}")

        for alias in model.get("aliases", []):
            if alias in aliases or alias in ids:
                fail(f"{model_id}: duplicate/colliding model alias: {alias}")
            aliases[alias] = model_id

        page_template = model.get("page_template")
        allowed_page_templates = {None, "catalog-reference", "editorial-reference", "family-reference"}
        if page_template not in allowed_page_templates:
            fail(f"{model_id}: invalid page_template {page_template!r}")
        if page_template in {"catalog-reference", "editorial-reference"}:
            if not model.get("sxf_url", "").startswith("/models/"):
                fail(f"{model_id}: model reference template requires a /models/ route")

        pricing_status = model.get("pricing_status")
        if pricing_status not in expected_pricing_statuses:
            fail(f"{model_id}: invalid pricing_status {pricing_status!r}")
        calculator_eligible = model.get("calculator_eligible")
        if not isinstance(calculator_eligible, bool):
            fail(f"{model_id}: calculator_eligible must be boolean")
        expected_eligible = pricing_status == "official-paid"
        if calculator_eligible != expected_eligible:
            fail(
                f"{model_id}: calculator_eligible={calculator_eligible} "
                f"does not match pricing_status={pricing_status!r}"
            )

        schedule = model.get("pricing", {}).get("standard")
        if pricing_status == "official-paid":
            if not isinstance(schedule, list) or not schedule:
                fail(f"{model_id}: official-paid pricing requires a Standard pricing schedule")
        elif schedule:
            fail(f"{model_id}: non-official-paid pricing must not populate Standard calculator rates")
        else:
            schedule = []

        previous_end = None
        open_ended_seen = False
        covers_verified_date = False
        for index, period in enumerate(schedule):
            try:
                start = datetime.fromisoformat(period["start"]).date()
                end = datetime.fromisoformat(period["end"]).date() if period.get("end") else None
            except Exception:
                fail(f"{model_id}: invalid pricing schedule date")

            if end is not None and end < start:
                fail(f"{model_id}: pricing period ends before it starts")
            if previous_end is not None and start <= previous_end:
                fail(f"{model_id}: overlapping Standard pricing periods")
            if open_ended_seen:
                fail(f"{model_id}: pricing period appears after an open-ended period")
            if end is None:
                open_ended_seen = True
            previous_end = end

            for field in ("input", "cached_input", "output"):
                value = period.get(field)
                if not isinstance(value, (int, float)) or value < 0:
                    fail(f"{model_id}: invalid {field} price")

            if start <= verified_date and (end is None or verified_date <= end):
                covers_verified_date = True

        if pricing_status == "official-paid" and not covers_verified_date:
            fail(f"{model_id}: no Standard pricing period covers source_verified={verified}")

        long_context = model.get("pricing", {}).get("long_context")
        if long_context:
            if not isinstance(long_context.get("threshold_input_tokens"), int) or long_context["threshold_input_tokens"] <= 0:
                fail(f"{model_id}: invalid long-context threshold")
            if long_context.get("applies_to_entire_request") is not True:
                fail(f"{model_id}: long-context rule must state that it applies to the entire request")
            multipliers = long_context.get("multipliers", {})
            for field in ("input", "cached_input", "output"):
                value = multipliers.get(field)
                if not isinstance(value, (int, float)) or value <= 0:
                    fail(f"{model_id}: invalid long-context {field} multiplier")

    from update_news import (
        MODEL_REFERENCE,
        active_standard_price,
        estimate_standard_cost,
        model_has_official_paid_pricing,
    )

    if not model_has_official_paid_pricing({
        "pricing_status": "official-paid",
        "calculator_eligible": True,
        "pricing": {"standard": [{"start": "2026-01-01"}]},
    }):
        fail("official-paid calculator eligibility regression")
    if model_has_official_paid_pricing({
        "pricing_status": "not-published",
        "calculator_eligible": False,
        "pricing": {},
    }):
        fail("unpublished pricing must not be calculator-eligible")
    forbidden_variant_fields = {
        "context", "max_output", "knowledge_cutoff",
        "input_price", "cached_price", "output_price", "source",
    }
    for family in ("GPT-5.6", "GPT-6"):
        for variant in MODEL_REFERENCE[family]["variants"]:
            duplicated = forbidden_variant_fields.intersection(variant)
            if duplicated:
                fail(f"{family} variant {variant.get('model_id')}: catalog facts duplicated in MODEL_REFERENCE: {sorted(duplicated)}")

    def expect_cost(label, actual, expected):
        if abs(actual - expected) > 1e-9:
            fail(f"{label}: calculated cost {actual} != expected {expected}")

    expect_cost("GPT-6 Sol short request", estimate_standard_cost("gpt-6-sol", 100_000, 10_000)[0], 0.30)
    expect_cost("GPT-6 Sol long request", estimate_standard_cost("gpt-6-sol", 500_000, 50_000)[0], 2.75)
    expect_cost(
        "GPT-6 Sol aggregate short-context volume",
        estimate_standard_cost("gpt-6-sol", 10_000_000, 1_000_000, pricing_input_tokens=100_000)[0],
        30.0,
    )
    expect_cost("GPT-6 Astra long request", estimate_standard_cost("gpt-6-astra", 500_000, 50_000)[0], 13.75)
    expect_cost("Claude Opus 5.5 short request", estimate_standard_cost("claude-opus-5-5", 100_000, 10_000)[0], 0.60)
    expect_cost("Claude Fable 5.1 short request", estimate_standard_cost("claude-fable-5-1", 100_000, 10_000)[0], 1.50)
    expect_cost("Gemini 3.8 Flash 2026 short request", estimate_standard_cost("gemini-3.8-flash", 100_000, 10_000, on_date="2026-09-27")[0], 0.1125)
    expect_cost("Gemini 3.8 Flash 2027 short request", estimate_standard_cost("gemini-3.8-flash", 100_000, 10_000, on_date="2027-01-01")[0], 0.225)
    expect_cost("Grok 4.6 short request", estimate_standard_cost("grok-4.6", 100_000, 10_000)[0], 0.26)
    expect_cost("Grok 4.6 long request", estimate_standard_cost("grok-4.6", 500_000, 50_000)[0], 2.60)
    expect_cost("Grok 4.3 short request", estimate_standard_cost("grok-4.3", 100_000, 10_000)[0], 0.15)
    expect_cost("Gemini 3.7 Flash 2026 short request", estimate_standard_cost("gemini-3.7-flash", 100_000, 10_000, on_date="2026-10-03")[0], 0.1125)

    try:
        active_standard_price("llama-4-scout", "2026-10-03")
    except RuntimeError as exc:
        if "not calculator-eligible" not in str(exc):
            fail(f"Llama 4 Scout pricing-state regression raised wrong error: {exc}")
    else:
        fail("Llama 4 Scout must not expose synthetic Standard paid pricing")

    gemini_2026 = active_standard_price("gemini-3.8-flash", "2026-12-31")
    gemini_2027 = active_standard_price("gemini-3.8-flash", "2027-01-01")
    if (gemini_2026["input"], gemini_2026["output"]) != (0.75, 3.75):
        fail("Gemini 3.8 Flash 2026 pricing schedule drift")
    if (gemini_2027["input"], gemini_2027["output"]) != (1.5, 7.5):
        fail("Gemini 3.8 Flash 2027 pricing schedule drift")

    pricing_page = ROOT / "models" / "pricing" / "index.html"
    if not pricing_page.exists():
        fail("generated model pricing page is missing")
    pricing_html = pricing_page.read_text(encoding="utf-8")
    row_count = len(re.findall(r"data-pricing-row(?:\s|>)", pricing_html))
    if row_count != len(models):
        fail(f"model pricing table has {row_count} rows for {len(models)} catalog models")
    if "/data/model-pricing.json" not in pricing_html:
        fail("model pricing page must link the canonical JSON dataset")
    if "PRIMARY-SOURCE VERIFIED" not in pricing_html.upper():
        fail("model pricing page must disclose primary-source verification")
    if "/data/model-history.json" not in pricing_html:
        fail("model pricing page must link the model change ledger")
    if "/models/pricing/pricing.js" not in pricing_html or "/models/pricing/pricing.css" not in pricing_html:
        fail("model pricing page is missing calculator assets")

    models_page = ROOT / "models" / "index.html"
    models_html = models_page.read_text(encoding="utf-8")
    if 'data-model-explorer' not in models_html:
        fail("models hub is missing the model explorer")
    if "/models/explorer.js" not in models_html:
        fail("models hub is missing model explorer behavior")
    explorer_rows = len(re.findall(r"data-model-row(?:\s|>)", models_html))
    if explorer_rows != len(models):
        fail(f"model explorer has {explorer_rows} rows for {len(models)} catalog models")
    if "PRIMARY-SOURCE VERIFIED" not in models_html:
        fail("model explorer must disclose primary-source verification")

    rendered_models = [
        model for model in models
        if model.get("page_template") in {"catalog-reference", "editorial-reference"}
    ]
    for model in rendered_models:
        model_path = local_path(BASE + model["sxf_url"])
        if not model_path.exists():
            fail(f"{model['model_id']}: generated model reference page missing")
        model_html = model_path.read_text(encoding="utf-8")
        if "data-model-history" not in model_html or "data-what-changed" not in model_html:
            fail(f"{model['model_id']}: model page missing shared history/change contract")
        if model["provenance"]["evidence"]["model_identity"] not in model_html:
            fail(f"{model['model_id']}: model page missing official identity evidence")

    providers = sorted({model["provider"] for model in models})
    providers_index = ROOT / "providers" / "index.html"
    if not providers_index.exists():
        fail("provider directory page is missing")
    providers_html = providers_index.read_text(encoding="utf-8")
    for provider in providers:
        provider_slug = re.sub(r"[^a-z0-9]+", "-", provider.lower()).strip("-")
        provider_path = ROOT / "providers" / provider_slug / "index.html"
        if not provider_path.exists():
            fail(f"{provider}: provider page is missing")
        provider_html = provider_path.read_text(encoding="utf-8")
        provider_models = [model for model in models if model["provider"] == provider]
        for model in provider_models:
            if model["sxf_url"] not in provider_html:
                fail(f"{provider}: provider page missing model route {model['sxf_url']}")
        if f"/providers/{provider_slug}/" not in providers_html:
            fail(f"provider index missing route for {provider}")

    calculator_page = ROOT / "tools" / "ai-model-cost-calculator" / "index.html"
    calculator_html = calculator_page.read_text(encoding="utf-8")
    calculator_js = (ROOT / "tools" / "ai-model-cost-calculator" / "calculator.js").read_text(encoding="utf-8")
    if "<h1>AI Model Cost Calculator</h1>" not in calculator_html:
        fail("AI model cost calculator must use the agreed direct H1")
    if calculator_html.find('id="calculator"') < calculator_html.find("<h1>AI Model Cost Calculator</h1>"):
        fail("AI model cost calculator must appear after the H1")
    if 'fetch("/data/model-pricing.json"' not in calculator_js:
        fail("AI model cost calculator must load the canonical model-pricing.json dataset")
    if "effectiveRates" not in calculator_js or "threshold_input_tokens" not in calculator_js:
        fail("AI model cost calculator must apply catalog pricing rules")
    if "<title>AI Model Cost Calculator — GPT, Claude &amp; Gemini API Pricing | SXF / AI</title>" not in calculator_html:
        fail("AI model cost calculator title must remain unchanged")
    if 'id="requestsPerMonth"' not in calculator_html or 'id="volumeMonthly"' not in calculator_html:
        fail("AI model cost calculator is missing monthly workload mode")
    if calculator_html.count("data-workload-preset") < 7:
        fail("AI model cost calculator must expose the realistic workload presets")
    if 'id="allModelsPanel"' not in calculator_html or 'id="allModelsRows"' not in calculator_html:
        fail("AI model cost calculator is missing compare-all-models UI")
    if "renderAllModels" not in calculator_js or "lowestCostModel" not in calculator_js:
        fail("AI model cost calculator is missing compare-all-models behavior")
    if "volumeMode" not in calculator_js or "requestsPerMonth" not in calculator_js:
        fail("AI model cost calculator is missing monthly workload behavior")
    if "best model" in calculator_html.lower() or "best model" in calculator_js.lower():
        fail("AI model cost calculator must not frame token cost as model quality")
    if "/tools/ai-model-cost-calculator/" not in (ROOT / "tools" / "index.html").read_text(encoding="utf-8"):
        fail("Tools hub must link to AI Model Cost Calculator")
    if "/tools/ai-model-cost-calculator/" not in (ROOT / "models" / "pricing" / "index.html").read_text(encoding="utf-8"):
        fail("Model Pricing must link to the full AI Model Cost Calculator")

    pricing_js = (ROOT / "models" / "pricing" / "pricing.js").read_text(encoding="utf-8")
    if 'fetch("/data/model-pricing.json"' not in pricing_js:
        fail("pricing calculator must load the canonical model-pricing.json dataset")
    if "effectiveRates" not in pricing_js or "threshold_input_tokens" not in pricing_js:
        fail("pricing calculator must apply catalog pricing rules")



def validate_super_agent_internal_links():
    target = "/guides/how-to-build-ai-super-agent/"
    pages = [
        ROOT / "guides" / "ai-super-agents" / "index.html",
        ROOT / "guides" / "ai-agent-security" / "index.html",
        ROOT / "guides" / "best-ai-agents" / "index.html",
        ROOT / "topics" / "ai-agents" / "index.html",
    ]
    for path in pages:
        if target not in path.read_text(encoding="utf-8"):
            fail(f"Missing contextual internal link to super-agent build guide: {path.relative_to(ROOT)}")


def validate_agentic_ai_guide():
    path = ROOT / "guides" / "what-is-agentic-ai" / "index.html"
    if not path.exists():
        fail("Agentic AI guide is missing")
    text = path.read_text(encoding="utf-8")
    required = [
        "<h1>What Is Agentic AI?",
        "How AI Agents Actually Work",
        'id="definition"', 'id="how-it-works"', 'id="comparison"',
        'id="examples"', 'id="use-cases"', 'id="multi-agent"',
        'id="security"', 'id="evaluation"', 'id="faq"',
        'href="/guides/best-ai-agents/"',
        'href="/guides/ai-super-agents/"',
        'href="/guides/ai-agent-security/"',
        'href="/guides/how-to-build-ai-super-agent/"',
        "Agentic AI vs generative AI",
        "AI agent vs chatbot",
    ]
    for marker in required:
        if marker not in text:
            fail(f"Agentic AI guide missing required marker: {marker}")
    if text.count('data-image-slot=') != 2:
        fail("Agentic AI guide must contain exactly two research image slots")
    for image_path in [
        "/guides/what-is-agentic-ai/images/how-agentic-ai-works.webp",
        "/guides/what-is-agentic-ai/images/agentic-ai-vs-chatbot-generative-ai.webp",
    ]:
        if f'<img src="{image_path}"' not in text:
            fail(f"Agentic AI guide must render research image path: {image_path}")
    marker = '<script type="application/ld+json">'
    start = text.find(marker)
    end = text.find("</script>", start + len(marker)) if start >= 0 else -1
    if start < 0 or end < 0:
        fail("Agentic AI guide missing JSON-LD")
    try:
        data = json.loads(text[start + len(marker):end])
    except json.JSONDecodeError as exc:
        fail(f"Agentic AI guide has invalid JSON-LD: {exc}")
    graph = data.get("@graph", [])
    types = {entry.get("@type") for entry in graph if isinstance(entry, dict)}
    for schema_type in {"WebPage", "TechArticle", "ImageObject", "ItemList", "FAQPage", "BreadcrumbList"}:
        if schema_type not in types:
            fail(f"Agentic AI guide missing schema type: {schema_type}")
    image_objects = [entry for entry in graph if isinstance(entry, dict) and entry.get("@type") == "ImageObject"]
    if len(image_objects) != 2:
        fail("Agentic AI guide schema must contain exactly two ImageObject nodes")
    guides = (ROOT / "guides" / "index.html").read_text(encoding="utf-8")
    if '/guides/what-is-agentic-ai/' not in guides or "What Is Agentic AI? How AI Agents Actually Work" not in guides:
        fail("Guides index missing Agentic AI guide")
    topic = (ROOT / "topics" / "ai-agents" / "index.html").read_text(encoding="utf-8")
    if '/guides/what-is-agentic-ai/' not in topic:
        fail("AI Agents topic page missing Agentic AI guide")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for image_path in ["/guides/what-is-agentic-ai/images/how-agentic-ai-works.webp", "/guides/what-is-agentic-ai/images/agentic-ai-vs-chatbot-generative-ai.webp"]:
        if f"https://sxf.si{image_path}" not in sitemap:
            fail(f"Sitemap missing Agentic AI image: {image_path}")
    best_agents = (ROOT / "guides" / "best-ai-agents" / "index.html").read_text(encoding="utf-8")
    super_agents = (ROOT / "guides" / "ai-super-agents" / "index.html").read_text(encoding="utf-8")
    if '/guides/what-is-agentic-ai/' not in best_agents or '/guides/what-is-agentic-ai/' not in super_agents:
        fail("Generated agent guides missing contextual links to Agentic AI guide")


def validate_ai_takeover_guide():
    path = ROOT / "guides" / "will-ai-take-over-the-world" / "index.html"
    if not path.exists():
        fail("AI takeover guide is missing")
    text = path.read_text(encoding="utf-8")
    required = [
        "Will AI Take Over the World?",
        "The First 24 Hours of an AI Takeover",
        'id="hook"',
        'id="requirements"',
        'id="reality-2026"',
        'id="superintelligence"',
        'id="self-improvement"',
        'id="controls"',
        'id="likelihood"',
        'href="/superintelligence/"',
        'href="/guides/ai-super-agents/"',
        'href="/guides/ai-agent-security/"',
        'href="/guides/how-to-build-ai-super-agent/"',
        "International AI Safety Report 2026",
        "recursive self-improvement",
    ]
    for marker in required:
        if marker not in text:
            fail(f"AI takeover guide missing required marker: {marker}")
    if text.count('data-image-slot=') != 4:
        fail("AI takeover guide must reserve exactly four research image slots")
    third_image = "/guides/will-ai-take-over-the-world/images/current-ai-vs-takeover-requirements.webp"
    if f'<img src="{third_image}"' not in text:
        fail("AI takeover guide must render its third research image")
    fourth_image = "/guides/will-ai-take-over-the-world/images/ai-takeover-realistic-timeline.webp"
    if f'<img src="{fourth_image}"' not in text:
        fail("AI takeover guide must render its fourth research image")
    secondary_image = "/guides/will-ai-take-over-the-world/images/digital-ai-takeover-vs-robots.webp"
    if f'<img src="{secondary_image}"' not in text:
        fail("AI takeover guide must render its second research image")
    primary_image = "/guides/will-ai-take-over-the-world/images/ai-takeover-capability-stack.webp"
    if f'<img src="{primary_image}"' not in text:
        fail("AI takeover guide must render its primary research image")
    if 'alt="AI takeover capability stack connecting artificial intelligence to global cloud, financial, communications and infrastructure systems"' not in text:
        fail("AI takeover guide primary image must keep descriptive alt text")
    if f'<meta property="og:image" content="https://sxf.si{primary_image}"' not in text:
        fail("AI takeover guide primary image must be the Open Graph image")
    if f'<meta name="twitter:image" content="https://sxf.si{primary_image}"' not in text:
        fail("AI takeover guide primary image must be the Twitter image")
    marker = '<script type="application/ld+json">'
    start = text.find(marker)
    end = text.find("</script>", start + len(marker)) if start >= 0 else -1
    if start < 0 or end < 0:
        fail("AI takeover guide missing JSON-LD")
    try:
        data = json.loads(text[start + len(marker):end])
    except json.JSONDecodeError as exc:
        fail(f"AI takeover guide has invalid JSON-LD: {exc}")
    graph = data.get("@graph", [])
    types = {entry.get("@type") for entry in graph if isinstance(entry, dict)}
    for schema_type in {"WebPage", "TechArticle", "ImageObject", "FAQPage", "BreadcrumbList"}:
        if schema_type not in types:
            fail(f"AI takeover guide missing schema type: {schema_type}")
    image_objects = [entry for entry in graph if isinstance(entry, dict) and entry.get("@type") == "ImageObject"]
    if len(image_objects) != 4:
        fail("AI takeover guide schema must contain exactly four ImageObject nodes")
    schema_blob = json.dumps(data, ensure_ascii=False)
    for image_path in [
        "/guides/will-ai-take-over-the-world/images/ai-takeover-capability-stack.webp",
        "/guides/will-ai-take-over-the-world/images/digital-ai-takeover-vs-robots.webp",
        "/guides/will-ai-take-over-the-world/images/current-ai-vs-takeover-requirements.webp",
        "/guides/will-ai-take-over-the-world/images/ai-takeover-realistic-timeline.webp",
    ]:
        if f"https://sxf.si{image_path}" not in schema_blob:
            fail(f"AI takeover guide schema missing image: {image_path}")

    guides = (ROOT / "guides" / "index.html").read_text(encoding="utf-8")
    if '/guides/will-ai-take-over-the-world/' not in guides:
        fail("Guides index missing AI takeover guide")
    if "Will AI Take Over the World? The First 24 Hours of an AI Takeover" not in guides:
        fail("Guides index must use the full AI takeover guide title")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for image_path in [
        "/guides/will-ai-take-over-the-world/images/ai-takeover-capability-stack.webp",
        "/guides/will-ai-take-over-the-world/images/digital-ai-takeover-vs-robots.webp",
        "/guides/will-ai-take-over-the-world/images/current-ai-vs-takeover-requirements.webp",
        "/guides/will-ai-take-over-the-world/images/ai-takeover-realistic-timeline.webp",
    ]:
        if f"https://sxf.si{image_path}" not in sitemap:
            fail(f"Sitemap missing AI takeover image: {image_path}")
    if 'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"' not in sitemap:
        fail("Sitemap missing Google image namespace")
    super_page = (ROOT / "superintelligence" / "index.html").read_text(encoding="utf-8")
    if '/guides/will-ai-take-over-the-world/' not in super_page:
        fail("Superintelligence hub missing AI takeover guide")
    if "Will AI Take Over the World? The First 24 Hours of an AI Takeover" not in super_page:
        fail("Superintelligence hub must use the full AI takeover guide title")
    super_agents = (ROOT / "guides" / "ai-super-agents" / "index.html").read_text(encoding="utf-8")
    expected_anchor = '<a href="/guides/will-ai-take-over-the-world/">Will AI Take Over the World? The First 24 Hours of an AI Takeover</a>'
    if expected_anchor not in super_agents:
        fail("AI Super Agents guide must use the full keyword-rich AI takeover anchor text")


def validate_how_to_build_super_agent():
    path = ROOT / "guides" / "how-to-build-ai-super-agent" / "index.html"
    if not path.exists():
        fail("How to Build an AI Super Agent guide is missing")
    text = path.read_text(encoding="utf-8")
    required = [
        "<h1>How to Build an AI Super Agent:",
        'id="orchestrator"', 'id="tools"', 'id="memory"', 'id="verification"',
        'id="security"', 'id="example"', 'id="checklist"',
        "/guides/ai-super-agents/", "/guides/ai-agent-security/",
    ]
    for marker in required:
        if marker not in text:
            fail(f"How-to super-agent guide missing required content: {marker}")
    if text.count('data-image-slot=') != 4:
        fail("How-to super-agent guide must reserve exactly four research image slots")
    rendered_images = [
        "/guides/how-to-build-ai-super-agent/images/ai-super-agent-architecture.webp",
        "/guides/how-to-build-ai-super-agent/images/ai-agent-orchestration-patterns.webp",
        "/guides/how-to-build-ai-super-agent/images/mcp-ai-agent-architecture.webp",
        "/guides/how-to-build-ai-super-agent/images/ai-agent-guardrails-human-approval.webp",
    ]
    for image_path in rendered_images:
        if f'<img src="{image_path}"' not in text:
            fail(f"How-to super-agent guide must render uploaded research image: {image_path}")
    required_image_paths = [
        "/guides/how-to-build-ai-super-agent/images/ai-super-agent-architecture.webp",
        "/guides/how-to-build-ai-super-agent/images/ai-agent-orchestration-patterns.webp",
        "/guides/how-to-build-ai-super-agent/images/mcp-ai-agent-architecture.webp",
        "/guides/how-to-build-ai-super-agent/images/ai-agent-guardrails-human-approval.webp",
    ]
    for image_path in required_image_paths:
        if image_path not in text:
            fail(f"How-to super-agent guide missing reserved image path: {image_path}")
    marker = '<script type="application/ld+json">'
    start = text.find(marker)
    end = text.find("</script>", start + len(marker)) if start >= 0 else -1
    if start < 0 or end < 0:
        fail("How-to super-agent guide is missing JSON-LD")
    schema = json.loads(text[start + len(marker):end])
    types = {node.get("@type") for node in schema.get("@graph", [])}
    for expected in {"TechArticle", "HowTo", "FAQPage", "BreadcrumbList", "WebPage"}:
        if expected not in types:
            fail(f"How-to super-agent guide schema missing {expected}")
    guides_html = (ROOT / "guides" / "index.html").read_text(encoding="utf-8")
    if "/guides/how-to-build-ai-super-agent/" not in guides_html:
        fail("Guides index must link to How to Build an AI Super Agent")


def validate_change_intelligence_regressions():
    from update_news import (
        change_delta_items,
        change_event_items,
        change_event_summary,
        percent_delta_label,
    )

    if percent_delta_label(4, 3) != "−25%":
        fail("change intelligence pricing percentage regression")
    if percent_delta_label(1_000_000, 2_000_000) != "+100%":
        fail("change intelligence context percentage regression")

    context_change = {
        "field": "context_window",
        "change_type": "context_change",
        "before": 1_000_000,
        "after": 2_000_000,
        "source_url": "https://example.com/specs",
    }
    context_items = change_delta_items(context_change, "2026-09-28")
    if context_items != [{
        "label": "Context window",
        "before": "1M tokens",
        "after": "2M tokens",
        "delta": "+100%",
    }]:
        fail(f"change intelligence context rendering drift: {context_items}")

    pricing_change = {
        "field": "pricing",
        "change_type": "pricing_change",
        "before": {"standard": [{"start": "2026-01-01", "end": None, "input": 4, "cached_input": 0.4, "output": 20}]},
        "after": {"standard": [{"start": "2026-09-28", "end": None, "input": 3, "cached_input": 0.3, "output": 15}]},
        "source_url": "https://example.com/pricing",
    }
    pricing_items = change_delta_items(pricing_change, "2026-09-28")
    expected = {
        "Input / MTok": ("$4.00", "$3.00", "−25%"),
        "Cached input / MTok": ("$0.40", "$0.30", "−25%"),
        "Output / MTok": ("$20.00", "$15.00", "−25%"),
    }
    actual = {item["label"]: (item["before"], item["after"], item["delta"]) for item in pricing_items}
    if actual != expected:
        fail(f"change intelligence pricing rendering drift: {actual}")

    event = {
        "type": "model_changed",
        "model_id": "example-model",
        "verified_at": "2026-09-28",
        "changes": [context_change, pricing_change],
    }
    event_items = change_event_items(event)
    if len(event_items) != 4:
        fail(f"change intelligence event item count drift: {len(event_items)}")
    summary = change_event_summary(event)
    if "Context window: 1M tokens → 2M tokens (+100%)" not in summary:
        fail("change intelligence summary missing context delta")
    if "Input / MTok: $4.00 → $3.00 (−25%)" not in summary:
        fail("change intelligence summary missing price delta")


def validate_compare_contracts_and_model_histories():
    catalog = json.loads((ROOT / "data" / "model-pricing.json").read_text(encoding="utf-8"))
    history = json.loads((ROOT / "data" / "model-history.json").read_text(encoding="utf-8"))
    registry_path = ROOT / "data" / "model-comparisons.json"
    if not registry_path.exists():
        fail("model comparison registry is missing")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry.get("schema_version") != "1.0":
        fail(f"model-comparisons.json schema drift: {registry.get('schema_version')!r}")

    models = {model["model_id"]: model for model in catalog["models"]}
    comparisons = registry.get("comparisons")
    if not isinstance(comparisons, list) or not comparisons:
        fail("model-comparisons.json must contain comparisons")

    slugs = [comparison.get("slug") for comparison in comparisons]
    if len(slugs) != len(set(slugs)) or any(not slug for slug in slugs):
        fail("model comparison registry contains missing or duplicate slugs")

    indexable = [comparison for comparison in comparisons if comparison.get("indexable") is True]
    if len(indexable) < 12:
        fail("compare engine v2 must expose at least 12 curated indexable comparisons")

    from update_news import compare_pair_fact_line
    hub_path = ROOT / "compare" / "index.html"
    if not hub_path.exists():
        fail("compare hub is missing")
    hub_html = hub_path.read_text(encoding="utf-8")
    compare_js = ROOT / "compare" / "compare.js"
    if not compare_js.exists():
        fail("compare builder JavaScript is missing")
    compare_js_text = compare_js.read_text(encoding="utf-8")
    for marker_text in (
        'data-compare-builder',
        '/data/model-comparisons.json',
        '/data/model-pricing.json',
        '<script src="/compare/compare.js" defer></script>',
    ):
        if marker_text not in hub_html:
            fail(f"compare hub missing v2 marker: {marker_text}")
    if "effectiveRates" not in compare_js_text or "modelCost" not in compare_js_text:
        fail("compare builder must apply catalog pricing rules")
    if "best model" in compare_js_text.lower():
        fail("compare builder must not manufacture a universal best-model claim")

    for comparison in indexable:
        slug = comparison.get("slug")
        model_ids = comparison.get("model_ids")
        template = comparison.get("template")
        if comparison.get("type") not in {"pair", "family"}:
            fail(f"{slug}: invalid comparison type")
        if template not in {"editorial", "generic"}:
            fail(f"{slug}: invalid comparison template")
        if not isinstance(model_ids, list) or len(model_ids) < 2 or len(model_ids) > 3:
            fail(f"{slug}: invalid model_ids")
        if len(model_ids) != len(set(model_ids)):
            fail(f"{slug}: duplicate model IDs")
        unknown = [model_id for model_id in model_ids if model_id not in models]
        if unknown:
            fail(f"{slug}: unknown models {unknown}")

        path = ROOT / "compare" / slug / "index.html"
        if not path.exists():
            fail(f"missing comparison page for contract validation: {slug}")
        html = path.read_text(encoding="utf-8")
        if "data-compare-contract" not in html:
            fail(f"{slug}: missing live compare contract")
        if "data-what-changed" not in html:
            fail(f"{slug}: missing what-changed intelligence")
        ids_match = re.search(r'data-model-ids="([^"]+)"', html)
        if not ids_match or ids_match.group(1).split(",") != model_ids:
            fail(f"{slug}: compare contract model IDs drift")

        expected = compare_pair_fact_line(model_ids)
        if expected not in hub_html:
            fail(f"compare hub facts drift for {model_ids}")
        if f'/compare/{slug}/' not in hub_html:
            fail(f"compare hub missing curated route {slug}")

        for model_id in model_ids:
            model = models[model_id]
            row_pattern = (
                rf'<article class="compare-live-card"[^>]+data-compare-model="{re.escape(model_id)}"'
                rf'[^>]+data-context="{int(model["context_window"])}"'
                rf'[^>]+data-max-output="{re.escape(str(model.get("max_output")))}"'
                rf'[^>]+data-pricing-status="{re.escape(model.get("pricing_status", "not-published"))}"'
            )
            if not re.search(row_pattern, html, re.S):
                fail(f"{slug}: live facts drift for {model_id}")
            evidence = model["provenance"]["evidence"]
            if evidence["model_identity"] not in html or evidence["pricing"] not in html:
                fail(f"{slug}: official evidence links missing for {model_id}")

        if template == "generic":
            for marker_text in ("DECISION FACTORS", "No synthetic winner score", "OFFICIAL SOURCES", "RELATED MATCHUPS"):
                if marker_text not in html:
                    fail(f"{slug}: generic comparison missing decision marker {marker_text!r}")

    meta_slug = "llama-4-scout-vs-llama-4-maverick"
    meta_html = (ROOT / "compare" / meta_slug / "index.html").read_text(encoding="utf-8")
    if "Not published" not in meta_html or "Direct Standard token-cost comparison is unavailable" not in meta_html:
        fail("open-weight comparison must preserve unavailable direct pricing instead of inventing rates")

    comparison_slugs_by_model = {}
    for comparison in indexable:
        for model_id in comparison["model_ids"]:
            comparison_slugs_by_model.setdefault(model_id, []).append(comparison["slug"])

    for model_id, slugs in comparison_slugs_by_model.items():
        model = models[model_id]
        url = model.get("sxf_url", "")
        if not url.startswith("/models/") or url == "/models/pricing/":
            continue
        model_path = local_path(BASE + url)
        if not model_path.exists():
            fail(f"{model_id}: comparison backlink target missing")
        model_html = model_path.read_text(encoding="utf-8")
        if f'data-model-comparisons="{model_id}"' not in model_html:
            fail(f"{model_id}: model page missing comparison bridge")
        if not any(f"/compare/{slug}/" in model_html for slug in slugs):
            fail(f"{model_id}: model page does not link a curated comparison")

    provider_slugs = {}
    for comparison in indexable:
        comparison_providers = {
            models[model_id]["provider"] for model_id in comparison["model_ids"]
        }
        for provider in comparison_providers:
            provider_slugs.setdefault(provider, []).append(comparison["slug"])

    for provider, slugs in provider_slugs.items():
        provider_slug = re.sub(r"[^a-z0-9]+", "-", provider.lower()).strip("-")
        provider_path = ROOT / "providers" / provider_slug / "index.html"
        if not provider_path.exists():
            fail(f"{provider}: provider comparison backlink target missing")
        provider_html = provider_path.read_text(encoding="utf-8")
        if f'data-provider-comparisons="{provider_slug}"' not in provider_html:
            fail(f"{provider}: provider page missing comparison bridge")
        if not any(f"/compare/{slug}/" in provider_html for slug in slugs):
            fail(f"{provider}: provider page does not link a curated comparison")

    # Every catalog-backed /models/ URL must surface the latest ledger event for its model.
    events_by_model = {}
    for event in history["events"]:
        events_by_model.setdefault(event["model_id"], []).append(event)

    for model_id, model in models.items():
        url = model.get("sxf_url", "")
        if not url.startswith("/models/") or url == "/models/pricing/":
            continue
        path = local_path(BASE + url)
        if not path.exists():
            fail(f"{model_id}: model history target missing: {url}")
        html = path.read_text(encoding="utf-8")
        if "data-model-history" not in html:
            fail(f"{model_id}: model page missing verified history timeline")
        if "data-what-changed" not in html:
            fail(f"{model_id}: model page missing what-changed intelligence")
        latest = events_by_model.get(model_id, [])[-1] if events_by_model.get(model_id) else None
        if latest is None:
            fail(f"{model_id}: no ledger event available")
        if latest["event_id"] not in html:
            fail(f"{model_id}: latest ledger event is not surfaced on model page")
        if f'data-model-id="{model_id}"' not in html:
            fail(f"{model_id}: model timeline does not identify the model")
        model_changes = [event for event in events_by_model.get(model_id, []) if event.get("type") == "model_changed"]
        expected_count = len(model_changes)
        if f'data-change-count="{expected_count}"' not in html:
            fail(f"{model_id}: what-changed count drift; expected {expected_count}")
        if expected_count == 0 and "No post-baseline factual changes recorded" not in html:
            fail(f"{model_id}: baseline-only state must disclose that no factual changes are recorded")


def validate_topic_relevance(archive):
    from update_news import (
        TOPICS,
        TOPIC_RELEVANCE_VERSION,
        topic_groups,
        topic_matches,
        topic_relevance,
    )

    topics = {topic["slug"]: topic for topic in TOPICS}

    def item(title, summary="", source="OpenAI", category="Tools"):
        return {
            "title": title,
            "summary": summary,
            "source": source,
            "category": category,
            "tags": [],
        }

    cases = [
        (
            "ai-security",
            item(
                "Sam Altman’s remarks at the United Nations Security Council",
                "OpenAI discusses AI safety, human control, and international cooperation.",
            ),
            False,
            "institutional use of the word Security must not imply AI security",
        ),
        (
            "ai-security",
            item(
                "Local sandboxing in the GitHub Copilot app",
                "The sandbox isolates agent tools and reduces security risk.",
                source="GitHub",
            ),
            True,
            "sandboxing is direct AI security evidence",
        ),
        (
            "ai-security",
            item(
                "Paul Christiano joins OpenAI Foundation Board",
                "He joins the Safety and Security Committee and has experience in alignment and standards.",
            ),
            False,
            "a board appointment must not enter AI Security from an incidental committee name",
        ),
        (
            "open-source-ai",
            item(
                "A product update with no open model change",
                "We’re on a journey to advance and democratize artificial intelligence through open source and open science.",
                source="Hugging Face",
            ),
            False,
            "known Hugging Face boilerplate must not create Open Source relevance",
        ),
        (
            "open-source-ai",
            item(
                "Transformers now runs llama.cpp quants",
                "New local inference support lands in Transformers.",
                source="Hugging Face",
                category="Open Source",
            ),
            True,
            "llama.cpp and quants are direct open-source/local-inference evidence",
        ),
        (
            "ai-agents",
            item(
                "A general product update",
                "The release mentions agents once.",
            ),
            False,
            "a single incidental summary mention of agents must not pass",
        ),
        (
            "ai-agents",
            item(
                "A general product update",
                "Agent workflows now execute multi-step tasks with tool calling.",
            ),
            True,
            "multiple independent agent signals in the summary should pass",
        ),
        (
            "coding-ai",
            item(
                "Private saved views for repository issues",
                "Repository administrators can configure saved views.",
                source="GitHub",
            ),
            False,
            "repository administration alone is not Coding AI",
        ),
        (
            "coding-ai",
            item(
                "Codex adds repository-scale code review",
                "The coding agent reviews pull requests and codebases.",
            ),
            True,
            "Codex plus code-review evidence is directly relevant",
        ),
        (
            "multimodal-ai",
            item(
                "AI agents resolve customer calls",
                "The product can route voice calls to an agent.",
            ),
            False,
            "an incidental voice mention must not make an agent product a multimodal signal",
        ),
        (
            "ai-safety",
            item(
                "Priorities for independent model assessments",
                "The framework sets safety evaluation standards and safeguards for frontier models.",
                category="Research",
            ),
            True,
            "safety plus evaluation/safeguards is direct AI Safety evidence",
        ),
    ]

    for slug, sample, expected, reason in cases:
        topic = topics[slug]
        score, evidence = topic_relevance(sample, topic)
        actual = topic_matches(sample, topic)
        if actual != expected:
            fail(
                f"topic relevance: {slug} -> {actual}, expected {expected}; "
                f"score={score}, evidence={evidence}; {reason}"
            )

    openai_topic = topics["openai"]
    google_topic = topics["google-ai"]
    openai_sample = item("OpenAI product update", source="OpenAI")
    if topic_relevance(openai_sample, openai_topic)[0] != 100:
        fail("source-owned OpenAI topic must score 100 for OpenAI signals")
    if topic_matches(openai_sample, google_topic):
        fail("source-owned Google AI topic must not match an OpenAI signal")

    groups = topic_groups(archive.get("items", []))
    expected_slugs = {topic["slug"] for topic in TOPICS}
    missing = expected_slugs - set(groups)
    if missing:
        fail(f"topic relevance removed all signals from topics: {sorted(missing)}")

    for slug, (topic, matched) in groups.items():
        if len(matched) < 3:
            fail(f"{slug}: topic coverage too thin after relevance filtering ({len(matched)} signals)")
        page = ROOT / "topics" / slug / "index.html"
        if not page.exists():
            fail(f"{slug}: generated topic page is missing")
        html = page.read_text(encoding="utf-8")
        rendered_rows = html.count('class="signal-row"')
        older_indexable = sum(1 for item in matched[30:] if item.get("seo_eligible"))
        expected_rows = min(30, len(matched)) + min(12, older_indexable)
        if rendered_rows != expected_rows:
            fail(
                f"{slug}: rendered {rendered_rows} topic rows for "
                f"{len(matched)} relevance-matched signals; expected {expected_rows}"
            )

    if archive.get("topic_relevance_version") != TOPIC_RELEVANCE_VERSION:
        fail(
            "archive topic relevance version drift: "
            f"{archive.get('topic_relevance_version')!r} != {TOPIC_RELEVANCE_VERSION!r}"
        )


def source_has_recorded_error(errors, name):
    prefix = f"{name}:"
    return any(isinstance(error, str) and error.startswith(prefix) for error in errors)


def expansion_source_presence_valid(name, archive_count, errors):
    return archive_count >= 1 or source_has_recorded_error(errors, name)


def validate_source_resilience_regressions():
    recorded = ["Google Research: upstream feed unavailable"]
    if not expansion_source_presence_valid("Google Research", 0, recorded):
        fail("source resilience regression: recorded outage must allow graceful degradation")
    if expansion_source_presence_valid("Google Research", 0, []):
        fail("source resilience regression: silent zero-item source must fail validation")


def validate_source_expansion(news, archive):
    from update_news import (
        SOURCES,
        SOURCE_CONFIGS,
        SOURCE_BY_NAME,
        SOURCE_STATUSES,
        SOURCE_LIFECYCLE_VERSION,
        SOURCE_SHADOW_PATH,
        SHADOW_MAX_ITEMS_PER_SOURCE,
        SHADOW_REJECTED_MAX_ITEMS_PER_SOURCE,
        SOURCE_EXPANSION_NAMES,
        SOURCE_EXPANSION_VERSION,
        SOURCE_EXPANSION_MAX_CURRENT_PER_SOURCE,
        SOURCE_EXPANSION_MAX_CURRENT_TOTAL,
        categorize,
        source_accepts_item,
    )

    names = [source["name"] for source in SOURCE_CONFIGS]
    urls = [source.get("url") for source in SOURCE_CONFIGS if source.get("url")]
    if len(names) != len(set(names)):
        fail("source registry contains duplicate source names")
    if len(urls) != len(set(urls)):
        fail("source registry contains duplicate feed URLs")

    for source in SOURCE_CONFIGS:
        name = source["name"]
        status = source.get("status")
        max_current = source.get("max_current")
        if status not in SOURCE_STATUSES:
            fail(f"{name}: invalid lifecycle status {status!r}")
        if not isinstance(max_current, int) or max_current < 0:
            fail(f"{name}: invalid max_current")
        if status in {"shadow", "disabled"} and max_current != 0:
            fail(f"{name}: {status} source must have max_current=0")

    expected = {
        "Google Research": "https://research.google/blog/rss/",
    }
    for name, url in expected.items():
        config = SOURCE_BY_NAME.get(name)
        if not config:
            fail(f"source expansion missing configured source: {name}")
        if config.get("url") != url:
            fail(f"{name}: feed URL drift: {config.get('url')!r}")
        if config.get("wave") != "source-expansion-v1":
            fail(f"{name}: source expansion wave marker missing")

    if archive.get("source_expansion_version") != SOURCE_EXPANSION_VERSION:
        fail("archive source expansion version drift")
    if news.get("source_expansion_version") != SOURCE_EXPANSION_VERSION:
        fail("news source expansion version drift")

    health = archive.get("source_health")
    if not isinstance(health, dict):
        fail("archive source_health metadata missing")
    if health.get("configured") != len(SOURCE_CONFIGS):
        fail("source_health configured count does not match source registry")
    if health.get("publishing_configured") != len(SOURCES):
        fail("source_health publishing_configured count does not match publishing registry")
    if health.get("lifecycle_version") != SOURCE_LIFECYCLE_VERSION:
        fail("source_health lifecycle version drift")
    if archive.get("source_lifecycle_version") != SOURCE_LIFECYCLE_VERSION:
        fail("archive source lifecycle version drift")
    if news.get("source_lifecycle_version") != SOURCE_LIFECYCLE_VERSION:
        fail("news source lifecycle version drift")

    archive_counts = health.get("archive_counts", {})
    current_counts = health.get("current_counts", {})
    errors = health.get("errors", [])
    if not isinstance(errors, list):
        fail("source_health errors must be a list")

    validate_source_resilience_regressions()

    for name in SOURCE_EXPANSION_NAMES:
        if not expansion_source_presence_valid(name, archive_counts.get(name, 0), errors):
            fail(
                f"{name}: expansion source produced no archived signals "
                "and no source error was recorded"
            )
        if current_counts.get(name, 0) > SOURCE_EXPANSION_MAX_CURRENT_PER_SOURCE:
            fail(f"{name}: current-source cap exceeded")

    expansion_current = sum(current_counts.get(name, 0) for name in SOURCE_EXPANSION_NAMES)
    if expansion_current > SOURCE_EXPANSION_MAX_CURRENT_TOTAL:
        fail(
            f"source expansion current share exceeded hard cap: "
            f"{expansion_current} > {SOURCE_EXPANSION_MAX_CURRENT_TOTAL}"
        )

    source_metrics = health.get("sources")
    if not isinstance(source_metrics, dict):
        fail("source_health sources metrics missing")
    for source in SOURCE_CONFIGS:
        name = source["name"]
        metrics = source_metrics.get(name)
        if not isinstance(metrics, dict):
            fail(f"{name}: source metrics missing")
        required_metrics = {
            "status", "fetch_success", "fetch_failure", "parsed_candidate_count",
            "relevance_accepted_count", "quality_accepted_count",
            "accepted_candidate_count", "rejected_candidate_count", "duplicate_count",
            "age_rejection_count", "relevance_rejection_count", "quality_rejection_count", "publish_count",
            "adapter", "adapter_contract_version", "adapter_discovered_count", "adapter_invalid_count",
            "adapter_fetch_failure_count", "schema_drift", "last_successful_fetch", "errors",
        }
        if not required_metrics.issubset(metrics):
            fail(f"{name}: source metrics shape invalid")
        if metrics.get("status") != source["status"]:
            fail(f"{name}: source metrics status drift")
        if not isinstance(metrics.get("errors"), list):
            fail(f"{name}: source metrics errors must be a list")
        if metrics.get("fetch_failure") and not metrics.get("errors"):
            fail(f"{name}: fetch failure disappeared without a recorded error")
        if metrics.get("adapter") != source.get("adapter"):
            fail(f"{name}: adapter metrics drift")
        if source.get("adapter") == "rss":
            if metrics.get("adapter_contract_version") is not None:
                fail(f"{name}: RSS source must not report adapter contract version")
        elif source.get("adapter") == "pending":
            if metrics.get("fetch_success"):
                fail(f"{name}: pending adapter unexpectedly fetched")
        else:
            from source_adapters import ADAPTER_CONTRACT_VERSION
            if metrics.get("adapter_contract_version") != ADAPTER_CONTRACT_VERSION:
                fail(f"{name}: adapter contract version drift")
            adapter_counts = [
                metrics.get("adapter_discovered_count"),
                metrics.get("adapter_invalid_count"),
                metrics.get("adapter_fetch_failure_count"),
            ]
            if any(not isinstance(value, int) or value < 0 for value in adapter_counts):
                fail(f"{name}: adapter diagnostics counts must be non-negative integers")
            if not isinstance(metrics.get("schema_drift"), bool):
                fail(f"{name}: schema_drift must be boolean")
            if metrics.get("fetch_success") and metrics.get("adapter_discovered_count", 0) <= 0:
                fail(f"{name}: adapter fetch succeeded with zero discovered candidates")
        parsed = metrics.get("parsed_candidate_count")
        accepted = metrics.get("accepted_candidate_count")
        rejected = metrics.get("rejected_candidate_count")
        relevance_accepted = metrics.get("relevance_accepted_count")
        relevance_rejected = metrics.get("relevance_rejection_count")
        duplicate_count = metrics.get("duplicate_count")
        age_rejected = metrics.get("age_rejection_count")
        quality_accepted = metrics.get("quality_accepted_count")
        quality_rejected = metrics.get("quality_rejection_count")
        numeric = [
            parsed, accepted, rejected, relevance_accepted, relevance_rejected,
            duplicate_count, age_rejected, quality_accepted, quality_rejected,
        ]
        if any(not isinstance(value, int) or value < 0 for value in numeric):
            fail(f"{name}: source metrics counts must be non-negative integers")
        if parsed != relevance_accepted + relevance_rejected:
            fail(f"{name}: parsed/relevance metrics do not balance")
        if relevance_accepted != duplicate_count + age_rejected + quality_accepted + quality_rejected:
            fail(f"{name}: post-relevance metrics do not balance")
        if accepted != quality_accepted:
            fail(f"{name}: accepted_candidate_count must equal quality_accepted_count")
        if rejected != relevance_rejected + duplicate_count + age_rejected + quality_rejected:
            fail(f"{name}: rejected_candidate_count does not match rejection reasons")
        if parsed != accepted + rejected:
            fail(f"{name}: parsed candidates must equal accepted + rejected")

    actual_current_counts = {
        name: sum(1 for item in news.get("items", []) if item.get("source") == name)
        for name in names
    }
    for name, count in actual_current_counts.items():
        if current_counts.get(name, 0) != count:
            fail(
                f"{name}: source_health current count {current_counts.get(name, 0)} "
                f"!= actual {count}"
            )
    for source in SOURCE_CONFIGS:
        name = source["name"]
        status = source["status"]
        current_count = actual_current_counts.get(name, 0)
        archive_count = sum(1 for item in archive.get("items", []) if item.get("source") == name)
        if status in {"shadow", "disabled"} and (current_count or archive_count):
            fail(f"{name}: {status} source leaked into production current/archive")
        if status in {"canary", "live"} and current_count > source["max_current"]:
            fail(f"{name}: lifecycle current quota exceeded")
        if status == "disabled" and source_metrics[name].get("publish_count", 0) != 0:
            fail(f"{name}: disabled source recorded published signals")
        if status == "shadow" and source_metrics[name].get("publish_count", 0) != 0:
            fail(f"{name}: shadow source recorded published signals")

    if not SOURCE_SHADOW_PATH.exists():
        fail("source-shadow.json missing after build")
    shadow = json.loads(SOURCE_SHADOW_PATH.read_text(encoding="utf-8"))
    shadow_items = shadow.get("items")
    if not isinstance(shadow_items, list):
        fail("source-shadow items must be a list")
    rejected_items = shadow.get("rejected_items")
    if not isinstance(rejected_items, list):
        fail("source-shadow rejected_items must be a list")
    if shadow.get("max_rejected_items_per_source") != SHADOW_REJECTED_MAX_ITEMS_PER_SOURCE:
        fail("source-shadow rejection cap metadata drift")
    from update_news import parse_date, SHADOW_RETENTION_DAYS
    shadow_cutoff = datetime.now(timezone.utc) - timedelta(days=SHADOW_RETENTION_DAYS)
    shadow_counts = {}
    production_urls = {item.get("url") for item in archive.get("items", [])}
    for item in shadow_items:
        name = item.get("source")
        config = SOURCE_BY_NAME.get(name)
        if not config or config.get("status") != "shadow":
            fail(f"source-shadow contains non-shadow source: {name}")
        published = parse_date(item.get("published", ""))
        if published is None or published < shadow_cutoff:
            fail(f"{name}: source-shadow contains item outside retention window")
        if item.get("url") in production_urls:
            fail(f"{name}: shadow candidate leaked into production archive")
        if name == "Anthropic":
            provenance = item.get("provenance")
            if not isinstance(provenance, dict):
                fail("Anthropic shadow candidate missing provenance")
            if provenance.get("discovered_via") != "official-sitemap":
                fail("Anthropic shadow candidate provenance discovery drift")
            if provenance.get("source_url") != item.get("url"):
                fail("Anthropic shadow candidate provenance source URL drift")
        shadow_counts[name] = shadow_counts.get(name, 0) + 1
    for name, count in shadow_counts.items():
        if count > SHADOW_MAX_ITEMS_PER_SOURCE:
            fail(f"{name}: shadow retention cap exceeded")
    accepted_shadow_urls = {item.get("url") for item in shadow_items}
    rejected_counts = {}
    for item in rejected_items:
        name = item.get("source")
        config = SOURCE_BY_NAME.get(name)
        if not config or config.get("status") != "shadow":
            fail(f"source-shadow rejected_items contains non-shadow source: {name}")
        if item.get("rejection_stage") != "quality" or item.get("rejection_reason") != "seo_quality_gate":
            fail(f"{name}: shadow rejection audit has invalid rejection metadata")
        if not isinstance(item.get("failed_checks"), list) or not item["failed_checks"]:
            fail(f"{name}: shadow rejection audit missing failed_checks")
        published = parse_date(item.get("published", ""))
        if published is None or published < shadow_cutoff:
            fail(f"{name}: rejected shadow item outside retention window")
        if item.get("url") in production_urls:
            fail(f"{name}: rejected shadow candidate leaked into production archive")
        if item.get("url") in accepted_shadow_urls:
            fail(f"{name}: URL appears in both accepted and rejected shadow sets")
        if name == "Anthropic":
            provenance = item.get("provenance")
            if not isinstance(provenance, dict):
                fail("Anthropic rejected shadow candidate missing provenance")
            if provenance.get("discovered_via") != "official-sitemap":
                fail("Anthropic rejected shadow candidate provenance discovery drift")
            if provenance.get("source_url") != item.get("url"):
                fail("Anthropic rejected shadow candidate provenance source URL drift")
        if not isinstance(item.get("seo_quality_score"), int):
            fail(f"{name}: rejected shadow audit missing seo_quality_score")
        if not isinstance(item.get("summary_chars"), int):
            fail(f"{name}: rejected shadow audit missing summary_chars")
        rejected_counts[name] = rejected_counts.get(name, 0) + 1
    for name, count in rejected_counts.items():
        if count > SHADOW_REJECTED_MAX_ITEMS_PER_SOURCE:
            fail(f"{name}: shadow rejection audit cap exceeded")

    google_research = SOURCE_BY_NAME["Google Research"]
    if source_accepts_item(
        google_research,
        "Designing faster datacenter networks",
        "A systems architecture update about datacenter fabrics, routing, and scheduling.",
    ):
        fail("Google Research AI filter admitted a non-AI systems article")
    if not source_accepts_item(
        google_research,
        "Scaling multimodal foundation models",
        "New research on vision-language learning.",
    ):
        fail("Google Research AI filter rejected a clearly relevant AI article")

    if categorize("A new method for biological discovery", "Google Research") != "Research":
        fail("Google Research fallback category must be Research")

    home_html = (ROOT / "index.html").read_text(encoding="utf-8")
    expected_source_label = f"{len(SOURCES):02d} SOURCES · 04 LAYERS"
    if expected_source_label not in home_html:
        fail(f"homepage source count drift: expected {expected_source_label}")
    for name in SOURCE_EXPANSION_NAMES:
        if name.upper() not in home_html.upper():
            fail(f"homepage source layer missing active expansion source: {name}")



def validate_indexable_signal_graph(archive):
    eligible = [item for item in archive.get("items", []) if item.get("seo_eligible")]
    if not eligible:
        return

    noindex = re.compile(
        r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',
        re.I,
    )
    indexable_pages = []
    for path in ROOT.rglob("*.html"):
        try:
            html = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if noindex.search(html):
            continue
        indexable_pages.append((path.resolve(), html))

    missing = []
    for item in eligible:
        slug = item.get("signal_slug")
        signal_url = item.get("signal_url")
        if not slug or not signal_url:
            missing.append(item.get("title", "<untitled>"))
            continue
        relative = f"/signals/{slug}/"
        link_pattern = re.compile(
            r'href=["\'](?:https://sxf\.si)?' + re.escape(relative) + r'["\']',
            re.I,
        )
        target = local_path(signal_url).resolve()
        inbound = [
            path for path, html in indexable_pages
            if path != target and link_pattern.search(html)
        ]
        if not inbound:
            missing.append(item.get("title", signal_url))

    if missing:
        fail(
            "indexable signal(s) lack inbound links from another indexable HTML page: "
            + " | ".join(missing)
        )

    open_source_html = (ROOT / "open-source" / "index.html").read_text(encoding="utf-8")
    if '/guides/open-source-ai-models/' not in open_source_html:
        fail("Open Source hub must link to the Open Source AI Models guide")

def validate_ai_enrichment_dry_run():
    if not AI_ENRICHMENT_CONFIG_PATH.exists():
        fail("AI enrichment config missing")
    if not AI_ENRICHMENT_CANDIDATES_PATH.exists():
        fail("AI enrichment candidate output missing")

    config = json.loads(AI_ENRICHMENT_CONFIG_PATH.read_text(encoding="utf-8"))
    payload = json.loads(AI_ENRICHMENT_CANDIDATES_PATH.read_text(encoding="utf-8"))

    if config.get("version") != "sxf-ai-enrichment-v1":
        fail("AI enrichment config version drift")
    if config.get("mode") != "dry-run":
        fail("AI enrichment must remain dry-run in v1")
    if config.get("publish_mode") != "manual-review":
        fail("AI enrichment v1 must require manual review")
    if not config.get("required_ai_intent"):
        fail("AI enrichment must require explicit enrichment intent")

    budget = config.get("monthly_budget_eur")
    page_limit = config.get("monthly_page_limit")
    input_cap = config.get("per_page_input_token_cap")
    output_cap = config.get("per_page_output_token_cap")
    if not isinstance(budget, (int, float)) or budget <= 0 or budget > 5:
        fail("AI enrichment monthly budget must be >0 and <=5 EUR")
    if not isinstance(page_limit, int) or page_limit <= 0 or page_limit > 100:
        fail("AI enrichment monthly page limit must be 1..100")
    if not isinstance(input_cap, int) or input_cap <= 0 or input_cap > 8000:
        fail("AI enrichment input token cap must be 1..8000")
    if not isinstance(output_cap, int) or output_cap <= 0 or output_cap > 5000:
        fail("AI enrichment output token cap must be 1..5000")

    quality_gate = config.get("publish_quality_gate")
    if not isinstance(quality_gate, dict):
        fail("AI publish quality gate config missing")
    if quality_gate.get("version") != "sxf-publish-quality-v1":
        fail("AI publish quality gate version drift")
    if not isinstance(quality_gate.get("minimum_ai_quality_score"), int) or quality_gate["minimum_ai_quality_score"] < 90:
        fail("AI publish quality score must be >=90")
    if quality_gate.get("faq_min", 0) < 3 or quality_gate.get("faq_max", 0) > 6:
        fail("AI publish FAQ bounds drift")
    required_schema = quality_gate.get("required_schema_types")
    if required_schema != ["TechArticle", "BreadcrumbList", "FAQPage"]:
        fail("AI publish schema requirements drift")
    if not quality_gate.get("require_item_list_for_comparison"):
        fail("AI publish comparisons must require ItemList schema")
    if not quality_gate.get("forbid_process_language"):
        fail("AI publish gate must forbid process language")
    if not quality_gate.get("require_direct_search_intent"):
        fail("AI publish gate must require direct search intent")
    if not quality_gate.get("require_value_beyond_news"):
        fail("AI publish gate must require value beyond news")

    if payload.get("version") != config.get("version") or payload.get("mode") != "dry-run":
        fail("AI enrichment candidate payload version/mode drift")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        fail("AI enrichment candidates must be a list")
    if payload.get("candidate_count") != len(candidates):
        fail("AI enrichment candidate count drift")
    if len(candidates) > int(config.get("candidate_limit", 0)):
        fail("AI enrichment candidate limit exceeded")

    budget_guard = payload.get("budget_guard", {})
    expected_guard = {
        "monthly_budget_eur": budget,
        "monthly_page_limit": page_limit,
        "per_page_input_token_cap": input_cap,
        "per_page_output_token_cap": output_cap,
        "writer_model": config.get("writer_model"),
        "validator_model": config.get("validator_model"),
    }
    if budget_guard != expected_guard:
        fail("AI enrichment budget guard drift")

    slugs = set()
    for row in candidates:
        slug = row.get("signal_slug")
        if not slug or slug in slugs:
            fail(f"AI enrichment duplicate/invalid signal slug: {slug}")
        slugs.add(slug)
        if row.get("generation_status") != "not-called":
            fail(f"{slug}: AI must not be called in dry-run")
        if row.get("index_decision") != "unchanged":
            fail(f"{slug}: dry-run must not change index decision")
        if not isinstance(row.get("priority_score"), int) or row["priority_score"] < 0:
            fail(f"{slug}: invalid enrichment priority score")
        evidence = row.get("evidence")
        if not isinstance(evidence, dict):
            fail(f"{slug}: missing evidence pack")
        signal = evidence.get("signal")
        if not isinstance(signal, dict) or signal.get("signal_url") != row.get("signal_url"):
            fail(f"{slug}: evidence signal identity drift")
        source_urls = evidence.get("source_urls")
        if not isinstance(source_urls, list) or not source_urls:
            fail(f"{slug}: evidence pack has no source URLs")
        pricing_basis = evidence.get("pricing_basis")
        if not isinstance(pricing_basis, dict):
            fail(f"{slug}: pricing basis missing from evidence")
        if evidence.get("models") and any(model.get("pricing_standard") for model in evidence.get("models", [])):
            if not pricing_basis.get("currency") or not pricing_basis.get("unit"):
                fail(f"{slug}: model pricing evidence missing currency/unit")
        if signal.get("url") not in source_urls:
            fail(f"{slug}: primary source missing from evidence source URLs")
        if any(not isinstance(url, str) or not url.startswith("https://") for url in source_urls):
            fail(f"{slug}: evidence source URL must be https")
        requested = row.get("requested_output")
        if not isinstance(requested, dict) or requested.get("fact_policy") != "evidence-only":
            fail(f"{slug}: requested output must be evidence-only")
        if requested.get("route_policy") != "preserve-existing-signal-route":
            fail(f"{slug}: AI must not control routing")
        if requested.get("seo_slug_policy") != "propose concise search-intent slug; code decides routing later":
            fail(f"{slug}: SEO slug policy drift")
        if "comparison" not in requested.get("value_policy", ""):
            fail(f"{slug}: enrichment must require comparison/value beyond news")
        if "FAQPage" not in requested.get("schema_requirement", ""):
            fail(f"{slug}: schema requirement missing FAQPage")
        if requested.get("unknown_policy") != "use unknown or omit; never infer unsupported facts":
            fail(f"{slug}: unknown policy drift")
        if not isinstance(row.get("evidence_hash"), str) or len(row["evidence_hash"]) != 64:
            fail(f"{slug}: invalid evidence hash")

    snapshot_hash = payload.get("snapshot_hash")
    if not isinstance(snapshot_hash, str) or len(snapshot_hash) != 64:
        fail("AI enrichment snapshot hash invalid")



def validate_evaluation_explorer():
    explorer_path = ROOT / "evaluations" / "explorer" / "index.html"
    script_path = ROOT / "evaluations" / "explorer" / "explorer.js"
    if not explorer_path.exists():
        fail("evaluation explorer page is missing")
    if not script_path.exists():
        fail("evaluation explorer JavaScript is missing")

    html = explorer_path.read_text(encoding="utf-8")
    js = script_path.read_text(encoding="utf-8")
    required_html = (
        "EVALUATION EXPLORER V1",
        "data-evaluation-explorer",
        "/data/model-evaluations.json",
        "/data/model-pricing.json",
        'data-eval-view="table"',
        'data-eval-view="cost"',
        'data-eval-view="context"',
        '<script src="/evaluations/explorer/explorer.js" defer></script>',
        "No speed view yet",
    )
    for marker in required_html:
        if marker not in html:
            fail(f"evaluation explorer missing marker: {marker}")

    required_js = (
        "comparableRows",
        "pareto",
        "workloadCost",
        "pricing_status",
        "calculator_eligible",
        "Multiple comparable groups are present",
        "Cost view requires calculator-eligible provider Standard pricing.",
    )
    for marker in required_js:
        if marker not in js:
            fail(f"evaluation explorer JS missing contract marker: {marker}")

    lowered = js.lower()
    for marker in ("universal intelligence score", "overall winner score", "best model overall"):
        if marker in lowered:
            fail(f"evaluation explorer contains banned synthetic-ranking language: {marker}")

    pricing = json.loads((ROOT / "data" / "model-pricing.json").read_text(encoding="utf-8"))
    model_by_id = {row["model_id"]: row for row in pricing["models"]}
    for model_id in (
        "gpt-6-astra", "gpt-6-sol", "claude-opus-5-5",
        "claude-fable-5-1", "gemini-3.8-flash", "grok-4.7",
    ):
        model = model_by_id.get(model_id)
        if model and model["model"] not in html:
            fail(f"evaluation explorer fallback missing {model_id}")


def validate_model_evaluations():
    path = ROOT / "data" / "model-evaluations.json"
    if not path.exists():
        fail("model-evaluations.json is missing")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != "1.0":
        fail(f"model-evaluations.json schema drift: {data.get('schema_version')!r}")

    pricing = json.loads((ROOT / "data" / "model-pricing.json").read_text(encoding="utf-8"))
    model_ids = {model["model_id"] for model in pricing["models"]}

    benchmarks = data.get("benchmarks")
    observations = data.get("observations")
    if not isinstance(benchmarks, list) or not benchmarks:
        fail("model-evaluations.json must contain benchmark definitions")
    if not isinstance(observations, list) or not observations:
        fail("model-evaluations.json must contain observations")

    benchmark_ids = [benchmark.get("benchmark_id") for benchmark in benchmarks]
    if any(not benchmark_id for benchmark_id in benchmark_ids) or len(benchmark_ids) != len(set(benchmark_ids)):
        fail("evaluation benchmark IDs must be present and unique")
    benchmark_by_id = {benchmark["benchmark_id"]: benchmark for benchmark in benchmarks}
    for benchmark in benchmarks:
        if benchmark.get("evidence_type") not in {"independent", "vendor-reported"}:
            fail(f"{benchmark['benchmark_id']}: invalid evidence type")
        if benchmark.get("status") not in {"active", "under-review", "deprecated"}:
            fail(f"{benchmark['benchmark_id']}: invalid benchmark status")
        if benchmark.get("direction") not in {"higher-is-better", "lower-is-better"}:
            fail(f"{benchmark['benchmark_id']}: invalid metric direction")
        if not benchmark.get("methodology_url") or not benchmark.get("source_url"):
            fail(f"{benchmark['benchmark_id']}: missing methodology/source URL")

    observation_ids = [row.get("observation_id") for row in observations]
    if any(not observation_id for observation_id in observation_ids) or len(observation_ids) != len(set(observation_ids)):
        fail("evaluation observation IDs must be present and unique")

    for row in observations:
        observation_id = row["observation_id"]
        if row.get("model_id") not in model_ids:
            fail(f"{observation_id}: unknown model_id {row.get('model_id')!r}")
        benchmark_id = row.get("benchmark_id")
        if benchmark_id not in benchmark_by_id:
            fail(f"{observation_id}: unknown benchmark_id {benchmark_id!r}")
        benchmark = benchmark_by_id[benchmark_id]
        if row.get("evidence_type") != benchmark.get("evidence_type"):
            fail(f"{observation_id}: evidence_type does not match benchmark definition")
        if not isinstance(row.get("score"), (int, float)):
            fail(f"{observation_id}: score must be numeric")
        if not row.get("observed_at"):
            fail(f"{observation_id}: observed_at is required")
        try:
            datetime.fromisoformat(row["observed_at"])
        except ValueError:
            fail(f"{observation_id}: invalid observed_at")
        if not row.get("source_url") or not row.get("source_name"):
            fail(f"{observation_id}: source provenance missing")
        if not isinstance(row.get("model_configuration"), dict):
            fail(f"{observation_id}: model_configuration must be an object")
        if not row.get("comparable_group"):
            fail(f"{observation_id}: comparable_group is required")

    under_review = {
        benchmark["benchmark_id"]
        for benchmark in benchmarks
        if benchmark.get("status") == "under-review"
    }
    if not {"scicode-aa", "critpt-aa"}.issubset(under_review):
        fail("current review status drift: SciCode and CritPt must remain explicitly under-review")

    evaluations_index = ROOT / "evaluations" / "index.html"
    if not evaluations_index.exists():
        fail("evaluation intelligence hub is missing")
    hub_html = evaluations_index.read_text(encoding="utf-8")
    for marker in ("EVALUATION INTELLIGENCE", "Same name does not mean same measurement.", "/data/model-evaluations.json"):
        if marker not in hub_html:
            fail(f"evaluation hub missing marker: {marker}")

    for benchmark in benchmarks:
        benchmark_id = benchmark["benchmark_id"]
        benchmark_path = ROOT / "evaluations" / benchmark_id / "index.html"
        if not benchmark_path.exists():
            fail(f"{benchmark_id}: benchmark evidence page is missing")
        html = benchmark_path.read_text(encoding="utf-8")
        if benchmark["methodology_url"] not in html:
            fail(f"{benchmark_id}: methodology link missing")
        if benchmark.get("status") == "under-review" and "UNDER-REVIEW" not in html:
            fail(f"{benchmark_id}: under-review warning is not surfaced")

    observed_models = {row["model_id"] for row in observations}
    model_catalog = {model["model_id"]: model for model in pricing["models"]}
    for model_id in observed_models:
        model = model_catalog[model_id]
        url = model.get("sxf_url", "")
        if not url.startswith("/models/") or url == "/models/pricing/":
            continue
        model_path = local_path(BASE + url)
        if not model_path.exists():
            fail(f"{model_id}: evaluation model target is missing")
        html = model_path.read_text(encoding="utf-8")
        if f'data-model-evaluations="{model_id}"' not in html:
            fail(f"{model_id}: model page missing evaluation evidence block")

    comparison_registry = json.loads((ROOT / "data" / "model-comparisons.json").read_text(encoding="utf-8"))
    for comparison in comparison_registry["comparisons"]:
        if comparison.get("indexable") is not True:
            continue
        compare_path = ROOT / "compare" / comparison["slug"] / "index.html"
        if not compare_path.exists():
            fail(f"{comparison['slug']}: comparison page missing for evaluation check")
        html = compare_path.read_text(encoding="utf-8")
        if "INDEPENDENT EVALUATIONS" not in html:
            fail(f"{comparison['slug']}: comparison page missing evaluation evidence section")

    # A comparable group may represent a multi-benchmark evaluation suite, but it must
    # not mix independent and vendor-reported evidence inside the same group.
    group_evidence_types = {}
    for row in observations:
        group_evidence_types.setdefault(row["comparable_group"], set()).add(row["evidence_type"])
    for group, evidence_types in group_evidence_types.items():
        if len(evidence_types) != 1:
            fail(f"comparable_group {group!r} mixes evidence types: {sorted(evidence_types)}")


def main():
    from update_news import categorize
    cases = {
        ("Local sandboxing in the GitHub Copilot app","GitHub"):"Tools",
        ("OpenTelemetry in the GitHub Copilot app","GitHub"):"Tools",
        ("Claude Opus 5.5 is now available in GitHub Copilot","GitHub"):"Tools",
        ("ChatGPT Ads expands to Southeast Asia and Taiwan","OpenAI"):"Tools",
        ("Introducing ChatGPT for Financial Services","OpenAI"):"Tools",
        ("Our framework for reporting model misalignment","OpenAI"):"Research",
        ("Introducing GPT-6 Sol and Luna","OpenAI"):"Models",
        ("Transformers now runs llama.cpp quants","Hugging Face"):"Open Source",
        ("TimesFM-3: A zero-shot foundation model for multivariate forecasting","Google Research"):"Models",
        ("GlucoFM: Foundation model for continuous glucose monitoring","Google Research"):"Models",
    }
    for (title, source), expected in cases.items():
        actual = categorize(title, source)
        if actual != expected:
            fail(f"classifier: {title!r} -> {actual}, expected {expected}")

    validate_model_pricing_catalog()
    validate_model_history()
    validate_super_agent_internal_links()
    validate_agentic_ai_guide()
    validate_ai_takeover_guide()
    validate_how_to_build_super_agent()
    validate_change_intelligence_regressions()
    validate_compare_contracts_and_model_histories()
    validate_model_evaluations()
    validate_evaluation_explorer()
    validate_ai_enrichment_dry_run()
    news = json.loads((ROOT/"data"/"news.json").read_text(encoding="utf-8"))
    archive = json.loads((ROOT/"data"/"archive.json").read_text(encoding="utf-8"))
    aliases = json.loads((ROOT/"data"/"slug_aliases.json").read_text(encoding="utf-8"))
    if not news.get("items"):
        fail("news.json has no items")
    if news.get("topic_relevance_version") != archive.get("topic_relevance_version"):
        fail("news/archive topic relevance versions must match")
    if len(archive.get("items",[])) < len(news["items"]):
        fail("archive must contain at least current feed items")
    validate_topic_relevance(archive)
    validate_source_expansion(news, archive)
    validate_indexable_signal_graph(archive)
    validate_site_shell()
    validate_section_counts(news)
    for item in news["items"]:
        required={"title","url","signal_url","source","published","category"}
        if not required.issubset(item):
            fail(f"news item missing fields: {item.get('title')}")
        if "editorial" in item:
            fail("news.json must stay client-light")
        if item["url"] in aliases and item["signal_url"] != BASE + "/signals/" + aliases[item["url"]] + "/":
            fail(f"canonical slug drift: {item['title']}")

    eligible = [item for item in archive.get("items", []) if item.get("seo_eligible")]
    if eligible:
        why_values = {item.get("editorial", {}).get("why_it_matters", "").strip() for item in eligible}
        verify_values = {item.get("editorial", {}).get("what_to_verify", "").strip() for item in eligible}
        if "" in why_values or "" in verify_values:
            fail("indexable signals must include Why it matters and What to verify")
        if len(eligible) >= 12 and len(why_values) < 6:
            fail(f"signal editorial diversity too low: only {len(why_values)} Why it matters variants for {len(eligible)} indexable signals")
        if len(eligible) >= 12 and len(verify_values) < 6:
            fail(f"signal editorial diversity too low: only {len(verify_values)} What to verify variants for {len(eligible)} indexable signals")
        boilerplate = re.compile(r"The post .+ appeared first on The GitHub Blog", re.I)
        for item in eligible:
            if boilerplate.search(item.get("editorial", {}).get("what_changed", "")):
                fail(f"RSS boilerplate leaked into signal editorial: {item.get('title')}")

    tree=ET.parse(ROOT/"sitemap.xml")
    ns={"s":"http://www.sitemaps.org/schemas/sitemap/0.9"}
    seen=set()
    for node in tree.findall("s:url",ns):
        loc=node.findtext("s:loc",namespaces=ns)
        if not loc or not loc.startswith(BASE):
            fail(f"invalid sitemap loc: {loc}")
        if loc in seen:
            fail(f"duplicate sitemap URL: {loc}")
        seen.add(loc)
        target=local_path(loc)
        if not target.exists():
            fail(f"sitemap URL missing file: {loc}")
        validate_html(target)
        html=target.read_text(encoding="utf-8")
        if re.search(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex',html,re.I):
            fail(f"noindex URL in sitemap: {loc}")

    core=[ROOT/"index.html",ROOT/"about"/"index.html",ROOT/"signals"/"index.html",ROOT/"topics"/"index.html",ROOT/"brief"/"index.html"]
    core += [ROOT/x/"index.html" for x in ("models","tools","research","open-source")]
    core.append(ROOT/"models"/"pricing"/"index.html")
    core.append(ROOT/"tools"/"ai-model-cost-calculator"/"index.html")
    for path in core:
        validate_html(path)
    for item in archive["items"]:
        validate_html(local_path(item["signal_url"]))

    section_js=(ROOT/"section.js").read_text(encoding="utf-8")
    if "x.signal_url||x.url" not in section_js:
        fail("section.js must prefer signal_url")

    print(f"Validation passed: {len(news['items'])} current / {len(archive['items'])} archived / {len(seen)} sitemap URLs")

if __name__ == "__main__":
    main()
