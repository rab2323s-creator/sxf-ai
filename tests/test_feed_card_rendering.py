#!/usr/bin/env python3
"""Regression tests for extracted homepage and section HTML feed cards."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from feed_card_rendering import FeedCardContext, featured_html, cards_html, section_cards_html
import update_news


def main():
    calls = []
    def relative(value):
        calls.append(value)
        return "2h ago"

    ctx = FeedCardContext(relative_time=relative)
    signal = {
        "title": '<Model & "AI">',
        "url": "https://source.test/story?a=1&b=2",
        "signal_url": "/signals/ai-test/?a=1&b=2",
        "source": "A&B",
        "published": "2026-10-08T12:00:00Z",
        "category": "Models & Tools",
    }
    original = signal.copy()
    href = "/signals/ai-test/?a=1&amp;b=2"
    featured_expected = f'''<a class="featured-story" href="{href}">
  <div class="featured-main">
    <div>
      <div class="featured-topline"><strong>A&amp;B</strong><i></i><span>2h ago</span></div>
      <h3 class="featured-title">&lt;Model &amp; "AI"&gt;</h3>
    </div>
    <div class="featured-footer"><span class="category-pill">Models &amp; Tools</span><span class="open-label">Read signal <b>↗</b></span></div>
  </div>
  <div class="featured-visual" aria-hidden="true"><span class="signal-cross">+</span><span class="signal-number">01</span></div>
</a>'''
    story_expected = f'''<a class="story-card" href="{href}">
  <div class="story-card-top"><span class="story-source">A&amp;B</span><span class="story-time">2h ago</span></div>
  <h3 class="story-title">&lt;Model &amp; "AI"&gt;</h3>
  <div class="story-card-bottom"><span class="category-pill">Models &amp; Tools</span><span class="story-arrow" aria-hidden="true">↗</span></div>
</a>'''
    section_expected = f'''<a class="intel-card" href="{href}">
  <div class="intel-meta"><strong>A&amp;B</strong><span>2h ago</span></div>
  <h3>&lt;Model &amp; "AI"&gt;</h3>
  <div class="intel-foot"><span>Models &amp; Tools</span><b>↗</b></div>
</a>'''

    assert featured_html(signal, ctx) == featured_expected
    assert cards_html([signal], ctx) == story_expected
    assert section_cards_html([signal], ctx) == section_expected
    assert cards_html([], ctx) == ""
    assert section_cards_html([], ctx) == ""
    assert signal == original, "Rendering must not mutate feed rows"

    source_only = dict(signal)
    del source_only["signal_url"]
    for renderer in (featured_html, cards_html, section_cards_html):
        value = renderer(source_only if renderer is featured_html else [source_only], ctx)
        assert 'href="https://source.test/story?a=1&amp;b=2"' in value

    many = [dict(signal, title=f"Story {i}") for i in range(14)]
    section = section_cards_html(many, ctx)
    assert section.count('class="intel-card"') == 12, "Section rendering must cap at 12 cards"
    assert "Story 0" in section and "Story 11" in section
    assert "Story 12" not in section and "Story 13" not in section
    assert section.index("Story 0") < section.index("Story 11")
    assert calls and all(value == signal["published"] for value in calls)

    # The original names are still importable and dynamically resolve the
    # existing relative_time callable, as before the extraction.
    old_formatter = update_news.relative_time
    try:
        update_news.relative_time = relative
        assert update_news.featured_html(signal) == featured_expected
        assert update_news.cards_html([signal]) == story_expected
        assert update_news.section_cards_html([signal]) == section_expected
    finally:
        update_news.relative_time = old_formatter

    print("PASS: exact homepage/section card HTML, escaping, fallback links, cap and compatibility")


if __name__ == "__main__":
    main()
