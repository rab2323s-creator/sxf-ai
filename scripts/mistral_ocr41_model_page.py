"""Durable, primary-source-backed SEO enrichment for generated Mistral OCR 4.1.

The canonical model catalog remains the owner of the model price and history.
This source-backed editorial fragment is reinserted during every site rebuild.
"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "data/model-page-content/mistral-ocr-4-1-seo.html"
URL = "https://sxf.si/models/mistral-ocr-4-1/"
TITLE = "Mistral OCR 4.1: API, Pricing, PDF & Tables | SXF"
DESCRIPTION = (
    "Mistral OCR 4.1 API guide: $0.004/page pricing, PDF extraction, "
    "tables, bounding boxes, confidence scores, Python examples and SXF cost calculator."
)
SOURCES = [
    "https://docs.mistral.ai/models/ocr-4-1",
    "https://docs.mistral.ai/studio/document-processing/basic_ocr",
    "https://docs.mistral.ai/inference/pricing",
    "https://docs.mistral.ai/studio/document-processing/annotations",
    "https://docs.mistral.ai/resources/changelogs",
    "https://docs.mistral.ai/api/endpoint/ocr",
    "https://docs.mistral.ai/studio/document-processing/document_qna",
]
FAQ = [
    ("What is the Mistral OCR 4.1 API model ID?",
     "Use mistral-ocr-4-1 through client.ocr.process() or POST /v1/ocr. The mistral-ocr-latest alias currently resolves to OCR 4.1 but can change."),
    ("How much does Mistral OCR 4.1 cost per page?",
     "Mistral publishes $4 per 1,000 Standard OCR pages ($0.004 per page), and separately lists $5 per 1,000 annotated pages ($0.005 per page). Confirm request and billing eligibility."),
    ("Can Mistral OCR 4.1 extract PDF tables?",
     "Yes. table_format can be markdown or html, returning separate table structures and references which need value and layout verification."),
    ("Does Mistral OCR 4.1 return bounding boxes?",
     "Yes. include_blocks=True returns blocks with type, content and document-region coordinates."),
    ("What confidence scores does OCR 4.1 support?",
     "The confidence_scores_granularity option supports page, block and word. Block mode needs include_blocks=True. Scores guide checks but do not guarantee correctness."),
    ("Is Mistral OCR 4.1 open source?",
     "Mistral markets OCR 4.1 as a GA Premier hosted Document AI service rather than downloadable open weights."),
    ("What changed from Mistral OCR 4.0 to OCR 4.1?",
     "OCR 4.1 adds block-level confidence granularity while retaining OCR block extraction. Mistral recommends moving from deprecated OCR 4.0 to OCR 4.1."),
    ("Can Mistral OCR 4.1 be used with RAG?",
     "Yes, as a document-extraction stage. Secure RAG also needs source/page provenance, correct table parsing, permission filters and retrieval evaluation."),
]
OLD_CAVEATS = '<section class="model-deep-section"><div class="model-section-head"><p class="eyebrow">CAVEATS</p>'
OLD_H1 = '<h1>OCR 4.1<br><span>verified model reference.</span></h1>'


def replace_once(page: str, old: str, new: str, label: str) -> str:
    count = page.count(old)
    if count != 1:
        raise ValueError(f"OCR 4.1 {label}: expected 1 occurrence, got {count}")
    return page.replace(old, new, 1)


def update_meta(page: str, name: str, value: str) -> str:
    attribute = "property" if name.startswith("og:") else "name"
    regex = r'(<meta ' + attribute + r'="' + re.escape(name) + r'" content=")[^"]*(")'
    updated, n = re.subn(
        regex,
        lambda m: m.group(1) + escape(value, quote=True) + m.group(2),
        page,
        count=1,
    )
    if n != 1:
        raise ValueError(f"OCR 4.1 missing metadata: {name}")
    return updated


def enrich_mistral_ocr_41_page(page: str) -> str:
    if page.count('rel="canonical" href="' + URL + '"') != 1:
        raise ValueError("OCR 4.1 canonical mismatch: refusing to enrich unrelated page")
    fragment = CONTENT.read_text(encoding="utf-8").strip()
    if fragment.count("data-mocr41-guide") != 1 or fragment.count('id="mocr41-faq"') != 1:
        raise ValueError("Missing OCR 4.1 authored editorial content")

    page = replace_once(
        page,
        "<title>OCR 4.1 — API Specs, Context &amp; Pricing | SXF / AI</title>",
        "<title>" + escape(TITLE) + "</title>",
        "SEO title",
    )
    for name, value in (
        ("description", DESCRIPTION),
        ("og:title", TITLE), ("og:description", DESCRIPTION),
        ("twitter:title", TITLE), ("twitter:description", DESCRIPTION),
    ):
        page = update_meta(page, name, value)
    page = replace_once(
        page,
        OLD_H1,
        '<h1>Mistral OCR 4.1<br><span>PDF API, pricing &amp; tables.</span></h1>',
        "H1",
    )
    page = replace_once(
        page,
        '<p>Latest GA Mistral Document AI OCR service for text and structured-content extraction from documents and images.</p>',
        '<p>Mistral OCR 4.1 PDF and image extraction: $4 per 1,000 pages, tables, bounding boxes, block confidence, Python and API integration.</p>',
        "hero",
    )
    page = replace_once(
        page,
        '<div><strong>Not published</strong><span>context not published</span></div>',
        '<div><strong>$0.004</strong><span>Standard OCR per page</span></div>',
        "hero price",
    )
    page = replace_once(
        page,
        '<div><strong>Not published</strong><span>max output</span></div>',
        '<div><strong>$0.005</strong><span>listed annotated-page rate</span></div>',
        "hero annotation price",
    )
    page = replace_once(
        page,
        '<div><span>CONTEXT WINDOW</span><strong>Not published</strong></div>',
        '<div><span>PROCESSING UNIT</span><strong>PDF page</strong><small>not conversational tokens</small></div>',
        "model fact",
    )
    page = replace_once(
        page,
        '<div><span>MAX OUTPUT</span><strong>Not published</strong></div>',
        '<div><span>STRUCTURED OUTPUT</span><strong>Markdown + blocks</strong><small>tables and coordinates optional</small></div>',
        "structured output",
    )
    page = replace_once(
        page,
        '<div><span>KNOWLEDGE CUTOFF</span><strong>Not published</strong></div>',
        '<div><span>MODEL STATUS</span><strong>GA Premier</strong><small>hosted Mistral Document AI</small></div>',
        "status",
    )
    page = replace_once(
        page,
        '<div><span>OUTPUT RATE</span><strong>—</strong><small>official-paid</small></div>',
        '<div><span>ANNOTATED PAGE</span><strong>$0.005</strong><small>separate published category</small></div>',
        "annotated rate",
    )
    page = replace_once(
        page,
        '<article><span>REASONING</span><h3>Not published</h3><p>Only provider-documented reasoning controls are shown; missing controls remain unpublished rather than inferred.</p></article>',
        '<article><span>DOCUMENT STRUCTURE</span><h3>Tables + blocks</h3><p>OCR extracts page text and layout regions. Block/word confidence assists review without guaranteeing error-free documents.</p></article>',
        "capability",
    )
    page = replace_once(
        page,
        '<p>SXF preserves the provider-published native billing basis. Only calculator-eligible generative token models enter token-cost arithmetic; specialist units and input-only embeddings remain visible without forced conversion.</p>',
        '<p>OCR 4.1 is charged per processed document page, not per input/output token. SXF keeps the original $0.004 Standard rate in the catalog, with annotated-page and human-review scenarios explained below.</p>',
        "pricing clarification",
    )
    page = replace_once(
        page, OLD_CAVEATS, fragment + "\n\n        " + OLD_CAVEATS,
        "editorial insertion",
    )
    page = replace_once(
        page, "</head>",
        '<link rel="stylesheet" href="/assets/mistral-ocr41-guide.css" />\n    </head>',
        "CSS",
    )
    page = replace_once(
        page, "</body>",
        '<script src="/assets/mistral-ocr41-cost.js" defer></script>\n    </body>',
        "calculator",
    )
    schema_match = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', page, re.S)
    if schema_match is None:
        raise ValueError("OCR 4.1 page lacks JSON-LD")
    schema = json.loads(schema_match.group(2))
    article = next(
        (node for node in schema["@graph"] if node.get("@type") == "TechArticle"),
        None,
    )
    if article is None:
        raise ValueError("OCR 4.1 page lacks TechArticle JSON-LD")
    article.update({
        "headline": TITLE.removesuffix(" | SXF"),
        "description": DESCRIPTION,
        "dateModified": "2026-11-07",
        "citation": SOURCES,
        "mainEntityOfPage": {"@type": "WebPage", "@id": URL},
        "author": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "publisher": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "keywords": [
            "Mistral OCR 4.1", "mistral-ocr-4-1",
            "Mistral OCR 4.1 API", "Mistral OCR 4.1 pricing",
            "Mistral OCR PDF extraction", "Mistral OCR tables",
            "OCR 4.1 bounding boxes", "OCR 4.1 block confidence",
        ],
    })
    schema["@graph"].append({
        "@type": "FAQPage",
        "@id": URL + "#faq", "url": URL + "#mocr41-faq",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in FAQ
        ],
    })
    serialized = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    return page[:schema_match.start(2)] + serialized + page[schema_match.end(2):]
