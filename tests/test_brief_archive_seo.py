#!/usr/bin/env python3
"""Enforce dated, issue-specific SEO on historical SXF Brief editions.

CI executes this before and after feed regeneration so today's dynamic /brief/
cannot overwrite dated archive titles, descriptions, canonical URLs or schema.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://sxf.si/brief/"
DATE_SLUG = re.compile(r"^\d{4}-\d{2}-\d{2}$")
ARCHIVE = ROOT / "brief"
MONTH = {1: "January", 2: "February", 3: "March", 4: "April",
         5: "May", 6: "June", 7: "July", 8: "August",
         9: "September", 10: "October", 11: "November", 12: "December"}


def require_one(pattern: str, html: str, issue: str, what: str) -> str:
    found = re.findall(pattern, html, re.I | re.S)
    assert len(found) == 1, f"{issue}: expected one {what}, got {len(found)}"
    return unescape(found[0]).strip()


def check_archive() -> None:
    pages = sorted(p for p in ARCHIVE.glob("*/index.html") if DATE_SLUG.fullmatch(p.parent.name))
    assert len(pages) >= 46, "Previously published Brief archive pages were lost"
    titles: set[str] = set()
    for page in pages:
        slug = page.parent.name
        issue_date = date.fromisoformat(slug)
        displayed = f"{MONTH[issue_date.month]} {issue_date.day}, {issue_date.year}"
        short_date = f"{MONTH[issue_date.month][:3]} {issue_date.day}, {issue_date.year}"
        canonical = BASE + slug + "/"
        html = page.read_text(encoding="utf-8")
        title = require_one(r"<title>(.*?)</title>", html, slug, "title")
        description = require_one(r'<meta name="description" content="([^"]+)"', html, slug, "description")
        h1_html = require_one(r"<h1\b[^>]*>(.*?)</h1>", html, slug, "H1")
        h1 = re.sub(r"<[^>]+>", " ", h1_html)
        h1 = " ".join(h1.split())
        assert title.startswith("AI News " + short_date + ":"), (slug, title)
        assert title.endswith(" | SXF Brief"), (slug, title)
        assert 45 <= len(title) <= 90, (slug, len(title))
        assert "AI News Today" not in title, slug
        if issue_date >= date(2026, 11, 1):
            # Dated, indexable issues name their primary real stories in H1,
            # rather than duplicating the generic "Top 5 Stories" archive H1.
            topic = title.split(": ", 1)[1].removesuffix(" | SXF Brief")
            assert h1 == f"AI News — {displayed}: {topic}", (slug, h1, title)
            assert 'class="sxbf-cover-issue-title"' in html, slug
            assert 'class="sxbf-cover-brand">SXF <span>Brief</span></div><h1' in html, slug
            assert '<section class="sxbf-cover sxbf-cover-dated">' in html, slug
            assert "SXF Brief" not in h1, (slug, h1)
        else:
            # Historical noindex editions keep their existing dated summary H1.
            assert displayed in h1 and "Top 5 Stories" in h1, (slug, h1)
        assert "AI News Today" not in h1, slug
        assert 90 <= len(description) <= 185, (slug, len(description))
        assert "AI news today" not in description.lower(), slug
        assert title not in titles, f"Duplicate archive title: {slug}"
        titles.add(title)

        assert require_one(r'<link rel="canonical" href="([^"]+)"', html, slug, "canonical") == canonical
        robots = require_one(r'<meta name="robots" content="([^"]+)"', html, slug, "robots")
        expected_indexed = issue_date >= date(2026, 11, 1)
        assert ("noindex" not in robots) == expected_indexed, f"{slug}: indexing policy drift"
        og_title = require_one(r'<meta property="og:title" content="([^"]+)"', html, slug, "OG title")
        assert og_title == title, (slug, og_title)
        assert require_one(r'<meta property="og:description" content="([^"]+)"', html, slug, "OG description") == description

        raw = require_one(r'<script type="application/ld\+json">(.*?)</script>', html, slug, "JSON-LD")
        ld = json.loads(raw)
        candidates = ld.get("@graph", [ld])
        pageschema = [item for item in candidates if item.get("@type") == "CollectionPage"]
        assert len(pageschema) == 1, f"{slug}: missing CollectionPage"
        node = pageschema[0]
        assert node.get("url") == canonical, (slug, "CollectionPage URL", node.get("url"))
        assert node.get("name") == title, (slug, "CollectionPage name")
        assert node.get("description") == description, (slug, "CollectionPage description")
        assert node.get("datePublished") == slug, (slug, "datePublished")
        # Current issue is not an archive; historic issues must be immutable.
        assert page != ARCHIVE / "index.html"
    assert len(titles) == len(pages)
    print(f"PASS: {len(pages)} dated Brief issues have unique, self-canonical, dated SEO and valid schema")


if __name__ == "__main__":
    check_archive()
