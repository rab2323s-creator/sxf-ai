#!/usr/bin/env python3
from __future__ import annotations
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
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
    ROOT / "research" / "index.html",
    ROOT / "open-source" / "index.html",
    ROOT / "guides" / "ai-agent-security" / "index.html",
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


def validate_model_pricing_catalog():
    path = ROOT / "data" / "model-pricing.json"
    data = json.loads(path.read_text(encoding="utf-8"))
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
    if "/models/pricing/pricing.js" not in pricing_html or "/models/pricing/pricing.css" not in pricing_html:
        fail("model pricing page is missing calculator assets")

    pricing_js = (ROOT / "models" / "pricing" / "pricing.js").read_text(encoding="utf-8")
    if 'fetch("/data/model-pricing.json"' not in pricing_js:
        fail("pricing calculator must load the canonical model-pricing.json dataset")
    if "effectiveRates" not in pricing_js or "threshold_input_tokens" not in pricing_js:
        fail("pricing calculator must apply catalog pricing rules")


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
        if rendered_rows != min(30, len(matched)):
            fail(
                f"{slug}: rendered {rendered_rows} topic rows for "
                f"{len(matched)} relevance-matched signals"
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
        SOURCE_BY_NAME,
        SOURCE_EXPANSION_NAMES,
        SOURCE_EXPANSION_VERSION,
        SOURCE_EXPANSION_MAX_CURRENT_PER_SOURCE,
        SOURCE_EXPANSION_MAX_CURRENT_TOTAL,
        categorize,
        source_accepts_item,
    )

    names = [source["name"] for source in SOURCES]
    urls = [source["url"] for source in SOURCES]
    if len(names) != len(set(names)):
        fail("source registry contains duplicate source names")
    if len(urls) != len(set(urls)):
        fail("source registry contains duplicate feed URLs")

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
    if health.get("configured") != len(SOURCES):
        fail("source_health configured count does not match source registry")

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
