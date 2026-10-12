"""Content-based lastmod tracking for the SXF static sitemap.

Keep a persistent per-page fingerprint so an automated build does not claim that
a page changed just because the workflow ran or unrelated markup was updated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

STATE_NAME = "sitemap-lastmod-state.json"
SITEMAP_NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
ROW_RE = re.compile(r"<loc>([^<]+)</loc><lastmod>([^<]+)</lastmod>")
OMIT_META = {"source_verified", "verified_at", "last_verified", "updated_at",
             "last_checked", "last_checked_at", "fetched_at"}
DYNAMIC_DATA = {
    "/models/": ("model-index.json",),
    "/models/pricing/": ("model-pricing.json",),
    "/tools/ai-model-cost-calculator/": ("model-pricing.json",),
    "/compare/": ("model-pricing.json", "model-comparisons.json"),
    "/providers/": ("model-pricing.json",),
    "/evaluations/": ("model-evaluations.json",),
    "/evaluations/explorer/": ("model-evaluations.json",),
}


class MainContent(HTMLParser):
    """Only visible main-content text, actionable links and images matter.

    In particular, JSON-LD timestamps, navigation, footer, scripts, styling,
    and <time> elements cannot make an article look freshly revised.
    """
    SKIP = {"script", "style", "noscript", "template", "svg", "time"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_main = False
        self.has_main = False
        self.ignored = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == "main":
            self.in_main = True
            self.has_main = True
            return
        if not self.in_main:
            return
        if tag in self.SKIP:
            self.ignored.append(tag)
            return
        if self.ignored:
            return
        props = dict(attrs)
        if tag == "a" and props.get("href"):
            self.parts.append("link:" + props["href"])
        if tag == "img":
            self.parts.append("image:" + props.get("src", "") + "|" + props.get("alt", ""))

    def handle_endtag(self, tag):
        if tag == "main":
            self.in_main = False
        elif self.ignored and tag == self.ignored[-1]:
            self.ignored.pop()

    def handle_data(self, data):
        if self.in_main and not self.ignored:
            content = " ".join(data.split())
            if content:
                self.parts.append(content)


def normalized_data(value):
    """Exclude verification bookkeeping; include real pricing/benchmark data."""
    if isinstance(value, dict):
        return {k: normalized_data(v) for k, v in sorted(value.items())
                if k not in OMIT_META and k != "provenance"}
    if isinstance(value, list):
        return [normalized_data(v) for v in value]
    return value


def html_path(root: Path, url: str, base_url: str) -> Path:
    parsed = urlsplit(url)
    base = urlsplit(base_url)
    if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc) or parsed.query or parsed.fragment:
        raise ValueError(f"Unexpected sitemap URL: {url}")
    route = parsed.path
    if ".." in Path(route).parts or not route.startswith("/"):
        raise ValueError(f"Unsafe sitemap path: {url}")
    relative = route.lstrip("/")
    return root / relative / "index.html" if route.endswith("/") else root / relative


def content_fingerprint(root: Path, url: str, base_url: str) -> str:
    path = html_path(root, url, base_url)
    if not path.is_file():
        raise FileNotFoundError(f"Sitemap target is missing: {path}")
    html = path.read_text(encoding="utf-8")
    parsed = MainContent()
    parsed.feed(html)
    if not parsed.has_main or not parsed.parts:
        raise ValueError(f"Sitemap page has no visible main content: {path}")
    title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    description = re.search(
        r'<meta\s+name=["\x27]description["\x27]\s+content=["\x27]([^"\x27]*)', html, re.I
    )
    parts = [
        unescape(title.group(1)) if title else "",
        unescape(description.group(1)) if description else "",
        *parsed.parts,
    ]
    route = urlsplit(url).path
    for name in DYNAMIC_DATA.get(route, ()):
        file = root / "data" / name
        if not file.is_file():
            raise FileNotFoundError(f"Required public dataset missing: {file}")
        payload = normalized_data(json.loads(file.read_text(encoding="utf-8")))
        parts.append(name + ":" + json.dumps(payload, sort_keys=True, ensure_ascii=False))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def sitemap_dates(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    tree = ET.parse(path)
    return {
        node.findtext("s:loc", namespaces=SITEMAP_NS):
        node.findtext("s:lastmod", namespaces=SITEMAP_NS)
        for node in tree.findall("s:url", SITEMAP_NS)
    }


def _date(value: str, fallback: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except (ValueError, TypeError):
        return fallback


def synchronize_lastmod(rows: list[str], sitemap_path: Path, base_url: str, *, today: str | None = None) -> list[str]:
    """Resolve every sitemap date against the saved content fingerprint."""
    root = sitemap_path.parent
    state_file = root / "data" / STATE_NAME
    old_dates = sitemap_dates(sitemap_path)
    prior = json.loads(state_file.read_text(encoding="utf-8")) if state_file.is_file() else {}
    if prior and prior.get("version") != 1:
        raise ValueError("Unsupported sitemap lastmod state format")
    saved = prior.get("pages", {})
    if not isinstance(saved, dict):
        raise ValueError("Invalid sitemap lastmod state")
    today = today or datetime.now(timezone.utc).date().isoformat()
    today = _date(today, "")
    if not today:
        raise ValueError("Invalid current date")
    pages = {}
    updated_rows = []
    for row in rows:
        match = ROW_RE.search(row)
        if not match:
            raise ValueError("Sitemap row is missing a URL or lastmod")
        url, proposed = match.groups()
        if url in pages:
            raise ValueError(f"Duplicate sitemap URL: {url}")
        fingerprint = content_fingerprint(root, url, base_url)
        previous = saved.get(url)
        if previous and previous.get("hash") == fingerprint:
            stamp = _date(previous.get("lastmod"), today)
        elif previous:
            stamp = today
        else:
            # First run: preserve published dates; never mark every old page as new.
            stamp = _date(old_dates.get(url) or proposed, today)
        if stamp > today:
            stamp = today
        pages[url] = {"hash": fingerprint, "lastmod": stamp}
        updated_rows.append(row[:match.start(2)] + stamp + row[match.end(2):])
    payload = json.dumps({"version": 1, "pages": pages}, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    if not state_file.is_file() or state_file.read_text(encoding="utf-8") != payload:
        state_file.write_text(payload, encoding="utf-8")
    return updated_rows


def refresh_existing_sitemap(sitemap_path: Path, base_url: str):
    """Recheck the final HTML after the workflows' post-render modifications."""
    xml = sitemap_path.read_text(encoding="utf-8")
    lines = xml.splitlines(keepends=True)
    indices = [i for i, line in enumerate(lines) if line.lstrip().startswith("<url>")]
    rows = [lines[i].rstrip("\n") for i in indices]
    updated = synchronize_lastmod(rows, sitemap_path, base_url)
    for i, row in zip(indices, updated):
        lines[i] = row + ("\n" if lines[i].endswith("\n") else "")
    result = "".join(lines)
    if result != xml:
        sitemap_path.write_text(result, encoding="utf-8")


def validate_sitemap_state(sitemap_path: Path, base_url: str):
    """Fail CI if a late HTML/data edit was not reflected in sitemap lastmod."""
    state_file = sitemap_path.parent / "data" / STATE_NAME
    if not state_file.is_file():
        raise ValueError("Missing sitemap lastmod state; run the site generator")
    records = json.loads(state_file.read_text(encoding="utf-8"))["pages"]
    sitemap = sitemap_dates(sitemap_path)
    if set(sitemap) != set(records):
        raise ValueError("Sitemap entries and lastmod state differ")
    for url, stamp in sitemap.items():
        saved = records[url]
        if saved.get("lastmod") != stamp:
            raise ValueError(f"Incorrect lastmod for {url}")
        if saved.get("hash") != content_fingerprint(sitemap_path.parent, url, base_url):
            raise ValueError(f"Stale sitemap content fingerprint for {url}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", required=True)
    args = parser.parse_args()
    refresh_existing_sitemap(Path(__file__).resolve().parents[1] / "sitemap.xml", "https://sxf.si")
    print("Sitemap lastmod dates synchronized with visible page content")
