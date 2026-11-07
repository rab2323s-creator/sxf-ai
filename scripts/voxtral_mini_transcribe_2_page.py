"""Persistent editorial SEO layer for Voxtral Mini Transcribe 2.

Mistral's canonical catalog owns model facts and its append-only history. The
version-specific SXF editorial layer lives in a checked-in HTML source and
is inserted after each site rebuild so automated feeds cannot erase it.
"""
from __future__ import annotations

import json
import re
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "data/model-page-content/voxtral-mini-transcribe-2-seo.html"
CANONICAL = "https://sxf.si/models/voxtral-mini-transcribe-2/"
TITLE = "Voxtral Mini Transcribe 2: API, Pricing & Diarization | SXF"
DESCRIPTION = (
    "Voxtral Mini Transcribe 2: $0.003/min pricing, Python API, "
    "speaker diarization, word timestamps and Voxtral 3 migration. "
    "Includes SXF cost calculator."
)
SOURCES = [
    "https://docs.mistral.ai/models/voxtral-mini-transcribe-26-02",
    "https://docs.mistral.ai/inference/pricing",
    "https://docs.mistral.ai/studio/audio/deprecated/speech_to_text/offline_transcription",
    "https://docs.mistral.ai/studio/audio/deprecated/overview",
    "https://docs.mistral.ai/studio/audio/migrate-from-voxtral-2",
    "https://docs.mistral.ai/models/voxtral-mini-transcribe-3-0",
    "https://docs.mistral.ai/models",
    "https://mistral.ai/news/voxtral-transcribe-2/",
]
FAQ = [
    ("What is the API model ID for Voxtral Mini Transcribe 2?",
     "The pinned Mistral ID is voxtral-mini-2602 for the /v1/audio/transcriptions endpoint, subject to deprecated-model availability."),
    ("How much does Voxtral Mini Transcribe 2 cost?",
     "The published historical Standard rate is $0.003 per audio minute ($0.18 per hour). Mistral separately lists an eligible Batch rate of $0.0003 per minute."),
    ("Does Voxtral Mini Transcribe 2 support Arabic?",
     "Yes. Arabic is among 13 documented languages; accuracy depends on dialect, noise, overlapping voices and recording conditions."),
    ("Does Voxtral Mini Transcribe 2 support speaker diarization?",
     "Yes, it can assign speaker labels to prerecorded audio, but those labels do not identify a person and require verification."),
    ("Does Voxtral 2 support word-level timestamps?",
     "Yes. Its legacy interface supports word-level timestamps, which Voxtral 3 removes in favor of segment-level timestamps."),
    ("Is Voxtral Mini Transcribe 2 open source?",
     "No downloadable open weights are listed for this Premier transcription-only endpoint. The separately named Voxtral Realtime 2 release has a different license."),
    ("Has Voxtral Mini Transcribe 2 been replaced by Voxtral 3?",
     "Yes. Mistral introduced Voxtral 3 on October 20, 2026 and lists the February 2026 model as deprecated. The documented replacement ID is voxtral-mini-transcribe-3-0."),
    ("What changes when migrating from Voxtral 2 to 3?",
     "Change the model ID, replace word-level timestamp requests with segment-level timestamps, check overlapping segments and re-evaluate context-bias configuration."),
]
CAVEATS = '<section class="model-deep-section"><div class="model-section-head"><p class="eyebrow">CAVEATS</p>'
H1 = '<h1>Voxtral Mini Transcribe 2<br><span>verified model reference.</span></h1>'


def replace_once(page: str, old: str, new: str, label: str) -> str:
    count = page.count(old)
    if count != 1:
        raise ValueError(f"Voxtral Mini Transcribe 2: {label} count {count}, expected 1")
    return page.replace(old, new, 1)


def meta(page: str, name: str, value: str) -> str:
    selector = "property" if name.startswith("og:") else "name"
    pattern = (
        r'(<meta ' + selector + r'="' + re.escape(name) + r'" content=")[^"]*(")'
    )
    new, count = re.subn(
        pattern,
        lambda match: match.group(1) + escape(value, quote=True) + match.group(2),
        page,
        count=1,
    )
    if count != 1:
        raise ValueError(f"Voxtral Mini Transcribe 2: {name} meta not found")
    return new


def enrich_voxtral_mini_transcribe_2_page(page: str) -> str:
    if page.count('rel="canonical" href="' + CANONICAL + '"') != 1:
        raise ValueError("Unexpected Voxtral 2 canonical; refusing SEO enrichment")

    source = CONTENT.read_text(encoding="utf-8").strip()
    if source.count("data-voxtral2-guide") != 1 or source.count('id="vox2-faq"') != 1:
        raise ValueError("Voxtral Mini Transcribe 2 editorial source is incomplete")

    page = replace_once(
        page,
        "<title>Voxtral Mini Transcribe 2 — API Specs, Context &amp; Pricing | SXF / AI</title>",
        "<title>" + escape(TITLE) + "</title>",
        "SEO title",
    )
    for key, value in (
        ("description", DESCRIPTION),
        ("og:title", TITLE), ("og:description", DESCRIPTION),
        ("twitter:title", TITLE), ("twitter:description", DESCRIPTION),
    ):
        page = meta(page, key, value)

    page = replace_once(
        page, H1,
        '<h1>Voxtral Mini Transcribe 2<br><span>API, pricing, diarization &amp; migration.</span></h1>',
        "H1",
    )
    page = replace_once(
        page,
        "<p>GA Mistral audio specialist optimized exclusively for transcription with timestamp support.</p>",
        "<p>Mistral Voxtral Mini Transcribe 2 (V2): $0.003/min speech-to-text, "
        "speaker diarization, word timestamps, Python API and Voxtral 3 migration.</p>",
        "hero description",
    )
    page = replace_once(
        page,
        '<div><strong>Not published</strong><span>context not published</span></div>',
        '<div><strong>$0.003</strong><span>historical Standard / audio minute</span></div>',
        "hero pricing",
    )
    page = replace_once(
        page,
        '<div><strong>Not published</strong><span>max output</span></div>',
        '<div><strong>13</strong><span>documented V2 languages</span></div>',
        "hero language coverage",
    )
    page = replace_once(
        page,
        '<div><span>CONTEXT WINDOW</span><strong>Not published</strong></div>',
        '<div><span>MODEL ID</span><strong>voxtral-mini-2602</strong><small>V2 pinned endpoint</small></div>',
        "context fact",
    )
    # Generated catalog has already displayed the model ID; rename duplicated fact
    # label for this slot to emphasize the legacy model lifecycle.
    page = replace_once(
        page,
        '<div><span>MODEL ID</span><strong>voxtral-mini-2602</strong><small>V2 pinned endpoint</small></div>',
        '<div><span>RELEASE</span><strong>February 2026</strong><small>superseded by Voxtral 3</small></div>',
        "release fact",
    )
    page = replace_once(
        page,
        '<div><span>MAX OUTPUT</span><strong>Not published</strong></div>',
        '<div><span>OUTPUT</span><strong>Transcript</strong><small>timestamps and speaker labels optional</small></div>',
        "output fact",
    )
    page = replace_once(
        page,
        '<div><span>KNOWLEDGE CUTOFF</span><strong>Not published</strong></div>',
        '<div><span>LIFECYCLE</span><strong>Deprecated</strong><small>Mistral recommends Voxtral 3</small></div>',
        "lifecycle fact",
    )
    page = replace_once(
        page,
        '<div><span>OUTPUT RATE</span><strong>—</strong><small>official-paid</small></div>',
        '<div><span>HISTORICAL BATCH RATE</span><strong>$0.0003</strong><small>per audio minute; eligible jobs only</small></div>',
        "Batch fact",
    )
    page = replace_once(
        page,
        '<article><span>REASONING</span><h3>Not published</h3><p>Only provider-documented reasoning controls are shown; missing controls remain unpublished rather than inferred.</p></article>',
        '<article><span>TRANSCRIPTION CONTROLS</span><h3>Diarization + timestamps</h3><p>The original V2 interface can separate speakers and supply word or segment timestamps for prerecorded audio.</p></article>',
        "transcription controls",
    )
    page = replace_once(
        page,
        '<p>SXF preserves the provider-published native billing basis. Only calculator-eligible generative token models enter token-cost arithmetic; specialist units and input-only embeddings remain visible without forced conversion.</p>',
        '<p>V2 transcription is charged by audio duration, not by language-model text tokens. The SXF pricing section compares historic Standard/Batch rates and models human review costs transparently.</p>',
        "pricing explanation",
    )
    page = replace_once(
        page, CAVEATS, source + "\n\n        " + CAVEATS,
        "editorial insertion",
    )
    page = replace_once(
        page, "</head>",
        '<link rel="stylesheet" href="/assets/voxtral-2-guide.css" />\n    </head>',
        "CSS",
    )
    page = replace_once(
        page, "</body>",
        '<script src="/assets/voxtral-2-cost-lab.js" defer></script>\n    </body>',
        "cost-lab JavaScript",
    )

    match = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', page, re.S)
    if not match:
        raise ValueError("Missing JSON-LD in Voxtral 2 page")
    graph = json.loads(match.group(2))
    if graph.get("@context") != "https://schema.org":
        raise ValueError("Unexpected JSON-LD context")
    article = next((item for item in graph["@graph"] if item.get("@type") == "TechArticle"), None)
    if article is None:
        raise ValueError("Voxtral 2 TechArticle missing")
    article.update({
        "headline": TITLE.removesuffix(" | SXF"),
        "description": DESCRIPTION,
        "dateModified": "2026-11-07",
        "citation": SOURCES,
        "mainEntityOfPage": {"@type": "WebPage", "@id": CANONICAL},
        "author": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "publisher": {"@type": "Organization", "name": "SXF / AI", "url": "https://sxf.si/"},
        "keywords": [
            "Voxtral Mini Transcribe 2", "Voxtral Mini Transcribe V2",
            "Voxtral Mini Transcribe 2.0", "voxtral-mini-2602",
            "Voxtral Mini Transcribe 2 pricing", "Voxtral API transcription",
            "Mistral speaker diarization", "Voxtral 2 vs Voxtral 3",
        ],
    })
    graph["@graph"].append({
        "@type": "FAQPage",
        "@id": CANONICAL + "#faq",
        "url": CANONICAL + "#vox2-faq",
        "mainEntity": [
            {"@type": "Question", "name": question, "acceptedAnswer": {
                "@type": "Answer", "text": answer,
            }}
            for question, answer in FAQ
        ],
    })
    graph_json = json.dumps(graph, ensure_ascii=False, separators=(",", ":"))
    return page[:match.start(2)] + graph_json + page[match.end(2):]
