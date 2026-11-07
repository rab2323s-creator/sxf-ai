"""Durable, evidence-grounded SEO enrichment for generated Meta Llama 4 Scout.

The model catalog continues to own facts, original provenance and price-status.
This editorial layer is reinserted into each scheduled site regeneration.
"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "data/model-page-content/llama-4-scout-seo.html"
URL = "https://sxf.si/models/llama-4-scout/"
TITLE = "Llama 4 Scout: 10M Context, 109B Specs & GPU VRAM | SXF"
DESCRIPTION = (
    "Meta Llama 4 Scout explained: 17B active/109B total parameters, "
    "10M-token context, H100 GPU memory, INT4 weights, license and Maverick comparison."
)
SOURCES = [
    "https://dev.meta.ai/llama/docs/model-cards-and-prompt-formats/llama4",
    "https://github.com/meta-llama/llama-models/blob/main/models/llama4/MODEL_CARD.md",
    "https://github.com/meta-llama/llama-models",
    "https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E-Instruct",
    "https://github.com/huggingface/blog/blob/main/llama4-release.md",
    "https://dev.meta.ai/llama/llama4/license",
    "https://dev.meta.ai/llama/llama4/use-policy",
    "https://vllm-project.github.io/2025/04/05/llama4.html",
]
FAQ = [
    ("Is Llama 4 Scout a 17B or 109B model?",
     "Llama 4 Scout is a mixture-of-experts model with 17B active parameters, 16 experts and 109B total parameters. Hardware must store the total model weights."),
    ("Does Llama 4 Scout support 10 million context tokens?",
     "Meta publishes a 10M maximum context for Scout Instruct and reports 512 GPUs for its 10M evaluation. Many actual hosted or local serving configurations impose smaller limits."),
    ("How much VRAM does Llama 4 Scout need?",
     "Meta documents an INT4 setup on one 80GB H100. A theoretical 4-bit 109B payload is 54.5 decimal GB before scales, KV cache and runtime overhead. Full BF16 raw weights are about 218 GB."),
    ("Where can I download Llama 4 Scout?",
     "Use the official gated meta-llama/Llama-4-Scout-17B-16E-Instruct model repository on Hugging Face subject to applicable access and license rights."),
    ("Can Llama 4 Scout be used commercially?",
     "Use is subject to the Llama 4 Community License and Acceptable Use Policy. Some rights are unavailable to EU-domiciled users and EU-headquartered organizations for multimodal Llama 4 models, subject to the policy's integrated-product exception."),
    ("Does Llama 4 Scout support images?",
     "It accepts text and up to five image inputs and emits text. Meta lists English-only image understanding."),
    ("What is Llama 4 Scout vs Llama 4 Maverick?",
     "Both have 17B active parameters; Scout has 109B total and 16 experts with 10M Instruct context, while Maverick has 400B total and 128 experts with 1M context."),
    ("What is the price of Llama 4 Scout API?",
     "Meta does not publish a universal direct Standard token rate for Scout weights. Hosted provider API fees, context limits, and self-hosted GPU costs must be compared separately."),
]
CAVEATS = '<section class="model-deep-section"><div class="model-section-head"><p class="eyebrow">CAVEATS</p>'
H1 = '<h1>Llama 4 Scout<br><span>verified model reference.</span></h1>'


def once(page: str, old: str, new: str, label: str) -> str:
    count = page.count(old)
    if count != 1:
        raise ValueError(f"Llama 4 Scout {label}: expected one match, got {count}")
    return page.replace(old, new, 1)


def metadata(page: str, name: str, value: str) -> str:
    selector = "property" if name.startswith("og:") else "name"
    regex = r'(<meta ' + selector + r'="' + re.escape(name) + r'" content=")[^"]*(")'
    result, count = re.subn(
        regex, lambda m: m.group(1) + escape(value, quote=True) + m.group(2),
        page, count=1,
    )
    if count != 1:
        raise ValueError(f"Llama 4 Scout missing {name} meta")
    return result


def enrich_llama_4_scout_page(page: str) -> str:
    if page.count('rel="canonical" href="' + URL + '"') != 1:
        raise ValueError("Llama 4 Scout canonical mismatch; aborting enrichment")
    fragment = CONTENT.read_text(encoding="utf-8").strip()
    if fragment.count('data-sxf-scout-guide') != 1 or fragment.count('id="scout-faq"') != 1:
        raise ValueError("Llama 4 Scout authored content missing or duplicated")

    page = once(
        page, '<title>Llama 4 Scout — API Specs, Context &amp; Pricing | SXF / AI</title>',
        '<title>' + escape(TITLE) + '</title>', "title",
    )
    for key, value in (
        ("description", DESCRIPTION), ("og:title", TITLE),
        ("og:description", DESCRIPTION), ("twitter:title", TITLE),
        ("twitter:description", DESCRIPTION),
    ):
        page = metadata(page, key, value)
    page = once(
        page, H1,
        '<h1>Llama 4 Scout<br><span>10M context, 109B parameters &amp; VRAM.</span></h1>',
        "H1",
    )
    page = once(
        page,
        '<p>Meta open-weight multimodal Llama 4 model optimized for very long context and efficient deployment.</p>',
        '<p>Meta Llama 4 Scout: 17B active/109B total MoE parameters, '
        '10-million-token Instruct context, hardware and license explained.</p>',
        "hero",
    )
    page = once(
        page,
        '<div><strong>Not published</strong><span>max output</span></div>',
        '<div><strong>109B / 17B</strong><span>total / active parameters</span></div>',
        "hero parameter display",
    )
    page = once(
        page,
        '<div><span>KNOWLEDGE CUTOFF</span><strong>2024-08</strong></div>',
        '<div><span>KNOWLEDGE CUTOFF</span><strong>August 2024</strong></div>',
        "cutoff wording",
    )
    page = once(
        page,
        '<article><span>REASONING</span><h3>Not published</h3><p>Only provider-documented reasoning controls are shown; missing controls remain unpublished rather than inferred.</p></article>',
        '<article><span>ARCHITECTURE</span><h3>MoE · 16 experts</h3><p>'
        'Scout has 109B total weights with 17B active parameters per token; '
        'no provider-documented reasoning budget should be inferred.</p></article>',
        "capability",
    )
    page = once(
        page,
        '<p>SXF preserves the provider-published native billing basis. Only calculator-eligible generative token models enter token-cost arithmetic; specialist units and input-only embeddings remain visible without forced conversion.</p>',
        '<p>Meta distributes Scout under a conditional community license, '
        'with no universal direct Meta Standard token price. Compare hosted '
        'provider rates or self-hosted GPU-hours and the end-to-end quality cost.</p>',
        "pricing",
    )
    page = once(page, CAVEATS, fragment + "\n\n        " + CAVEATS, "editorial insertion")
    page = once(
        page, '</head>',
        '<link rel="stylesheet" href="/assets/llama4-scout-guide.css" />\n    </head>',
        "styles",
    )
    page = once(
        page, '</body>',
        '<script src="/assets/llama4-scout-memory.js" defer></script>\n    </body>',
        "script",
    )

    match = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', page, re.S)
    if match is None:
        raise ValueError("Missing Scout page JSON-LD")
    schema = json.loads(match.group(2))
    article = next((node for node in schema["@graph"] if node.get("@type") == "TechArticle"), None)
    if article is None:
        raise ValueError("Missing Scout TechArticle")
    article.update({
        "headline": TITLE.removesuffix(" | SXF"),
        "description": DESCRIPTION,
        "dateModified": "2026-11-07",
        "citation": SOURCES,
        "mainEntityOfPage": {"@type": "WebPage", "@id": URL},
        "author": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "publisher": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "keywords": [
            "Llama 4 Scout", "Llama-4-Scout-17B-16E-Instruct",
            "Llama 4 Scout 109B", "Llama 4 Scout 17B",
            "Llama 4 Scout VRAM", "Llama 4 Scout 10M context",
            "Llama 4 Scout license", "Llama 4 Scout vs Maverick",
        ],
    })
    schema["@graph"].append({
        "@type": "FAQPage", "@id": URL + "#faq", "url": URL + "#scout-faq",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in FAQ
        ],
    })
    new_schema = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    return page[:match.start(2)] + new_schema + page[match.end(2):]
