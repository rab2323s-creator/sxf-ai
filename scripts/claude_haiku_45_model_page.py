"""Persistent source-backed SEO enrichment for the generated Claude Haiku 4.5 page."""
from __future__ import annotations
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "data/model-page-content/claude-haiku-4-5-seo.html"
URL = "https://sxf.si/models/claude-haiku-4-5/"
TITLE = "Claude Haiku 4.5: API Pricing, Context & Python Guide | SXF"
DESCRIPTION = ("Claude Haiku 4.5 API: $1 input/$5 output per million tokens, 200K context, "
               "Python examples, caching calculator, extended thinking and Haiku 5.5 comparison.")
SOURCES = [
    "https://platform.claude.com/docs/en/models/haiku-4-5/overview",
    "https://platform.claude.com/docs/en/about-claude/pricing",
    "https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide",
    "https://platform.claude.com/docs/en/models/haiku-5-5/overview",
    "https://platform.claude.com/docs/en/about-claude/model-deprecations",
    "https://platform.claude.com/docs/en/build-with-claude/prompt-caching",
    "https://platform.claude.com/docs/en/build-with-claude/extended-thinking",
    "https://platform.claude.com/docs/en/api/messages",
]
QUESTIONS = [
    ("What is the Claude Haiku 4.5 model ID?",
     "The pinned Claude API model ID is claude-haiku-4-5-20251001. Anthropic also provides the alias claude-haiku-4-5."),
    ("How much does Claude Haiku 4.5 cost?",
     "Anthropic prices direct Standard API usage at $1 per million input tokens and $5 per million output tokens. Cache reads cost $0.10, five-minute writes $1.25, and one-hour writes $2 per million tokens."),
    ("What are Haiku 4.5's context and output limits?",
     "Its context window is 200,000 tokens, and its maximum output limit is 64,000 tokens."),
    ("Does Claude Haiku 4.5 support extended thinking?",
     "Yes. Haiku 4.5 uses manual extended thinking, with thinking.type enabled and a budget_tokens allocation."),
    ("Is Claude Haiku 4.5 still active?",
     "Anthropic's model reference lists it as active, with a retirement commitment no sooner than October 15, 2026. That date does not itself mean the model was retired."),
    ("What is different about Claude Haiku 5.5?",
     "Haiku 5.5 offers 1M context, adaptive thinking and prompt-length-dependent pricing, plus a different tokenizer. Check migration requirements before replacing 4.5."),
    ("Can Claude Haiku 4.5 accept images?",
     "Yes. It accepts both text and image inputs and generates text output."),
    ("Is Anthropic's Batch API available for Haiku 4.5?",
     "The Haiku 4.5 model card lists a 50 percent discount for Batch API input and output pricing. Batch workflows are asynchronous."),
]
INSERT = '<section class="model-deep-section">\n          <div class="model-section-head"><p class="eyebrow">EXPLORE</p>'
H1 = '<h1>Claude Haiku 4.5<br><span>verified model reference.</span></h1>'

def once(page: str, old: str, new: str, label: str) -> str:
    count = page.count(old)
    if count != 1:
        raise ValueError(f"Claude Haiku 4.5 {label}: expected one match, got {count}")
    return page.replace(old, new, 1)

def meta(page: str, name: str, value: str) -> str:
    selector = "property" if name.startswith("og:") else "name"
    pattern = r'(<meta ' + selector + r'="' + re.escape(name) + r'" content=")[^"]*(")'
    result, n = re.subn(pattern, lambda m: m.group(1) + escape(value, quote=True) + m.group(2), page, count=1)
    if n != 1:
        raise ValueError(f"Missing {name} meta")
    return result

def enrich_claude_haiku_45_page(page: str) -> str:
    if page.count('rel="canonical" href="' + URL + '"') != 1:
        raise ValueError("Unexpected Haiku 4.5 canonical URL")
    fragment = CONTENT.read_text(encoding="utf-8").strip()
    if fragment.count("data-haiku45-guide") != 1 or fragment.count('id="haiku45-faq"') != 1:
        raise ValueError("Haiku 4.5 editorial source missing")
    page = once(page, "<title>Claude Haiku 4.5 — API Specs, Context &amp; Pricing | SXF / AI</title>",
                "<title>" + escape(TITLE) + "</title>", "title")
    for name, value in (("description", DESCRIPTION), ("og:title", TITLE), ("og:description", DESCRIPTION),
                        ("twitter:title", TITLE), ("twitter:description", DESCRIPTION)):
        page = meta(page, name, value)
    page = once(page, H1,
                '<h1>Claude Haiku 4.5<br><span>API pricing, 200K context &amp; Python.</span></h1>', "H1")
    page = once(page, '<p>Fastest Claude tier for latency-sensitive and high-volume workloads.</p>',
                '<p>Claude Haiku 4.5: exact Anthropic model ID, $1/$5 token pricing, 200K context, caching, '
                'extended thinking, API examples and Haiku 5.5 migration.</p>', "hero description")
    page = once(page,
                '<div><strong>200,000</strong><span>context tokens</span></div>',
                '<div><strong>200K</strong><span>context tokens</span></div>',
                "hero context")
    page = once(page,
                '<div><strong>64,000</strong><span>max output</span></div>',
                '<div><strong>$1 / $5</strong><span>input / output per MTok</span></div>',
                "hero pricing")
    page = once(page,
                '<article><span>REASONING</span><h3>manual budget</h3><p>Only provider-documented reasoning controls are shown; missing controls remain unpublished rather than inferred.</p></article>',
                '<article><span>EXTENDED THINKING</span><h3>Manual budget</h3><p>Use thinking.type=enabled with budget_tokens and reserve output space for the final answer.</p></article>',
                "reasoning")
    page = once(page,
                '<p>SXF preserves the provider-published native billing basis. Only calculator-eligible generative token models enter token-cost arithmetic; specialist units and input-only embeddings remain visible without forced conversion.</p>',
                '<p>Standard input, output, cached read and cache-write tokens have different prices. '
                'SXF&#x27;s original calculator below models them separately and distinguishes asynchronous Batch costs.</p>',
                "price explanation")
    page = once(page, INSERT, fragment + "\n\n        " + INSERT, "editorial injection")
    page = once(page, "</head>", '<link rel="stylesheet" href="/assets/haiku45-guide.css" />\n    </head>', "CSS")
    page = once(page, "</body>", '<script src="/assets/haiku45-cost-lab.js" defer></script>\n    </body>', "JS")
    match = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', page, re.S)
    if match is None:
        raise ValueError("Missing JSON-LD")
    schema = json.loads(match.group(2))
    article = next((entry for entry in schema["@graph"] if entry.get("@type") == "TechArticle"), None)
    if article is None:
        raise ValueError("Missing article schema")
    article.update({
        "headline": TITLE.removesuffix(" | SXF"),
        "description": DESCRIPTION, "dateModified": "2026-11-07",
        "citation": SOURCES,
        "mainEntityOfPage": {"@type": "WebPage", "@id": URL},
        "author": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "publisher": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "keywords": ["Claude Haiku 4.5", "claude haiku api price", "claude-haiku-4-5-20251001",
                     "Claude Haiku 4.5 pricing", "Claude Haiku 4.5 Python API",
                     "Claude Haiku 4.5 prompt caching", "Claude Haiku 4.5 vs 5.5"],
    })
    schema["@graph"].append({
        "@type": "FAQPage", "@id": URL + "#faq", "url": URL + "#haiku45-faq",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                       for q, a in QUESTIONS],
    })
    serialized = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
    return page[:match.start(2)] + serialized + page[match.end(2):]
