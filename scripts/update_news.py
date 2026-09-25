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
SLUG_ALIASES_PATH = ROOT / "data" / "slug_aliases.json"
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
        page = page.replace('<a href="/open-source/">Open Source</a><a href="/brief/">Brief</a>', '<a href="/open-source/">Open Source</a><a href="/guides/">Guides</a><a href="/brief/">Brief</a>')
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
COMPARE_DIR = ROOT / "compare"
GUIDES_DIR = ROOT / "guides"
GPT6_COMPARE_SLUG = "gpt-6-astra-vs-sol-vs-luna"
GPT6_SOL_CLAUDE_COMPARE_SLUG = "gpt-6-sol-vs-claude-opus-5-5"

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
    {
        "slug": "ai-security",
        "name": "AI Security",
        "description": "Security controls, sandboxing, cyber defense and deployment safeguards across AI products and infrastructure.",
        "keywords": ["security", "cyber", "sandbox", "sandboxing", "proof of presence"],
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

def load_slug_aliases():
    if not SLUG_ALIASES_PATH.exists():
        return {}
    try:
        data = json.loads(SLUG_ALIASES_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

SLUG_ALIASES = load_slug_aliases()

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
        row["signal_slug"] = SLUG_ALIASES.get(row["url"]) or row.get("signal_slug") or signal_slug(row)
        row["signal_url"] = f'{BASE_URL}/signals/{row["signal_slug"]}/'
        score, factors = signal_score(row)
        row["signal_score"] = score
        row["score_factors"] = factors
        quality_score, quality_factors = seo_quality(row)
        row["seo_quality_score"] = quality_score
        row["seo_quality_factors"] = quality_factors
        row["seo_eligible"] = seo_signal_eligible(row, quality_score)
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

    # Handle grouped family announcements such as "GPT-6 Sol and Luna".
    grouped = re.search(r"\b(GPT[- ]\d+(?:\.\d+)?)\s+(Astra|Sol|Luna)\s+(?:and|&)\s+(Astra|Sol|Luna)\b", text_value, re.I)
    if grouped:
        family = re.sub(r"^GPT\s+(?=\d)", "GPT-", grouped.group(1), flags=re.I)
        family = re.sub(r"gpt", "GPT", family, flags=re.I)
        for variant in (grouped.group(2), grouped.group(3)):
            full = f"{family} {variant.title()}"
            if full not in found:
                found.append(full)
        if family not in found:
            found.append(family)
    return found

SEO_MIN_SUMMARY_CHARS = 90
SEO_MIN_QUALITY_SCORE = 50
SEO_STRONG_EVENT = re.compile(
    r"\bintroducing\b|\blaunch(?:ed|es)?\b|\brelease(?:d|s)?\b|\bnow available\b|"
    r"\bavailable\b|\bbenchmark\b|\bevaluation\b|\bframework\b|\bpricing\b|"
    r"\bsafety overview\b|\bnew features?\b|\bimprovements?\b|\bexpands?\b|\bprompt caching\b",
    re.I,
)
SEO_HIGH_VALUE_TAGS = {
    "GitHub Copilot", "AI Agents", "Coding AI", "Multimodal AI",
    "Open Source AI", "Research", "Security",
}
MODEL_CASE_STUDY = re.compile(
    r"\bhelps?\b|\btrusts?\b|\bcuts?\b|\bboost(?:ing|s|ed)?\b|\busing\b|\bwith GPT\b",
    re.I,
)

MODEL_REFERENCE = {
    "GPT-6": {
        "provider": "OpenAI",
        "summary": "GPT-6 is OpenAI’s current flagship model family, spanning Astra for the hardest end-to-end work, Sol for demanding coding and agentic workflows, and Luna for efficient high-volume tasks.",
        "pricing_note": "Standard API pricing per 1M text tokens for prompts up to 272K input tokens. Longer prompts use higher rates.",
        "modalities": "Text and image input · text output",
        "variants": [
            {
                "name": "GPT-6 Astra",
                "model_id": "gpt-6-astra",
                "positioning": "Highest capability",
                "best_for": "Complex reasoning, coding, computer use, research and document creation",
                "context": "1,050,000",
                "max_output": "128,000",
                "knowledge_cutoff": "Apr 30, 2026",
                "input_price": "$10.00",
                "cached_price": "$1.00",
                "output_price": "$50.00",
                "released": "Sep 3, 2026",
                "source": "https://developers.openai.com/api/docs/models/gpt-6-astra",
            },
            {
                "name": "GPT-6 Sol",
                "model_id": "gpt-6-sol",
                "positioning": "Capability / cost balance",
                "best_for": "Complex coding and agentic workflows",
                "context": "1,050,000",
                "max_output": "128,000",
                "knowledge_cutoff": "Apr 20, 2026",
                "input_price": "$2.00",
                "cached_price": "$0.20",
                "output_price": "$10.00",
                "released": "Sep 22, 2026",
                "source": "https://developers.openai.com/api/docs/models/gpt-6-sol",
            },
            {
                "name": "GPT-6 Luna",
                "model_id": "gpt-6-luna",
                "positioning": "Efficiency",
                "best_for": "Focused, high-volume and cost-sensitive workloads",
                "context": "1,050,000",
                "max_output": "128,000",
                "knowledge_cutoff": "May 18, 2026",
                "input_price": "$0.10",
                "cached_price": "$0.01",
                "output_price": "$0.50",
                "released": "Sep 22, 2026",
                "source": "https://developers.openai.com/api/docs/models/gpt-6-luna",
            },
        ],
        "sources": [
            ("OpenAI model catalog", "https://developers.openai.com/api/docs/models"),
            ("OpenAI API pricing", "https://developers.openai.com/api/docs/pricing"),
            ("GPT-6 model guidance", "https://developers.openai.com/api/docs/guides/latest-model"),
            ("OpenAI API changelog", "https://developers.openai.com/api/docs/changelog"),
        ],
        "faq": [
            ("What models are in the GPT-6 family?", "OpenAI currently lists GPT-6 Astra, GPT-6 Sol and GPT-6 Luna as the flagship GPT-6 family."),
            ("What is the GPT-6 context window?", "Astra, Sol and Luna each have a 1,050,000-token context window and support up to 128,000 output tokens."),
            ("How much does GPT-6 cost in the API?", "For Standard API requests up to 272K input tokens, Astra is $10 input / $50 output per 1M tokens, Sol is $2 / $10, and Luna is $0.10 / $0.50. Cached-input rates are lower."),
            ("What is each GPT-6 model for?", "OpenAI positions Astra for the hardest end-to-end work, Sol for complex coding and agentic workflows, and Luna for efficient high-volume tasks."),
        ],
    }
}

def model_reference(name):
    if name == "GPT-6" or name.startswith("GPT-6 "):
        return MODEL_REFERENCE["GPT-6"]
    return None

def model_reference_html(name):
    ref = model_reference(name)
    if not ref:
        return ""

    variants = ref["variants"]
    selected = next((v for v in variants if v["name"].lower() == name.lower()), None)
    focus = selected or None
    verified = datetime.now(timezone.utc).date().isoformat()

    if focus:
        facts = f'''<div class="model-fact-grid">
          <div><span>MODEL ID</span><strong>{escape(focus["model_id"])}</strong></div>
          <div><span>CONTEXT WINDOW</span><strong>{escape(focus["context"])}</strong><small>tokens</small></div>
          <div><span>MAX OUTPUT</span><strong>{escape(focus["max_output"])}</strong><small>tokens</small></div>
          <div><span>KNOWLEDGE CUTOFF</span><strong>{escape(focus["knowledge_cutoff"])}</strong></div>
          <div><span>STANDARD INPUT</span><strong>{escape(focus["input_price"])}</strong><small>/ 1M tokens</small></div>
          <div><span>STANDARD OUTPUT</span><strong>{escape(focus["output_price"])}</strong><small>/ 1M tokens</small></div>
        </div>'''
        intro = f'''<div class="model-reference-copy"><p class="eyebrow">MODEL REFERENCE</p><h2>{escape(name)} at a glance.</h2>
          <p>{escape(focus["best_for"])}. OpenAI lists a {escape(focus["context"])}-token context window, up to {escape(focus["max_output"])} output tokens and a {escape(focus["knowledge_cutoff"])} knowledge cutoff.</p>
          <p class="reference-note">Released {escape(focus["released"])} · {escape(ref["modalities"])} · Last verified {escape(verified)}</p></div>'''
    else:
        facts = '''<div class="model-fact-grid">
          <div><span>FAMILY</span><strong>3</strong><small>flagship variants</small></div>
          <div><span>CONTEXT WINDOW</span><strong>1,050,000</strong><small>tokens across family</small></div>
          <div><span>MAX OUTPUT</span><strong>128,000</strong><small>tokens across family</small></div>
          <div><span>INPUT</span><strong>Text + image</strong></div>
          <div><span>OUTPUT</span><strong>Text</strong></div>
          <div><span>PROVIDER</span><strong>OpenAI</strong></div>
        </div>'''
        intro = f'''<div class="model-reference-copy"><p class="eyebrow">MODEL REFERENCE</p><h2>GPT-6 family at a glance.</h2>
          <p>{escape(ref["summary"])}</p>
          <p class="reference-note">{escape(ref["modalities"])} · Last verified {escape(verified)}</p></div>'''

    rows = "".join(
        f'''<tr class="{"is-current" if focus and v["name"] == focus["name"] else ""}">
          <th scope="row"><a href="/models/{escape(slugify(v["name"]), quote=True)}/">{escape(v["name"])}</a><small>{escape(v["model_id"])}</small></th>
          <td>{escape(v["positioning"])}</td><td>{escape(v["context"])}</td><td>{escape(v["max_output"])}</td>
          <td>{escape(v["input_price"])}</td><td>{escape(v["cached_price"])}</td><td>{escape(v["output_price"])}</td>
        </tr>''' for v in variants
    )
    sources = "".join(
        f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(label)}</span><b>↗</b></a>'
        for label, url in ref["sources"]
    )
    faq = "".join(
        f'<details><summary>{escape(question)}</summary><p>{escape(answer)}</p></details>'
        for question, answer in ref["faq"]
    )
    return f'''<section class="model-reference shell">
      <div class="model-reference-intro">{intro}{facts}</div>
      <div class="model-comparison">
        <div class="intel-section-head"><div><p class="eyebrow">FAMILY COMPARISON</p><h2>Astra, Sol and Luna.</h2></div><a class="comparison-cta" href="/compare/{GPT6_COMPARE_SLUG}/">Full decision guide ↗</a></div>
        <div class="model-table-wrap"><table><thead><tr><th>Model</th><th>Positioning</th><th>Context</th><th>Max output</th><th>Input</th><th>Cached</th><th>Output</th></tr></thead><tbody>{rows}</tbody></table></div>
        <p class="reference-note">{escape(ref["pricing_note"])}</p>
      </div>
      <div class="model-reference-lower">
        <div class="model-sources"><p class="eyebrow">OFFICIAL SOURCES</p>{sources}</div>
        <div class="model-faq"><p class="eyebrow">QUICK ANSWERS</p>{faq}</div>
      </div>
    </section>'''

def seo_quality(item):
    summary_len = len(clean_summary(item.get("summary", "")))
    score = 30 if summary_len >= 120 else 24 if summary_len >= 90 else 14 if summary_len >= 60 else 0
    factors = []

    if summary_len >= SEO_MIN_SUMMARY_CHARS:
        factors.append("substantive-source-summary")
    if SEO_STRONG_EVENT.search(item["title"]):
        score += 18
        factors.append("search-worthy-event")
    if extract_models(item["title"]):
        score += 18
        factors.append("named-model")

    signal = item.get("signal_score", 0)
    score += 15 if signal >= 55 else 12 if signal >= 45 else 9 if signal >= 38 else 3

    if item["category"] in {"Models", "Research", "Open Source"}:
        score += 8
        factors.append("durable-intelligence-layer")
    if SEO_HIGH_VALUE_TAGS.intersection(item.get("tags", [])):
        score += 10
        factors.append("high-value-topic")

    if item["category"] == "Models" and not SEO_STRONG_EVENT.search(item["title"]) and MODEL_CASE_STUDY.search(item["title"]):
        score -= 20
        factors.append("case-study-penalty")

    return max(0, min(100, score)), factors

def seo_signal_eligible(item, quality_score=None):
    summary_len = len(clean_summary(item.get("summary", "")))
    if summary_len < SEO_MIN_SUMMARY_CHARS:
        return False
    if quality_score is None:
        quality_score, _ = seo_quality(item)
    return quality_score >= SEO_MIN_QUALITY_SCORE

def model_page_indexable(name, items):
    substantive = [item for item in items if len(clean_summary(item.get("summary", ""))) >= SEO_MIN_SUMMARY_CHARS]
    if len(items) >= 2 and len(substantive) >= 2:
        return True
    return any(
        item.get("seo_eligible", seo_signal_eligible(item))
        and SEO_STRONG_EVENT.search(item["title"])
        for item in items
    )

def topic_page_indexable(items):
    substantive = sum(
        1 for item in items
        if len(clean_summary(item.get("summary", ""))) >= SEO_MIN_SUMMARY_CHARS
    )
    return len(items) >= 3 and substantive >= 2

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
        ("/guides/", "Guides", "guides"),
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

def page_head(title, description, canonical, schema, page_type="website", robots="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1"):
    safe_description = escape(description[:180], quote=True)
    return f'''<head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta name="color-scheme" content="dark" />
      <title>{escape(title)}</title>
      <meta name="description" content="{safe_description}" />
      <meta name="robots" content="{escape(robots, quote=True)}" />
      <meta name="googlebot" content="{escape(robots, quote=True)}" />
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
    indexable = bool(item.get("seo_eligible", seo_signal_eligible(item)))
    robots = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" if indexable else "noindex,follow"
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
    {page_head(item["title"] + " | SXF / AI", description, canonical, schema, "article", robots)}
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
    latest = items[0]
    latest_summary = clean_summary(latest.get("summary", "")) or compact_description(latest)
    first_date = display_date(items[-1]["published"])
    latest_date = display_date(latest["published"])
    source_count = len({item["source"] for item in items})
    robots = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" if topic_page_indexable(items) else "noindex,follow"
    schema = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": f'{topic["name"]} AI Signals | SXF / AI', "url": canonical,
        "description": topic["description"], "isPartOf": {"@id": "https://sxf.si/#website"}, "inLanguage": "en"
    }
    rows = "".join(signal_row(item) for item in items[:30])
    return f'''<!doctype html><html lang="en">{page_head(topic["name"] + " — AI Signals | SXF / AI", topic["description"], canonical, schema, robots=robots)}
    <body class="intel-page topic-page">{page_header()}<main>
      <section class="collection-hero shell"><nav class="intel-breadcrumb"><a href="/">SXF</a><span>/</span><a href="/topics/">Topics</a><span>/</span><span>{escape(topic["name"])}</span></nav>
      <p class="eyebrow">TOPIC INTELLIGENCE</p><h1>{escape(topic["name"])}<br><span>signal history.</span></h1><p>{escape(topic["description"])}</p>
      <div class="collection-stats"><div><strong>{len(items)}</strong><span>tracked signals</span></div><div><strong>{source_count}</strong><span>primary sources</span></div><div><strong>{escape(latest_date)}</strong><span>latest tracked</span></div></div></section>
      <section class="signal-layout shell"><article class="signal-brief"><p class="eyebrow">LATEST DEVELOPMENT</p><h2>{escape(latest["title"])}</h2><p class="signal-summary">{escape(latest_summary)}</p><a class="brief-open" href="/signals/{escape(latest["signal_slug"], quote=True)}/">Open latest signal ↗</a></article>
      <aside class="source-card"><span class="source-card-label">COVERAGE WINDOW</span><strong>{escape(topic["name"])}</strong><p>Tracked from {escape(first_date)} through {escape(latest_date)} across {source_count} primary source{"s" if source_count != 1 else ""}.</p></aside></section>
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
    ref = model_reference(name)
    if ref:
        description = (
            f"{name} reference: pricing, context window, API specifications, model family details "
            f"and the latest primary-source updates tracked by SXF / AI."
        )
        title = f"{name} — Pricing, Context Window, API & Updates | SXF / AI" if name != "GPT-6" else "GPT-6 Models — Pricing, Context Window & Updates | SXF / AI"
    else:
        description = f"Track {name} releases, capability changes and related primary-source signals on SXF / AI."
        title = name + " — Releases & Signals | SXF / AI"
    latest = items[0]
    latest_summary = clean_summary(latest.get("summary", "")) or compact_description(latest)
    first_date = display_date(items[-1]["published"])
    latest_date = display_date(latest["published"])
    source_count = len({item["source"] for item in items})
    robots = "index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" if model_page_indexable(name, items) else "noindex,follow"
    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {
                "@type":"CollectionPage","name":f"{name} reference and updates | SXF / AI","url":canonical,
                "description":description,"isPartOf":{"@id":"https://sxf.si/#website"},
                "about":{"@type":"Thing","name":name},"inLanguage":"en"
            },
            {
                "@type":"BreadcrumbList",
                "itemListElement":[
                    {"@type":"ListItem","position":1,"name":"SXF / AI","item":BASE_URL + "/"},
                    {"@type":"ListItem","position":2,"name":"Models","item":BASE_URL + "/models/"},
                    {"@type":"ListItem","position":3,"name":name,"item":canonical},
                ]
            }
        ]
    }
    rows = "".join(signal_row(item) for item in items[:30])
    reference = model_reference_html(name)
    return f'''<!doctype html><html lang="en">{page_head(title, description, canonical, schema, robots=robots)}
    <body class="intel-page model-page">{page_header("models")}<main>
      <section class="collection-hero shell"><nav class="intel-breadcrumb"><a href="/">SXF</a><span>/</span><a href="/models/">Models</a><span>/</span><span>{escape(name)}</span></nav>
      <p class="eyebrow">MODEL INTELLIGENCE</p><h1>{escape(name)}<br><span>{"reference & signals." if ref else "release signals."}</span></h1><p>{escape(description)}</p>
      <div class="collection-stats"><div><strong>{len(items)}</strong><span>tracked signals</span></div><div><strong>{source_count}</strong><span>primary sources</span></div><div><strong>{escape(latest_date)}</strong><span>latest tracked</span></div></div></section>
      {reference}
      <section class="signal-layout shell"><article class="signal-brief"><p class="eyebrow">LATEST DEVELOPMENT</p><h2>{escape(latest["title"])}</h2><p class="signal-summary">{escape(latest_summary)}</p><a class="brief-open" href="/signals/{escape(latest["signal_slug"], quote=True)}/">Open latest signal ↗</a></article>
      <aside class="source-card"><span class="source-card-label">MODEL TIMELINE</span><strong>{escape(name)}</strong><p>Tracked from {escape(first_date)} through {escape(latest_date)} across {source_count} primary source{"s" if source_count != 1 else ""}.</p></aside></section>
      <section class="related-signals shell"><div class="intel-section-head"><div><p class="eyebrow">MODEL TIMELINE</p><h2>Recent {escape(name)} signals.</h2></div><a href="/models/">All models ↗</a></div><div class="signal-list">{rows}</div></section>
    </main>{page_footer()}</body></html>'''




def best_ai_coding_tools_html(items):
    canonical = f"{BASE_URL}/guides/best-ai-coding-tools/"
    published = "2026-09-25"
    verified = "2026-09-25"
    title = "Best AI Coding Tools in 2026: Features, Pricing & Comparison | SXF / AI"
    description = "Compare Claude Code, OpenAI Codex, GitHub Copilot, Cursor and Windsurf/Devin Desktop in 2026 by agent workflow, pricing, IDE support, autonomy and team fit."

    tools = [
        {
            "name": "Claude Code",
            "best": "Terminal-first autonomous engineering",
            "surface": "CLI + IDE",
            "agent": "High",
            "free": "No",
            "starting": "$20/mo",
            "pricing": "Claude Pro is $20/month ($17/month equivalent on annual billing); Max starts at $100/month. Claude Code is included in paid Claude plans.",
            "source": "https://claude.com/pricing",
            "internal": "/topics/coding-ai/",
        },
        {
            "name": "OpenAI Codex",
            "best": "OpenAI / ChatGPT coding workflows",
            "surface": "Desktop + CLI + IDE + cloud",
            "agent": "High",
            "free": "Yes",
            "starting": "$0",
            "pricing": "Codex is available across ChatGPT plans. Free access exists for short coding tasks; Plus is $20/month, with higher-capacity Pro plans starting at $100/month. API-key usage is billed separately.",
            "source": "https://developers.openai.com/docs/pricing",
            "internal": "/topics/coding-ai/",
        },
        {
            "name": "GitHub Copilot",
            "best": "GitHub-native teams and broad IDE coverage",
            "surface": "IDE + GitHub + CLI + cloud",
            "agent": "High",
            "free": "Yes",
            "starting": "$0",
            "pricing": "Free includes limited usage. Individual paid plans currently start at Pro $10/month, with Pro+ at $39 and Max at $100.",
            "source": "https://github.com/features/copilot/plans",
            "internal": "/topics/github-copilot/",
        },
        {
            "name": "Cursor",
            "best": "AI-native editor with local and cloud agents",
            "surface": "AI IDE + cloud agents",
            "agent": "High",
            "free": "Yes",
            "starting": "$0",
            "pricing": "Hobby is free. Cursor Pro is $20/month and Teams starts at $40/user/month. Cloud Agents are billed using the selected model's API pricing.",
            "source": "https://cursor.com/pricing",
            "internal": "/topics/coding-ai/",
        },
        {
            "name": "Windsurf / Devin Desktop",
            "best": "Multi-agent command-center workflows",
            "surface": "AI IDE + local/cloud agents",
            "agent": "High",
            "free": "Yes",
            "starting": "$0",
            "pricing": "Windsurf has been renamed Devin Desktop. Current listed plans are Free $0, Pro $20/month and Max $200/month; team pricing is separate.",
            "source": "https://windsurf.com/editor",
            "internal": "/topics/coding-ai/",
        },
    ]

    rows = "".join(
        f'''<tr>
          <th scope="row"><a href="#{escape(slugify(t["name"]), quote=True)}">{escape(t["name"])}</a></th>
          <td>{escape(t["best"])}</td><td>{escape(t["surface"])}</td><td>{escape(t["agent"])}</td>
          <td>{escape(t["free"])}</td><td>{escape(t["starting"])}</td>
        </tr>'''
        for t in tools
    )

    toc = [
        ("quick-comparison", "Quick comparison"),
        ("how-we-evaluated", "How we evaluated"),
        ("claude-code", "Claude Code"),
        ("openai-codex", "OpenAI Codex"),
        ("github-copilot", "GitHub Copilot"),
        ("cursor", "Cursor"),
        ("windsurf-devin-desktop", "Windsurf / Devin Desktop"),
        ("large-codebases", "Best for large codebases"),
        ("autonomous-agents", "Best autonomous coding agent"),
        ("github-workflows", "Best for GitHub workflows"),
        ("free-tools", "Best free option"),
        ("claude-code-vs-cursor-vs-copilot", "Claude Code vs Cursor vs Copilot"),
        ("agent-vs-autocomplete", "AI agent vs autocomplete"),
        ("pricing", "Pricing explained"),
        ("faq", "FAQ"),
    ]
    toc_html = "".join(f'<a href="#{escape(anchor, quote=True)}">{escape(label)}</a>' for anchor,label in toc)

    source_links = "".join(
        f'<a href="{escape(t["source"], quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(t["name"])} official pricing/product page</span><b>↗</b></a>'
        for t in tools
    )

    faq = [
        ("What is the best AI coding tool in 2026?", "There is no universal winner because the products optimize different workflows. Claude Code is strongest as a terminal-first agent, Codex spans local and cloud OpenAI workflows, GitHub Copilot is deeply integrated with GitHub and many IDEs, Cursor is an AI-native editor with cloud agents, and Devin Desktop builds on Windsurf as a multi-agent command center."),
        ("What is the best AI coding tool for large codebases?", "For large repositories, the critical factors are context retrieval, environment setup, test execution and the ability to keep long tasks coherent. Claude Code, Codex and Cursor Cloud Agents are especially relevant when the task requires multi-file planning and verification rather than just completion."),
        ("Which AI coding tool is best for GitHub?", "GitHub Copilot has the most native GitHub surface area because it is built directly into GitHub workflows, including code review and cloud-agent features. Codex, Cursor and Claude Code can also work with GitHub repositories, but through different delegation models."),
        ("Are free AI coding tools good enough?", "Yes for evaluation and light work. GitHub Copilot, Cursor, Codex and Devin Desktop all have free entry points as of the verification date. Heavy agent sessions, premium models and team workflows usually require paid usage."),
        ("Is an AI coding agent the same as autocomplete?", "No. Autocomplete predicts or generates code around the current edit. An agent can inspect a repository, plan work, edit multiple files, run commands and tests, use tools, and sometimes continue remotely in its own development environment."),
        ("Should teams use one coding agent for everything?", "Usually not. The better architecture is to standardize security, review and repository rules, then choose the agent surface that fits each workflow. Inline coding, local debugging, cloud delegation and pull-request review have different operational requirements."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in faq)

    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "TechArticle",
                "@id": canonical + "#article",
                "headline": "Best AI Coding Tools in 2026: Features, Pricing & Comparison",
                "description": description,
                "url": canonical,
                "mainEntityOfPage": canonical,
                "datePublished": published,
                "dateModified": verified,
                "author": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "creator": {"@id": "https://vivamediacreative.com/labs/#organization"},
                "isPartOf": {"@id": "https://sxf.si/#website"},
                "articleSection": "AI Coding",
                "keywords": [
                    "best AI coding tools 2026", "AI coding agents", "Claude Code", "OpenAI Codex",
                    "GitHub Copilot", "Cursor", "Windsurf", "Devin Desktop"
                ],
                "about": [{"@type": "SoftwareApplication", "name": t["name"], "url": t["source"]} for t in tools],
                "citation": [t["source"] for t in tools],
                "inLanguage": "en",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Guides", "item": BASE_URL + "/guides/"},
                    {"@type": "ListItem", "position": 3, "name": "Best AI Coding Tools in 2026", "item": canonical},
                ],
            },
            {
                "@type": "ItemList",
                "name": "AI coding tools compared",
                "numberOfItems": len(tools),
                "itemListElement": [
                    {"@type": "ListItem", "position": i + 1, "name": t["name"], "url": t["source"]}
                    for i,t in enumerate(tools)
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}}
                    for q,a in faq
                ],
            },
        ],
    }

    return f'''<!doctype html><html lang="en">{page_head(title, description, canonical, schema, page_type="article")}
    <body class="intel-page guide-article-page">{page_header("guides")}<main>
      <article>
        <header class="guide-article-hero shell">
          <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/guides/">Guides</a><span>/</span><span>AI Coding Tools</span></nav>
          <p class="eyebrow">SXF GUIDE / AI CODING</p>
          <h1>Best AI Coding Tools in 2026:<br><span>Features, Pricing & Comparison</span></h1>
          <p class="guide-deck">Claude Code, Codex, GitHub Copilot, Cursor and Windsurf have converged on the same destination — agentic software development — but they approach the job from very different surfaces. This guide compares the architecture of the workflow, not just the model name in the picker.</p>
          <div class="guide-byline">
            <div><span>Published</span><strong>September 25, 2026</strong></div>
            <div><span>Last verified</span><strong>September 25, 2026</strong></div>
            <div><span>Reading time</span><strong>18 min</strong></div>
            <div><span>Research standard</span><strong>Primary-source first</strong></div>
          </div>
        </header>

        <section class="guide-answer shell">
          <div class="guide-answer-label">QUICK ANSWER</div>
          <div><h2>There is no single “best” AI coding tool. The best choice depends on where you want the agent to work.</h2>
          <p><strong>Claude Code</strong> is the cleanest terminal-first agent. <strong>Codex</strong> is strongest when you want OpenAI’s coding stack across desktop, CLI, IDE and cloud. <strong>GitHub Copilot</strong> is the natural fit for GitHub-centric organizations. <strong>Cursor</strong> is the most integrated AI-first editor in this group, with local and cloud agents in one product. <strong>Windsurf, now Devin Desktop,</strong> is evolving toward a command center for managing multiple agents while retaining a full IDE.</p></div>
        </section>

        <div class="guide-reading shell">
          <aside class="guide-toc"><span>IN THIS GUIDE</span>{toc_html}<a class="guide-toc-top" href="#top">Back to top ↑</a></aside>

          <div class="guide-prose" id="top">
            <section id="quick-comparison">
              <p class="eyebrow">QUICK COMPARISON</p>
              <h2>Best AI coding tools in 2026 at a glance</h2>
              <p>The coding-tool market has moved beyond autocomplete. The important distinction in 2026 is whether a product can <em>close the loop</em>: understand the repository, make coordinated edits, execute tools, run tests, inspect failures and keep working until a task is actually verified.</p>
              <div class="guide-table-wrap"><table class="guide-table"><thead><tr><th>Tool</th><th>Best fit</th><th>Main surface</th><th>Agentic workflow</th><th>Free entry</th><th>Starts at</th></tr></thead><tbody>{rows}</tbody></table></div>
              <p class="guide-fact-note">Pricing and product availability verified September 25, 2026. Subscription limits, model availability and usage-based charges can change independently of base plan prices.</p>
            </section>

            <section id="how-we-evaluated">
              <p class="eyebrow">METHODOLOGY</p>
              <h2>How we evaluated the best AI coding tools</h2>
              <p>A useful coding agent is not just a model wrapped in a chat panel. SXF evaluates the system around the model. We focus on seven things that determine whether an agent survives real engineering work:</p>
              <div class="guide-criteria">
                <article><span>01</span><h3>Repository understanding</h3><p>Can it retrieve the right files, symbols and history without flooding the context window?</p></article>
                <article><span>02</span><h3>Execution loop</h3><p>Can it edit, run commands, test, inspect failures and iterate instead of stopping after code generation?</p></article>
                <article><span>03</span><h3>Autonomy</h3><p>Can work continue across many steps or in a remote environment without constant human prompting?</p></article>
                <article><span>04</span><h3>Reviewability</h3><p>Can engineers see diffs, logs, test results and artifacts before accepting changes?</p></article>
                <article><span>05</span><h3>Workflow fit</h3><p>Does it live where the developer already works: terminal, IDE, GitHub, cloud or all four?</p></article>
                <article><span>06</span><h3>Cost model</h3><p>Is the economics predictable for daily use, or does heavy agent activity become usage-based?</p></article>
                <article><span>07</span><h3>Team controls</h3><p>Does it support policy, permissions, secrets, auditability and repeatable engineering instructions?</p></article>
              </div>
              <div class="guide-callout"><strong>Expert note</strong><p>We do not rank tools by vendor benchmark charts alone. Coding benchmarks can use different models, harnesses, reasoning settings and evaluation rules. Product architecture matters because the same model can perform very differently when retrieval, tools and verification loops change.</p></div>
            </section>

            <section class="tool-review" id="claude-code">
              <div class="tool-review-head"><span>01</span><div><p class="eyebrow">ANTHROPIC</p><h2>Claude Code: best for terminal-first autonomous engineering</h2></div></div>
              <p>Claude Code is fundamentally different from an editor assistant. Its center of gravity is the terminal and the repository, which makes it feel closer to a software-engineering agent than an AI feature inside an IDE. Anthropic also supports Claude Code in IDEs, but the mental model remains task delegation with tools rather than inline completion.</p>
              <p>That architecture is particularly effective for work that crosses many files: migrations, debugging, dependency changes, test repair, refactors and implementation tasks where the agent needs to inspect the codebase before it can decide what to change. Anthropic has also expanded the product with agent management, scheduled routines, computer use and multi-agent workflows.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>Repo-scale terminal workflows</strong></div><div><span>Primary surface</span><strong>CLI + IDE</strong></div><div><span>Paid access</span><strong>Pro from $20/mo</strong></div><div><span>Workflow style</span><strong>Agent-first</strong></div></div>
              <h3>Where Claude Code is strongest</h3>
              <p>Its advantage is not that “Claude writes better code” in every scenario. The advantage is that the product is comfortable operating as a long-running collaborator with direct access to development tools. For engineers who already live in a shell, that reduces interface friction and makes complex tasks feel natural.</p>
              <h3>What to watch</h3>
              <p>Usage limits are shared across Claude products on subscription plans, and heavy coding can consume capacity quickly. Teams should also design permission boundaries carefully because terminal agents become more useful as they receive more command, network and credential access.</p>
              <div class="tool-links"><a href="https://claude.com/product/claude-code" target="_blank" rel="noopener noreferrer">Claude Code official page ↗</a><a href="https://claude.com/pricing" target="_blank" rel="noopener noreferrer">Official pricing ↗</a><a href="/topics/coding-ai/">SXF Coding AI signals ↗</a></div>
            </section>

            <section class="tool-review" id="openai-codex">
              <div class="tool-review-head"><span>02</span><div><p class="eyebrow">OPENAI</p><h2>OpenAI Codex: best for OpenAI-native coding across local and cloud workflows</h2></div></div>
              <p>Codex is no longer one interface. It spans the desktop app, CLI, IDE extension and cloud execution, and OpenAI exposes related automation surfaces such as the Codex SDK, GitHub Action and cloud agent infrastructure. That makes Codex less like a single editor plugin and more like a coding layer across local and remote environments.</p>
              <p>The important architectural point is delegation. You can work interactively when the problem needs steering, or hand off a task to a cloud environment when you want the agent to keep running, test its changes and return with results. For teams already using ChatGPT and OpenAI models, this lowers the operational cost of introducing a separate coding stack.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>OpenAI / ChatGPT workflows</strong></div><div><span>Primary surface</span><strong>Desktop + CLI + IDE + cloud</strong></div><div><span>Entry</span><strong>Free plan available</strong></div><div><span>Workflow style</span><strong>Local + delegated cloud</strong></div></div>
              <h3>Where Codex is strongest</h3>
              <p>Codex makes sense when software work is part of a broader OpenAI workflow rather than an isolated coding feature. The product can move between interactive development, remote execution and automation, and API-key users can also build Codex into CI or shared engineering systems.</p>
              <h3>What to watch</h3>
              <p>There are two economics to understand: subscription usage when signing in with ChatGPT, and token/API pricing when using an API key. Those are not interchangeable. Teams should decide which path they are standardizing before they compare headline subscription prices.</p>
              <div class="tool-links"><a href="https://developers.openai.com/docs/" target="_blank" rel="noopener noreferrer">Codex documentation ↗</a><a href="https://developers.openai.com/docs/pricing" target="_blank" rel="noopener noreferrer">Official pricing ↗</a><a href="/topics/openai/">OpenAI intelligence ↗</a></div>
            </section>

            <section class="tool-review" id="github-copilot">
              <div class="tool-review-head"><span>03</span><div><p class="eyebrow">GITHUB</p><h2>GitHub Copilot: best for GitHub-native teams and broad IDE coverage</h2></div></div>
              <p>Copilot has evolved from completion into a portfolio of coding surfaces: inline suggestions, chat, agent mode, CLI, code review and cloud agents. Its structural advantage is GitHub itself. Repository hosting, pull requests, code review and agent delegation can live inside the same platform that already owns the team’s development workflow.</p>
              <p>GitHub also offers model choice and access to third-party coding agents on higher plans, so Copilot increasingly acts as an orchestration layer rather than a bet on one model. For organizations with many developers and mixed IDE preferences, that breadth is difficult to ignore.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>GitHub-centric organizations</strong></div><div><span>Primary surface</span><strong>IDE + GitHub + CLI</strong></div><div><span>Entry</span><strong>Free · Pro $10/mo</strong></div><div><span>Workflow style</span><strong>Assist + review + agents</strong></div></div>
              <h3>Where GitHub Copilot is strongest</h3>
              <p>The product is strongest when the organization wants one coding layer that follows developers from the editor to pull requests and review. It also has a lower individual paid entry price than several AI-first editors in this comparison.</p>
              <h3>What to watch</h3>
              <p>The new AI-credit model means “subscription price” is not the complete cost story for agent-heavy usage. Code completions remain unlimited on paid plans, but chats, agents and other AI features draw from credits depending on model and task complexity.</p>
              <div class="tool-links"><a href="https://github.com/features/copilot" target="_blank" rel="noopener noreferrer">GitHub Copilot ↗</a><a href="https://github.com/features/copilot/plans" target="_blank" rel="noopener noreferrer">Official plans ↗</a><a href="/topics/github-copilot/">SXF GitHub Copilot intelligence ↗</a></div>
            </section>

            <section class="tool-review" id="cursor">
              <div class="tool-review-head"><span>04</span><div><p class="eyebrow">CURSOR</p><h2>Cursor: best AI coding editor for integrated local and cloud agent workflows</h2></div></div>
              <p>Cursor’s advantage is product coherence. The editor, agent, model selection, codebase search and cloud agents are designed as one system. That matters because agentic development creates context switching: inspect locally, delegate remotely, review results, continue debugging. Cursor tries to keep those modes inside the same interface and account model.</p>
              <p>Its Cloud Agents run in isolated development environments with repositories, dependencies, secrets and network access. They can build, test and create pull requests without keeping your laptop online, and can be started from the editor, web, mobile, Slack, GitHub, Linear or API.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>AI-first editor workflows</strong></div><div><span>Primary surface</span><strong>Editor + cloud agents</strong></div><div><span>Entry</span><strong>Free · Pro $20/mo</strong></div><div><span>Cloud agent cost</span><strong>Model API pricing</strong></div></div>
              <h3>Where Cursor is strongest</h3>
              <p>Cursor is compelling for developers who want the AI agent to be the editor experience rather than an extension layered on top of an existing IDE. The cloud-agent system also makes parallel work and remote delegation a first-class workflow instead of an add-on.</p>
              <h3>What to watch</h3>
              <p>Cloud-agent economics can differ from the base subscription because remote runs are billed at the selected model’s API rate. Teams should measure real token use on their repositories rather than assume the $20 subscription is the ceiling.</p>
              <div class="tool-links"><a href="https://cursor.com/" target="_blank" rel="noopener noreferrer">Cursor ↗</a><a href="https://cursor.com/pricing" target="_blank" rel="noopener noreferrer">Official pricing ↗</a><a href="https://cursor.com/docs/cloud-agent" target="_blank" rel="noopener noreferrer">Cloud Agents docs ↗</a></div>
            </section>

            <section class="tool-review" id="windsurf-devin-desktop">
              <div class="tool-review-head"><span>05</span><div><p class="eyebrow">COGNITION</p><h2>Windsurf / Devin Desktop: best for managing multiple coding agents from one editor</h2></div></div>
              <p>There is an important naming change in 2026: Windsurf is now called <strong>Devin Desktop</strong>. The underlying IDE experience remains, but the product direction is explicitly moving toward an agent command center where engineers plan, delegate, review and manage local and cloud agents from one surface.</p>
              <p>This makes it less useful to think of Windsurf as “another AI editor.” The strategic idea is multi-agent supervision: the developer stays in a full IDE while several agents can do implementation work around them. Cognition also highlights Fast Context for codebase retrieval and unlimited access to its SWE-1.7 model on the current product page.</p>
              <div class="tool-facts"><div><span>Best for</span><strong>Multi-agent supervision</strong></div><div><span>Primary surface</span><strong>IDE + agent command center</strong></div><div><span>Entry</span><strong>Free · Pro $20/mo</strong></div><div><span>Current name</span><strong>Devin Desktop</strong></div></div>
              <h3>Where Devin Desktop is strongest</h3>
              <p>The product is interesting for engineers who expect the future workflow to involve several agents rather than one chat session. The IDE stays available for deep inspection while the command-center layer is designed for delegation and review.</p>
              <h3>What to watch</h3>
              <p>The rebrand is recent, so search results, documentation and user language still mix “Windsurf” and “Devin Desktop.” For discovery, both names matter. For purchasing decisions, use the current Devin Desktop pricing and documentation rather than older Windsurf plan comparisons.</p>
              <div class="tool-links"><a href="https://windsurf.com/editor" target="_blank" rel="noopener noreferrer">Devin Desktop / Windsurf official page ↗</a><a href="/topics/coding-ai/">SXF Coding AI signals ↗</a></div>
            </section>

            <section id="large-codebases">
              <p class="eyebrow">LONG-TAIL QUESTION</p>
              <h2>What is the best AI coding tool for large codebases?</h2>
              <p>Large repositories expose the weakness of simplistic “context window” comparisons. A coding agent rarely succeeds by loading the entire repository into one prompt. It succeeds by retrieving the right slices of code, preserving task state, running the software and validating its own edits.</p>
              <p>For that reason, <strong>Claude Code, Codex and Cursor Cloud Agents</strong> are the most relevant tools in this group for repo-scale implementation work. Claude Code is attractive when the terminal and local environment are central. Codex is attractive when you want to move between local interaction and delegated cloud work. Cursor is attractive when the editor itself should coordinate both local and remote agents.</p>
              <div class="guide-callout"><strong>What to test on your own repository</strong><p>Give each tool the same multi-file bug or migration. Measure files inspected, unnecessary edits, test execution, recovery from a failing test, total review time and how often a human must re-explain repository context. That tells you more than a generic leaderboard.</p></div>
            </section>

            <section id="autonomous-agents">
              <p class="eyebrow">LONG-TAIL QUESTION</p>
              <h2>Which AI coding tool is best for autonomous coding agents?</h2>
              <p>All five products now have agentic capabilities, so “has agent mode” is no longer a meaningful differentiator. The useful question is where the agent runs and what verification loop surrounds it.</p>
              <p><strong>Cursor</strong> and <strong>Codex</strong> have clear local-to-cloud delegation stories. <strong>Claude Code</strong> is strong when autonomy lives close to the terminal and development environment. <strong>GitHub Copilot</strong> is compelling when delegation should start from issues, pull requests or the GitHub platform. <strong>Devin Desktop</strong> is explicitly designed around supervising multiple agents.</p>
            </section>

            <section id="github-workflows">
              <p class="eyebrow">LONG-TAIL QUESTION</p>
              <h2>What is the best AI coding tool for GitHub workflows and pull requests?</h2>
              <p>For a team whose engineering system already revolves around GitHub, <strong>GitHub Copilot</strong> has the structural advantage. Code review, cloud-agent work, repository context and account governance live inside the same platform. That reduces integration work and gives organizations a single control plane.</p>
              <p>The alternative is not “GitHub or another tool.” Codex, Cursor and Claude Code can all work with GitHub repositories. The tradeoff is whether GitHub should be the agent interface itself or simply the source-control system the agent hands work back to.</p>
            </section>

            <section id="free-tools">
              <p class="eyebrow">LONG-TAIL QUESTION</p>
              <h2>What is the best free AI coding tool in 2026?</h2>
              <p>If the goal is to evaluate the category before paying, there are multiple credible free entry points. <strong>GitHub Copilot Free</strong> includes limited completions and agent/chat usage. <strong>Cursor Hobby</strong> is free with limited agent requests. <strong>Codex</strong> has a free-plan entry for short coding tasks. <strong>Devin Desktop</strong> lists a free plan. Claude Code, by contrast, is included in paid Claude plans rather than Claude Free.</p>
              <p>Free tiers are useful for testing interaction design, but they are poor proxies for the economics of daily autonomous work. Agent sessions consume more model inference, tools and execution time than autocomplete, so serious evaluation should include a paid month and a real repository.</p>
            </section>

            <section id="claude-code-vs-cursor-vs-copilot">
              <p class="eyebrow">CHOOSING BETWEEN LEADERS</p>
              <h2>Claude Code vs Cursor vs GitHub Copilot: how should developers choose?</h2>
              <div class="guide-choice-grid">
                <article><span>Choose Claude Code when…</span><p>You want the terminal to be the primary interface, you delegate complex multi-file work, and you value an agent that feels close to the development environment.</p></article>
                <article><span>Choose Cursor when…</span><p>You want an AI-native editor where chat, editing, model selection and cloud agents feel like one integrated product.</p></article>
                <article><span>Choose GitHub Copilot when…</span><p>Your organization is standardized on GitHub, developers use mixed IDEs, and you want AI assistance, agents and review to share the existing repository platform.</p></article>
              </div>
              <p>Many advanced teams will use more than one. The key is to avoid overlapping tools without a reason. Define which tool owns inline assistance, which owns delegated implementation and which owns automated review.</p>
            </section>

            <section id="agent-vs-autocomplete">
              <p class="eyebrow">FOUNDATION</p>
              <h2>AI coding agent vs autocomplete: what changed?</h2>
              <p>Autocomplete answers a local question: <em>what code probably comes next?</em> An agent answers a systems question: <em>what sequence of actions completes this engineering task?</em></p>
              <div class="guide-difference">
                <div><span>AUTOCOMPLETE</span><strong>Predict → suggest → accept</strong><p>Fast, low-friction and ideal for local edits, boilerplate and repetitive code.</p></div>
                <div><span>CODING AGENT</span><strong>Inspect → plan → edit → run → verify</strong><p>Higher cost and more operational risk, but able to handle tasks that span files, tools and time.</p></div>
              </div>
              <p>This distinction explains why pricing is changing across the category. A completion can be measured as a short inference. An agent may use a frontier model repeatedly, search a repository, call tools, create environments and run tests. The product economics increasingly look like compute orchestration rather than a simple IDE subscription.</p>
            </section>

            <section id="pricing">
              <p class="eyebrow">PRICING GUIDE</p>
              <h2>AI coding tool pricing in 2026: why the monthly fee is only part of the cost</h2>
              <p>The headline subscription price is useful for lightweight interactive coding, but autonomous work introduces a second layer: usage. GitHub uses AI credits for many agent interactions. Cursor Cloud Agents are billed at model API pricing. Codex can run against a ChatGPT allowance or an API key. Claude paid plans share usage across Claude and Claude Code, with optional usage credits. The result is that two developers on the same $20 plan can have very different effective costs.</p>
              <div class="guide-pricing-list">
                {"".join(f'<div><strong>{escape(t["name"])}</strong><p>{escape(t["pricing"])}</p><a href="{escape(t["source"], quote=True)}" target="_blank" rel="noopener noreferrer">Verify pricing ↗</a></div>' for t in tools)}
              </div>
              <div class="guide-callout"><strong>SXF cost rule</strong><p>For teams, compare cost per accepted engineering task — not cost per seat. Include agent usage, review time, failed runs and the human time required to recover from wrong changes.</p></div>
            </section>

            <section class="guide-faq-section" id="faq">
              <p class="eyebrow">FAQ</p>
              <h2>Frequently asked questions about AI coding tools</h2>
              <div class="model-faq">{faq_html}</div>
            </section>

            <section class="guide-sources">
              <p class="eyebrow">PRIMARY SOURCES</p>
              <h2>Official documentation used for this guide</h2>
              <p>Pricing and product capabilities change quickly. SXF links directly to the vendor pages used for verification so readers can check the current state before purchasing.</p>
              <div class="model-sources">{source_links}</div>
            </section>
          </div>
        </div>
      </article>
    </main>{page_footer()}</body></html>'''


def gpt6_vs_claude_guide_html(items):
    canonical = f"{BASE_URL}/guides/gpt-6-vs-claude/"
    published = "2026-09-25"
    verified = "2026-09-25"
    title = "GPT-6 vs Claude in 2026: Models, Pricing, Coding, Context & API Comparison | SXF / AI"
    description = "GPT-6 vs Claude in 2026: compare Astra, Sol and Luna with Claude Fable 5.1, Opus 5.5, Sonnet 5 and Haiku 4.5 on pricing, context, coding, agents and APIs."

    openai_models = [
        {
            "name":"GPT-6 Astra","id":"gpt-6-astra","role":"Highest capability","context":"1.05M","output":"128K",
            "input":"$10","cached":"$1","output_price":"$50","reasoning":"Low → Max",
            "best":"Hardest end-to-end reasoning, coding, research and computer use",
            "source":"https://developers.openai.com/api/docs/models/gpt-6-astra",
            "internal":"/models/gpt-6-astra/"
        },
        {
            "name":"GPT-6 Sol","id":"gpt-6-sol","role":"Capability / cost balance","context":"1.05M","output":"128K",
            "input":"$2","cached":"$0.20","output_price":"$10","reasoning":"None → Max",
            "best":"Complex coding and agentic workflows",
            "source":"https://developers.openai.com/api/docs/models/gpt-6-sol",
            "internal":"/models/gpt-6-sol/"
        },
        {
            "name":"GPT-6 Luna","id":"gpt-6-luna","role":"Efficiency","context":"1.05M","output":"128K",
            "input":"$0.10","cached":"$0.01","output_price":"$0.50","reasoning":"None → Max",
            "best":"Focused, high-volume and cost-sensitive work",
            "source":"https://developers.openai.com/api/docs/models/gpt-6-luna",
            "internal":"/models/gpt-6-luna/"
        },
    ]
    claude_models = [
        {
            "name":"Claude Fable 5.1","id":"claude-fable-5-1","role":"Demanding reasoning","context":"1M","output":"128K",
            "input":"$10","cached":"$0.25","output_price":"$50","reasoning":"Adaptive · always on",
            "best":"Long-horizon agentic work and demanding reasoning",
            "source":"https://platform.claude.com/docs/en/models/fable-5-1/overview"
        },
        {
            "name":"Claude Opus 5.5","id":"claude-opus-5-5","role":"Agentic coding / knowledge work","context":"1M","output":"128K",
            "input":"$4","cached":"$0.20","output_price":"$20","reasoning":"Adaptive · always on",
            "best":"Long-running agentic coding and knowledge work",
            "source":"https://platform.claude.com/docs/en/models/opus-5-5/overview",
            "internal":"/models/claude-opus-5-5/"
        },
        {
            "name":"Claude Sonnet 5","id":"claude-sonnet-5","role":"Speed / intelligence balance","context":"1M","output":"128K",
            "input":"$2","cached":"$0.20","output_price":"$10","reasoning":"Adaptive",
            "best":"Everyday coding, agents, analysis and enterprise work",
            "source":"https://platform.claude.com/docs/en/models/sonnet-5/whats-new-sonnet-5"
        },
        {
            "name":"Claude Haiku 4.5","id":"claude-haiku-4-5","role":"Lowest latency / cost","context":"200K","output":"64K",
            "input":"$1","cached":"$0.10","output_price":"$5","reasoning":"Extended thinking",
            "best":"Real-time and high-volume cost-sensitive workloads",
            "source":"https://platform.claude.com/docs/en/models/haiku-4-5/overview"
        },
    ]

    all_models = openai_models + claude_models
    rows = "".join(
        f'''<tr>
          <th scope="row">{f'<a href="{escape(m.get("internal"), quote=True)}">{escape(m["name"])}</a>' if m.get("internal") else escape(m["name"])}<small>{escape(m["id"])}</small></th>
          <td>{escape("OpenAI" if m in openai_models else "Anthropic")}</td>
          <td>{escape(m["role"])}</td><td>{escape(m["context"])}</td><td>{escape(m["output"])}</td>
          <td>{escape(m["reasoning"])}</td><td>{escape(m["input"])}</td><td>{escape(m["cached"])}</td><td>{escape(m["output_price"])}</td>
        </tr>'''
        for m in all_models
    )

    def cost(input_rate, output_rate, in_m, out_m):
        value = input_rate * in_m + output_rate * out_m
        return ("$" + f"{value:,.4f}").rstrip("0").rstrip(".")

    # Standard short-context example: 100K input + 10K output.
    short = [
        ("GPT-6 Astra", cost(10,50,.1,.01)),
        ("Claude Fable 5.1", cost(10,50,.1,.01)),
        ("GPT-6 Sol", cost(2,10,.1,.01)),
        ("Claude Sonnet 5", cost(2,10,.1,.01)),
        ("Claude Opus 5.5", cost(4,20,.1,.01)),
        ("GPT-6 Luna", cost(.1,.5,.1,.01)),
        ("Claude Haiku 4.5", cost(1,5,.1,.01)),
    ]
    short_cards = "".join(f'<div><span>{escape(n)}</span><strong>{escape(c)}</strong><small>100K input + 10K output</small></div>' for n,c in short)

    # Long-context example: 500K input + 50K output.
    # GPT-6 uses 2x input and 1.5x output above 272K input; Claude 1M models keep standard token pricing.
    long = [
        ("GPT-6 Astra", cost(20,75,.5,.05)),
        ("Claude Fable 5.1", cost(10,50,.5,.05)),
        ("GPT-6 Sol", cost(4,15,.5,.05)),
        ("Claude Sonnet 5", cost(2,10,.5,.05)),
        ("Claude Opus 5.5", cost(4,20,.5,.05)),
        ("GPT-6 Luna", cost(.2,.75,.5,.05)),
    ]
    long_cards = "".join(f'<div><span>{escape(n)}</span><strong>{escape(c)}</strong><small>500K input + 50K output</small></div>' for n,c in long)

    toc = [
        ("quick-answer","Quick answer"),
        ("family-map","GPT-6 and Claude model map"),
        ("pricing","GPT-6 vs Claude pricing"),
        ("context-window","Context window and long context"),
        ("coding","Coding"),
        ("reasoning","Reasoning"),
        ("agents","Agents and tool use"),
        ("api","API differences"),
        ("multimodal","Multimodal capabilities"),
        ("speed","Speed and latency"),
        ("research-writing","Research and writing"),
        ("business","Business and enterprise"),
        ("which-model","Which model should you use?"),
        ("gpt6-vs-claude-opus","GPT-6 vs Claude Opus 5.5"),
        ("faq","FAQ"),
    ]
    toc_html = "".join(f'<a href="#{escape(a, quote=True)}">{escape(label)}</a>' for a,label in toc)

    sources = [
        ("OpenAI GPT-6 model catalog","https://developers.openai.com/api/docs/models"),
        ("OpenAI GPT-6 guidance","https://developers.openai.com/api/docs/guides/latest-model"),
        ("OpenAI GPT-6 Astra","https://developers.openai.com/api/docs/models/gpt-6-astra"),
        ("OpenAI GPT-6 Sol","https://developers.openai.com/api/docs/models/gpt-6-sol"),
        ("OpenAI GPT-6 Luna","https://developers.openai.com/api/docs/models/gpt-6-luna"),
        ("Anthropic current models","https://platform.claude.com/docs/en/models/overview"),
        ("Claude Fable 5.1","https://platform.claude.com/docs/en/models/fable-5-1/overview"),
        ("Claude Opus 5.5","https://platform.claude.com/docs/en/models/opus-5-5/overview"),
        ("Claude Sonnet 5","https://platform.claude.com/docs/en/models/sonnet-5/whats-new-sonnet-5"),
        ("Claude context windows","https://platform.claude.com/docs/en/build-with-claude/context-windows"),
        ("Claude API pricing","https://platform.claude.com/docs/en/about-claude/pricing"),
    ]
    source_links = "".join(f'<a href="{escape(url, quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(label)}</span><b>↗</b></a>' for label,url in sources)

    faq = [
        ("Is GPT-6 better than Claude?", "There is no defensible universal answer from vendor specifications alone. GPT-6 and Claude each contain several models optimized for different capability, latency and cost targets. The useful comparison is workload-specific: model tier, token economics, tool stack, reasoning controls and your own evaluation results."),
        ("Which is cheaper, GPT-6 or Claude?", "At standard short-context rates, GPT-6 Astra and Claude Fable 5.1 both list $10 input and $50 output per million tokens, while GPT-6 Sol and Claude Sonnet 5 both list $2 and $10. GPT-6 Luna is much cheaper than Claude Haiku 4.5 at $0.10/$0.50 versus $1/$5. Long-context economics differ because GPT-6 applies higher rates above 272K input tokens while Claude's 1M models keep standard token pricing."),
        ("Which has the larger context window, GPT-6 or Claude?", "GPT-6 Astra, Sol and Luna each list 1,050,000 tokens. Claude Fable 5.1, Opus 5.5 and Sonnet 5 list 1,000,000 tokens. Claude Haiku 4.5 lists 200,000 tokens. Maximum output is 128K on the GPT-6 family and the three larger Claude models, while Haiku 4.5 lists 64K."),
        ("Which is better for coding, GPT-6 or Claude?", "Both vendors explicitly position current models for coding. OpenAI describes GPT-6 Sol as built for complex coding and agentic workflows and Astra for the hardest end-to-end work. Anthropic positions Opus 5.5 for long-running agentic coding, Sonnet 5 for everyday coding and Fable 5.1 for demanding long-horizon work. The better choice depends on your repository, tools, latency target and cost profile."),
        ("Which is better for AI agents?", "Both platforms now expose serious agent tool stacks. GPT-6 through the Responses API supports built-in tools including web search, file search, code interpreter, hosted shell, computer use and MCP. Claude supports server and client tools including web search, web fetch, code execution, computer use, browser use, tool search and MCP. Tool architecture and operational fit matter as much as the base model."),
        ("Is GPT-6 vs Claude the same as ChatGPT vs Claude?", "No. GPT-6 and Claude refer to model families and APIs. ChatGPT and the Claude app are consumer or workplace products with their own plan limits, interface features, connectors and routing behavior. An API comparison should not be treated as a complete comparison of the apps."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in faq)

    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {
                "@type":"TechArticle","@id":canonical+"#article","url":canonical,"mainEntityOfPage":canonical,
                "headline":"GPT-6 vs Claude in 2026: Models, Pricing, Coding, Context & API Comparison",
                "description":description,"datePublished":published,"dateModified":verified,
                "author":{"@id":"https://vivamediacreative.com/labs/#organization"},
                "creator":{"@id":"https://vivamediacreative.com/labs/#organization"},
                "isPartOf":{"@id":"https://sxf.si/#website"},
                "articleSection":"AI Models",
                "keywords":["GPT-6 vs Claude","GPT-6 vs Claude 2026","GPT-6 vs Claude pricing","GPT-6 vs Claude coding","GPT-6 vs Claude API","GPT-6 vs Claude context window","GPT-6 vs Claude Opus 5.5"],
                "about":[{"@type":"Thing","name":"GPT-6"},{"@type":"Thing","name":"Claude"}],
                "citation":[url for _label,url in sources],
                "inLanguage":"en"
            },
            {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"SXF / AI","item":BASE_URL+"/"},
                {"@type":"ListItem","position":2,"name":"Guides","item":BASE_URL+"/guides/"},
                {"@type":"ListItem","position":3,"name":"GPT-6 vs Claude","item":canonical}
            ]},
            {"@type":"ItemList","name":"GPT-6 and Claude models compared","numberOfItems":len(all_models),"itemListElement":[
                {"@type":"ListItem","position":i+1,"name":m["name"],"url":m["source"]} for i,m in enumerate(all_models)
            ]},
            {"@type":"FAQPage","mainEntity":[
                {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq
            ]}
        ]
    }

    return f'''<!doctype html><html lang="en">{page_head(title, description, canonical, schema, page_type="article")}
    <body class="intel-page guide-article-page">{page_header("guides")}<main>
      <article>
        <header class="guide-article-hero shell">
          <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/guides/">Guides</a><span>/</span><span>GPT-6 vs Claude</span></nav>
          <p class="eyebrow">SXF GUIDE / FRONTIER MODELS</p>
          <h1>GPT-6 vs Claude in 2026:<br><span>Models, Pricing, Coding, Context & API</span></h1>
          <p class="guide-deck">GPT-6 and Claude are no longer single-model comparisons. They are model families with different tiers, reasoning controls, long-context economics and agent stacks. This guide compares the systems layer by layer so you can choose for a real workload instead of comparing brand names.</p>
          <div class="guide-byline">
            <div><span>Published</span><strong>September 25, 2026</strong></div>
            <div><span>Last verified</span><strong>September 25, 2026</strong></div>
            <div><span>Reading time</span><strong>22 min</strong></div>
            <div><span>Evidence</span><strong>Official model docs</strong></div>
          </div>
        </header>

        <section class="guide-answer shell" id="quick-answer">
          <div class="guide-answer-label">QUICK ANSWER</div>
          <div><h2>GPT-6 vs Claude is really a question of model tier, workload shape and agent architecture.</h2>
          <p>At the top end, <strong>GPT-6 Astra</strong> and <strong>Claude Fable 5.1</strong> carry the same listed $10/$50 standard token price and nearly the same context size. In the balanced tier, <strong>GPT-6 Sol</strong> and <strong>Claude Sonnet 5</strong> are both $2/$10. Anthropic inserts <strong>Claude Opus 5.5</strong> between those tiers for long-running agentic coding at $4/$20. At the efficiency end, <strong>GPT-6 Luna</strong> is dramatically cheaper than Claude Haiku 4.5 on listed token rates. The biggest hidden difference is long context: GPT-6 applies higher pricing above 272K input tokens, while Anthropic bills its 1M-context Claude models at standard token rates.</p></div>
        </section>

        <div class="guide-reading shell">
          <aside class="guide-toc"><span>IN THIS GUIDE</span>{toc_html}<a class="guide-toc-top" href="#top">Back to top ↑</a></aside>

          <div class="guide-prose" id="top">
            <section id="family-map">
              <p class="eyebrow">MODEL FAMILY MAP</p>
              <h2>GPT-6 and Claude are families, not one-to-one models</h2>
              <p>The first mistake in a GPT-6 vs Claude comparison is treating each brand as one model. OpenAI currently splits GPT-6 into Astra, Sol and Luna. Anthropic's current lineup includes Fable 5.1, Opus 5.5, Sonnet 5 and Haiku 4.5. Those tiers do not map perfectly, but their pricing and positioning reveal useful comparison pairs.</p>
              <div class="guide-matchup-grid">
                <article><span>TOP-END</span><h3>GPT-6 Astra ↔ Claude Fable 5.1</h3><p>Both list $10 input / $50 output per million tokens and roughly one million tokens of context. OpenAI positions Astra for its hardest end-to-end work; Anthropic reserves Fable for demanding reasoning and long-horizon agents.</p></article>
                <article><span>EVERYDAY / BALANCED</span><h3>GPT-6 Sol ↔ Claude Sonnet 5</h3><p>Both list $2 input / $10 output. Sol is positioned around complex coding and agents; Sonnet 5 around speed plus intelligence for everyday coding, agents and enterprise tasks.</p></article>
                <article><span>AGENTIC CODING</span><h3>GPT-6 Sol ↔ Claude Opus 5.5</h3><p>This is the more interesting coding comparison. Opus 5.5 costs twice Sol at standard token rates, but Anthropic specifically targets long-running agentic coding and keeps standard rates across its 1M context.</p></article>
                <article><span>EFFICIENCY</span><h3>GPT-6 Luna ↔ Claude Haiku 4.5</h3><p>Both target efficient, high-volume work, but their economics are far apart: Luna lists $0.10/$0.50 while Haiku lists $1/$5, and Luna also has a much larger context window.</p></article>
              </div>

              <div class="guide-table-wrap"><table class="guide-table family-table"><thead><tr><th>Model</th><th>Provider</th><th>Positioning</th><th>Context</th><th>Max output</th><th>Thinking</th><th>Input</th><th>Cached</th><th>Output</th></tr></thead><tbody>{rows}</tbody></table></div>
              <p class="guide-fact-note">Prices are USD per 1M text tokens at standard listed rates. GPT-6 long-context pricing changes above 272K input tokens; Claude's 1M-context models use standard token pricing across that context window.</p>
            </section>

            <section id="pricing">
              <p class="eyebrow">GPT-6 VS CLAUDE PRICING</p>
              <h2>Which is cheaper: GPT-6 or Claude?</h2>
              <p>At short context, the answer depends entirely on tier. Astra and Fable 5.1 have identical headline input/output prices. Sol and Sonnet 5 also have identical headline prices. Opus 5.5 occupies a higher-cost coding tier. Luna is the outlier: its token price is one-tenth of Haiku 4.5's listed rate.</p>
              <h3>Example: 100K input tokens + 10K output tokens</h3>
              <div class="cost-grid guide-cost-grid">{short_cards}</div>
              <p>The short-context numbers expose why brand-level statements like “Claude is cheaper” or “GPT is cheaper” are misleading. The model tier matters more than the logo.</p>

              <h3>Long-context economics change the comparison</h3>
              <p>OpenAI states that GPT-6 requests above 272K input tokens are billed at <strong>2× input/cache rates and 1.5× output rates for the full request</strong>. Anthropic states that its 1M-context models use 1M as the default and that long-context requests are billed at standard pricing.</p>
              <h3>Example: 500K input tokens + 50K output tokens</h3>
              <div class="cost-grid guide-cost-grid">{long_cards}</div>
              <p class="guide-fact-note">Claude Haiku 4.5 is excluded from the 500K example because its context window is 200K. These examples cover token charges only; tools, regional processing, fast tiers, caching and other platform charges can alter total cost.</p>
              <div class="guide-callout"><strong>SXF analysis</strong><p>For short prompts, GPT-6 Sol and Claude Sonnet 5 have essentially the same headline token economics. For very long prompts, Claude Sonnet 5 becomes materially cheaper than Sol because Anthropic does not add a long-context multiplier. That is a workload-level difference, not a generic statement that one vendor is cheaper.</p></div>
            </section>

            <section id="context-window">
              <p class="eyebrow">CONTEXT WINDOW</p>
              <h2>GPT-6 vs Claude context window: 1.05M vs 1M is not the whole story</h2>
              <p>GPT-6 Astra, Sol and Luna each list a <strong>1,050,000-token</strong> context window and <strong>128,000 max output tokens</strong>. Claude Fable 5.1, Opus 5.5 and Sonnet 5 each list <strong>1,000,000 tokens</strong> of context and <strong>128,000 max output</strong>. Claude Haiku 4.5 is smaller at 200K context and 64K max output.</p>
              <p>The raw 50K-token difference between 1.05M and 1M is unlikely to be the deciding factor for most systems. Retrieval quality, prompt structure, tool results, cached prefixes and how much context remains after reasoning tokens often matter more. The pricing rule above 272K is more operationally important than the 5% difference in nominal context.</p>
              <h3>Which is better for long documents and giant codebases?</h3>
              <p>For a one-shot request that genuinely needs 500K–1M tokens, Claude's standard long-context billing is economically attractive. For agentic systems, the better design may be to avoid repeatedly sending huge contexts at all: use retrieval, caching, compaction and tools to keep the active working set smaller.</p>
            </section>

            <section id="coding">
              <p class="eyebrow">GPT-6 VS CLAUDE FOR CODING</p>
              <h2>Which is better for coding: GPT-6 or Claude?</h2>
              <p>Both vendors explicitly optimize current models for software engineering, but they emphasize different tiers. OpenAI calls GPT-6 Sol a model built for complex coding and agentic workflows and positions Astra above it for the hardest end-to-end work. Anthropic positions Opus 5.5 for long-running agentic coding, Sonnet 5 for everyday coding and Fable 5.1 for demanding long-horizon work.</p>
              <p>That means the useful comparison is not “GPT-6 vs Claude coding score.” It is <strong>Sol vs Sonnet for everyday economics</strong>, <strong>Sol vs Opus 5.5 for long-running agents</strong>, and <strong>Astra vs Fable 5.1 when capability matters more than latency or token cost</strong>.</p>
              <div class="guide-choice-grid">
                <article><span>Use GPT-6 Sol when…</span><p>You want OpenAI's complex coding/agent tier at $2/$10 and your workflow benefits from explicit reasoning-effort controls and the Responses API tool stack.</p></article>
                <article><span>Use Claude Opus 5.5 when…</span><p>Your workload is long-running agentic coding and you value Anthropic's 1M context at standard rates, adaptive thinking and Claude's tool ecosystem.</p></article>
                <article><span>Use Astra or Fable when…</span><p>The task is difficult enough that cost and latency are secondary to getting a stronger end-to-end result. Test both on your own repository rather than extrapolating from vendor charts.</p></article>
              </div>
              <p>For product-level coding workflows, also separate the models from the coding tools around them. A developer using Claude Code is evaluating a different system than someone calling Claude through a raw API; the same is true for Codex versus a direct GPT-6 API call.</p>
              <div class="tool-links"><a href="/guides/best-ai-coding-tools/">Best AI Coding Tools in 2026 ↗</a><a href="/compare/gpt-6-sol-vs-claude-opus-5-5/">Sol vs Opus 5.5 deep dive ↗</a><a href="/topics/coding-ai/">Coding AI signals ↗</a></div>
            </section>

            <section id="reasoning">
              <p class="eyebrow">REASONING CONTROLS</p>
              <h2>GPT-6 vs Claude reasoning: explicit effort vs adaptive thinking</h2>
              <p>OpenAI exposes a broad reasoning-effort ladder on GPT-6. Astra supports low through max. Sol and Luna additionally support <strong>none</strong>, which lets applications trade reasoning depth for latency and cost on simpler requests.</p>
              <p>Claude's newest models lean more heavily on adaptive thinking. Fable 5.1 and Opus 5.5 keep adaptive thinking always on, with default effort levels of high and medium respectively. Sonnet 5 uses adaptive thinking and allows it to be disabled; Haiku 4.5 uses the older extended-thinking model.</p>
              <div class="guide-callout"><strong>Why this matters</strong><p>Reasoning controls affect more than benchmark quality. They change latency, output-token consumption, cache behavior and how deterministic your cost envelope feels. For production systems, the ability to route easy work to lighter reasoning can be as valuable as peak capability.</p></div>
            </section>

            <section id="agents">
              <p class="eyebrow">AGENTS & TOOL USE</p>
              <h2>GPT-6 vs Claude for AI agents: both are now full agent platforms</h2>
              <p>The agent comparison is no longer “which model can call a function.” Both ecosystems expose substantial tool infrastructure.</p>
              <div class="guide-difference agent-platform-grid">
                <div><span>OPENAI / RESPONSES API</span><strong>Built-in execution surfaces</strong><p>GPT-6 model pages list support for web search, file search, image generation, code interpreter, hosted shell, apply patch, skills, computer use, MCP and tool search, in addition to function calling and structured outputs.</p></div>
                <div><span>ANTHROPIC / MESSAGES API</span><strong>Server + client tool architecture</strong><p>Claude supports server tools such as web search, web fetch, code execution, advisor and tool search, plus MCP. Anthropic also defines client toolsets for computer use, browser use, bash, text editing and memory.</p></div>
              </div>
              <h3>Which agent stack is better?</h3>
              <p>That cannot be answered responsibly from a feature checklist. The engineering questions are: where tools execute, how credentials are isolated, how state persists, how failures are retried, what is billed separately, and how easy it is to inspect what the agent actually did. The right answer can change by deployment architecture even when the model quality is similar.</p>
            </section>

            <section id="api">
              <p class="eyebrow">API COMPARISON</p>
              <h2>GPT-6 vs Claude API: Responses API vs Messages API</h2>
              <p>OpenAI recommends the <strong>Responses API</strong> as the primary path for new GPT-6 applications. It combines model output with built-in tools, stateful workflows and agent features. Claude's core interface is the <strong>Messages API</strong>, with tool calls represented as structured content blocks and an expanding set of Anthropic-hosted server tools.</p>
              <p>Both platforms support function/tool calling, vision, streaming and MCP-based integration. The deeper difference is interface philosophy. OpenAI increasingly bundles execution primitives directly around Responses. Anthropic distinguishes server tools from client tools more explicitly and gives developers detailed control over where execution occurs.</p>
              <h3>Migration cost matters more than syntax</h3>
              <p>If your application already depends on one provider's prompt caching, reasoning format, tool schemas, safety handling or streaming events, switching is not just replacing a model ID. The model may be API-compatible at the HTTP level while the surrounding control plane is not.</p>
            </section>

            <section id="multimodal">
              <p class="eyebrow">MULTIMODAL</p>
              <h2>GPT-6 vs Claude multimodal capabilities</h2>
              <p>Current GPT-6 models accept <strong>text and image input</strong> and return text. OpenAI's model pages list audio and video as unsupported for these GPT-6 text models. Anthropic's current Claude lineup also supports text and image input with text output, plus vision across the family.</p>
              <p>If your application needs speech, realtime audio or native image generation, the comparison moves beyond GPT-6 vs Claude base models and into each vendor's specialized model and tool ecosystem. Do not infer multimodal breadth from the flagship language-model name alone.</p>
            </section>

            <section id="speed">
              <p class="eyebrow">SPEED & LATENCY</p>
              <h2>Which is faster: GPT-6 or Claude?</h2>
              <p>There is no clean cross-vendor answer in the official documentation. Anthropic publishes relative latency labels inside its own lineup: Fable 5.1 is slower, Opus 5.5 moderate, Sonnet 5 fast and Haiku 4.5 fastest. OpenAI exposes model-specific speed characteristics but does not provide a directly comparable, standardized latency number against Claude.</p>
              <p>A serious latency test should measure <strong>time to first token, total completion time, output tokens per second, tool-call round trips and p95/p99 latency</strong> from the region where your application actually runs. Reasoning effort must be held constant enough to make the comparison meaningful.</p>
              <div class="guide-callout"><strong>Do not benchmark the brand</strong><p>“GPT-6 vs Claude speed” is too broad. Benchmark the exact model, effort setting, service tier, prompt length, output length and tool path you plan to deploy.</p></div>
            </section>

            <section id="research-writing">
              <p class="eyebrow">RESEARCH & WRITING</p>
              <h2>GPT-6 vs Claude for research, writing and knowledge work</h2>
              <p>OpenAI positions Astra for research and document creation and describes Sol as a strong everyday driver for writing, coding and work that needs judgment. Anthropic positions Opus 5.5 for long-running knowledge work, Fable 5.1 for multi-step research and demanding reasoning, and Sonnet 5 for everyday content creation and analysis.</p>
              <p>For research systems, the surrounding tools again matter. Both providers offer web access and code execution paths. Citation quality, source-selection behavior and document handling should be tested on the actual research workflow rather than assumed from generic model intelligence.</p>
              <h3>What about long reports?</h3>
              <p>Both top families can emit up to 128K tokens in a single response under their documented limits, although practical applications usually benefit from structured generation, intermediate validation and section-by-section review. Anthropic additionally documents a 300K max-output beta for Opus 5.5 in the Batch API.</p>
            </section>

            <section id="business">
              <p class="eyebrow">ENTERPRISE</p>
              <h2>GPT-6 vs Claude for business and enterprise AI</h2>
              <p>Enterprise choice should not start with “which chatbot feels smarter.” It should start with deployment requirements: data residency, cloud availability, identity and governance, auditability, tool permissions, rate limits, procurement and the cost of operating agents at scale.</p>
              <p>Anthropic distributes current Claude models through the Claude API and major cloud platforms including Amazon Bedrock, Google Cloud and Microsoft Foundry. OpenAI exposes GPT-6 through its API platform with data-residency options that vary by model and processing tier. For regulated workloads, verify the exact model, region and service tier rather than assuming a family-wide policy.</p>
              <h3>Multi-model routing may be better than choosing one vendor model</h3>
              <p>Both companies' own guidance points toward workload-specific model selection. In practice, a robust system often routes easy/high-volume requests to an efficient model and escalates difficult tasks to a stronger one. The unit of optimization is therefore the <em>workflow</em>, not the prestige of the default model.</p>
            </section>

            <section id="which-model">
              <p class="eyebrow">DECISION GUIDE</p>
              <h2>Which GPT-6 or Claude model should you use?</h2>
              <div class="guide-decision-table">
                <div><span>Hardest end-to-end work</span><strong>GPT-6 Astra or Claude Fable 5.1</strong><p>Both occupy the $10/$50 top tier. Run your own evals on the exact task.</p></div>
                <div><span>Everyday coding and agents</span><strong>GPT-6 Sol or Claude Sonnet 5</strong><p>Both list $2/$10 standard pricing; ecosystem and long-context behavior become key differentiators.</p></div>
                <div><span>Long-running agentic coding</span><strong>Claude Opus 5.5 or GPT-6 Sol</strong><p>Opus is explicitly positioned for this workload; Sol is half the standard token price and built for complex coding/agents.</p></div>
                <div><span>Huge prompts above 272K</span><strong>Claude 1M models deserve a close look</strong><p>Anthropic keeps standard token pricing across 1M context; GPT-6 raises rates once input exceeds 272K.</p></div>
                <div><span>High-volume low-cost automation</span><strong>GPT-6 Luna</strong><p>Its $0.10/$0.50 listed rate is materially below Claude Haiku 4.5's $1/$5, while also offering a larger context window.</p></div>
                <div><span>Lowest latency inside Claude</span><strong>Claude Haiku 4.5</strong><p>Anthropic labels it the fastest current Claude model; test against Luna if cross-vendor latency matters.</p></div>
              </div>
            </section>

            <section id="gpt6-vs-claude-opus">
              <p class="eyebrow">DEEP DIVE</p>
              <h2>GPT-6 vs Claude Opus 5.5: which comparison matters most?</h2>
              <p>“GPT-6 vs Claude Opus” can refer to several different pairings. If the question is cost-balanced coding, GPT-6 Sol is the logical OpenAI comparison. If the question is absolute capability, Astra is the higher OpenAI tier. That distinction matters because Sol is $2/$10 while Opus 5.5 is $4/$20, whereas Astra is $10/$50.</p>
              <p>For a detailed Sol-specific comparison—including cache pricing, long-context cost examples and reasoning controls—use the dedicated SXF comparison below.</p>
              <div class="guide-inline-cta"><div><span>SXF DEEP DIVE</span><strong>GPT-6 Sol vs Claude Opus 5.5</strong><p>Pricing, context, reasoning controls and long-context economics using official vendor specifications.</p></div><a href="/compare/gpt-6-sol-vs-claude-opus-5-5/">Open comparison ↗</a></div>
            </section>

            <section class="guide-faq-section" id="faq">
              <p class="eyebrow">FAQ</p>
              <h2>Frequently asked questions about GPT-6 vs Claude</h2>
              <div class="model-faq">{faq_html}</div>
            </section>

            <section class="guide-sources">
              <p class="eyebrow">PRIMARY SOURCES</p>
              <h2>Official sources used for this comparison</h2>
              <p>This guide separates vendor-documented specifications from SXF analysis. Pricing, context windows, reasoning controls and product positioning were checked against the official documentation linked below.</p>
              <div class="model-sources">{source_links}</div>
            </section>
          </div>
        </div>
      </article>
    </main>{page_footer()}</body></html>'''

def guides_index_html(items, current_items):
    canonical = f"{BASE_URL}/guides/"
    description = "In-depth AI guides covering models, coding tools, agents, open-source AI, research and superintelligence, built from primary sources and SXF intelligence."
    published = [
        {
            "href": "/guides/best-ai-coding-tools/",
            "category": "Coding",
            "categories": ["coding", "agents"],
            "kicker": "BUYING GUIDE",
            "title": "Best AI Coding Tools in 2026",
            "description": "Claude Code, Codex, GitHub Copilot, Cursor and Windsurf/Devin Desktop compared by workflow, pricing, autonomy and team fit.",
            "meta": "Coding agents · Pricing · Comparison",
            "updated": "Sep 25, 2026",
            "read_time": "18 min",
        },
        {
            "href": "/guides/gpt-6-vs-claude/",
            "category": "Models",
            "categories": ["models", "coding", "agents", "research"],
            "kicker": "FRONTIER MODEL GUIDE",
            "title": "GPT-6 vs Claude in 2026",
            "description": "A family-level comparison of models, pricing, coding, context windows, reasoning, agents and API architecture.",
            "meta": "Models · Pricing · API · Agents",
            "updated": "Sep 25, 2026",
            "read_time": "22 min",
        },
        {
            "href": f"/compare/{GPT6_COMPARE_SLUG}/",
            "category": "Models",
            "categories": ["models"],
            "kicker": "MODEL SELECTION",
            "title": "GPT-6 Astra vs Sol vs Luna",
            "description": "Compare OpenAI’s GPT-6 family on capability positioning, context, API pricing and workload economics.",
            "meta": "Pricing · Context · Use cases",
            "updated": "Sep 25, 2026",
            "read_time": "6 min",
        },
        {
            "href": f"/compare/{GPT6_SOL_CLAUDE_COMPARE_SLUG}/",
            "category": "Models · Coding · Agents",
            "categories": ["models", "coding", "agents"],
            "kicker": "FRONTIER COMPARISON",
            "title": "GPT-6 Sol vs Claude Opus 5.5",
            "description": "A source-backed comparison of pricing, long-context economics, reasoning controls and agentic positioning.",
            "meta": "API · Agents · Long context",
            "updated": "Sep 25, 2026",
            "read_time": "7 min",
        },
    ]
    featured = published[:2]
    featured_cards = "".join(
        f'''<a class="guide-feature-card {"guide-feature-lead" if i == 0 else ""}" href="{escape(g["href"], quote=True)}">
          <div class="guide-card-top"><span class="guide-card-kicker">{escape(g["kicker"])}</span><small>{escape(g["updated"])}</small></div>
          <h2>{escape(g["title"])}</h2>
          <p>{escape(g["description"])}</p>
          <div class="guide-card-foot"><span>{escape(g["category"])} · {escape(g["read_time"])}</span><b>Read guide ↗</b></div>
        </a>'''
        for i, g in enumerate(featured)
    )
    library_cards = "".join(
        f'''<article class="guide-library-card" data-categories="{escape(" ".join(g["categories"]), quote=True)}" data-search="{escape((g["title"] + " " + g["description"] + " " + g["category"] + " " + g["meta"]).lower(), quote=True)}">
          <a href="{escape(g["href"], quote=True)}">
            <div class="guide-library-meta"><span>{escape(g["category"])}</span><span>Updated {escape(g["updated"])} · {escape(g["read_time"])}</span></div>
            <h3>{escape(g["title"])}</h3>
            <p>{escape(g["description"])}</p>
            <div class="guide-library-foot"><small>{escape(g["meta"])}</small><b>Open guide ↗</b></div>
          </a>
        </article>'''
        for g in published
    )
    tracks = [
        ("/models/", "01", "AI Models", "Capabilities, context windows, pricing, releases and persistent model reference pages.", "Explore models"),
        ("/topics/coding-ai/", "02", "AI Coding", "Coding agents, copilots, developer workflows and the tools changing software engineering.", "Track coding AI"),
        ("/topics/ai-agents/", "03", "AI Agents", "Agentic systems, APIs, orchestration and multi-step AI workflows.", "Explore agents"),
        ("/open-source/", "04", "Open-Source AI", "Open weights, runtimes, local inference, frameworks and deployable model ecosystems.", "Open-source layer"),
        ("/research/", "05", "Research & Safety", "Evaluations, benchmarks, alignment, security and evidence behind capability claims.", "Research layer"),
        ("/topics/ai-safety/", "06", "Superintelligence", "Capability scaling, autonomy, safety and the systems that may shape intelligence beyond today’s frontier models.", "Follow the research"),
    ]
    track_cards = "".join(
        f'''<a class="guide-track" href="{escape(href, quote=True)}"><span>{num}</span><div><h3>{escape(title)}</h3><p>{escape(copy)}</p></div><b>{escape(cta)} ↗</b></a>'''
        for href, num, title, copy, cta in tracks
    )
    latest_rows = "".join(signal_row(item) for item in current_items[:6])
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": "AI Guides — Models, Agents, Coding & Superintelligence | SXF / AI",
                "description": description,
                "isPartOf": {"@id": "https://sxf.si/#website"},
                "about": [
                    {"@type": "Thing", "name": "Artificial intelligence"},
                    {"@type": "Thing", "name": "Artificial superintelligence"},
                ],
                "hasPart": [{"@id": BASE_URL + g["href"]} for g in published],
                "inLanguage": "en",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "SXF / AI", "item": BASE_URL + "/"},
                    {"@type": "ListItem", "position": 2, "name": "Guides", "item": canonical},
                ],
            },
            {
                "@type": "ItemList",
                "name": "SXF AI guides",
                "numberOfItems": len(published),
                "itemListElement": [
                    {"@type": "ListItem", "position": i + 1, "url": BASE_URL + g["href"], "name": g["title"]}
                    for i, g in enumerate(published)
                ],
            },
        ],
    }
    filters = [
        ("all", "All"),
        ("models", "Models"),
        ("coding", "Coding"),
        ("agents", "Agents"),
        ("open-source", "Open Source"),
        ("research", "Research"),
        ("superintelligence", "Superintelligence"),
    ]
    filter_buttons = "".join(
        f'<button class="guide-filter{" is-active" if key == "all" else ""}" type="button" data-filter="{escape(key, quote=True)}">{escape(label)}</button>'
        for key, label in filters
    )
    library_script = '''<script>
    (() => {
      const input = document.getElementById("guideSearch");
      const cards = [...document.querySelectorAll(".guide-library-card")];
      const buttons = [...document.querySelectorAll(".guide-filter")];
      const empty = document.getElementById("guideEmpty");
      const count = document.getElementById("guideVisibleCount");
      let active = "all";
      const apply = () => {
        const q = (input.value || "").trim().toLowerCase();
        let visible = 0;
        cards.forEach(card => {
          const categories = (card.dataset.categories || "").split(" ");
          const categoryMatch = active === "all" || categories.includes(active);
          const searchMatch = !q || (card.dataset.search || "").includes(q);
          const show = categoryMatch && searchMatch;
          card.hidden = !show;
          if (show) visible += 1;
        });
        count.textContent = visible;
        empty.hidden = visible !== 0;
      };
      buttons.forEach(button => button.addEventListener("click", () => {
        buttons.forEach(x => x.classList.remove("is-active"));
        button.classList.add("is-active");
        active = button.dataset.filter || "all";
        apply();
      }));
      input.addEventListener("input", apply);
      apply();
    })();
    </script>'''
    return f'''<!doctype html><html lang="en">{page_head("AI Guides — Models, Agents, Coding & Superintelligence | SXF / AI", description, canonical, schema)}
    <body class="intel-page guides-page">{page_header("guides")}<main>
      <section class="guides-hero shell">
        <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><span>Guides</span></nav>
        <div class="guides-hero-grid">
          <div><p class="eyebrow">SXF GUIDES</p><h1>AI guides.<br><span>Built for decisions.</span></h1></div>
          <div class="guides-hero-copy"><p>Source-backed guides for choosing models, tools and AI systems — with pricing, capabilities, tradeoffs and live context from the SXF radar.</p></div>
        </div>
      </section>

      <section class="guides-featured shell">
        <div class="intel-section-head"><div><p class="eyebrow">FEATURED GUIDES</p><h2>Start here.</h2></div><span>Primary-source research · Living references</span></div>
        <div class="guide-feature-grid">{featured_cards}</div>
      </section>

      <section class="guide-library shell" id="all-guides">
        <div class="guide-library-heading">
          <div><p class="eyebrow">ALL GUIDES</p><h2>Browse the library.</h2><p>Find comparisons and reference guides by subject or search directly.</p></div>
          <div class="guide-library-count"><strong id="guideVisibleCount">{len(published)}</strong><span>guides shown</span></div>
        </div>
        <div class="guide-library-tools">
          <label class="guide-search"><span class="sr-only">Search SXF guides</span><input id="guideSearch" type="search" placeholder="Search guides, models, tools..." autocomplete="off" /></label>
          <div class="guide-filters" aria-label="Filter guides">{filter_buttons}</div>
        </div>
        <div class="guide-library-grid">{library_cards}</div>
        <div class="guide-empty" id="guideEmpty" hidden>No published guides match this filter yet.</div>
      </section>

      <section class="guides-map shell">
        <div class="intel-section-head"><div><p class="eyebrow">EXPLORE BY TOPIC</p><h2>Go deeper into the intelligence stack.</h2></div><span>Models · Tools · Research</span></div>
        <div class="guide-track-grid">{track_cards}</div>
      </section>

      <section class="guide-standard shell">
        <div class="guide-standard-head"><p class="eyebrow">EDITORIAL STANDARD</p><h2>Useful after the launch cycle ends.</h2></div>
        <div class="guide-standard-grid">
          <article><span>01</span><h3>Primary-source first</h3><p>Specifications, pricing, availability and release details trace back to vendor documentation whenever a primary source exists.</p></article>
          <article><span>02</span><h3>Facts before claims</h3><p>Directly comparable facts stay separate from vendor benchmarks, launch claims and interpretation.</p></article>
          <article><span>03</span><h3>Decision-oriented</h3><p>Guides answer practical questions: what changed, what it costs, what it is built for and where tradeoffs appear.</p></article>
          <article><span>04</span><h3>Living references</h3><p>Guides connect to Models, Topics and Signals so new developments update context instead of becoming isolated posts.</p></article>
        </div>
      </section>

      <section class="related-signals shell">
        <div class="intel-section-head"><div><p class="eyebrow">LATEST SIGNALS</p><h2>Live context behind the guides.</h2></div><a href="/signals/">All signals ↗</a></div>
        <div class="signal-list">{latest_rows}</div>
      </section>
    </main>{page_footer()}{library_script}</body></html>'''

def gpt6_comparison_html(items):
    canonical = f"{BASE_URL}/compare/{GPT6_COMPARE_SLUG}/"
    verified = datetime.now(timezone.utc).date().isoformat()
    ref = MODEL_REFERENCE["GPT-6"]
    variants = ref["variants"]
    family_signals = [item for item in items if any(name.startswith("GPT-6") for name in extract_models(item["title"]))][:10]

    def money(value):
        return ("$" + f"{value:,.3f}").rstrip("0").rstrip(".")

    short_examples, monthly_examples = [], []
    for v in variants:
        input_rate = float(v["input_price"].replace("$", ""))
        output_rate = float(v["output_price"].replace("$", ""))
        short_examples.append((v["name"], money(input_rate * 0.1 + output_rate * 0.01)))
        monthly_examples.append((v["name"], money(input_rate * 10 + output_rate)))

    short_cards = "".join(
        f'<div><span>{escape(name)}</span><strong>{escape(cost)}</strong><small>100K input + 10K output</small></div>'
        for name, cost in short_examples
    )
    monthly_cards = "".join(
        f'<div><span>{escape(name)}</span><strong>{escape(cost)}</strong><small>10M input + 1M output</small></div>'
        for name, cost in monthly_examples
    )
    rows = "".join(
        f'''<tr><th scope="row"><a href="/models/{escape(slugify(v["name"]), quote=True)}/">{escape(v["name"])}</a><small>{escape(v["model_id"])}</small></th>
        <td>{escape(v["positioning"])}</td><td>{escape(v["best_for"])}</td><td>{escape(v["context"])}</td><td>{escape(v["max_output"])}</td>
        <td>{escape(v["input_price"])}</td><td>{escape(v["cached_price"])}</td><td>{escape(v["output_price"])}</td></tr>'''
        for v in variants
    )
    source_links = "".join(
        f'<a href="{escape(v["source"], quote=True)}" target="_blank" rel="noopener noreferrer"><span>{escape(v["name"])} model card</span><b>↗</b></a>'
        for v in variants
    ) + '<a href="https://developers.openai.com/api/docs/pricing" target="_blank" rel="noopener noreferrer"><span>OpenAI API pricing</span><b>↗</b></a>'
    signal_rows = "".join(signal_row(item) for item in family_signals)
    faq_items = [
        ("What is the difference between GPT-6 Astra, Sol and Luna?", "OpenAI positions Astra as its most capable model for the hardest end-to-end work, Sol for complex coding and agentic workflows, and Luna as its most efficient option for focused high-volume tasks."),
        ("Do GPT-6 Astra, Sol and Luna have the same context window?", "Yes. OpenAI lists a 1,050,000-token context window and a 128,000-token maximum output for all three models."),
        ("Which GPT-6 model is cheapest?", "GPT-6 Luna has the lowest listed token prices: $0.10 per 1M input tokens, $0.01 cached input and $0.50 output at the listed short-context rates."),
        ("When does GPT-6 long-context pricing apply?", "OpenAI states that prompts above 272K input tokens use higher rates for the full request: 2x input and cache rates and 1.5x output rates."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q, a in faq_items)
    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {"@type":"WebPage","@id":canonical+"#webpage","url":canonical,"name":"GPT-6 Astra vs Sol vs Luna: Pricing, Context & Use Cases","description":"Compare GPT-6 Astra, Sol and Luna on API pricing, context window, output limits and official use-case positioning.","dateModified":verified,"isPartOf":{"@id":"https://sxf.si/#website"},"about":[{"@type":"Thing","name":v["name"]} for v in variants],"citation":[v["source"] for v in variants]+["https://developers.openai.com/api/docs/pricing"],"inLanguage":"en"},
            {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"SXF / AI","item":BASE_URL+"/"},{"@type":"ListItem","position":2,"name":"Models","item":BASE_URL+"/models/"},{"@type":"ListItem","position":3,"name":"GPT-6 comparison","item":canonical}]},
            {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq_items]},
        ],
    }
    description = "GPT-6 Astra vs Sol vs Luna: compare OpenAI API pricing, 1.05M context windows, 128K output limits and official use-case positioning."
    return f'''<!doctype html><html lang="en">{page_head("GPT-6 Astra vs Sol vs Luna — Pricing & Use Cases | SXF / AI", description, canonical, schema)}
    <body class="intel-page comparison-page">{page_header("models")}<main>
      <section class="comparison-hero shell"><nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/models/">Models</a><span>/</span><span>GPT-6 comparison</span></nav>
      <p class="eyebrow">MODEL COMPARISON / VERIFIED {escape(verified)}</p><h1>GPT-6 Astra<br><span>vs Sol vs Luna.</span></h1>
      <p>A decision-oriented comparison built from OpenAI’s official model cards and API pricing. Same 1.05M context window. Very different capability positioning and unit economics.</p>
      <div class="hero-actions"><a class="primary-cta" href="#decision">Choose by workload <span>↓</span></a><a class="secondary-cta" href="/models/gpt-6/">GPT-6 reference</a></div></section>

      <section id="decision" class="decision-grid shell">
        <article><span>ASTRA</span><h2>Maximize capability.</h2><p>For the hardest end-to-end work: complex reasoning, coding, computer use, research and document creation.</p><strong>$10 input · $50 output</strong><a href="/models/gpt-6-astra/">GPT-6 Astra reference ↗</a></article>
        <article><span>SOL</span><h2>Balance capability and cost.</h2><p>Built for complex coding and agentic workflows, at one-fifth of Astra’s listed short-context token rates.</p><strong>$2 input · $10 output</strong><a href="/models/gpt-6-sol/">GPT-6 Sol reference ↗</a></article>
        <article><span>LUNA</span><h2>Optimize for volume.</h2><p>OpenAI’s most efficient GPT-6 option for focused, high-volume tasks and cost-sensitive workloads.</p><strong>$0.10 input · $0.50 output</strong><a href="/models/gpt-6-luna/">GPT-6 Luna reference ↗</a></article>
      </section>

      <section class="comparison-table-section shell"><div class="intel-section-head"><div><p class="eyebrow">SPECIFICATIONS</p><h2>Side-by-side.</h2></div><span>Prices per 1M tokens</span></div>
      <div class="model-table-wrap"><table><thead><tr><th>Model</th><th>Positioning</th><th>Best fit</th><th>Context</th><th>Max output</th><th>Input</th><th>Cached</th><th>Output</th></tr></thead><tbody>{rows}</tbody></table></div>
      <p class="reference-note">Listed rates are the official short-context token prices shown on OpenAI’s model cards. Prompts above 272K input tokens use 2x input/cache rates and 1.5x output rates for the full request.</p></section>

      <section class="cost-section shell"><div class="intel-section-head"><div><p class="eyebrow">COST EXAMPLES</p><h2>What the price gap means.</h2></div><span>Token charges only</span></div>
      <h3>One short-context workload</h3><div class="cost-grid">{short_cards}</div><h3>Monthly volume</h3><div class="cost-grid">{monthly_cards}</div>
      <p class="reference-note">Monthly example assumes requests remain at or below 272K input tokens each. Tool calls, regional processing and other service tiers can change total cost.</p></section>

      <section class="comparison-notes shell"><article><p class="eyebrow">WHAT STAYS THE SAME</p><h2>Context is not the differentiator.</h2><p>All three official model cards list a 1,050,000-token context window and 128,000 maximum output tokens. The choice is driven more by capability needs, workload type and cost.</p></article>
      <article><p class="eyebrow">PRICE RATIO</p><h2>100× from Luna to Astra.</h2><p>At the listed short-context rates, Astra’s input and output token prices are 100× Luna’s. Sol sits at 20× Luna and one-fifth of Astra.</p></article></section>

      <section class="model-reference-lower shell"><div class="model-sources"><p class="eyebrow">OFFICIAL SOURCES</p>{source_links}</div><div class="model-faq"><p class="eyebrow">QUICK ANSWERS</p>{faq_html}</div></section>
      <section class="related-signals shell"><div class="intel-section-head"><div><p class="eyebrow">LATEST GPT-6 SIGNALS</p><h2>What changed recently.</h2></div><a href="/models/gpt-6/">GPT-6 reference ↗</a></div><div class="signal-list">{signal_rows}</div></section>
    </main>{page_footer()}</body></html>'''


def gpt6_sol_vs_claude_opus_html(items):
    canonical = f"{BASE_URL}/compare/{GPT6_SOL_CLAUDE_COMPARE_SLUG}/"
    verified = datetime.now(timezone.utc).date().isoformat()
    sol = {
        "name": "GPT-6 Sol",
        "provider": "OpenAI",
        "model_id": "gpt-6-sol",
        "released": "Sep 22, 2026",
        "positioning": "Complex coding and agentic workflows",
        "context": "1,050,000",
        "max_output": "128,000",
        "knowledge_cutoff": "Apr 20, 2026",
        "thinking": "Optional; none through max",
        "input_price": "$2.00",
        "cached_price": "$0.20",
        "cache_write": "$2.50",
        "output_price": "$10.00",
        "source": "https://developers.openai.com/api/docs/models/gpt-6-sol",
    }
    claude = {
        "name": "Claude Opus 5.5",
        "provider": "Anthropic",
        "model_id": "claude-opus-5-5",
        "released": "Sep 22, 2026",
        "positioning": "Long-running agentic coding and knowledge work",
        "context": "1,000,000",
        "max_output": "128,000",
        "knowledge_cutoff": "Jun 2026",
        "thinking": "Adaptive; always on",
        "input_price": "$4.00",
        "cached_price": "$0.20",
        "cache_write": "$5.00 / $8.00",
        "output_price": "$20.00",
        "source": "https://platform.claude.com/docs/en/models/opus-5-5/overview",
    }

    rows = "".join([
        f'''<tr><th scope="row"><a href="/models/gpt-6-sol/">{escape(sol["name"])}</a><small>{escape(sol["model_id"])}</small></th>
        <td>{escape(sol["provider"])}</td><td>{escape(sol["positioning"])}</td><td>{escape(sol["context"])}</td><td>{escape(sol["max_output"])}</td>
        <td>{escape(sol["thinking"])}</td><td>{escape(sol["input_price"])}</td><td>{escape(sol["cached_price"])}</td><td>{escape(sol["cache_write"])}</td><td>{escape(sol["output_price"])}</td></tr>''',
        f'''<tr><th scope="row"><a href="/models/claude-opus-5-5/">{escape(claude["name"])}</a><small>{escape(claude["model_id"])}</small></th>
        <td>{escape(claude["provider"])}</td><td>{escape(claude["positioning"])}</td><td>{escape(claude["context"])}</td><td>{escape(claude["max_output"])}</td>
        <td>{escape(claude["thinking"])}</td><td>{escape(claude["input_price"])}</td><td>{escape(claude["cached_price"])}</td><td>{escape(claude["cache_write"])}</td><td>{escape(claude["output_price"])}</td></tr>''',
    ])

    def cost(input_rate, output_rate, input_m, output_m):
        value = input_rate * input_m + output_rate * output_m
        return ("$" + f"{value:,.3f}").rstrip("0").rstrip(".")

    standard_examples = [
        ("GPT-6 Sol", cost(2, 10, .1, .01)),
        ("Claude Opus 5.5", cost(4, 20, .1, .01)),
    ]
    monthly_examples = [
        ("GPT-6 Sol", cost(2, 10, 10, 1)),
        ("Claude Opus 5.5", cost(4, 20, 10, 1)),
    ]
    long_examples = [
        ("GPT-6 Sol", cost(4, 15, .5, .05)),
        ("Claude Opus 5.5", cost(4, 20, .5, .05)),
    ]
    standard_cards = "".join(f'<div><span>{escape(n)}</span><strong>{escape(c)}</strong><small>100K input + 10K output</small></div>' for n,c in standard_examples)
    monthly_cards = "".join(f'<div><span>{escape(n)}</span><strong>{escape(c)}</strong><small>10M input + 1M output</small></div>' for n,c in monthly_examples)
    long_cards = "".join(f'<div><span>{escape(n)}</span><strong>{escape(c)}</strong><small>500K input + 50K output</small></div>' for n,c in long_examples)

    relevant = [
        item for item in items
        if "GPT-6 Sol" in extract_models(item["title"]) or "Claude Opus 5.5" in extract_models(item["title"])
    ][:10]
    signal_rows = "".join(signal_row(item) for item in relevant)

    faq_items = [
        ("How much cheaper is GPT-6 Sol than Claude Opus 5.5 at standard token rates?",
         "At the official standard rates, GPT-6 Sol is priced at $2 input and $10 output per million tokens, while Claude Opus 5.5 is $4 input and $20 output. The uncached input and output rates are therefore half as high for Sol."),
        ("Do GPT-6 Sol and Claude Opus 5.5 have the same context window?",
         "No. OpenAI lists a 1,050,000-token context window for GPT-6 Sol. Anthropic lists 1,000,000 tokens for Claude Opus 5.5. Both list a 128,000-token maximum output."),
        ("How do long-context prices differ?",
         "OpenAI states that GPT-6 Sol requests above 272K input tokens use 2x input/cache rates and 1.5x output rates for the full request. Anthropic states that the 1M context window is standard and long-context requests are billed at standard pricing."),
        ("How does reasoning control differ?",
         "GPT-6 Sol supports reasoning effort from none through max. Claude Opus 5.5 uses adaptive thinking that is always on, with medium as the default effort."),
        ("Which model is positioned for coding and agents?",
         "Both vendors position these models for coding and agentic work. OpenAI describes Sol as built for complex coding and agentic workflows; Anthropic describes Opus 5.5 as built for long-running agentic coding and knowledge work."),
    ]
    faq_html = "".join(f'<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>' for q,a in faq_items)

    sources = "".join([
        '<a href="https://developers.openai.com/api/docs/models/gpt-6-sol" target="_blank" rel="noopener noreferrer"><span>OpenAI · GPT-6 Sol model card</span><b>↗</b></a>',
        '<a href="https://developers.openai.com/api/docs/pricing" target="_blank" rel="noopener noreferrer"><span>OpenAI · API pricing</span><b>↗</b></a>',
        '<a href="https://platform.claude.com/docs/en/models/opus-5-5/overview" target="_blank" rel="noopener noreferrer"><span>Anthropic · Claude Opus 5.5 model card</span><b>↗</b></a>',
        '<a href="https://www.anthropic.com/claude-opus-5-5" target="_blank" rel="noopener noreferrer"><span>Anthropic · Opus 5.5 announcement</span><b>↗</b></a>',
    ])

    schema = {
        "@context":"https://schema.org",
        "@graph":[
            {
                "@type":"WebPage","@id":canonical+"#webpage","url":canonical,
                "name":"GPT-6 Sol vs Claude Opus 5.5: Pricing, Context & API Comparison",
                "description":"Compare GPT-6 Sol and Claude Opus 5.5 using official pricing, context, output limits, reasoning controls and long-context billing.",
                "dateModified":verified,"isPartOf":{"@id":"https://sxf.si/#website"},
                "about":[{"@type":"Thing","name":"GPT-6 Sol"},{"@type":"Thing","name":"Claude Opus 5.5"}],
                "citation":[sol["source"],"https://developers.openai.com/api/docs/pricing",claude["source"],"https://www.anthropic.com/claude-opus-5-5"],
                "inLanguage":"en"
            },
            {"@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":1,"name":"SXF / AI","item":BASE_URL+"/"},
                {"@type":"ListItem","position":2,"name":"Models","item":BASE_URL+"/models/"},
                {"@type":"ListItem","position":3,"name":"GPT-6 Sol vs Claude Opus 5.5","item":canonical}
            ]},
            {"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq_items]},
        ]
    }
    description = "GPT-6 Sol vs Claude Opus 5.5: official API pricing, 1.05M vs 1M context, 128K output, reasoning controls and long-context costs."
    return f'''<!doctype html><html lang="en">{page_head("GPT-6 Sol vs Claude Opus 5.5 — Pricing & Context | SXF / AI", description, canonical, schema)}
    <body class="intel-page comparison-page">{page_header("models")}<main>
      <section class="comparison-hero shell">
        <nav class="intel-breadcrumb" aria-label="Breadcrumb"><a href="/">SXF</a><span>/</span><a href="/models/">Models</a><span>/</span><span>Sol vs Opus 5.5</span></nav>
        <p class="eyebrow">MODEL COMPARISON / VERIFIED {escape(verified)}</p>
        <h1>GPT-6 Sol<br><span>vs Claude Opus 5.5.</span></h1>
        <p>Two models released on September 22, 2026 and aimed at serious coding and agentic work. This comparison separates official specifications and pricing from vendor performance claims.</p>
        <div class="hero-actions"><a class="primary-cta" href="#specs">Compare specs <span>↓</span></a><a class="secondary-cta" href="/models/gpt-6-sol/">GPT-6 Sol reference</a></div>
      </section>

      <section class="decision-grid duel-grid shell">
        <article><span>OPENAI · GPT-6 SOL</span><h2>Lower standard token rates.</h2><p>OpenAI positions Sol for complex coding and agentic workflows. It supports optional reasoning effort from none through max and a 1.05M context window.</p><strong>$2 input · $10 output / MTok</strong><a href="/models/gpt-6-sol/">Open Sol reference ↗</a></article>
        <article><span>ANTHROPIC · OPUS 5.5</span><h2>Long-running agentic work.</h2><p>Anthropic positions Opus 5.5 for long-running agentic coding and knowledge work. Adaptive thinking is always on and its 1M context is billed at standard rates.</p><strong>$4 input · $20 output / MTok</strong><a href="/models/claude-opus-5-5/">Open Opus 5.5 signals ↗</a></article>
      </section>

      <section id="specs" class="comparison-table-section shell">
        <div class="intel-section-head"><div><p class="eyebrow">OFFICIAL SPECIFICATIONS</p><h2>Side-by-side facts.</h2></div><span>Vendor documentation</span></div>
        <div class="model-table-wrap"><table><thead><tr><th>Model</th><th>Provider</th><th>Positioning</th><th>Context</th><th>Max output</th><th>Thinking</th><th>Input</th><th>Cache read</th><th>Cache write</th><th>Output</th></tr></thead><tbody>{rows}</tbody></table></div>
        <p class="reference-note">Prices shown are standard per 1M tokens. Claude cache-write pricing is $5 for a 5-minute cache and $8 for a 1-hour cache. GPT-6 Sol cache write is $2.50 per 1M tokens at the listed standard short-context rate.</p>
      </section>

      <section class="cost-section shell">
        <div class="intel-section-head"><div><p class="eyebrow">COST EXAMPLES</p><h2>Same tokens, different billing.</h2></div><span>Direct token charges</span></div>
        <h3>Short-context request</h3><div class="cost-grid two-up">{standard_cards}</div>
        <h3>Monthly standard volume</h3><div class="cost-grid two-up">{monthly_cards}</div>
        <h3>Single long-context request</h3><div class="cost-grid two-up">{long_cards}</div>
        <p class="reference-note">The 500K + 50K example applies OpenAI’s published long-context uplift to Sol and Anthropic’s standard Opus 5.5 rates. It excludes tool calls, regional processing and service-tier adjustments.</p>
      </section>

      <section class="comparison-notes shell">
        <article><p class="eyebrow">CONTEXT ECONOMICS</p><h2>The gap narrows on very long prompts.</h2><p>Sol’s standard uncached token prices are half of Opus 5.5. Above 272K input tokens, however, Sol’s full request moves to higher long-context rates while Anthropic says Opus 5.5 keeps standard pricing across its 1M context window.</p></article>
        <article><p class="eyebrow">CACHE READS</p><h2>Both list $0.20 / MTok.</h2><p>At standard rates, both vendors list $0.20 per million cached or cache-read input tokens. Their cache-write pricing and long-context billing differ, so agent cost depends on the shape of the workload rather than headline input price alone.</p></article>
      </section>

      <section class="comparison-notes shell">
        <article><p class="eyebrow">REASONING CONTROL</p><h2>Optional vs always-on thinking.</h2><p>GPT-6 Sol lets API users select reasoning effort from none to max. Claude Opus 5.5 uses adaptive thinking that cannot be disabled; Anthropic lists medium as its default effort.</p></article>
        <article><p class="eyebrow">BENCHMARK CAUTION</p><h2>Keep vendor claims attributable.</h2><p>Launch benchmark charts can use different harnesses, effort settings and comparison models. SXF keeps this page centered on directly comparable official specifications rather than declaring a benchmark winner from mismatched tests.</p></article>
      </section>

      <section class="model-reference-lower shell"><div class="model-sources"><p class="eyebrow">OFFICIAL SOURCES</p>{sources}</div><div class="model-faq"><p class="eyebrow">QUICK ANSWERS</p>{faq_html}</div></section>
      <section class="related-signals shell"><div class="intel-section-head"><div><p class="eyebrow">RELATED SIGNALS</p><h2>Recent Sol and Opus 5.5 updates.</h2></div><a href="/signals/">All signals ↗</a></div><div class="signal-list">{signal_rows}</div></section>
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
    return f'''<!doctype html><html lang="en">{page_head("SXF Brief — " + pretty, description, canonical, schema, "article", "noindex,follow")}
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
    COMPARE_DIR.mkdir(parents=True, exist_ok=True)
    GUIDES_DIR.mkdir(parents=True, exist_ok=True)

    (GUIDES_DIR / "index.html").write_text(guides_index_html(items, current_items), encoding="utf-8")
    coding_guide_path = GUIDES_DIR / "best-ai-coding-tools"
    coding_guide_path.mkdir(parents=True, exist_ok=True)
    (coding_guide_path / "index.html").write_text(best_ai_coding_tools_html(items), encoding="utf-8")
    model_guide_path = GUIDES_DIR / "gpt-6-vs-claude"
    model_guide_path.mkdir(parents=True, exist_ok=True)
    (model_guide_path / "index.html").write_text(gpt6_vs_claude_guide_html(items), encoding="utf-8")
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

    comparison_path = COMPARE_DIR / GPT6_COMPARE_SLUG
    comparison_path.mkdir(parents=True, exist_ok=True)
    (comparison_path / "index.html").write_text(gpt6_comparison_html(items), encoding="utf-8")

    duel_path = COMPARE_DIR / GPT6_SOL_CLAUDE_COMPARE_SLUG
    duel_path.mkdir(parents=True, exist_ok=True)
    (duel_path / "index.html").write_text(gpt6_sol_vs_claude_opus_html(items), encoding="utf-8")

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
        sitemap_entry(f"{BASE_URL}/guides/", generated_today),
        sitemap_entry(f"{BASE_URL}/guides/best-ai-coding-tools/", "2026-09-25"),
        sitemap_entry(f"{BASE_URL}/guides/gpt-6-vs-claude/", "2026-09-25"),
        sitemap_entry(f"{BASE_URL}/compare/{GPT6_COMPARE_SLUG}/", generated_today),
        sitemap_entry(f"{BASE_URL}/compare/{GPT6_SOL_CLAUDE_COMPARE_SLUG}/", generated_today),
    ]

    for item in items:
        if not item.get("seo_eligible", seo_signal_eligible(item)):
            continue
        modified = parse_date(item.get("modified_at", "")) or parse_date(item["published"])
        rows.append(sitemap_entry(item["signal_url"], modified.date().isoformat()))

    for slug, (_topic, matched) in topic_groups(items).items():
        if topic_page_indexable(matched):
            rows.append(sitemap_entry(f"{BASE_URL}/topics/{slug}/", generated_today))

    for name, matched in model_groups(items).items():
        if model_page_indexable(name, matched):
            rows.append(sitemap_entry(f"{BASE_URL}/models/{slugify(name)}/", generated_today))

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
        "seo_quality_version": "sxf-seo-quality-v1",
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
