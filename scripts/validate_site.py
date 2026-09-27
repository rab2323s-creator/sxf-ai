#!/usr/bin/env python3
from __future__ import annotations
import json
import re
import sys
import xml.etree.ElementTree as ET
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
    }
    for (title, source), expected in cases.items():
        actual = categorize(title, source)
        if actual != expected:
            fail(f"classifier: {title!r} -> {actual}, expected {expected}")

    news = json.loads((ROOT/"data"/"news.json").read_text(encoding="utf-8"))
    archive = json.loads((ROOT/"data"/"archive.json").read_text(encoding="utf-8"))
    aliases = json.loads((ROOT/"data"/"slug_aliases.json").read_text(encoding="utf-8"))
    if not news.get("items"):
        fail("news.json has no items")
    if len(archive.get("items",[])) < len(news["items"]):
        fail("archive must contain at least current feed items")
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
