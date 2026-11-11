"""Stable, source-led Gemini family landing page and reciprocal discovery links.

The feed builder owns models/gemini/index.html. This module injects authored
evergreen material from data/model-page-content/gemini-family.html on every run.
The dynamic signal timeline and history are retained from the existing builder.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
URL = "https://sxf.si/models/gemini/"
TITLE = "Google Gemini Models (2026): Compare Versions, API Pricing & Features | SXF / AI"
DESCRIPTION = ("Compare Google Gemini 4, 3.8 Flash, Flash-Lite, Live, TTS, Nano Banana "
               "and Embedding models. API prices, model IDs, use cases and SXF cost calculator.")
FAQ = [
    ("What is Google Gemini?", "Gemini is Google's family of multimodal AI models. Individual model endpoints differ in text reasoning, image creation, audio, embeddings, context windows, availability and API pricing."),
    ("Which Gemini model should I use?", "For a general-purpose text-output API start by testing Gemini 3.8 Flash. Test Gemini 4 Argon or Carbon for more difficult reasoning; use Flash-Lite for economical throughput. Use dedicated Live, TTS, image and embedding models for those output types."),
    ("What is the latest Gemini model in November 2026?", "Google announced Gemini 4 Carbon on November 10, 2026, after Gemini 4 Argon. The latest appropriate choice depends on whether you need frontier reasoning, Flash efficiency, realtime voice or generated media."),
    ("How much does Gemini 3.8 Flash cost?", "As of November 11, 2026, Google's paid Standard introductory Gemini 3.8 Flash text-token price is $0.75 per million input tokens and $3.75 per million output tokens through December 31, 2026. It changes to $1.50 and $7.50 on January 1, 2027. Other modalities and tool services have separate charges."),
    ("Is the Gemini API free?", "Google offers free-tier access for some Gemini models with limitations. Not all models, capacities or features qualify. Check the current model-specific free and paid tiers and rate limits in Google's pricing documentation."),
    ("What is the difference between Gemini, Google AI Studio and the Gemini API?", "Gemini is the model family and name of Google's consumer assistant. Google AI Studio is a developer workspace; the Gemini API is programmatic access to specific model IDs. A consumer Gemini subscription does not represent API token pricing."),
    ("What is the difference between Gemini Flash and Flash-Lite?", "Flash is positioned for more demanding general agent, coding and multimodal tasks. Flash-Lite prioritizes economical, high-throughput processing. Compare latency, quality and cost on your workload before choosing."),
    ("Can Gemini generate images or speech?", "Some Gemini-branded specialized endpoints generate images, speech or live audio. Standard Gemini 3.8 Flash accepts multiple input types but returns text; use dedicated Nano Banana, TTS or Live endpoints when the required output is not text."),
    ("What is the Gemini 3.8 Flash context window?", "Google documents up to 1,048,576 input tokens and up to 65,536 output tokens for Gemini 3.8 Flash. Other Gemini models have their own limits."),
    ("How do I access the Gemini API?", "Create or obtain an API key in Google AI Studio, choose an available model ID, use Google's supported SDK or HTTP API, and follow Google's quickstart and rate limit documentation."),
    ("What are Gemini Embedding 001 and Embedding 2 for?", "Gemini Embedding 001 creates text vector representations. Gemini Embedding 2 supports multimodal representations for semantic retrieval and RAG. They are embedding models, not conversational text generators."),
    ("How do I migrate from older Gemini models?", "Pin your model ID, check Google's official deprecation and migration guides, then test output format, thinking configurations, tool calls, token usage and latency before changing production traffic."),
]


def faq_markup() -> str:
    rows = "".join(
        '<details><summary>' + escape(question) + '</summary><p>' + escape(answer) +
        '</p></details>' for question, answer in FAQ
    )
    return ('<section class="gemini-section gemini-faq" id="gemini-faq" '
            'aria-labelledby="gemini-faq-heading"><div class="gemini-section-heading">'
            '<p class="eyebrow">COMMON GOOGLE GEMINI QUESTIONS</p>'
            '<h2 id="gemini-faq-heading">Google Gemini FAQ: direct answers</h2>'
            '<p>Short, model-specific answers to the questions developers and '
            'researchers search for most often.</p></div>'
            '<div class="gemini-faq-list">' + rows + '</div></section>')


def enrich_gemini_family_page(page: str) -> str:
    if 'data-sxf-gemini-guide' in page:
        return page
    content = (ROOT / "data/model-page-content/gemini-family.html").read_text(encoding="utf-8")
    assert content.count("{{GEMINI_FAQ}}") == 1
    content = content.replace("{{GEMINI_FAQ}}", faq_markup())
    assert page.count('</head>') == page.count('<main>') == 1
    page = re.sub(r'<title>.*?</title>', '<title>' + escape(TITLE) + '</title>', page, count=1, flags=re.S)
    page = re.sub(r'<meta name="description" content="[^"]*"\s*/>', '<meta name="description" content="' + escape(DESCRIPTION, quote=True) + '" />', page, count=1)
    for prop in ("og:title", "twitter:title"):
        page = re.sub(r'(<meta (?:name|property)="' + prop + r'" content=")[^"]*(")', lambda m: m.group(1) + escape(TITLE, quote=True) + m.group(2), page, count=1)
    for prop in ("og:description", "twitter:description"):
        page = re.sub(r'(<meta (?:name|property)="' + prop + r'" content=")[^"]*(")', lambda m: m.group(1) + escape(DESCRIPTION, quote=True) + m.group(2), page, count=1)
    graph = [
        {"@type": "CollectionPage", "@id": URL + "#webpage", "url": URL,
         "name": "Google Gemini models, API pricing and comparisons | SXF / AI",
         "description": DESCRIPTION, "inLanguage": "en",
         "isPartOf": {"@id": "https://sxf.si/#website"},
         "about": {"@type": "Thing", "name": "Google Gemini",
                   "sameAs": "https://ai.google.dev/gemini-api/docs/models"},
         "mainEntity": {"@id": URL + "#models"}, "dateModified": "2026-11-11"},
        {"@type": "BreadcrumbList", "@id": URL + "#breadcrumbs", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": "https://sxf.si/"},
            {"@type": "ListItem", "position": 2, "name": "Models", "item": "https://sxf.si/models/"},
            {"@type": "ListItem", "position": 3, "name": "Gemini", "item": URL},
        ]},
        {"@type": "ItemList", "@id": URL + "#models", "name": "SXF Gemini model family references",
         "numberOfItems": 9, "itemListElement": [
             {"@type": "ListItem", "position": i + 1, "name": name, "url": "https://sxf.si" + path}
             for i, (name, path) in enumerate([
                 ("Gemini 4", "/models/gemini-4/"),
                 ("Gemini 3.8 Flash", "/models/gemini-3-8-flash/"),
                 ("Gemini 3.7 Flash", "/models/gemini-3-7-flash/"),
                 ("Gemini 3.5 Flash-Lite", "/models/gemini-3-5-flash-lite/"),
                 ("Gemini 3.8 Live", "/models/gemini-3-8-live/"),
                 ("Gemini 3.8 Flash TTS", "/models/gemini-3-8-flash-tts/"),
                 ("Nano Banana 2.1", "/models/gemini-nano-banana-2-1/"),
                 ("Gemini Embedding 001", "/models/gemini-embedding-001/"),
                 ("Gemini Embedding 2", "/models/gemini-embedding-2/"),
             ])
         ]},
        {"@type": "FAQPage", "@id": URL + "#faq", "mainEntity": [
            {"@type": "Question", "name": question, "acceptedAnswer": {"@type": "Answer", "text": answer}}
            for question, answer in FAQ
        ]},
    ]
    schema = json.dumps({"@context": "https://schema.org", "@graph": graph},
                        ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    page, count = re.subn(
        r'<script type="application/ld\+json">.*?</script>',
        lambda _: '<script type="application/ld+json">' + schema + '</script>',
        page, count=1, flags=re.S)
    assert count == 1
    page = page.replace('</head>',
        '  <link rel="stylesheet" href="/assets/gemini-family.css" />\n</head>', 1)
    page = page.replace('<p class="eyebrow">MODEL INTELLIGENCE</p><h1>Gemini<br><span>release signals.</span></h1>',
        '<p class="eyebrow">GOOGLE GEMINI MODEL FAMILY · SXF REFERENCE</p>'
        '<h1>Google Gemini models<br><span>compared for 2026.</span></h1>', 1)
    page = page.replace('<section class="signal-layout shell">',
        content + '\n<section class="signal-layout shell">', 1)
    page = page.replace('<section class="related-signals shell">',
        '<section class="related-signals shell" id="gemini-news">', 1)
    page = page.replace('</body>',
        '<script defer src="/assets/gemini-family.js"></script></body>', 1)
    return page


def add_gemini_discovery_links(root: Path) -> None:
    """Reapply reciprocal links on every regeneration, without accumulating duplicates."""
    snippets = {
        "models/index.html": (
            '<section class="shell" data-gemini-hub-link aria-label="Google Gemini family reference">'
            '<div class="model-related-links"><a href="/models/gemini/"><span>GOOGLE GEMINI FAMILY</span>'
            '<strong>Compare Gemini versions, API pricing, modalities and the SXF cost lab</strong><b>↗</b></a></div></section>'),
        "providers/google/index.html": (
            '<section class="shell" data-gemini-hub-link aria-label="Google Gemini model family guide">'
            '<div class="model-related-links"><a href="/models/gemini/"><span>FAMILY HUB</span>'
            '<strong>Google Gemini: model versions, API prices, voice, images and embeddings</strong><b>↗</b></a></div></section>'),
        "models/gemini-3-8-flash/index.html": (
            '<aside class="shell" data-gemini-hub-link aria-label="Gemini family navigation">'
            '<p>Comparing the full Gemini family? <a href="/models/gemini/">Explore the Gemini models, API pricing and use-case selector</a>.</p></aside>'),
        "models/gemini-4/index.html": (
            '<aside class="shell" data-gemini-hub-link aria-label="Gemini family navigation">'
            '<p>Compare Gemini 4 with Flash, Live, image and embedding models in the '
            '<a href="/models/gemini/">Gemini family guide</a>.</p></aside>'),
        "models/gemini-embedding-001/index.html": (
            '<aside class="shell" data-gemini-hub-link aria-label="Gemini family navigation">'
            '<p>Need multimodal embeddings or a generative model? See the '
            '<a href="/models/gemini/">Gemini model family and selection guide</a>.</p></aside>'),
        "models/gemini-3-8-flash-tts/index.html": (
            '<aside class="shell" data-gemini-hub-link aria-label="Gemini family navigation">'
            '<p>See how Gemini speech models differ from text, Live and image endpoints: '
            '<a href="/models/gemini/">Gemini model family guide</a>.</p></aside>'),
    }
    for rel, snippet in snippets.items():
        path = root / rel
        if not path.is_file():
            raise RuntimeError(f"Gemini discovery target missing: {rel}")
        html = path.read_text(encoding="utf-8")
        if 'data-gemini-hub-link' in html:
            continue
        if html.count("</main>") != 1:
            raise RuntimeError(f"Gemini discovery target main tag changed: {rel}")
        if rel in {"models/index.html", "providers/google/index.html"}:
            # Put the family hub immediately after the page hero, not below huge tables.
            if "</section>" not in html:
                raise RuntimeError(f"Gemini discovery target hero missing: {rel}")
            html = html.replace("</section>", "</section>" + snippet, 1)
        else:
            html = html.replace("</main>", snippet + "</main>", 1)
        path.write_text(html, encoding="utf-8")
