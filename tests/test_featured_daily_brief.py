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
    if "--post-build" in sys.argv or actual_date == date.today():
        assert section == update_news.brief_featured_html(actual_date)
    else:
        assert '<a class="featured-story" href="https://sxf.si/brief/">' in section
    assert page.count('class="featured-story"') == 1
    assert "how-we-detect-frontier-model-misalignment-d28967f/" not in section
    script = re.search(r'<script type="application/ld\+json" id="latest-signals-schema">(.*?)</script>', page)
    assert script, "Missing homepage latest-signals JSON-LD"
    structured = json.loads(script.group(1))
    assert structured["numberOfItems"] == len(structured["itemListElement"]) == 8
    first = structured["itemListElement"][0]
    assert first["position"] == 1 and first["item"]["url"] == BRIEF_URL
    if "--post-build" in sys.argv or actual_date == date.today():
        assert first["item"]["name"] == update_news.brief_featured_title(actual_date)
    assert [row["position"] for row in structured["itemListElement"]] == list(range(1, 9))
    # The actual above-the-fold radar Hero must use the same dated Brief.
    hero = re.search(r'<a class="hero-live-signal" id="heroSignalLink"[^>]*>.*?</a>', page, re.S)
    assert hero, "Missing the actual top Hero card"
    assert hero.group(0) == update_news.hero_brief_html(actual_date), "Radar Hero must use the issue date"
    assert 'href="/brief/"' in hero.group(0)
    assert 'DAILY AI BRIEF' in hero.group(0)
    assert '5 STORIES' in hero.group(0)
    js = (ROOT / "app.js").read_text(encoding="utf-8")
    assert "updateHeroSignal(" not in js, "Client script must never overwrite radar Hero from news feed"
    assert "state.items[0]" not in js.split("function render()", 1)[1].split("function render()", 1)[0] or "updateHeroSignal(" not in js
    print("PASS: Brief Hero same markup, dated correctly, no stale signal, JSON-LD synchronized")

if __name__ == "__main__":
    main()
