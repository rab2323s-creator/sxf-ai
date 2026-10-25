"""Source-backed Runway provider guide applied after canonical catalog rendering.

The catalog remains authoritative for model count, identity, base pricing and
verification timestamp. Runway Creative subscriptions are editorial snapshots
with explicit vendor citations and must not replace catalog API prices.
"""
import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAGMENT = ROOT / "data/provider-page-content/runway-seo.html"
CANONICAL = "https://sxf.si/providers/runway/"
TITLE = "Runway AI Pricing & Models (2026): Credits, API & Gen-4.5 | SXF"
DESCRIPTION = "Explore Runway AI pricing, Free/Standard/Pro/Max plans, Gen-4.5 video credits and API costs. Compare Runway vs Kling with source-backed model guidance."
SOURCES = [
    "https://runway.com/pricing",
    "https://docs.dev.runwayml.com/guides/pricing/",
    "https://docs.dev.runwayml.com/guides/models/",
    "https://docs.dev.runwayml.com/guides/using-the-api/",
    "https://help.runwayml.com/hc/en-us/articles/46974685288467-Creating-with-Gen-4-5",
]
FAQ = [
    ("How much does Runway AI cost?", "Runway Creative offers a limited Free option plus Standard, Pro and Max subscriptions. Observed annual-billing monthly prices are $12, $28 and $76 respectively; month-to-month prices are higher. Runway Dev API is separately metered by generation, model and format."),
    ("Is Runway AI free?", "There is a Free creative plan with 125 one-time credits for a selection of tools. It is not unlimited access to every model. API usage and its purchased developer credits are a separate product."),
    ("How much does Runway Gen-4.5 cost per second?", "At the published Runway developer rate, Gen-4.5 uses 12 credits per second and purchased API credits are $0.01 each. The base equivalent is $0.12 per second before taxes and optional output charges."),
    ("Are Runway credits the same for plans and the API?", "No. Creative subscription credit allowances and developer-project API credits are distinct billing contexts. Compare generation costs within the product and plan you will actually use."),
    ("What models does Runway offer?", "Runway Creative and Runway Dev provide access to Runway-developed models and selected third-party models. SXF currently tracks Runway Gen-4.5 as one verified Runway-origin model in its own database; that count is not Runway's complete platform offering."),
    ("Does Runway Gen-4.5 support text-to-video and image-to-video?", "Yes. Gen-4.5 accepts text instructions or a reference image plus a motion prompt to generate short video clips. Its standard creator workflow documents 2–10-second durations at 720p, with mode-specific aspect ratios."),
]

def enrich_runway_provider(page, models):
    """Add editorial guidance without duplicating or mutating canonical records."""
    if len(models) != 1 or models[0].get("model_id") != "gen4.5":
        raise ValueError("Runway lineup changed: review provider narrative and schema")
    if page.count('<link rel="canonical" href="' + CANONICAL + '"') != 1:
        raise ValueError("Runway provider canonical mismatch")
    if page.count('<section class="model-reference model-reference-deep shell">') != 1:
        raise ValueError("Runway model directory anchor missing")
    if 'data-runway-provider-guide' in page:
        raise ValueError("Runway provider enrichment already applied")
    fragment = FRAGMENT.read_text(encoding="utf-8")
    if fragment.count('data-runway-provider-guide') != 1 or fragment.count('id="runway-estimator"') != 1:
        raise ValueError("Runway guide lacks expected content or estimator")
    page = page.replace(
        '<section class="model-reference model-reference-deep shell">',
        fragment + '\n<section class="model-reference model-reference-deep shell" id="runway-directory">',
        1,
    )
    page = page.replace("</head>", '<link rel="stylesheet" href="/providers/runway/reference.css" />\n</head>', 1)
    page = page.replace("</body>", '<script src="/providers/runway/reference.js" defer></script></body>', 1)
    page = re.sub(r'<title>.*?</title>', lambda _: "<title>" + escape(TITLE) + "</title>", page, count=1, flags=re.S)
    for key, value in (
        ("description", DESCRIPTION),
        ("og:title", TITLE),
        ("og:description", DESCRIPTION),
        ("twitter:title", TITLE),
        ("twitter:description", DESCRIPTION),
    ):
        pattern = r'(<meta (?:name|property)="' + re.escape(key) + r'" content=")[^"]*(")'
        page, count = re.subn(pattern, lambda m: m.group(1) + escape(value, quote=True) + m.group(2), page, count=1)
        if count != 1:
            raise ValueError("Runway missing SEO meta: " + key)
    old_h1 = '<h1>Runway.<br><span>Verified model portfolio.</span></h1>'
    if page.count(old_h1) != 1:
        raise ValueError("Runway hero anchor changed")
    page = page.replace(old_h1, '<h1>Runway AI.<br><span>Video models, plans &amp; API pricing.</span></h1>', 1)
    old_hero = 'Specs, pricing availability and source-backed change history are normalized from the same canonical database used across SXF / AI.'
    if page.count(old_hero) != 1:
        raise ValueError("Runway hero description anchor changed")
    page = page.replace(old_hero, 'Compare Runway AI plans, Gen-4.5 video credits and Developer API economics, with independent primary-source model research.', 1)
    page = page.replace('calculator-priced</span>', 'token-calculator eligible</span>', 1)
    if page.count('<strong>0</strong><span>token-calculator eligible</span>') != 1:
        raise ValueError("Runway status label mismatch")
    page = page.replace('<strong>0</strong><span>token-calculator eligible</span>',
                        '<strong>12</strong><span>API credits / video second</span>', 1)
    page = page.replace('<div class="model-family-spec"><b>Not published context</b><small>Not published max output</small></div>',
                        '<div class="model-family-spec"><b>Text / image → video</b><small>2–10s creator clips · 720p</small></div>', 1)
    page = page.replace('$7.20 per generated minute (equivalent to $0.12/second; 12 credits/second)</strong>',
                        '$0.12 per generated second · 12 API credits/sec</strong>', 1)
    graph = [
        {"@type": "CollectionPage", "@id": CANONICAL + "#webpage",
         "name": TITLE, "url": CANONICAL, "description": DESCRIPTION,
         "inLanguage": "en", "isPartOf": {"@id": "https://sxf.si/#website"},
         "about": {"@type": "Organization", "name": "Runway", "url": "https://runway.com/"},
         "breadcrumb": {"@id": CANONICAL + "#breadcrumb"},
         "mainEntity": {"@id": CANONICAL + "#model-list"}},
        {"@type": "BreadcrumbList", "@id": CANONICAL + "#breadcrumb",
         "itemListElement": [
             {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": "https://sxf.si/"},
             {"@type": "ListItem", "position": 2, "name": "Providers", "item": "https://sxf.si/providers/"},
             {"@type": "ListItem", "position": 3, "name": "Runway", "item": CANONICAL},
         ]},
        {"@type": "ItemList", "@id": CANONICAL + "#model-list",
         "name": "Runway-origin models tracked by SXF / AI",
         "numberOfItems": len(models),
         "itemListElement": [
             {"@type": "ListItem", "position": i + 1,
              "name": model["model"], "url": "https://sxf.si" + model["sxf_url"]}
             for i, model in enumerate(models)
         ]},
        {"@type": "TechArticle", "@id": CANONICAL + "#guide", "url": CANONICAL,
         "headline": "Runway AI models and pricing: Creative plans, Gen-4.5 and Developer API",
         "description": DESCRIPTION, "mainEntityOfPage": {"@id": CANONICAL + "#webpage"},
         "dateModified": "2026-10-25", "inLanguage": "en",
         "author": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
         "citation": SOURCES},
        {"@type": "FAQPage", "@id": CANONICAL + "#faq",
         "mainEntity": [
             {"@type": "Question", "name": question,
              "acceptedAnswer": {"@type": "Answer", "text": answer}}
             for question, answer in FAQ
         ]},
    ]
    schema = json.dumps({"@context": "https://schema.org", "@graph": graph},
                        ensure_ascii=False, separators=(",", ":"))
    page, count = re.subn(
        r'<script type="application/ld\+json">.*?</script>',
        lambda _: '<script type="application/ld+json">' + schema + '</script>',
        page, count=1, flags=re.S,
    )
    if count != 1:
        raise ValueError("Runway JSON-LD script missing")
    return page
