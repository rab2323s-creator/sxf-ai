"""SXF owned GPT-6 Sol vs Gemini 3.8 Flash SEO/developer decision guide.

Called after inject_compare_contract; preserves live catalog, matched evaluation
observations, model history, existing FAQ, sources and editorial signals.
Authored fragments belong in data/comparison-page-content/gpt6-sol-vs-gemini-38.html.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
URL = "https://sxf.si/compare/gpt-6-sol-vs-gemini-3-8-flash/"
TITLE = "GPT-6 Sol vs Gemini 3.8 Flash: Pricing, Coding & API | SXF / AI"
DESCRIPTION = ("Compare GPT-6 Sol vs Gemini 3.8 Flash on API pricing, coding, agents, "
               "reasoning and multimodal inputs. Try SXF's cost-per-success calculator.")
H1 = ("GPT-6 Sol vs Gemini 3.8 Flash<br>"
      "<span>API Pricing, Coding &amp; Which to Choose</span>")


def enrich_sol_vs_gemini(html: str) -> str:
    if 'data-sxf-sol-gemini-guide="1"' in html:
        return html
    template = (ROOT / "data/comparison-page-content/gpt6-sol-vs-gemini-38.html").read_text(encoding="utf-8")
    markers = ("<!-- SXF_SLOT_TOP -->", "<!-- SXF_SLOT_BENCH -->",
               "<!-- SXF_SLOT_LAB -->", "<!-- SXF_SLOT_METHOD -->")
    for marker in markers:
        if template.count(marker) != 1:
            raise RuntimeError(f"Sol/Gemini authored content missing marker {marker}")
    top = template.split(markers[0], 1)[1].split(markers[1], 1)[0]
    bench = template.split(markers[1], 1)[1].split(markers[2], 1)[0]
    lab = template.split(markers[2], 1)[1].split(markers[3], 1)[0]
    method = template.split(markers[3], 1)[1]

    if html.count("<h1>") != 1:
        raise RuntimeError("Unexpected Sol/Gemini hero headings")
    html = re.sub(r'<h1>GPT-6 Sol<br><span>vs Gemini 3\.8 Flash\.</span></h1>',
                  lambda _: "<h1>" + H1 + "</h1>", html, count=1)
    html = re.sub(r'<title>.*?</title>', '<title>' + escape(TITLE) + '</title>',
                  html, count=1, flags=re.S)
    html = re.sub(r'(<meta name="description" content=")[^"]*(")',
                  lambda m: m.group(1) + escape(DESCRIPTION, quote=True) + m.group(2),
                  html, count=1)
    for prop, value in (("og:title", TITLE), ("twitter:title", TITLE),
                        ("og:description", DESCRIPTION), ("twitter:description", DESCRIPTION)):
        pat = r'(<meta (?:property|name)="' + prop + r'" content=")[^"]*(")'
        html, count = re.subn(pat, lambda m: m.group(1) + escape(value, quote=True) + m.group(2),
                              html, count=1)
        if count != 1:
            raise RuntimeError(f"Sol/Gemini head property missing: {prop}")

    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, flags=re.S)
    if not match:
        raise RuntimeError("Sol/Gemini JSON-LD missing")
    graph = json.loads(match.group(1))
    if "WebPage" not in {x.get("@type") for x in graph.get("@graph", [])}:
        raise RuntimeError("Sol/Gemini WebPage graph missing")
    page = next(x for x in graph["@graph"] if x.get("@type") == "WebPage")
    page["name"] = TITLE
    page["description"] = DESCRIPTION
    page["mainEntity"] = {"@id": URL + "#article"}
    graph["@graph"].append({
        "@type": "TechArticle", "@id": URL + "#article",
        "headline": "GPT-6 Sol vs Gemini 3.8 Flash: pricing, reasoning, coding and model choice",
        "description": DESCRIPTION,
        "url": URL, "mainEntityOfPage": {"@id": URL + "#webpage"},
        "inLanguage": "en",
        "dateModified": "2026-11-11",
        "author": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "about": [
            {"@type": "Thing", "name": "GPT-6 Sol", "sameAs": "https://developers.openai.com/api/docs/models/gpt-6-sol"},
            {"@type": "Thing", "name": "Gemini 3.8 Flash", "sameAs": "https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash"},
        ],
        "citation": [
            "https://developers.openai.com/api/docs/models/gpt-6-sol",
            "https://developers.openai.com/api/docs/pricing",
            "https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash",
            "https://ai.google.dev/gemini-api/docs/pricing",
            "https://artificialanalysis.ai/methodology/intelligence-benchmarking",
            "https://deepmind.google/models/model-cards/gemini-3-8-flash/",
        ],
    })
    schema = json.dumps(graph, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html = html[:match.start(1)] + schema + html[match.end(1):]

    if html.count('id="quick-answer"') != 1 or html.count('id="specs"') != 1:
        raise RuntimeError("Sol/Gemini quick answer anchor changed")
    # Existing decision summary is replaced, not duplicated.
    quick = re.compile(r'<section id="quick-answer" class="model-deep-section shell">.*?</section>', re.S)
    html, n = quick.subn("", html, count=1)
    if n != 1:
        raise RuntimeError("Sol/Gemini old quick answer changed")
    hero_end = '</section><section class="compare-live-facts shell"'
    if html.count(hero_end) != 1:
        raise RuntimeError("Sol/Gemini hero/compare live facts boundary changed")
    html = html.replace(hero_end, '</section>' + top + '<section class="compare-live-facts shell"', 1)
    spec_marker = '<section id="specs" class="comparison-table-section shell">'
    if html.count(spec_marker) != 1:
        raise RuntimeError("Sol/Gemini specification section missing")
    html = html.replace(spec_marker, bench + spec_marker, 1)
    cost_end = '<section class="model-deep-section model-split shell">'
    if html.count(cost_end) < 1:
        raise RuntimeError("Sol/Gemini long context section missing")
    html = html.replace(cost_end, lab + cost_end, 1)
    tail_marker = '<div class="model-reference-lower shell">'
    if html.count(tail_marker) != 1:
        raise RuntimeError("Sol/Gemini related and source section missing")
    html = html.replace(tail_marker, method + tail_marker, 1)
    html = html.replace('</head>',
        '<link rel="stylesheet" href="/assets/sol-vs-gemini.css" />\n</head>', 1)
    html = html.replace('</body>',
        '<script defer src="/assets/sol-vs-gemini.js"></script></body>', 1)
    return html
