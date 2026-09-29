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

    baseline_count = sum(1 for event in history["events"] if event.get("type") == "baseline")
    if baseline_count != len(catalog["models"]):
        fail(f"model history baseline count {baseline_count} != {len(catalog['models'])} catalog models")

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
    if data.get("schema_version") != "1.1":
        fail(f"model-pricing.json schema_version drift: {data.get('schema_version')!r}")

    policy = data.get("verification_policy")
    if not isinstance(policy, dict) or policy.get("standard") != "Primary-source verification":
        fail("model-pricing.json verification policy missing or invalid")

    models = data.get("models")
    if not isinstance(models, list) or not models:
        fail("model-pricing.json must contain a non-empty models array")

    required_ids = {
        "gpt-6-astra", "gpt-6-sol", "gpt-6-luna",
        "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna",
        "claude-fable-5-1", "claude-opus-5-5", "claude-sonnet-5",
        "claude-haiku-4-5-20251001", "gemini-3.8-flash",
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
        if not isinstance(model.get("max_output"), int) or model["max_output"] <= 0:
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
        if provenance.get("verified_at") != verified:
            fail(
                f"{model_id}: provenance verified_at {provenance.get('verified_at')!r} "
                f"must match catalog source_verified {verified!r}"
            )
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

        schedule = model.get("pricing", {}).get("standard")
        if not isinstance(schedule, list) or not schedule:
            fail(f"{model_id}: missing Standard pricing schedule")

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

        if not covers_verified_date:
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

    from update_news import MODEL_REFERENCE, active_standard_price, estimate_standard_cost
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
    guides = (ROOT / "guides" / "index.html").read_text(encoding="utf-8")
    if '/guides/will-ai-take-over-the-world/' not in guides:
        fail("Guides index missing AI takeover guide")
    if "Will AI Take Over the World? The First 24 Hours of an AI Takeover" not in guides:
        fail("Guides index must use the full AI takeover guide title")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    if "https://sxf.si/guides/will-ai-take-over-the-world/images/ai-takeover-capability-stack.webp" not in sitemap:
        fail("Sitemap missing AI takeover primary image")
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
    models = {model["model_id"]: model for model in catalog["models"]}

    comparisons = {
        "gpt-6-astra-vs-sol-vs-luna": ["gpt-6-astra", "gpt-6-sol", "gpt-6-luna"],
        "gpt-6-sol-vs-claude-opus-5-5": ["gpt-6-sol", "claude-opus-5-5"],
        "gpt-6-sol-vs-gemini-3-8-flash": ["gpt-6-sol", "gemini-3.8-flash"],
        "claude-opus-5-5-vs-gemini-3-8-flash": ["claude-opus-5-5", "gemini-3.8-flash"],
        "gpt-6-astra-vs-claude-fable-5-1": ["gpt-6-astra", "claude-fable-5-1"],
    }

    verified = catalog["source_verified"]
    for slug, model_ids in comparisons.items():
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

        for model_id in model_ids:
            model = models[model_id]
            schedule = model["pricing"]["standard"]
            price = None
            target = datetime.fromisoformat(verified).date()
            for period in schedule:
                start = datetime.fromisoformat(period["start"]).date()
                end = datetime.fromisoformat(period["end"]).date() if period.get("end") else None
                if start <= target and (end is None or target <= end):
                    price = period
                    break
            if price is None:
                fail(f"{slug}: no active Standard price for {model_id}")

            row_pattern = (
                rf'<article class="compare-live-card"[^>]+data-compare-model="{re.escape(model_id)}"'
                rf'[^>]+data-context="{int(model["context_window"])}"'
                rf'[^>]+data-max-output="{int(model["max_output"])}"'
                rf'[^>]+data-input="{float(price["input"]):g}"'
                rf'[^>]+data-cached="{float(price["cached_input"]):g}"'
                rf'[^>]+data-output="{float(price["output"]):g}"'
            )
            if not re.search(row_pattern, html, re.S):
                fail(f"{slug}: live facts drift for {model_id}")

            evidence = model["provenance"]["evidence"]
            if evidence["model_identity"] not in html or evidence["pricing"] not in html:
                fail(f"{slug}: official evidence links missing for {model_id}")

    from update_news import compare_pair_fact_line
    hub_html = (ROOT / "compare" / "index.html").read_text(encoding="utf-8")
    hub_pairs = [
        ["gpt-6-astra", "claude-fable-5-1"],
        ["gpt-6-sol", "gemini-3.8-flash"],
        ["claude-opus-5-5", "gemini-3.8-flash"],
        ["gpt-6-sol", "claude-opus-5-5"],
        ["gpt-6-astra", "gpt-6-sol", "gpt-6-luna"],
    ]
    for model_ids in hub_pairs:
        expected = compare_pair_fact_line(model_ids)
        if expected not in hub_html:
            fail(f"compare hub facts drift for {model_ids}")

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
            "last_successful_fetch", "errors",
        }
        if not required_metrics.issubset(metrics):
            fail(f"{name}: source metrics shape invalid")
        if metrics.get("status") != source["status"]:
            fail(f"{name}: source metrics status drift")
        if not isinstance(metrics.get("errors"), list):
            fail(f"{name}: source metrics errors must be a list")
        if metrics.get("fetch_failure") and not metrics.get("errors"):
            fail(f"{name}: fetch failure disappeared without a recorded error")
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
        shadow_counts[name] = shadow_counts.get(name, 0) + 1
    for name, count in shadow_counts.items():
        if count > SHADOW_MAX_ITEMS_PER_SOURCE:
            fail(f"{name}: shadow retention cap exceeded")

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
    validate_ai_takeover_guide()
    validate_how_to_build_super_agent()
    validate_change_intelligence_regressions()
    validate_compare_contracts_and_model_histories()
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
