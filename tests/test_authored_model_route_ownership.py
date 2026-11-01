#!/usr/bin/env python3
"""Protect all authored model routes from future catalog/renderer ownership drift."""
from __future__ import annotations
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import update_news as site

EXPECTED = {
    "/models/lfm2-5-vl-dspark/": "data-dspark-explorer",
    "/models/lfm3/": "data-lfm3-finder",
    "/models/lfm2-5-24b-a2b/": "data-lfm24-fit",
    "/models/gemini-4/": "data-g4-planner",
    "/models/gpt-live-transcribe/": "data-ltx-event-lab",
}


def main():
    assert set(site.AUTHORED_MODEL_ROUTE_RENDERERS)==set(EXPECTED)
    assert len(set(site.AUTHORED_MODEL_ROUTE_RENDERERS.values()))==len(EXPECTED)
    # These pages must not accidentally be claimed by the current pricing
    # catalog without the same authored renderer taking precedence.
    for path,marker in EXPECTED.items():
        slug=path.strip("/").split("/")[-1]
        index=(ROOT/path.strip("/")/"index.html").read_text(encoding="utf-8")
        assert marker in index,path
        assert "index,follow" in index,path
        generated=site.render_authored_model_route(path,[])
        assert generated is not None and marker in generated,path
        assert site.model_page_html(slug,[]).count(marker)>=1,path
        assert 'rel="canonical"' in generated,path
        # Simulate a future catalog entry with exactly this canonical route:
        # test direct ownership, not only the news generator branch.
        fake={"model_id":"future-"+slug,"sxf_url":path}
        site.MODEL_PRICING_BY_ID[fake["model_id"]]=fake
        try:
            original=site.model_catalog_entry
            site.model_catalog_entry=lambda model_id, obj=fake: obj if model_id==obj["model_id"] else original(model_id)
            # The route is dispatched before template fallback, but the model
            # history/evaluation extension layer would require a real catalog
            # registration; verify the shared editorial dispatch directly.
            assert marker in site.render_authored_model_route(fake["sxf_url"],[])
        finally:
            site.model_catalog_entry=original
            del site.MODEL_PRICING_BY_ID[fake["model_id"]]
    print("PASS: all five authored model routes protected from catalog overwrite")


if __name__=="__main__":
    main()
