#!/usr/bin/env python3
"""Regression: the FLUX.2 Klein 9B source-backed page survives generated builds."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import flux2_klein_9b_model_page as klein

URL = "https://sxf.si/models/flux-2-klein-9b/"
PAGE = ROOT / "models/flux-2-klein-9b/index.html"


def verify(page: str) -> None:
    assert page.count('rel="canonical" href="' + URL + '"') == 1
    assert page.count('data-flux2-klein-guide') == 1
    assert page.count('<h1>') == 1
    assert 'FLUX.2 Klein 9B: Pricing, API, ComfyUI &amp; VRAM | SXF' in page
    assert '19.6 GB' in page and '24 GB' in page
    assert 'FLUX Non-Commercial License' in page
    assert 'SXF ORIGINAL COST ANALYSIS' in page
    assert 'SXF REPRODUCIBLE EVALUATION METHOD' in page
    assert 'not a claim that SXF has already executed the benchmark' in page
    assert 'id="flux2-klein-faq"' in page
    assert 'href="/assets/flux2-klein-guide.css"' in page
    assert 'href="/compare/flux-2-pro-vs-flux-2-klein-9b/"' in page
    assert 'href="/guides/flux-3-image-klein/"' in page
    assert 'href="/guides/ai-model-licensing/"' in page
    assert 'href="/models/flux-2-max/"' in page
    assert len(re.findall(r'<h2\b[^>]*>', page)) >= 15
    schema = re.search(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    assert schema
    obj = json.loads(schema.group(1))
    assert obj["@context"] == "https://schema.org"
    article = next(x for x in obj["@graph"] if x["@type"] == "TechArticle")
    assert article["dateModified"] == "2026-11-07"
    assert article["mainEntityOfPage"]["@id"] == URL
    assert len(article["citation"]) >= 5
    faq = next(x for x in obj["@graph"] if x["@type"] == "FAQPage")
    assert len(faq["mainEntity"]) == 6
    for output_mp, ref_mp, dollars in [(1, 0, 0.015), (2, 0, 0.017), (4, 0, 0.021), (2, 2, 0.021)]:
        assert round(0.015 + (output_mp - 1) * 0.002 + ref_mp * 0.002, 5) == dollars
        assert ("$" + format(dollars, ".3f")) in page


def main() -> None:
    page = PAGE.read_text(encoding="utf-8")
    verify(page)
    source = (ROOT / "scripts/update_news.py").read_text(encoding="utf-8")
    assert "from flux2_klein_9b_model_page import enrich_flux2_klein_9b_page" in source
    assert 'if model_id == "flux-2-klein-9b":' in source
    assert "page = enrich_flux2_klein_9b_page(page)" in source
    fragment = klein.CONTENT.read_text(encoding="utf-8").strip()
    assert fragment in page
    for anchor in (
        "flux2-klein-overview", "flux2-klein-specs", "flux2-klein-pricing",
        "flux2-klein-api", "flux2-klein-comfyui", "flux2-klein-license",
        "flux2-klein-comparison", "flux2-klein-lab", "flux2-klein-faq",
        "flux2-klein-sources",
    ):
        assert page.count('id="' + anchor + '"') == 1
    print("PASS: FLUX.2 Klein 9B SEO, arithmetic, evidence, schema and rebuild hook")


if __name__ == "__main__":
    main()
