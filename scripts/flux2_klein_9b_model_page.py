"""Editorial SEO enrichment for generated FLUX.2 [klein] 9B reference.

The model catalog owns facts, rates and history. An authored HTML fragment owns
the source-backed editorial content, and is re-injected on every site rebuild.
"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "data/model-page-content/flux-2-klein-9b-seo.html"
TITLE = "FLUX.2 Klein 9B: Pricing, API, ComfyUI & VRAM | SXF"
DESCRIPTION = (
    "FLUX.2 Klein 9B guide: $0.015 starting API price, cost examples, "
    "ComfyUI installation, 19.6GB VRAM reference, local license and 4B vs Pro."
)
URL = "https://sxf.si/models/flux-2-klein-9b/"
SOURCES = [
    "https://bfl.ai/models/flux-2-klein",
    "https://bfl.ai/pricing?category=flux.2",
    "https://help.bfl.ai/articles/7592221790-how-do-i-generate-quickly-with-flux-2-klein",
    "https://help.bfl.ai/articles/9272590838-self-serve-dev-license-overview-pricing",
    "https://huggingface.co/black-forest-labs/FLUX.2-klein-9B",
    "https://docs.comfy.org/tutorials/flux/flux-2-klein",
    "https://api.bfl.ai/docs",
]
FAQ = [
    ("How much does FLUX.2 Klein 9B cost per image?",
     "The BFL API starts at $0.015 for the first billed output megapixel, plus $0.002 for each additional output MP and $0.002 per billed reference-image input MP."),
    ("What is the FLUX.2 Klein 9B API endpoint?",
     "POST https://api.bfl.ai/v1/flux-2-klein-9b with the x-key header. Check the official API documentation for current request and result handling."),
    ("Can I run FLUX.2 Klein 9B in ComfyUI?",
     "Yes. ComfyUI publishes workflows for the distilled 9B model, including compatible diffusion, text encoder, and VAE weights."),
    ("How much VRAM does FLUX.2 Klein 9B require?",
     "BFL reports 19.6 GB for its distilled 9B reference configuration and recommends planning about 24 GB for local use. Your precision, image size, and offloading settings matter."),
    ("Is FLUX.2 Klein 9B commercially usable with local weights?",
     "The downloadable 9B weights use FLUX Non-Commercial License. Commercial self-hosting needs a separate BFL license; commercial use is included with BFL's paid API under its terms."),
    ("What is FLUX.2 Klein 9B Base?",
     "9B Base is an undistilled separate checkpoint intended for customization and fine-tuning, not the four-step distilled 9B inference configuration."),
]
INSERT_ANCHOR = '<section class="model-deep-section"><div class="model-section-head"><p class="eyebrow">CAVEATS</p>'
H1_ANCHOR = '<h1>FLUX.2 Klein 9B<br><span>verified model reference.</span></h1>'

def exactly_once(page: str, old: str, new: str, label: str) -> str:
    if page.count(old) != 1:
        raise ValueError(f"FLUX.2 Klein 9B: {label} missing or repeated ({page.count(old)})")
    return page.replace(old, new, 1)

def set_meta(page: str, identifier: str, text: str) -> str:
    if identifier == "description":
        pattern = r'(<meta name="description" content=")[^"]*(")'
    else:
        pattern = r'(<meta property="' + re.escape(identifier) + r'" content=")[^"]*(")' if identifier.startswith("og:") else r'(<meta name="' + re.escape(identifier) + r'" content=")[^"]*(")'
    result, n = re.subn(pattern, lambda m: m.group(1) + escape(text, quote=True) + m.group(2), page, count=1)
    if n != 1:
        raise ValueError(f"FLUX.2 Klein 9B missing {identifier}")
    return result

def enrich_flux2_klein_9b_page(page: str) -> str:
    if page.count('rel="canonical" href="' + URL + '"') != 1:
        raise ValueError("Unexpected FLUX.2 Klein 9B canonical; refusing to enrich")
    fragment = CONTENT.read_text(encoding="utf-8").strip()
    if fragment.count('data-flux2-klein-guide') != 1 or fragment.count('id="flux2-klein-faq"') != 1:
        raise ValueError("Editorial fragment integrity failure")
    page = exactly_once(page, "<title>FLUX.2 Klein 9B — API Specs, Context &amp; Pricing | SXF / AI</title>", "<title>" + escape(TITLE) + "</title>", "title")
    for identifier, value in [
        ("description", DESCRIPTION),
        ("og:title", TITLE), ("og:description", DESCRIPTION),
        ("twitter:title", TITLE), ("twitter:description", DESCRIPTION),
    ]:
        page = set_meta(page, identifier, value)
    page = exactly_once(page, H1_ANCHOR,
        '<h1>FLUX.2 Klein 9B<br><span>Pricing, API, ComfyUI &amp; GPU requirements.</span></h1>', "H1")
    page = exactly_once(page,
        '<p>Black Forest Labs fast, compact 9B image generation and editing model with open weights and high-throughput API.</p>',
        '<p>FLUX.2 Klein 9B image generation and editing: pricing per megapixel, BFL API, ComfyUI setup, GPU memory and commercial license explained.</p>',
        "hero")
    page = exactly_once(page,
        '<div><strong>Not published</strong><span>context not published</span></div>',
        '<div><strong>$0.015</strong><span>first output MP · BFL API</span></div>',
        "hero pricing")
    page = exactly_once(page,
        '<div><strong>Not published</strong><span>max output</span></div>',
        '<div><strong>19.6 GB</strong><span>BFL reference VRAM · plan ~24 GB</span></div>',
        "hero VRAM")
    page = exactly_once(page,
        '<div><span>CONTEXT WINDOW</span><strong>Not published</strong></div>',
        '<div><span>MODEL SIZE</span><strong>9B</strong><small>distilled, four inference steps</small></div>',
        "model size")
    page = exactly_once(page,
        '<div><span>MAX OUTPUT</span><strong>Not published</strong></div>',
        '<div><span>BFL REFERENCE VRAM</span><strong>19.6 GB</strong><small>actual requirements depend on setup</small></div>',
        "VRAM fact")
    page = exactly_once(page,
        '<div><span>KNOWLEDGE CUTOFF</span><strong>Not published</strong></div>',
        '<div><span>WEIGHT LICENSE</span><strong>Non-commercial</strong><small>9B local weights; API rights separate</small></div>',
        "license fact")
    page = exactly_once(page,
        '<div><span>OUTPUT RATE</span><strong>—</strong><small>official-paid</small></div>',
        '<div><span>ADDITIONAL OUTPUT MP</span><strong>+$0.002</strong><small>reference MP +$0.002</small></div>',
        "pricing fact")
    page = exactly_once(page,
        '<article><span>REASONING</span><h3>Not published</h3><p>Only provider-documented reasoning controls are shown; missing controls remain unpublished rather than inferred.</p></article>',
        '<article><span>GENERATION</span><h3>Four steps</h3><p>The distilled 9B checkpoint is designed for fast visual generation and editing; 9B Base is undistilled and targets customization.</p></article>',
        "capability")
    page = exactly_once(page,
        '<p>SXF preserves the provider-published native billing basis. Only calculator-eligible generative token models enter token-cost arithmetic; specialist units and input-only embeddings remain visible without forced conversion.</p>',
        '<p>This image-model service is billed per rounded image megapixel, not text tokens. The SXF pricing breakdown below shows separately billed output and reference-image inputs.</p>',
        "pricing explanation")
    page = exactly_once(page, INSERT_ANCHOR, fragment + "\n\n        " + INSERT_ANCHOR, "editorial insert")
    page = exactly_once(page, "</head>", '<link rel="stylesheet" href="/assets/flux2-klein-guide.css" />\n    </head>', "CSS")
    tag = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', page, re.S)
    if not tag:
        raise ValueError("No schema JSON-LD on generated Klein page")
    graph = json.loads(tag.group(2))
    article = next((x for x in graph["@graph"] if x.get("@type") == "TechArticle"), None)
    if article is None:
        raise ValueError("No TechArticle in Klein page JSON-LD")
    article.update({
        "headline": TITLE.removesuffix(" | SXF"),
        "description": DESCRIPTION,
        "citation": SOURCES,
        "mainEntityOfPage": {"@type": "WebPage", "@id": URL},
        "author": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "publisher": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "keywords": ["FLUX.2 Klein 9B", "flux 2 klein 9b", "flux 2 klein API", "FLUX.2 Klein 9B pricing", "FLUX.2 Klein ComfyUI", "FLUX.2 Klein 9B VRAM"],
        "dateModified": "2026-11-07",
    })
    graph["@graph"].append({
        "@type": "FAQPage", "@id": URL + "#faq", "url": URL + "#flux2-klein-faq",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in FAQ
        ],
    })
    replacement = json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
    return page[:tag.start(2)] + replacement + page[tag.end(2):]
