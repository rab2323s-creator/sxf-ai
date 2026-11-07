#!/usr/bin/env python3
"""Voxtral 2 SEO, primary-source provenance, costs, test fixtures and generator safety."""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import voxtral_mini_transcribe_2_page as editorial

PAGE = ROOT / "models/voxtral-mini-transcribe-2/index.html"
URL = "https://sxf.si/models/voxtral-mini-transcribe-2/"
FILES = ROOT / "models/voxtral-mini-transcribe-2"


def test_model_page() -> None:
    page = PAGE.read_text(encoding="utf-8")
    assert page.count('rel="canonical" href="' + URL + '"') == 1
    assert '<title>Voxtral Mini Transcribe 2: API, Pricing &amp; Diarization | SXF</title>' in page
    assert page.count("<h1>") == 1
    assert page.count("data-voxtral2-guide") == 1
    assert len(re.findall(r"<h2\b", page)) >= 18
    assert "voxtral-mini-2602" in page
    assert "voxtral-mini-transcribe-3-0" in page
    assert "October 20, 2026" in page
    assert "Word timestamps" in page
    assert "Speaker diarization" in page or "speaker diarization" in page
    assert "data-vox2-cost-lab" in page
    assert "SXF ORIGINAL REPRODUCIBLE RESEARCH DESIGN" in page
    assert "not a claim that SXF has run paid model calls" in page
    assert "synthetic" in page.lower()
    assert 'href="/assets/voxtral-2-guide.css"' in page
    assert 'src="/assets/voxtral-2-cost-lab.js"' in page
    for path in (
        "/models/voxtral-mini-transcribe-realtime/",
        "/models/scribe-v2/",
        "/models/scribe-v2-realtime/",
        "/models/gpt-transcribe/",
        "/models/gemini-3-5-transcribe/",
        "/models/pricing/",
        "/providers/mistral-ai/",
        "/compare/deepgram-nova-3-vs-elevenlabs-scribe-v2/",
        "/guides/ai-agent-security/",
    ):
        assert 'href="' + path + '"' in page, path
        assert (ROOT / path.lstrip("/") / "index.html").exists(), path
    for anchor in (
        "vox2-overview", "vox2-features", "vox2-pricing", "vox2-api",
        "vox2-diarization", "vox2-migration", "vox2-compare", "vox2-lab",
        "vox2-use-cases", "vox2-faq", "vox2-sources",
    ):
        assert page.count('id="' + anchor + '"') == 1
    schema = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    assert schema
    graph = json.loads(schema.group(1))
    article = next(x for x in graph["@graph"] if x["@type"] == "TechArticle")
    faq = next(x for x in graph["@graph"] if x["@type"] == "FAQPage")
    assert article["dateModified"] == "2026-11-07"
    assert article["mainEntityOfPage"]["@id"] == URL
    assert len(article["citation"]) >= 7
    assert len(faq["mainEntity"]) == 8
    assert page.count('<link rel="canonical" href="' + URL + '"') == 1
    assert editorial.CONTENT.read_text(encoding="utf-8").strip() in page
    source = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    assert "from voxtral_mini_transcribe_2_page import enrich_voxtral_mini_transcribe_2_page" in source
    assert 'if model_id == "voxtral-mini-2602":' in source
    assert "page = enrich_voxtral_mini_transcribe_2_page(page)" in source


def test_reciprocal_link() -> None:
    target = (ROOT / "models/voxtral-mini-transcribe-realtime/index.html").read_text(encoding="utf-8")
    source = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    assert 'data-voxtral2-offline-bridge' in target
    assert 'href="/models/voxtral-mini-transcribe-2/"' in target
    assert 'if model_id == "voxtral-mini-transcribe-realtime-2602":' in source
    assert "Need recorded-file transcription instead of realtime captions?" in source


def test_original_economics() -> None:
    for minutes, standard, batch in [
        (10, 0.03, 0.003),
        (60, 0.18, 0.018),
        (600, 1.8, 0.18),
        (6000, 18.0, 1.8),
        (60000, 180.0, 18.0),
    ]:
        assert round(minutes * 0.003, 5) == standard
        assert round(minutes * 0.0003, 5) == batch
    assert round(600 * 1.05 * 0.003, 2) == 1.89
    assert round((600 / 60) * (15 / 60) * 25, 2) == 62.5
    assert round(1.89 + 62.5, 2) == 64.39
    assert round((0.0035 / 0.003 - 1) * 100, 1) == 16.7
    js = (ROOT / "assets/voxtral-2-cost-lab.js").read_text(encoding="utf-8")
    assert "audio * (1 + retryFraction) * rate" in js
    assert "fetch(" not in js and "localStorage" not in js
    assert (ROOT / "assets/voxtral-2-guide.css").exists()


def test_research_scorer() -> None:
    script = FILES / "sxf-stt-score.py"
    example = FILES / "sxf-stt-example.jsonl"
    result = subprocess.run(
        [sys.executable, str(script), str(example), "--by-language"],
        check=True, text=True, capture_output=True, timeout=20,
    )
    report = json.loads(result.stdout)
    assert report["clips"] == 12
    assert set(report["by_language"]) == {"en", "ar", "de", "es"}
    assert report["total"]["wer_percent"] > 0
    assert report["total"]["cer_percent"] > 0
    assert all("hypothesis" in json.loads(line) for line in example.read_text(encoding="utf-8").splitlines())
    assert "synthetic" in script.read_text(encoding="utf-8")


if __name__ == "__main__":
    test_model_page()
    test_reciprocal_link()
    test_original_economics()
    test_research_scorer()
    print("PASS: Voxtral 2 SEO, source, pricing math, reciprocal links and research fixtures")
