#!/usr/bin/env python3
"""Daily Brief featured card retains legacy styling and honest issue-date copy."""
from __future__ import annotations
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import update_news

BRIEF_URL = "https://sxf.si/brief/"

def main():
    actual_date = update_news.brief_issue_date()
    assert actual_date <= date.today(), "Brief date in the future"
    assert update_news.brief_featured_title(date(2026, 11, 2), today=date(2026, 11, 2)) == "The 5 AI Stories That Matter Today"
    assert update_news.brief_featured_title(date(2026, 11, 1), today=date(2026, 11, 2)) == "5 Essential AI Stories — Latest Brief"
    assert update_news.brief_featured_title(date(2026, 11, 3), today=date(2026, 11, 2)) != "The 5 AI Stories That Matter Today"
    assert update_news.brief_issue_date('<script type="application/ld+json">{"@graph":[{"@type":"CollectionPage","url":"https://sxf.si/brief/","datePublished":"2026-11-01"}]}</script>') == date(2026, 11, 1)
    try:
        update_news.brief_issue_date('<script type="application/ld+json">{"@graph":[{"@type":"CollectionPage","url":"https://sxf.si/brief/"}]}</script>')
    except RuntimeError:
        pass
    else:
        raise AssertionError("Missing issue date must fail closed")
    markup = update_news.brief_featured_html(actual_date, today=actual_date)
    assert markup.startswith('<a class="featured-story" href="https://sxf.si/brief/">')
    assert 'class="featured-main"' in markup
    assert 'class="featured-topline"' in markup
    assert 'class="featured-title"' in markup
    assert 'class="featured-footer"' in markup
    assert 'class="featured-visual"' in markup
    assert 'The 5 AI Stories That Matter Today' in markup
    assert '5 ESSENTIAL STORIES' in markup
    assert 'signal-number">05' in markup
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    start = '<!-- SXF:FEATURED_START -->'
    end = '<!-- SXF:FEATURED_END -->'
    assert page.count(start) == page.count(end) == 1
    section = page.split(start, 1)[1].split(end, 1)[0].strip()
    # A checked-in homepage must track the actual editorial date; subsequent
    # scheduled news runs refresh the Today/Latest label automatically.
    assert section == update_news.brief_featured_html(actual_date)
    assert page.count('class="featured-story"') == 1
    assert "how-we-detect-frontier-model-misalignment-d28967f/" not in section
    script = re.search(r'<script type="application/ld\+json" id="latest-signals-schema">(.*?)</script>', page)
    assert script, "Missing homepage latest-signals JSON-LD"
    structured = json.loads(script.group(1))
    assert structured["numberOfItems"] == len(structured["itemListElement"]) == 8
    first = structured["itemListElement"][0]
    assert first["position"] == 1 and first["item"]["url"] == BRIEF_URL
    assert first["item"]["name"] == update_news.brief_featured_title(actual_date)
    assert [row["position"] for row in structured["itemListElement"]] == list(range(1, 9))
    print("PASS: Brief Hero same markup, dated correctly, no stale signal, JSON-LD synchronized")

if __name__ == "__main__":
    main()
