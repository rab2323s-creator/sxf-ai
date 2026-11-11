"""Specialist Gemini Flash 3.8 vs 3.7 comparison, owned outside the generic generator.

The authored source lives in data/comparison-page-content/gemini-38-vs-37.html.
The canonical model catalog continues to provide dynamic live facts, comparable
evaluations and verified model history on every news rebuild.
"""
from __future__ import annotations

from html import escape
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
URL = "https://sxf.si/compare/gemini-3-8-flash-vs-gemini-3-7-flash/"
TITLE = "Gemini 3.8 Flash vs 3.7 Flash: Pricing & Differences | SXF / AI"
DESCRIPTION = (
    "Gemini 3.8 Flash vs 3.7 Flash: compare coding, AI agents, benchmarks, "
    "1M context and API pricing. See which to use, migration advice and SXF cost lab."
)
FAQ = [
    ("Is Gemini 3.8 Flash better than Gemini 3.7 Flash?",
     "Google positions Gemini 3.8 Flash as stronger for long-horizon coding, agents and complex multi-step reasoning. The better option on a given task depends on independently measured quality, latency and total billed tokens; 3.7 remains supported."),
    ("What is the main difference between Gemini 3.8 Flash and 3.7 Flash?",
     "Both have the same published input/output token limits and input modalities. The most consequential difference is Google's newer 3.8 Flash positioning and reported gains on complex engineering and autonomous-agent tasks."),
    ("Which is cheaper: Gemini 3.8 Flash or Gemini 3.7 Flash?",
     "Their paid Standard rates match: through December 31, 2026 both cost $0.75 per million input tokens and $3.75 per million billed output tokens. From January 1, 2027, the published rates are $1.50 and $7.50. Real task cost can differ if reasoning or tool usage differs."),
    ("Does Gemini 3.8 Flash have a larger context window than Gemini 3.7 Flash?",
     "No. Google documents 1,048,576 input tokens and up to 65,536 output tokens for both models."),
    ("Should I migrate from Gemini 3.7 Flash to 3.8 Flash?",
     "Test 3.8 on representative tasks and compare task completion, tool correctness, output token usage, latency and error rates before migrating. Google states that 3.7 Flash remains supported, so migration need not be automatic."),
    ("What are the Gemini 3.8 Flash and 3.7 Flash API model IDs?",
     "Use gemini-3.8-flash and gemini-3.7-flash respectively. Explicit IDs help keep an A/B evaluation reproducible."),
    ("Do both models accept images, video, audio and PDFs?",
     "Yes. Both accept text, image, video, audio and PDF inputs and output text. Dedicated image generation and text-to-speech endpoints are separate models."),
    ("Can I use Gemini Flash for coding agents and tool calling?",
     "Both support function calling, structured outputs and code execution. Tool reliability and successful-task cost should be measured for your own agent workflow."),
    ("Does SXF run its own Gemini 3.8 vs 3.7 benchmark?",
     "No. SXF distinguishes vendor claims from versioned third-party evidence in its evaluation dataset and provides a transparent calculation tool. The site does not claim an original head-to-head performance benchmark."),
]


def faq_markup() -> str:
    cards = "".join(
        "<details><summary>" + escape(question) + "</summary><p>" + escape(answer) + "</p></details>"
        for question, answer in FAQ
    )
    return (
        '<section class="gf-section" id="gf-faq" aria-labelledby="gf-faq-title">'
        '<div class="gf-section-head"><p class="eyebrow">GEMINI 3.8 VS 3.7 FLASH FAQ</p>'
        '<h2 id="gf-faq-title">Gemini Flash upgrade questions, answered</h2>'
        '<p>Direct, concise answers; source details and limitations are linked throughout the guide.</p>'
        '</div><div class="gf-faq-list">' + cards + "</div></section>"
    )


def render_page(*, page_head, page_header, page_footer, live_facts, evaluations,
                changes, related_html, verified):
    source = (ROOT / "data/comparison-page-content/gemini-38-vs-37.html").read_text(encoding="utf-8")
    if source.count("{{GF_FAQ}}") != 1 or source.count("<!-- SXF_GEMINI_FLASH_LIVE_FACTS -->") != 1:
        raise RuntimeError("Gemini comparison editorial template is missing its required markers")
    source = source.replace("{{GF_FAQ}}", faq_markup())
    source = source.replace("<!-- SXF_GEMINI_FLASH_LIVE_FACTS -->", live_facts)
    # Keep evaluation observations and model history dynamically generated rather
    # than duplicating numbers or freezing updates in the authored HTML.
    marker = '  <section class="gf-section" id="gf-use-cases"'
    if source.count(marker) != 1:
        raise RuntimeError("Cannot locate Gemini evaluation slot")
    source = source.replace(marker, evaluations + "\n" + marker, 1)
    schema = {
        "@context": "https://schema.org", "@graph": [
            {
                "@type": "TechArticle", "@id": URL + "#article",
                "headline": "Gemini 3.8 Flash vs Gemini 3.7 Flash: differences, API pricing and which to use",
                "description": DESCRIPTION, "url": URL,
                "mainEntityOfPage": {"@id": URL + "#webpage"},
                "dateModified": "2026-11-11", "inLanguage": "en",
                "author": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
                "about": [
                    {"@type": "Thing", "name": "Gemini 3.8 Flash",
                     "sameAs": "https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash"},
                    {"@type": "Thing", "name": "Gemini 3.7 Flash",
                     "sameAs": "https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash"},
                ],
                "citation": [
                    "https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash",
                    "https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash",
                    "https://ai.google.dev/gemini-api/docs/pricing",
                    "https://blog.google/innovation-and-ai/models-and-research/gemini-models/3-8-flash-and-3-8-flash-cyber/",
                    "https://ai.google.dev/gemini-api/docs/whats-new-gemini-3.8",
                    "https://deepmind.google/models/model-cards/gemini-3-8-flash/",
                    "https://artificialanalysis.ai/methodology/intelligence-benchmarking",
                ],
            },
            {
                "@type": "WebPage", "@id": URL + "#webpage", "url": URL, "name": TITLE,
                "isPartOf": {"@id": "https://sxf.si/#website"},
                "mainEntity": {"@id": URL + "#article"}, "inLanguage": "en",
            },
            {
                "@type": "BreadcrumbList", "@id": URL + "#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": "https://sxf.si/"},
                    {"@type": "ListItem", "position": 2, "name": "Compare", "item": "https://sxf.si/compare/"},
                    {"@type": "ListItem", "position": 3, "name": "Gemini 3.8 vs 3.7 Flash", "item": URL},
                ],
            },
            {
                "@type": "FAQPage", "@id": URL + "#faq",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q, a in FAQ
                ],
            },
        ],
    }
    head = page_head(TITLE, DESCRIPTION, URL, schema, page_type="article")
    head = head.replace(
        "</head>",
        '<link rel="stylesheet" href="/assets/gemini-flash-comparison.css" />\n</head>', 1
    )
    return (
        '<!doctype html><html lang="en">' + head
        + '<body class="intel-page comparison-page compare-v2-page gemini-specialist-comparison">'
        + page_header("compare")
        + '<main><section class="comparison-hero shell">'
        + '<nav class="intel-breadcrumb"><a href="/">SXF</a><span>/</span>'
        + '<a href="/compare/">Compare</a><span>/</span><span>Gemini 3.8 vs 3.7 Flash</span></nav>'
        + '<p class="eyebrow">GOOGLE GEMINI FLASH API · HEAD-TO-HEAD</p>'
        + '<h1>Gemini 3.8 Flash vs Gemini 3.7 Flash<br><span>Pricing, Benchmarks &amp; Which to Choose</span></h1>'
        + '<p>Compare Google Gemini Flash versions on coding, agents, 1M context, '
        + 'official API prices, evidence quality and migration tradeoffs. '
        + 'Use SXF’s scenario calculator to estimate real-workload token economics.</p>'
        + '<div class="comparison-meta">'
        + '<div><span>PROVIDER</span><strong>Google AI</strong></div>'
        + '<div><span>CONTEXT</span><strong>1,048,576 each</strong></div>'
        + '<div><span>STANDARD RATES</span><strong>$0.75 input / $3.75 output per MTok, each</strong></div>'
        + '</div></section>'
        + source + changes
        + '<section class="compare-v2-related shell">'
        + '<div class="intel-section-head"><div><p class="eyebrow">RELATED MATCHUPS · GEMINI AND AI MODEL COMPARISONS</p>'
        + '<h2>Continue the model-selection decision.</h2></div><a href="/compare/">All comparisons ↗</a></div>'
        + '<div class="model-related-links">'
        + '<a href="/models/gemini/"><span>GEMINI FAMILY HUB</span><strong>Google Gemini versions, prices and API models</strong><b>↗</b></a>'
        + '<a href="/models/gemini-3-8-flash/"><span>MODEL REFERENCE</span><strong>Gemini 3.8 Flash: model, API and pricing</strong><b>↗</b></a>'
        + '<a href="/models/gemini-3-7-flash/"><span>MODEL REFERENCE</span><strong>Gemini 3.7 Flash: context, pricing and API</strong><b>↗</b></a>'
        + related_html + '</div></section></main>'
        + page_footer()
        + '<script defer src="/assets/gemini-flash-comparison.js"></script>'
        + '</body></html>'
    )
