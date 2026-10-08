"""Render homepage and section feed cards from prepared signal records.

No fetching, filesystem operations, or global site state. Caller supplies the
relative-time formatter so existing update_news entrypoints remain compatible.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Callable


@dataclass(frozen=True)
class FeedCardContext:
    relative_time: Callable[[str], str]


def featured_html(item, context: FeedCardContext):
    relative_time = context.relative_time
    href = item.get("signal_url", item["url"])
    return f'''<a class="featured-story" href="{escape(href, quote=True)}">
  <div class="featured-main">
    <div>
      <div class="featured-topline"><strong>{escape(item["source"])}</strong><i></i><span>{escape(relative_time(item["published"]))}</span></div>
      <h3 class="featured-title">{escape(item["title"])}</h3>
    </div>
    <div class="featured-footer"><span class="category-pill">{escape(item["category"])}</span><span class="open-label">Read signal <b>↗</b></span></div>
  </div>
  <div class="featured-visual" aria-hidden="true"><span class="signal-cross">+</span><span class="signal-number">01</span></div>
</a>'''


def cards_html(items, context: FeedCardContext):
    relative_time = context.relative_time
    rows = []
    for item in items:
        href = item.get("signal_url", item["url"])
        rows.append(f'''<a class="story-card" href="{escape(href, quote=True)}">
  <div class="story-card-top"><span class="story-source">{escape(item["source"])}</span><span class="story-time">{escape(relative_time(item["published"]))}</span></div>
  <h3 class="story-title">{escape(item["title"])}</h3>
  <div class="story-card-bottom"><span class="category-pill">{escape(item["category"])}</span><span class="story-arrow" aria-hidden="true">↗</span></div>
</a>''')
    return "\n".join(rows)


def section_cards_html(items, context: FeedCardContext):
    relative_time = context.relative_time
    rows = []
    for item in items[:12]:
        href = item.get("signal_url", item["url"])
        rows.append(f'''<a class="intel-card" href="{escape(href, quote=True)}">
  <div class="intel-meta"><strong>{escape(item["source"])}</strong><span>{escape(relative_time(item["published"]))}</span></div>
  <h3>{escape(item["title"])}</h3>
  <div class="intel-foot"><span>{escape(item["category"])}</span><b>↗</b></div>
</a>''')
    return "\n".join(rows)
