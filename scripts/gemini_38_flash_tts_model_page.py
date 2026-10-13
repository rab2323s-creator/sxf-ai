"""Durable, model-specific content and SEO for Gemini 3.8 Flash TTS.

The canonical model catalog remains the source of truth for pricing/history.
This enriches only the presentational model page and survives feed regeneration.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
PARTIAL = ROOT / "data/model-page-content/gemini-3-8-flash-tts.html"
SCHEMA = ROOT / "data/model-page-content/gemini-3-8-flash-tts.schema.json"
MODEL_URL = "https://sxf.si/models/gemini-3-8-flash-tts/"
TITLE = "Gemini 3.8 Flash TTS: Pricing, Voice API & Examples | SXF / AI"
DESCRIPTION = ("Gemini 3.8 Flash TTS guide: voice API examples, $9/M audio tokens, "
               "8K input, 130+ languages, multi-speaker controls, limits and Flash-Lite comparison.")
MODEL_SECTION = '      <section class="model-reference model-reference-deep shell">'
NEXT_SECTION = '      <section class="model-change-watch shell"'


def enrich_gemini_38_flash_tts_page(page: str) -> str:
    """Replace the thin generic model body; retain route, history and shared shell."""
    if page.count(MODEL_SECTION) != 1 or page.count(NEXT_SECTION) != 1:
        raise ValueError("Gemini 3.8 Flash TTS: catalog model markers changed")
    start = page.index(MODEL_SECTION)
    end = page.index(NEXT_SECTION, start)
    body = PARTIAL.read_text(encoding="utf-8").strip("\n")
    page = page[:start] + body + "\n\n" + page[end:]
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    if schema["@graph"][0]["@id"] != MODEL_URL + "#article":
        raise ValueError("Gemini 3.8 Flash TTS: incorrect structured-data identity")
    schema_json = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    replacements = [
        (r"<title>.*?</title>", "<title>" + escape(TITLE) + "</title>"),
        (r'<meta name="description" content="[^"]*" />',
         '<meta name="description" content="' + escape(DESCRIPTION, quote=True) + '" />'),
        (r'<meta property="og:title" content="[^"]*" />',
         '<meta property="og:title" content="' + escape(TITLE, quote=True) + '" />'),
        (r'<meta name="twitter:title" content="[^"]*" />',
         '<meta name="twitter:title" content="' + escape(TITLE, quote=True) + '" />'),
        (r'<meta property="og:description" content="[^"]*" />',
         '<meta property="og:description" content="' + escape(DESCRIPTION, quote=True) + '" />'),
        (r'<meta name="twitter:description" content="[^"]*" />',
         '<meta name="twitter:description" content="' + escape(DESCRIPTION, quote=True) + '" />'),
        (r'<script type="application/ld\+json">.*?</script>',
         '<script type="application/ld+json">' + schema_json + '</script>'),
    ]
    for pattern, replacement in replacements:
        page, count = re.subn(pattern, lambda _: replacement, page, count=1, flags=re.S)
        if count != 1:
            raise ValueError(f"Gemini 3.8 Flash TTS: missing SEO field {pattern}")
    page = page.replace(
        '<h1>Gemini 3.8 Flash TTS<br><span>verified model reference.</span></h1>',
        '<h1>Gemini 3.8 Flash TTS<br><span>pricing, voice API &amp; examples.</span></h1>',
    )
    page = page.replace(
        "Google&#x27;s flagship production text-to-speech model for high-fidelity, expressive long-form and multi-speaker audio generation.",
        "Google's expressive text-to-speech model: verified API pricing, voice controls, "
        "single- and multi-speaker synthesis, examples and Flash-Lite comparison.",
    )
    if page.count('data-gemini-38-flash-tts-guide') != 1:
        raise ValueError("Gemini 3.8 Flash TTS: enrichment missing or duplicated")
    if page.count('rel="canonical" href="' + MODEL_URL + '"') != 1:
        raise ValueError("Gemini 3.8 Flash TTS: canonical URL changed")
    return page
