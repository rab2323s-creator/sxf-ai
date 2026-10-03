#!/usr/bin/env python3
from __future__ import annotations

import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

ADAPTER_CONTRACT_VERSION = "sxf-source-adapter-v1"
ANTHROPIC_HOSTS = {"anthropic.com", "www.anthropic.com"}
META_HOSTS = {"ai.meta.com"}
XAI_HOSTS = {"x.ai", "www.x.ai"}
ANTHROPIC_MODEL_ANNOUNCEMENT = re.compile(
    r"^/claude-(?:opus|sonnet|haiku|fable|mythos)-[a-z0-9-]+/?$",
    re.I,
)
MONTH_DATE = re.compile(
    r"\b("
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
    r")\s+(\d{1,2}),\s+(\d{4})\b",
    re.I,
)


class AdapterDriftError(RuntimeError):
    pass


def _parse_iso(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _clean_text(value, limit=900):
    value = unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit]


def _fetch(url, user_agent, attempts=3):
    last_error = None
    for attempt in range(attempts):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": user_agent,
                "Accept": "application/xml,text/xml,text/html;q=0.9,*/*;q=0.8",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                return response.read()
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(1.0 * (2 ** attempt))
    raise last_error


def _anthropic_candidate_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() not in ANTHROPIC_HOSTS:
        return False
    path = parsed.path.rstrip("/") or "/"
    if path.startswith("/news/"):
        return True
    return bool(ANTHROPIC_MODEL_ANNOUNCEMENT.match(path))


def parse_anthropic_sitemap(body, now, discovery_days=45, max_urls=30):
    try:
        root = ET.fromstring(body)
    except Exception as exc:
        raise AdapterDriftError(f"Anthropic sitemap is not valid XML: {exc}") from exc

    cutoff = now - timedelta(days=discovery_days)
    discovered = []
    invalid = 0
    for node in root.findall(".//{*}url"):
        loc_node = node.find("{*}loc")
        lastmod_node = node.find("{*}lastmod")
        loc = (loc_node.text or "").strip() if loc_node is not None else ""
        lastmod = _parse_iso((lastmod_node.text or "").strip()) if lastmod_node is not None else None
        if not loc or not _anthropic_candidate_url(loc):
            continue
        is_model_announcement = bool(
            ANTHROPIC_MODEL_ANNOUNCEMENT.match(urlparse(loc).path.rstrip("/") or "/")
        )
        if lastmod is None:
            if is_model_announcement:
                discovered.append((now, loc))
                continue
            invalid += 1
            continue
        if not is_model_announcement and (lastmod < cutoff or lastmod > now + timedelta(days=1)):
            continue
        if is_model_announcement and lastmod > now + timedelta(days=1):
            invalid += 1
            continue
        discovered.append((lastmod, loc))

    model_rows = [row for row in discovered if ANTHROPIC_MODEL_ANNOUNCEMENT.match(urlparse(row[1]).path.rstrip("/") or "/")]
    news_rows = [row for row in discovered if row not in model_rows]
    model_rows.sort(key=lambda row: row[0], reverse=True)
    news_rows.sort(key=lambda row: row[0], reverse=True)

    reserved_model_slots = min(len(model_rows), max(1, max_urls // 3))
    selected = model_rows[:reserved_model_slots]
    selected.extend(news_rows[: max(0, max_urls - len(selected))])
    if len(selected) < max_urls:
        selected.extend(model_rows[reserved_model_slots : reserved_model_slots + (max_urls - len(selected))])
    selected = sorted(selected, key=lambda row: row[0], reverse=True)[:max_urls]

    urls = [url for _lastmod, url in selected]
    if not urls:
        raise AdapterDriftError("Anthropic sitemap yielded zero recent news/model announcement URLs")
    return urls, invalid


class _ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = {}
        self.h1_parts = []
        self.title_parts = []
        self.paragraphs = []
        self.visible_parts = []
        self.time_values = []
        self._in_h1 = 0
        self._in_title = 0
        self._in_p = 0
        self._current_p = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs = {str(key).lower(): (value or "") for key, value in attrs}
        if tag == "meta":
            key = (attrs.get("property") or attrs.get("name") or attrs.get("itemprop") or "").lower()
            content = attrs.get("content", "")
            if key and content and key not in self.meta:
                self.meta[key] = content
        elif tag == "h1":
            self._in_h1 += 1
        elif tag == "title":
            self._in_title += 1
        elif tag == "p":
            self._in_p += 1
            self._current_p = []
        elif tag == "time":
            value = attrs.get("datetime")
            if value:
                self.time_values.append(value)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "h1" and self._in_h1:
            self._in_h1 -= 1
        elif tag == "title" and self._in_title:
            self._in_title -= 1
        elif tag == "p" and self._in_p:
            self._in_p -= 1
            value = _clean_text(" ".join(self._current_p))
            if value:
                self.paragraphs.append(value)
            self._current_p = []

    def handle_data(self, data):
        value = re.sub(r"\s+", " ", data or "").strip()
        if not value:
            return
        self.visible_parts.append(value)
        if self._in_h1:
            self.h1_parts.append(value)
        if self._in_title:
            self.title_parts.append(value)
        if self._in_p:
            self._current_p.append(value)


def _parse_visible_date(text):
    match = MONTH_DATE.search(text)
    if not match:
        return None
    month, day, year = match.groups()
    for fmt in ("%b %d %Y", "%B %d %Y"):
        try:
            parsed = datetime.strptime(f"{month} {day} {year}", fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def parse_anthropic_article(body, url):
    html = body.decode("utf-8", "ignore") if isinstance(body, (bytes, bytearray)) else str(body)
    parser = _ArticleParser()
    parser.feed(html)

    title = _clean_text(" ".join(parser.h1_parts), 240)
    if not title:
        title = _clean_text(parser.meta.get("og:title") or parser.meta.get("twitter:title"), 240)
    if not title:
        title = _clean_text(" ".join(parser.title_parts), 240)
    title = re.sub(r"\s*[\\|·-]\s*Anthropic\s*$", "", title, flags=re.I).strip()

    summary = _clean_text(
        parser.meta.get("description")
        or parser.meta.get("og:description")
        or parser.meta.get("twitter:description")
    )
    if len(summary) < 60:
        summary = next((value for value in parser.paragraphs if len(value) >= 60), summary)

    published = None
    for key in ("article:published_time", "datepublished", "date", "publishdate"):
        published = _parse_iso(parser.meta.get(key))
        if published is not None:
            break
    if published is None:
        for value in parser.time_values:
            published = _parse_iso(value)
            if published is not None:
                break
    if published is None:
        published = _parse_visible_date(" ".join(parser.visible_parts[:120]))

    missing = []
    if not title:
        missing.append("title")
    if not summary:
        missing.append("summary")
    if published is None:
        missing.append("published")
    if missing:
        raise AdapterDriftError(f"Anthropic article missing required fields {missing}: {url}")

    return {
        "title": title,
        "url": url,
        "published": published.isoformat().replace("+00:00", "Z"),
        "summary": summary,
    }



class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        attrs = {str(key).lower(): (value or "") for key, value in attrs}
        href = attrs.get("href", "").strip()
        if href:
            self.hrefs.append(href)


def _meta_candidate_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() not in META_HOSTS:
        return False
    path = parsed.path.rstrip("/")
    return path.startswith("/blog/") and path != "/blog"


def parse_meta_blog_index(body, discovery_url, max_urls=30):
    html = body.decode("utf-8", "ignore") if isinstance(body, (bytes, bytearray)) else str(body)
    parser = _LinkParser()
    parser.feed(html)

    urls = []
    seen = set()
    for href in parser.hrefs:
        absolute = urljoin(discovery_url, href)
        parsed = urlparse(absolute)
        canonical = parsed._replace(query="", fragment="").geturl()
        if not _meta_candidate_url(canonical) or canonical in seen:
            continue
        seen.add(canonical)
        urls.append(canonical)
        if len(urls) >= max_urls:
            break

    if not urls:
        raise AdapterDriftError("Meta blog index yielded zero official blog article URLs")
    return urls


def parse_meta_article(body, url):
    if not _meta_candidate_url(url):
        raise AdapterDriftError(f"Meta article URL is outside the official blog: {url}")

    html = body.decode("utf-8", "ignore") if isinstance(body, (bytes, bytearray)) else str(body)
    parser = _ArticleParser()
    parser.feed(html)

    title = _clean_text(" ".join(parser.h1_parts), 240)
    if not title:
        title = _clean_text(parser.meta.get("og:title") or parser.meta.get("twitter:title"), 240)
    if not title:
        title = _clean_text(" ".join(parser.title_parts), 240)
    title = re.sub(r"\s*[\\|·-]\s*(?:AI at Meta|Meta AI)\s*$", "", title, flags=re.I).strip()

    summary = _clean_text(
        parser.meta.get("description")
        or parser.meta.get("og:description")
        or parser.meta.get("twitter:description")
    )
    if len(summary) < 60:
        summary = next((value for value in parser.paragraphs if len(value) >= 60), summary)

    published = None
    for key in ("article:published_time", "datepublished", "date", "publishdate", "publish_date"):
        published = _parse_iso(parser.meta.get(key))
        if published is not None:
            break
    if published is None:
        for value in parser.time_values:
            published = _parse_iso(value)
            if published is not None:
                break
    if published is None:
        published = _parse_visible_date(" ".join(parser.visible_parts[:120]))

    missing = []
    if not title:
        missing.append("title")
    if not summary:
        missing.append("summary")
    if published is None:
        missing.append("published")
    if missing:
        raise AdapterDriftError(f"Meta article missing required fields {missing}: {url}")

    return {
        "title": title,
        "url": url,
        "published": published.isoformat().replace("+00:00", "Z"),
        "summary": summary,
    }


def run_meta_blog_adapter(source_config, user_agent, now=None, fetcher=None):
    now = now or datetime.now(timezone.utc)
    fetcher = fetcher or (lambda url: _fetch(url, user_agent))
    discovery_url = source_config["url"]
    discovery_pages = max(1, int(source_config.get("discovery_pages", 2)))
    max_discovery = max(1, int(source_config.get("max_discovery", 30)))

    discovered = []
    seen = set()
    errors = []
    fetch_failures = 0
    invalid_items = 0

    for page in range(1, discovery_pages + 1):
        page_url = discovery_url if page == 1 else f"{discovery_url}?page={page}"
        try:
            page_body = fetcher(page_url)
            page_urls = parse_meta_blog_index(
                page_body,
                discovery_url=discovery_url,
                max_urls=max_discovery,
            )
        except Exception as exc:
            if isinstance(exc, AdapterDriftError):
                invalid_items += 1
                errors.append(str(exc))
            else:
                fetch_failures += 1
                errors.append(f"{page_url}: {exc}")
            continue

        for url in page_urls:
            if url in seen:
                continue
            seen.add(url)
            discovered.append(url)
            if len(discovered) >= max_discovery:
                break
        if len(discovered) >= max_discovery:
            break

    if not discovered:
        detail = "; ".join(errors[:3]) if errors else "no discoverable articles"
        raise AdapterDriftError(f"Meta adapter zero-result anomaly: {detail}")

    items = []
    for url in discovered:
        try:
            article = parse_meta_article(fetcher(url), url)
            item = {
                **article,
                "source": source_config["name"],
                "provenance": {
                    "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
                    "adapter": source_config["adapter"],
                    "discovery_url": discovery_url,
                    "source_url": url,
                    "discovered_via": "official-blog-index",
                },
            }
            validate_contract_item(source_config["name"], item, discovery_url)
            items.append(item)
        except Exception as exc:
            invalid_items += 1
            if isinstance(exc, AdapterDriftError):
                errors.append(str(exc))
            else:
                fetch_failures += 1
                errors.append(f"{url}: {exc}")

    if not items:
        detail = "; ".join(errors[:3]) if errors else "no parseable articles"
        raise AdapterDriftError(f"Meta adapter zero-result anomaly: {detail}")

    diagnostics = {
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "discovered_count": len(discovered),
        "parsed_count": len(items),
        "invalid_count": invalid_items,
        "fetch_failure_count": fetch_failures,
        "schema_drift": bool(invalid_items and not items),
        "errors": errors[:10],
    }
    return items, diagnostics


def _xai_candidate_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc.lower() not in XAI_HOSTS:
        return False
    path = parsed.path.rstrip("/")
    return path.startswith("/news/") and path != "/news"


def parse_xai_news_index(body, discovery_url, max_urls=20):
    html = body.decode("utf-8", "ignore") if isinstance(body, (bytes, bytearray)) else str(body)
    parser = _LinkParser()
    parser.feed(html)

    urls = []
    seen = set()
    for href in parser.hrefs:
        absolute = urljoin(discovery_url, href)
        parsed = urlparse(absolute)
        canonical = parsed._replace(query="", fragment="").geturl()
        if not _xai_candidate_url(canonical) or canonical in seen:
            continue
        seen.add(canonical)
        urls.append(canonical)
        if len(urls) >= max_urls:
            break

    if not urls:
        raise AdapterDriftError("xAI news index yielded zero official news article URLs")
    return urls


def parse_xai_article(body, url):
    if not _xai_candidate_url(url):
        raise AdapterDriftError(f"xAI article URL is outside the official news section: {url}")

    html = body.decode("utf-8", "ignore") if isinstance(body, (bytes, bytearray)) else str(body)
    parser = _ArticleParser()
    parser.feed(html)

    title = _clean_text(" ".join(parser.h1_parts), 240)
    if not title:
        title = _clean_text(parser.meta.get("og:title") or parser.meta.get("twitter:title"), 240)
    if not title:
        title = _clean_text(" ".join(parser.title_parts), 240)
    title = re.sub(r"\s*[\\|·-]\s*(?:SpaceXAI|xAI)\s*$", "", title, flags=re.I).strip()

    summary = _clean_text(
        parser.meta.get("description")
        or parser.meta.get("og:description")
        or parser.meta.get("twitter:description")
    )
    if len(summary) < 60:
        summary = next((value for value in parser.paragraphs if len(value) >= 60), summary)

    published = None
    for key in ("article:published_time", "datepublished", "date", "publishdate", "publish_date"):
        published = _parse_iso(parser.meta.get(key))
        if published is not None:
            break
    if published is None:
        for value in parser.time_values:
            published = _parse_iso(value)
            if published is not None:
                break
    if published is None:
        published = _parse_visible_date(" ".join(parser.visible_parts[:160]))

    missing = []
    if not title:
        missing.append("title")
    if not summary:
        missing.append("summary")
    if published is None:
        missing.append("published")
    if missing:
        raise AdapterDriftError(f"xAI article missing required fields {missing}: {url}")

    return {
        "title": title,
        "url": url,
        "published": published.isoformat().replace("+00:00", "Z"),
        "summary": summary,
    }


def run_xai_news_adapter(source_config, user_agent, now=None, fetcher=None):
    now = now or datetime.now(timezone.utc)
    fetcher = fetcher or (lambda url: _fetch(url, user_agent))
    discovery_url = source_config["url"]
    max_discovery = max(1, int(source_config.get("max_discovery", 20)))

    index_body = fetcher(discovery_url)
    urls = parse_xai_news_index(
        index_body,
        discovery_url=discovery_url,
        max_urls=max_discovery,
    )

    items = []
    errors = []
    fetch_failures = 0
    invalid_items = 0
    for url in urls:
        try:
            article = parse_xai_article(fetcher(url), url)
            item = {
                **article,
                "source": source_config["name"],
                "provenance": {
                    "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
                    "adapter": source_config["adapter"],
                    "discovery_url": discovery_url,
                    "source_url": url,
                    "discovered_via": "official-news-index",
                },
            }
            validate_contract_item(source_config["name"], item, discovery_url)
            items.append(item)
        except Exception as exc:
            invalid_items += 1
            if isinstance(exc, AdapterDriftError):
                errors.append(str(exc))
            else:
                fetch_failures += 1
                errors.append(f"{url}: {exc}")

    if not items:
        detail = "; ".join(errors[:3]) if errors else "no parseable articles"
        raise AdapterDriftError(f"xAI adapter zero-result anomaly: {detail}")

    diagnostics = {
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "discovered_count": len(urls),
        "parsed_count": len(items),
        "invalid_count": invalid_items,
        "fetch_failure_count": fetch_failures,
        "schema_drift": bool(invalid_items and not items),
        "errors": errors[:10],
    }
    return items, diagnostics

def validate_contract_item(source, item, discovery_url):
    required = ("title", "url", "source", "published", "summary", "provenance")
    missing = [key for key in required if not item.get(key)]
    if missing:
        raise AdapterDriftError(f"{source}: adapter item missing {missing}")
    parsed = urlparse(item["url"])
    if parsed.scheme != "https" or not parsed.netloc:
        raise AdapterDriftError(f"{source}: adapter item has invalid URL {item['url']!r}")
    if _parse_iso(item["published"]) is None:
        raise AdapterDriftError(f"{source}: adapter item has invalid published date")
    provenance = item.get("provenance")
    if not isinstance(provenance, dict):
        raise AdapterDriftError(f"{source}: provenance must be an object")
    if provenance.get("adapter_contract_version") != ADAPTER_CONTRACT_VERSION:
        raise AdapterDriftError(f"{source}: adapter contract version missing or invalid")
    if provenance.get("discovery_url") != discovery_url:
        raise AdapterDriftError(f"{source}: discovery provenance drift")
    if provenance.get("source_url") != item["url"]:
        raise AdapterDriftError(f"{source}: source URL provenance drift")


def run_anthropic_sitemap_adapter(source_config, user_agent, now=None, fetcher=None):
    now = now or datetime.now(timezone.utc)
    fetcher = fetcher or (lambda url: _fetch(url, user_agent))
    discovery_url = source_config["url"]
    discovery_days = int(source_config.get("discovery_days", 45))
    max_discovery = int(source_config.get("max_discovery", 30))

    sitemap_body = fetcher(discovery_url)
    urls, sitemap_invalid = parse_anthropic_sitemap(
        sitemap_body,
        now=now,
        discovery_days=discovery_days,
        max_urls=max_discovery,
    )

    items = []
    errors = []
    fetch_failures = 0
    invalid_items = sitemap_invalid
    for url in urls:
        try:
            article = parse_anthropic_article(fetcher(url), url)
            item = {
                **article,
                "source": source_config["name"],
                "provenance": {
                    "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
                    "adapter": source_config["adapter"],
                    "discovery_url": discovery_url,
                    "source_url": url,
                    "discovered_via": "official-sitemap",
                },
            }
            validate_contract_item(source_config["name"], item, discovery_url)
            items.append(item)
        except Exception as exc:
            invalid_items += 1
            if isinstance(exc, AdapterDriftError):
                errors.append(str(exc))
            else:
                fetch_failures += 1
                errors.append(f"{url}: {exc}")

    if not items:
        detail = "; ".join(errors[:3]) if errors else "no parseable articles"
        raise AdapterDriftError(f"Anthropic adapter zero-result anomaly: {detail}")

    diagnostics = {
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "discovered_count": len(urls),
        "parsed_count": len(items),
        "invalid_count": invalid_items,
        "fetch_failure_count": fetch_failures,
        "schema_drift": bool(invalid_items and not items),
        "errors": errors[:10],
    }
    return items, diagnostics


def run_source_adapter(source_config, user_agent, now=None, fetcher=None):
    adapter = source_config.get("adapter")
    if adapter == "anthropic-sitemap":
        return run_anthropic_sitemap_adapter(
            source_config,
            user_agent=user_agent,
            now=now,
            fetcher=fetcher,
        )
    if adapter == "meta-blog":
        return run_meta_blog_adapter(
            source_config,
            user_agent=user_agent,
            now=now,
            fetcher=fetcher,
        )
    if adapter == "xai-news":
        return run_xai_news_adapter(
            source_config,
            user_agent=user_agent,
            now=now,
            fetcher=fetcher,
        )
    raise RuntimeError(f"Unsupported source adapter: {adapter}")
