#!/usr/bin/env python3
"""Ensure SXF original agent evidence remains indexable and discoverable after feed regeneration."""
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
URL = "https://sxf.si/research/ai-agent-hands-on-2026-11/"
study = (ROOT / "research/ai-agent-hands-on-2026-11/index.html").read_text(encoding="utf-8")
hub = (ROOT / "research/index.html").read_text(encoding="utf-8")
guide = (ROOT / "guides/best-ai-agents/index.html").read_text(encoding="utf-8")
sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
generator = (ROOT / "scripts/sitemap_generation.py").read_text(encoding="utf-8")

assert '<meta name="robots" content="index,follow">' in study
assert f'<link rel="canonical" href="{URL}">' in study
assert 'ChatGPT Work vs Claude Cowork vs Manus Lite' in study
assert 'source evidence' in study.lower() or 'source files' in study.lower()
assert study.count('<h1>') == 1
assert study.count('id="limitations"') == 1
assert '/research/ai-agent-hands-on-2026-11/' in hub, "Research hub must link study"
assert '/research/ai-agent-hands-on-2026-11/' in guide, "Comparison guide must link study"
assert 'sitemap_entry(f"{BASE_URL}/research/ai-agent-hands-on-2026-11/"' in generator
rows = [v.text for v in ET.fromstring(sitemap).iter() if v.tag.endswith('loc')]
assert rows.count(URL) == 1, "Original study must appear exactly once in sitemap"
match = re.search(r'<script type="application/ld[+]json">(.*?)</script>', study, re.S)
assert match, "Missing JSON-LD article metadata"
obj = json.loads(match.group(1))
assert any(x.get("@type") == "TechArticle" for x in obj["@graph"])
assert len([x for x in obj["@graph"] if x.get("@type") == "BreadcrumbList"]) == 1
print("PASS: original SXF AI Agent Lab study discoverable, indexed in sitemap and linked from hubs")
