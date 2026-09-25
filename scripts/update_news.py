#!/usr/bin/env python3
from __future__ import annotations

import email.utils
import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from html import escape, unescape
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "news.json"
ARCHIVE_OUT = ROOT / "data" / "archive.json"
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
MAX_META_ENRICH_PER_RUN = 8
INITIAL_ARCHIVE_DAYS = 35

def text(node, *names):
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return found.text.strip()
    return ""

def clean_title(title):
    return re.sub(r"\s+", " ", title).strip()[:240]

def clean_summary(value):
    if not value:
        return ""
    value = unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:900]

def parse_date(value):
    if not value:
        return None
    try:
        d = email.utils.parsedate_to_datetime(value)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        pass
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None

def categorize(title, source):
    t = title.replace("‑", "-").replace("–", "-").replace("—", "-").lower()

    # Product and developer surfaces beat incidental model mentions.
    if re.search(r"\bcopilot\b|\bchatgpt\b|\bagents? api\b|\bsandbox(?:ing)?\b|\bcode reviews?\b|\bgithub actions\b", t):
        if re.search(r"\bresearch\b|\bbenchmark\b|\bevaluation\b|\bstudy\b|\bsafety\b|\bmisalignment\b", t):
            return "Research"
        return "Tools"

    if re.search(r"\bresearch\b|\bpaper\b|\bstudy\b|\bbenchmark\b|\bevaluation\b|\bscience\b|\bsafety\b|\bmisalignment\b|\bassessment\b", t):
        return "Research"

    if re.search(r"\bopen[- ]source\b|\bopen weights?\b|\bweights\b|\bcheckpoint\b|\bllama\.cpp\b|\bmlx\b|\bquants?\b|\brepository release\b", t):
        return "Open Source"

    if re.search(r"\bgpt[- ]\d+(?:\.\d+)?\b|\bclaude(?:\s+[a-z]+)?\s+\d+(?:\.\d+)?\b|\bgemini(?:\s+\d+(?:\.\d+)?)?\b|\blfm\d+(?:\.\d+)?\b|\bllm\b|\bvision-language model\b|\bmultimodal model\b|\breasoning model\b|\bembedding model\b", t):
        return "Models"

    return "Tools"

def classify_tags(title, source, category):
    t = title.replace("‑", "-").replace("–", "-").replace("—", "-").lower()
    tags = []
    rules = [
        ("GitHub Copilot", r"\bcopilot\b"),
        ("Coding AI", r"\bcode\b|\bcoding\b|\bcodex\b|\bdeveloper\b|\brepository\b|\bjetbrains\b"),
        ("AI Agents", r"\bagents?\b|\bagentic\b"),
        ("Security", r"\bsecurity\b|\bsafety\b|\bsandbox(?:ing)?\b|\bcyber\b|\bproof of presence\b"),
        ("Multimodal AI", r"\bmultimodal\b|\bvision\b|\bimage\b|\bvideo\b|\bvoice\b|\baudio\b"),
        ("Open Source AI", r"\bopen[- ]source\b|\bopen weights?\b|\bweights\b|\bcheckpoint\b|\bllama\.cpp\b|\bmlx\b|\bquants?\b"),
        ("Research", r"\bresearch\b|\bpaper\b|\bstudy\b|\bbenchmark\b|\bevaluation\b|\bscience\b"),
    ]
    for label, pattern in rules:
        if re.search(pattern, t):
            tags.append(label)
    if source == "OpenAI":
        tags.append("OpenAI")
    elif source == "Google AI":
        tags.append("Google AI")
    if category == "Open Source" and "Open Source AI" not in tags:
        tags.append("Open Source AI")
    return list(dict.fromkeys(tags))

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
        published = parse_date(text(item, "pubDate", "date"))
        summary = clean_summary(text(item, "description", "summary", "content"))
        if title and link and published is not None:
            rows.append((title, link, published, summary))
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
            published = parse_date(text(entry, "{*}published", "{*}updated"))
            summary = clean_summary(text(entry, "{*}summary", "{*}content"))
            if title and link and published is not None:
                rows.append((title, link, published, summary))

    output = []
    for title, link, published, summary in rows:
        category = categorize(title, source)
        output.append({
            "title": title,
            "url": link,
            "source": source,
            "published": published.isoformat().replace("+00:00", "Z"),
            "category": category,
            "tags": classify_tags(title, source, category),
            "summary": summary,
        })
    return output

def fetch_meta_description(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
        with urllib.request.urlopen(req, timeout=12) as r:
            ctype = (r.headers.get("Content-Type") or "").lower()
            if "html" not in ctype:
                return ""
            raw = r.read(350000).decode("utf-8", "ignore")
        patterns = [
            r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:name|property)=["\'](?:description|og:description)["\']',
        ]
        for pattern in patterns:
            m = re.search(pattern, raw, re.I | re.S)
            if m:
                value = clean_summary(m.group(1))
                if 40 <= len(value) <= 900:
                    return value
    except Exception:
        pass
    return ""

def enrich_summaries(items, existing_by_url):
    enriched = 0
    floor = datetime.min.replace(tzinfo=timezone.utc)
    for item in sorted(items, key=lambda x: parse_date(x["published"]) or floor, reverse=True):
        if enriched >= MAX_META_ENRICH_PER_RUN:
            break
        previous = existing_by_url.get(item["url"], {})
        if item.get("summary") or previous.get("summary"):
            continue
        summary = fetch_meta_description(item["url"])
        if summary:
            item["summary"] = summary
            item["summary_origin"] = "source-meta"
            enriched += 1
    return enriched

def valid_url(url):
    p = urlparse(url)
    return p.scheme in ("http", "https") and bool(p.netloc)

def relative_time(date_str):
    d = parse_date(date_str)
    if d is None:
        return ""
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

def cards_html(items):
    rows = []
    for item in items:
        href = item.get("signal_url", item["url"])
        rows.append(f'''<a class="story-card" href="{escape(href, quote=True)}">
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
                "item": {"@type": "Thing", "name": item["title"], "url": item.get("signal_url", item["url"])},
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
        href = item.get("signal_url", item["url"])
        rows.append(f'''<a class="intel-card" href="{escape(href, quote=True)}">
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
                {"@type": "ListItem", "position": i + 1, "item": {"@type": "Thing", "name": item["title"], "url": item.get("signal_url", item["url"])}}
                for i, item in enumerate(filtered[:10])
            ],
        }
        schema_html = '<script type="application/ld+json" id="section-signals-schema">' + json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c") + "</script>"
        page = replace_block(page, "<!-- SXF:SECTION_SCHEMA_START -->", "<!-- SXF:SECTION_SCHEMA_END -->", schema_html)
        if category == "Models":
            page = replace_block(page, "<!-- SXF:TRACKED_MODELS_START -->", "<!-- SXF:TRACKED_MODELS_END -->", tracked_models_html(items))
        path.write_text(page, encoding="utf-8")


BASE_URL = "https://sxf.si"
SIGNALS_DIR = ROOT / "signals"
TOPICS_DIR = ROOT / "topics"
BRIEF_DIR = ROOT / "brief"

TOPICS = [
    {
        "slug": "openai",
        "name": "OpenAI",
        "description": "Product, model, research and platform signals published by OpenAI.",
        "source": "OpenAI",
    },
    {
        "slug": "google-ai",
        "name": "Google AI",
        "description": "AI product, research and developer signals published across Google's AI channels.",
        "source": "Google AI",
    },
    {
        "slug": "github-copilot",
        "name": "GitHub Copilot",
        "description": "Copilot product, coding workflow and developer tooling changes from GitHub.",
        "keywords": ["copilot"],
    },
    {
        "slug": "ai-agents",
        "name": "AI Agents",
        "description": "Agent systems, agentic workflows, APIs and products that act across multi-step tasks.",
        "keywords": ["agent", "agents", "agentic"],
    },
    {
        "slug": "coding-ai",
        "name": "Coding AI",
        "description": "AI coding systems, developer tools, code intelligence and software engineering workflows.",
        "keywords": ["code", "coding", "codex", "developer", "copilot", "repository"],
    },
    {
        "slug": "multimodal-ai",
        "name": "Multimodal AI",
        "description": "Vision, image, video, voice and multimodal model or product developments.",
        "keywords": ["multimodal", "vision", "image", "video", "voice", "audio"],
    },
    {
        "slug": "ai-safety",
        "name": "AI Safety",
        "description": "Safety, evaluation, alignment, risk and responsible deployment signals.",
        "keywords": ["safety", "alignment", "misalignment", "risk", "evaluation", "assessment"],
    },
    {
        "slug": "open-source-ai",
        "name": "Open Source AI",
        "description": "Open models, weights, runtimes, frameworks, repositories and local AI tooling.",
        "category": "Open Source",
        "keywords": ["open source", "open-source", "weights", "llama.cpp", "mlx", "repository"],
    },
]

MODEL_PATTERNS = [
    re.compile(r"\bGPT[- ]\d+(?:\.\d+)?(?:\s+(?:Astra|Sol|Luna|Live))?", re.I),
    re.compile(r"\bClaude\s+[A-Za-z]+\s+\d+(?:\.\d+)?", re.I),
    re.compile(r"\bGemini(?:\s+\d+(?:\.\d+)?)?(?:\s+(?:Pro|Flash|Ultra))?", re.I),
    re.compile(r"\bLFM\d+(?:\.\d+)?(?:[- ][A-Za-z0-9.]+)*", re.I),
]

STOPWORDS = {
    "the","a","an","and","or","to","of","for","with","in","on","at","is","are","by",
    "from","how","new","now","more","ai","using","use","your","its","into","as"
}

def slugify(value):
    value = value.replace("‑", "-").replace("–", "-").replace("—", "-")
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:82] or "signal"

def signal_slug(item):
    digest = hashlib.sha1(item["url"].encode("utf-8")).hexdigest()[:7]
    return f'{slugify(item["title"])[:70]}-{digest}'

SIGNAL_SCORE_RULES = [
    (re.compile(r"\bintroducing\b|\blaunch(?:ed|es)?\b|\brelease(?:d|s)?\b|\bnow available\b", re.I), 18, "release"),
    (re.compile(r"\bGPT[- ]\d|\bClaude\b|\bGemini\b|\bLFM\d|\bmodel\b", re.I), 14, "model"),
    (re.compile(r"\bagents?\b|\bagentic\b|\bAPI\b|\bCopilot\b|\bdeveloper\b", re.I), 10, "developer"),
    (re.compile(r"\bresearch\b|\bbenchmark\b|\bevaluation\b|\bstudy\b|\bscience\b", re.I), 12, "research"),
    (re.compile(r"\bsafety\b|\balignment\b|\bmisalignment\b|\bassessment\b|\bcyber\b", re.I), 10, "safety"),
    (re.compile(r"\bopen[- ]source\b|\bweights\b|\brepository\b|\bllama\.cpp\b|\bMLX\b", re.I), 10, "open-source"),
    (re.compile(r"\bexpands?\b|\bnew features?\b|\bimproves?\b|\bfaster\b|\bbetter\b", re.I), 7, "product-change"),
]

def signal_score(item, now=None):
    title = item["title"]
    score = 24
    factors = []
    for pattern, points, label in SIGNAL_SCORE_RULES:
        if pattern.search(title):
            score += points
            factors.append(label)

    if item["category"] == "Models":
        score += 8
    elif item["category"] == "Research":
        score += 7
    elif item["category"] == "Open Source":
        score += 6
    else:
        score += 4
    return min(100, score), factors[:5]

def brief_priority(item, now=None):
    now = now or datetime.now(timezone.utc)
    base = item.get("signal_score", 0)
    published = parse_date(item.get("published", ""))
    if published is None:
        return base
    age_hours = max(0.0, (now - published).total_seconds() / 3600)
    freshness = 18 if age_hours <= 12 else 14 if age_hours <= 24 else 9 if age_hours <= 72 else 4 if age_hours <= 168 else 0
    return min(100, base + freshness)

def event_fingerprint(item):
    title = item["title"].replace("‑", "-").replace("–", "-").replace("—", "-").lower()
    models = sorted(set(slugify(name) for name in extract_models(item["title"])))
    if models and re.search(r"\bintroducing\b|\brelease(?:d|s)?\b|\bavailable\b|\blaunch(?:ed|es)?\b", title):
        return "model-release:" + "|".join(models)
    tokens = [
        token for token in re.findall(r"[a-z0-9]+", title)
        if len(token) > 3 and token not in STOPWORDS and token not in {"openai","github","google","hugging","face"}
    ]
    return "title:" + "-".join(tokens[:8])

def editorial_units(item):
    title = item["title"]
    source = item["source"]
    category = item["category"]
    summary = clean_summary(item.get("summary", ""))

    if summary:
        what_changed = summary
    elif re.search(r"\bintroducing\b|\blaunch(?:ed|es)?\b|\brelease(?:d|s)?\b", title, re.I):
        what_changed = f'{source} published a release-focused update titled “{title}.” SXF is tracking it as a {category.lower()} signal and keeps the original publication as the source of record.'
    elif re.search(r"\bnow available\b|\bavailable\b|\bexpands?\b|\benablement\b", title, re.I):
        what_changed = f'{source} published an availability or rollout update titled “{title}.” The signal is indexed here so changes in access, rollout scope and related product details can be followed over time.'
    elif re.search(r"\bbenchmark\b|\bevaluation\b|\bresearch\b|\bstudy\b|\bscience\b", title, re.I):
        what_changed = f'{source} published a research-oriented update titled “{title}.” SXF places it in the radar as a traceable research signal rather than treating the headline as an independently verified finding.'
    else:
        what_changed = f'{source} published an update titled “{title}.” SXF classifies it under {category} and preserves the direct path to the original publication for the complete context.'

    if category == "Models":
        why = "Model signals can change capability expectations, access patterns or deployment choices. The useful questions are what changed, who can access it, how it compares with prior versions, and which claims are supported by published evaluations."
    elif category == "Research":
        why = "Research signals matter when they change the evidence available around capability, evaluation, safety or scientific use. The paper or primary publication should be checked for methodology, scope, limitations and reproducibility."
    elif category == "Open Source":
        why = "Open-source signals can affect what developers are able to inspect, run or build on. The practical value depends on the released artifacts, license, hardware requirements, maintenance status and reproducibility."
    else:
        why = "Tool and platform changes matter when they alter what users or developers can actually do. The practical impact depends on availability, supported workflows, pricing or limits, and whether the change is generally released or still restricted."

    verify = "Verify the exact claims, benchmarks, pricing, rollout status, safety notes and technical limitations in the original source. SXF adds organization and context; it does not replace the publisher’s documentation."
    return {
        "what_changed": clean_summary(what_changed)[:1100],
        "why_it_matters": why,
        "what_to_verify": verify,
    }

def select_brief_items(items, limit=5):
    floor = datetime.min.replace(tzinfo=timezone.utc)
    ranked = sorted(
        items,
        key=lambda item: (brief_priority(item), parse_date(item["published"]) or floor),
        reverse=True,
    )
    selected = []
    source_counts = {}
    category_counts = {}
    events = set()

    for item in ranked:
        source = item["source"]
        category = item["category"]
        event = event_fingerprint(item)
        if event in events:
            continue
        if source_counts.get(source, 0) >= 2:
            continue
        if category_counts.get(category, 0) >= 2 and len(selected) < limit - 1:
            continue
        selected.append(item)
        events.add(event)
        source_counts[source] = source_counts.get(source, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1
        if len(selected) == limit:
            return selected

    for item in ranked:
        event = event_fingerprint(item)
        if item in selected or event in events:
            continue
        selected.append(item)
        events.add(event)
        if len(selected) == limit:
            break
    return selected

def prepare_items(items):
    prepared = []
    for item in items:
        row = dict(item)
        row["summary"] = clean_summary(row.get("summary", ""))
        row["category"] = categorize(row["title"], row["source"])
        row["tags"] = classify_tags(row["title"], row["source"], row["category"])
        row["signal_slug"] = signal_slug(row)
        row["signal_url"] = f'{BASE_URL}/signals/{row["signal_slug"]}/'
        score, factors = signal_score(row)
        row["signal_score"] = score
        row["score_factors"] = factors
        row["editorial"] = editorial_units(row)
        prepared.append(row)
    return prepared

def load_items(path):
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload.get("items", []) if isinstance(payload, dict) else []
    except Exception:
        return []

def merge_archive(existing_items, incoming_items):
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    by_url = {item.get("url"): dict(item) for item in existing_items if valid_url(item.get("url", ""))}

    for incoming in incoming_items:
        url = incoming["url"]
        previous = by_url.get(url, {})
        merged = dict(previous)
        merged.update(incoming)
        if not merged.get("summary") and previous.get("summary"):
            merged["summary"] = previous["summary"]
            merged["summary_origin"] = previous.get("summary_origin", "")
        merged["category"] = categorize(merged["title"], merged["source"])
        merged["tags"] = classify_tags(merged["title"], merged["source"], merged["category"])
        merged["first_seen"] = previous.get("first_seen") or now_iso

        before = {
            "title": previous.get("title"),
            "source": previous.get("source"),
            "published": previous.get("published"),
            "category": previous.get("category"),
            "summary": clean_summary(previous.get("summary", "")),
            "tags": previous.get("tags", []),
        }
        after = {
            "title": merged.get("title"),
            "source": merged.get("source"),
            "published": merged.get("published"),
            "category": merged.get("category"),
            "summary": clean_summary(merged.get("summary", "")),
            "tags": merged.get("tags", []),
        }
        merged["modified_at"] = now_iso if before != after else previous.get("modified_at", now_iso)
        merged["last_seen"] = now_iso
        by_url[url] = merged

    valid = []
    for item in by_url.values():
        if not valid_url(item.get("url", "")):
            continue
        if parse_date(item.get("published", "")) is None:
            continue
        if not item.get("first_seen"):
            item["first_seen"] = now_iso
        if not item.get("modified_at"):
            item["modified_at"] = now_iso
        valid.append(item)
    valid.sort(key=lambda x: parse_date(x["published"]), reverse=True)
    return prepare_items(valid)

def client_item(item):
    return {
        "title": item["title"],
        "url": item["url"],
        "signal_url": item["signal_url"],
        "source": item["source"],
        "published": item["published"],
        "category": item["category"],
        "tags": item.get("tags", []),
        "signal_score": item.get("signal_score", 0),
    }

def normalize_model_text(value):
    return value.replace("‑", "-").replace("–", "-").replace("—", "-")

def extract_models(title):
    text_value = normalize_model_text(title)
    found = []
    for pattern in MODEL_PATTERNS:
        for match in pattern.findall(text_value):
            name = re.sub(r"\s+", " ", match).strip()
            name = re.sub(r"gpt", "GPT", name, flags=re.I)
            name = re.sub(r"^GPT\s+(?=\d)", "GPT-", name)
            name = re.sub(r"claude", "Claude", name, flags=re.I)
            name = re.sub(r"gemini", "Gemini", name, flags=re.I)
            if name and name not in found:
                found.append(name)
                base = re.match(r"^(GPT-\d+(?:\.\d+)?)\s+", name, re.I)
                if base:
                    parent = re.sub(r"gpt", "GPT", base.group(1), flags=re.I)
                    if parent not in found:
                        found.append(parent)
    return found

def model_groups(items):
    groups = {}
    for item in items:
        for name in extract_models(item["title"]):
            groups.setdefault(name, []).append(item)
    return dict(sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0].lower())))

def tracked_models_html(items):
    groups = model_groups(items)
    cards = []
    for name, matched in list(groups.items())[:12]:
        cards.append(
            f'<a class="tracked-model" href="/models/{escape(slugify(name), quote=True)}/">'
            f'<span>{len(matched):02d}</span><strong>{escape(name)}</strong>'
            f'<small>{len(matched)} signal{"s" if len(matched) != 1 else ""}</small><b>↗</b></a>'
        )
    return "".join(cards)

def topic_matches(item, topic):
    if topic.get("source") and item["source"] == topic["source"]:
        return True
    tags = set(item.get("tags", []))
    if topic["name"] in tags:
        return True
    if topic.get("category") and item["category"] == topic["category"]:
        return True
    haystack = f'{item["title"]} {item.get("summary","")}'.lower()
    for keyword in topic.get("keywords", []):
        key = keyword.lower()
        if (" " in key and key in haystack) or (" " not in key and re.search(rf"\b{re.escape(key)}\b", haystack)):
            return True
    return False

def topic_groups(items):
    result = {}
    for topic in TOPICS:
        matches = [item for item in items if topic_matches(item, topic)]
        if matches:
            result[topic["slug"]] = (topic, matches)
    return result

def item_topics(item):
    return [topic for topic in TOPICS if topic_matches(item, topic)]

def display_date(value):
    d = parse_date(value)
    return d.strftime("%B %-d, %Y") if d is not None else "Unknown date"

def compact_description(item):
    editorial = item.get("editorial") or editorial_units(item)
    return editorial["what_changed"]

def category_context(category):
    return {
        "Models": "Tracked in the Models layer for model releases, capability shifts and deployment changes.",
        "Tools": "Tracked in the Tools layer for products, APIs, agents and practical AI workflows.",
        "Research": "Tracked in the Research layer for studies, evaluations, benchmarks, safety and scientific work.",
        "Open Source": "Tracked in the Open Source layer for repositories, weights, runtimes, frameworks and local AI.",
    }.get(category, "Tracked as part of the SXF AI signal layer.")

def category_path(category):
    return {
        "Models": "/models/",
        "Tools": "/tools/",
        "Research": "/research/",
        "Open Source": "/open-source/",
    }.get(category, "/signals/")

def page_header(active=""):
    links = [
        ("/models/", "Models", "models"),
        ("/tools/", "Tools", "tools"),
        ("/research/", "Research", "research"),
        ("/open-source/", "Open Source", "open-source"),
        ("/brief/", "Brief", "brief"),
        ("/about/", "About", "about"),
    ]
    nav_parts = []
    for href, label, key in links:
        current = ' aria-current="page"' if key == active else ""
        nav_parts.append(f'<a href="{href}"{current}>{label}</a>')
    nav = "".join(nav_parts)
    return f'''<header class="site-header"><div class="header-inner">
      <a class="brand" href="/" aria-label="SXF AI home"><span class="brand-mark">SXF</span><span class="brand-divider">/</span><span class="brand-ai">AI</span></a>
      <nav class="top-nav" aria-label="Primary navigation">{nav}</nav>
      <div class="header-status"><span class="pulse-dot"></span>LIVE</div>
    </div></header>'''

def page_footer():
    return '''<footer class="footer shell">
      <a class="brand footer-brand" href="/"><span class="brand-mark">SXF</span><span class="brand-divider">/</span><span class="brand-ai">AI</span></a>
      <p>Primary-source AI intelligence · <a href="/about/">Method & attribution</a></p>
      <p>© <span id="year"></span> SXF</p>
    </footer><script>document.getElementById("year").textContent=new Date().getFullYear();</script>'''

def page_head(title, description, canonical, schema, page_type="website"):
    safe_description = escape(description[:180], quote=True)
    return f'''<head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta name="color-scheme" content="dark" />
      <title>{escape(title)}</title>
      <meta name="description" content="{safe_description}" />
      <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />
      <meta name="googlebot" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />
      <meta name="theme-color" content="#07090d" />
      <link rel="canonical" href="{escape(canonical, quote=True)}" />
      <link rel="alternate" hreflang="en" href="{escape(canonical, quote=True)}" />
      <link rel="alternate" hreflang="x-default" href="{escape(canonical, quote=True)}" />
      <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
      <meta property="og:type" content="{escape(page_type, quote=True)}" />
      <meta property="og:site_name" content="SXF / AI" />
      <meta property="og:title" content="{escape(title, quote=True)}" />
      <meta property="og:description" content="{safe_description}" />
      <meta property="og:url" content="{escape(canonical, quote=True)}" />
      <meta name="twitter:card" content="summary" />
      <meta name="twitter:title" content="{escape(title, quote=True)}" />
      <meta name="twitter:description" content="{safe_description}" />
      <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")}</script>
      <link rel="stylesheet" href="/styles.css" />
      <link rel="stylesheet" href="/intelligence.css" />
    </head>'''

def related_items(item, items, limit=5):
    base_tokens = set(re.findall(r"[a-z0-9]+", normalize_model_text(item["title"]).lower())) - STOPWORDS
    scored = []
    for other in items:
        if other["url"] == item["url"]:
            continue
        other_tokens = set(re.findall(r"[a-z0-9]+", normalize_model_text(other["title"]).lower())) - STOPWORDS
        score = len(base_tokens & other_tokens)
        if other["source"] == item["source"]:
            score += 2
        if other["category"] == item["category"]:
            score += 1
        if score:
            scored.append((score, parse_date(other["published"]), other))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [row[2] for row in scored[:limit]]

def signal_row(item):
    return f'''<a class="signal-row" href="/signals/{escape(item["signal_slug"], quote=True)}/">
      <div class="signal-row-meta"><span>{escape(item["source"])}</span><time datetime="{escape(item["published"], quote=True)}">{escape(display_date(item["published"]))}</time></div>
      <h3>{escape(item["title"])}</h3>
      <div class="signal-row-foot"><span>{escape(item["category"])}</span><b>Open signal ↗</b></div>
    </a>'''

def signal_page_html(item, items):
    canonical = item["signal_url"]
    description = compact_description(item)
    modified = item.get("modified_at") or item["published"]
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Article",
                "@id": canonical + "#article",
                "headline": item["title"],
                "datePublished": item["published"],
                "dateModified": modified,
                "mainEntityOfPage": canonical,
                "url": canonical,
                "articleSection": item["category"],
                "isPartOf": {"@id": "https://sxf.si/#website"},
                "author": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "creator": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "citation": item["url"],
                "inLanguage": "en",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Signals", "item": BASE_URL + "/signals/"},
                    {"@type": "ListItem", "position": 3, "name": item["category"], "item": BASE_URL + category_path(item["category"])},
                ],
            },
        ],
    }
    topics = item_topics(item)
    models = extract_models(item["title"])
    topic_links = "".join(
        f'<a href="/topics/{escape(t["slug"], quote=True)}/">{escape(t["name"])}</a>' for t in topics[:4]
    )
    model_links = "".join(
        f'<a href="/models/{escape(slugify(name), quote=True)}/">{escape(name)}</a>' for name in models[:4]
    )
    related = "".join(signal_row(x) for x in related_items(item, items))
    editorial = item.get("editorial") or editorial_units(item)
    summary_label = "Source summary" if item.get("summary") else "SXF signal note"
    return f'''<!doctype html><html lang="en">
    {page_head(item["title"] + " | SXF / AI", description, canonical, schema, "article")}
    <body class="intel-page signal-page">
      <a class="skip-link" href="#signal-main">Skip to signal</a>
      <div class="ambient ambient-one" aria-hidden="true"></div><div class="ambient ambient-two" aria-hidden="true"></div>
      {page_header()}
      <main id="signal-main">
        <section class="intel-hero shell">
          <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/signals/">Signals</a><span>/</span><a href="{escape(category_path(item["category"]), quote=True)}">{escape(item["category"])}</a></nav>
          <div class="intel-kicker"><span class="pulse-dot"></span> SIGNAL / {escape(item["category"].upper())}</div>
          <h1>{escape(item["title"])}</h1>
          <div class="signal-meta-strip">
            <div><span>SOURCE</span><strong>{escape(item["source"])}</strong></div>
            <div><span>PUBLISHED</span><strong>{escape(display_date(item["published"]))}</strong></div>
            <div><span>LAYER</span><strong>{escape(item["category"])}</strong></div>
            <div><span>SIGNAL SCORE</span><strong>{item.get("signal_score", 0):02d}/100</strong></div>
          </div>
        </section>
        <section class="signal-layout shell">
          <article class="signal-brief">
            <p class="eyebrow">{summary_label.upper()}</p>
            <p class="signal-summary">{escape(editorial["what_changed"])}</p>
            <div class="signal-context"><span>WHY IT MATTERS</span><p>{escape(editorial["why_it_matters"])}</p></div>
            <div class="signal-context"><span>WHAT TO VERIFY</span><p>{escape(editorial["what_to_verify"])}</p></div>
          </article>
          <aside class="source-card">
            <span class="source-card-label">SOURCE OF RECORD</span><strong>{escape(item["source"])}</strong>
            <p>Read the original publication for the complete context behind this signal.</p>
            <a href="{escape(item["url"], quote=True)}" target="_blank" rel="noopener noreferrer">Open original source <b>↗</b></a>
          </aside>
        </section>
        <section class="signal-taxonomy shell">
          <div><span>TOPICS</span>{topic_links or '<small>No topic tag yet</small>'}</div>
          <div><span>MODELS</span>{model_links or '<small>No named model detected</small>'}</div>
        </section>
        <section class="related-signals shell">
          <div class="intel-section-head"><div><p class="eyebrow">RELATED SIGNALS</p><h2>Keep the context connected.</h2></div><a href="/signals/">All signals ↗</a></div>
          <div class="signal-list">{related}</div>
        </section>
      </main>
      {page_footer()}
    </body></html>'''
def signals_index_html(items):
    canonical = f"{BASE_URL}/signals/"
    description = "Latest AI signals tracked by SXF / AI across models, tools, research and open source, with direct links to primary sources."
    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "AI Signals | SXF / AI",
        "url": canonical,
        "isPartOf": {"@id": "https://sxf.si/#website"},
        "inLanguage": "en",
    }
    rows = "".join(signal_row(item) for item in items[:40])
    return f'''<!doctype html><html lang="en">{page_head("AI Signals — Latest Primary-Source AI Updates | SXF / AI", description, canonical, schema)}
    <body class="intel-page collection-page"><a class="skip-link" href="#signals-main">Skip to signals</a>
    {page_header()}<main id="signals-main">
      <section class="collection-hero shell">
        <p class="eyebrow">SXF SIGNAL INDEX</p><h1>The AI changes<br><span>worth opening.</span></h1>
        <p>Models, tools, research and open-source developments organized as traceable signals with the primary source kept one click away.</p>
        <div class="collection-stats"><div><strong>{len(items)}</strong><span>tracked signals</span></div><div><strong>4</strong><span>intelligence layers</span></div><div><strong>3h</strong><span>refresh cycle</span></div></div>
      </section>
      <section class="related-signals shell"><div class="intel-section-head"><div><p class="eyebrow">LATEST</p><h2>Signal stream.</h2></div><a href="/brief/">Read today’s brief ↗</a></div><div class="signal-list">{rows}</div></section>
    </main>{page_footer()}</body></html>'''

def topic_page_html(topic, items):
    canonical = f'{BASE_URL}/topics/{topic["slug"]}/'
    schema = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": f'{topic["name"]} AI Signals | SXF / AI', "url": canonical,
        "description": topic["description"], "isPartOf": {"@id": "https://sxf.si/#website"}, "inLanguage": "en"
    }
    rows = "".join(signal_row(item) for item in items[:30])
    return f'''<!doctype html><html lang="en">{page_head(topic["name"] + " — AI Signals | SXF / AI", topic["description"], canonical, schema)}
    <body class="intel-page topic-page">{page_header()}<main>
      <section class="collection-hero shell"><nav class="intel-breadcrumb"><a href="/">SXF</a><span>/</span><a href="/topics/">Topics</a><span>/</span><span>{escape(topic["name"])}</span></nav>
      <p class="eyebrow">TOPIC INTELLIGENCE</p><h1>{escape(topic["name"])}<br><span>signal history.</span></h1><p>{escape(topic["description"])}</p>
      <div class="collection-stats"><div><strong>{len(items)}</strong><span>tracked signals</span></div><div><strong>Primary</strong><span>source links</span></div><div><strong>Live</strong><span>rolling index</span></div></div></section>
      <section class="related-signals shell"><div class="intel-section-head"><div><p class="eyebrow">RECENT</p><h2>Latest in {escape(topic["name"])}.</h2></div><a href="/topics/">All topics ↗</a></div><div class="signal-list">{rows}</div></section>
    </main>{page_footer()}</body></html>'''

def topics_index_html(groups):
    canonical = f"{BASE_URL}/topics/"
    description = "Explore SXF / AI topic intelligence across companies, agents, coding AI, multimodal systems, safety and open-source AI."
    schema = {"@context":"https://schema.org","@type":"CollectionPage","name":"AI Topics | SXF / AI","url":canonical,"isPartOf":{"@id":"https://sxf.si/#website"},"inLanguage":"en"}
    cards = "".join(
        f'''<a class="topic-card" href="/topics/{escape(slug, quote=True)}/"><span>{len(items):02d}</span><h2>{escape(topic["name"])}</h2><p>{escape(topic["description"])}</p><b>Open topic ↗</b></a>'''
        for slug,(topic,items) in groups.items()
    )
    return f'''<!doctype html><html lang="en">{page_head("AI Topics — Companies, Agents, Safety & Open Source | SXF / AI", description, canonical, schema)}
    <body class="intel-page topics-page">{page_header()}<main>
    <section class="collection-hero shell"><p class="eyebrow">TOPIC MAP</p><h1>Follow the subject,<br><span>not just the headline.</span></h1><p>Persistent topic pages turn individual releases into a navigable signal history.</p></section>
    <section class="topic-grid shell">{cards}</section></main>{page_footer()}</body></html>'''

def model_page_html(name, items):
    slug = slugify(name)
    canonical = f"{BASE_URL}/models/{slug}/"
    description = f"Track {name} releases, capability changes and related primary-source signals on SXF / AI."
    schema = {"@context":"https://schema.org","@type":"CollectionPage","name":f"{name} updates | SXF / AI","url":canonical,"description":description,"isPartOf":{"@id":"https://sxf.si/#website"},"about":{"@type":"Thing","name":name},"inLanguage":"en"}
    rows = "".join(signal_row(item) for item in items[:30])
    return f'''<!doctype html><html lang="en">{page_head(name + " — Releases & Signals | SXF / AI", description, canonical, schema)}
    <body class="intel-page model-page">{page_header("models")}<main>
      <section class="collection-hero shell"><nav class="intel-breadcrumb"><a href="/">SXF</a><span>/</span><a href="/models/">Models</a><span>/</span><span>{escape(name)}</span></nav>
      <p class="eyebrow">MODEL INTELLIGENCE</p><h1>{escape(name)}<br><span>release signals.</span></h1><p>{escape(description)}</p>
      <div class="collection-stats"><div><strong>{len(items)}</strong><span>tracked signals</span></div><div><strong>Primary</strong><span>source trail</span></div><div><strong>Rolling</strong><span>release history</span></div></div></section>
      <section class="related-signals shell"><div class="intel-section-head"><div><p class="eyebrow">MODEL TIMELINE</p><h2>Recent {escape(name)} signals.</h2></div><a href="/models/">All models ↗</a></div><div class="signal-list">{rows}</div></section>
    </main>{page_footer()}</body></html>'''

def brief_issue_html(items, issue_date):
    selected = select_brief_items(items)
    pretty = issue_date.strftime("%B %-d, %Y")
    slug = issue_date.isoformat()
    canonical = f"{BASE_URL}/brief/{slug}/"
    description = f"SXF Brief for {pretty}: five AI signals from primary sources across models, tools, research and open source."
    schema = {"@context":"https://schema.org","@type":"Article","headline":f"SXF Brief — {pretty}","datePublished":issue_date.isoformat(),"mainEntityOfPage":canonical,"isPartOf":{"@id":"https://sxf.si/#website"},"creator":{"@id":"https://vivamediacreative.com/labs/#organization"},"inLanguage":"en"}
    cards = ""
    for i,item in enumerate(selected, 1):
        cards += f'''<article class="brief-signal"><span class="brief-no">{i:02d}</span><div><div class="brief-meta"><strong>{escape(item["source"])}</strong><span>{escape(item["category"])}</span><span>SCORE {item.get("signal_score",0):02d}</span></div><h2><a href="/signals/{escape(item["signal_slug"], quote=True)}/">{escape(item["title"])}</a></h2><p>{escape(compact_description(item))}</p><a class="brief-open" href="/signals/{escape(item["signal_slug"], quote=True)}/">Open signal ↗</a></div></article>'''
    return f'''<!doctype html><html lang="en">{page_head("SXF Brief — " + pretty, description, canonical, schema, "article")}
    <body class="intel-page brief-page">{page_header("brief")}<main>
      <section class="brief-issue-hero shell"><div><p class="eyebrow">SXF BRIEF / {escape(slug)}</p><h1>Five signals.<br><span>Zero noise.</span></h1></div><p>Five high-priority signals selected by SXF’s internal scoring system, with source and category diversity built into the shortlist. Every item keeps the primary source attached.</p></section>
      <section class="brief-stack shell">{cards}</section>
      <section class="brief-note shell"><span>METHOD</span><p>The brief is a discovery layer, not a substitute for the source. Open each signal for attribution and the original publication.</p><a href="/about/">Read SXF methodology ↗</a></section>
    </main>{page_footer()}</body></html>'''

def brief_index_html(items, issue_date):
    selected = select_brief_items(items)
    current = issue_date.isoformat()
    canonical = f"{BASE_URL}/brief/"
    description = "SXF Brief: five primary-source AI signals to scan each day, selected from the live SXF radar."
    schema = {"@context":"https://schema.org","@type":"CollectionPage","name":"SXF Brief","url":canonical,"description":description,"isPartOf":{"@id":"https://sxf.si/#website"},"inLanguage":"en"}
    archive = []
    if BRIEF_DIR.exists():
        for p in sorted(BRIEF_DIR.iterdir(), reverse=True):
            if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name):
                archive.append(p.name)
    archive_html = "".join(f'<a href="/brief/{d}/"><span>{d}</span><b>Open issue ↗</b></a>' for d in archive[:14])
    return f'''<!doctype html><html lang="en">{page_head("SXF Brief — Five AI Signals, Zero Noise", description, canonical, schema)}
    <body class="intel-page brief-index">{page_header("brief")}<main>
      <section class="collection-hero shell"><p class="eyebrow">DAILY INTELLIGENCE</p><h1>Five signals.<br><span>Zero noise.</span></h1><p>A compact daily read built from SXF’s live primary-source radar.</p><div class="hero-actions"><a class="primary-cta" href="/brief/{current}/">Read latest brief <span>↗</span></a><a class="secondary-cta" href="/signals/">Browse all signals</a></div></section>
      <section class="brief-preview shell"><div class="intel-section-head"><div><p class="eyebrow">LATEST ISSUE</p><h2>{escape(issue_date.strftime("%B %-d, %Y"))}</h2></div><a href="/brief/{current}/">Open full issue ↗</a></div>
      <div class="brief-preview-grid">{"".join(f'<a href="/signals/{escape(x["signal_slug"], quote=True)}/"><span>{i:02d}</span><strong>{escape(x["title"])}</strong><small>{escape(x["source"])} · {escape(x["category"])}</small></a>' for i,x in enumerate(selected,1))}</div></section>
      <section class="brief-archive shell"><p class="eyebrow">ARCHIVE</p><div>{archive_html}</div></section>
    </main>{page_footer()}</body></html>'''

def build_discovery_pages(items, current_items):
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    TOPICS_DIR.mkdir(parents=True, exist_ok=True)
    BRIEF_DIR.mkdir(parents=True, exist_ok=True)

    (SIGNALS_DIR / "index.html").write_text(signals_index_html(items), encoding="utf-8")
    for item in items:
        path = SIGNALS_DIR / item["signal_slug"]
        path.mkdir(parents=True, exist_ok=True)
        (path / "index.html").write_text(signal_page_html(item, items), encoding="utf-8")

    groups = topic_groups(items)
    (TOPICS_DIR / "index.html").write_text(topics_index_html(groups), encoding="utf-8")
    for slug, (topic, matched) in groups.items():
        path = TOPICS_DIR / slug
        path.mkdir(parents=True, exist_ok=True)
        (path / "index.html").write_text(topic_page_html(topic, matched), encoding="utf-8")

    for name, matched in model_groups(items).items():
        if not matched:
            continue
        path = ROOT / "models" / slugify(name)
        path.mkdir(parents=True, exist_ok=True)
        (path / "index.html").write_text(model_page_html(name, matched), encoding="utf-8")

    issue_date = datetime.now(timezone.utc).date()
    issue_dir = BRIEF_DIR / issue_date.isoformat()
    issue_dir.mkdir(parents=True, exist_ok=True)
    (issue_dir / "index.html").write_text(brief_issue_html(current_items, issue_date), encoding="utf-8")
    (BRIEF_DIR / "index.html").write_text(brief_index_html(current_items, issue_date), encoding="utf-8")
def sitemap_entry(url, lastmod):
    return f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod></url>"

def update_sitemap(items):
    generated_today = datetime.now(timezone.utc).date().isoformat()
    rows = [
        sitemap_entry(f"{BASE_URL}/", generated_today),
        sitemap_entry(f"{BASE_URL}/models/", generated_today),
        sitemap_entry(f"{BASE_URL}/tools/", generated_today),
        sitemap_entry(f"{BASE_URL}/research/", generated_today),
        sitemap_entry(f"{BASE_URL}/open-source/", generated_today),
        sitemap_entry(f"{BASE_URL}/signals/", generated_today),
        sitemap_entry(f"{BASE_URL}/topics/", generated_today),
        sitemap_entry(f"{BASE_URL}/brief/", generated_today),
        sitemap_entry(f"{BASE_URL}/about/", generated_today),
    ]

    for item in items:
        modified = parse_date(item.get("modified_at", "")) or parse_date(item["published"])
        rows.append(sitemap_entry(item["signal_url"], modified.date().isoformat()))

    for slug, (_topic, _matched) in topic_groups(items).items():
        rows.append(sitemap_entry(f"{BASE_URL}/topics/{slug}/", generated_today))

    for name in model_groups(items):
        rows.append(sitemap_entry(f"{BASE_URL}/models/{slugify(name)}/", generated_today))

    if BRIEF_DIR.exists():
        for p in sorted(BRIEF_DIR.iterdir()):
            if p.is_dir() and re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.name):
                rows.append(sitemap_entry(f"{BASE_URL}/brief/{p.name}/", p.name))

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(rows) + "\n</urlset>\n"
    SITEMAP.write_text(xml, encoding="utf-8")
def main():
    incoming = []
    errors = []
    for source, url in SOURCES:
        try:
            incoming.extend(parse_feed(source, fetch(url)))
        except Exception as exc:
            errors.append(f"{source}: {exc}")

    existing = load_items(ARCHIVE_OUT)
    if not existing:
        existing = load_items(OUT)
    existing_by_url = {item.get("url"): item for item in existing if item.get("url")}
    ingest_cutoff = datetime.now(timezone.utc) - timedelta(days=INITIAL_ARCHIVE_DAYS)
    incoming = [
        item for item in incoming
        if parse_date(item.get("published", "")) is not None and parse_date(item["published"]) >= ingest_cutoff
    ]
    enriched = enrich_summaries(incoming, existing_by_url)

    archive = merge_archive(existing, incoming)
    if not archive:
        raise RuntimeError("No valid signals available after archive merge")

    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    current = [
        item for item in archive
        if parse_date(item["published"]) is not None and parse_date(item["published"]) >= cutoff
    ][:MAX_ITEMS]
    if not current:
        current = archive[:MAX_ITEMS]

    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    ARCHIVE_OUT.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE_OUT.write_text(json.dumps({
        "updated_at": now_iso,
        "items": archive,
        "feed_errors": errors,
        "scoring_version": "sxf-signal-score-v2",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    OUT.write_text(json.dumps({
        "updated_at": now_iso,
        "items": [client_item(item) for item in current],
        "feed_errors": errors,
        "scoring_version": "sxf-signal-score-v2",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    update_index(current)
    update_section_pages(current)
    build_discovery_pages(archive, current)
    update_sitemap(archive)
    print(
        f"Wrote {len(current)} current signals from {len(archive)} archived signals; "
        f"enriched {enriched} summaries; source errors: {len(errors)}"
    )
if __name__ == "__main__":
    main()
