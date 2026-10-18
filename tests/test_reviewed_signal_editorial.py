#!/usr/bin/env python3
"""Verify source-backed editorial reviews survive normal regeneration."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from html import unescape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import update_news
from signal_editorial_reviews import REVIEWS, get_review, render_review_evidence

ARCHIVE = json.loads((ROOT / "data/archive.json").read_text(encoding="utf-8"))["items"]
SOURCE = {row["signal_slug"]: row for row in ARCHIVE}

def main():
    assert len(REVIEWS) >= 2
    for slug, review in REVIEWS.items():
        item = SOURCE[slug]
        assert get_review(item) == review
        assert item["summary"] == review["summary"]
        assert item["editorial"] == review["editorial"]
        assert item["seo_eligible"], f"Reviewed primary-source page must be eligible: {slug}"
        assert len(review["summary"]) >= 120
        assert 100 <= len(review["meta_description"]) <= 165
        assert len(review["evidence"]) >= 3
        assert all(e["source"] in review["sources"] for e in review["evidence"])
        assert all(e["fact"] and e["label"] for e in review["evidence"])
        prepared = update_news.prepare_items([item])[0]
        assert prepared["summary"] == review["summary"]
        assert prepared["editorial"] == review["editorial"]
        assert prepared["seo_eligible"], slug
        html = update_news.signal_page_html(prepared, [prepared])
        assert '<meta name="robots" content="index,follow' in html
        assert '<h1>' + review["h1"] + '</h1>' in unescape(html)
        assert 'signal-evidence" aria-labelledby="signal-evidence-title"' in html
        assert review["limitations"] in unescape(html)
        for evidence in review["evidence"]:
            assert evidence["label"] in unescape(html)
        schema = json.loads(html.split('<script type="application/ld+json">', 1)[1].split("</script>", 1)[0])["@graph"]
        assert schema[1]["citation"] == review["sources"]
        assert schema[1]["dateModified"] >= review["reviewed_at"]
        assert "This signal may affect how the model" not in html
        assert "The important change is broader access to the announced product" not in html
        assert "We’re on a journey to advance" not in html
    print("PASS: reviewed Signals are specific, citable, indexable and regenerate safely")

if __name__ == "__main__":
    main()
