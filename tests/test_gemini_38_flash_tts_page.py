#!/usr/bin/env python3
"""Guard against losing the TTS model SEO when catalog pages regenerate."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gemini_38_flash_tts_model_page import enrich_gemini_38_flash_tts_page

page = (ROOT / "models/gemini-3-8-flash-tts/index.html").read_text(encoding="utf-8")
enriched = enrich_gemini_38_flash_tts_page(page)
assert page == enriched, "Checked-in model page differs from generator output"
assert enriched.count('<h1>') == 1
assert enriched.count('data-gemini-38-flash-tts-guide') == 1
assert enriched.count('rel="canonical" href="https://sxf.si/models/gemini-3-8-flash-tts/"') == 1
assert "2027" in enriched and "$9.00" in enriched and "speech_metadata" in enriched
assert enriched.count('data-model-history') == 1
assert enriched.count('data-what-changed') == 1
assert len(enriched) > 20000
print("PASS: Gemini 3.8 Flash TTS SEO and regeneration parity")
