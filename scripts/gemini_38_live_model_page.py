"""Source-backed Gemini 3.8 Live SEO enrichment for the generated model page.

The canonical model catalog owns model facts and history; this module inserts
audited editorial guidance on each site rebuild without changing the route.
"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "data/model-page-content/gemini-3-8-live-seo.html"
CANONICAL = "https://sxf.si/models/gemini-3-8-live/"
TITLE = "Gemini 3.8 Live API: Voice Agents, Pricing & Python | SXF"
DESCRIPTION = (
    "Gemini 3.8 Live API guide: native voice agents, WebSocket Python setup, "
    "audio pricing calculator, async tools, session limits and Extended Thinking comparison."
)
HERO = (
    "Build low-latency voice agents with Gemini 3.8 Live. Explore native audio, "
    "Google's Live API, Python streaming, voice costs and session management."
)
SOURCES = [
    "https://ai.google.dev/gemini-api/docs/models/gemini-3.8-live",
    "https://ai.google.dev/gemini-api/docs/pricing",
    "https://ai.google.dev/gemini-api/docs/live-api/get-started-sdk",
    "https://ai.google.dev/gemini-api/docs/live-api/capabilities",
    "https://ai.google.dev/gemini-api/docs/live-api/session-management",
    "https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-8-live-gemini-3-8-live-extended-thinking/",
]
FAQS = [
    ("What is the Gemini 3.8 Live API model ID?",
     "Use gemini-3.8-live with Google's Gemini Live API for real-time bidirectional speech and tool calls."),
    ("Is Gemini 3.8 Live free?",
     "Google offers a free tier subject to limits. Standard paid pricing depends on whether usage is text, input audio, output audio or image/video."),
    ("How much does a Gemini 3.8 Live voice session cost?",
     "Google lists approximate audio charges of $0.005 per input minute and $0.018 per output minute. Five input minutes and three output minutes cost about $0.079 for audio alone."),
    ("Can Gemini 3.8 Live call tools without interrupting speech?",
     "Yes. Non-blocking asynchronous function calling is supported and is the default mode. Apps must authorize consequential tool actions."),
    ("Can I set thinking_level on Gemini 3.8 Live?",
     "No. Google says thinking_config and thinking_level are unsupported on the standard Gemini 3.8 Live model; the Extended Thinking variant supports configurable reasoning."),
    ("Is Gemini 3.8 Live the same as Gemini 3.8 Flash TTS?",
     "No. Gemini Live handles interactive voice sessions with bidirectional real-time input, while Flash TTS generates audio from supplied text."),
]
INSERT = '<section class="model-deep-section"><div class="model-section-head"><p class="eyebrow">CAVEATS</p>'
H1 = '<h1>Gemini 3.8 Live<br><span>verified model reference.</span></h1>'

def replace_once(page: str, before: str, after: str, label: str) -> str:
    occurrences = page.count(before)
    if occurrences != 1:
        raise ValueError(f"Gemini 3.8 Live: {label} count is {occurrences}, expected one")
    return page.replace(before, after, 1)


def replace_meta(page: str, name: str, value: str) -> str:
    selector = "property" if name.startswith("og:") else "name"
    pattern = r'(<meta ' + selector + r'="' + re.escape(name) + r'" content=")[^"]*(")'
    updated, count = re.subn(
        pattern, lambda match: match.group(1) + escape(value, quote=True) + match.group(2),
        page, count=1,
    )
    if count != 1:
        raise ValueError(f"Gemini 3.8 Live: missing SEO meta {name}")
    return updated


def enrich_gemini_38_live_page(page: str) -> str:
    if page.count('rel="canonical" href="' + CANONICAL + '"') != 1:
        raise ValueError("Gemini 3.8 Live: unexpected canonical; refusing to overwrite")
    fragment = CONTENT.read_text(encoding="utf-8").strip()
    if fragment.count("data-g38-live-guide") != 1 or fragment.count('id="g38-live-faq"') != 1:
        raise ValueError("Gemini 3.8 Live: editorial source integrity failure")

    page = replace_once(
        page, "<title>Gemini 3.8 Live — API Specs, Context &amp; Pricing | SXF / AI</title>",
        "<title>" + escape(TITLE) + "</title>", "title",
    )
    for key, value in (
        ("description", DESCRIPTION), ("og:title", TITLE),
        ("og:description", DESCRIPTION), ("twitter:title", TITLE),
        ("twitter:description", DESCRIPTION),
    ):
        page = replace_meta(page, key, value)

    page = replace_once(
        page, H1,
        '<h1>Gemini 3.8 Live<br><span>API, pricing &amp; real-time voice agents.</span></h1>',
        "H1",
    )
    page = replace_once(
        page,
        "<p>Google&#x27;s stable low-latency native-audio Live API model for voice agents with asynchronous function calling and multimodal inputs.</p>",
        "<p>" + escape(HERO) + "</p>",
        "hero introduction",
    )
    page = replace_once(
        page,
        '<div><strong>131,072</strong><span>context tokens</span></div>',
        '<div><strong>131K</strong><span>input context tokens</span></div>',
        "hero context",
    )
    page = replace_once(
        page,
        '<div><strong>65,536</strong><span>max output</span></div>',
        '<div><strong>$0.005/min</strong><span>estimated audio input rate</span></div>',
        "hero audio",
    )
    page = replace_once(
        page,
        '<div><span>KNOWLEDGE CUTOFF</span><strong>Not published</strong></div>',
        '<div><span>AUDIO INPUT</span><strong>$3.00</strong><small>per 1M audio tokens</small></div>',
        "audio input",
    )
    page = replace_once(
        page,
        '<article><span>REASONING</span><h3>supported</h3><p>Only provider-documented reasoning controls are shown; missing controls remain unpublished rather than inferred.</p></article>',
        '<article><span>REASONING MODE</span><h3>Interleaved</h3><p>Google says standard Live does not accept thinking_level or thinking_config. Use Extended Thinking for configurable reasoning.</p></article>',
        "reasoning distinction",
    )
    page = replace_once(
        page,
        '<p>SXF preserves the provider-published native billing basis. Only calculator-eligible generative token models enter token-cost arithmetic; specialist units and input-only embeddings remain visible without forced conversion.</p>',
        '<p>Real-time audio and image/video are billed separately from text tokens. The SXF estimator below models audio minutes using Google’s approximate equivalents; token-only arithmetic does not capture complete voice-session cost.</p>',
        "media economics",
    )
    page = replace_once(page, INSERT, fragment + "\n\n        " + INSERT, "editorial insert")
    page = replace_once(
        page, "</head>",
        '<link rel="stylesheet" href="/assets/gemini-38-live-guide.css" />\n    </head>',
        "editorial CSS",
    )
    page = replace_once(
        page, "</body>",
        '<script src="/assets/gemini-38-live-calculator.js" defer></script>\n    </body>',
        "calculator JavaScript",
    )

    schema_match = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', page, re.S)
    if not schema_match:
        raise ValueError("Gemini 3.8 Live: JSON-LD unavailable")
    graph = json.loads(schema_match.group(2))
    if graph.get("@context") != "https://schema.org":
        raise ValueError("Gemini 3.8 Live: unexpected JSON-LD context")
    article = next((n for n in graph["@graph"] if n.get("@type") == "TechArticle"), None)
    if article is None:
        raise ValueError("Gemini 3.8 Live: missing TechArticle")
    article.update({
        "headline": TITLE.removesuffix(" | SXF"),
        "description": DESCRIPTION,
        "dateModified": "2026-11-07",
        "citation": SOURCES,
        "mainEntityOfPage": {"@type": "WebPage", "@id": CANONICAL},
        "author": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "publisher": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "keywords": [
            "Gemini 3.8 Live", "Gemini 3.8 Live API", "Gemini Live pricing",
            "Gemini Live API Python", "Gemini voice agents",
            "Gemini 3.8 Live vs Extended Thinking",
        ],
    })
    graph["@graph"].append({
        "@type": "FAQPage", "@id": CANONICAL + "#faq",
        "url": CANONICAL + "#g38-live-faq",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in FAQS
        ],
    })
    graph_json = json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
    return page[:schema_match.start(2)] + graph_json + page[schema_match.end(2):]
