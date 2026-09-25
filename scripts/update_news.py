#!/usr/bin/env python3
from __future__ import annotations

import email.utils
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "news.json"
INDEX = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"
SECTION_PAGES = {
    "Models": ROOT / "models" / "index.html",
    "Tools": ROOT / "tools" / "index.html",
    "Research": ROOT / "research" / "index.html",
    "Open Source": ROOT / "open-source" / "index.html",
}

SOURCES = [
    ("OpenAI", "https://openai.com/news/rss.xml"),
    ("Google AI", "https://blog.google/technology/ai/rss/"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    ("GitHub", "https://github.blog/changelog/feed/"),
]
USER_AGENT = "SXF-AI-Radar/1.1 (+https://sxf.si/)"
MAX_ITEMS = 80
MAX_AGE_DAYS = 21

def text(node, *names):
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""

def clean_title(title):
    return re.sub(r"\s+", " ", title).strip()[:240]

def parse_date(value):
    if not value:
        return datetime.now(timezone.utc)
    try:
        d = email.utils.parsedate_to_datetime(value)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)

def categorize(title, source):
    t = title.lower()
    if any(k in t for k in ["open source", "open-source", "github", "weights", "checkpoint"]):
        return "Open Source"
    if any(k in t for k in ["model", "gpt", "gemini", "claude", "llm", "vision", "reasoning", "multimodal", "embedding"]):
        return "Models"
    if any(k in t for k in ["research", "paper", "study", "benchmark", "evaluation", "science", "safety"]):
        return "Research"
    return "Tools"

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()

def parse_feed(source, body):
    root = ET.fromstring(body)
    rows = []
    for item in root.findall(".//item"):
        title = clean_title(text(item, "title"))
        link = text(item, "link")
        published = text(item, "pubDate", "date")
        if title and link:
            rows.append((title, link, published))
    if not rows:
        for entry in root.findall(".//{*}entry"):
            title = clean_title(text(entry, "{*}title"))
            link = ""
            for ln in entry.findall("{*}link"):
                href = ln.attrib.get("href", "")
                rel = ln.attrib.get("rel", "alternate")
                if href and rel in ("alternate", ""):
                    link = href
                    break
            published = text(entry, "{*}published", "{*}updated")
            if title and link:
                rows.append((title, link, published))
    return [
        {
            "title": title,
            "url": link,
            "source": source,
            "published": parse_date(published).isoformat().replace("+00:00", "Z"),
            "category": categorize(title, source),
        }
        for title, link, published in rows
    ]

def valid_url(url):
    p = urlparse(url)
    return p.scheme in ("http", "https") and bool(p.netloc)

def relative_time(date_str):
    d = parse_date(date_str)
    diff = max(timedelta(0), datetime.now(timezone.utc) - d)
    minutes = int(diff.total_seconds() // 60)
    if minutes < 2:
        return "just now"
    if minutes < 60:
        return f"{minutes}m ago"
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    if days < 7:
        return f"{days}d ago"
    return d.strftime("%b %-d")

def featured_html(item):
    return f'''<a class="featured-story" href="{escape(item["url"], quote=True)}" target="_blank" rel="noopener noreferrer">
  <div class="featured-main">
    <div>
      <div class="featured-topline"><strong>{escape(item["source"])}</strong><i></i><span>{escape(relative_time(item["published"]))}</span></div>
      <h3 class="featured-title">{escape(item["title"])}</h3>
    </div>
    <div class="featured-footer"><span class="category-pill">{escape(item["category"])}</span><span class="open-label">Open source <b>↗</b></span></div>
  </div>
  <div class="featured-visual" aria-hidden="true"><span class="signal-cross">+</span><span class="signal-number">01</span></div>
</a>'''

def cards_html(items):
    rows = []
    for item in items:
        rows.append(f'''<a class="story-card" href="{escape(item["url"], quote=True)}" target="_blank" rel="noopener noreferrer">
  <div class="story-card-top"><span class="story-source">{escape(item["source"])}</span><span class="story-time">{escape(relative_time(item["published"]))}</span></div>
  <h3 class="story-title">{escape(item["title"])}</h3>
  <div class="story-card-bottom"><span class="category-pill">{escape(item["category"])}</span><span class="story-arrow" aria-hidden="true">↗</span></div>
</a>''')
    return "\n".join(rows)

def replace_block(source, start, end, body):
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    replacement = f"{start}\n{body}\n{end}"
    return pattern.sub(lambda _m: replacement, source, count=1)

def update_index(items):
    if not INDEX.exists() or not items:
        return
    page = INDEX.read_text(encoding="utf-8")
    page = replace_block(page, "<!-- SXF:FEATURED_START -->", "<!-- SXF:FEATURED_END -->", featured_html(items[0]))
    page = replace_block(page, "<!-- SXF:FEED_START -->", "<!-- SXF:FEED_END -->", cards_html(items[1:13]))
    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Latest AI signals",
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "numberOfItems": min(len(items), 10),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {"@type": "Thing", "name": item["title"], "url": item["url"]},
            }
            for i, item in enumerate(items[:10])
        ],
    }
    schema = '<script type="application/ld+json" id="latest-signals-schema">' + json.dumps(item_list, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c") + "</script>"
    page = replace_block(page, "<!-- SXF:ITEMLIST_START -->", "<!-- SXF:ITEMLIST_END -->", schema)
    INDEX.write_text(page, encoding="utf-8")


def section_cards_html(items):
    rows = []
    for item in items[:12]:
        rows.append(f'''<a class="intel-card" href="{escape(item["url"], quote=True)}" target="_blank" rel="noopener noreferrer">
  <div class="intel-meta"><strong>{escape(item["source"])}</strong><span>{escape(relative_time(item["published"]))}</span></div>
  <h3>{escape(item["title"])}</h3>
  <div class="intel-foot"><span>{escape(item["category"])}</span><b>↗</b></div>
</a>''')
    return "\n".join(rows)

def update_section_pages(items):
    for category, path in SECTION_PAGES.items():
        if not path.exists():
            continue
        filtered = [item for item in items if item["category"] == category]
        page = path.read_text(encoding="utf-8")
        page = replace_block(page, "<!-- SXF:SECTION_FEED_START -->", "<!-- SXF:SECTION_FEED_END -->", section_cards_html(filtered))
        schema = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": f"Latest {category} AI signals",
            "itemListOrder": "https://schema.org/ItemListOrderDescending",
            "numberOfItems": min(len(filtered), 10),
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "item": {"@type": "Thing", "name": item["title"], "url": item["url"]}}
                for i, item in enumerate(filtered[:10])
            ],
        }
        schema_html = '<script type="application/ld+json" id="section-signals-schema">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c") + "</script>"
        page = replace_block(page, "<!-- SXF:SECTION_SCHEMA_START -->", "<!-- SXF:SECTION_SCHEMA_END -->", schema_html)
        path.write_text(page, encoding="utf-8")

def update_sitemap(items):
    latest = parse_date(items[0]["published"]).date().isoformat() if items else datetime.now(timezone.utc).date().isoformat()
    urls = [
        ("https://sxf.si/", "1.0"),
        ("https://sxf.si/models/", "0.9"),
        ("https://sxf.si/tools/", "0.9"),
        ("https://sxf.si/research/", "0.9"),
        ("https://sxf.si/open-source/", "0.9"),
    ]
    rows = "\n".join(
        f"  <url>\n    <loc>{url}</loc>\n    <lastmod>{latest}</lastmod>\n    <changefreq>hourly</changefreq>\n    <priority>{priority}</priority>\n  </url>"
        for url, priority in urls
    )
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{rows}
</urlset>
'''
    SITEMAP.write_text(xml, encoding="utf-8")

def main():
    items = []
    errors = []
    for source, url in SOURCES:
        try:
            items.extend(parse_feed(source, fetch(url)))
        except Exception as exc:
            errors.append(f"{source}: {exc}")

    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    dedup = {}
    for item in items:
        if not valid_url(item["url"]):
            continue
        dt = parse_date(item["published"])
        if dt < cutoff:
            continue
        key = re.sub(r"\W+", "", item["title"].lower())[:140]
        current = dedup.get(key)
        if current is None or dt > parse_date(current["published"]):
            dedup[key] = item

    final = sorted(dedup.values(), key=lambda x: parse_date(x["published"]), reverse=True)[:MAX_ITEMS]
    if not final and errors and OUT.exists():
        try:
            final = json.loads(OUT.read_text(encoding="utf-8")).get("items", [])
        except Exception:
            pass

    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "items": final,
        "feed_errors": errors,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    update_index(final)
    update_section_pages(final)
    update_sitemap(final)
    print(f"Wrote {len(final)} items. Errors: {len(errors)}")

if __name__ == "__main__":
    main()
