#!/usr/bin/env python3
"""Regression: GitHub license-compliance signal stays accurate and survives regeneration."""
from __future__ import annotations

import json
import re
import sys
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import update_news
import github_license_compliance_signal_page as reference

SLUG = "open-source-license-compliance-generally-available-f70342f"
URL = "https://sxf.si/signals/" + SLUG + "/"

def main():
    archive = json.loads((ROOT / "data" / "archive.json").read_text(encoding="utf-8"))["items"]
    item = next(row for row in archive if row["signal_slug"] == SLUG)
    assert item["signal_url"] == URL
    html = update_news.signal_page_html(item, [item])
    assert html.count("<link rel=\"canonical\" href=\"" + URL + "\"") == 1
    assert "<h1>" + reference.H1 + "</h1>" in html
    assert reference.DESCRIPTION in html
    assert html.count("data-license-compliance-analysis") == 1
    assert "This can change what developers are able to run locally" not in html
    assert "supported quantization or model formats" not in html
    assert "GitHub Enterprise Cloud" in html
    assert "Require license compliance results before merging" in html
    assert "40 package URLs" in unescape(html)
    assert "data-license-compliance-analysis" in html
    assert "/guides/ai-model-licensing/" in html
    graph = json.loads(html.split('<script type="application/ld+json">', 1)[1].split("</script>", 1)[0])["@graph"]
    article = next(entry for entry in graph if entry.get("@id") == URL + "#article")
    assert "TechArticle" in article["@type"]
    assert article["citation"] == reference.SOURCES
    assert article["keywords"] == reference.KEYWORDS
    assert article["datePublished"] == item["published"]
    assert article["dateModified"] >= reference.EDITED_AT
    faq = next(entry for entry in graph if entry.get("@type") == "FAQPage")
    assert len(faq["mainEntity"]) >= 6
    assert all(qa["acceptedAnswer"]["text"] for qa in faq["mainEntity"])
    saved = (ROOT / "signals" / SLUG / "index.html").read_text(encoding="utf-8")
    assert reference.H1 in saved and "data-license-compliance-analysis" in saved
    assert reference.DESCRIPTION in saved
    assert "40 package URLs" in unescape(saved)
    assert 100 <= len(reference.DESCRIPTION) <= 165
    assert all(source.startswith("https://") for source in reference.SOURCES)
    assert len(re.sub(r"<[^>]+>", " ", reference.BODY_HTML).split()) >= 1100
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    assert URL in sitemap
    print("PASS: GitHub license compliance source facts, FAQ schema, canonical, preserved URL and regeneration parity")

if __name__ == "__main__":
    main()
