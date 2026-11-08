#!/usr/bin/env python3
"""SXF GPT-Realtime-2.1 Playground: SEO, scientific integrity and discoverability."""
from pathlib import Path
import json,re,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"guides/gpt-realtime-2-1-playground/index.html"
html=P.read_text(encoding="utf-8")
url="https://sxf.si/guides/gpt-realtime-2-1-playground/"
assert html.count("<h1 ")==1
assert '<link rel="canonical" href="'+url+'">' in html
assert 'name="robots" content="index,follow' in html
assert '<meta name="description"' in html
assert "gpt-realtime-2.1 playground" in html.lower()
assert "no measured pass rates" in html.lower()
assert "not a measured benchmark" in html.lower() or "not a claim" in html.lower()
assert "/guides/ai-receptionist/" in html and "/models/gpt-realtime-2-1/" in html
assert (P.parent/"reference.css").exists()
assert (P.parent/"reference.js").exists()
assert (P.parent/"sxf-voice-agent-evaluation-scorecard.csv").exists()
for image in ("realtime-voice-hero.svg","voice-evaluation-method.svg"):
    assert (P.parent/"images"/image).exists()
    assert image in html
s=re.search(r'<script type="application/ld\+json">(.*?)</script>',html,re.S)
assert s,"JSON-LD missing"
graph=json.loads(s.group(1))["@graph"]
types=[node["@type"] for node in graph]
assert {"TechArticle","WebPage","BreadcrumbList","FAQPage","Dataset","ImageObject"}.issubset(set(types))
assert len([n for n in graph if n["@type"]=="ImageObject"])==2
questions=[n for n in graph if n["@type"]=="FAQPage"][0]["mainEntity"]
assert len(questions)==7
assert "Try in Playground" in html
assert url in (ROOT/"sitemap.xml").read_text(encoding="utf-8")
assert "/guides/gpt-realtime-2-1-playground/" in (ROOT/"guides/index.html").read_text(encoding="utf-8")
print("PASS: SXF realtime playground guide metadata, research disclaimers, images, interactive assets, schema and discovery")
